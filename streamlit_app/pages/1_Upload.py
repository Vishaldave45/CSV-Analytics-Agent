"""Page 1: CSV Upload & Sample Dataset Selector (Landing Page)."""

from __future__ import annotations

import streamlit as st

from streamlit_app.components.footer import render_footer
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.components.uploader import render_uploader
from streamlit_app.config import APP_ICON, APP_TITLE
from streamlit_app.theme import apply_custom_theme

st.set_page_config(
    page_title=f"Upload CSV — {APP_TITLE}",
    page_icon=APP_ICON,
    layout="wide",
)

apply_custom_theme()
render_sidebar()
render_uploader()
render_footer()
