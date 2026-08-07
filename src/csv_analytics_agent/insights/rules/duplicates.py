"""Duplicate rows business rule evaluation."""

from __future__ import annotations

from csv_analytics_agent.insights.models import (
    Evidence,
    Insight,
    InsightCategory,
    Severity,
)
from csv_analytics_agent.profiler.models import DatasetProfile


def check_duplicate_rows(profile: DatasetProfile) -> list[Insight]:
    """Check dataset for duplicate rows.

    Args:
        profile: The complete dataset profile.

    Returns:
        List of duplicate row insights with evidence (empty if no duplicates found).
    """
    duplicate_count = profile.duplicates.duplicate_rows
    if duplicate_count == 0:
        return []

    total_rows = profile.summary.row_count
    pct = (duplicate_count / total_rows * 100.0) if total_rows > 0 else 0.0

    evidence = Evidence(
        column=None,
        metric="duplicate_rows",
        value=duplicate_count,
        threshold=0,
    )

    return [
        Insight(
            category=InsightCategory.DUPLICATES,
            severity=Severity.MEDIUM,
            title="Duplicate Rows Detected",
            description=(
                f"Found {duplicate_count} duplicate row(s) ({pct:.1f}% of {total_rows} total rows)."
            ),
            recommendation=(
                "Review duplicate rows and consider deduplicating "
                "the dataset before downstream modeling."
            ),
            evidence=[evidence],
        )
    ]
