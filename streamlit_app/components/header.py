"""Header component displaying top workspace bar for Quiet Data Studio."""

from __future__ import annotations

import streamlit as st

from streamlit_app.services.session import get_state


def render_header(title: str, icon: str = "📊") -> None:
    """Render workspace header bar with title, active dataset name, and status pill."""
    dataset_name = get_state("dataset_name", "No dataset loaded")
    df = get_state("raw_df")
    is_ready = df is not None

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"""
            <div style="margin-bottom: 1rem;">
                <h1 class="studio-title" style="display: flex; align-items: center; gap: 0.5rem;">
                    <span>{icon}</span> <span>{title}</span>
                </h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        status_html = (
            f"""
            <div style="text-align: right; padding-top: 0.3rem;">
                <span style="font-size: 0.85rem; color: #38bdf8; font-weight: 500;">{dataset_name}</span>
                <span class="studio-badge studio-badge-success" style="margin-left: 0.4rem;">● Active</span>
            </div>
            """
            if is_ready
            else """
            <div style="text-align: right; padding-top: 0.3rem;">
                <span class="studio-badge studio-badge-warning">● No Dataset</span>
            </div>
            """
        )
        st.markdown(status_html, unsafe_allow_html=True)


__all__ = ["render_header"]
