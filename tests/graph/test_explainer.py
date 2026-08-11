"""Unit tests for Stage 7.8A Explainer Node."""

from langchain_core.messages import AIMessage

from csv_analytics_agent.execution.models import ExecutionResult, ExecutionStatus
from csv_analytics_agent.graph.explainer import (
    explainer_node,
    format_execution_explanation,
)
from csv_analytics_agent.graph.state import create_initial_state


def test_explainer_node_success_result() -> None:
    """Verify explainer emits the checkpoint-safe AnalysisResult narrative."""
    state = create_initial_state()
    state["last_analysis_result"] = {
        "status": "success",
        "narrative": "Calculated mean salary: 77,000.",
        "artifacts": [],
        "execution_time_ms": 12.5,
        "source": "deterministic_engine",
        "question": None,
        "dataset_hash": None,
        "metadata": {"column": "salary", "operation": "mean"},
        "error_type": None,
        "error_message": None,
    }

    update = explainer_node(state)
    assert "messages" in update
    assert len(update["messages"]) == 1

    msg = update["messages"][0]
    assert isinstance(msg, AIMessage)
    assert "77,000" in msg.content or "77000" in msg.content


def test_explainer_node_failed_result() -> None:
    """Verify formatting of a failed checkpoint-safe AnalysisResult."""
    state = create_initial_state()
    state["last_analysis_result"] = {
        "status": "failed",
        "narrative": "Column 'invalid_col' not found.",
        "artifacts": [],
        "execution_time_ms": 5.0,
        "source": "deterministic_engine",
        "question": None,
        "dataset_hash": None,
        "metadata": {},
        "error_type": "ColumnNotFound",
        "error_message": "Column 'invalid_col' not found.",
    }

    update = explainer_node(state)
    msg = update["messages"][0]

    assert isinstance(msg, AIMessage)
    assert "Column 'invalid_col' not found." in msg.content


def test_explainer_node_empty_last_result() -> None:
    """Verify fallback message when last_result is None and no AI message exists."""
    state = create_initial_state()
    state["router_decision"] = {"intent": "new_query", "next_node": "explainer"}
    assert state["last_analysis_result"] is None

    update = explainer_node(state)
    msg = update["messages"][0]

    assert isinstance(msg, AIMessage)
    assert "No execution result found in state" in msg.content


def test_explainer_node_chitchat() -> None:
    """Verify explainer handles CHITCHAT intent properly."""
    state = create_initial_state()
    state["router_decision"] = {"intent": "chitchat", "next_node": "explainer"}

    update = explainer_node(state)
    msg = update["messages"][0]
    assert isinstance(msg, AIMessage)
    assert "How can I help you analyze" in msg.content


def test_explainer_node_meta() -> None:
    """Verify explainer handles META intent properly."""
    state = create_initial_state()
    state["router_decision"] = {"intent": "meta", "next_node": "explainer"}

    update = explainer_node(state)
    msg = update["messages"][0]
    assert isinstance(msg, AIMessage)
    assert "I am a data analytics assistant" in msg.content


def test_explainer_node_unsupported() -> None:
    """Verify explainer handles UNSUPPORTED intent properly."""
    state = create_initial_state()
    state["router_decision"] = {"intent": "unsupported", "next_node": "explainer"}

    update = explainer_node(state)
    msg = update["messages"][0]
    assert isinstance(msg, AIMessage)
    assert "cannot answer general knowledge questions" in msg.content


def test_explainer_node_clarification() -> None:
    """Verify explainer handles CLARIFICATION intent properly."""
    state = create_initial_state()
    state["router_decision"] = {"intent": "clarification", "next_node": "explainer"}

    update = explainer_node(state)
    msg = update["messages"][0]
    assert isinstance(msg, AIMessage)
    assert "Could you please clarify" in msg.content


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
