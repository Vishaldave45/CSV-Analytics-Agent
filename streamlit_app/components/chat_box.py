"""Chat message renderer component for Quiet Data Studio."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pandas as pd
import streamlit as st

from streamlit_app.components.artifact_renderer import (
    render_analysis_result,
    render_artifact,
)
from streamlit_app.components.evidence import render_evidence_drawer
from streamlit_app.components.suggested_questions import render_contextual_suggestions


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
    total_messages = len(messages)
    row_count = len(df) if df is not None else None

    for idx, msg in enumerate(messages):
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        metadata = msg.get("metadata")
        data_preview = msg.get("data")
        img_bytes = msg.get("image")
        analysis_result = msg.get("analysis_result")
        artifacts = msg.get("artifacts")

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
                st.markdown(
                    f"""
                    <div style="font-size: 0.95rem; color: #e2e8f0; line-height: 1.6; margin-bottom: 0.75rem;">
                        {content}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Render unified AnalysisResult if attached to message
                if analysis_result is not None:
                    render_analysis_result(analysis_result)

                # Render artifacts list if attached directly
                elif artifacts and isinstance(artifacts, list):
                    for art in artifacts:
                        render_artifact(art)

                else:
                    if img_bytes is not None and isinstance(img_bytes, bytes):
                        st.image(img_bytes, use_container_width=True)
                        st.download_button(
                            label="Export Chart PNG",
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
                        with st.expander("View Data Preview", expanded=False):
                            st.code(str(data_preview), language="text")

                # Render Evidence & Trust Attribution Drawer
                render_evidence_drawer(metadata=metadata, row_count=row_count)

                # Render contextual follow-up prompt chips for the latest assistant message
                if idx == total_messages - 1 and content:
                    render_contextual_suggestions(content, on_select=on_select_followup)


__all__ = ["render_chat_messages"]
