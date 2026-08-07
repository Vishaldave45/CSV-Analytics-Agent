"""Unit tests for Phase 5 RulePlanner."""

import pytest

from csv_analytics_agent.execution.domain.analytics import AnalyticsEngine
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.planner.planner import RulePlanner


@pytest.fixture
def registered_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    engine = AnalyticsEngine()
    for desc in engine.list_capabilities():
        registry.register(desc, engine)
    return registry


def test_rule_planner_aggregate_success(registered_registry: CapabilityRegistry) -> None:
    planner = RulePlanner()
    columns = ["salary", "age", "department"]
    res = planner.plan("What is the average salary?", columns, registered_registry)

    assert res.success is True
    assert res.confidence > 0.8
    assert res.execution_request is not None
    assert res.execution_request.capability_name == "aggregate"
    assert res.execution_request.target_columns == ["salary"]
    assert res.execution_request.parameters["operation"] == "mean"
    assert "average" in str(res.matched_rule)
    assert len(res.reasoning_trace) > 0


def test_rule_planner_top_n_success(registered_registry: CapabilityRegistry) -> None:
    planner = RulePlanner()
    columns = ["employee_id", "revenue", "department"]
    res = planner.plan("Top 5 revenue", columns, registered_registry)

    assert res.success is True
    assert res.execution_request is not None
    assert res.execution_request.capability_name == "top_n"
    assert res.execution_request.target_columns == ["revenue"]
    assert res.execution_request.parameters["n"] == 5


def test_rule_planner_unregistered_capability() -> None:
    empty_registry = CapabilityRegistry()
    planner = RulePlanner()
    columns = ["salary"]
    res = planner.plan("What is the average salary?", columns, empty_registry)

    assert res.success is False
    assert res.execution_request is None
    assert "is not available" in str(res.error_message)


def test_rule_planner_empty_query(registered_registry: CapabilityRegistry) -> None:
    planner = RulePlanner()
    res = planner.plan("", ["salary"], registered_registry)

    assert res.success is False
    assert res.confidence == 0.0
    assert "empty" in str(res.error_message)
