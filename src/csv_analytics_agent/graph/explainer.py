"""Deterministic Explainer Node converting ExecutionResult payloads into structured AIMessages."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

from csv_analytics_agent.execution.models import ExecutionResult, ExecutionStatus
from csv_analytics_agent.graph.state import AgentState


def format_execution_explanation(result: ExecutionResult[Any]) -> str:
    """Format an ExecutionResult into a deterministic Markdown explanation string.

    Args:
        result: ExecutionResult payload from the Execution Framework.

    Returns:
        Formatted Markdown text string.
    """
    lines: list[str] = []

    # Title & Capability Header
    status_icon = "✅" if result.status == ExecutionStatus.SUCCESS else "❌"
    lines.append(f"### {status_icon} Analysis Outcome: {result.capability_name.title()}")
    lines.append(f"**Status**: `{result.status.value}`")
    lines.append(f"**Summary**: {result.message}\n")

    # Data / Answer Section
    if result.data is not None:
        lines.append("#### 📊 Result Data")
        if isinstance(result.data, (dict, list)):
            lines.append(f"```json\n{result.data}\n```")
        else:
            lines.append(f"> **{result.data}**")
        lines.append("")

    # Evidence & Metadata Section
    if result.metadata:
        lines.append("#### 🔍 Evidence & Metadata")
        for key, val in sorted(result.metadata.items()):
            lines.append(f"- **{key}**: {val}")
        lines.append("")

    # Performance / Timing Footer
    lines.append(f"_Execution Time: {result.execution_time_ms:.2f} ms_")

    return "\n".join(lines)


def explainer_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node formatting the latest ExecutionResult into an AIMessage response.

    Args:
        state: Active AgentState containing last_result.

    Returns:
        Partial AgentState dictionary update containing emitted AIMessage.
    """
    last_result: ExecutionResult[Any] | None = state.get("last_result")

    if last_result is None:
        fallback_msg = AIMessage(content="No execution result found in state to explain.")
        return {"messages": [fallback_msg]}

    explanation_text = format_execution_explanation(last_result)
    ai_message = AIMessage(content=explanation_text)

    return {"messages": [ai_message]}


__all__ = [
    "explainer_node",
    "format_execution_explanation",
]
