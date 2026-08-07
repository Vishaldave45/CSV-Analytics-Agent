"""Page 3: Data Quality Insights & Empirical Evidence."""

from __future__ import annotations

import streamlit as st

from streamlit_app.components.insight_card import render_insight_cards
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.services.session import get_state

st.set_page_config(
    page_title="Data Quality Insights — LOGIC_OS_2.0",
    page_icon="💡",
    layout="wide",
)

render_sidebar()

df = get_state("raw_df")
insights = get_state("insights", [])
dataset_name = get_state("dataset_name", "Dataset")

st.markdown(f"## 💡 Data Quality Insights: `{dataset_name}`")

if df is None:
    st.warning("No dataset loaded yet. Please upload a CSV file on the Upload page.")
    st.stop()

st.markdown("Proactive findings evaluated deterministically by the Stage 3 Evidence Engine.")
st.write("---")

render_insight_cards(insights)
