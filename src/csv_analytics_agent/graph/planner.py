"""LLM Planner Node for orchestrating tool selection without tool execution."""

from __future__ import annotations

from typing import Any

import pandas as pd
from langchain_core.messages import AIMessage, BaseMessage

from csv_analytics_agent.execution.models import ExecutionRequest
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.adapter import as_langchain_tools
from csv_analytics_agent.graph.checkpoint import json_safe
from csv_analytics_agent.graph.models import PlannerResult
from csv_analytics_agent.graph.state import AgentState
from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.llm.python_generator import BasePythonCodeGenerator
from csv_analytics_agent.logging_config import get_logger
from csv_analytics_agent.profiler.models import DatasetProfile
from csv_analytics_agent.python_engine.base import BasePythonExecutor
from csv_analytics_agent.python_engine.tool import create_python_analysis_tool

logger = get_logger(__name__)

DEFAULT_MAX_ITERATIONS = 6


def planner_node(
    state: AgentState,
    llm: BaseLLM,
    registry: CapabilityRegistry,
    dataframe: pd.DataFrame,
    python_generator: BasePythonCodeGenerator | None = None,
    python_executor: BasePythonExecutor | None = None,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
) -> dict[str, Any]:
    """LangGraph node binding execution tools to an LLM and generating tool calls.

    Args:
        state: Active AgentState containing messages and iteration_count.
        llm: Abstract BaseLLM instance.
        registry: CapabilityRegistry instance.
        dataframe: Target dataset pandas DataFrame context.
        python_generator: Optional BasePythonCodeGenerator instance.
        python_executor: Optional BasePythonExecutor instance.
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
            "planner_result": json_safe(planner_res.model_dump(mode="json")),
            "metadata": {
                **(state.get("metadata", {})),
                "next_node": "explainer",
                "loop_limit_exceeded": True,
            },
        }

    # 2. Discover Capabilities & Convert to StructuredTools via Stage 7.2 Adapter
    descriptors = registry.discover()
    tools = list(as_langchain_tools(descriptors, registry, dataframe))

    # 3. Add Python Analysis Tool if dependencies are provided
    if python_generator is not None and python_executor is not None:
        py_tool = create_python_analysis_tool(
            generator=python_generator,
            executor=python_executor,
            dataframe=dataframe,
            schema=(
                DatasetProfile.model_validate(state["profile"])
                if state.get("profile") is not None
                else None
            ),
            retrieved_columns=state.get("retrieved_columns"),
            dataset_hash=state.get("dataset_hash"),
        )
        tools.append(py_tool)

    # 4. Bind Tools to LLM & Invoke
    from csv_analytics_agent.prompts import get_planner_prompt

    col_descriptions: list[str] = []
    for col in dataframe.columns:
        dtype_str = str(dataframe[col].dtype)
        if pd.api.types.is_numeric_dtype(dataframe[col]):
            col_descriptions.append(f"  - `{col}` (numeric, {dtype_str})")
        elif pd.api.types.is_datetime64_any_dtype(dataframe[col]):
            col_descriptions.append(f"  - `{col}` (datetime)")
        else:
            n_unique = dataframe[col].nunique()
            col_descriptions.append(f"  - `{col}` (categorical, {n_unique} unique values)")

    col_desc_text = "\n".join(col_descriptions)
    active_filters = state.get("active_filters", [])
    filters_text = str(active_filters) if active_filters else "None"

    system_prompt = get_planner_prompt().format(
        row_count=len(dataframe),
        column_descriptions=col_desc_text,
        active_filters_summary=filters_text,
    )

    from langchain_core.messages import SystemMessage

    raw_messages: list[BaseMessage] = state.get("messages", [])
    messages: list[BaseMessage] = [SystemMessage(content=system_prompt)] + [
        m for m in raw_messages if not isinstance(m, SystemMessage)
    ]

    bound_llm = llm.bind_tools(tools)

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
        # Allow top-level parameter passthrough when not nested under 'parameters'
        for k, v in args.items():
            if k not in ("target_columns", "parameters"):
                parameters.setdefault(k, v)

        descriptor = next(
            (desc for desc in descriptors if desc.name == call_name),
            None,
        )
        preferred_engine = (
            descriptor.preferred_execution_engine
            if descriptor and descriptor.preferred_execution_engine
            else "deterministic_engine"
        )
        output_contract = descriptor.output_contract if descriptor else None

        exec_request = ExecutionRequest(
            capability_name=call_name,
            target_columns=target_columns,
            parameters=parameters,
        )
        planner_result = PlannerResult(
            execution_request=exec_request,
            confidence=1.0,
            matched_rule=call_name,
            analysis_plan={
                "operation": call_name,
                "target_columns": target_columns,
                "parameters": parameters,
                "preferred_execution_engine": preferred_engine,
                "output_contract": output_contract,
            },
            reasoning_trace=[f"Selected capability '{call_name}' for execution."],
            success=True,
        )
    else:
        planner_result = PlannerResult(
            execution_request=None,
            confidence=0.5,
            matched_rule="direct_explanation",
            analysis_plan={
                "operation": "direct_explanation",
                "preferred_execution_engine": "deterministic_engine",
                "output_contract": {"type": "text"},
            },
            reasoning_trace=["No capability tool calls; direct explanation generated."],
            success=True,
        )

    # 4. Return State Update with Incremented Iteration Count & PlannerResult
    return {
        "messages": [response_msg],
        "iteration_count": iteration_count + 1,
        "planner_result": json_safe(planner_result.model_dump(mode="json")),
    }


__all__ = [
    "DEFAULT_MAX_ITERATIONS",
    "planner_node",
]
