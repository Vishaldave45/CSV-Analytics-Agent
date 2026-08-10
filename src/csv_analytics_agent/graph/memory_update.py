"""Memory Update Node for persisting conversation context into MemoryService."""

from __future__ import annotations

from typing import Any

from csv_analytics_agent.execution.models import ExecutionResult
from csv_analytics_agent.graph.message_utils import extract_last_human_text
from csv_analytics_agent.graph.state import AgentState
from csv_analytics_agent.memory.models import MetadataValue
from csv_analytics_agent.memory.service import MemoryService


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
    user_text = extract_last_human_text(messages)
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
