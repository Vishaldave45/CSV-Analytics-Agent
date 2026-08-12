"""Tests for the AgentResponse normalizer mapping logic."""

from langchain_core.messages import AIMessage

from csv_analytics_agent.graph.router import RouterIntent
from csv_analytics_agent.graph.state import create_initial_state
from csv_analytics_agent.models.response import AgentResponseType
from csv_analytics_agent.python_engine.models import PythonArtifactType
from csv_analytics_agent.results.models import AnalysisArtifact, AnalysisResult
from csv_analytics_agent.services.result_normalizer import normalize_state_to_response


def test_normalize_chitchat() -> None:
    """Verify chitchat routing produces a TEXT response type with the answer."""
    state = create_initial_state()
    state["router_decision"] = '{"intent": "chitchat"}'
    state["messages"] = [AIMessage(content="Hello! How can I help?")]

    response = normalize_state_to_response(state)
    assert response.type == AgentResponseType.TEXT
    assert response.answer == "Hello! How can I help?"
    assert response.table is None
    assert response.visualization is None


def test_normalize_clarification() -> None:
    """Verify clarification intent sets type to CLARIFICATION with suggestions."""
    state = create_initial_state()
    state["router_decision"] = {"intent": RouterIntent.CLARIFICATION.value}
    state["messages"] = [AIMessage(content="What do you mean by 'best'?")]

    response = normalize_state_to_response(state)
    assert response.type == AgentResponseType.CLARIFICATION
    assert response.answer == "What do you mean by 'best'?"
    assert len(response.suggestions) > 0


def test_normalize_table_result() -> None:
    """Verify analysis_result with a table produces TABLE response type."""
    state = create_initial_state()
    state["messages"] = [AIMessage(content="Here are the top products.")]

    table_art = AnalysisArtifact(
        artifact_id="123",
        artifact_type=PythonArtifactType.TABLE,
        name="top_products",
        payload={"data": [], "row_count": 5},
    )

    result = AnalysisResult(
        status="success",
        narrative="Here are the top products.",
        artifacts=[table_art],
    )
    # Mock how checkpoint serialization looks
    state["last_analysis_result"] = result.model_dump()

    response = normalize_state_to_response(state)
    assert response.type == AgentResponseType.TABLE
    assert response.answer == "Here are the top products."
    assert response.table is not None
    assert response.table.name == "top_products"
    assert response.visualization is None


def test_normalize_empty_table_result() -> None:
    """Verify empty result sets a default answer message."""
    state = create_initial_state()

    table_art = AnalysisArtifact(
        artifact_id="123",
        artifact_type=PythonArtifactType.TABLE,
        name="filtered_data",
        payload={"data": [], "row_count": 0},
    )
    result = AnalysisResult(
        status="success",
        artifacts=[table_art],
    )
    state["last_analysis_result"] = result.model_dump()

    response = normalize_state_to_response(state)
    assert response.type == AgentResponseType.TABLE
    assert "No matching records" in response.answer


def test_normalize_error_status() -> None:
    """Verify failed analysis result produces ERROR response."""
    state = create_initial_state()
    result = AnalysisResult.failure(
        error_type="ValueError",
        error_message="Invalid column requested",
    )
    state["last_analysis_result"] = result.model_dump()

    response = normalize_state_to_response(state)
    assert response.type == AgentResponseType.ERROR
    assert response.error == "Invalid column requested"
    assert "couldn't complete" in response.answer
    assert "Invalid column requested" in response.calculation


def test_normalize_table_and_chart() -> None:
    """Verify result with both table and chart produces TABLE_AND_CHART response."""
    state = create_initial_state()

    table_art = AnalysisArtifact(
        artifact_id="t1",
        artifact_type=PythonArtifactType.TABLE,
        name="data",
    )
    chart_art = AnalysisArtifact(
        artifact_id="c1",
        artifact_type=PythonArtifactType.IMAGE,
        name="chart",
    )
    result = AnalysisResult(
        status="success",
        artifacts=[table_art, chart_art],
    )
    state["last_analysis_result"] = result.model_dump()

    response = normalize_state_to_response(state)
    assert response.type == AgentResponseType.TABLE_AND_CHART
    assert response.table is not None
    assert response.visualization is not None
    assert len(response.artifacts) == 2
    assert response.artifacts[0].artifact_id == "t1"
    assert response.artifacts[1].artifact_id == "c1"


def test_normalize_raw_json_block_message() -> None:
    """Verify raw block JSON lists are recursively parsed into clean text."""
    state = create_initial_state()
    state["messages"] = [
        AIMessage(content='[{"type": "text", "text": "This is a clean explanation narrative."}]')
    ]

    response = normalize_state_to_response(state)
    assert response.type == AgentResponseType.TEXT
    assert response.answer == "This is a clean explanation narrative."


def test_normalize_python_repr_block_message() -> None:
    """Verify Python repr single-quote string representations with extras are parsed cleanly."""
    state = create_initial_state()
    raw_repr = (
        "[{'type': 'text', 'text': 'Clean narrative text.', 'extras': {'signature': 'EI4K...'}}]"
    )
    state["messages"] = [AIMessage(content=raw_repr)]

    response = normalize_state_to_response(state)
    assert response.type == AgentResponseType.TEXT
    assert response.answer == "Clean narrative text."
