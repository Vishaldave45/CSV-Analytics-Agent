"""Page 4: Visualizations & Interactive Chart Explorer."""

from __future__ import annotations

import streamlit as st

from streamlit_app.components.chart_view import render_chart_views
from streamlit_app.components.footer import render_footer
from streamlit_app.components.header import render_header
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.config import APP_TITLE
from streamlit_app.services.session import get_state
from streamlit_app.theme import apply_custom_theme

try:
    import plotly.express as px

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

st.set_page_config(
    page_title=f"Visualizations — {APP_TITLE}",
    page_icon="🎨",
    layout="wide",
)

apply_custom_theme()
render_sidebar()

df = get_state("raw_df")
charts = get_state("charts", [])

render_header("Visualizations", icon="🎨")

if df is None:
    st.warning("⚠️ No dataset loaded yet. Please upload a CSV file on the home page.")
    st.stop()

tab_auto, tab_explorer = st.tabs(["📊 Recommended Charts", "🛠️ Custom Explorer"])

with tab_auto:
    st.markdown("### Recommended Visualizations")
    st.caption("Automatically selected based on column data types and distribution patterns.")
    render_chart_views(charts, df)

with tab_explorer:
    st.markdown("### Interactive Chart Builder")

    c1, c2, c3 = st.columns(3)
    cols_all = list(df.columns)
    num_cols = list(df.select_dtypes(include=["number"]).columns)
    cat_cols = list(df.select_dtypes(exclude=["number"]).columns)

    with c1:
        chart_type = st.selectbox("Chart Type", options=["Bar", "Line", "Scatter"], index=0)
    with c2:
        x_col = st.selectbox("X Axis Dimension", options=cols_all, index=0)
    with c3:
        y_col = st.selectbox("Y Axis Measure", options=num_cols if num_cols else cols_all, index=0)

    if HAS_PLOTLY:
        try:
            color_col = st.selectbox("Group By (Color)", options=[None] + cat_cols, index=0)
            if chart_type == "Bar":
                fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=f"{x_col} vs {y_col}")
            elif chart_type == "Line":
                fig = px.line(df, x=x_col, y=y_col, color=color_col, title=f"{x_col} vs {y_col}")
            else:
                fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=f"{x_col} vs {y_col}")

            fig.update_layout(template="plotly_dark", height=500)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as exc:
            st.error(f"Could not render Plotly chart: {exc}")
    else:
        try:
            chart_df = df[[x_col, y_col]].dropna().set_index(x_col)
            if chart_type == "Bar":
                st.bar_chart(chart_df)
            elif chart_type == "Line":
                st.line_chart(chart_df)
            else:
                st.scatter_chart(chart_df)
        except Exception as exc:
            st.error(f"Could not render chart: {exc}")

render_footer()
