"""Domain models for Stage 7.4 Memory Service & Vector Store infrastructure.

This module defines immutable Pydantic v2 models for memory records, search results,
and vector collection metadata.
"""

from __future__ import annotations

import time

from pydantic import BaseModel, ConfigDict, Field

MetadataValue = str | int | float | bool


class MemoryRecord(BaseModel):
    """Immutable representation of a document or context snippet stored in memory.

    Attributes:
        id: Unique record identifier.
        text: Plain text content associated with the record.
        embedding: Vector embedding list of floats or None.
        metadata: Metadata key-value payload associated with the record.
        timestamp: Unix epoch timestamp recorded at creation.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., min_length=1, description="Unique record identifier.")
    text: str = Field(..., min_length=1, description="Plain text payload content.")
    embedding: list[float] | None = Field(
        default=None,
        description="Vector embedding float list.",
    )
    metadata: dict[str, MetadataValue] = Field(
        default_factory=dict,
        description="Arbitrary metadata key-value mapping.",
    )
    timestamp: float = Field(
        default_factory=time.time,
        description="Unix epoch creation timestamp.",
    )


class MemorySearchResult(BaseModel):
    """Immutable representation of a vector similarity search result.

    Attributes:
        record: Matched MemoryRecord instance.
        score: Similarity or distance score matching search query.
    """

    model_config = ConfigDict(frozen=True)

    record: MemoryRecord = Field(..., description="Matched memory record.")
    score: float = Field(..., description="Similarity distance score.")


class MemoryMetadata(BaseModel):
    """Immutable metadata describing a vector store collection state.

    Attributes:
        collection_name: Name of the vector store memory collection.
        embedding_model: Identifier of the embedding provider model.
        dimension: Vector embedding dimensionality integer.
        record_count: Total number of active records stored in collection.
        created_at: Epoch timestamp when collection was created.
    """

    model_config = ConfigDict(frozen=True)

    collection_name: str = Field(..., min_length=1, description="Collection name.")
    embedding_model: str = Field(..., min_length=1, description="Embedding model name.")
    dimension: int = Field(..., gt=0, description="Embedding vector dimension.")
    record_count: int = Field(default=0, ge=0, description="Total record count.")
    created_at: float = Field(default_factory=time.time, description="Creation epoch timestamp.")


__all__ = [
    "MemoryMetadata",
    "MemoryRecord",
    "MemorySearchResult",
    "MetadataValue",
]
