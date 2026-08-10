"""Chat message renderer component with StitchMCP AI-Card layout and execution details."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from streamlit_app.components.execution_trace import render_execution_trace


def render_chat_messages(messages: list[dict[str, Any]], df: pd.DataFrame | None = None) -> None:
    """Render chat conversation history message bubbles matching StitchMCP layout.

    Args:
        messages: List of chat message dictionaries.
        df: Active pandas DataFrame context.
    """
    for idx, msg in enumerate(messages):
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        metadata = msg.get("metadata")
        data_preview = msg.get("data")
        img_bytes = msg.get("image")

        if role == "user":
            with st.chat_message("user"):
                st.markdown(
                    f"""
                    <div style="font-size: 1rem; color: #f8fafc; font-weight: 500;">
                        {content}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            with st.chat_message("assistant"):
                st.markdown(
                    f"""
                    <div class="ai-card" style="margin-bottom: 0.5rem;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span style="color: #d0bcff; font-size: 1.1rem;">🧠</span>
                                <span style="font-family: var(--font-mono); font-size: 0.75rem; color: #869397; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;">
                                    LOGIC_OS DETERMINISTIC ENGINE
                                </span>
                            </div>
                            <span class="badge badge-trend">AI VERIFIED</span>
                        </div>
                        <div style="font-size: 0.96rem; color: #e5e1e4; line-height: 1.6;">
                            {content}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if img_bytes is not None and isinstance(img_bytes, bytes):
                    st.image(img_bytes, use_container_width=True)
                    st.download_button(
                        label="🖼️ Export Chart PNG",
                        data=img_bytes,
                        file_name="chart.png",
                        mime="image/png",
                        key=f"btn_dl_chat_img_{idx}",
                    )

                if (
                    data_preview
                    and data_preview != "None"
                    and not str(data_preview).startswith("b'\\x89PNG")
                ):
                    with st.expander("📄 Expand Source Table Output", expanded=False):
                        st.code(str(data_preview), language="text")

                render_execution_trace(metadata)


__all__ = ["render_chat_messages"]
