"""Unit tests for AnalysisArtifact and AnalysisResult domain models."""

import pytest
from pydantic import ValidationError

from csv_analytics_agent.python_engine.models import PythonArtifactType
from csv_analytics_agent.results.models import (
    AnalysisArtifact,
    AnalysisResult,
    AnalysisStatus,
)


def test_analysis_artifact_construction() -> None:
    """Verify AnalysisArtifact model instantiation and default fields."""
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.SCALAR,
        name="average_price",
        payload=42.5,
    )
    assert art.artifact_id != ""
    assert art.artifact_type == PythonArtifactType.SCALAR
    assert art.name == "average_price"
    assert art.payload == 42.5
    assert art.downloadable is False


def test_artifact_immutability() -> None:
    """Verify AnalysisArtifact is immutable."""
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.TEXT,
        name="summary",
        payload="Hello",
    )
    with pytest.raises(ValidationError):
        art.name = "new_name"  # type: ignore[misc]


def test_analysis_result_construction() -> None:
    """Verify AnalysisResult model instantiation and default fields."""
    res = AnalysisResult(
        status=AnalysisStatus.SUCCESS,
        narrative="Analysis successful.",
        source="python_engine",
    )
    assert res.status == AnalysisStatus.SUCCESS
    assert res.narrative == "Analysis successful."
    assert res.source == "python_engine"
    assert len(res.artifacts) == 0


def test_result_immutability() -> None:
    """Verify AnalysisResult is immutable."""
    res = AnalysisResult(narrative="Test")
    with pytest.raises(ValidationError):
        res.narrative = "Mutated"  # type: ignore[misc]


def test_analysis_result_failure_constructor() -> None:
    """Verify AnalysisResult.failure constructor produces FAILED status."""
    res = AnalysisResult.failure(
        error_type="TimeoutError",
        error_message="Execution exceeded limit.",
        source="python_engine",
        question="What is total sales?",
    )
    assert res.status == AnalysisStatus.FAILED
    assert res.error_type == "TimeoutError"
    assert res.error_message == "Execution exceeded limit."
    assert res.narrative == "Execution exceeded limit."
    assert res.source == "python_engine"


def test_analysis_result_partial_constructor() -> None:
    """Verify AnalysisResult.partial constructor produces PARTIAL status."""
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.SCALAR,
        name="sales",
        payload=100,
    )
    res = AnalysisResult.partial(
        artifacts=[art],
        error_type="ChartError",
        error_message="Failed to build chart.",
        narrative="Calculated scalar sales.",
    )
    assert res.status == AnalysisStatus.PARTIAL
    assert len(res.artifacts) == 1
    assert res.error_type == "ChartError"


def test_analysis_result_merge_both_success() -> None:
    """Verify merging two successful AnalysisResult instances."""
    art1 = AnalysisArtifact(
        artifact_type=PythonArtifactType.SCALAR,
        name="res1",
        payload=10,
    )
    art2 = AnalysisArtifact(
        artifact_type=PythonArtifactType.TABLE,
        name="res2",
        payload={"a": [1]},
    )

    r1 = AnalysisResult(
        status=AnalysisStatus.SUCCESS,
        narrative="First narrative",
        artifacts=[art1],
        source="engine1",
        execution_time_ms=100.0,
    )
    r2 = AnalysisResult(
        status=AnalysisStatus.SUCCESS,
        narrative="Second narrative",
        artifacts=[art2],
        source="engine2",
        execution_time_ms=200.0,
    )

    merged = r1.merge(r2)
    assert merged.status == AnalysisStatus.SUCCESS
    assert len(merged.artifacts) == 2
    assert "First narrative" in merged.narrative
    assert "Second narrative" in merged.narrative
    assert merged.execution_time_ms == 300.0
    assert merged.artifacts[0].artifact_id == art1.artifact_id
    assert merged.artifacts[1].artifact_id == art2.artifact_id


def test_analysis_result_merge_partial_status() -> None:
    """Verify merging SUCCESS and FAILED results in PARTIAL status."""
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.SCALAR,
        name="res1",
        payload=10,
    )
    r1 = AnalysisResult(status=AnalysisStatus.SUCCESS, artifacts=[art])
    r2 = AnalysisResult.failure("Error", "Chart failed")

    merged = r1.merge(r2)
    assert merged.status == AnalysisStatus.PARTIAL
    assert len(merged.artifacts) == 1
