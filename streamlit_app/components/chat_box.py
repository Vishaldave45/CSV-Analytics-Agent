"""Chat message renderer component with execution details and CSV export."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from streamlit_app.components.execution_trace import render_execution_trace


def render_chat_messages(messages: list[dict[str, Any]], df: pd.DataFrame | None = None) -> None:
    """Render chat conversation history message bubbles.

    Args:
        messages: List of chat message dictionaries.
        df: Active pandas DataFrame context.
    """
    for msg in messages:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        metadata = msg.get("metadata")
        data_preview = msg.get("data")

        with st.chat_message(role):
            st.markdown(content)

            if data_preview and data_preview != "None":
                with st.expander("Expand Source Table Data", expanded=False):
                    st.code(str(data_preview))

            if role == "assistant":
                render_execution_trace(metadata)


__all__ = ["render_chat_messages"]
