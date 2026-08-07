"""Insights engine package."""

from csv_analytics_agent.insights.generator import RULES, InsightGenerator
from csv_analytics_agent.insights.models import (
    Evidence,
    Insight,
    InsightCategory,
    Severity,
)
from csv_analytics_agent.insights.rules import (
    HIGH_MISSING_THRESHOLD,
    MEDIUM_MISSING_THRESHOLD,
    check_duplicate_rows,
    check_missing_values,
)

__all__ = [
    "HIGH_MISSING_THRESHOLD",
    "MEDIUM_MISSING_THRESHOLD",
    "RULES",
    "Evidence",
    "Insight",
    "InsightCategory",
    "InsightGenerator",
    "Severity",
    "check_duplicate_rows",
    "check_missing_values",
]
