"""Page 2: Dataset Overview & Statistical Summary."""

from __future__ import annotations

import streamlit as st

from streamlit_app.components.profile_card import render_profile_cards
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.services.session import get_state

st.set_page_config(
    page_title="Dataset Overview — LOGIC_OS_2.0",
    page_icon="📊",
    layout="wide",
)

render_sidebar()

df = get_state("raw_df")
profile = get_state("profile")
dataset_name = get_state("dataset_name", "Dataset")

st.markdown(f"## 📊 Dataset Overview: `{dataset_name}`")

if df is None or profile is None:
    st.warning("No dataset loaded yet. Please upload a CSV file on the Upload page.")
    st.stop()

# 1. Render Summary KPI Cards
render_profile_cards(profile)
st.write("---")

# 2. Render Data Preview Table
st.markdown("### 📄 Data Preview")
st.dataframe(df.head(20), use_container_width=True)

# 3. Render Column Data Profiles
st.write("---")
st.markdown("### 🔍 Column Profiles & Data Types")

col_summary_data = []
for col_prof in profile.column_profiles:
    col_summary_data.append(
        {
            "Column Name": col_prof.column_name,
            "Data Type": col_prof.data_type.value,
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
