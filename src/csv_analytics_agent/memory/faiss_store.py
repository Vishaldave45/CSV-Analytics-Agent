"""FAISS vector store implementation and SentenceTransformer embedding provider."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from csv_analytics_agent.memory.base import BaseEmbeddingProvider, BaseVectorStore
from csv_analytics_agent.memory.models import (
    MemoryMetadata,
    MemoryRecord,
    MemorySearchResult,
)


class SentenceTransformerEmbeddings(BaseEmbeddingProvider):
    """SentenceTransformer embedding provider using huggingface sentence-transformers."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        dimension: int = 384,
    ) -> None:
        """Initialize SentenceTransformerEmbeddings.

        Args:
            model_name: HuggingFace model identifier (default 'all-MiniLM-L6-v2').
            dimension: Dimension length of output embeddings (default 384).
        """
        self._model_name = model_name
        self._dimension = dimension
        self._model: Any = None

    def _get_model(self) -> Any:
        """Lazy load SentenceTransformer model when needed."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string into a vector float list.

        Args:
            text: Input text string.

        Returns:
            List of floats representing vector embedding.
        """
        model = self._get_model()
        vec = model.encode(text, convert_to_numpy=True)
        return [float(x) for x in vec.tolist()]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of text strings into vector float lists.

        Args:
            texts: List of input text strings.

        Returns:
            List of vector float lists.
        """
        if not texts:
            return []
        model = self._get_model()
        vecs = model.encode(texts, convert_to_numpy=True)
        return [[float(x) for x in row] for row in vecs.tolist()]

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name


class FaissVectorStore(BaseVectorStore):
    """FAISS vector store for high-performance L2 similarity search."""

    def __init__(
        self,
        collection_name: str = "default_collection",
        dimension: int = 384,
        embedding_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        """Initialize FaissVectorStore.

        Args:
            collection_name: Name of the memory collection.
            dimension: Embedding vector dimension length.
            embedding_model: Name of bound embedding provider.
        """
        self._collection_name = collection_name
        self._dimension = dimension
        self._embedding_model = embedding_model
        self._index: faiss.Index = faiss.IndexFlatL2(dimension)
        self._records: list[MemoryRecord] = []
        self._id_to_index: dict[str, int] = {}

    @property
    def metadata(self) -> MemoryMetadata:
        return MemoryMetadata(
            collection_name=self._collection_name,
            embedding_model=self._embedding_model,
            dimension=self._dimension,
            record_count=len(self._records),
        )

    def add(self, records: list[MemoryRecord]) -> list[str]:
        """Add records containing embeddings to the FAISS index.

        Args:
            records: List of MemoryRecord objects with populated embedding fields.

        Returns:
            List of record IDs successfully added.

        Raises:
            ValueError: If a record lacks an embedding vector.
        """
        if not records:
            return []

        added_ids: list[str] = []
        vectors: list[list[float]] = []

        for rec in records:
            if rec.embedding is None or len(rec.embedding) != self._dimension:
                err_msg = f"Record ID '{rec.id}' requires vector of dimension {self._dimension}."
                raise ValueError(err_msg)
            vectors.append(rec.embedding)
            self._id_to_index[rec.id] = len(self._records)
            self._records.append(rec)
            added_ids.append(rec.id)

        np_vectors = np.array(vectors, dtype=np.float32)
        self._index.add(np_vectors)
        return added_ids

    def search(self, query_vector: list[float], top_k: int = 5) -> list[MemorySearchResult]:
        """Perform nearest neighbor L2 similarity search.

        Args:
            query_vector: Float list embedding of the search query.
            top_k: Maximum number of results to return.

        Returns:
            List of MemorySearchResult objects sorted by score.
        """
        if len(self._records) == 0 or top_k <= 0:
            return []

        query_np = np.array([query_vector], dtype=np.float32)
        k_val = min(top_k, len(self._records))
        distances, indices = self._index.search(query_np, k_val)

        results: list[MemorySearchResult] = []
        for idx, dist in zip(indices[0], distances[0], strict=False):
            if 0 <= idx < len(self._records):
                record = self._records[int(idx)]
                results.append(MemorySearchResult(record=record, score=float(dist)))

        return results

    def delete(self, record_ids: list[str]) -> None:
        """Delete records matching record_ids and rebuild FAISS index.

        Args:
            record_ids: List of record ID strings to remove.
        """
        id_set = set(record_ids)
        remaining_records = [r for r in self._records if r.id not in id_set]

        self.clear()
        if remaining_records:
            self.add(remaining_records)

    def clear(self) -> None:
        """Clear all stored records and reset FAISS index."""
        self._index = faiss.IndexFlatL2(self._dimension)
        self._records = []
        self._id_to_index = {}

    def count(self) -> int:
        return len(self._records)

    def persist(self, path: Path | str) -> None:
        """Persist FAISS index and record metadata to disk.

        Args:
            path: Directory path for persistence.
        """
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)

        index_file = dir_path / "faiss.index"
        meta_file = dir_path / "records.json"

        faiss.write_index(self._index, str(index_file))

        records_data = [r.model_dump() for r in self._records]
        meta_payload = {
            "collection_name": self._collection_name,
            "dimension": self._dimension,
            "embedding_model": self._embedding_model,
            "records": records_data,
        }
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta_payload, f, indent=2)

    def load(self, path: Path | str) -> None:
        """Load FAISS index and record metadata from disk.

        Args:
            path: Directory path to load from.
        """
        dir_path = Path(path)
        index_file = dir_path / "faiss.index"
        meta_file = dir_path / "records.json"

        if not index_file.exists() or not meta_file.exists():
            raise FileNotFoundError(f"Persisted vector store files not found in '{path}'.")

        self._index = faiss.read_index(str(index_file))

        with open(meta_file, encoding="utf-8") as f:
            data = json.load(f)

        self._collection_name = data.get("collection_name", self._collection_name)
        self._dimension = data.get("dimension", self._dimension)
        self._embedding_model = data.get("embedding_model", self._embedding_model)

        self._records = [MemoryRecord(**r) for r in data.get("records", [])]
        self._id_to_index = {r.id: i for i, r in enumerate(self._records)}


__all__ = [
    "FaissVectorStore",
    "SentenceTransformerEmbeddings",
]
