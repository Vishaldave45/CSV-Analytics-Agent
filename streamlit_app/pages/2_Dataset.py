"""Page 2: Dataset Overview & Statistical Summary."""

from __future__ import annotations

import streamlit as st

from streamlit_app.components.dataframe_view import render_dataframe_view
from streamlit_app.components.dataset_card import render_dataset_card
from streamlit_app.components.footer import render_footer
from streamlit_app.components.header import render_header
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.config import APP_TITLE
from streamlit_app.services.session import get_state
from streamlit_app.theme import apply_custom_theme

st.set_page_config(
    page_title=f"Dataset Overview — {APP_TITLE}",
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
    st.warning("No dataset loaded yet. Please upload a CSV file on the Upload page.")
    st.stop()

# 1. Render Dataset Overview KPI Card
render_dataset_card(profile, dataset_name=dataset_name)
st.write("---")

# 2. Render Data Preview Table
render_dataframe_view(df, title="Data Preview", max_rows=20)

# 3. Render Column Data Profiles Table
st.write("---")
st.markdown("### 🔍 Column Profiles & Data Types")

col_summary_data = []
for col_prof in profile.columns:
    col_summary_data.append(
        {
            "Column Name": col_prof.name,
            "Data Type": col_prof.dtype,
            "Missing Count": col_prof.missing_count,
            "Missing %": f"{col_prof.missing_percentage:.1f}%",
            "Unique Values": col_prof.unique_count,
        }
    )

st.dataframe(col_summary_data, use_container_width=True)

# 4. Render Numeric Summary Statistics
st.write("---")
st.markdown("### 📈 Numeric Summary Statistics")
st.dataframe(df.describe().T, use_container_width=True)

render_footer()
