"""Unit tests for duplicate rows business rule evaluation."""

from csv_analytics_agent.insights.models import InsightCategory, Severity
from csv_analytics_agent.insights.rules.duplicates import check_duplicate_rows
from csv_analytics_agent.profiler.models import (
    DatasetProfile,
    DatasetSummary,
    DuplicateSummary,
    MissingSummary,
)


def _make_dummy_profile(
    row_count: int = 100,
    duplicate_rows: int = 0,
) -> DatasetProfile:
    """Helper to build a DatasetProfile for duplicate testing."""
    return DatasetProfile(
        summary=DatasetSummary(
            row_count=row_count,
            column_count=0,
            memory_usage_bytes=1024,
        ),
        columns=[],
        missing=MissingSummary(total_missing_values=0, columns_with_missing=0),
        duplicates=DuplicateSummary(duplicate_rows=duplicate_rows),
    )


def test_check_duplicate_rows_detected() -> None:
    """Verify duplicate rows produce a MEDIUM severity insight with evidence."""
    profile = _make_dummy_profile(row_count=100, duplicate_rows=5)
    insights = check_duplicate_rows(profile)

    assert len(insights) == 1
    insight = insights[0]
    assert insight.category == InsightCategory.DUPLICATES
    assert insight.severity == Severity.MEDIUM
    assert len(insight.evidence) == 1
    evidence = insight.evidence[0]
    assert evidence.column is None
    assert evidence.metric == "duplicate_rows"
    assert evidence.value == 5
    assert evidence.threshold == 0
    assert "5 duplicate row(s)" in insight.description


def test_check_duplicate_rows_zero() -> None:
    """Verify zero duplicate rows produces no insights."""
    profile = _make_dummy_profile(row_count=100, duplicate_rows=0)
    insights = check_duplicate_rows(profile)
    assert len(insights) == 0


def test_check_duplicate_rows_empty_dataset() -> None:
    """Verify empty dataset (0 rows) produces no duplicate insights."""
    profile = _make_dummy_profile(row_count=0, duplicate_rows=0)
    insights = check_duplicate_rows(profile)
    assert len(insights) == 0
