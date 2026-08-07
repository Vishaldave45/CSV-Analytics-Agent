"""Deterministic Rule-Based Planner orchestrator implementation.

This module coordinates QueryParser and CapabilityMatcher to translate natural language
analytical queries into structured ExecutionRequest objects with full reasoning traces.
"""

from __future__ import annotations

from csv_analytics_agent.execution.models import ExecutionRequest
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.planner.matcher import CapabilityMatcher
from csv_analytics_agent.planner.models import (
    IntentType,
    PlannerMetadata,
    PlannerResult,
)
from csv_analytics_agent.planner.parser import QueryParser
from csv_analytics_agent.planner.rules import RuleEngine


class RulePlanner:
    """Deterministic rule-based query planner."""

    def __init__(
        self,
        parser: QueryParser | None = None,
        matcher: CapabilityMatcher | None = None,
    ) -> None:
        """Initialize RulePlanner with parser and matcher instances.

        Args:
            parser: QueryParser instance (defaults to default QueryParser if None).
            matcher: CapabilityMatcher instance (defaults to default CapabilityMatcher if None).
        """
        self._parser = parser or QueryParser(RuleEngine())
        self._matcher = matcher or CapabilityMatcher()

    @property
    def metadata(self) -> PlannerMetadata:
        return PlannerMetadata(
            name="rule_planner",
            version="1.0.0",
            description="Deterministic rule-based query planner translating text.",
        )

    def plan(
        self,
        query: str,
        available_columns: list[str],
        registry: CapabilityRegistry,
    ) -> PlannerResult:
        """Translate a natural language question into a PlannerResult.

        Args:
            query: Natural language query string.
            available_columns: List of valid column names in dataset.
            registry: CapabilityRegistry instance.

        Returns:
            PlannerResult payload containing ExecutionRequest, trace, and status.
        """
        if not query or not query.strip():
            return PlannerResult(
                confidence=0.0,
                reasoning_trace=["Empty query string received"],
                success=False,
                error_message="Query string cannot be empty.",
            )

        # 1. Parse Query & Extract Intent
        parsed_intent, rule, confidence, trace = self._parser.parse(query, available_columns)

        if parsed_intent.intent_type == IntentType.UNKNOWN or not rule:
            trace.append("Planning rejected: Unable to identify analytical intent from query")
            return PlannerResult(
                confidence=0.0,
                matched_rule=None,
                reasoning_trace=trace,
                success=False,
                error_message=f"Unsupported question: '{query}'. Could not resolve intent.",
            )

        matched_rule_desc = rule.description

        # 2. Match Capability in Registry
        descriptor, parameters, match_trace = self._matcher.match(parsed_intent, registry)
        trace.extend(match_trace)

        if not descriptor:
            cap_name = parsed_intent.intent_type.value
            trace.append(f"Planning rejected: Required capability '{cap_name}' is not registered")
            return PlannerResult(
                confidence=0.0,
                matched_rule=matched_rule_desc,
                reasoning_trace=trace,
                success=False,
                error_message=f"Capability '{cap_name}' is not available in registry.",
            )

        # 3. Build ExecutionRequest
        exec_request = ExecutionRequest(
            capability_name=descriptor.name,
            target_columns=parsed_intent.target_columns,
            parameters=parameters,
            context_metadata={"raw_query": query},
        )

        cols_str = str(parsed_intent.target_columns)
        success_msg = f"Constructed ExecutionRequest for '{descriptor.name}' on columns {cols_str}"
        trace.append(success_msg)

        return PlannerResult(
            execution_request=exec_request,
            confidence=confidence,
            matched_rule=matched_rule_desc,
            reasoning_trace=trace,
            success=True,
        )


__all__ = ["RulePlanner"]
