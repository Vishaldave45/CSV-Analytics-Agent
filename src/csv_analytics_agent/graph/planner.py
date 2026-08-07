"""LLM Planner Node for orchestrating tool selection without tool execution."""

from __future__ import annotations

from typing import Any

import pandas as pd
from langchain_core.messages import AIMessage, BaseMessage

from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.adapter import as_langchain_tools
from csv_analytics_agent.graph.state import AgentState
from csv_analytics_agent.llm.base import BaseLLM

DEFAULT_MAX_ITERATIONS = 6


def planner_node(
    state: AgentState,
    llm: BaseLLM,
    registry: CapabilityRegistry,
    dataframe: pd.DataFrame,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
) -> dict[str, Any]:
    """LangGraph node binding execution tools to an LLM and generating tool calls.

    Args:
        state: Active AgentState containing messages and iteration_count.
        llm: Abstract BaseLLM instance.
        registry: CapabilityRegistry instance.
        dataframe: Target dataset pandas DataFrame context.
        max_iterations: Maximum loop iteration limit before routing to explainer (default 6).

    Returns:
        Partial AgentState dict update with response message and iteration_count.
    """
    iteration_count = state.get("iteration_count", 0)

    # 1. Loop Protection Check
    if iteration_count >= max_iterations:
        loop_msg = AIMessage(
            content=f"Maximum iteration limit ({max_iterations}) reached; routing to explainer."
        )
        return {
            "messages": [loop_msg],
            "iteration_count": iteration_count + 1,
            "metadata": {
                **(state.get("metadata", {})),
                "next_node": "explainer",
                "loop_limit_exceeded": True,
            },
        }

    # 2. Discover Capabilities & Convert to StructuredTools via Stage 7.2 Adapter
    descriptors = registry.discover()
    tools = as_langchain_tools(descriptors, registry, dataframe)

    # 3. Bind Tools to LLM & Invoke
    bound_llm = llm.bind_tools(tools)
    messages: list[BaseMessage] = state.get("messages", [])

    response_msg = bound_llm.invoke(messages)

    # 4. Return State Update with Incremented Iteration Count
    return {
        "messages": [response_msg],
        "iteration_count": iteration_count + 1,
    }


__all__ = [
    "DEFAULT_MAX_ITERATIONS",
    "planner_node",
]
