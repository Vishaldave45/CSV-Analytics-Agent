"""Footer component for Quiet Data Studio."""

from __future__ import annotations

import streamlit as st


def render_footer() -> None:
    """Render clean application footer."""
    st.write("---")
    st.markdown(
        """
        <div style="text-align: center; color: #64748b; font-size: 0.78rem; padding-bottom: 1.5rem;">
            Data Studio — Analytical Workspace
        </div>
        """,
        unsafe_allow_html=True,
    )


__all__ = ["render_footer"]
