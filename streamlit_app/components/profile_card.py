"""Dataset profile and KPI cards component."""

from __future__ import annotations

import streamlit as st

from csv_analytics_agent.profiler.models import DatasetProfile


def render_profile_cards(profile: DatasetProfile) -> None:
    """Render KPI metric summary cards for a DatasetProfile.

    Args:
        profile: Target DatasetProfile instance.
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-value">{profile.summary.row_count:,}</div>
                <div class="metric-label">Total Rows</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-value">{profile.summary.column_count}</div>
                <div class="metric-label">Columns</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        total_cells = profile.summary.row_count * profile.summary.column_count
        missing_pct = 0.0
        if total_cells > 0:
            missing_pct = (profile.missing.total_missing_values / total_cells) * 100.0

        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-value">{missing_pct:.1f}%</div>
                <div class="metric-label">Missing Data</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        mem_mb = f"{profile.summary.memory_usage_bytes / (1024 * 1024):.2f} MB"
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-value">{mem_mb}</div>
                <div class="metric-label">Memory Size</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


__all__ = ["render_profile_cards"]
