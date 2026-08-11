"""Unit tests verifying full-graph chitchat routing flow and UI-level intent handlers."""

from langchain_core.messages import AIMessage, HumanMessage

from csv_analytics_agent.graph.build import route_after_router
from csv_analytics_agent.graph.explainer import explainer_node
from csv_analytics_agent.graph.router import RouterIntent, router_node
from csv_analytics_agent.graph.state import create_initial_state


def test_router_outputs_state_dict() -> None:
    """Verify router_node returns a state update dictionary, not a Pydantic model."""
    state = create_initial_state()
    state["messages"] = [HumanMessage(content="hello")]

    update = router_node(state)

    assert isinstance(update, dict)
    assert "router_decision" in update
    decision_dict = update["router_decision"]
    assert decision_dict["intent"] == RouterIntent.CHITCHAT.value
    assert decision_dict["next_node"] == "explainer"


def test_route_after_router_reads_state_dict() -> None:
    """Verify route_after_router correctly reads the new dictionary state structure."""
    state = create_initial_state()
    state["router_decision"] = {
        "intent": RouterIntent.CHITCHAT.value,
        "next_node": "explainer",
        "confidence": 0.9,
    }

    next_node = route_after_router(state)
    assert next_node == "explainer"


def test_explainer_handles_chitchat() -> None:
    """Verify explainer_node detects chitchat intent and returns a friendly greeting."""
    state = create_initial_state()
    state["router_decision"] = {
        "intent": RouterIntent.CHITCHAT.value,
        "next_node": "explainer",
    }

    update = explainer_node(state)
    assert "messages" in update
    msg = update["messages"][0]
    assert isinstance(msg, AIMessage)
    assert "Hello" in msg.content or "How can I help" in msg.content


def test_explainer_handles_meta() -> None:
    """Verify explainer_node detects meta intent and returns capabilities."""
    state = create_initial_state()
    state["router_decision"] = {
        "intent": RouterIntent.META.value,
        "next_node": "explainer",
    }

    update = explainer_node(state)
    msg = update["messages"][0]
    assert isinstance(msg, AIMessage)
    assert "filter, group, aggregate" in msg.content


def test_full_chitchat_flow_simulation() -> None:
    """Simulate the router -> conditional edge -> explainer flow for a chitchat message."""
    state = create_initial_state()
    state["messages"] = [HumanMessage(content="thanks")]

    # 1. Router classifies
    router_update = router_node(state)
    state.update(router_update)

    assert state["router_decision"]["intent"] == RouterIntent.CHITCHAT.value

    # 2. Conditional edge routes
    next_node = route_after_router(state)
    assert next_node == "explainer"

    # 3. Explainer responds
    explainer_update = explainer_node(state)
    assert "messages" in explainer_update
    assert "Hello" in explainer_update["messages"][0].content
