"""Header component displaying top bar status, active dataset, and title for Stage 8.11."""

from __future__ import annotations

import streamlit as st

from streamlit_app.services.session import get_state


def render_header(title: str, icon: str = "⚡") -> None:
    """Render workspace header bar with title, active dataset name, and status pill."""
    dataset_name = get_state("dataset_name", "No dataset loaded")
    df = get_state("raw_df")
    is_ready = df is not None

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"""
            <div style="margin-bottom: 1rem;">
                <h1 style="font-family: var(--font-display); font-size: 1.85rem; font-weight: 700; margin: 0; display: flex; align-items: center; gap: 0.5rem; color: #e5e1e4;">
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
                <span style="font-family: var(--font-mono); font-size: 0.8rem; color: #4cd7f6; font-weight: 600;">{dataset_name}</span>
                <span class="badge badge-optimal" style="margin-left: 0.4rem;">● Ready</span>
            </div>
            """
            if is_ready
            else """
            <div style="text-align: right; padding-top: 0.3rem;">
                <span class="badge badge-anomaly">● No Dataset</span>
            </div>
            """
        )
        st.markdown(status_html, unsafe_allow_html=True)


__all__ = ["render_header"]
