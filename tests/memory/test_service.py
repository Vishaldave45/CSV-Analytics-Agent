"""Unit tests for Stage 7.4 MemoryService."""

from pathlib import Path
from typing import Any

import pytest

from csv_analytics_agent.memory.base import BaseEmbeddingProvider
from csv_analytics_agent.memory.faiss_store import FaissVectorStore
from csv_analytics_agent.memory.service import MemoryService


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic mock embedding provider for unit tests."""

    def __init__(self, dimension: int = 4) -> None:
        self._dimension = dimension

    def embed_text(self, text: str) -> list[float]:
        val = float(len(text) % 10)
        return [val] * self._dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return "mock_minilm_v2"


@pytest.fixture
def mock_service() -> MemoryService:
    provider = MockEmbeddingProvider(dimension=4)
    store = FaissVectorStore(
        collection_name="test_service",
        dimension=4,
        embedding_model="mock_minilm_v2",
    )
    return MemoryService(vector_store=store, embedding_provider=provider)


def test_memory_service_store_and_retrieve(mock_service: MemoryService) -> None:
    rec = mock_service.store(
        text="Average salary in IT department",
        metadata={"column": "salary"},
        record_id="rec_sal",
    )
    assert rec.id == "rec_sal"
    assert mock_service.count() == 1

    results = mock_service.retrieve("salary", top_k=1)
    assert len(results) == 1
    assert results[0].record.id == "rec_sal"
    assert results[0].record.metadata["column"] == "salary"


def test_memory_service_store_batch(mock_service: MemoryService) -> None:
    items: list[tuple[str, dict[str, Any] | None]] = [
        ("revenue", {"type": "numeric"}),
        ("department", {"type": "categorical"}),
    ]
    recs = mock_service.store_batch(items)
    assert len(recs) == 2
    assert mock_service.count() == 2


def test_memory_service_delete_and_reset(mock_service: MemoryService) -> None:
    rec1 = mock_service.store("text one", record_id="r1")
    rec2 = mock_service.store("text two", record_id="r2")
    assert mock_service.count() == 2
    assert rec2.id == "r2"

    mock_service.delete([rec1.id])
    assert mock_service.count() == 1

    mock_service.reset()
    assert mock_service.count() == 0


def test_memory_service_empty_text_error(mock_service: MemoryService) -> None:
    with pytest.raises(ValueError, match="Cannot store empty"):
        mock_service.store("   ")


def test_memory_service_persistence(mock_service: MemoryService, tmp_path: Path) -> None:
    mock_service.store("Sample memory to persist", record_id="p1")
    save_dir = tmp_path / "mem_dir"

    mock_service.persist(save_dir)

    provider = MockEmbeddingProvider(dimension=4)
    new_store = FaissVectorStore(dimension=4)
    new_service = MemoryService(vector_store=new_store, embedding_provider=provider)

    new_service.load(save_dir)
    assert new_service.count() == 1
    res = new_service.retrieve("Sample memory to persist", top_k=1)
    assert len(res) == 1
    assert res[0].record.id == "p1"
