"""Unit tests for Phase 3 QueryParser."""

from csv_analytics_agent.planner.models import IntentType
from csv_analytics_agent.planner.parser import QueryParser


def test_query_parser_aggregate_mean() -> None:
    parser = QueryParser()
    columns = ["salary", "age", "department"]
    parsed, rule, confidence, trace = parser.parse("What is the average salary?", columns)

    assert parsed.intent_type == IntentType.AGGREGATE
    assert parsed.target_columns == ["salary"]
    assert parsed.parameters["operation"] == "mean"
    assert confidence > 0.8
    assert len(trace) > 0


def test_query_parser_top_n() -> None:
    parser = QueryParser()
    columns = ["employee_id", "revenue", "department"]
    parsed, rule, confidence, trace = parser.parse("Top 10 revenue", columns)

    assert parsed.intent_type == IntentType.TOP_N
    assert parsed.target_columns == ["revenue"]
    assert parsed.parameters["n"] == 10
    assert parsed.parameters["order"] == "desc"


def test_query_parser_filter() -> None:
    parser = QueryParser()
    columns = ["age", "salary"]
    parsed, rule, confidence, trace = parser.parse("Filter age older than 30", columns)

    assert parsed.intent_type == IntentType.FILTER
    assert parsed.target_columns == ["age"]
    assert parsed.parameters["operator"] == "gt"
    assert parsed.parameters["value"] == 30


def test_query_parser_group_by() -> None:
    parser = QueryParser()
    columns = ["salary", "department"]
    parsed, rule, confidence, trace = parser.parse("Group sales by department", columns)

    assert parsed.intent_type == IntentType.GROUP
    assert "department" in parsed.target_columns
    assert parsed.parameters["by"] == "department"
