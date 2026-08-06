"""Insights engine package."""

from csv_analytics_agent.insights.generator import RULES, InsightGenerator
from csv_analytics_agent.insights.models import (
    Evidence,
    Insight,
    InsightCategory,
    Severity,
)
from csv_analytics_agent.insights.rules import (
    HIGH_CARDINALITY_THRESHOLD,
    HIGH_MISSING_THRESHOLD,
    MEDIUM_MISSING_THRESHOLD,
    check_duplicate_rows,
    check_high_cardinality,
    check_identifier_columns,
    check_missing_values,
    evaluate_all_rules,
)

__all__ = [
    "HIGH_CARDINALITY_THRESHOLD",
    "HIGH_MISSING_THRESHOLD",
    "MEDIUM_MISSING_THRESHOLD",
    "RULES",
    "Evidence",
    "Insight",
    "InsightCategory",
    "InsightGenerator",
    "Severity",
    "check_duplicate_rows",
    "check_high_cardinality",
    "check_identifier_columns",
    "check_missing_values",
    "evaluate_all_rules",
]