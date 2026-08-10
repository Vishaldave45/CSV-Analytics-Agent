"""Dataset Overview card component matching StitchMCP Dataset DNA layout."""

from __future__ import annotations

import streamlit as st

from csv_analytics_agent.profiler.models import DatasetProfile


def render_dataset_card(profile: DatasetProfile, dataset_name: str) -> None:
    """Render summary card of dataset metadata, health score gauge, and bento grid.

    Args:
        profile: DatasetProfile instance.
        dataset_name: Active dataset name string.
    """
    total_cells = profile.summary.row_count * profile.summary.column_count
    missing_pct = (
        (profile.missing.total_missing_values / total_cells) * 100.0 if total_cells > 0 else 0.0
    )
    duplicate_rows = profile.duplicates.duplicate_rows

    # Compute deterministic health score (100 - penalties)
    health_score = 100
    if missing_pct > 0:
        health_score -= min(30, int(missing_pct * 3))
    if duplicate_rows > 0:
        health_score -= min(20, int((duplicate_rows / max(1, profile.summary.row_count)) * 50))
    health_score = max(10, min(100, health_score))

    health_status = "Optimal"
    badge_cls = "badge-optimal"
    gauge_color = "#4cd7f6"
    if health_score < 70:
        health_status = "Warning"
        badge_cls = "badge-anomaly"
        gauge_color = "#fbbf24"
    if health_score < 50:
        health_status = "Critical"
        badge_cls = "badge-critical"
        gauge_color = "#f43f5e"

    # SVG Dash calculation (perimeter ~ 100 for r=15.9155)
    dash_array = f"{health_score}, 100"

    card_html = f"""
    <div class="glass-panel" style="margin-bottom: 1.5rem; position: relative; overflow: hidden;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div>
                <div style="display: flex; align-items: center; gap: 0.5rem; font-family: var(--font-mono); font-size: 0.75rem; color: #869397; margin-bottom: 0.3rem;">
                    <span>DATA_LAKE_ACTIVE</span>
                    <span>›</span>
                    <span style="color: #acedff;">{dataset_name}</span>
                </div>
                <h2 style="margin: 0; font-family: var(--font-display); font-size: 1.8rem; color: #e5e1e4;">
                    {dataset_name}
                </h2>
                <div style="font-family: var(--font-mono); font-size: 0.8rem; color: #94a3b8; margin-top: 0.25rem;">
                    Pre-computed Statistical DNA & Rule Synthesis Profile
                </div>
            </div>
            <!-- Health Score Gauge -->
            <div style="display: flex; align-items: center; gap: 1.25rem; background: rgba(14, 14, 18, 0.8); border: 1px solid #1e293b; border-radius: 12px; padding: 0.75rem 1.25rem;">
                <div style="position: relative; width: 56px; height: 56px; display: flex; align-items: center; justify-content: center;">
                    <svg class="pulse-health" viewBox="0 0 36 36" style="width: 100%; height: 100%; transform: rotate(-90deg);">
                        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#2a2a2c" stroke-width="3.5"></path>
                        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="{gauge_color}" stroke-dasharray="{dash_array}" stroke-linecap="round" stroke-width="3.5"></path>
                    </svg>
                    <div style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-family: var(--font-display); font-weight: 700; font-size: 1.05rem; color: #e5e1e4;">
                        {health_score}
                    </div>
                </div>
                <div>
                    <div style="font-family: var(--font-mono); font-size: 0.7rem; color: #869397; text-transform: uppercase; letter-spacing: 0.05em;">
                        Data Health Score
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.2rem;">
                        <span class="badge {badge_cls}">{health_status}</span>
                        <span style="font-family: var(--font-mono); font-size: 0.75rem; color: #94a3b8;">Deterministic</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


__all__ = ["render_dataset_card"]
