"""Suggested Prompt Chips & Contextual Follow-ups Component for Stage 8.11."""

from __future__ import annotations

from collections.abc import Callable

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


def generate_contextual_followups(last_answer_text: str) -> list[str]:
    """Generate dynamic contextual follow-up prompt shortcuts based on assistant response."""
    text_lower = str(last_answer_text).lower()

    if "electronics" in text_lower or "furniture" in text_lower or "category" in text_lower:
        return [
            "Why is Electronics the highest category?",
            "Show top products inside Electronics",
            "Plot monthly trend by category",
        ]
    elif "revenue" in text_lower or "units_sold" in text_lower:
        return [
            "Show distribution of Units Sold",
            "Calculate Pearson correlation between Units Sold and Revenue",
            "Filter sales in Europe",
        ]
    elif "europe" in text_lower or "region" in text_lower:
        return [
            "Compare North America vs Europe",
            "Which category is highest in Europe?",
            "Show top 5 products by region",
        ]
    else:
        return [
            "Show revenue by category",
            "Plot interactive sales trend",
            "Identify outlier orders",
        ]


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
