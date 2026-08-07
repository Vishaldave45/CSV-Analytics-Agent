"""Footer component with privacy message and version string."""

from __future__ import annotations

import streamlit as st

from streamlit_app.config import APP_TITLE, APP_VERSION


def render_footer() -> None:
    """Render clean application footer."""
    st.write("---")
    st.markdown(
        f"""
        <div style="text-align: center; color: #64748b; font-size: 0.8rem; padding-bottom: 1rem;">
            🔒 <strong>{APP_TITLE}</strong> {APP_VERSION} — Clean Architecture Presentation Layer.
        </div>
        """,
        unsafe_allow_html=True,
    )


__all__ = ["render_footer"]
