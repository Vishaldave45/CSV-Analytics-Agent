"""Page 4: Visualizations & Interactive Chart Explorer for Stage 8.11 Workspace."""

from __future__ import annotations

import plotly.express as px
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

render_header("Visualization Explorer Workspace", icon="🎨")

if df is None:
    st.warning("⚠️ No dataset loaded yet. Please upload a CSV file on the home page.")
    st.stop()

tab_auto, tab_explorer = st.tabs(["⚡ Auto Recommended Charts", "🛠️ Custom Chart Explorer"])

with tab_auto:
    st.markdown("### ⚡ Deterministically Recommended Visualizations")
    st.caption(
        "Engineered chart specifications based on column statistical distributions and cardinality."
    )
    render_chart_views(charts, df)

with tab_explorer:
    st.markdown("### 🛠️ Interactive Plotly Chart Explorer")

    c1, c2, c3, c4 = st.columns(4)
    cols_all = list(df.columns)
    num_cols = list(df.select_dtypes(include=["number"]).columns)
    cat_cols = list(df.select_dtypes(exclude=["number"]).columns)

    with c1:
        chart_type = st.selectbox(
            "Chart Type", options=["Bar", "Line", "Scatter", "Histogram", "Box"], index=0
        )
    with c2:
        x_col = st.selectbox("X Axis Dimension", options=cols_all, index=0)
    with c3:
        y_col = st.selectbox(
            "Y Axis Measure", options=[None] + num_cols, index=1 if num_cols else 0
        )
    with c4:
        color_col = st.selectbox("Group By (Color)", options=[None] + cat_cols, index=0)

    try:
        if chart_type == "Bar":
            fig = px.bar(
                df, x=x_col, y=y_col, color=color_col, title=f"{x_col} vs {y_col or 'Count'}"
            )
        elif chart_type == "Line":
            fig = px.line(df, x=x_col, y=y_col, color=color_col, title=f"{x_col} vs {y_col}")
        elif chart_type == "Scatter":
            fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=f"{x_col} vs {y_col}")
        elif chart_type == "Histogram":
            fig = px.histogram(df, x=x_col, color=color_col, title=f"Distribution of {x_col}")
        else:
            fig = px.box(
                df, x=x_col, y=y_col, color=color_col, title=f"Box Plot of {y_col} by {x_col}"
            )

        fig.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as exc:
        st.error(f"Could not render chart with selected dimensions: {exc}")

render_footer()
