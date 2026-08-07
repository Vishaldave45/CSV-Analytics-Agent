"""Theme loader for injecting CSS styles into Streamlit app."""

from __future__ import annotations

import streamlit as st

from streamlit_app.config import STYLES_PATH


def apply_custom_theme() -> None:
    """Inject assets/styles.css into active Streamlit DOM."""
    if STYLES_PATH.exists():
        css_content = STYLES_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


__all__ = ["apply_custom_theme"]
