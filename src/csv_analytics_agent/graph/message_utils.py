"""Shared message utility helpers for LangGraph graph nodes."""

from __future__ import annotations

from langchain_core.messages import BaseMessage, HumanMessage


def extract_last_human_text(messages: list[BaseMessage] | None) -> str:
    """Extract string content of the last HumanMessage in conversation history.

    Args:
        messages: Conversation message list or None.

    Returns:
        Stripped string content of last user message, or empty string.
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
                joined = " ".join(texts).strip()
                if joined:
                    return joined

    return ""


__all__ = ["extract_last_human_text"]
