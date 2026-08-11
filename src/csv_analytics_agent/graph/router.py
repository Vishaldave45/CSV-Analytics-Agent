"""Deterministic Router Node for LangGraph agent workflows.

This module provides the deterministic `router_node` function and immutable `RouterDecision`
models used to route incoming user queries to graph destinations without LLM invocation.
"""

from __future__ import annotations

import re
from enum import Enum

from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel, ConfigDict, Field

from csv_analytics_agent.graph.message_utils import normalize_message_content
from csv_analytics_agent.graph.state import AgentState

RESET_KEYWORDS = {
    "reset",
    "start over",
    "clear filters",
    "clear context",
    "restart",
    "clear",
}

META_KEYWORDS = {
    "help",
    "what can you do",
    "show capabilities",
    "what capabilities",
    "usage",
    "commands",
    "capabilities",
}

FOLLOW_UP_PREFIXES = (
    "what about",
    "and for",
    "how about",
    "filter by",
    "also show",
    "now group",
    "now sort",
    "instead of",
)

CHITCHAT_PATTERNS = (
    r"^h(i)+$",
    r"^hi$",
    r"^hello$",
    r"^hey$",
    r"^good morning$",
    r"^good afternoon$",
    r"^good evening$",
    r"^thanks$",
    r"^thank you$",
    r"^thank you so much$",
    r"^thanks a lot$",
    r"^thank you very much$",
)

UNSUPPORTED_PATTERNS = (
    "capital of",
    "what is the capital",
    "population",
    "country",
    "state",
    "language",
    "president",
    "movie",
    "book",
    "author",
    "history",
    "geography",
    "define ",
)

AMBIGUOUS_PATTERNS = (
    r"\bbest\b.*\b(category|product|department|group|segment|option)\b",
    r"\btop\b.*\b(category|product|department|group|segment|option)\b",
    r"\bhighest\b.*\b(category|product|department|group|segment|option)\b",
    r"\blowest\b.*\b(category|product|department|group|segment|option)\b",
)


class RouterIntent(str, Enum):
    """High-level query routing intent category."""

    NEW_QUERY = "new_query"
    FOLLOW_UP = "follow_up"
    RESET = "reset"
    META = "meta"
    CHITCHAT = "chitchat"
    UNSUPPORTED = "unsupported"
    CLARIFICATION = "clarification"
    UNKNOWN = "unknown"


class RouterDecision(BaseModel):
    """Immutable payload representing a deterministic routing decision.

    Attributes:
        intent: Classified routing intent category.
        confidence: Confidence score of classification (0.0 to 1.0).
        reason: Explanation trace detailing why this route was selected.
        next_node: Programmatic target node name for StateGraph transitions.
        metadata: Contextual routing metadata dictionary.
    """

    model_config = ConfigDict(frozen=True)

    intent: RouterIntent = Field(..., description="Classified query routing intent.")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Classification confidence score between 0.0 and 1.0.",
    )
    reason: str = Field(..., min_length=1, description="Reasoning trace explanation.")
    next_node: str = Field(..., min_length=1, description="Target graph node identifier.")
    metadata: dict[str, str | int | float | bool] = Field(
        default_factory=dict,
        description="Routing metadata payload.",
    )


def _extract_last_user_text(messages: list[BaseMessage] | None) -> str:
    """Extract string content of the last HumanMessage in conversation history.

    Args:
        messages: Conversation message list or None.

    Returns:
        Lowercased stripped content of last user message, or empty string.
    """
    if not messages:
        return ""

    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            return normalize_message_content(msg.content).lower()

    # Fallback to last message string representation if no explicit HumanMessage found
    last_content = messages[-1].content
    return normalize_message_content(last_content).lower()


def _matches_patterns(text: str, patterns: tuple[str, ...]) -> bool:
    """Check whether normalized text matches any provided substring or regex pattern."""
    import re

    for pattern in patterns:
        if pattern.startswith("^") or pattern.endswith("$") or "\\b" in pattern:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return True
        elif pattern in text:
            return True
    return False


def router_node(state: AgentState) -> RouterDecision:
    """Deterministic router node evaluating AgentState to select next graph destination.

    Args:
        state: AgentState dictionary containing messages, active_filters, and metadata.

    Returns:
        Immutable RouterDecision defining target next_node and routing intent.
    """
    messages = state.get("messages", [])
    active_filters = state.get("active_filters", [])
    text = _extract_last_user_text(messages)

    if not text:
        return RouterDecision(
            intent=RouterIntent.UNKNOWN,
            confidence=0.0,
            reason="Empty message history or blank user query received.",
            next_node="unknown",
            metadata={"message_count": len(messages)},
        )

    # 1. Check RESET Intent
    if any(kw in text for kw in RESET_KEYWORDS):
        return RouterDecision(
            intent=RouterIntent.RESET,
            confidence=1.0,
            reason=f"Matched reset command keyword in user text: '{text}'.",
            next_node="reset",
            metadata={"matched_text": text},
        )

    # 2. Check META / HELP Intent
    if any(kw in text for kw in META_KEYWORDS):
        return RouterDecision(
            intent=RouterIntent.META,
            confidence=1.0,
            reason=f"Matched system metadata/help command in user text: '{text}'.",
            next_node="meta",
            metadata={"matched_text": text},
        )

    # 3. Check CHITCHAT Intent
    if _matches_patterns(text, CHITCHAT_PATTERNS):
        return RouterDecision(
            intent=RouterIntent.CHITCHAT,
            confidence=0.8,
            reason=f"Classified chitchat query, skipping analytical execution: '{text}'.",
            next_node="explainer",
            metadata={"matched_text": text, "category": "chitchat"},
        )

    # 4. Check UNSUPPORTED / OUT-OF-DOMAIN Intent
    if _matches_patterns(text, UNSUPPORTED_PATTERNS):
        return RouterDecision(
            intent=RouterIntent.UNSUPPORTED,
            confidence=0.6,
            reason=f"Classified unsupported outside-dataset query: '{text}'.",
            next_node="explainer",
            metadata={"matched_text": text, "category": "unsupported"},
        )

    # 5. Check FOLLOW_UP Intent
    human_msg_count = sum(
        1 for m in messages if isinstance(m, HumanMessage) or getattr(m, "type", "") == "human"
    )
    has_prior_context = human_msg_count > 1 or len(active_filters) > 0

    if has_prior_context and (
        text.startswith(FOLLOW_UP_PREFIXES) or "what about" in text or "filter by" in text
    ):
        return RouterDecision(
            intent=RouterIntent.FOLLOW_UP,
            confidence=0.9,
            reason="Detected follow-up query phrasing with existing conversation context.",
            next_node="planner",
            metadata={
                "human_message_count": human_msg_count,
                "active_filter_count": len(active_filters),
            },
        )

    # 6. Check AMBIGUOUS CATEGORY
    if _matches_patterns(text, AMBIGUOUS_PATTERNS) and not has_prior_context:
        return RouterDecision(
            intent=RouterIntent.CLARIFICATION,
            confidence=0.5,
            reason=f"Classified ambiguous dataset question requiring clarification: '{text}'.",
            next_node="explainer",
            metadata={"matched_text": text, "category": "clarification"},
        )

    # 7. Minimum query length check before routing to analytical planner
    if len(text.strip()) <= 2 or all(char in "?!" for char in text):
        return RouterDecision(
            intent=RouterIntent.UNKNOWN,
            confidence=0.0,
            reason=f"Query too short or non-substantive for deterministic routing: '{text}'.",
            next_node="unknown",
            metadata={"text": text},
        )

    # 8. Check NEW_QUERY Intent
    return RouterDecision(
        intent=RouterIntent.NEW_QUERY,
        confidence=0.9 if not has_prior_context else 0.8,
        reason="Classified as standard analytical query for query planner.",
        next_node="planner",
        metadata={"has_prior_context": has_prior_context},
    )


__all__ = [
    "RouterDecision",
    "RouterIntent",
    "router_node",
]
