"""Unit tests for Python and deterministic result converters."""

from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from csv_analytics_agent.execution.models import ExecutionResult, ExecutionStatus
from csv_analytics_agent.python_engine.models import (
    PythonArtifact,
    PythonArtifactType,
    PythonExecutionResult,
)
from csv_analytics_agent.results.converters import (
    dataframe_to_analysis_artifact,
    deterministic_result_to_analysis_result,
    matplotlib_figure_to_analysis_artifact,
    plotly_figure_to_analysis_artifact,
    python_artifact_to_analysis_artifact,
    python_result_to_analysis_result,
)
from csv_analytics_agent.results.models import AnalysisStatus


def test_python_artifact_to_analysis_artifact() -> None:
    """Verify python_artifact_to_analysis_artifact conversion."""
    py_art = PythonArtifact(
        artifact_type=PythonArtifactType.DATAFRAME,
        name="sales_df",
        mime_type="application/json",
        data=pd.DataFrame({"a": [1, 2]}),
        metadata={"custom": "value"},
    )
    analysis_art = python_artifact_to_analysis_artifact(py_art)
    assert analysis_art.artifact_type == PythonArtifactType.DATAFRAME
    assert analysis_art.name == "sales_df"
    assert analysis_art.metadata["custom"] == "value"
    assert analysis_art.downloadable is True


def test_python_result_to_analysis_result_success() -> None:
    """Verify python_result_to_analysis_result on successful execution."""
    py_res = PythonExecutionResult(
        success=True,
        stdout="Total revenue calculated.",
        stderr="",
        artifacts=[
            PythonArtifact(
                artifact_type=PythonArtifactType.SCALAR,
                name="total_revenue",
                data=5000.0,
            )
        ],
        execution_time_ms=45.2,
    )
    res = python_result_to_analysis_result(py_res, question="Total revenue?")
    assert res.status == AnalysisStatus.SUCCESS
    assert res.source == "python_engine"
    assert res.narrative == "Total revenue calculated."
    assert len(res.artifacts) == 1
    assert res.execution_time_ms == 45.2


def test_python_result_to_analysis_result_failure() -> None:
    """Verify python_result_to_analysis_result on failed execution."""
    py_res = PythonExecutionResult(
        success=False,
        stdout="",
        stderr="ZeroDivisionError",
        error_type="ZeroDivisionError",
        error_message="division by zero",
    )
    res = python_result_to_analysis_result(py_res)
    assert res.status == AnalysisStatus.FAILED
    assert res.error_type == "ZeroDivisionError"
    assert res.narrative == "division by zero"


def test_deterministic_result_to_analysis_result_dataframe() -> None:
    """Verify deterministic ExecutionResult wrapping DataFrame."""
    df = pd.DataFrame({"category": ["A", "B"], "count": [10, 20]})
    exec_res = ExecutionResult(
        capability_name="group_count",
        status=ExecutionStatus.SUCCESS,
        data=df,
        message="Count by category completed.",
    )
    res = deterministic_result_to_analysis_result(exec_res, capability_name="group_count")
    assert res.status == AnalysisStatus.SUCCESS
    assert res.source == "deterministic_engine"
    assert len(res.artifacts) == 1
    assert res.artifacts[0].artifact_type == PythonArtifactType.DATAFRAME


def test_deterministic_result_to_analysis_result_scalar() -> None:
    """Verify deterministic ExecutionResult wrapping scalar."""
    exec_res = ExecutionResult(
        capability_name="mean",
        status=ExecutionStatus.SUCCESS,
        data=123.45,
        message="Mean computed.",
    )
    res = deterministic_result_to_analysis_result(exec_res, capability_name="mean")
    assert res.status == AnalysisStatus.SUCCESS
    assert res.artifacts[0].artifact_type == PythonArtifactType.SCALAR
    assert res.artifacts[0].payload == 123.45


def test_dataframe_to_analysis_artifact() -> None:
    """Verify dataframe_to_analysis_artifact wrapper."""
    df = pd.DataFrame({"a": [1, 2, 3]})
    art = dataframe_to_analysis_artifact(df, name="custom_df", title="Custom Title")
    assert art.artifact_type == PythonArtifactType.DATAFRAME
    assert art.name == "custom_df"
    assert art.title == "Custom Title"
    assert art.metadata["row_count"] == 3


def test_matplotlib_figure_to_analysis_artifact() -> None:
    """Verify Matplotlib figure conversion to PNG image bytes artifact."""
    fig, ax = plt.subplots()
    ax.plot([1, 2], [3, 4])
    art = matplotlib_figure_to_analysis_artifact(fig, name="my_plot")
    plt.close(fig)

    assert art.artifact_type == PythonArtifactType.IMAGE
    assert art.mime_type == "image/png"
    assert isinstance(art.payload, bytes)
    assert len(art.payload) > 0


def test_plotly_figure_to_analysis_artifact() -> None:
    """Verify Plotly figure wrapper."""

    class DummyPlotlyFig:
        def __module__(self) -> str:
            return "plotly.graph_objects"

        def to_dict(self) -> dict[str, list[Any]]:
            return {"data": [], "layout": {}}

    fig = DummyPlotlyFig()
    art = plotly_figure_to_analysis_artifact(fig, name="plotly_fig")
    assert art.artifact_type == PythonArtifactType.INTERACTIVE
    assert art.mime_type == "application/json+plotly"
