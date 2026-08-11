"""Suggested Prompt Chips & Contextual Follow-ups Component for Stage 8.11."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st

INITIAL_PROMPT_SUGGESTIONS = [
    ("📊 Compare Categories", "Compare order counts and revenue across product categories."),
    ("📈 Revenue Trend", "Show total revenue trends over time as an interactive chart."),
    ("🏆 Top Products", "What are the top 5 products by revenue?"),
    ("🔍 Detect Anomalies", "Identify any outlier sales or anomalous orders."),
]


def render_initial_suggestions(on_select: Callable[[str], None] | None = None) -> None:
    """Render initial sample prompt chips for landing / empty conversation state."""
    st.markdown(
        """
        <div style="margin-top: 1.5rem; margin-bottom: 0.75rem;">
            <p style="font-family: var(--font-mono); font-size: 0.78rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.5rem;">
                💡 Try asking about your dataset:
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    for idx, (label, prompt_text) in enumerate(INITIAL_PROMPT_SUGGESTIONS):
        with cols[idx % 4]:
            if st.button(label, key=f"btn_init_suggest_{idx}", use_container_width=True):
                if on_select is not None:
                    on_select(prompt_text)
                else:
                    st.session_state["pending_prompt"] = prompt_text
                    st.rerun()


def generate_contextual_followups(
    last_answer_text: str,
    columns: list[str] | None = None,
    active_filters: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Generate dynamic contextual follow-up prompt shortcuts using generic intent rules and conversation state."""
    text_lower = str(last_answer_text).lower()
    followups: list[str] = []

    if any(kw in text_lower for kw in ("grouped by", "category", "categories", "highest", "group")):
        followups.append("Show top 5 items for the highest group")
        followups.append("Compare distribution across groups")
        followups.append("Plot an interactive chart breakdown")
    elif any(kw in text_lower for kw in ("sum", "total", "average", "mean", "revenue", "count")):
        followups.append("Break this down by category")
        followups.append("Calculate correlation with other metrics")
        followups.append("Filter top 10 rows")
    elif any(kw in text_lower for kw in ("filter", "filtered", "where")):
        followups.append("Clear active filters and show overall total")
        followups.append("Show top products under current filter")
        followups.append("Compare current filter with remaining dataset")
    else:
        followups.append("Compare top categories")
        followups.append("Show trend over time")
        followups.append("Identify anomalous values")

    return followups[:3]


def render_contextual_suggestions(
    last_answer_text: str,
    on_select: Callable[[str], None] | None = None,
) -> None:
    """Render dynamic contextual follow-up prompt chips below assistant responses."""
    suggestions = generate_contextual_followups(last_answer_text)

    st.markdown(
        """
        <div style="margin-top: 1rem; margin-bottom: 0.5rem;">
            <span style="font-family: var(--font-mono); font-size: 0.74rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">
                ⚡ Explore further:
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(len(suggestions))
    for idx, prompt_text in enumerate(suggestions):
        with cols[idx]:
            if st.button(
                f"🔍 {prompt_text}",
                key=f"btn_ctx_suggest_{idx}_{hash(prompt_text) % 10000}",
                use_container_width=True,
            ):
                if on_select is not None:
                    on_select(prompt_text)
                else:
                    st.session_state["pending_prompt"] = prompt_text
                    st.rerun()
