"""Orchestrator for deterministic insight generation."""

from __future__ import annotations

from collections.abc import Callable

from csv_analytics_agent.insights.models import Insight
from csv_analytics_agent.insights.rules.cardinality import (
    check_high_cardinality,
    check_identifier_columns,
)
from csv_analytics_agent.insights.rules.duplicates import check_duplicate_rows
from csv_analytics_agent.insights.rules.missing import check_missing_values
from csv_analytics_agent.profiler.models import DatasetProfile

# Tuple of rule evaluation functions to execute during insight generation
RULES: tuple[Callable[[DatasetProfile], list[Insight]], ...] = (
    check_missing_values,
    check_duplicate_rows,
    check_identifier_columns,
    check_high_cardinality,
)


class InsightGenerator:
    """Orchestrates rule evaluations and generates sorted insights from a dataset profile."""

    def __init__(
        self,
        rules: tuple[Callable[[DatasetProfile], list[Insight]], ...] | None = None,
    ) -> None:
        """Initialize InsightGenerator with rule functions.

        Args:
            rules: Optional custom tuple of rule evaluation functions. Defaults to RULES.
        """
        self._rules = rules if rules is not None else RULES

    def generate(self, profile: DatasetProfile) -> list[Insight]:
        """Generate all insights for the given dataset profile sorted by severity.

        Args:
            profile: The input DatasetProfile.

        Returns:
            Sorted list of generated Insight objects (highest severity first).
        """
        insights: list[Insight] = []

        for rule in self._rules:
            insights.extend(rule(profile))

        return self._sort(insights)

    @staticmethod
    def _sort(insights: list[Insight]) -> list[Insight]:
        """Sort insights by severity priority (critical -> high -> medium -> low -> info).

        Args:
            insights: Unsorted list of Insight objects.

        Returns:
            List of Insight objects sorted by severity descending.
        """
        severity_order: dict[str, int] = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
            "info": 4,
        }

        return sorted(
            insights,
            key=lambda insight: severity_order.get(insight.severity.value, 99),
        )
