"""Unit tests for the deterministic rule engine."""

from csv_analytics_agent.insights.constants import (
    RULE_ID_DUPLICATES,
    RULE_ID_HIGH_CARDINALITY,
    RULE_ID_HIGH_MISSING,
    RULE_ID_IDENTIFIER,
    RULE_ID_MEDIUM_MISSING,
)
from csv_analytics_agent.insights.models import (
    ComparisonOperator,
    InsightCategory,
    Severity,
)
from csv_analytics_agent.insights.rules import (
    check_duplicate_rows,
    check_high_cardinality,
    check_identifier_columns,
    check_missing_values,
    evaluate_all_rules,
)
from csv_analytics_agent.profiler.models import (
    CategoricalStatistics,
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
    duplicate_rows: int = 0,
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
        duplicates=DuplicateSummary(duplicate_rows=duplicate_rows),
    )


def test_check_missing_values_high_threshold() -> None:
    """Verify >= 30% missing values produces HIGH severity insight with structured evidence."""
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
    assert insight.id == RULE_ID_HIGH_MISSING
    assert insight.category == InsightCategory.MISSING_VALUES
    assert insight.severity == Severity.HIGH
    assert len(insight.evidence) == 1
    evidence = insight.evidence[0]
    assert evidence.column_name == "salary"
    assert evidence.metric_name == "missing_percentage"
    assert evidence.observed_value == 35.0
    assert evidence.threshold == 30.0
    assert evidence.comparison == ComparisonOperator.GREATER_THAN_OR_EQUAL
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
    assert insight.id == RULE_ID_MEDIUM_MISSING
    assert insight.category == InsightCategory.MISSING_VALUES
    assert insight.severity == Severity.MEDIUM
    assert len(insight.evidence) == 1
    evidence = insight.evidence[0]
    assert evidence.column_name == "age"
    assert evidence.metric_name == "missing_percentage"
    assert evidence.observed_value == 15.0
    assert evidence.threshold == 10.0
    assert evidence.comparison == ComparisonOperator.GREATER_THAN_OR_EQUAL
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


def test_check_duplicate_rows_detected() -> None:
    """Verify duplicate rows produce a MEDIUM severity insight with structured evidence."""
    profile = _make_dummy_profile(row_count=100, duplicate_rows=5)
    insights = check_duplicate_rows(profile)

    assert len(insights) == 1
    insight = insights[0]
    assert insight.id == RULE_ID_DUPLICATES
    assert insight.category == InsightCategory.DUPLICATES
    assert insight.severity == Severity.MEDIUM
    assert len(insight.evidence) == 1
    evidence = insight.evidence[0]
    assert evidence.column_name is None
    assert evidence.metric_name == "duplicate_rows"
    assert evidence.observed_value == 5
    assert evidence.threshold == 0
    assert evidence.comparison == ComparisonOperator.GREATER_THAN
    assert "5 duplicate row(s)" in insight.description


def test_check_duplicate_rows_zero() -> None:
    """Verify zero duplicate rows produces no insights."""
    profile = _make_dummy_profile(row_count=100, duplicate_rows=0)
    insights = check_duplicate_rows(profile)
    assert len(insights) == 0


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
    assert insight.id == RULE_ID_IDENTIFIER
    assert insight.category == InsightCategory.CARDINALITY
    assert insight.severity == Severity.INFO
    assert len(insight.evidence) == 1
    evidence = insight.evidence[0]
    assert evidence.column_name == "user_id"
    assert evidence.metric_name == "unique_ratio"
    assert evidence.observed_value == 1.0
    assert evidence.threshold == 1.0
    assert evidence.comparison == ComparisonOperator.EQUAL
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
    assert insight.id == RULE_ID_HIGH_CARDINALITY
    assert insight.category == InsightCategory.CARDINALITY
    assert insight.severity == Severity.LOW
    assert len(insight.evidence) == 1
    evidence = insight.evidence[0]
    assert evidence.column_name == "zip_code"
    assert evidence.metric_name == "unique_count"
    assert evidence.observed_value == 150
    assert evidence.threshold == 100
    assert evidence.comparison == ComparisonOperator.GREATER_THAN
    assert "zip_code" in insight.title


def test_evaluate_all_rules_combined() -> None:
    """Verify evaluate_all_rules orchestrates all rule evaluations into a combined list."""
    high_missing_col = ColumnProfile(
        name="salary", dtype="float64", missing_count=40, missing_percentage=40.0, unique_count=50
    )
    id_col = ColumnProfile(
        name="emp_id", dtype="int64", missing_count=0, missing_percentage=0.0, unique_count=100
    )

    profile = _make_dummy_profile(
        row_count=100,
        columns=[high_missing_col, id_col],
        duplicate_rows=3,
    )

    insights = evaluate_all_rules(profile)

    assert len(insights) == 3
    categories = {i.category for i in insights}
    assert InsightCategory.MISSING_VALUES in categories
    assert InsightCategory.DUPLICATES in categories
    assert InsightCategory.CARDINALITY in categories
