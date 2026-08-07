"""Unit tests for Stage 7.9 Graph Assembly & Build."""

from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest
from langchain_core.messages import AIMessage, BaseMessage

from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.build import (
    build_graph,
    route_after_planner,
    route_after_router,
)
from csv_analytics_agent.graph.router import RouterDecision, RouterIntent
from csv_analytics_agent.graph.state import create_initial_state
from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.memory.service import MemoryService


class MockLLM(BaseLLM):
    """Mock LLM implementation for testing build graph compilation."""

    def bind_tools(self, tools: list[Any]) -> BaseLLM:
        return self

    def invoke(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> BaseMessage:
        return AIMessage(content="Mock answer")

    def stream(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> Any:
        yield AIMessage(content="Mock stream")

    @property
    def model_name(self) -> str:
        return "mock_model"


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({"salary": [50000.0, 60000.0]})


def test_build_graph_compiles(sample_df: pd.DataFrame) -> None:
    """Verify build_graph returns a compiled StateGraph containing all nodes."""
    mock_llm = MockLLM()
    mock_registry = MagicMock(spec=CapabilityRegistry)
    mock_registry.discover.return_value = []
    mock_memory = MagicMock(spec=MemoryService)

    compiled = build_graph(
        llm=mock_llm,
        registry=mock_registry,
        memory_service=mock_memory,
        dataframe=sample_df,
    )
    assert compiled is not None

    # Verify node names in graph structure
    nodes = compiled.nodes
    assert "router" in nodes
    assert "retrieval" in nodes
    assert "planner" in nodes
    assert "tool" in nodes
    assert "explainer" in nodes
    assert "memory_update" in nodes
    assert "reset" in nodes


def test_route_after_router_conditional_decisions() -> None:
    """Verify conditional edge routing after router node."""
    dec_reset = RouterDecision(
        intent=RouterIntent.RESET,
        confidence=1.0,
        reason="Reset command",
        next_node="reset",
    )
    assert route_after_router(dec_reset) == "reset"

    dec_meta = RouterDecision(
        intent=RouterIntent.META,
        confidence=1.0,
        reason="Help command",
        next_node="meta",
    )
    assert route_after_router(dec_meta) == "explainer"

    dec_new = RouterDecision(
        intent=RouterIntent.NEW_QUERY,
        confidence=0.9,
        reason="New analytical query",
        next_node="retrieval",
    )
    assert route_after_router(dec_new) == "retrieval"


def test_route_after_planner_conditional_decisions() -> None:
    """Verify conditional edge routing after planner node based on tool calls."""
    state_no_tool = create_initial_state()
    state_no_tool["messages"] = [AIMessage(content="Just text answer.")]
    assert route_after_planner(state_no_tool) == "explainer"

    state_with_tool = create_initial_state()
    ai_tool_msg = AIMessage(
        content="Calling aggregate",
        tool_calls=[{"name": "aggregate", "args": {}, "id": "1"}],
    )
    state_with_tool["messages"] = [ai_tool_msg]
    assert route_after_planner(state_with_tool) == "tool"
