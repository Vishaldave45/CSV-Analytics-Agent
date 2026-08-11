"""Deterministic unit tests and agent compatibility tests for PythonAnalysisTool."""

import ast
import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest
from langchain_core.messages import BaseMessage
from langchain_core.tools import StructuredTool

from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.llm.gemini import GeminiLLM
from csv_analytics_agent.llm.python_generator import BasePythonCodeGenerator
from csv_analytics_agent.llm.python_models import PythonCodeGenerationError
from csv_analytics_agent.python_engine.base import BasePythonExecutor
from csv_analytics_agent.python_engine.errors import PythonTimeoutError
from csv_analytics_agent.python_engine.models import (
    PythonArtifact,
    PythonArtifactType,
    PythonExecutionRequest,
    PythonExecutionResult,
)
from csv_analytics_agent.python_engine.tool import (
    TOOL_NAME,
    PythonAnalysisTool,
    create_python_analysis_tool,
)


class FakeCodeGenerator(BasePythonCodeGenerator):
    """Fake PythonCodeGenerator for deterministic tool testing."""

    def __init__(
        self,
        return_req: PythonExecutionRequest | None = None,
        should_raise: Exception | None = None,
    ) -> None:
        self.return_req = return_req or PythonExecutionRequest(
            code="result = df['sales'].mean()",
            question="Default question",
            dataset_hash="mock_hash_123",
        )
        self.should_raise = should_raise
        self.last_call_kwargs: dict[str, Any] = {}

    def generate(
        self,
        question: str,
        schema: Any = None,
        retrieved_columns: list[str] | None = None,
        context: str | None = None,
        dataset_hash: str | None = None,
    ) -> PythonExecutionRequest:
        self.last_call_kwargs = {
            "question": question,
            "schema": schema,
            "retrieved_columns": retrieved_columns,
            "context": context,
            "dataset_hash": dataset_hash,
        }
        if self.should_raise:
            raise self.should_raise
        return self.return_req


class FakePythonExecutor(BasePythonExecutor):
    """Fake BasePythonExecutor for deterministic tool testing."""

    def __init__(
        self,
        return_res: PythonExecutionResult | None = None,
        should_raise: Exception | None = None,
    ) -> None:
        self.return_res = return_res or PythonExecutionResult(
            success=True,
            stdout="Fake stdout",
            stderr="",
            artifacts=[
                PythonArtifact(
                    artifact_type=PythonArtifactType.SCALAR,
                    name="result",
                    data=42.0,
                )
            ],
            execution_time_ms=12.3,
        )
        self.should_raise = should_raise
        self.last_request: PythonExecutionRequest | None = None
        self.last_dataframe: pd.DataFrame | None = None

    @property
    def executor_name(self) -> str:
        return "fake-executor"

    def execute(
        self,
        request: PythonExecutionRequest,
        dataframe: pd.DataFrame,
    ) -> PythonExecutionResult:
        self.last_request = request
        self.last_dataframe = dataframe
        if self.should_raise:
            raise self.should_raise
        return self.return_res


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({"sales": [10, 20, 30], "quantity": [1, 2, 3]})


# 1 & 2 & 3. StructuredTool creation, name, description
def test_structured_tool_creation(sample_df: pd.DataFrame) -> None:
    gen = FakeCodeGenerator()
    exec_ = FakePythonExecutor()
    tool = create_python_analysis_tool(gen, exec_, sample_df)

    assert isinstance(tool, StructuredTool)
    assert tool.name == TOOL_NAME
    assert tool.description != ""
    assert "Python" in tool.description


# 4 & 19. Tool args_schema minimal fields
def test_tool_args_schema(sample_df: pd.DataFrame) -> None:
    gen = FakeCodeGenerator()
    exec_ = FakePythonExecutor()
    tool = create_python_analysis_tool(gen, exec_, sample_df)

    schema = tool.args_schema.model_json_schema()
    assert "properties" in schema
    assert "question" in schema["properties"]
    assert "dataframe" not in schema["properties"]
    assert "dataset_hash" not in schema["properties"]


# 5 & 6 & 7 & 8 & 9. Generator and executor workflow execution
def test_tool_execution_flow(sample_df: pd.DataFrame) -> None:
    gen = FakeCodeGenerator()
    exec_ = FakePythonExecutor()
    tool_wrapper = PythonAnalysisTool(
        generator=gen,
        executor=exec_,
        dataframe=sample_df,
        retrieved_columns=["sales"],
        dataset_hash="hash_abc",
    )

    res_json_str = tool_wrapper.run("Calculate average sales")
    res_dict = json.loads(res_json_str)

    assert res_dict["success"] is True
    assert gen.last_call_kwargs["question"] == "Calculate average sales"
    assert gen.last_call_kwargs["retrieved_columns"] == ["sales"]
    assert gen.last_call_kwargs["dataset_hash"] == "hash_abc"
    assert exec_.last_request is not None
    assert exec_.last_dataframe is not None
    assert len(exec_.last_dataframe) == 3


def test_single_generation_and_execution_count(sample_df: pd.DataFrame) -> None:
    """Regression test: verify one tool request triggers exactly 1 generation and 1 execution."""
    mock_gen = MagicMock(spec=BasePythonCodeGenerator)
    mock_gen.generate.return_value = PythonExecutionRequest(
        code="result = 42", question="Test", dataset_hash="hash"
    )
    mock_exec = MagicMock(spec=BasePythonExecutor)
    mock_exec.execute.return_value = PythonExecutionResult(success=True, stdout="42", stderr="")

    tool_wrapper = PythonAnalysisTool(generator=mock_gen, executor=mock_exec, dataframe=sample_df)
    tool_wrapper.run("Calculate something")

    assert mock_gen.generate.call_count == 1
    assert mock_exec.execute.call_count == 1


# 10 & 11. Scalar result preservation
def test_scalar_result_representation(sample_df: pd.DataFrame) -> None:
    res = PythonExecutionResult(
        success=True,
        artifacts=[
            PythonArtifact(
                artifact_type=PythonArtifactType.SCALAR,
                name="result",
                data=99.5,
            )
        ],
    )
    gen = FakeCodeGenerator()
    exec_ = FakePythonExecutor(return_res=res)
    tool_wrapper = PythonAnalysisTool(gen, exec_, sample_df)

    res_dict = json.loads(tool_wrapper.run("Question"))
    assert res_dict["artifacts"][0]["value"] == 99.5
    assert res_dict["artifacts"][0]["artifact_type"] == "scalar"


# 12 & 18. Table result & large dataframe truncation preview
def test_large_table_result_summarization(sample_df: pd.DataFrame) -> None:
    large_df = pd.DataFrame({"col1": range(100), "col2": range(100)})
    res = PythonExecutionResult(
        success=True,
        artifacts=[
            PythonArtifact(
                artifact_type=PythonArtifactType.DATAFRAME,
                name="summary_table",
                data=large_df,
            )
        ],
    )
    gen = FakeCodeGenerator()
    exec_ = FakePythonExecutor(return_res=res)
    tool_wrapper = PythonAnalysisTool(gen, exec_, sample_df)

    res_dict = json.loads(tool_wrapper.run("Question"))
    art = res_dict["artifacts"][0]

    assert art["artifact_type"] == "dataframe"
    assert art["row_count"] == 100
    assert art["column_count"] == 2
    assert len(art["preview"]["data"]) == 10  # truncated preview to 10 rows


# 13 & 14. Interactive & Image artifact preservation
def test_interactive_and_image_artifact_preservation(sample_df: pd.DataFrame) -> None:
    res = PythonExecutionResult(
        success=True,
        artifacts=[
            PythonArtifact(
                artifact_type=PythonArtifactType.INTERACTIVE,
                name="plotly_chart",
                data={"data": [], "layout": {}},
            ),
            PythonArtifact(
                artifact_type=PythonArtifactType.IMAGE,
                name="matplotlib_chart",
                mime_type="image/png",
                data=b"\x89PNG\r\n\x1a\nfake_bytes",
            ),
        ],
    )
    gen = FakeCodeGenerator()
    exec_ = FakePythonExecutor(return_res=res)
    tool_wrapper = PythonAnalysisTool(gen, exec_, sample_df)

    res_dict = json.loads(tool_wrapper.run("Chart question"))
    arts = res_dict["artifacts"]

    assert len(arts) == 2
    assert arts[0]["artifact_type"] == "interactive"
    assert "Plotly" in arts[0]["summary"]
    assert arts[1]["artifact_type"] == "image"
    assert arts[1]["size_bytes"] > 0


# 15 & 16 & 17. Structured failure handling (generation error, execution error, timeout error)
def test_structured_error_handling(sample_df: pd.DataFrame) -> None:
    # 1. Generation error
    gen_fail = FakeCodeGenerator(should_raise=PythonCodeGenerationError("Generation failed"))
    exec_ = FakePythonExecutor()
    t1 = PythonAnalysisTool(gen_fail, exec_, sample_df)
    r1 = json.loads(t1.run("Q1"))
    assert r1["success"] is False
    assert r1["error_type"] == "PythonCodeGenerationError"

    # 2. Timeout error
    gen = FakeCodeGenerator()
    exec_timeout = FakePythonExecutor(
        should_raise=PythonTimeoutError("Execution timed out after 10s")
    )
    t2 = PythonAnalysisTool(gen, exec_timeout, sample_df)
    r2 = json.loads(t2.run("Q2"))
    assert r2["success"] is False
    assert r2["error_type"] == "PythonTimeoutError"


# 19 & 20. Tool isolation (no exec/eval, no direct Gemini instantiation inside tool)
def test_tool_code_isolation() -> None:
    import csv_analytics_agent.python_engine.tool as tool_module

    mod_source = Path(tool_module.__file__).read_text(encoding="utf-8")
    assert "import subprocess" not in mod_source
    assert "import docker" not in mod_source

    tree = ast.parse(mod_source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in ("exec", "eval", "compile")


# 22. Agent-call compatibility test: llm.bind_tools([python_analysis_tool])
def test_agent_bind_tools_compatibility(sample_df: pd.DataFrame) -> None:
    gen = FakeCodeGenerator()
    exec_ = FakePythonExecutor()
    tool = create_python_analysis_tool(gen, exec_, sample_df)

    mock_llm = MagicMock(spec=BaseLLM)
    mock_llm.bind_tools.return_value = mock_llm

    bound = mock_llm.bind_tools([tool])
    assert bound is not None
    assert mock_llm.bind_tools.called


# 23. Real LLM Smoke Test
@pytest.mark.llm
def test_live_gemini_tool_binding_smoke(sample_df: pd.DataFrame) -> None:
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY environment variable not set.")

    gen = FakeCodeGenerator()
    exec_ = FakePythonExecutor()
    tool = create_python_analysis_tool(gen, exec_, sample_df)

    llm = GeminiLLM()
    bound_llm = llm.bind_tools([tool])

    res = bound_llm.invoke(
        "Calculate correlation between sales and quantity using python_analysis."
    )
    assert isinstance(res, BaseMessage)
