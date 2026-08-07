"""Rule engine and synonym mapping system for query intent resolution."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from csv_analytics_agent.planner.models import IntentType


class IntentRule(BaseModel):
    """Rule mapping keyword synonyms to an analytical intent and default parameters.

    Attributes:
        capability_name: Target capability name (e.g. 'aggregate', 'top_n').
        intent_type: High-level IntentType category.
        keywords: Synonyms/keywords triggering this rule.
        default_parameters: Default parameter key-values.
        description: Rule pattern description for reasoning traces.
    """

    model_config = ConfigDict(frozen=True)

    capability_name: str = Field(..., min_length=1, description="Target capability name.")
    intent_type: IntentType = Field(..., description="High-level intent classification.")
    keywords: list[str] = Field(..., min_length=1, description="Keyword synonyms triggering rule.")
    default_parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Default parameters dictionary.",
    )
    description: str = Field(..., min_length=1, description="Rule description snippet.")


DEFAULT_RULES: list[IntentRule] = [
    # Aggregation rules
    IntentRule(
        capability_name="aggregate",
        intent_type=IntentType.AGGREGATE,
        keywords=["average", "mean", "avg"],
        default_parameters={"operation": "mean"},
        description="Matched average/mean synonym -> aggregate(operation='mean')",
    ),
    IntentRule(
        capability_name="aggregate",
        intent_type=IntentType.AGGREGATE,
        keywords=["highest", "maximum", "max", "peak"],
        default_parameters={"operation": "max"},
        description="Matched maximum/highest synonym -> aggregate(operation='max')",
    ),
    IntentRule(
        capability_name="aggregate",
        intent_type=IntentType.AGGREGATE,
        keywords=["lowest", "minimum", "min"],
        default_parameters={"operation": "min"},
        description="Matched minimum/lowest synonym -> aggregate(operation='min')",
    ),
    IntentRule(
        capability_name="aggregate",
        intent_type=IntentType.AGGREGATE,
        keywords=["total", "sum"],
        default_parameters={"operation": "sum"},
        description="Matched total/sum synonym -> aggregate(operation='sum')",
    ),
    IntentRule(
        capability_name="aggregate",
        intent_type=IntentType.AGGREGATE,
        keywords=["count", "number of", "how many"],
        default_parameters={"operation": "count"},
        description="Matched count synonym -> aggregate(operation='count')",
    ),
    # Top N rules
    IntentRule(
        capability_name="top_n",
        intent_type=IntentType.TOP_N,
        keywords=["top", "first", "best"],
        default_parameters={"order": "desc"},
        description="Matched top N synonym -> top_n(order='desc')",
    ),
    IntentRule(
        capability_name="top_n",
        intent_type=IntentType.TOP_N,
        keywords=["bottom", "worst"],
        default_parameters={"order": "asc"},
        description="Matched bottom N synonym -> top_n(order='asc')",
    ),
    # Grouping rules
    IntentRule(
        capability_name="group",
        intent_type=IntentType.GROUP,
        keywords=["group by", "grouped by", "by department", "by region", "per"],
        default_parameters={"operation": "mean"},
        description="Matched group by synonym -> group",
    ),
    # Sorting rules
    IntentRule(
        capability_name="sort",
        intent_type=IntentType.SORT,
        keywords=["sort", "order by", "ascending", "descending"],
        default_parameters={"order": "asc"},
        description="Matched sort synonym -> sort",
    ),
    # Filtering rules
    IntentRule(
        capability_name="filter",
        intent_type=IntentType.FILTER,
        keywords=[
            "filter",
            "greater than",
            "less than",
            "equal to",
            "older than",
            "younger than",
            "above",
            "below",
        ],
        default_parameters={"operator": "eq"},
        description="Matched filter condition -> filter",
    ),
]


class RuleEngine:
    """Configurable rule evaluator for natural language intent matching."""

    def __init__(self, rules: list[IntentRule] | None = None) -> None:
        """Initialize RuleEngine with custom or default rules.

        Args:
            rules: List of IntentRule objects (defaults to DEFAULT_RULES if None).
        """
        self._rules = rules if rules is not None else DEFAULT_RULES

    def match_intent(self, query: str) -> tuple[IntentRule | None, str | None, float]:
        """Match query text against registered rules.

        Args:
            query: Natural language query string.

        Returns:
            Tuple of (matched IntentRule or None, matched keyword, confidence score).
        """
        lower_query = query.lower()

        for rule in self._rules:
            for kw in rule.keywords:
                if kw in lower_query:
                    # Longer matching keywords yield slightly higher confidence
                    confidence = 0.95 if len(kw) > 3 else 0.90
                    return rule, kw, confidence

        return None, None, 0.0


__all__ = [
    "DEFAULT_RULES",
    "IntentRule",
    "RuleEngine",
]
