"""Uploader component for Quiet Data Studio."""

from __future__ import annotations

import hashlib
import time

import pandas as pd
import streamlit as st

from csv_analytics_agent.exceptions import (
    CSVEncodingError,
    CSVParsingError,
    EmptyCSVError,
)
from csv_analytics_agent.profiler.models import DatasetProfile
from streamlit_app.config import (
    SAMPLE_DATA_DIR,
    SAMPLE_DATASETS,
)
from streamlit_app.services.backend import (
    get_insights,
    get_profile,
    recommend_visualization,
    upload_dataset,
)
from streamlit_app.services.session import set_state


def process_loaded_dataframe(
    df: pd.DataFrame,
    filename: str,
    dataset_hash: str | None = None,
    profile: DatasetProfile | None = None,
) -> None:
    """Process loaded DataFrame through profiling, insights, and chart recommendation pipeline.

    Args:
        df: Loaded pandas DataFrame.
        filename: Name string of loaded dataset.
        dataset_hash: SHA-256 content hash of dataset.
        profile: Optional precomputed/cached DatasetProfile instance.
    """
    if dataset_hash is None:
        raw_bytes = df.to_csv(index=False).encode("utf-8")
        dataset_hash = hashlib.sha256(raw_bytes).hexdigest()

    if profile is None:
        profile = get_profile(df, dataset_name=filename)
    insights = get_insights(profile)
    charts = recommend_visualization(profile, insights=insights)

    set_state("raw_df", df)
    set_state("dataset_name", filename)
    set_state("dataset_hash", dataset_hash)
    set_state("profile", profile)
    set_state("insights", insights)
    set_state("charts", charts)


def render_uploader() -> None:
    """Render quiet CSV uploader and sample dataset loaders."""
    st.markdown(
        """
        <div style="text-align: center; margin-top: 1.5rem; margin-bottom: 2rem;">
            <h1 class="studio-title" style="font-size: 2.8rem;">Data Studio</h1>
            <p style="font-size: 1.05rem; color: #94a3b8; margin-top: 0.4rem;">
                CSV Analytics & Exploration Workspace
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Dropzone Container
    st.markdown(
        """
        <div class="studio-card" style="text-align: center; padding: 2.5rem 1.5rem; margin-bottom: 1.5rem;">
            <div style="font-size: 1.25rem; font-weight: 600; color: #f8fafc;">
                Upload a CSV file to start exploring
            </div>
            <div style="font-size: 0.85rem; color: #64748b; margin-top: 0.3rem;">
                Drag and drop your file below
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload CSV",
        type=["csv"],
        key="csv_file_uploader",
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        content = uploaded_file.getvalue()
        filename = uploaded_file.name
        try:
            with st.status(f"Analyzing '{filename}'...", expanded=True) as status:
                st.write("Reading dataset structure...")
                df, profile, content_hash = upload_dataset(content, filename=filename)

                st.write("Profiling column statistics...")
                time.sleep(0.1)

                st.write("Generating dataset insights...")
                process_loaded_dataframe(
                    df, filename=filename, dataset_hash=content_hash, profile=profile
                )

                st.write("Recommending visualizations...")
                status.update(label=f"'{filename}' ready for analysis", state="complete")

            st.success(f"Loaded **`{filename}`** ({len(df):,} rows × {len(df.columns)} columns)")
            st.rerun()
        except EmptyCSVError:
            st.error(
                f"Empty file: '{filename}' contains no data rows. Please upload a non-empty CSV."
            )
        except CSVEncodingError:
            st.error(
                f"Encoding error: Could not read '{filename}'. Try re-saving the file as UTF-8."
            )
        except CSVParsingError as exc:
            st.error(f"Parse error: '{filename}' could not be parsed as a CSV. {exc}")
        except Exception as exc:
            st.error(f"Unexpected error loading '{filename}': {exc}")

    st.write("")
    st.markdown(
        '<div style="text-align: center; margin-top: 1.5rem; margin-bottom: 0.8rem; '
        'font-size: 0.78rem; color: #64748b; font-weight: 600; letter-spacing: 0.05em;">'
        "OR EXPLORE A SAMPLE DATASET</div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(len(SAMPLE_DATASETS))
    for idx, sample_info in enumerate(SAMPLE_DATASETS):
        with cols[idx]:
            btn_label = f"📄 {sample_info['name']}"
            if st.button(btn_label, key=f"btn_sample_{idx}", use_container_width=True):
                file_path = SAMPLE_DATA_DIR / sample_info["name"]
                if file_path.exists():
                    try:
                        with st.status(
                            f"Loading sample '{sample_info['name']}'...", expanded=True
                        ) as status:
                            st.write("Reading dataset...")
                            raw_bytes = file_path.read_bytes()
                            df, profile, content_hash = upload_dataset(
                                raw_bytes, filename=sample_info["name"]
                            )
                            st.write("Generating profile & insights...")
                            process_loaded_dataframe(
                                df,
                                filename=sample_info["name"],
                                dataset_hash=content_hash,
                                profile=profile,
                            )
                            status.update(label="Sample dataset ready", state="complete")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not load sample dataset: {exc}")
                else:
                    st.warning(f"Sample file not found: {file_path.name}")


__all__ = ["render_uploader"]
