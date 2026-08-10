"""Unit tests for Stage 7.8A Explainer Node."""

from langchain_core.messages import AIMessage

from csv_analytics_agent.execution.models import ExecutionResult, ExecutionStatus
from csv_analytics_agent.graph.explainer import (
    explainer_node,
    format_execution_explanation,
)
from csv_analytics_agent.graph.state import create_initial_state


def test_explainer_node_success_result() -> None:
    """Verify deterministic formatting of a successful ExecutionResult."""
    state = create_initial_state()
    res: ExecutionResult = ExecutionResult(
        capability_name="aggregate",
        status=ExecutionStatus.SUCCESS,
        message="Calculated mean salary.",
        data=77000.0,
        execution_time_ms=12.5,
        metadata={"column": "salary", "operation": "mean"},
    )
    state["last_result"] = res

    update = explainer_node(state)
    assert "messages" in update
    assert len(update["messages"]) == 1

    msg = update["messages"][0]
    assert isinstance(msg, AIMessage)
    assert "77,000" in msg.content or "77000" in msg.content
    assert "salary" in msg.content.lower()
    assert "mean" in msg.content.lower()


def test_explainer_node_failed_result() -> None:
    """Verify formatting of a failed ExecutionResult."""
    state = create_initial_state()
    res: ExecutionResult = ExecutionResult(
        capability_name="filter",
        status=ExecutionStatus.FAILED,
        message="Column 'invalid_col' not found.",
        data=None,
        execution_time_ms=5.0,
    )
    state["last_result"] = res

    update = explainer_node(state)
    msg = update["messages"][0]

    assert isinstance(msg, AIMessage)
    assert "Execution Failed: Filter" in msg.content
    assert "Column 'invalid_col' not found." in msg.content


def test_explainer_node_empty_last_result() -> None:
    """Verify fallback message when last_result is None."""
    state = create_initial_state()
    assert state["last_result"] is None

    update = explainer_node(state)
    msg = update["messages"][0]

    assert isinstance(msg, AIMessage)
    assert "No execution result found in state" in msg.content


def test_format_execution_explanation_deterministic() -> None:
    """Verify deterministic output matching for identical ExecutionResult inputs."""
    res: ExecutionResult = ExecutionResult(
        capability_name="top_n",
        status=ExecutionStatus.SUCCESS,
        message="Extracted top 5 records.",
        data=5,
        execution_time_ms=8.0,
    )

    out1 = format_execution_explanation(res)
    out2 = format_execution_explanation(res)
    assert out1 == out2
    assert "Top_N" in out1


def test_format_execution_explanation_chart_bytes() -> None:
    """Verify that image bytes do not dump raw binary into markdown explanation."""
    res = ExecutionResult(
        capability_name="render_visualization",
        status=ExecutionStatus.SUCCESS,
        message="Rendered chart 'line' into PNG bytes.",
        data=b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR",
        metadata={"chart_type": "line", "title": "Revenue Trend"},
    )
    explanation = format_execution_explanation(res)
    assert "Chart Generated" in explanation
    assert "Revenue Trend" in explanation
    assert "b'\\x89PNG" not in explanation
