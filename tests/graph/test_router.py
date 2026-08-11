"""Unit tests for Stage 7.3 Router Node."""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from csv_analytics_agent.graph.router import (
    RouterIntent,
    router_node,
)
from csv_analytics_agent.graph.state import AgentState, create_initial_state


def test_router_new_query() -> None:
    """Verify routing of a standalone new analytical query."""
    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="What is the average salary?")
    state["messages"] = [msg]

    update = router_node(state)
    decision = update.get("router_decision")
    assert decision is not None
    assert decision["intent"] == RouterIntent.NEW_QUERY
    assert decision["next_node"] == "planner"
    assert decision["confidence"] == 0.9
    assert "analytical query" in decision["reason"]


def test_router_follow_up_query() -> None:
    """Verify routing of a follow-up query when conversation history exists."""
    msg1: BaseMessage = HumanMessage(content="What is the average salary?")
    msg2: BaseMessage = AIMessage(content="The average salary is $77,000.")
    msg3: BaseMessage = HumanMessage(content="What about the IT department?")

    state: AgentState = {
        "messages": [msg1, msg2, msg3],
        "active_filters": [{"column": "department", "eq": "IT"}],
    }

    update = router_node(state)
    decision = update.get("router_decision")
    assert decision is not None
    assert decision["intent"] == RouterIntent.FOLLOW_UP
    assert decision["next_node"] == "planner"
    assert decision["confidence"] == 0.9
    assert decision["metadata"]["human_message_count"] == 2


def test_router_reset_command() -> None:
    """Verify routing of reset/start over commands."""
    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="Start over and clear filters")
    state["messages"] = [msg]

    update = router_node(state)
    decision = update.get("router_decision")
    assert decision is not None
    assert decision["intent"] == RouterIntent.RESET
    assert decision["next_node"] == "reset"
    assert decision["confidence"] == 1.0


def test_router_meta_help_command() -> None:
    """Verify routing of help and capability commands."""
    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="What capabilities are available?")
    state["messages"] = [msg]

    update = router_node(state)
    decision = update.get("router_decision")
    assert decision is not None
    assert decision["intent"] == RouterIntent.META
    assert decision["next_node"] == "meta"
    assert decision["confidence"] == 1.0


def test_router_empty_messages() -> None:
    """Verify routing outcome when message list is empty."""
    state = create_initial_state()
    update = router_node(state)
    decision = update.get("router_decision")
    assert decision is not None

    assert decision["intent"] == RouterIntent.UNKNOWN
    assert decision["next_node"] == "unknown"
    assert decision["confidence"] == 0.0


def test_router_unknown_query() -> None:
    """Verify routing outcome for blank or single character query."""
    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="?")
    state["messages"] = [msg]

    update = router_node(state)
    decision = update.get("router_decision")
    assert decision is not None
    assert decision["intent"] == RouterIntent.UNKNOWN
    assert decision["next_node"] == "unknown"
    assert decision["confidence"] == 0.0


def test_router_chitchat_query() -> None:
    """Verify chitchat queries route to the explainer rather than analytics."""
    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="hiii")
    state["messages"] = [msg]

    update = router_node(state)
    decision = update.get("router_decision")
    assert decision is not None
    assert decision["intent"] == RouterIntent.CHITCHAT
    assert decision["next_node"] == "explainer"
    assert decision["confidence"] == 0.8
    assert decision["metadata"]["category"] == "chitchat"


def test_router_unsupported_query() -> None:
    """Verify outside-domain queries route to the explainer."""
    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="What is the capital of France?")
    state["messages"] = [msg]

    update = router_node(state)
    decision = update.get("router_decision")
    assert decision is not None
    assert decision["intent"] == RouterIntent.UNSUPPORTED
    assert decision["next_node"] == "explainer"
    assert decision["metadata"]["category"] == "unsupported"


def test_router_ambiguous_query_without_context() -> None:
    """Verify ambiguous dataset questions request clarification when no prior context exists."""
    state = create_initial_state()
    msg: BaseMessage = HumanMessage(content="What is the best product?")
    state["messages"] = [msg]

    update = router_node(state)
    decision = update.get("router_decision")
    assert decision is not None
    assert decision["intent"] == RouterIntent.CLARIFICATION
    assert decision["next_node"] == "explainer"
    assert decision["metadata"]["category"] == "clarification"


def test_router_partial_state() -> None:
    """Verify router stability when given a minimal partial AgentState dict."""
    msg: BaseMessage = HumanMessage(content="Help")
    partial_state: AgentState = {"messages": [msg]}

    update = router_node(partial_state)
    decision = update.get("router_decision")
    assert decision is not None
    assert decision["intent"] == RouterIntent.META
    assert decision["next_node"] == "meta"
