"""Graph Assembly and Compilation module for LangGraph Agent Runtime."""

from __future__ import annotations

from typing import Any

import pandas as pd
from langchain_core.messages import AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.explainer import explainer_node
from csv_analytics_agent.graph.memory_update import memory_update_node
from csv_analytics_agent.graph.planner import planner_node
from csv_analytics_agent.graph.retrieval import retrieval_node
from csv_analytics_agent.graph.router import RouterDecision, RouterIntent, router_node
from csv_analytics_agent.graph.state import AgentState
from csv_analytics_agent.graph.tool_node import tool_node
from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.memory.service import MemoryService


def reset_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node resetting active filters, retrieved columns, and session state.

    Args:
        state: Active AgentState instance.

    Returns:
        Partial AgentState dictionary update resetting context.
    """
    reset_msg = AIMessage(content="Session state and active dataset filters have been reset.")
    return {
        "messages": [reset_msg],
        "retrieved_columns": [],
        "active_filters": [],
        "last_result": None,
        "iteration_count": 0,
    }


def route_after_router(decision: RouterDecision | dict[str, Any]) -> str:
    """Conditional routing function evaluating router outcome.

    Args:
        decision: RouterDecision instance or dict state.

    Returns:
        Target node identifier string ('retrieval', 'planner', 'reset', 'explainer').
    """
    if isinstance(decision, RouterDecision):
        next_node_name = decision.next_node
        intent: Any = decision.intent
    elif isinstance(decision, dict):
        next_node_name = str(decision.get("next_node", ""))
        intent = decision.get("intent")
    else:
        return "planner"

    if next_node_name == "reset" or intent == RouterIntent.RESET:
        return "reset"
    if next_node_name in ("meta", "unknown") or intent in (
        RouterIntent.META,
        RouterIntent.UNKNOWN,
    ):
        return "explainer"
    if intent == RouterIntent.NEW_QUERY or next_node_name == "retrieval":
        return "retrieval"
    return "planner"


def route_after_planner(state: AgentState) -> str:
    """Conditional routing function determining if planner produced tool calls.

    Args:
        state: Active AgentState instance.

    Returns:
        Target node identifier string ('tool' or 'explainer').
    """
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, AIMessage) and getattr(last_msg, "tool_calls", None):
            return "tool"
    return "explainer"


def build_graph(
    llm: BaseLLM,
    registry: CapabilityRegistry,
    memory_service: MemoryService,
    dataframe: pd.DataFrame,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph[AgentState, Any, Any]:
    """Construct and compile the LangGraph agent state graph workflow.

    Args:
        llm: Abstract BaseLLM provider dependency.
        registry: CapabilityRegistry instance containing registered domain engines.
        memory_service: MemoryService instance for vector retrieval and persistence.
        dataframe: Target dataset pandas DataFrame context.
        checkpointer: Optional BaseCheckpointSaver instance for state persistence.

    Returns:
        CompiledStateGraph instance ready for invocation.
    """
    builder = StateGraph(AgentState)

    # 1. Register Graph Nodes
    builder.add_node("router", router_node)
    builder.add_node("retrieval", lambda s: retrieval_node(s, memory_service=memory_service))
    builder.add_node(
        "planner",
        lambda s: planner_node(s, llm=llm, registry=registry, dataframe=dataframe),
    )
    builder.add_node(
        "tool",
        lambda s: tool_node(s, registry=registry, dataframe=dataframe),
    )
    builder.add_node(
        "explainer",
        lambda s: explainer_node(s, dataframe=dataframe, llm=llm),
    )
    builder.add_node(
        "memory_update",
        lambda s: memory_update_node(s, memory_service=memory_service),
    )
    builder.add_node("reset", reset_node)

    # 2. Configure Entry Point & Edges
    builder.set_entry_point("router")

    builder.add_conditional_edges(
        "router",
        route_after_router,
        {
            "retrieval": "retrieval",
            "planner": "planner",
            "reset": "reset",
            "explainer": "explainer",
        },
    )

    builder.add_edge("retrieval", "planner")

    builder.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "tool": "tool",
            "explainer": "explainer",
        },
    )

    builder.add_edge("tool", "planner")
    builder.add_edge("explainer", "memory_update")
    builder.add_edge("memory_update", END)
    builder.add_edge("reset", END)

    # 3. Compile Graph with Checkpointer
    return builder.compile(checkpointer=checkpointer)


__all__ = [
    "build_graph",
    "reset_node",
    "route_after_planner",
    "route_after_router",
]
