"""Page 4: Visualization Recommendations & Matplotlib Rendering."""

from __future__ import annotations

import streamlit as st

from streamlit_app.components.chart_view import render_chart_views
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.services.session import get_state

st.set_page_config(
    page_title="Visualizations — LOGIC_OS_2.0",
    page_icon="🎨",
    layout="wide",
)

render_sidebar()

df = get_state("raw_df")
charts = get_state("charts", [])
dataset_name = get_state("dataset_name", "Dataset")

st.markdown(f"## 🎨 Visualization Recommendations: `{dataset_name}`")

if df is None:
    st.warning("No dataset loaded yet. Please upload a CSV file on the Upload page.")
    st.stop()

st.markdown("Renderer-independent chart specifications mapped deterministically by Stage 4 rules.")
st.write("---")

render_chart_views(charts, df)
