"""Unit tests for Stage 7.8B Memory Update Node."""

from unittest.mock import MagicMock

from langchain_core.messages import BaseMessage, HumanMessage

from csv_analytics_agent.execution.models import ExecutionResult, ExecutionStatus
from csv_analytics_agent.graph.memory_update import memory_update_node
from csv_analytics_agent.graph.state import create_initial_state
from csv_analytics_agent.memory.service import MemoryService


def test_memory_update_node_stores_context() -> None:
    """Verify memory_update_node stores question and execution outcome into MemoryService."""
    mock_memory = MagicMock(spec=MemoryService)

    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="What is the average salary?")
    res: ExecutionResult[float] = ExecutionResult(
        capability_name="aggregate",
        status=ExecutionStatus.SUCCESS,
        message="Calculated mean salary.",
        data=77000.0,
    )
    state["messages"] = [msg]
    state["last_result"] = res

    update = memory_update_node(state, memory_service=mock_memory)
    assert update == {}

    mock_memory.store.assert_called_once()
    call_kwargs = mock_memory.store.call_args.kwargs
    assert "Question: What is the average salary?" in call_kwargs["text"]
    assert "Capability: aggregate" in call_kwargs["text"]
    assert call_kwargs["metadata"]["capability"] == "aggregate"


def test_memory_update_node_no_op_when_last_result_missing() -> None:
    """Verify memory_update_node does not store when last_result is None."""
    mock_memory = MagicMock(spec=MemoryService)

    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="Hello")
    state["messages"] = [msg]
    state["last_result"] = None

    update = memory_update_node(state, memory_service=mock_memory)
    assert update == {}
    mock_memory.store.assert_not_called()
