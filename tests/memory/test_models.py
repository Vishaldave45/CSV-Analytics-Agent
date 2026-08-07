"""Unit tests for Stage 7.4 memory domain models."""

from csv_analytics_agent.memory.models import (
    MemoryMetadata,
    MemoryRecord,
    MemorySearchResult,
)


def test_memory_record_immutability() -> None:
    rec = MemoryRecord(
        id="rec_1",
        text="Sample text content",
        embedding=[0.1, 0.2, 0.3],
        metadata={"category": "test"},
    )
    assert rec.id == "rec_1"
    assert rec.text == "Sample text content"
    assert rec.embedding == [0.1, 0.2, 0.3]
    assert rec.metadata["category"] == "test"
    assert rec.timestamp > 0.0


def test_memory_search_result() -> None:
    rec = MemoryRecord(id="rec_1", text="Sample text content")
    res = MemorySearchResult(record=rec, score=0.05)

    assert res.record.id == "rec_1"
    assert res.score == 0.05


def test_memory_metadata() -> None:
    meta = MemoryMetadata(
        collection_name="test_col",
        embedding_model="mock_model",
        dimension=4,
        record_count=10,
    )
    assert meta.collection_name == "test_col"
    assert meta.dimension == 4
    assert meta.record_count == 10
