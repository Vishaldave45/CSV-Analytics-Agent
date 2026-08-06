"""Insights engine package."""

from csv_analytics_agent.insights.constants import (
    HIGH_CARDINALITY_THRESHOLD,
    HIGH_MISSING_THRESHOLD,
    MEDIUM_MISSING_THRESHOLD,
    RULE_ID_DUPLICATES,
    RULE_ID_HIGH_CARDINALITY,
    RULE_ID_HIGH_MISSING,
    RULE_ID_IDENTIFIER,
    RULE_ID_MEDIUM_MISSING,
)
from csv_analytics_agent.insights.generator import RULES, InsightGenerator
from csv_analytics_agent.insights.models import (
    ComparisonOperator,
    Evidence,
    Insight,
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

__all__ = [
    "HIGH_CARDINALITY_THRESHOLD",
    "HIGH_MISSING_THRESHOLD",
    "MEDIUM_MISSING_THRESHOLD",
    "RULES",
    "RULE_ID_DUPLICATES",
    "RULE_ID_HIGH_CARDINALITY",
    "RULE_ID_HIGH_MISSING",
    "RULE_ID_IDENTIFIER",
    "RULE_ID_MEDIUM_MISSING",
    "ComparisonOperator",
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