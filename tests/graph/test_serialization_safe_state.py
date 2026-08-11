"""Regression tests for LangGraph checkpoint-safe graph state."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from csv_analytics_agent.config.setting import Settings
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.checkpoint import (
    RuntimeArtifactStore,
    analysis_result_to_checkpoint,
)
from csv_analytics_agent.graph.runtime import AgentRuntime
from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.llm.python_generator import BasePythonCodeGenerator
from csv_analytics_agent.memory.service import MemoryService
from csv_analytics_agent.python_engine.base import BasePythonExecutor
from csv_analytics_agent.python_engine.models import (
    PythonArtifact,
    PythonArtifactType,
    PythonExecutionRequest,
    PythonExecutionResult,
)
from csv_analytics_agent.results.models import AnalysisArtifact, AnalysisResult


class NonSerializableFigure:
    """Small arbitrary object standing in for a Plotly figure."""

    def to_dict(self) -> dict[str, object]:
        return {"kind": "figure"}


def _checkpoint_config(thread_id: str) -> dict[str, dict[str, str]]:
    return {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_ns": "",
            "checkpoint_id": f"{thread_id}_cp",
        }
    }


def test_raw_analysis_result_rejected_but_checkpoint_representation_persists() -> None:
    """Prove MemorySaver accepts only the bounded checkpoint representation."""
    raw_result = AnalysisResult(
        narrative="Generated mixed artifacts.",
        source="python_engine",
        artifacts=[
            AnalysisArtifact(
                artifact_type=PythonArtifactType.DATAFRAME,
                name="detail_rows",
                payload=pd.DataFrame({"sales": [100, 200]}),
            ),
            AnalysisArtifact(
                artifact_type=PythonArtifactType.INTERACTIVE,
                name="sales_chart",
                payload=NonSerializableFigure(),
            ),
            AnalysisArtifact(
                artifact_type=PythonArtifactType.IMAGE,
                name="sales_png",
                mime_type="image/png",
                payload=b"\x89PNG\r\n\x1a\n",
            ),
        ],
    )

    with pytest.raises(TypeError):
        InMemorySaver().put_writes(
            _checkpoint_config("raw"),
            [("last_analysis_result", raw_result)],
            task_id="task_raw",
        )

    artifact_store = RuntimeArtifactStore()
    checkpoint_result = analysis_result_to_checkpoint(raw_result, artifact_store)

    InMemorySaver().put_writes(
        _checkpoint_config("safe"),
        [("last_analysis_result", checkpoint_result)],
        task_id="task_safe",
    )

    for artifact in checkpoint_result["artifacts"]:
        assert "payload" not in artifact
        assert artifact_store.get(artifact["artifact_id"]) is not None


class ToolCallingLLM(BaseLLM):
    """Fake LLM that calls python_analysis, then synthesizes after the ToolMessage."""

    def bind_tools(self, tools: list[Any]) -> BaseLLM:
        return self

    def invoke(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> BaseMessage:
        messages = input_data if isinstance(input_data, list) else []
        visible_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
        last_msg = visible_messages[-1] if visible_messages else None

        if isinstance(last_msg, ToolMessage):
            return AIMessage(content="Generated heavy artifacts.")

        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "python_analysis",
                    "args": {"question": "Show total sales with supporting artifacts."},
                    "id": "call_python_1",
                }
            ],
        )

    def stream(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> Any:
        yield self.invoke(input_data)

    @property
    def model_name(self) -> str:
        return "tool-calling-test-llm"


class HeavyArtifactGenerator(BasePythonCodeGenerator):
    """Fake generator for runtime serialization regression tests."""

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


class HeavyArtifactExecutor(BasePythonExecutor):
    """Fake executor returning payloads that must stay out of checkpoints."""

    @property
    def executor_name(self) -> str:
        return "heavy-artifact-test-executor"

    def execute(
        self,
        request: PythonExecutionRequest,
        dataframe: pd.DataFrame,
    ) -> PythonExecutionResult:
        return PythonExecutionResult(
            success=True,
            stdout="Generated heavy artifacts.",
            artifacts=[
                PythonArtifact(
                    artifact_type=PythonArtifactType.DATAFRAME,
                    name="sales_rows",
                    data=dataframe.copy(),
                ),
                PythonArtifact(
                    artifact_type=PythonArtifactType.INTERACTIVE,
                    name="sales_chart",
                    data=NonSerializableFigure(),
                ),
                PythonArtifact(
                    artifact_type=PythonArtifactType.IMAGE,
                    name="sales_png",
                    mime_type="image/png",
                    data=b"\x89PNG\r\n\x1a\n",
                ),
            ],
            execution_time_ms=3.0,
        )


def test_runtime_two_invokes_checkpoint_safe_with_heavy_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run two MemorySaver-backed turns with heavy artifacts and no database files."""
    monkeypatch.chdir(tmp_path)
    dataframe = pd.DataFrame({"sales": [100, 200], "region": ["East", "West"]})
    memory = MagicMock(spec=MemoryService)
    memory.count.return_value = 1
    memory.retrieve.return_value = [
        SimpleNamespace(record=SimpleNamespace(metadata={"column_name": "sales"}, text="sales"))
    ]

    runtime = AgentRuntime(
        llm=ToolCallingLLM(),
        registry=CapabilityRegistry(),
        memory_service=memory,
        dataframe=dataframe,
        python_generator=HeavyArtifactGenerator(),
        python_executor=HeavyArtifactExecutor(),
        settings=Settings(default_thread_id="serialization_safe"),
        checkpointer=InMemorySaver(),
    )

    first_state = runtime.run("Show total sales.", thread_id="serialization_safe")
    first_result = first_state["last_analysis_result"]
    assert first_result is not None
    assert all("payload" in artifact for artifact in first_result["artifacts"])

    checkpoint_snapshot = runtime._graph.get_state(
        {"configurable": {"thread_id": "serialization_safe"}}
    )
    checkpoint_result = checkpoint_snapshot.values["last_analysis_result"]
    assert checkpoint_result is not None
    assert all("payload" not in artifact for artifact in checkpoint_result["artifacts"])

    runtime.run("Show total sales again.", thread_id="serialization_safe")
    resumed = runtime.resume("serialization_safe")
    assert resumed["last_analysis_result"] is not None

    assert not list(tmp_path.glob("*.db"))
    assert not list(tmp_path.glob("*.sqlite*"))
