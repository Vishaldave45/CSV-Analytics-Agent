"""Missing values business rule evaluation."""

from __future__ import annotations

from csv_analytics_agent.insights.models import (
    Evidence,
    Insight,
    InsightCategory,
    Severity,
)
from csv_analytics_agent.profiler.models import DatasetProfile

# Business threshold values for missing value evaluation
HIGH_MISSING_THRESHOLD: float = 30.0
MEDIUM_MISSING_THRESHOLD: float = 10.0


def check_missing_values(profile: DatasetProfile) -> list[Insight]:
    """Check dataset columns for high or moderate missing value percentages.

    Args:
        profile: The complete dataset profile.

    Returns:
        List of generated missing value insights with supporting evidence.
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
