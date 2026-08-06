"""Centralized constants and rule IDs for the Insights Engine."""

from __future__ import annotations

# Threshold constants for rule evaluation
HIGH_MISSING_THRESHOLD: float = 30.0
MEDIUM_MISSING_THRESHOLD: float = 10.0
HIGH_CARDINALITY_THRESHOLD: int = 100

# Centralized Rule Programmatic Identifiers
RULE_ID_HIGH_MISSING: str = "MISSING_HIGH"
RULE_ID_MEDIUM_MISSING: str = "MISSING_MEDIUM"
RULE_ID_DUPLICATES: str = "DUPLICATE_ROWS"
RULE_ID_IDENTIFIER: str = "POSSIBLE_IDENTIFIER"
RULE_ID_HIGH_CARDINALITY: str = "HIGH_CARDINALITY"
