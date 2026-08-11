"""Dataset profile KPI summary cards for Quiet Data Studio."""

from __future__ import annotations

import textwrap

import streamlit as st

from csv_analytics_agent.profiler.models import DatasetProfile


def render_profile_cards(profile: DatasetProfile) -> None:
    """Render summary KPI cards for a DatasetProfile.

    Args:
        profile: Target DatasetProfile instance.
    """
    total_cells = profile.summary.row_count * profile.summary.column_count
    missing_pct = 0.0
    if total_cells > 0:
        missing_pct = (profile.missing.total_missing_values / total_cells) * 100.0

    mem_mb = f"{profile.summary.memory_usage_bytes / (1024 * 1024):.2f} MB"
    duplicates = profile.duplicates.duplicate_rows

    bento_html = f"""<div class="bento-grid">
<div class="bento-card">
<div class="bento-label">TOTAL ROWS</div>
<div class="bento-value">{profile.summary.row_count:,}</div>
<div class="bento-subtext">{profile.summary.column_count} columns indexed</div>
</div>

<div class="bento-card">
<div class="bento-label">MISSING VALUES</div>
<div class="bento-value">{missing_pct:.1f}%</div>
<div class="bento-subtext">{profile.missing.total_missing_values:,} missing cells</div>
</div>

<div class="bento-card">
<div class="bento-label">DUPLICATE ROWS</div>
<div class="bento-value">{duplicates:,}</div>
<div class="bento-subtext">{"Duplicate entries" if duplicates > 0 else "Zero duplicate rows"}</div>
</div>

<div class="bento-card">
<div class="bento-label">MEMORY FOOTPRINT</div>
<div class="bento-value">{mem_mb}</div>
<div class="bento-subtext">In-memory size</div>
</div>
</div>"""

    st.markdown(textwrap.dedent(bento_html), unsafe_allow_html=True)


__all__ = ["render_profile_cards"]
