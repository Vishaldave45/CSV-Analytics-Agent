"""Memory Update Node for persisting conversation context into MemoryService."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage

from csv_analytics_agent.execution.models import ExecutionResult
from csv_analytics_agent.graph.state import AgentState
from csv_analytics_agent.memory.models import MetadataValue
from csv_analytics_agent.memory.service import MemoryService


def _extract_user_text(messages: list[BaseMessage] | None) -> str:
    """Extract content of the latest HumanMessage in conversation history.

    Args:
        messages: Conversation message list or None.

    Returns:
        Stripped string content or empty string if absent.
    """
    if not messages:
        return ""

    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            content = msg.content
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):
                texts = [str(item) for item in content if isinstance(item, str)]
                return " ".join(texts).strip()

    return ""


def memory_update_node(
    state: AgentState,
    memory_service: MemoryService,
) -> dict[str, Any]:
    """LangGraph node persisting conversation question and execution outcome into MemoryService.

    Args:
        state: Active AgentState containing messages and last_result.
        memory_service: MemoryService instance for vector memory persistence.

    Returns:
        Partial AgentState update dictionary.
    """
    messages = state.get("messages", [])
    user_text = _extract_user_text(messages)
    last_result: ExecutionResult | None = state.get("last_result")

    if user_text and last_result is not None:
        narrative_text = (
            f"Question: {user_text} | "
            f"Capability: {last_result.capability_name} | "
            f"Result: {last_result.message}"
        )
        meta_payload: dict[str, MetadataValue] = {
            "capability": last_result.capability_name,
            "status": last_result.status.value,
        }

        memory_service.store(
            text=narrative_text,
            metadata=meta_payload,
        )

    return {}


__all__ = ["memory_update_node"]
