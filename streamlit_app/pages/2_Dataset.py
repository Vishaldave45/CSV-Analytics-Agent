"""Page 2: Dataset DNA & Statistical Summary matching StitchMCP layout."""

from __future__ import annotations

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
    page_title=f"Dataset DNA — {APP_TITLE}",
    page_icon="🧬",
    layout="wide",
)

apply_custom_theme()
render_sidebar()

df = get_state("raw_df")
profile = get_state("profile")
dataset_name = get_state("dataset_name", "Dataset")

render_header("Dataset DNA & Statistical Profile", icon="🧬")

if df is None or profile is None:
    st.warning("⚠️ No dataset loaded yet. Please upload a CSV file on the Upload page.")
    st.stop()

# 1. Render Dataset Health Score Header Card
render_dataset_card(profile, dataset_name=dataset_name)

# 2. Render 4-Card Bento Grid
render_profile_cards(profile)

# 3. Two-Column Bento Layout: Column DNA (Left) & Statistical Profile (Right)
col_dna, col_stats = st.columns([3, 2], gap="medium")

with col_dna:
    st.markdown("### 🧬 Column DNA & Semantic Types")
    st.caption("Inspected column data types, completeness, and inferred semantic roles")

    for col in profile.columns:
        # Determine badge type and color
        dtype_str = col.dtype.upper()
        if "INT" in dtype_str or "FLOAT" in dtype_str:
            type_badge = "badge-trend"
        elif "DATE" in dtype_str or "TIME" in dtype_str:
            type_badge = "badge-quality"
        elif col.unique_count == profile.summary.row_count:
            type_badge = "badge-optimal"
            dtype_str = "IDENTIFIER"
        else:
            type_badge = "badge-trend"

        missing_text = f"{col.missing_percentage:.1f}% Missing" if col.missing_percentage > 0 else "0% Null"
        missing_color = "#fbbf24" if col.missing_percentage > 0 else "#10b981"

        card_html = f"""
        <div class="dna-card">
            <div class="dna-header">
                <div style="display: flex; align-items: center; gap: 0.6rem;">
                    <span style="color: #4cd7f6; font-size: 1rem;">◈</span>
                    <span class="dna-col-name">{col.name}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span class="badge {type_badge}">{dtype_str}</span>
                    <span style="font-family: var(--font-mono); font-size: 0.75rem; color: {missing_color};">
                        {missing_text}
                    </span>
                </div>
            </div>
            <div class="dna-stats-row">
                <div>Distinct: <strong style="color: #e5e1e4;">{col.unique_count:,}</strong></div>
                <div>Nulls: <strong style="color: #e5e1e4;">{col.missing_count:,}</strong></div>
                <div>Semantic: <strong style="color: #d0bcff;">{col.dtype}</strong></div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

with col_stats:
    st.markdown("### 📈 Numeric Distribution & Summary")
    st.caption("Descriptive statistics computed deterministically across numeric dimensions")
    
    numeric_df = df.select_dtypes(include=["number"])
    if not numeric_df.empty:
        st.dataframe(
            numeric_df.describe().T[["mean", "std", "min", "50%", "max"]],
            use_container_width=True,
        )
    else:
        st.info("No continuous numeric dimensions detected in active dataset.")

    # Categorical summary
    cat_df = df.select_dtypes(exclude=["number"])
    if not cat_df.empty:
        st.markdown("### 🏷️ Categorical Summary")
        st.dataframe(cat_df.describe().T, use_container_width=True)

st.write("---")

# 4. Render Interactive Data Preview Table
render_dataframe_view(df, title="Raw Data Explorer", max_rows=50)

render_footer()
