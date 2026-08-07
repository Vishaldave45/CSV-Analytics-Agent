"""Semantic column retrieval node for LangGraph agent workflows.

This module provides the `retrieval_node` function that uses MemoryService to query
dataset column indices and identify top-k relevant columns for downstream planning.
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage

from csv_analytics_agent.exceptions.data_errors import CSVAnalyticsError
from csv_analytics_agent.graph.state import AgentState
from csv_analytics_agent.memory.service import MemoryService


class RetrievalError(CSVAnalyticsError):
    """Base exception for column retrieval errors."""

    pass


class IndexNotFoundError(RetrievalError, ValueError):
    """Raised when the dataset column index is missing or empty in MemoryService."""

    pass


class EmptyQueryError(RetrievalError, ValueError):
    """Raised when the user query string is blank or missing from AgentState."""

    pass


def _extract_user_query(messages: list[BaseMessage] | None) -> str:
    """Extract string content from the last user message in conversation history.

    Args:
        messages: List of BaseMessage objects or None.

    Returns:
        Stripped user query string.

    Raises:
        EmptyQueryError: If no valid human query is found.
    """
    if not messages:
        raise EmptyQueryError("No conversation messages found in AgentState.")

    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            content = msg.content
            if isinstance(content, str) and content.strip():
                return content.strip()
            if isinstance(content, list):
                texts = [str(item) for item in content if isinstance(item, str)]
                joined = " ".join(texts).strip()
                if joined:
                    return joined

    raise EmptyQueryError("No valid human user query found in message history.")


def retrieval_node(
    state: AgentState,
    memory_service: MemoryService,
    top_k: int = 5,
) -> dict[str, Any]:
    """LangGraph node retrieving relevant dataset columns using MemoryService.

    Args:
        state: Current AgentState containing conversation message history.
        memory_service: Injected MemoryService instance containing indexed columns.
        top_k: Maximum number of relevant column names to retrieve (default 5).

    Returns:
        Dictionary update containing updated 'retrieved_columns' list.

    Raises:
        EmptyQueryError: If the latest user message is empty or missing.
        IndexNotFoundError: If the memory index is empty or unpopulated.
        RetrievalError: If memory service retrieval fails.
    """
    messages = state.get("messages", [])
    query_text = _extract_user_query(messages)

    if memory_service.count() == 0:
        err_msg = "Dataset column index is empty in MemoryService. Index must be populated."
        raise IndexNotFoundError(err_msg)

    results = memory_service.retrieve(query_text, top_k=top_k)

    retrieved_cols: list[str] = []
    for item in results:
        col_name = item.record.metadata.get("column_name")
        if isinstance(col_name, str) and col_name:
            if col_name not in retrieved_cols:
                retrieved_cols.append(col_name)
        else:
            txt = item.record.text.strip()
            if txt and txt not in retrieved_cols:
                retrieved_cols.append(txt)

    return {"retrieved_columns": retrieved_cols}


__all__ = [
    "EmptyQueryError",
    "IndexNotFoundError",
    "RetrievalError",
    "retrieval_node",
]
