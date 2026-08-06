"""Unit tests for cardinality and identifier column business rule evaluations."""

from csv_analytics_agent.insights.models import InsightCategory, Severity
from csv_analytics_agent.insights.rules.cardinality import (
    HIGH_CARDINALITY_THRESHOLD,
    check_high_cardinality,
    check_identifier_columns,
)
from csv_analytics_agent.profiler.models import (
    CategoricalStatistics,
    ColumnProfile,
    DatasetProfile,
    DatasetSummary,
    DuplicateSummary,
    MissingSummary,
)


def _make_dummy_profile(
    row_count: int = 100,
    columns: list[ColumnProfile] | None = None,
) -> DatasetProfile:
    """Helper to build a DatasetProfile for cardinality testing."""
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


def test_check_identifier_columns() -> None:
    """Verify columns with 100% unique non-null values trigger INFO identifier insights."""
    id_col = ColumnProfile(
        name="user_id",
        dtype="int64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=100,
    )
    non_id_col = ColumnProfile(
        name="city",
        dtype="object",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=5,
    )

    profile = _make_dummy_profile(row_count=100, columns=[id_col, non_id_col])
    insights = check_identifier_columns(profile)

    assert len(insights) == 1
    insight = insights[0]
    assert insight.category == InsightCategory.CARDINALITY
    assert insight.severity == Severity.INFO
    assert len(insight.evidence) == 1
    evidence = insight.evidence[0]
    assert evidence.column == "user_id"
    assert evidence.metric == "unique_ratio"
    assert evidence.value == 1.0
    assert evidence.threshold == 1.0
    assert "user_id" in insight.title


def test_check_identifier_columns_empty_dataset() -> None:
    """Verify check_identifier_columns returns [] for empty datasets (row_count=0)."""
    profile = _make_dummy_profile(row_count=0)
    assert check_identifier_columns(profile) == []


def test_check_high_cardinality() -> None:
    """Verify categorical columns exceeding cardinality threshold produce LOW severity insights."""
    high_card_col = ColumnProfile(
        name="zip_code",
        dtype="object",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=150,
        categorical=CategoricalStatistics(category_count=150),
    )
    low_card_col = ColumnProfile(
        name="state",
        dtype="object",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=50,
        categorical=CategoricalStatistics(category_count=50),
    )

    profile = _make_dummy_profile(row_count=200, columns=[high_card_col, low_card_col])
    insights = check_high_cardinality(profile)

    assert len(insights) == 1
    insight = insights[0]
    assert insight.category == InsightCategory.CARDINALITY
    assert insight.severity == Severity.LOW
    assert len(insight.evidence) == 1
    evidence = insight.evidence[0]
    assert evidence.column == "zip_code"
    assert evidence.metric == "unique_count"
    assert evidence.value == 150
    assert evidence.threshold == HIGH_CARDINALITY_THRESHOLD
    assert "zip_code" in insight.title


def test_check_high_cardinality_boundary() -> None:
    """Verify unique_count == HIGH_CARDINALITY_THRESHOLD (100) does not trigger high cardinality."""
    exact_threshold_col = ColumnProfile(
        name="code",
        dtype="object",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=100,
        categorical=CategoricalStatistics(category_count=100),
    )
    profile = _make_dummy_profile(row_count=200, columns=[exact_threshold_col])
    assert check_high_cardinality(profile) == []
