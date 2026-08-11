"""Unit tests for AgentState and serialization-safe state utilities."""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph.message import add_messages

from csv_analytics_agent.graph.state import (
    AgentState,
    create_initial_state,
)
from csv_analytics_agent.profiler.models import (
    DatasetProfile,
    DatasetSummary,
    DuplicateSummary,
    MissingSummary,
)


def test_create_initial_state_defaults() -> None:
    """Verify default values in create_initial_state helper."""
    state = create_initial_state(thread_id="session_123")
    assert state["messages"] == []
    assert state["profile"] is None
    assert state["dataset_hash"] is None
    assert state["active_filters"] == []
    assert state["last_analysis_result"] is None
    assert state["retrieved_columns"] == []
    assert state["iteration_count"] == 0
    assert state["planner_result"] is None
    assert state["thread_id"] == "session_123"
    assert state["metadata"] == {}


def test_agent_state_message_accumulation() -> None:
    """Test message reducer accumulation behavior using add_messages."""
    msg1: BaseMessage = HumanMessage(content="What is the average salary?")
    msg2: BaseMessage = AIMessage(content="Calculating average salary...")

    left: list[BaseMessage] = [msg1]
    right: list[BaseMessage] = [msg2]

    combined = add_messages(left, right)  # type: ignore[arg-type]
    assert isinstance(combined, list)
    assert len(combined) == 2
    first_msg = combined[0]
    second_msg = combined[1]
    assert isinstance(first_msg, HumanMessage)
    assert isinstance(second_msg, AIMessage)
    assert first_msg.content == "What is the average salary?"
    assert second_msg.content == "Calculating average salary..."


def test_agent_state_contains_checkpoint_safe_values() -> None:
    """Verify AgentState stores JSON-compatible model representations."""
    profile = DatasetProfile(
        summary=DatasetSummary(row_count=2, column_count=1, memory_usage_bytes=128),
        columns=[],
        missing=MissingSummary(total_missing_values=0, columns_with_missing=0),
        duplicates=DuplicateSummary(duplicate_rows=0),
    )

    state: AgentState = {
        "messages": [HumanMessage(content="Hi")],
        "profile": profile.model_dump(mode="json"),
        "dataset_hash": "hash_abc",
        "active_filters": [{"capability": "filter", "target_columns": ["salary"]}],
        "last_analysis_result": {
            "status": "success",
            "narrative": "Aggregated mean.",
            "artifacts": [
                {
                    "artifact_id": "artifact_1",
                    "artifact_type": "scalar",
                    "name": "mean_salary",
                    "mime_type": None,
                    "title": "Mean Salary",
                    "description": None,
                    "metadata": {"unit": "USD"},
                    "downloadable": False,
                }
            ],
            "execution_time_ms": 12.5,
            "source": "deterministic_engine",
            "question": "What is the average salary?",
            "dataset_hash": "hash_abc",
            "metadata": {"capability": "aggregate"},
            "error_type": None,
            "error_message": None,
        },
        "retrieved_columns": ["salary"],
        "iteration_count": 1,
        "planner_result": {
            "confidence": 0.95,
            "matched_rule": "average -> mean",
            "reasoning_trace": ["Step 1"],
            "success": True,
        },
        "thread_id": "thread_1",
        "executed_tools": ["aggregate"],
        "metadata": {"source": "unit_test"},
    }

    assert state["profile"] is not None
    assert state["profile"]["summary"]["row_count"] == 2
    assert state["planner_result"] is not None
    assert state["planner_result"]["confidence"] == 0.95
    assert state["last_analysis_result"] is not None
    assert state["last_analysis_result"]["artifacts"][0]["artifact_id"] == "artifact_1"
    assert state["iteration_count"] == 1


def test_agent_state_partial_updates() -> None:
    """Test partial state dictionary updates expected during graph transitions."""
    state = create_initial_state()
    assert state["iteration_count"] == 0

    # Simulate node state update
    state_update: AgentState = {
        "iteration_count": state["iteration_count"] + 1,
        "retrieved_columns": ["age", "income"],
    }

    state.update(state_update)
    assert state["iteration_count"] == 1
    assert state["retrieved_columns"] == ["age", "income"]
