"""Unit tests for Stage 7.4 FaissVectorStore."""

from pathlib import Path

import pytest

from csv_analytics_agent.memory.faiss_store import FaissVectorStore
from csv_analytics_agent.memory.models import MemoryRecord


def test_faiss_store_add_and_count() -> None:
    store = FaissVectorStore(collection_name="unit_test", dimension=2)
    assert store.count() == 0

    rec1 = MemoryRecord(id="r1", text="text1", embedding=[1.0, 0.0])
    rec2 = MemoryRecord(id="r2", text="text2", embedding=[0.0, 1.0])

    added = store.add([rec1, rec2])
    assert added == ["r1", "r2"]
    assert store.count() == 2
    assert store.metadata.record_count == 2


def test_faiss_store_search_ordering() -> None:
    store = FaissVectorStore(collection_name="unit_test", dimension=2)

    rec1 = MemoryRecord(id="r1", text="text1", embedding=[1.0, 0.0])
    rec2 = MemoryRecord(id="r2", text="text2", embedding=[10.0, 10.0])
    store.add([rec1, rec2])

    results = store.search([1.0, 0.1], top_k=2)
    assert len(results) == 2
    assert results[0].record.id == "r1"
    assert results[0].score < results[1].score


def test_faiss_store_delete_and_clear() -> None:
    store = FaissVectorStore(collection_name="unit_test", dimension=2)

    rec1 = MemoryRecord(id="r1", text="text1", embedding=[1.0, 0.0])
    rec2 = MemoryRecord(id="r2", text="text2", embedding=[0.0, 1.0])
    store.add([rec1, rec2])

    store.delete(["r1"])
    assert store.count() == 1

    remaining = store.search([0.0, 1.0], top_k=5)
    assert len(remaining) == 1
    assert remaining[0].record.id == "r2"

    store.clear()
    assert store.count() == 0


def test_faiss_store_persistence(tmp_path: Path) -> None:
    store = FaissVectorStore(collection_name="persist_col", dimension=2)
    rec = MemoryRecord(id="r1", text="persisted_text", embedding=[0.5, 0.5])
    store.add([rec])

    persist_dir = tmp_path / "faiss_test"
    store.persist(persist_dir)

    new_store = FaissVectorStore(collection_name="new_col", dimension=2)
    new_store.load(persist_dir)

    assert new_store.count() == 1
    res = new_store.search([0.5, 0.5], top_k=1)
    assert len(res) == 1
    assert res[0].record.text == "persisted_text"


def test_faiss_store_invalid_dimension() -> None:
    store = FaissVectorStore(dimension=2)
    bad_rec = MemoryRecord(id="bad", text="bad", embedding=[1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="requires vector of dimension 2"):
        store.add([bad_rec])
