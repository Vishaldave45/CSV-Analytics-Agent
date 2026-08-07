"""Page 1: CSV Upload & Sample Dataset Selector."""

from __future__ import annotations

import streamlit as st

from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.components.uploader import render_uploader

st.set_page_config(
    page_title="Upload CSV — LOGIC_OS_2.0",
    page_icon="📄",
    layout="wide",
)

render_sidebar()
render_uploader()
