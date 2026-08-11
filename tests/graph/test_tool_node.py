"""Unit tests for Stage 7.7 Tool Execution Node."""

import json

import pandas as pd
import pytest
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

from csv_analytics_agent.execution.domain.analytics import AnalyticsEngine
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.state import create_initial_state
from csv_analytics_agent.graph.tool_node import tool_node


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "salary": [50000.0, 60000.0, 70000.0],
            "age": [25, 30, 35],
        }
    )


@pytest.fixture
def configured_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    engine = AnalyticsEngine()
    for desc in engine.list_capabilities():
        registry.register(desc, engine)
    return registry


def test_tool_node_single_tool_execution(
    sample_df: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    state = create_initial_state()
    ai_msg = AIMessage(
        content="Aggregating salary.",
        tool_calls=[
            {
                "name": "aggregate",
                "args": {"target_columns": ["salary"], "parameters": {"operation": "mean"}},
                "id": "call_1",
            }
        ],
    )
    state["messages"] = [ai_msg]

    update = tool_node(state, configured_registry, sample_df)

    assert "messages" in update
    assert len(update["messages"]) == 1
    tool_msg = update["messages"][0]
    assert isinstance(tool_msg, ToolMessage)
    assert tool_msg.tool_call_id == "call_1"

    content = json.loads(tool_msg.content)
    assert content["capability"] == "aggregate"
    assert content["status"] == "success"
    assert content["data"] == "60000.0"

    assert update["last_analysis_result"] is not None
    assert update["last_analysis_result"]["status"] == "success"
    assert update["last_analysis_result"]["source"] == "deterministic_engine"
    assert "payload" not in update["last_analysis_result"]["artifacts"][0]


def test_tool_node_multiple_tool_calls_order_preserved(
    sample_df: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    state = create_initial_state()
    ai_msg = AIMessage(
        content="Executing mean and top 2.",
        tool_calls=[
            {
                "name": "aggregate",
                "args": {"target_columns": ["salary"], "parameters": {"operation": "mean"}},
                "id": "call_1",
            },
            {
                "name": "top_n",
                "args": {"target_columns": ["salary"], "parameters": {"n": 2}},
                "id": "call_2",
            },
        ],
    )
    state["messages"] = [ai_msg]

    update = tool_node(state, configured_registry, sample_df)

    assert len(update["messages"]) == 2
    msg1, msg2 = update["messages"][0], update["messages"][1]

    assert msg1.tool_call_id == "call_1"
    assert msg2.tool_call_id == "call_2"

    res1 = json.loads(msg1.content)
    res2 = json.loads(msg2.content)

    assert res1["capability"] == "aggregate"
    assert res2["capability"] == "top_n"


def test_tool_node_filter_capability_updates_active_filters(
    sample_df: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    state = create_initial_state()
    ai_msg = AIMessage(
        content="Filtering age older than 25.",
        tool_calls=[
            {
                "name": "filter",
                "args": {
                    "target_columns": ["age"],
                    "parameters": {"operator": "gt", "value": 25},
                },
                "id": "call_filter_1",
            }
        ],
    )
    state["messages"] = [ai_msg]

    update = tool_node(state, configured_registry, sample_df)

    assert "active_filters" in update
    assert len(update["active_filters"]) == 1
    assert update["active_filters"][0]["capability"] == "filter"


def test_tool_node_unknown_capability_handled(
    sample_df: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    state = create_initial_state()
    ai_msg = AIMessage(
        content="Attempting non-existent tool.",
        tool_calls=[
            {
                "name": "unsupported_magic_tool",
                "args": {},
                "id": "call_bad",
            }
        ],
    )
    state["messages"] = [ai_msg]

    update = tool_node(state, configured_registry, sample_df)

    assert len(update["messages"]) == 1
    tool_msg = update["messages"][0]
    content = json.loads(tool_msg.content)

    assert content["status"] == "failed"
    assert "not registered" in content["message"]
    assert update["last_analysis_result"]["status"] == "failed"
    assert update["last_analysis_result"]["source"] == "deterministic_engine"


def test_tool_node_no_tool_calls_returns_empty(
    sample_df: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    state = create_initial_state()
    msg: BaseMessage = AIMessage(content="Just text, no tool calls.")
    state["messages"] = [msg]

    update = tool_node(state, configured_registry, sample_df)
    assert update == {}
