"""Unit tests for visualization recommendation rules."""

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
from csv_analytics_agent.visualization.models import ChartType
from csv_analytics_agent.visualization.rules import (
    recommend_bar,
    recommend_categorical_rules,
    recommend_distribution_rules,
    recommend_histogram,
    recommend_line,
    recommend_relationship_rules,
    recommend_scatter,
    recommend_temporal_rules,
)


def _create_mock_profile(columns: list[ColumnProfile]) -> DatasetProfile:
    """Helper to generate a mock DatasetProfile with given columns."""
    return DatasetProfile(
        summary=DatasetSummary(row_count=100, column_count=len(columns), memory_usage_bytes=1024),
        columns=columns,
        missing=MissingSummary(total_missing_values=0, columns_with_missing=0),
        duplicates=DuplicateSummary(duplicate_rows=0),
    )


def test_recommend_histogram_success() -> None:
    num_col = ColumnProfile(
        name="salary",
        dtype="float64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=50,
        numeric=NumericStatistics(mean=50000.0, std=10000.0, min=20000.0, max=100000.0),
    )
    profile = _create_mock_profile([num_col])

    spec = recommend_histogram(profile)
    assert spec is not None
    assert spec.chart_type == ChartType.HISTOGRAM
    assert spec.x_axis.column == "salary"


def test_recommend_distribution_rules() -> None:
    num_col = ColumnProfile(
        name="income",
        dtype="float64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=30,
        numeric=NumericStatistics(mean=45000.0),
    )
    profile = _create_mock_profile([num_col])

    specs = recommend_distribution_rules(profile)
    assert len(specs) == 2
    types = [s.chart_type for s in specs]
    assert ChartType.HISTOGRAM in types
    assert ChartType.BOXPLOT in types


def test_recommend_bar_with_numeric() -> None:
    cat_col = ColumnProfile(
        name="region",
        dtype="object",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=4,
        categorical=CategoricalStatistics(mode="North", category_count=4),
    )
    num_col = ColumnProfile(
        name="sales",
        dtype="float64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=80,
        numeric=NumericStatistics(mean=100.0),
    )
    profile = _create_mock_profile([cat_col, num_col])

    spec = recommend_bar(profile)
    assert spec is not None
    assert spec.chart_type == ChartType.BAR
    assert spec.x_axis.column == "region"
    assert spec.y_axis is not None
    assert spec.y_axis.column == "sales"


def test_recommend_categorical_rules() -> None:
    cat_col = ColumnProfile(
        name="status",
        dtype="object",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=3,
        categorical=CategoricalStatistics(mode="active", category_count=3),
    )
    profile = _create_mock_profile([cat_col])

    specs = recommend_categorical_rules(profile)
    assert len(specs) == 2
    types = [s.chart_type for s in specs]
    assert ChartType.BAR in types
    assert ChartType.PIE in types


def test_recommend_line_success() -> None:
    dt_col = ColumnProfile(
        name="date",
        dtype="datetime64[ns]",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=100,
        datetime=DatetimeStatistics(earliest="2026-01-01", latest="2026-12-31"),
    )
    num_col = ColumnProfile(
        name="revenue",
        dtype="float64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=90,
        numeric=NumericStatistics(mean=500.0),
    )
    profile = _create_mock_profile([dt_col, num_col])

    spec = recommend_line(profile)
    assert spec is not None
    assert spec.chart_type == ChartType.LINE
    assert spec.x_axis.column == "date"
    assert spec.y_axis is not None
    assert spec.y_axis.column == "revenue"

    specs = recommend_temporal_rules(profile)
    assert len(specs) == 1
    assert specs[0].chart_type == ChartType.LINE


def test_recommend_scatter_and_relationship_rules() -> None:
    num1 = ColumnProfile(
        name="height",
        dtype="float64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=40,
        numeric=NumericStatistics(mean=170.0),
    )
    num2 = ColumnProfile(
        name="weight",
        dtype="float64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=40,
        numeric=NumericStatistics(mean=70.0),
    )
    profile = _create_mock_profile([num1, num2])

    spec = recommend_scatter(profile)
    assert spec is not None
    assert spec.chart_type == ChartType.SCATTER

    specs = recommend_relationship_rules(profile)
    assert len(specs) == 2
    types = [s.chart_type for s in specs]
    assert ChartType.SCATTER in types
    assert ChartType.HEATMAP in types
