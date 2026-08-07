"""Chart recommendation visualizer component."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from csv_analytics_agent.visualization.models import ChartSpecification
from streamlit_app.services.backend import render_chart_image


def render_chart_views(charts: list[ChartSpecification], df: pd.DataFrame) -> None:
    """Render recommended ChartSpecification cards and Matplotlib chart images.

    Args:
        charts: List of recommended ChartSpecification objects.
        df: Input pandas DataFrame context.
    """
    if not charts:
        st.info("No visualization recommendations available for dataset.")
        return

    selected_chart_idx = st.selectbox(
        "Select Recommended Visualization Spec",
        options=list(range(len(charts))),
        format_func=lambda i: f"[{charts[i].chart_type.value.upper()}] {charts[i].title}",
    )

    spec = charts[selected_chart_idx]

    st.markdown(
        f"""
        <div class="logic-card logic-card-glowing">
            <span class="badge badge-trend">{spec.chart_type.value} CHART — AUTO-RECOMMENDED</span>
            <h3 style="margin-top: 0.4rem; color: #00f0ff;">{spec.title}</h3>
            <p style="color: #94a3b8; font-size: 0.9rem;">{spec.description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        img_bytes = render_chart_image(spec, df)
        st.image(img_bytes, caption=spec.title, use_container_width=True)
    except Exception as err:
        st.error(f"Failed to render chart specification: {err}")

    with st.expander("Chart Specification Specs"):
        st.json(spec.model_dump())


__all__ = ["render_chart_views"]
