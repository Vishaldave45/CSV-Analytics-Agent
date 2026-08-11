"""Chat message renderer component for Quiet Data Studio."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pandas as pd
import streamlit as st


def render_chat_messages(
    messages: list[dict[str, Any]],
    df: pd.DataFrame | None = None,
    on_select_followup: Callable[[str], None] | None = None,
) -> None:
    """Render chat conversation history for Quiet Data Studio.

    Args:
        messages: List of chat message dictionaries.
        df: Active pandas DataFrame context.
        on_select_followup: Optional callback for clicking contextual follow-up prompt chips.
    """
    row_count = len(df) if df is not None else None
    total_messages = len(messages)

    for msg_index, msg in enumerate(messages):
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        is_last = msg_index == total_messages - 1

        if role == "user":
            with st.chat_message("user"):
                st.markdown(
                    f"""
                    <div style="font-size: 0.95rem; color: #f8fafc; font-weight: 500;">
                        {content}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            with st.chat_message("assistant"):
                agent_resp = msg.get("agent_response")
                if agent_resp:
                    from streamlit_app.components.agent_response import render_agent_response

                    render_agent_response(
                        agent_resp,
                        row_count=row_count,
                        on_select_followup=on_select_followup,
                        msg_index=msg_index,
                        is_last=is_last,
                    )
                else:
                    # Fallback for old unnormalized state payloads if any
                    if content:
                        st.markdown(content)


__all__ = ["render_chat_messages"]
