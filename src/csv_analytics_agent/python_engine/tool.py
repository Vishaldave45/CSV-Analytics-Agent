"""LangChain StructuredTool adapter exposing Python code sandbox execution to LLMs."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pandas as pd
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from csv_analytics_agent.llm.python_generator import BasePythonCodeGenerator
from csv_analytics_agent.profiler.models import DatasetProfile
from csv_analytics_agent.python_engine.base import BasePythonExecutor
from csv_analytics_agent.python_engine.errors import (
    PythonArtifactError,
    PythonExecutionError,
    PythonOutputLimitError,
    PythonTimeoutError,
    PythonValidationError,
)
from csv_analytics_agent.python_engine.models import (
    PythonArtifact,
    PythonArtifactType,
    PythonExecutionResult,
)

TOOL_NAME = "python_analysis"
TOOL_DESCRIPTION = (
    "Use this tool for open-ended Python data analysis, custom calculations, statistical tests, "
    "or advanced visualizations on the CSV dataset that cannot be handled by standard deterministic capabilities."
)


class PythonAnalysisInput(BaseModel):
    """Input argument model for the python_analysis LangChain StructuredTool."""

    model_config = ConfigDict(frozen=True)

    question: str = Field(
        ...,
        description="Detailed analytical question or data operation to execute via Python code.",
    )


def _summarize_artifact_for_tool(artifact: PythonArtifact) -> dict[str, Any]:
    """Serialize artifact into a bounded, LLM-safe metadata dictionary representation."""
    art_dict: dict[str, Any] = {
        "artifact_type": artifact.artifact_type.value,
        "name": artifact.name,
        "mime_type": artifact.mime_type,
    }

    if artifact.artifact_type in (PythonArtifactType.DATAFRAME, PythonArtifactType.TABLE):
        if isinstance(artifact.data, pd.DataFrame):
            df_val = artifact.data
            art_dict["row_count"] = len(df_val)
            art_dict["column_count"] = len(df_val.columns)
            art_dict["columns"] = list(df_val.columns)
            art_dict["preview"] = df_val.head(10).to_dict(orient="split")
        elif isinstance(artifact.data, dict):
            dict_data = artifact.data
            data_rows = dict_data.get("data", [])
            cols = dict_data.get("columns", [])
            art_dict["row_count"] = len(data_rows) if isinstance(data_rows, list) else 0
            art_dict["column_count"] = len(cols) if isinstance(cols, list) else 0
            art_dict["columns"] = cols
            if isinstance(data_rows, list):
                art_dict["preview"] = data_rows[:10]
            else:
                art_dict["preview"] = dict_data
        else:
            art_dict["summary"] = str(artifact.data)[:500]

    elif artifact.artifact_type == PythonArtifactType.IMAGE:
        size_bytes = len(artifact.data) if isinstance(artifact.data, bytes) else 0
        art_dict["size_bytes"] = size_bytes
        art_dict["summary"] = f"Rendered image graphic ({artifact.name}, {size_bytes} bytes)"

    elif artifact.artifact_type == PythonArtifactType.INTERACTIVE:
        art_dict["summary"] = f"Plotly interactive graphic specification ({artifact.name})"

    elif artifact.artifact_type in (PythonArtifactType.SCALAR, PythonArtifactType.TEXT):
        art_dict["value"] = artifact.data

    else:
        art_dict["summary"] = str(artifact.data)[:300]

    return art_dict


def serialize_execution_result(result: PythonExecutionResult) -> str:
    """Serialize PythonExecutionResult into a clean JSON string for ToolMessage consumption.

    Args:
        result: PythonExecutionResult output model.

    Returns:
        JSON string representation.
    """
    serialized_artifacts = [_summarize_artifact_for_tool(art) for art in result.artifacts]

    payload: dict[str, Any] = {
        "success": result.success,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "execution_time_ms": result.execution_time_ms,
        "error_type": result.error_type,
        "error_message": result.error_message,
        "artifacts": serialized_artifacts,
    }
    return json.dumps(payload)


class PythonAnalysisTool:
    """Dependency-injected wrapper building a LangChain StructuredTool for Python sandbox execution."""

    def __init__(
        self,
        generator: BasePythonCodeGenerator,
        executor: BasePythonExecutor,
        dataframe: pd.DataFrame,
        schema: DatasetProfile | None = None,
        retrieved_columns: list[str] | None = None,
        dataset_hash: str | None = None,
    ) -> None:
        """Initialize PythonAnalysisTool with runtime dependencies.

        Args:
            generator: BasePythonCodeGenerator instance.
            executor: BasePythonExecutor instance.
            dataframe: Target pandas DataFrame context.
            schema: Optional DatasetProfile metadata.
            retrieved_columns: Optional list of retrieved column strings.
            dataset_hash: Optional SHA-256 dataset hash string.
        """
        self._generator = generator
        self._executor = executor
        self._dataframe = dataframe
        self._schema = schema
        self._retrieved_columns = retrieved_columns or []
        self._dataset_hash = dataset_hash

    @property
    def generator(self) -> BasePythonCodeGenerator:
        """Return bound Python code generator."""
        return self._generator

    @property
    def executor(self) -> BasePythonExecutor:
        """Return bound Python sandbox executor."""
        return self._executor

    @property
    def dataframe(self) -> pd.DataFrame:
        """Return bound pandas DataFrame."""
        return self._dataframe

    def run(self, question: str) -> str:
        """Execute python analysis flow: generate request -> execute sandbox -> serialize result.

        Args:
            question: Analytical question query string.

        Returns:
            JSON string representation of execution result for ToolMessage.
        """
        from csv_analytics_agent.llm.python_models import PythonCodeGenerationError

        try:
            req = self._generator.generate(
                question=question,
                schema=self._schema,
                retrieved_columns=self._retrieved_columns,
                dataset_hash=self._dataset_hash,
            )
            res = self._executor.execute(req, self._dataframe)
            return serialize_execution_result(res)

        except (
            PythonCodeGenerationError,
            PythonValidationError,
            PythonTimeoutError,
            PythonOutputLimitError,
            PythonArtifactError,
            PythonExecutionError,
        ) as err:
            fail_payload = {
                "success": False,
                "stdout": "",
                "stderr": str(err),
                "execution_time_ms": 0.0,
                "error_type": type(err).__name__,
                "error_message": str(err),
                "artifacts": [],
            }
            return json.dumps(fail_payload)

        except Exception as exc:
            fail_payload = {
                "success": False,
                "stdout": "",
                "stderr": str(exc),
                "execution_time_ms": 0.0,
                "error_type": type(exc).__name__,
                "error_message": f"Python analysis tool execution failed: {exc}",
                "artifacts": [],
            }
            return json.dumps(fail_payload)

    def to_structured_tool(self) -> StructuredTool:
        """Construct LangChain StructuredTool instance bound to this tool runner.

        Returns:
            StructuredTool object ready for LLM tool binding.
        """

        def _tool_func(question: str) -> str:
            return self.run(question)

        return StructuredTool.from_function(
            func=_tool_func,
            name=TOOL_NAME,
            description=TOOL_DESCRIPTION,
            args_schema=PythonAnalysisInput,
        )


def create_python_analysis_tool(
    generator: BasePythonCodeGenerator,
    executor: BasePythonExecutor,
    dataframe: pd.DataFrame,
    schema: DatasetProfile | None = None,
    retrieved_columns: list[str] | None = None,
    dataset_hash: str | None = None,
) -> StructuredTool:
    """Factory helper constructing a LangChain StructuredTool for python analysis.

    Args:
        generator: BasePythonCodeGenerator instance.
        executor: BasePythonExecutor instance.
        dataframe: Target pandas DataFrame context.
        schema: Optional DatasetProfile metadata.
        retrieved_columns: Optional list of retrieved column strings.
        dataset_hash: Optional SHA-256 dataset hash string.

    Returns:
        Configured StructuredTool object.
    """
    tool_wrapper = PythonAnalysisTool(
        generator=generator,
        executor=executor,
        dataframe=dataframe,
        schema=schema,
        retrieved_columns=retrieved_columns,
        dataset_hash=dataset_hash,
    )
    return tool_wrapper.to_structured_tool()


__all__ = [
    "TOOL_DESCRIPTION",
    "TOOL_NAME",
    "PythonAnalysisInput",
    "PythonAnalysisTool",
    "create_python_analysis_tool",
    "serialize_execution_result",
]
