"""Unit tests for Stage 8.7 unified agent routing & Python tool integration."""

from typing import Any
from unittest.mock import MagicMock

import pandas as pd
from langchain_core.messages import AIMessage, BaseMessage

from csv_analytics_agent.execution.domain.analytics import AnalyticsEngine
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.build import build_graph
from csv_analytics_agent.graph.planner import planner_node
from csv_analytics_agent.graph.state import create_initial_state
from csv_analytics_agent.graph.tool_node import tool_node
from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.llm.python_generator import BasePythonCodeGenerator
from csv_analytics_agent.python_engine.base import BasePythonExecutor
from csv_analytics_agent.python_engine.models import (
    PythonArtifact,
    PythonArtifactType,
    PythonExecutionRequest,
    PythonExecutionResult,
)


class FakeLLM(BaseLLM):
    """Fake BaseLLM for testing tool binding and planner invocation."""

    def __init__(self, response_msg: AIMessage | None = None) -> None:
        self.response_msg = response_msg or AIMessage(content="Direct response")
        self.bound_tools: list[Any] = []

    def bind_tools(self, tools: list[Any]) -> BaseLLM:
        self.bound_tools = list(tools)
        return self

    def invoke(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> BaseMessage:
        return self.response_msg

    def stream(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> Any:
        yield self.invoke(input_data)

    @property
    def model_name(self) -> str:
        return "fake-llm"


class FakeCodeGenerator(BasePythonCodeGenerator):
    """Fake BasePythonCodeGenerator for deterministic routing tests."""

    def generate(
        self,
        question: str,
        schema: Any = None,
        retrieved_columns: list[str] | None = None,
        context: str | None = None,
        dataset_hash: str | None = None,
    ) -> PythonExecutionRequest:
        return PythonExecutionRequest(
            code="result = df['sales'].sum()",
            question=question,
            dataset_hash=dataset_hash,
        )


class FakeExecutor(BasePythonExecutor):
    """Fake BasePythonExecutor for deterministic routing tests."""

    @property
    def executor_name(self) -> str:
        return "fake-executor"

    def execute(
        self,
        request: PythonExecutionRequest,
        dataframe: pd.DataFrame,
    ) -> PythonExecutionResult:
        return PythonExecutionResult(
            success=True,
            stdout="Total sales calculated.",
            artifacts=[
                PythonArtifact(
                    artifact_type=PythonArtifactType.SCALAR,
                    name="total_sales",
                    data=600,
                )
            ],
            execution_time_ms=5.0,
        )


def test_planner_binds_deterministic_and_python_tools() -> None:
    """Verify planner_node binds both deterministic tools and python_analysis tool."""
    df = pd.DataFrame({"sales": [10, 20, 30]})
    registry = CapabilityRegistry()
    engine = AnalyticsEngine()
    for desc in engine.list_capabilities():
        registry.register(desc, engine)

    fake_llm = FakeLLM()
    gen = FakeCodeGenerator()
    exec_ = FakeExecutor()

    state = create_initial_state()
    res_state = planner_node(
        state=state,
        llm=fake_llm,
        registry=registry,
        dataframe=df,
        python_generator=gen,
        python_executor=exec_,
    )

    assert "planner_result" in res_state
    # Check that tools were bound to LLM
    # Expect deterministic tools (6) + python_analysis (1) = 7 tools
    assert len(fake_llm.bound_tools) > 0
    tool_names = [t.name for t in fake_llm.bound_tools]
    assert "aggregate" in tool_names
    assert "python_analysis" in tool_names


def test_tool_node_executes_python_analysis_tool() -> None:
    """Verify tool_node handles python_analysis tool call and populates last_analysis_result."""
    df = pd.DataFrame({"sales": [100, 200, 300]})
    registry = CapabilityRegistry()
    gen = FakeCodeGenerator()
    exec_ = FakeExecutor()

    ai_msg = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "python_analysis",
                "args": {"question": "What is the total sales?"},
                "id": "call_py_123",
            }
        ],
    )

    state = create_initial_state()
    state["messages"] = [ai_msg]

    update = tool_node(
        state=state,
        registry=registry,
        dataframe=df,
        python_generator=gen,
        python_executor=exec_,
    )

    assert len(update["messages"]) == 1
    assert update["messages"][0].tool_call_id == "call_py_123"

    analysis_res = update.get("last_analysis_result")
    assert analysis_res is not None
    assert analysis_res["status"] == "success"
    assert analysis_res["source"] == "python_engine"
    assert len(analysis_res["artifacts"]) == 1
    assert analysis_res["artifacts"][0]["name"] == "total_sales"
    assert "payload" not in analysis_res["artifacts"][0]


def test_tool_node_executes_deterministic_tool() -> None:
    """Verify tool_node handles deterministic capability tool call and populates last_analysis_result."""
    df = pd.DataFrame({"sales": [10, 20, 30]})
    registry = CapabilityRegistry()
    engine = AnalyticsEngine()
    for desc in engine.list_capabilities():
        registry.register(desc, engine)

    ai_msg = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "aggregate",
                "args": {"target_columns": ["sales"], "parameters": {"operation": "mean"}},
                "id": "call_det_456",
            }
        ],
    )

    state = create_initial_state()
    state["messages"] = [ai_msg]

    update = tool_node(
        state=state,
        registry=registry,
        dataframe=df,
    )

    assert len(update["messages"]) == 1
    assert update["messages"][0].tool_call_id == "call_det_456"

    analysis_res = update.get("last_analysis_result")
    assert analysis_res is not None
    assert analysis_res["status"] == "success"
    assert analysis_res["source"] == "deterministic_engine"
    assert len(analysis_res["artifacts"]) == 1


def test_build_graph_with_python_dependencies() -> None:
    """Verify build_graph compiles cleanly with python generator and executor."""
    df = pd.DataFrame({"a": [1]})
    registry = CapabilityRegistry()
    mem_service = MagicMock()
    fake_llm = FakeLLM()
    gen = FakeCodeGenerator()
    exec_ = FakeExecutor()

    graph = build_graph(
        llm=fake_llm,
        registry=registry,
        memory_service=mem_service,
        dataframe=df,
        python_generator=gen,
        python_executor=exec_,
    )
    assert graph is not None
