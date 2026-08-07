"""Unit tests for visualization recommender engine."""

import pytest

from csv_analytics_agent.insights.models import Insight, InsightCategory, Severity
from csv_analytics_agent.profiler.models import (
    CategoricalStatistics,
    ColumnProfile,
    DatasetProfile,
    DatasetSummary,
    DatetimeStatistics,
    DuplicateSummary,
    MissingSummary,
    NumericStatistics,
)
from csv_analytics_agent.visualization import (
    ChartType,
    NoSuitableVisualizationError,
    VisualizationPlan,
    recommend_visualizations,
)


def _create_mock_profile(columns: list[ColumnProfile]) -> DatasetProfile:
    """Helper to generate a mock DatasetProfile with given columns."""
    return DatasetProfile(
        summary=DatasetSummary(row_count=100, column_count=len(columns), memory_usage_bytes=1024),
        columns=columns,
        missing=MissingSummary(total_missing_values=0, columns_with_missing=0),
        duplicates=DuplicateSummary(duplicate_rows=0),
    )


def test_recommend_visualizations_with_temporal_data() -> None:
    dt_col = ColumnProfile(
        name="date",
        dtype="datetime64[ns]",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=100,
        datetime=DatetimeStatistics(earliest="2026-01-01", latest="2026-12-31"),
    )
    num_col = ColumnProfile(
        name="sales",
        dtype="float64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=80,
        numeric=NumericStatistics(mean=1000.0),
    )
    profile = _create_mock_profile([dt_col, num_col])

    plan = recommend_visualizations(profile)
    assert isinstance(plan, VisualizationPlan)
    assert plan.primary.chart_type == ChartType.LINE
    assert plan.primary.x_axis.column == "date"
    assert len(plan.alternatives) > 0


def test_recommend_visualizations_categorical_only() -> None:
    cat_col = ColumnProfile(
        name="category",
        dtype="object",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=4,
        categorical=CategoricalStatistics(mode="Tech", category_count=4),
    )
    profile = _create_mock_profile([cat_col])

    plan = recommend_visualizations(profile)
    assert plan.primary.chart_type == ChartType.BAR
    assert plan.primary.x_axis.column == "category"


def test_recommend_visualizations_two_numeric_columns() -> None:
    num1 = ColumnProfile(
        name="height",
        dtype="float64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=50,
        numeric=NumericStatistics(mean=170.0),
    )
    num2 = ColumnProfile(
        name="weight",
        dtype="float64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=50,
        numeric=NumericStatistics(mean=70.0),
    )
    profile = _create_mock_profile([num1, num2])

    plan = recommend_visualizations(profile)
    assert plan.primary.chart_type == ChartType.SCATTER
    alt_types = [spec.chart_type for spec in plan.alternatives]
    assert ChartType.HISTOGRAM in alt_types or ChartType.HEATMAP in alt_types


def test_recommend_visualizations_with_optional_insights() -> None:
    cat_col = ColumnProfile(
        name="category",
        dtype="object",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=4,
        categorical=CategoricalStatistics(mode="Tech", category_count=4),
    )
    profile = _create_mock_profile([cat_col])
    insight = Insight(
        category=InsightCategory.GENERAL,
        severity=Severity.INFO,
        title="Sample Insight",
        description="Dataset summary",
        recommendation="No action needed",
    )

    plan = recommend_visualizations(profile, insights=[insight])
    assert plan.primary.chart_type == ChartType.BAR


def test_recommend_visualizations_empty_profile_raises_error() -> None:
    profile = _create_mock_profile([])
    with pytest.raises(NoSuitableVisualizationError):
        recommend_visualizations(profile)
