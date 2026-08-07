"""Unit tests for Stage 7.2 LangChain Tool Adapter."""

import pandas as pd
import pytest
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ValidationError

from csv_analytics_agent.execution.domain.analytics import AnalyticsEngine
from csv_analytics_agent.execution.models import ExecutionResult, ExecutionStatus
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.adapter import as_langchain_tool, as_langchain_tools


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "salary": [50000.0, 60000.0, 70000.0],
            "department": ["HR", "IT", "Sales"],
        }
    )


@pytest.fixture
def configured_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    engine = AnalyticsEngine()
    for desc in engine.list_capabilities():
        registry.register(desc, engine)
    return registry


def test_as_langchain_tools_generation(
    sample_df: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    engine = AnalyticsEngine()
    descriptors = engine.list_capabilities()

    tools = as_langchain_tools(descriptors, configured_registry, sample_df)
    assert len(tools) == len(descriptors)
    assert all(isinstance(t, StructuredTool) for t in tools)

    names = [t.name for t in tools]
    assert "aggregate" in names
    assert "filter" in names
    assert "group" in names


def test_tool_metadata_propagation(
    sample_df: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    engine = AnalyticsEngine()
    desc = [d for d in engine.list_capabilities() if d.name == "aggregate"][0]

    tool = as_langchain_tool(desc, configured_registry, sample_df)
    assert tool.name == "aggregate"
    assert tool.description == desc.description
    assert issubclass(tool.args_schema, BaseModel)  # type: ignore[arg-type]


def test_tool_runtime_execution(
    sample_df: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    engine = AnalyticsEngine()
    desc = [d for d in engine.list_capabilities() if d.name == "aggregate"][0]

    tool = as_langchain_tool(desc, configured_registry, sample_df)

    # Invoke tool func directly
    assert tool.func is not None
    res = tool.func(target_columns=["salary"], parameters={"operation": "mean"})
    assert isinstance(res, ExecutionResult)
    assert res.status == ExecutionStatus.SUCCESS
    assert res.data == 60000.0


def test_tool_invalid_argument_validation(
    sample_df: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    engine = AnalyticsEngine()
    desc = [d for d in engine.list_capabilities() if d.name == "aggregate"][0]

    tool = as_langchain_tool(desc, configured_registry, sample_df)

    # Invoke with invalid target_columns type
    with pytest.raises((ValidationError, TypeError)):
        tool.invoke({"target_columns": "not_a_list"})
