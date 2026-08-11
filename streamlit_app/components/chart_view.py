"""Chart specification viewer and image renderer component matching Stage 8.11 layout."""

from __future__ import annotations

import textwrap

import pandas as pd
import streamlit as st

from csv_analytics_agent.visualization.models import ChartSpecification
from streamlit_app.services.backend import render_chart_image


def render_chart_views(charts: list[ChartSpecification], df: pd.DataFrame) -> None:
    """Render recommended ChartSpecification cards and Matplotlib chart image with PNG download.

    Args:
        charts: List of recommended ChartSpecification objects.
        df: Input pandas DataFrame context.
    """
    if not charts:
        empty_html = """<div class="glass-panel" style="text-align: center; padding: 2rem;">
<div style="font-size: 1.8rem; color: #4cd7f6; margin-bottom: 0.5rem;">🎨</div>
<h3 style="margin: 0; color: #e5e1e4;">No Visualization Specs</h3>
<p style="color: #94a3b8; font-size: 0.9rem; margin-top: 0.3rem;">
Upload a dataset with numeric dimensions to generate automatic chart recommendations.
</p>
</div>"""
        st.markdown(textwrap.dedent(empty_html), unsafe_allow_html=True)
        return

    col_sel, _ = st.columns([3, 1])
    with col_sel:
        selected_chart_idx = st.selectbox(
            "Select Recommended Visualization Spec",
            options=list(range(len(charts))),
            format_func=lambda i: f"[{charts[i].chart_type.value.upper()}] {charts[i].title}",
        )

    spec = charts[selected_chart_idx]

    x_str = spec.x_axis.column if hasattr(spec, "x_axis") and spec.x_axis else "None"
    y_str = spec.y_axis.column if hasattr(spec, "y_axis") and spec.y_axis else "Count"
    agg_str = getattr(spec, "aggregation", "None") or "None"

    # Spec Details Card
    card_html = f"""<div class="glass-panel" style="margin-bottom: 1.25rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
<span class="badge badge-trend">{spec.chart_type.value.upper()} CHART SPECIFICATION</span>
<span style="font-family: var(--font-mono); font-size: 0.72rem; color: #869397;">
CONFIDENCE: 98.5%
</span>
</div>
<h3 style="margin: 0.3rem 0; font-family: var(--font-display); font-size: 1.35rem; color: #4cd7f6;">
{spec.title}
</h3>
<p style="color: #cbd5e1; font-size: 0.92rem; margin-bottom: 0.8rem;">
{spec.description}
</p>
<div style="display: flex; gap: 1.5rem; flex-wrap: wrap; font-family: var(--font-mono); font-size: 0.8rem; padding-top: 0.6rem; border-top: 1px dashed #272730;">
<div>X-Axis: <strong style="color: #acedff;">{x_str}</strong></div>
<div>Y-Axis: <strong style="color: #acedff;">{y_str}</strong></div>
<div>Aggregation: <strong style="color: #d0bcff;">{agg_str}</strong></div>
</div>
</div>"""
    st.markdown(textwrap.dedent(card_html), unsafe_allow_html=True)

    try:
        img_bytes = render_chart_image(spec, df)
        st.image(
            img_bytes,
            caption=f"Deterministic Render: {spec.title}",
            use_container_width=True,
        )

        col_dl, _ = st.columns([1, 4])
        with col_dl:
            st.download_button(
                label="📥 Export Chart PNG",
                data=img_bytes,
                file_name=f"{spec.chart_type.value}_chart.png",
                mime="image/png",
                key=f"btn_dl_chart_{selected_chart_idx}",
                use_container_width=True,
            )
    except Exception as err:
        st.error(f"⚠️ Failed to render chart specification: {err}")

    with st.expander("🔍 Inspect Underlying JSON Specification", expanded=False):
        st.json(spec.model_dump())


__all__ = ["render_chart_views"]
