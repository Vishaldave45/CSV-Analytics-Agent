"""Page 4: Visualization Recommendations & Matplotlib Rendering."""

from __future__ import annotations

import streamlit as st

from streamlit_app.components.chart_view import render_chart_views
from streamlit_app.components.footer import render_footer
from streamlit_app.components.header import render_header
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.config import APP_TITLE
from streamlit_app.services.session import get_state
from streamlit_app.theme import apply_custom_theme

st.set_page_config(
    page_title=f"Visualizations — {APP_TITLE}",
    page_icon="🎨",
    layout="wide",
)

apply_custom_theme()
render_sidebar()

df = get_state("raw_df")
charts = get_state("charts", [])

render_header("Visualization Recommendations", icon="🎨")

if df is None:
    st.warning("No dataset loaded yet. Please upload a CSV file on the Upload page.")
    st.stop()

st.markdown("Renderer-independent chart specifications recommended deterministically.")
st.write("---")

render_chart_views(charts, df)
render_footer()
