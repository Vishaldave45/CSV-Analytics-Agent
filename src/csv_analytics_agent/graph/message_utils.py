"""Shared message utility helpers for LangGraph graph nodes."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage


def normalize_message_content(content: Any) -> str:
    """Safely extract and normalize LangChain message content into a clean string.

    Handles:
        - str: returned stripped
        - None: returned as ""
        - list[dict]: extracts 'text' or 'content' keys from block dicts and joins them
        - list[str]: joins items with spaces
        - list[Any]: extracts string representations of text blocks
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                if item.strip():
                    parts.append(item.strip())
            elif isinstance(item, dict):
                txt = item.get("text") or item.get("content") or ""
                if isinstance(txt, str) and txt.strip():
                    parts.append(txt.strip())
                elif isinstance(txt, list):
                    sub_norm = normalize_message_content(txt)
                    if sub_norm:
                        parts.append(sub_norm)
            else:
                s_item = str(item).strip()
                if s_item:
                    parts.append(s_item)
        return " ".join(parts).strip()
    return str(content).strip()


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
            return normalize_message_content(msg.content)

    return ""


__all__ = ["extract_last_human_text", "normalize_message_content"]
