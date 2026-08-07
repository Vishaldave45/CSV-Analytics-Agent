"""Header component displaying top bar status and title."""

from __future__ import annotations

import streamlit as st

from streamlit_app.config import APP_SUBTITLE, APP_TITLE
from streamlit_app.services.session import get_state


def render_header(title: str, icon: str = "⚡") -> None:
    """Render top header bar with page title and active dataset badge."""
    dataset_name = get_state("dataset_name", "No dataset active")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"""
            <div style="margin-bottom: 1rem;">
                <h1 style="font-size: 2rem; font-weight: 700; margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                    <span>{icon}</span> <span>{title}</span>
                </h1>
                <p style="color: #94a3b8; font-size: 0.9rem; margin-top: 0.2rem;">
                    {APP_TITLE} • {APP_SUBTITLE}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div style="text-align: right; padding-top: 0.5rem;">
                <span class="badge badge-trend">ACTIVE: {dataset_name}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


__all__ = ["render_header"]
