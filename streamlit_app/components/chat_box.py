"""AI Agent Conversational Chat Box & Execution Trace Component."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

SUGGESTED_QUESTIONS = (
    "What is the average revenue?",
    "Show top 5 products by revenue",
    "Filter by region Europe",
    "Show missing values summary",
    "Calculate average satisfaction score",
)


def render_execution_timeline(steps: list[str]) -> None:
    """Render high-tech graph execution step badges.

    Args:
        steps: List of executed step node identifiers.
    """
    html_steps: list[str] = []
    for step in steps:
        html_steps.append(
            f'<span class="timeline-step timeline-step-active">⚡ {step.upper()}</span>'
        )

    st.markdown(
        f"""
        <div style="margin-top: 0.5rem; margin-bottom: 1rem;">
            {"".join(html_steps)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_messages(messages: list[dict[str, Any]], df: pd.DataFrame) -> None:
    """Render conversation message history and Logic Engine output cards.

    Args:
        messages: List of message payload dicts.
        df: Input pandas DataFrame context.
    """
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "user":
            with st.chat_message("user"):
                st.write(content)
        else:
            with st.chat_message("assistant"):
                title_html = (
                    '<div style="font-size: 0.8rem; font-weight: 700; '
                    'color: #00f0ff; letter-spacing: 0.05em; margin-bottom: 0.4rem;">'
                    "🧠 LOGIC ENGINE RESPONSE</div>"
                )
                st.markdown(
                    f"""
                    <div class="logic-card logic-card-glowing">
                        {title_html}
                        <div style="font-size: 1rem; color: #f8fafc; line-height: 1.5;">
                            {content}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Render execution steps if present
                steps = msg.get("execution_steps", ["Router", "Retrieval", "Planner", "Explainer"])
                render_execution_timeline(steps)

                # Render expandable raw source data payload if present
                if "data" in msg and msg["data"]:
                    with st.expander("📄 View source data payload"):
                        st.write(msg["data"])


def render_suggested_followups(on_select: Any) -> None:
    """Render suggested query chip buttons (from image.png mockup).

    Args:
        on_select: Callback function receiving query string.
    """
    label_html = (
        '<div style="font-size: 0.8rem; font-weight: 600; color: #94a3b8; '
        'letter-spacing: 0.05em; margin-top: 1rem; margin-bottom: 0.4rem;">'
        "SUGGESTED QUICK QUESTIONS</div>"
    )
    st.markdown(label_html, unsafe_allow_html=True)

    cols = st.columns(len(SUGGESTED_QUESTIONS))
    for idx, question in enumerate(SUGGESTED_QUESTIONS):
        with cols[idx % len(cols)]:
            if st.button(f"💬 {question}", key=f"btn_sugg_{idx}"):
                on_select(question)


__all__ = [
    "render_chat_messages",
    "render_execution_timeline",
    "render_suggested_followups",
]
