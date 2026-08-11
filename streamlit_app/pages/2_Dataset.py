"""Page 2: Dataset Overview & Schema Workspace."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_app.components.dataframe_view import render_dataframe_view
from streamlit_app.components.dataset_card import render_dataset_card
from streamlit_app.components.footer import render_footer
from streamlit_app.components.header import render_header
from streamlit_app.components.profile_card import render_profile_cards
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.config import APP_TITLE
from streamlit_app.services.session import get_state
from streamlit_app.theme import apply_custom_theme

st.set_page_config(
    page_title=f"Dataset — {APP_TITLE}",
    page_icon="📊",
    layout="wide",
)

apply_custom_theme()
render_sidebar()

df = get_state("raw_df")
profile = get_state("profile")
dataset_name = get_state("dataset_name", "Dataset")

render_header("Dataset Overview", icon="📊")

if df is None or profile is None:
    st.warning("⚠️ No dataset loaded yet. Please upload a CSV file on the home page.")
    st.stop()

# Tabbed Dataset Exploration Interface
tab_overview, tab_data, tab_schema, tab_quality = st.tabs(
    ["📊 Overview", "📄 Data Preview", "📋 Schema & Types", "🛡️ Quality Audit"]
)

with tab_overview:
    render_dataset_card(profile, dataset_name=dataset_name)
    render_profile_cards(profile)

    col_stats_num, col_stats_cat = st.columns(2, gap="medium")
    with col_stats_num:
        st.markdown("### Numeric Statistics")
        num_df = df.select_dtypes(include=["number"])
        if not num_df.empty:
            st.dataframe(
                num_df.describe().T[["mean", "std", "min", "50%", "max"]],
                use_container_width=True,
            )
        else:
            st.info("No numeric columns detected.")

    with col_stats_cat:
        st.markdown("### Categorical Summary")
        cat_df = df.select_dtypes(exclude=["number"])
        if not cat_df.empty:
            st.dataframe(cat_df.describe().T, use_container_width=True)
        else:
            st.info("No categorical columns detected.")

with tab_data:
    st.markdown(f"### Raw Data (`{len(df):,}` total rows)")
    render_dataframe_view(df, title="Interactive Data Preview", max_rows=100)

with tab_schema:
    st.markdown("### Column Schema & Data Types")

    schema_records = []
    for col in profile.columns:
        schema_records.append(
            {
                "Column": col.name,
                "Data Type": col.dtype,
                "Unique Values": col.unique_count,
                "Missing Count": col.missing_count,
                "Missing %": f"{col.missing_percentage:.1f}%",
            }
        )
    schema_df = pd.DataFrame(schema_records)
    st.dataframe(schema_df, use_container_width=True, hide_index=True)

with tab_quality:
    st.markdown("### Quality Audit")

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

    c_q1, c_q2, c_q3 = st.columns(3)
    with c_q1:
        st.metric("Health Score", f"{health_score}/100")
    with c_q2:
        st.metric("Duplicate Rows", f"{duplicate_rows:,}")
    with c_q3:
        st.metric("Total Cells Missing", f"{profile.missing.total_missing_values:,}")

    if duplicate_rows > 0:
        st.warning(f"⚠️ Dataset contains **{duplicate_rows:,}** duplicate row entries.")
    else:
        st.success("✅ Zero duplicate rows detected across dataset.")

render_footer()
