"""Unit tests for Phase 4 CapabilityMatcher."""

from csv_analytics_agent.execution.domain.analytics import AnalyticsEngine
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.planner.matcher import CapabilityMatcher
from csv_analytics_agent.planner.models import IntentType, ParsedIntent


def test_capability_matcher_success() -> None:
    registry = CapabilityRegistry()
    engine = AnalyticsEngine()
    for desc in engine.list_capabilities():
        registry.register(desc, engine)

    matcher = CapabilityMatcher()
    intent = ParsedIntent(
        intent_type=IntentType.AGGREGATE,
        target_columns=["salary"],
        parameters={"operation": "mean"},
        raw_query="What is the average salary?",
    )

    descriptor, params, trace = matcher.match(intent, registry)
    assert descriptor is not None
    assert descriptor.name == "aggregate"
    assert params["operation"] == "mean"
    assert len(trace) > 0


def test_capability_matcher_unregistered() -> None:
    registry = CapabilityRegistry()
    matcher = CapabilityMatcher()
    intent = ParsedIntent(
        intent_type=IntentType.AGGREGATE,
        target_columns=["salary"],
        parameters={"operation": "mean"},
        raw_query="What is the average salary?",
    )

    descriptor, params, trace = matcher.match(intent, registry)
    assert descriptor is None
    assert params == {}
    assert "is not registered" in trace[-1]
