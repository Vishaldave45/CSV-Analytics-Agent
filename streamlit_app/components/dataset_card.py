"""Dataset Overview card component for Quiet Data Studio."""

from __future__ import annotations

import textwrap

import streamlit as st

from csv_analytics_agent.profiler.models import DatasetProfile


def render_dataset_card(profile: DatasetProfile, dataset_name: str) -> None:
    """Render summary card of dataset metadata and health score.

    Args:
        profile: DatasetProfile instance.
        dataset_name: Active dataset name string.
    """
    total_cells = profile.summary.row_count * profile.summary.column_count
    missing_pct = (
        (profile.missing.total_missing_values / total_cells) * 100.0 if total_cells > 0 else 0.0
    )
    duplicate_rows = profile.duplicates.duplicate_rows

    health_score = 100
    if missing_pct > 0:
        health_score -= min(30, int(missing_pct * 3))
    if duplicate_rows > 0:
        health_score -= min(20, int((duplicate_rows / max(1, profile.summary.row_count)) * 50))
    health_score = max(10, min(100, health_score))

    badge_cls = "studio-badge-success"
    if health_score < 70:
        badge_cls = "studio-badge-warning"

    card_html = f"""<div class="studio-card" style="margin-bottom: 1.25rem;">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
<div>
<h2 class="studio-title" style="font-size: 1.6rem; color: #f8fafc;">
{dataset_name}
</h2>
<div style="font-size: 0.88rem; color: #94a3b8; margin-top: 0.25rem;">
{profile.summary.row_count:,} rows × {profile.summary.column_count} columns
</div>
</div>
<div style="display: flex; align-items: center; gap: 0.85rem; background: #162032; border: 1px solid #334155; border-radius: 8px; padding: 0.65rem 1rem;">
<div style="font-size: 1.3rem; font-weight: 700; color: #38bdf8;">
{health_score}/100
</div>
<div>
<div style="font-size: 0.74rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
Data Health
</div>
<div style="margin-top: 0.15rem;">
<span class="studio-badge {badge_cls}">Deterministic</span>
</div>
</div>
</div>
</div>
</div>"""

    st.markdown(textwrap.dedent(card_html), unsafe_allow_html=True)


__all__ = ["render_dataset_card"]
