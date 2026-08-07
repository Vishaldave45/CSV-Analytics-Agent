"""Unit tests for Phase 1 planner domain models."""

import pytest
from pydantic import ValidationError

from csv_analytics_agent.execution.models import ExecutionRequest
from csv_analytics_agent.planner.models import (
    IntentType,
    Parameter,
    ParsedIntent,
    PlannerMetadata,
    PlannerResult,
)


def test_intent_type_enum() -> None:
    """Verify IntentType enum values."""
    assert IntentType.AGGREGATE.value == "aggregate"
    assert IntentType.FILTER.value == "filter"
    assert IntentType.GROUP.value == "group"
    assert IntentType.SORT.value == "sort"
    assert IntentType.TOP_N.value == "top_n"
    assert IntentType.UNKNOWN.value == "unknown"


def test_parameter_model() -> None:
    """Test Parameter model immutability."""
    param = Parameter(name="operation", value="mean", raw_text="average")
    assert param.name == "operation"
    assert param.value == "mean"
    assert param.raw_text == "average"

    with pytest.raises(ValidationError):
        setattr(param, "name", "new_name")  # noqa: B010


def test_parsed_intent_model() -> None:
    """Test ParsedIntent creation and validation."""
    intent = ParsedIntent(
        intent_type=IntentType.AGGREGATE,
        target_columns=["salary"],
        parameters={"operation": "mean"},
        raw_query="What is the average salary?",
    )
    assert intent.intent_type == IntentType.AGGREGATE
    assert intent.target_columns == ["salary"]
    assert intent.parameters["operation"] == "mean"


def test_planner_metadata_model() -> None:
    """Test PlannerMetadata creation."""
    meta = PlannerMetadata(
        name="rule_planner",
        version="1.0.0",
        description="Deterministic rule-based query planner.",
    )
    assert meta.name == "rule_planner"


def test_planner_result_success() -> None:
    """Test PlannerResult success construction with reasoning trace."""
    req = ExecutionRequest(
        capability_name="aggregate",
        target_columns=["salary"],
        parameters={"operation": "mean"},
    )
    res = PlannerResult(
        execution_request=req,
        confidence=0.95,
        matched_rule="average -> aggregate(mean)",
        reasoning_trace=["Parsed query", "Matched synonym 'average'", "Created request"],
        success=True,
    )
    assert res.success is True
    assert res.confidence == 0.95
    assert res.execution_request is not None
    assert res.execution_request.capability_name == "aggregate"
    assert len(res.reasoning_trace) == 3


def test_planner_result_failure() -> None:
    """Test PlannerResult rejection construction."""
    res = PlannerResult(
        confidence=0.0,
        reasoning_trace=["Query unrecognized"],
        success=False,
        error_message="Unsupported question intent.",
    )
    assert res.success is False
    assert res.execution_request is None
    assert res.error_message == "Unsupported question intent."
