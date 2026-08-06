"""Unit tests for missing values business rule evaluation."""

from csv_analytics_agent.insights.models import InsightCategory, Severity
from csv_analytics_agent.insights.rules.missing import (
    HIGH_MISSING_THRESHOLD,
    MEDIUM_MISSING_THRESHOLD,
    check_missing_values,
)
from csv_analytics_agent.profiler.models import (
    ColumnProfile,
    DatasetProfile,
    DatasetSummary,
    DuplicateSummary,
    MissingSummary,
    NumericStatistics,
)


def _make_dummy_profile(
    row_count: int = 100,
    columns: list[ColumnProfile] | None = None,
) -> DatasetProfile:
    """Helper to build a DatasetProfile for rule testing."""
    cols = columns or []
    total_missing = sum(c.missing_count for c in cols)
    cols_with_missing = sum(1 for c in cols if c.missing_count > 0)

    return DatasetProfile(
        summary=DatasetSummary(
            row_count=row_count,
            column_count=len(cols),
            memory_usage_bytes=1024,
        ),
        columns=cols,
        missing=MissingSummary(
            total_missing_values=total_missing,
            columns_with_missing=cols_with_missing,
        ),
        duplicates=DuplicateSummary(duplicate_rows=0),
    )


def test_check_missing_values_high_threshold() -> None:
    """Verify >= 30% missing values produces HIGH severity insight with evidence."""
    col = ColumnProfile(
        name="salary",
        dtype="float64",
        missing_count=35,
        missing_percentage=35.0,
        unique_count=50,
        numeric=NumericStatistics(mean=50000.0),
    )
    profile = _make_dummy_profile(row_count=100, columns=[col])
    insights = check_missing_values(profile)

    assert len(insights) == 1
    insight = insights[0]
    assert insight.category == InsightCategory.MISSING_VALUES
    assert insight.severity == Severity.HIGH
    assert len(insight.evidence) == 1
    evidence = insight.evidence[0]
    assert evidence.column == "salary"
    assert evidence.metric == "missing_percentage"
    assert evidence.value == 35.0
    assert evidence.threshold == HIGH_MISSING_THRESHOLD
    assert "salary" in insight.title
    assert "35.0%" in insight.description


def test_check_missing_values_medium_threshold() -> None:
    """Verify 10% - 29.9% missing values produces MEDIUM severity insight."""
    col = ColumnProfile(
        name="age",
        dtype="float64",
        missing_count=15,
        missing_percentage=15.0,
        unique_count=40,
    )
    profile = _make_dummy_profile(row_count=100, columns=[col])
    insights = check_missing_values(profile)

    assert len(insights) == 1
    insight = insights[0]
    assert insight.category == InsightCategory.MISSING_VALUES
    assert insight.severity == Severity.MEDIUM
    assert len(insight.evidence) == 1
    evidence = insight.evidence[0]
    assert evidence.column == "age"
    assert evidence.metric == "missing_percentage"
    assert evidence.value == 15.0
    assert evidence.threshold == MEDIUM_MISSING_THRESHOLD
    assert "age" in insight.title


def test_check_missing_values_boundaries() -> None:
    """Test boundary conditions for missing values thresholds (30.0%, 29.9%, 10.0%, 9.9%)."""
    col_exact_high = ColumnProfile(
        name="c1", dtype="float64", missing_count=30, missing_percentage=30.0, unique_count=10
    )
    col_just_below_high = ColumnProfile(
        name="c2", dtype="float64", missing_count=29, missing_percentage=29.9, unique_count=10
    )
    col_exact_medium = ColumnProfile(
        name="c3", dtype="float64", missing_count=10, missing_percentage=10.0, unique_count=10
    )
    col_below_medium = ColumnProfile(
        name="c4", dtype="float64", missing_count=9, missing_percentage=9.9, unique_count=10
    )

    profile = _make_dummy_profile(
        row_count=100,
        columns=[col_exact_high, col_just_below_high, col_exact_medium, col_below_medium],
    )
    insights = check_missing_values(profile)

    assert len(insights) == 3
    assert insights[0].severity == Severity.HIGH  # 30.0%
    assert insights[1].severity == Severity.MEDIUM  # 29.9%
    assert insights[2].severity == Severity.MEDIUM  # 10.0%


def test_check_missing_values_zero_missing() -> None:
    """Verify zero missing values produces no insights."""
    col = ColumnProfile(
        name="id", dtype="int64", missing_count=0, missing_percentage=0.0, unique_count=100
    )
    profile = _make_dummy_profile(row_count=100, columns=[col])
    assert check_missing_values(profile) == []
