"""Unit tests for Stage 7.5 Semantic Column Retrieval Node."""

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import BaseMessage, HumanMessage

from csv_analytics_agent.graph.retrieval import (
    EmptyQueryError,
    IndexNotFoundError,
    retrieval_node,
)
from csv_analytics_agent.graph.state import create_initial_state
from csv_analytics_agent.memory.models import MemoryRecord, MemorySearchResult
from csv_analytics_agent.memory.service import MemoryService


def test_retrieval_node_success() -> None:
    """Verify successful column retrieval from mocked MemoryService."""
    mock_memory = MagicMock(spec=MemoryService)
    mock_memory.count.return_value = 5

    rec1 = MemoryRecord(
        id="col_salary",
        text="salary",
        metadata={"column_name": "salary"},
    )
    rec2 = MemoryRecord(
        id="col_income",
        text="income",
        metadata={"column_name": "income"},
    )
    mock_memory.retrieve.return_value = [
        MemorySearchResult(record=rec1, score=0.1),
        MemorySearchResult(record=rec2, score=0.2),
    ]

    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="What is the average employee salary?")
    state["messages"] = [msg]

    update = retrieval_node(state, memory_service=mock_memory, top_k=2)

    assert "retrieved_columns" in update
    assert update["retrieved_columns"] == ["salary", "income"]
    mock_memory.retrieve.assert_called_once_with("What is the average employee salary?", top_k=2)


def test_retrieval_node_respects_top_k() -> None:
    """Verify top_k parameter is forwarded to MemoryService."""
    mock_memory = MagicMock(spec=MemoryService)
    mock_memory.count.return_value = 10
    mock_memory.retrieve.return_value = []

    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="Show revenue")
    state["messages"] = [msg]

    retrieval_node(state, memory_service=mock_memory, top_k=10)
    mock_memory.retrieve.assert_called_once_with("Show revenue", top_k=10)


def test_retrieval_node_empty_query_error() -> None:
    """Verify EmptyQueryError when message history has no user text."""
    mock_memory = MagicMock(spec=MemoryService)
    state = create_initial_state()

    with pytest.raises(EmptyQueryError, match="No valid human user query found"):
        retrieval_node(state, memory_service=mock_memory)

    msg_empty: BaseMessage = HumanMessage(content="   ")
    state["messages"] = [msg_empty]
    with pytest.raises(EmptyQueryError, match="No valid human user query found"):
        retrieval_node(state, memory_service=mock_memory)


def test_retrieval_node_index_not_found_error() -> None:
    """Verify IndexNotFoundError when MemoryService index is unpopulated."""
    mock_memory = MagicMock(spec=MemoryService)
    mock_memory.count.return_value = 0

    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="What is the average salary?")
    state["messages"] = [msg]

    with pytest.raises(IndexNotFoundError, match="Dataset column index is empty"):
        retrieval_node(state, memory_service=mock_memory)


def test_retrieval_node_fallback_text_when_metadata_missing() -> None:
    """Verify fallback to record.text when metadata column_name is missing."""
    mock_memory = MagicMock(spec=MemoryService)
    mock_memory.count.return_value = 1

    rec = MemoryRecord(id="col_raw", text="department_id", metadata={})
    mock_memory.retrieve.return_value = [MemorySearchResult(record=rec, score=0.05)]

    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="Group by department")
    state["messages"] = [msg]

    update = retrieval_node(state, memory_service=mock_memory)
    assert update["retrieved_columns"] == ["department_id"]
