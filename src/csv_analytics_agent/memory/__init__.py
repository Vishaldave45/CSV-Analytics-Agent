"""Memory and vector store infrastructure package.

Optional heavy dependencies (FAISS, sentence-transformers) are imported
only when available so lightweight test environments can import this
package without installing optional native dependencies.
"""

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
try:  # pragma: no cover - optional dependency
    from csv_analytics_agent.memory.faiss_store import (
        FaissVectorStore,
        SentenceTransformerEmbeddings,
    )
except Exception:  # pragma: no cover - optional dependency
    FaissVectorStore = None  # type: ignore[assignment]
    SentenceTransformerEmbeddings = None  # type: ignore[assignment]

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
