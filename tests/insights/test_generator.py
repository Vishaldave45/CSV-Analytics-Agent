"""Unit tests for the InsightGenerator orchestrator."""

from unittest.mock import MagicMock

from csv_analytics_agent.insights.generator import RULES, InsightGenerator
from csv_analytics_agent.insights.models import (
    Insight,
    InsightCategory,
    Severity,
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
    duplicate_rows: int = 0,
) -> DatasetProfile:
    """Helper to build a DatasetProfile for generator testing."""
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


def test_generate_no_issues() -> None:
    """Verify a clean profile with no violations generates an empty insights list."""
    col = ColumnProfile(
        name="score",
        dtype="float64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=50,  # Not 100 (not identifier), not >100 (not high card)
    )
    profile = _make_dummy_profile(row_count=100, columns=[col], duplicate_rows=0)

    generator = InsightGenerator()
    insights = generator.generate(profile)

    assert insights == []


def test_generate_single_rule_trigger() -> None:
    """Verify triggering a single rule returns 1 insight."""
    col = ColumnProfile(
        name="salary",
        dtype="float64",
        missing_count=40,
        missing_percentage=40.0,
        unique_count=50,
    )
    profile = _make_dummy_profile(row_count=100, columns=[col])

    generator = InsightGenerator()
    insights = generator.generate(profile)

    assert len(insights) == 1
    assert insights[0].severity == Severity.HIGH
    assert insights[0].category == InsightCategory.MISSING_VALUES


def test_generate_multiple_rules_trigger() -> None:
    """Verify multiple violations generate multiple insights."""
    missing_col = ColumnProfile(
        name="age",
        dtype="float64",
        missing_count=35,
        missing_percentage=35.0,
        unique_count=50,
    )
    id_col = ColumnProfile(
        name="user_id",
        dtype="int64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=100,
    )
    high_card_col = ColumnProfile(
        name="city",
        dtype="object",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=90,  # unique_count < 100, not high card
    )

    profile = _make_dummy_profile(
        row_count=100,
        columns=[missing_col, id_col, high_card_col],
        duplicate_rows=10,
    )

    generator = InsightGenerator()
    insights = generator.generate(profile)

    # 1 HIGH (missing values), 1 MEDIUM (duplicates), 1 INFO (identifier column)
    assert len(insights) == 3


def test_generate_sort_order() -> None:
    """Verify insights are sorted by severity priority descending."""
    high_missing_col = ColumnProfile(
        name="col_high",
        dtype="float64",
        missing_count=35,
        missing_percentage=35.0,
        unique_count=50,
    )
    id_col = ColumnProfile(
        name="col_info",
        dtype="int64",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=200,
    )
    high_card_col = ColumnProfile(
        name="col_low",
        dtype="object",
        missing_count=0,
        missing_percentage=0.0,
        unique_count=120,
        categorical=CategoricalStatistics(category_count=120),
    )

    profile = _make_dummy_profile(
        row_count=200,
        columns=[high_missing_col, id_col, high_card_col],
        duplicate_rows=5,  # Trigger MEDIUM severity
    )

    generator = InsightGenerator()
    insights = generator.generate(profile)

    assert len(insights) == 4
    severities = [i.severity for i in insights]
    assert severities == [Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]


def test_generate_sort_critical_severity() -> None:
    """Verify critical severity insight is placed at index 0."""
    critical_insight = Insight(
        category=InsightCategory.DATA_QUALITY,
        severity=Severity.CRITICAL,
        title="Critical Schema Corruption",
        description="Dataset is corrupted.",
        recommendation="Fix ingestion pipeline.",
    )

    info_insight = Insight(
        category=InsightCategory.CARDINALITY,
        severity=Severity.INFO,
        title="ID Column",
        description="ID col found.",
        recommendation="Ignore ID.",
    )

    unsorted = [info_insight, critical_insight]
    sorted_insights = InsightGenerator._sort(unsorted)

    assert sorted_insights[0].severity == Severity.CRITICAL
    assert sorted_insights[1].severity == Severity.INFO


def test_generate_custom_rules_execution() -> None:
    """Verify custom rule tuple functions are called exactly once."""
    mock_rule1 = MagicMock(return_value=[])
    mock_rule2 = MagicMock(return_value=[])

    profile = _make_dummy_profile()
    generator = InsightGenerator(rules=(mock_rule1, mock_rule2))
    insights = generator.generate(profile)

    assert insights == []
    mock_rule1.assert_called_once_with(profile)
    mock_rule2.assert_called_once_with(profile)


def test_default_rules_tuple() -> None:
    """Verify default RULES tuple contains all 4 business rule functions."""
    assert len(RULES) == 4
