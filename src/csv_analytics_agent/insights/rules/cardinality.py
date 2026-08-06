"""Cardinality and identifier column business rule evaluations."""

from __future__ import annotations

from csv_analytics_agent.insights.models import (
    Evidence,
    Insight,
    InsightCategory,
    Severity,
)
from csv_analytics_agent.profiler.models import DatasetProfile

# Business threshold for high cardinality detection
HIGH_CARDINALITY_THRESHOLD: int = 100


def check_identifier_columns(profile: DatasetProfile) -> list[Insight]:
    """Identify columns that serve as primary keys or unique identifiers.

    Args:
        profile: The complete dataset profile.

    Returns:
        List of identifier column insights with evidence.
    """
    total_rows = profile.summary.row_count
    if total_rows == 0:
        return []

    insights: list[Insight] = []
    for col in profile.columns:
        if col.unique_count == total_rows and col.missing_count == 0:
            evidence = Evidence(
                column=col.name,
                metric="unique_ratio",
                value=1.0,
                threshold=1.0,
            )
            insights.append(
                Insight(
                    category=InsightCategory.CARDINALITY,
                    severity=Severity.INFO,
                    title=f"Possible Identifier Column '{col.name}'",
                    description=(
                        f"Column '{col.name}' has 100% unique values "
                        f"({col.unique_count} distinct values for {total_rows} rows)."
                    ),
                    recommendation=(
                        f"Treat column '{col.name}' as a primary key/ID column. "
                        f"Exclude from statistical aggregations."
                    ),
                    evidence=[evidence],
                )
            )

    return insights


def check_high_cardinality(profile: DatasetProfile) -> list[Insight]:
    """Check categorical/text columns for high cardinality.

    Args:
        profile: The complete dataset profile.

    Returns:
        List of high cardinality insights with evidence.
    """
    insights: list[Insight] = []
    total_rows = profile.summary.row_count

    for col in profile.columns:
        if col.unique_count > HIGH_CARDINALITY_THRESHOLD and col.unique_count < total_rows:
            if col.categorical is not None or "str" in col.dtype or "object" in col.dtype:
                evidence = Evidence(
                    column=col.name,
                    metric="unique_count",
                    value=col.unique_count,
                    threshold=HIGH_CARDINALITY_THRESHOLD,
                )
                insights.append(
                    Insight(
                        category=InsightCategory.CARDINALITY,
                        severity=Severity.LOW,
                        title=f"High Cardinality in '{col.name}'",
                        description=(
                            f"Categorical/text column '{col.name}' contains "
                            f"{col.unique_count} distinct values "
                            f"(exceeds threshold of {HIGH_CARDINALITY_THRESHOLD})."
                        ),
                        recommendation=(
                            f"Consider target encoding, frequency encoding, "
                            f"or grouping rare categories in '{col.name}'."
                        ),
                        evidence=[evidence],
                    )
                )

    return insights
