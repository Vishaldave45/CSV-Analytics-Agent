"""Unit tests for Phase 2 RuleEngine and IntentRule."""

from csv_analytics_agent.planner.models import IntentType
from csv_analytics_agent.planner.rules import IntentRule, RuleEngine


def test_intent_rule_creation() -> None:
    rule = IntentRule(
        capability_name="aggregate",
        intent_type=IntentType.AGGREGATE,
        keywords=["average", "mean"],
        default_parameters={"operation": "mean"},
        description="Average rule",
    )
    assert rule.capability_name == "aggregate"
    assert rule.intent_type == IntentType.AGGREGATE
    assert "average" in rule.keywords


def test_rule_engine_matching_average() -> None:
    engine = RuleEngine()
    rule, kw, score = engine.match_intent("What is the average salary?")
    assert rule is not None
    assert rule.capability_name == "aggregate"
    assert rule.default_parameters["operation"] == "mean"
    assert kw == "average"
    assert score > 0.8


def test_rule_engine_matching_top_n() -> None:
    engine = RuleEngine()
    rule, kw, score = engine.match_intent("Show top 5 employees")
    assert rule is not None
    assert rule.capability_name == "top_n"
    assert rule.default_parameters["order"] == "desc"
    assert kw == "top"
    assert score > 0.8


def test_rule_engine_unmatched() -> None:
    engine = RuleEngine()
    rule, kw, score = engine.match_intent("gibberish query with no intent")
    assert rule is None
    assert kw is None
    assert score == 0.0
