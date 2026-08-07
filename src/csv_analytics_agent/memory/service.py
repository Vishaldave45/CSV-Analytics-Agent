"""High-level Memory Service wrapping BaseVectorStore and BaseEmbeddingProvider."""

from __future__ import annotations

import uuid
from pathlib import Path

from csv_analytics_agent.memory.base import BaseEmbeddingProvider, BaseVectorStore
from csv_analytics_agent.memory.faiss_store import (
    FaissVectorStore,
    SentenceTransformerEmbeddings,
)
from csv_analytics_agent.memory.models import (
    MemoryMetadata,
    MemoryRecord,
    MemorySearchResult,
    MetadataValue,
)


class MemoryService:
    """Infrastructure service providing high-level vector storage and similarity retrieval.

    MemoryService coordinates BaseEmbeddingProvider and BaseVectorStore to convert plain text
    into embeddings and manage vector indices for column retrieval, conversation memory, and RAG.
    """

    def __init__(
        self,
        vector_store: BaseVectorStore | None = None,
        embedding_provider: BaseEmbeddingProvider | None = None,
    ) -> None:
        """Initialize MemoryService with vector store and embedding provider dependencies.

        Args:
            vector_store: Vector store instance (defaults to FaissVectorStore).
            embedding_provider: Embedding provider instance (SentenceTransformerEmbeddings).
        """
        self._embedding_provider = embedding_provider or SentenceTransformerEmbeddings()
        self._vector_store = vector_store or FaissVectorStore(
            dimension=self._embedding_provider.dimension,
            embedding_model=self._embedding_provider.model_name,
        )

    @property
    def metadata(self) -> MemoryMetadata:
        """Return memory collection metadata."""
        return self._vector_store.metadata

    def store(
        self,
        text: str,
        metadata: dict[str, MetadataValue] | None = None,
        record_id: str | None = None,
    ) -> MemoryRecord:
        """Store a single text snippet in vector memory.

        Args:
            text: Plain text content to store.
            metadata: Optional metadata payload.
            record_id: Optional custom record ID (auto-generates UUID if None).

        Returns:
            Created and indexed MemoryRecord.
        """
        if not text or not text.strip():
            raise ValueError("Cannot store empty or whitespace-only text.")

        rec_id = record_id or f"mem_{uuid.uuid4().hex[:12]}"
        embedding = self._embedding_provider.embed_text(text)

        record = MemoryRecord(
            id=rec_id,
            text=text,
            embedding=embedding,
            metadata=metadata or {},
        )
        self._vector_store.add([record])
        return record

    def store_batch(
        self,
        items: list[tuple[str, dict[str, MetadataValue] | None]],
    ) -> list[MemoryRecord]:
        """Store a batch of (text, metadata) tuples in vector memory.

        Args:
            items: List of (text, metadata_dict) tuples.

        Returns:
            List of created and indexed MemoryRecord objects.
        """
        if not items:
            return []

        texts = [text for text, _ in items]
        embeddings = self._embedding_provider.embed_documents(texts)

        records: list[MemoryRecord] = []
        for (text, meta), emb in zip(items, embeddings, strict=False):
            rec_id = f"mem_{uuid.uuid4().hex[:12]}"
            rec = MemoryRecord(
                id=rec_id,
                text=text,
                embedding=emb,
                metadata=meta or {},
            )
            records.append(rec)

        self._vector_store.add(records)
        return records

    def retrieve(self, query_text: str, top_k: int = 5) -> list[MemorySearchResult]:
        """Retrieve top_k nearest neighbor memory records for a query string.

        Args:
            query_text: Natural language or column query string.
            top_k: Maximum number of nearest neighbor results to return.

        Returns:
            List of MemorySearchResult objects sorted by similarity.
        """
        if not query_text or not query_text.strip():
            return []

        query_vector = self._embedding_provider.embed_text(query_text)
        return self._vector_store.search(query_vector, top_k=top_k)

    def delete(self, record_ids: list[str]) -> None:
        """Delete records from memory by ID list.

        Args:
            record_ids: List of record ID strings to remove.
        """
        self._vector_store.delete(record_ids)

    def reset(self) -> None:
        """Clear all stored vector records."""
        self._vector_store.clear()

    def count(self) -> int:
        """Return total count of stored records in memory."""
        return self._vector_store.count()

    def persist(self, path: Path | str) -> None:
        """Persist vector index to disk.

        Args:
            path: Directory path for persistence.
        """
        self._vector_store.persist(path)

    def load(self, path: Path | str) -> None:
        """Load vector index from disk.

        Args:
            path: Directory path to load from.
        """
        self._vector_store.load(path)


__all__ = ["MemoryService"]
