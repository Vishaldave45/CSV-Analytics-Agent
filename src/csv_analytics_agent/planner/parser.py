"""Query parser for extracting intent, columns, and parameters from natural language."""

from __future__ import annotations

import re
from typing import Any

from csv_analytics_agent.planner.models import IntentType, ParsedIntent
from csv_analytics_agent.planner.rules import IntentRule, RuleEngine


class QueryParser:
    """Parses natural language analytical queries against a list of target dataset columns."""

    def __init__(self, rule_engine: RuleEngine | None = None) -> None:
        """Initialize QueryParser with an underlying RuleEngine.

        Args:
            rule_engine: RuleEngine instance (defaults to default RuleEngine if None).
        """
        self._rule_engine = rule_engine or RuleEngine()

    def parse(
        self,
        query: str,
        available_columns: list[str],
    ) -> tuple[ParsedIntent, IntentRule | None, float, list[str]]:
        """Parse query string into a ParsedIntent and reasoning trace steps.

        Args:
            query: Natural language query string.
            available_columns: List of valid column names in target dataset.

        Returns:
            Tuple of (ParsedIntent, matched IntentRule or None, confidence float, reasoning trace).
        """
        trace: list[str] = [f"Parsing raw query: '{query}'"]
        lower_query = query.lower()

        # 1. Match Rule Intent
        rule, matched_kw, confidence = self._rule_engine.match_intent(query)
        intent_type = rule.intent_type if rule else IntentType.UNKNOWN

        if rule and matched_kw:
            trace.append(f"Matched keyword '{matched_kw}' -> intent '{intent_type.value}'")
        else:
            trace.append("No rule matched; classified as 'UNKNOWN'")

        # 2. Extract Columns
        target_columns, by_columns = self._extract_columns(lower_query, available_columns)
        if target_columns:
            trace.append(f"Matched column(s): {target_columns}")
        else:
            trace.append("No matching columns identified from dataset schema")

        # 3. Extract Parameters & Numbers
        parameters: dict[str, Any] = dict(rule.default_parameters) if rule else {}

        # Handle top_n / bottom_n count extraction
        if intent_type == IntentType.TOP_N:
            count = self._extract_first_number(lower_query) or 5
            parameters["n"] = count
            trace.append(f"Extracted count n={count} for top_n")

        # Handle filter operator and value extraction
        if intent_type == IntentType.FILTER:
            operator, val = self._extract_filter_operator_and_value(lower_query)
            if operator:
                parameters["operator"] = operator
            if val is not None:
                parameters["value"] = val
                trace.append(f"Extracted filter condition: operator='{operator}', value={val}")

        # Handle group by target/by extraction
        if intent_type == IntentType.GROUP:
            if by_columns:
                by_col = by_columns[0]
                parameters["by"] = by_col
                remaining_cols = [c for c in target_columns if c != by_col]
                if remaining_cols:
                    parameters["target"] = remaining_cols[0]
                by_msg = f"Assigned grouping: by='{by_col}', target='{parameters.get('target')}'"
                trace.append(by_msg)

        parsed = ParsedIntent(
            intent_type=intent_type,
            target_columns=target_columns,
            parameters=parameters,
            raw_query=query,
        )

        return parsed, rule, confidence, trace

    def _extract_columns(
        self,
        lower_query: str,
        available_columns: list[str],
    ) -> tuple[list[str], list[str]]:
        """Extract matching columns from query text sorted by length.

        Args:
            lower_query: Lowercased query text string.
            available_columns: Valid dataset column names.

        Returns:
            Tuple of (matched target columns, matched group-by columns).
        """
        matched: list[str] = []
        by_cols: list[str] = []

        sorted_cols = sorted(available_columns, key=len, reverse=True)

        for col in sorted_cols:
            col_lower = col.lower()
            col_pattern = rf"\b{re.escape(col_lower)}\b"
            if re.search(col_pattern, lower_query):
                matched.append(col)
                by_pattern = rf"\b(by|per|grouped by)\s+{re.escape(col_lower)}\b"
                if re.search(by_pattern, lower_query):
                    by_cols.append(col)

        return matched, by_cols

    def _extract_first_number(self, lower_query: str) -> int | None:
        """Extract the first integer from query string."""
        matches = re.findall(r"\b\d+\b", lower_query)
        if matches:
            return int(matches[0])
        return None

    def _extract_filter_operator_and_value(self, lower_query: str) -> tuple[str | None, Any | None]:
        """Extract comparison filter operator and numeric/text value."""
        operator: str | None = "eq"
        val: Any | None = None

        if "greater than" in lower_query or "above" in lower_query or "older than" in lower_query:
            operator = "gt"
        elif "less than" in lower_query or "below" in lower_query or "younger than" in lower_query:
            operator = "lt"
        elif "equal to" in lower_query or "equals" in lower_query:
            operator = "eq"

        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", lower_query)
        if numbers:
            try:
                num_val = float(numbers[0])
                val = int(num_val) if num_val.is_integer() else num_val
            except ValueError:
                val = numbers[0]

        return operator, val


__all__ = ["QueryParser"]
