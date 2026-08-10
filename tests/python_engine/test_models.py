"""Unit tests for Python engine domain models."""

import pandas as pd
import pytest
from pydantic import ValidationError

from csv_analytics_agent.python_engine.models import (
    PythonArtifact,
    PythonArtifactType,
    PythonExecutionRequest,
    PythonExecutionResult,
)


def test_valid_python_execution_request() -> None:
    """Verify valid PythonExecutionRequest construction and defaults."""
    req = PythonExecutionRequest(
        code="result = df['sales'].sum()",
        question="What is total sales?",
        dataset_hash="a1b2c3d4",
    )
    assert req.code == "result = df['sales'].sum()"
    assert req.question == "What is total sales?"
    assert req.dataset_hash == "a1b2c3d4"
    assert req.timeout_seconds == 30.0
    assert req.max_output_bytes == 10_000_000
    assert req.metadata == {}


def test_empty_code_rejected() -> None:
    """Verify empty or whitespace-only code raises ValidationError."""
    with pytest.raises(ValidationError, match="Field must not be empty"):
        PythonExecutionRequest(code="", question="What is total sales?")

    with pytest.raises(ValidationError, match="Field must not be empty"):
        PythonExecutionRequest(code="   \n  ", question="What is total sales?")


def test_empty_question_rejected() -> None:
    """Verify empty or whitespace-only question raises ValidationError."""
    with pytest.raises(ValidationError, match="Field must not be empty"):
        PythonExecutionRequest(code="x = 1", question="")

    with pytest.raises(ValidationError, match="Field must not be empty"):
        PythonExecutionRequest(code="x = 1", question=" \t ")


def test_invalid_timeout_rejected() -> None:
    """Verify non-positive timeout_seconds raises ValidationError."""
    with pytest.raises(ValidationError, match="timeout_seconds must be greater than 0"):
        PythonExecutionRequest(code="x = 1", question="calc", timeout_seconds=0.0)

    with pytest.raises(ValidationError, match="timeout_seconds must be greater than 0"):
        PythonExecutionRequest(code="x = 1", question="calc", timeout_seconds=-5.0)


def test_invalid_max_output_bytes_rejected() -> None:
    """Verify non-positive max_output_bytes raises ValidationError."""
    with pytest.raises(ValidationError, match="max_output_bytes must be greater than 0"):
        PythonExecutionRequest(code="x = 1", question="calc", max_output_bytes=0)

    with pytest.raises(ValidationError, match="max_output_bytes must be greater than 0"):
        PythonExecutionRequest(code="x = 1", question="calc", max_output_bytes=-100)


def test_request_is_immutable() -> None:
    """Verify PythonExecutionRequest fields cannot be mutated post-creation."""
    req = PythonExecutionRequest(code="x = 1", question="calc")
    with pytest.raises(ValidationError):
        req.code = "x = 2"  # type: ignore[misc]


def test_artifact_construction() -> None:
    """Verify PythonArtifact construction with various payload types."""
    df_payload = pd.DataFrame({"a": [1, 2]})
    art_df = PythonArtifact(
        artifact_type=PythonArtifactType.DATAFRAME,
        name="sales_table",
        mime_type="text/csv",
        data=df_payload,
    )
    assert art_df.artifact_type == PythonArtifactType.DATAFRAME
    assert art_df.name == "sales_table"
    assert art_df.mime_type == "text/csv"
    assert isinstance(art_df.data, pd.DataFrame)

    art_plot = PythonArtifact(
        artifact_type=PythonArtifactType.INTERACTIVE,
        name="plotly_chart",
        data={"data": [], "layout": {}},
    )
    assert art_plot.artifact_type == PythonArtifactType.INTERACTIVE

    art_bytes = PythonArtifact(
        artifact_type=PythonArtifactType.IMAGE,
        name="chart_png",
        mime_type="image/png",
        data=b"\x89PNG...",
    )
    assert art_bytes.data == b"\x89PNG..."


def test_result_construction() -> None:
    """Verify PythonExecutionResult construction for successful execution."""
    art = PythonArtifact(
        artifact_type=PythonArtifactType.SCALAR,
        name="sum_result",
        data=42.0,
    )
    res = PythonExecutionResult(
        success=True,
        stdout="Calculated sum\n",
        stderr="",
        artifacts=[art],
        execution_time_ms=12.5,
    )
    assert res.success is True
    assert res.stdout == "Calculated sum\n"
    assert len(res.artifacts) == 1
    assert res.artifacts[0].data == 42.0
    assert res.execution_time_ms == 12.5
    assert res.error_type is None
    assert res.error_message is None


def test_result_execution_time_cannot_be_negative() -> None:
    """Verify negative execution_time_ms raises ValidationError."""
    with pytest.raises(ValidationError, match="execution_time_ms must be non-negative"):
        PythonExecutionResult(success=True, execution_time_ms=-1.0)


def test_failed_result_can_contain_error_information() -> None:
    """Verify failed PythonExecutionResult captures error_type and error_message."""
    res = PythonExecutionResult(
        success=False,
        stdout="",
        stderr="ZeroDivisionError: division by zero",
        execution_time_ms=5.0,
        error_type="ZeroDivisionError",
        error_message="division by zero",
    )
    assert res.success is False
    assert res.error_type == "ZeroDivisionError"
    assert res.error_message == "division by zero"


def test_default_artifacts_are_independent_per_instance() -> None:
    """Verify default artifacts list is fresh per instance."""
    res1 = PythonExecutionResult(success=True)
    res2 = PythonExecutionResult(success=True)
    assert res1.artifacts is not res2.artifacts


def test_metadata_accepts_documented_primitive_values() -> None:
    """Verify metadata accepts str, int, float, and bool values."""
    req = PythonExecutionRequest(
        code="x = 1",
        question="calc",
        metadata={
            "str_key": "val",
            "int_key": 100,
            "float_key": 3.14,
            "bool_key": True,
        },
    )
    assert req.metadata["str_key"] == "val"
    assert req.metadata["int_key"] == 100
    assert req.metadata["float_key"] == 3.14
    assert req.metadata["bool_key"] is True

    res = PythonExecutionResult(
        success=True,
        metadata={
            "tag": "test",
            "retries": 0,
            "score": 0.99,
            "cached": False,
        },
    )
    assert res.metadata["tag"] == "test"
    assert res.metadata["retries"] == 0
    assert res.metadata["score"] == 0.99
    assert res.metadata["cached"] is False
