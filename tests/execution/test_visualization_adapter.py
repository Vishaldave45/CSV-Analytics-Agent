"""Unit tests for Phase 7 VisualizationEngine adapter."""

import pandas as pd
import pytest

from csv_analytics_agent.execution.domain.visualization import VisualizationEngine
from csv_analytics_agent.execution.models import (
    ExecutionRequest,
    ExecutionStatus,
)
from csv_analytics_agent.profiler.models import (
    ColumnProfile,
    DatasetProfile,
    DatasetSummary,
    DuplicateSummary,
    MissingSummary,
    NumericStatistics,
)
from csv_analytics_agent.visualization.models import (
    Axis,
    ChartSpecification,
    ChartType,
)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": [20, 30, 40, 50],
            "income": [40000.0, 50000.0, 60000.0, 70000.0],
        }
    )


@pytest.fixture
def sample_profile() -> DatasetProfile:
    return DatasetProfile(
        summary=DatasetSummary(row_count=4, column_count=2, memory_usage_bytes=512),
        columns=[
            ColumnProfile(
                name="age",
                dtype="int64",
                missing_count=0,
                missing_percentage=0.0,
                unique_count=4,
                numeric=NumericStatistics(mean=35.0),
            ),
            ColumnProfile(
                name="income",
                dtype="float64",
                missing_count=0,
                missing_percentage=0.0,
                unique_count=4,
                numeric=NumericStatistics(mean=55000.0),
            ),
        ],
        missing=MissingSummary(total_missing_values=0, columns_with_missing=0),
        duplicates=DuplicateSummary(duplicate_rows=0),
    )


def test_visualization_engine_recommend(
    sample_df: pd.DataFrame, sample_profile: DatasetProfile
) -> None:
    engine = VisualizationEngine()
    req = ExecutionRequest(
        capability_name="recommend_visualization",
        context_metadata={"profile": sample_profile},
    )
    res = engine.execute_capability(req, sample_df)
    assert res.status == ExecutionStatus.SUCCESS
    assert res.data is not None


def test_visualization_engine_render(sample_df: pd.DataFrame) -> None:
    engine = VisualizationEngine()
    spec = ChartSpecification(
        chart_type=ChartType.HISTOGRAM,
        title="Age Distribution",
        x_axis=Axis(column="age"),
        description="Histogram of ages",
    )
    req = ExecutionRequest(
        capability_name="render_visualization",
        parameters={"spec": spec},
    )
    res = engine.execute_capability(req, sample_df)
    assert res.status == ExecutionStatus.SUCCESS
    assert isinstance(res.data, bytes)
    assert len(res.data) > 0


def test_visualization_engine_render_flat_parameters(sample_df: pd.DataFrame) -> None:
    """Test render_visualization with top-level flat parameters from LLM."""
    engine = VisualizationEngine()
    req = ExecutionRequest(
        capability_name="render_visualization",
        parameters={
            "chart_type": "line",
            "x_axis": "age",
            "y_axis": "income",
            "title": "Income over Age",
        },
    )
    res = engine.execute_capability(req, sample_df)
    assert res.status == ExecutionStatus.SUCCESS
    assert isinstance(res.data, bytes)
    assert len(res.data) > 0


def test_visualization_engine_render_target_columns_fallback(sample_df: pd.DataFrame) -> None:
    """Test render_visualization with target_columns fallback."""
    engine = VisualizationEngine()
    req = ExecutionRequest(
        capability_name="render_visualization",
        target_columns=["age", "income"],
        parameters={"chart_type": "scatter"},
    )
    res = engine.execute_capability(req, sample_df)
    assert res.status == ExecutionStatus.SUCCESS
    assert isinstance(res.data, bytes)
    assert len(res.data) > 0


def test_visualization_engine_recommend_self_healing_profile(sample_df: pd.DataFrame) -> None:
    """Test recommend_visualization when profile is not in context metadata."""
    engine = VisualizationEngine()
    req = ExecutionRequest(capability_name="recommend_visualization")
    res = engine.execute_capability(req, sample_df)
    assert res.status == ExecutionStatus.SUCCESS
    assert res.data is not None
