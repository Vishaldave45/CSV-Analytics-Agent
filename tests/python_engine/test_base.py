"""Unit tests for BasePythonExecutor interface."""

import pandas as pd

from csv_analytics_agent.python_engine.base import BasePythonExecutor
from csv_analytics_agent.python_engine.models import (
    PythonArtifact,
    PythonArtifactType,
    PythonExecutionRequest,
    PythonExecutionResult,
)


class FakePythonExecutor(BasePythonExecutor):
    """Deterministic stub executor for testing BasePythonExecutor contract."""

    @property
    def executor_name(self) -> str:
        return "fake_python_executor"

    def execute(
        self,
        request: PythonExecutionRequest,
        dataframe: pd.DataFrame,
    ) -> PythonExecutionResult:
        artifact = PythonArtifact(
            artifact_type=PythonArtifactType.SCALAR,
            name="row_count",
            data=len(dataframe),
        )
        return PythonExecutionResult(
            success=True,
            stdout=f"Executed question: {request.question}",
            stderr="",
            artifacts=[artifact],
            execution_time_ms=1.5,
            metadata={"executor": self.executor_name},
        )


def test_base_python_executor_interface() -> None:
    """Verify FakePythonExecutor implements BasePythonExecutor contract."""
    executor = FakePythonExecutor()
    assert executor.executor_name == "fake_python_executor"

    req = PythonExecutionRequest(
        code="result = len(df)",
        question="How many rows?",
    )
    df = pd.DataFrame({"col1": [1, 2, 3]})

    result = executor.execute(req, df)

    assert isinstance(result, PythonExecutionResult)
    assert result.success is True
    assert "How many rows?" in result.stdout
    assert len(result.artifacts) == 1
    assert result.artifacts[0].data == 3
    assert result.metadata["executor"] == "fake_python_executor"
