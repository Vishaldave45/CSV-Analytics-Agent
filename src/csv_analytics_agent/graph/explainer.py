"""Explainer Node converting ExecutionResults into rich analytical responses."""

from __future__ import annotations

from typing import Any

import pandas as pd
from langchain_core.messages import AIMessage

from csv_analytics_agent.execution.models import ExecutionResult, ExecutionStatus
from csv_analytics_agent.graph.message_utils import (
    normalize_message_content,
)
from csv_analytics_agent.graph.router import RouterIntent
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
        state: Active AgentState containing last_analysis_result, messages, and router_decision.
        dataframe: Optional DataFrame context for visualization and tables.
        llm: Optional BaseLLM provider instance for contextual narrative synthesis.

    Returns:
        Partial AgentState dictionary update containing emitted AIMessage.
    """
    messages = state.get("messages", [])
    router_decision = state.get("router_decision") or {}
    intent_str = str(router_decision.get("intent", ""))

    # 1. Check for specific non-analytical intents handled directly by the explainer
    if intent_str == RouterIntent.DATASET_METADATA.value:
        if dataframe is not None:
            r_cnt, c_cnt = len(dataframe), len(dataframe.columns)
            cols_str = ", ".join(f"`{col}`" for col in dataframe.columns)
            msg_content = f"The loaded dataset contains **{r_cnt:,} rows** and **{c_cnt} columns**:\n{cols_str}"
        elif state.get("profile") is not None:
            prof = state["profile"]
            r_cnt = 0
            c_cnt = 0
            if isinstance(prof, dict):
                summary = prof.get("summary")
                if isinstance(summary, dict):
                    r_val = summary.get("row_count", 0)
                    c_val = summary.get("column_count", 0)
                    r_cnt = int(str(r_val)) if r_val is not None else 0
                    c_cnt = int(str(c_val)) if c_val is not None else 0
            msg_content = f"The dataset contains **{r_cnt:,} rows** and **{c_cnt} columns**."
        else:
            msg_content = "Dataset metadata is currently unavailable."
        return {"messages": [AIMessage(content=msg_content)]}

    if intent_str == RouterIntent.CHITCHAT.value:
        return {
            "messages": [AIMessage(content="Hello! How can I help you analyze your dataset today?")]
        }
    if intent_str == RouterIntent.META.value:
        return {
            "messages": [
                AIMessage(
                    content="I am a data analytics assistant. I can help you filter, group, aggregate, sort, and visualize your dataset. Just ask me a question!"
                )
            ]
        }
    if intent_str == RouterIntent.UNSUPPORTED.value:
        return {
            "messages": [
                AIMessage(
                    content="I specialize in analyzing the loaded CSV dataset, but I cannot answer general knowledge questions outside of this dataset."
                )
            ]
        }
    if intent_str == RouterIntent.CLARIFICATION.value:
        return {
            "messages": [
                AIMessage(
                    content="Could you please clarify your question? For example, specify which column or metric you'd like to analyze."
                )
            ]
        }

    # 2. Check for analytical execution results
    checkpoint_result = state.get("last_analysis_result")

    if checkpoint_result is None:
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content and not getattr(msg, "tool_calls", None):
                content_str = normalize_message_content(msg.content)
                if content_str and content_str != "No execution result found in state to explain.":
                    return {"messages": [AIMessage(content=content_str)]}
        fallback_msg = AIMessage(content="No execution result found in state to explain.")
        return {"messages": [fallback_msg]}

    # Payloads are not checkpointed; the UI rehydrates them from its runtime store.
    return {"messages": [AIMessage(content=checkpoint_result["narrative"])]}


__all__ = [
    "explainer_node",
    "format_execution_explanation",
]
