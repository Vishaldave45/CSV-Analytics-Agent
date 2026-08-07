"""KPI metrics component for statistical metrics and parameters."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_metric_grid(metrics: dict[str, Any]) -> None:
    """Render a responsive grid of metric KPI cards.

    Args:
        metrics: Dictionary of metric labels and numeric/string values.
    """
    if not metrics:
        return

    cols = st.columns(min(len(metrics), 4))
    keys = list(metrics.keys())

    for idx, key in enumerate(keys):
        val = metrics[key]
        with cols[idx % len(cols)]:
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-value">{val}</div>
                    <div class="metric-label">{key.replace("_", " ").title()}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


__all__ = ["render_metric_grid"]
