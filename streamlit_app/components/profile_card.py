"""Dataset profile and Bento KPI cards component matching StitchMCP layout."""

from __future__ import annotations

import streamlit as st

from csv_analytics_agent.profiler.models import DatasetProfile


def render_profile_cards(profile: DatasetProfile) -> None:
    """Render KPI Bento summary cards for a DatasetProfile.

    Args:
        profile: Target DatasetProfile instance.
    """
    total_cells = profile.summary.row_count * profile.summary.column_count
    missing_pct = 0.0
    if total_cells > 0:
        missing_pct = (profile.missing.total_missing_values / total_cells) * 100.0

    mem_mb = f"{profile.summary.memory_usage_bytes / (1024 * 1024):.2f} MB"
    duplicates = profile.duplicates.duplicate_rows

    bento_html = f"""
    <div class="bento-grid">
        <!-- Bento Card 1: Total Rows -->
        <div class="bento-card">
            <div class="bento-label">
                <span>TOTAL ROWS</span>
                <span style="color: #4cd7f6;">▦</span>
            </div>
            <div>
                <div class="bento-value">{profile.summary.row_count:,}</div>
                <div style="width: 100%; height: 20px; margin-top: 0.4rem; opacity: 0.7;">
                    <svg viewBox="0 0 100 20" style="width: 100%; height: 100%;" preserveAspectRatio="none">
                        <polyline fill="none" stroke="#4cd7f6" stroke-width="2" points="0,15 20,12 40,16 60,8 80,10 100,4"></polyline>
                    </svg>
                </div>
            </div>
            <div class="bento-subtext">{profile.summary.column_count} columns indexed</div>
        </div>

        <!-- Bento Card 2: Missing Values -->
        <div class="bento-card">
            <div class="bento-label">
                <span>MISSING VALUES</span>
                <span style="color: #d0bcff;">⚠️</span>
            </div>
            <div>
                <div class="bento-value" style="color: {'#fbbf24' if missing_pct > 0 else '#4cd7f6'};">{missing_pct:.1f}%</div>
                <div style="width: 100%; height: 20px; margin-top: 0.4rem; opacity: 0.7;">
                    <svg viewBox="0 0 100 20" style="width: 100%; height: 100%;" preserveAspectRatio="none">
                        <polyline fill="none" stroke="{'#fbbf24' if missing_pct > 0 else '#10b981'}" stroke-width="2" points="0,4 25,6 50,3 75,{'12' if missing_pct > 0 else '4'} 100,{'16' if missing_pct > 0 else '3'}"></polyline>
                    </svg>
                </div>
            </div>
            <div class="bento-subtext">{profile.missing.total_missing_values:,} null cells</div>
        </div>

        <!-- Bento Card 3: Exact Duplicates / Anomalies -->
        <div class="bento-card" style="border-left: 2px solid {'#f43f5e' if duplicates > 0 else '#4cd7f6'};">
            <div class="bento-label">
                <span>EXACT DUPLICATES</span>
                <span style="color: #f43f5e;">⚡</span>
            </div>
            <div>
                <div class="bento-value" style="color: {'#f43f5e' if duplicates > 0 else '#e5e1e4'};">{duplicates:,}</div>
            </div>
            <div class="bento-subtext" style="color: {'#f43f5e' if duplicates > 0 else '#10b981'};">
                {'⚠️ Duplicates found' if duplicates > 0 else '✅ Zero duplicate records'}
            </div>
        </div>

        <!-- Bento Card 4: Memory Size & Engine -->
        <div class="bento-card">
            <div class="bento-label">
                <span>IN-MEMORY PROFILE</span>
                <span style="color: #4cd7f6;">⚡</span>
            </div>
            <div>
                <div class="bento-value">{mem_mb}</div>
            </div>
            <div class="bento-subtext">Deterministic Pandas Core</div>
        </div>
    </div>
    """
    st.markdown(bento_html, unsafe_allow_html=True)


__all__ = ["render_profile_cards"]
