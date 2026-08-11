"""Memory and vector store infrastructure package.

Optional heavy dependencies (FAISS, sentence-transformers) are imported
only when available so lightweight test environments can import this
package without installing optional native dependencies.
"""

from typing import Any

from csv_analytics_agent.memory.base import (
    BaseEmbeddingProvider,
    BaseVectorStore,
)
from csv_analytics_agent.memory.models import (
    MemoryMetadata,
    MemoryRecord,
    MemorySearchResult,
    MetadataValue,
)
from csv_analytics_agent.memory.service import MemoryService

# Optional FAISS-backed implementations. Import lazily to avoid hard
# dependency on native FAISS during tests or lightweight runs.
FaissVectorStore: type[Any] | None = None
SentenceTransformerEmbeddings: type[Any] | None = None

try:  # pragma: no cover - optional dependency
    from csv_analytics_agent.memory.faiss_store import (
        FaissVectorStore as _FaissVectorStore,
    )
    from csv_analytics_agent.memory.faiss_store import (
        SentenceTransformerEmbeddings as _SentenceTransformerEmbeddings,
    )

    FaissVectorStore = _FaissVectorStore
    SentenceTransformerEmbeddings = _SentenceTransformerEmbeddings
except Exception:  # pragma: no cover - optional dependency
    pass

__all__ = [
    "BaseEmbeddingProvider",
    "BaseVectorStore",
    "FaissVectorStore",
    "MemoryMetadata",
    "MemoryRecord",
    "MemorySearchResult",
    "MemoryService",
    "MetadataValue",
    "SentenceTransformerEmbeddings",
]
