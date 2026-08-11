"""Graph Assembly and Compilation module for LangGraph Agent Runtime."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from langchain_core.messages import AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

if TYPE_CHECKING:
    from csv_analytics_agent.memory.service import MemoryService

from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.checkpoint import RuntimeArtifactStore
from csv_analytics_agent.graph.explainer import explainer_node
from csv_analytics_agent.graph.memory_update import memory_update_node
from csv_analytics_agent.graph.planner import planner_node
from csv_analytics_agent.graph.retrieval import retrieval_node
from csv_analytics_agent.graph.router import RouterIntent, router_node
from csv_analytics_agent.graph.state import AgentState
from csv_analytics_agent.graph.tool_node import tool_node
from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.llm.python_generator import BasePythonCodeGenerator
from csv_analytics_agent.python_engine.base import BasePythonExecutor


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
        "last_analysis_result": None,
        "iteration_count": 0,
    }


def route_after_router(state: AgentState | dict[str, Any] | Any) -> str:
    """Conditional routing function evaluating router outcome.

    Args:
        state: AgentState instance containing router_decision, or RouterDecision object directly.

    Returns:
        Target node identifier string ('retrieval', 'planner', 'reset', 'explainer').
    """
    if hasattr(state, "intent"):
        intent = getattr(state, "intent", None)
        next_node_name = str(getattr(state, "next_node", ""))
    elif isinstance(state, dict):
        decision = state.get("router_decision") or state
        if hasattr(decision, "intent"):
            intent = getattr(decision, "intent", None)
            next_node_name = str(getattr(decision, "next_node", ""))
        elif isinstance(decision, dict):
            next_node_name = str(decision.get("next_node", ""))
            intent = decision.get("intent")
        else:
            intent = None
            next_node_name = ""
    else:
        intent = None
        next_node_name = ""

    intent_val = (
        str(intent.value)  # type: ignore[union-attr]
        if hasattr(intent, "value")
        else str(intent)
        if intent is not None
        else ""
    )

    if next_node_name == "reset" or intent_val == RouterIntent.RESET.value:
        return "reset"
    if next_node_name in ("meta", "unknown", "explainer") or intent_val in (
        RouterIntent.META.value,
        RouterIntent.UNKNOWN.value,
        RouterIntent.CHITCHAT.value,
        RouterIntent.UNSUPPORTED.value,
        RouterIntent.CLARIFICATION.value,
    ):
        return "explainer"
    if intent_val == RouterIntent.NEW_QUERY.value or next_node_name == "retrieval":
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
    python_generator: BasePythonCodeGenerator | None = None,
    python_executor: BasePythonExecutor | None = None,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
    artifact_store: RuntimeArtifactStore | None = None,
) -> CompiledStateGraph[AgentState, Any, Any]:
    """Construct and compile the LangGraph agent state graph workflow.

    Args:
        llm: Abstract BaseLLM provider dependency.
        registry: CapabilityRegistry instance containing registered domain engines.
        memory_service: MemoryService instance for vector retrieval and persistence.
        dataframe: Target dataset pandas DataFrame context.
        python_generator: Optional BasePythonCodeGenerator instance.
        python_executor: Optional BasePythonExecutor instance.
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
        lambda s: planner_node(
            s,
            llm=llm,
            registry=registry,
            dataframe=dataframe,
            python_generator=python_generator,
            python_executor=python_executor,
        ),
    )
    builder.add_node(
        "tool",
        lambda s: tool_node(
            s,
            registry=registry,
            dataframe=dataframe,
            python_generator=python_generator,
            python_executor=python_executor,
            artifact_store=artifact_store,
        ),
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
