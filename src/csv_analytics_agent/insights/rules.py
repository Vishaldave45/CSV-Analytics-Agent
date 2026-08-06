"""Deterministic rule engine for dataset analysis and insight generation."""

from __future__ import annotations

from csv_analytics_agent.insights.models import (
    Evidence,
    Insight,
    InsightCategory,
    Severity,
)
from csv_analytics_agent.profiler.models import DatasetProfile

# Rule evaluation thresholds owned by business logic
HIGH_MISSING_THRESHOLD: float = 30.0
MEDIUM_MISSING_THRESHOLD: float = 10.0
HIGH_CARDINALITY_THRESHOLD: int = 100


def check_missing_values(profile: DatasetProfile) -> list[Insight]:
    """Check dataset columns for high or moderate missing value percentages.

    Args:
        profile: The complete dataset profile.

    Returns:
        List of generated missing value insights with evidence.
    """
    insights: list[Insight] = []

    for col in profile.columns:
        pct = col.missing_percentage
        if pct >= HIGH_MISSING_THRESHOLD:
            evidence = Evidence(
                column=col.name,
                metric="missing_percentage",
                value=round(pct, 2),
                threshold=HIGH_MISSING_THRESHOLD,
            )
            insights.append(
                Insight(
                    category=InsightCategory.MISSING_VALUES,
                    severity=Severity.HIGH,
                    title=f"High Missing Values in '{col.name}'",
                    description=(
                        f"Column '{col.name}' has {pct:.1f}% missing values "
                        f"({col.missing_count} out of {profile.summary.row_count} rows)."
                    ),
                    recommendation=(
                        f"Consider imputing or dropping column '{col.name}' "
                        f"due to severe missingness (>= {HIGH_MISSING_THRESHOLD:.0f}%)."
                    ),
                    evidence=[evidence],
                )
            )
        elif pct >= MEDIUM_MISSING_THRESHOLD:
            evidence = Evidence(
                column=col.name,
                metric="missing_percentage",
                value=round(pct, 2),
                threshold=MEDIUM_MISSING_THRESHOLD,
            )
            insights.append(
                Insight(
                    category=InsightCategory.MISSING_VALUES,
                    severity=Severity.MEDIUM,
                    title=f"Moderate Missing Values in '{col.name}'",
                    description=(
                        f"Column '{col.name}' has {pct:.1f}% missing values "
                        f"({col.missing_count} out of {profile.summary.row_count} rows)."
                    ),
                    recommendation=(
                        f"Evaluate imputation strategies for column '{col.name}' "
                        f"as missingness exceeds {MEDIUM_MISSING_THRESHOLD:.0f}%."
                    ),
                    evidence=[evidence],
                )
            )

    return insights


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
                f"Found {duplicate_count} duplicate row(s) "
                f"({pct:.1f}% of {total_rows} total rows)."
            ),
            recommendation=(
                "Review duplicate rows and consider deduplicating "
                "the dataset before downstream modeling."
            ),
            evidence=[evidence],
        )
    ]


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


def evaluate_all_rules(profile: DatasetProfile) -> list[Insight]:
    """Evaluate all deterministic business rules on a dataset profile.

    Args:
        profile: The complete dataset profile.

    Returns:
        Combined list of all generated insights with evidence.
    """
    insights: list[Insight] = []
    insights.extend(check_missing_values(profile))
    insights.extend(check_duplicate_rows(profile))
    insights.extend(check_identifier_columns(profile))
    insights.extend(check_high_cardinality(profile))
    return insights
