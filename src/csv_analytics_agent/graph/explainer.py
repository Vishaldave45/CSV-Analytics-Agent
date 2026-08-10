"""Explainer Node converting ExecutionResults into rich analytical responses."""

from __future__ import annotations

from typing import Any

import pandas as pd
from langchain_core.messages import AIMessage

from csv_analytics_agent.execution.models import ExecutionResult, ExecutionStatus
from csv_analytics_agent.graph.interpreter import interpret_execution_result
from csv_analytics_agent.graph.message_utils import extract_last_human_text
from csv_analytics_agent.graph.state import AgentState
from csv_analytics_agent.llm.base import BaseLLM


def format_execution_explanation(result: ExecutionResult) -> str:
    """Format an ExecutionResult into a deterministic Markdown explanation string.

    Args:
        result: ExecutionResult payload from the Execution Framework.

    Returns:
        Formatted Markdown text string.
    """
    lines: list[str] = []

    status_icon = "✅" if result.status == ExecutionStatus.SUCCESS else "❌"
    lines.append(f"### {status_icon} Analysis Outcome: {result.capability_name.title()}")
    lines.append(f"**Status**: `{result.status.value}`")
    lines.append(f"**Summary**: {result.message}\n")

    if result.data is not None:
        if isinstance(result.data, bytes):
            lines.append("#### 📊 Chart Generated")
            chart_type = result.metadata.get("chart_type", "visualization")
            title = result.metadata.get("title", "")
            if title:
                lines.append(f"> **Rendered `{chart_type}` chart: *{title}*.**")
            else:
                lines.append(f"> **Rendered `{chart_type}` chart image successfully.**")
        elif hasattr(result.data, "primary"):
            lines.append("#### 📊 Recommended Visualization Plan")
            primary = getattr(result.data, "primary", None)
            if primary:
                desc_text = f" ({primary.description})" if primary.description else ""
                lines.append(
                    f"- **Primary Chart**: `{primary.chart_type.value.upper()}` — "
                    f"*{primary.title}*{desc_text}"
                )
            alts = getattr(result.data, "alternatives", [])
            for alt in alts:
                lines.append(f"- **Alternative**: `{alt.chart_type.value.upper()}` — *{alt.title}*")
        elif isinstance(result.data, (dict, list)):
            lines.append("#### 📊 Result Data")
            lines.append(f"```json\n{result.data}\n```")
        else:
            lines.append("#### 📊 Result Data")
            lines.append(f"> **{result.data}**")
        lines.append("")

    if result.metadata:
        lines.append("#### 🔍 Evidence & Metadata")
        for key, val in sorted(result.metadata.items()):
            lines.append(f"- **{key}**: {val}")
        lines.append("")

    lines.append(f"_Execution Time: {result.execution_time_ms:.2f} ms_")
    return "\n".join(lines)


def explainer_node(
    state: AgentState,
    dataframe: pd.DataFrame | None = None,
    llm: BaseLLM | None = None,
) -> dict[str, Any]:
    """LangGraph node interpreting ExecutionResult into a structured, user-friendly response.

    Args:
        state: Active AgentState containing last_result and messages.
        dataframe: Optional DataFrame context for visualization and tables.
        llm: Optional BaseLLM provider instance for contextual narrative synthesis.

    Returns:
        Partial AgentState dictionary update containing emitted AIMessage and chart_bytes.
    """
    last_result: ExecutionResult | None = state.get("last_result")
    messages = state.get("messages", [])

    if last_result is None:
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content and not getattr(msg, "tool_calls", None):
                content_str = str(msg.content).strip()
                if content_str and content_str != "No execution result found in state to explain.":
                    return {"messages": [msg]}
        fallback_msg = AIMessage(content="No execution result found in state to explain.")
        return {"messages": [fallback_msg]}

    df = dataframe if dataframe is not None else state.get("working_df")
    if df is None:
        df = pd.DataFrame()

    user_query = extract_last_human_text(messages)
    analytical_resp = interpret_execution_result(
        user_query=user_query,
        result=last_result,
        df=df,
        llm=llm,
    )

    explanation_text = analytical_resp.to_markdown()
    ai_message = AIMessage(content=explanation_text)

    state_update: dict[str, Any] = {
        "messages": [ai_message],
        "chart_bytes": analytical_resp.chart_bytes,
    }
    return state_update


__all__ = [
    "explainer_node",
    "format_execution_explanation",
]
