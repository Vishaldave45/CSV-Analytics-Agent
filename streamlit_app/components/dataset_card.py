"""Dataset Overview card component."""

from __future__ import annotations

import streamlit as st

from csv_analytics_agent.profiler.models import DatasetProfile


def render_dataset_card(profile: DatasetProfile, dataset_name: str) -> None:
    """Render summary card of dataset metadata."""
    total_cells = profile.summary.row_count * profile.summary.column_count
    missing_pct = (
        (profile.missing.total_missing_values / total_cells) * 100.0 if total_cells > 0 else 0.0
    )
    mem_mb = profile.summary.memory_usage_bytes / (1024 * 1024)

    card_html = f"""
    <div class="logic-card logic-card-glowing">
        <span class="badge badge-trend">DATASET LOADED</span>
        <h3 style="margin-top: 0.4rem; color: #f8fafc; font-size: 1.4rem;">`{dataset_name}`</h3>
        <div style="display: flex; gap: 1.5rem; margin-top: 0.8rem; font-family: var(--font-mono); font-size: 0.9rem;">
            <div><span style="color: #94a3b8;">Rows:</span> <strong style="color: #00f0ff;">{profile.summary.row_count:,}</strong></div>
            <div><span style="color: #94a3b8;">Columns:</span> <strong style="color: #00f0ff;">{profile.summary.column_count}</strong></div>
            <div><span style="color: #94a3b8;">Missing:</span> <strong style="color: #a855f7;">{missing_pct:.1f}%</strong></div>
            <div><span style="color: #94a3b8;">Memory:</span> <strong style="color: #f8fafc;">{mem_mb:.2f} MB</strong></div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


__all__ = ["render_dataset_card"]
