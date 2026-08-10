"""Uploader component matching StitchMCP Onboarding & Ingestion layout."""

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
    APP_SUBTITLE,
    APP_TITLE,
    EXAMPLE_QUESTIONS,
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
    """Render hero CSV dropzone, sample dataset quick loaders, and example question chips."""
    st.markdown(
        f"""
        <div style="text-align: center; margin-top: 1.5rem; margin-bottom: 2rem;">
            <h1 class="brand-title" style="font-size: 3.4rem; letter-spacing: -0.04em;">{APP_TITLE}</h1>
            <p style="font-size: 1.15rem; color: #94a3b8; margin-top: 0.4rem; font-family: var(--font-sans);">
                {APP_SUBTITLE} • Ask your data anything with mathematical precision.
            </p>
            <div style="margin-top: 0.8rem;">
                <span class="brand-status-badge">
                    <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #4cd7f6;"></span>
                    CORE_V2 OPERATIONAL
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Dropzone Container
    st.markdown(
        """
        <div class="dropzone-container" style="margin-bottom: 1.5rem;">
            <div style="font-size: 2.2rem; color: #4cd7f6; margin-bottom: 0.5rem;">☁️</div>
            <div style="font-family: var(--font-display); font-size: 1.4rem; font-weight: 600; color: #e5e1e4;">
                Drop your CSV file here
            </div>
            <div style="font-family: var(--font-mono); font-size: 0.85rem; color: #869397; margin-top: 0.3rem;">
                or click below to browse — up to 500MB
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
            with st.status(f"⚡ Ingesting '{filename}' into LOGIC_OS...", expanded=True) as status:
                st.write("🔍 Parsing bytes and inspecting CSV encoding...")
                df, profile, content_hash = upload_dataset(content, filename=filename)

                st.write("📊 Computing column statistical DNA & data distributions...")
                time.sleep(0.1)

                st.write("💡 Synthesizing proactive empirical data insights...")
                process_loaded_dataframe(
                    df, filename=filename, dataset_hash=content_hash, profile=profile
                )

                st.write("🎨 Recommending deterministic visualization specifications...")
                status.update(label=f"✅ '{filename}' successfully analyzed!", state="complete")

            st.success(
                f"🚀 Loaded **`{filename}`** ({len(df):,} rows × {len(df.columns)} columns)!"
            )
            st.rerun()
        except EmptyCSVError:
            st.error(
                f"⚠️ **Empty file**: '{filename}' contains no data rows. "
                "Please upload a non-empty CSV."
            )
        except CSVEncodingError:
            st.error(
                f"⚠️ **Encoding error**: Could not read '{filename}'. "
                "Try re-saving the file as UTF-8 (e.g. in Excel: Save As → CSV UTF-8)."
            )
        except CSVParsingError as exc:
            st.error(f"⚠️ **Parse error**: '{filename}' could not be parsed as a CSV. {exc}")
        except Exception as exc:
            st.error(f"⚠️ **Unexpected error** loading '{filename}': {exc}")

    st.write("")
    sample_hdr_html = (
        '<div style="text-align: center; margin-top: 1.8rem; margin-bottom: 0.9rem; '
        'font-family: var(--font-mono); font-size: 0.8rem; color: #869397; font-weight: 600; letter-spacing: 0.08em;">'
        "OR EXPLORE A PRE-INDEXED SAMPLE DATASET</div>"
    )
    st.markdown(sample_hdr_html, unsafe_allow_html=True)

    cols = st.columns(len(SAMPLE_DATASETS))
    for idx, sample_info in enumerate(SAMPLE_DATASETS):
        with cols[idx]:
            btn_label = f"{sample_info['icon']} {sample_info['name']}"
            if st.button(btn_label, key=f"btn_sample_{idx}", use_container_width=True):
                file_path = SAMPLE_DATA_DIR / sample_info["name"]
                if file_path.exists():
                    try:
                        with st.status(
                            f"⚡ Loading sample '{sample_info['name']}'...", expanded=True
                        ) as status:
                            st.write("Reading pre-indexed dataset bytes...")
                            raw_bytes = file_path.read_bytes()
                            df, profile, content_hash = upload_dataset(
                                raw_bytes, filename=sample_info["name"]
                            )
                            st.write("Evaluating column profiles & generating insights...")
                            process_loaded_dataframe(
                                df,
                                filename=sample_info["name"],
                                dataset_hash=content_hash,
                                profile=profile,
                            )
                            status.update(label="✅ Sample dataset ready!", state="complete")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"⚠️ Could not load sample dataset: {exc}")
                else:
                    st.warning(f"Sample file not found: {file_path.name}")

    st.write("")
    st.markdown(
        '<div style="text-align: center; margin-top: 2rem; margin-bottom: 0.9rem; '
        'font-family: var(--font-mono); font-size: 0.8rem; color: #869397; font-weight: 600; letter-spacing: 0.08em;">'
        "EXAMPLE QUESTIONS YOU CAN ASK</div>",
        unsafe_allow_html=True,
    )

    ex_cols = st.columns(len(EXAMPLE_QUESTIONS))
    for idx, q_text in enumerate(EXAMPLE_QUESTIONS):
        with ex_cols[idx]:
            if st.button(f"💡 {q_text}", key=f"btn_ex_home_{idx}", use_container_width=True):
                set_state("pending_prompt", q_text)
                st.switch_page("pages/5_AI_Chat.py")

    st.markdown(
        """
        <div style="text-align: center; margin-top: 3rem; color: #869397; font-family: var(--font-mono); font-size: 0.78rem;">
            🔒 <strong>100% Deterministic & Local</strong> — Data never leaves your machine. Only schema definitions are sent to LLM planners.
        </div>
        """,
        unsafe_allow_html=True,
    )


__all__ = ["render_uploader"]
