"""Unit tests for Stage 7.6 LLM Planner Node."""

from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from csv_analytics_agent.execution.domain.analytics import AnalyticsEngine
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.planner import DEFAULT_MAX_ITERATIONS, planner_node
from csv_analytics_agent.graph.state import create_initial_state
from csv_analytics_agent.llm.base import BaseLLM


class MockLLM(BaseLLM):
    """Mock LLM implementation for testing planner node interactions."""

    def __init__(self, response_message: BaseMessage | None = None) -> None:
        self.bound_tools: list[Any] = []
        self.response_message = response_message or AIMessage(
            content="I will aggregate salary.",
            tool_calls=[
                {
                    "name": "aggregate",
                    "args": {"target_columns": ["salary"], "parameters": {"operation": "mean"}},
                    "id": "call_123",
                }
            ],
        )

    def bind_tools(self, tools: list[Any]) -> BaseLLM:
        new_llm = MockLLM(self.response_message)
        new_llm.bound_tools = tools
        return new_llm

    def invoke(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> BaseMessage:
        return self.response_message

    def stream(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> Any:
        yield self.response_message

    @property
    def model_name(self) -> str:
        return "mock_planner_llm"


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({"salary": [50000.0, 60000.0]})


@pytest.fixture
def configured_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    engine = AnalyticsEngine()
    for desc in engine.list_capabilities():
        registry.register(desc, engine)
    return registry


def test_planner_node_tool_binding_and_state_update(
    sample_df: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    mock_llm = MockLLM()
    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="What is the average salary?")
    state["messages"] = [msg]
    state["iteration_count"] = 0

    update = planner_node(state, mock_llm, configured_registry, sample_df)

    assert "messages" in update
    assert "iteration_count" in update
    assert update["iteration_count"] == 1

    emitted_msg = update["messages"][0]
    assert isinstance(emitted_msg, AIMessage)
    assert len(emitted_msg.tool_calls) == 1
    assert emitted_msg.tool_calls[0]["name"] == "aggregate"


def test_planner_node_max_iterations_loop_protection(
    sample_df: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    mock_llm = MockLLM()
    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="Infinite loop query")
    state["messages"] = [msg]
    state["iteration_count"] = DEFAULT_MAX_ITERATIONS

    update = planner_node(state, mock_llm, configured_registry, sample_df)

    assert update["iteration_count"] == DEFAULT_MAX_ITERATIONS + 1
    assert update["metadata"]["next_node"] == "explainer"
    assert update["metadata"]["loop_limit_exceeded"] is True
    assert "Maximum iteration limit" in update["messages"][0].content


def test_planner_node_does_not_execute_tools(
    sample_df: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    # Ensure registry get_engine or providers are not invoked during planning
    mock_registry = MagicMock(spec=CapabilityRegistry)
    engine = AnalyticsEngine()
    mock_registry.discover.return_value = engine.list_capabilities()
    mock_registry.get_engine.side_effect = AssertionError(
        "Planner node MUST NOT invoke registry.get_engine or execute capabilities directly!"
    )

    mock_llm = MockLLM()
    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="Calculate total revenue")
    state["messages"] = [msg]

    update = planner_node(state, mock_llm, mock_registry, sample_df)
    assert update["iteration_count"] == 1
    mock_registry.discover.assert_called_once()
    mock_registry.get_engine.assert_not_called()
