"""LLM Planner Node for orchestrating tool selection without tool execution."""

from __future__ import annotations

from typing import Any

import pandas as pd
from langchain_core.messages import AIMessage, BaseMessage

from csv_analytics_agent.execution.models import ExecutionRequest
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.adapter import as_langchain_tools
from csv_analytics_agent.graph.models import PlannerResult
from csv_analytics_agent.graph.state import AgentState
from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.logging_config import get_logger

logger = get_logger(__name__)

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
        Partial AgentState dict update with response message, iteration_count, and planner_result.
    """
    iteration_count = state.get("iteration_count", 0)

    # 1. Loop Protection Check
    if iteration_count >= max_iterations:
        loop_msg = AIMessage(
            content=f"Maximum iteration limit ({max_iterations}) reached; routing to explainer."
        )
        planner_res = PlannerResult(
            confidence=0.0,
            matched_rule="loop_limit_exceeded",
            reasoning_trace=[f"Loop limit {max_iterations} exceeded."],
            success=False,
            error_message=f"Maximum iteration limit ({max_iterations}) reached.",
        )
        return {
            "messages": [loop_msg],
            "iteration_count": iteration_count + 1,
            "planner_result": planner_res,
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

    logger.info(
        "planner_invoke",
        iteration=iteration_count,
        tools_bound=len(tools),
    )
    response_msg = bound_llm.invoke(messages)

    tool_calls = getattr(response_msg, "tool_calls", None) or []
    has_tool_calls = bool(tool_calls)
    logger.info(
        "planner_response",
        iteration=iteration_count,
        has_tool_calls=has_tool_calls,
    )

    if has_tool_calls:
        first_call = tool_calls[0]
        call_name = str(first_call.get("name", "unknown"))
        args = dict(first_call.get("args", {}))
        target_columns = list(args.get("target_columns", []))
        parameters = dict(args.get("parameters", {}))
        exec_request = ExecutionRequest(
            capability_name=call_name,
            target_columns=target_columns,
            parameters=parameters,
        )
        planner_result = PlannerResult(
            execution_request=exec_request,
            confidence=1.0,
            matched_rule=call_name,
            reasoning_trace=[f"Selected capability '{call_name}' for execution."],
            success=True,
        )
    else:
        planner_result = PlannerResult(
            execution_request=None,
            confidence=0.5,
            matched_rule="direct_explanation",
            reasoning_trace=["No capability tool calls; direct explanation generated."],
            success=True,
        )

    # 4. Return State Update with Incremented Iteration Count & PlannerResult
    return {
        "messages": [response_msg],
        "iteration_count": iteration_count + 1,
        "planner_result": planner_result,
    }


__all__ = [
    "DEFAULT_MAX_ITERATIONS",
    "planner_node",
]
