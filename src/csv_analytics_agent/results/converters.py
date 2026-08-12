"""Converters mapping deterministic ExecutionResult and PythonExecutionResult into unified AnalysisResult models."""

from __future__ import annotations

import io
import uuid
from typing import Any

import pandas as pd

from csv_analytics_agent.execution.models import ExecutionResult, ExecutionStatus
from csv_analytics_agent.python_engine.models import (
    PythonArtifact,
    PythonArtifactType,
    PythonExecutionResult,
)
from csv_analytics_agent.results.models import (
    AnalysisArtifact,
    AnalysisResult,
    AnalysisStatus,
)


def python_artifact_to_analysis_artifact(
    art: PythonArtifact,
    title: str | None = None,
    description: str | None = None,
) -> AnalysisArtifact:
    """Convert a PythonArtifact into an application-level AnalysisArtifact.

    Args:
        art: Source PythonArtifact model.
        title: Optional title override.
        description: Optional description override.

    Returns:
        AnalysisArtifact model.
    """
    return AnalysisArtifact(
        artifact_id=str(uuid.uuid4()),
        artifact_type=art.artifact_type,
        name=art.name,
        mime_type=art.mime_type,
        title=title or art.name.replace("_", " ").title(),
        description=description,
        payload=art.data,
        metadata=dict(art.metadata),
        downloadable=art.artifact_type in (PythonArtifactType.DATAFRAME, PythonArtifactType.FILE),
    )


def dataframe_to_analysis_artifact(
    df_val: pd.DataFrame,
    name: str = "dataframe",
    title: str | None = None,
    description: str | None = None,
) -> AnalysisArtifact:
    """Wrap a pandas DataFrame into an AnalysisArtifact instance."""
    return AnalysisArtifact(
        artifact_id=str(uuid.uuid4()),
        artifact_type=PythonArtifactType.DATAFRAME,
        name=name,
        mime_type="application/json",
        title=title or name.replace("_", " ").title(),
        description=description
        or f"DataFrame with {len(df_val)} rows and {len(df_val.columns)} columns.",
        payload=df_val,
        metadata={"row_count": len(df_val), "column_count": len(df_val.columns)},
        downloadable=True,
    )


def plotly_figure_to_analysis_artifact(
    fig: Any,
    name: str = "plotly_chart",
    title: str | None = None,
    description: str | None = None,
) -> AnalysisArtifact:
    """Wrap a Plotly figure object into an AnalysisArtifact instance."""
    return AnalysisArtifact(
        artifact_id=str(uuid.uuid4()),
        artifact_type=PythonArtifactType.INTERACTIVE,
        name=name,
        mime_type="application/json+plotly",
        title=title or "Interactive Plotly Chart",
        description=description or "Interactive Plotly visualization specification.",
        payload=fig,
        metadata={"renderer": "plotly"},
        downloadable=False,
    )


def matplotlib_figure_to_analysis_artifact(
    fig: Any,
    name: str = "matplotlib_chart",
    title: str | None = None,
    description: str | None = None,
) -> AnalysisArtifact:
    """Wrap a Matplotlib figure into an AnalysisArtifact containing rendered image bytes."""
    img_buf = io.BytesIO()
    try:
        fig.savefig(img_buf, format="png", bbox_inches="tight")
        img_bytes = img_buf.getvalue()
    except Exception:
        img_bytes = b""

    return AnalysisArtifact(
        artifact_id=str(uuid.uuid4()),
        artifact_type=PythonArtifactType.IMAGE,
        name=name,
        mime_type="image/png",
        title=title or "Static Matplotlib Chart",
        description=description or "Rendered static PNG image graphic.",
        payload=img_bytes,
        metadata={"size_bytes": len(img_bytes)},
        downloadable=True,
    )


def python_result_to_analysis_result(
    res: PythonExecutionResult,
    question: str | None = None,
    dataset_hash: str | None = None,
) -> AnalysisResult:
    """Convert a PythonExecutionResult into a unified AnalysisResult model.

    Args:
        res: Source PythonExecutionResult model.
        question: Optional natural-language question.
        dataset_hash: Optional SHA-256 dataset hash string.

    Returns:
        Unified AnalysisResult instance.
    """
    artifacts = [python_artifact_to_analysis_artifact(art) for art in res.artifacts]

    if res.success:
        status = AnalysisStatus.SUCCESS
    elif artifacts:
        status = AnalysisStatus.PARTIAL
    else:
        status = AnalysisStatus.FAILED

    narrative = res.stdout.strip()
    if not narrative:
        if status == AnalysisStatus.SUCCESS:
            # Generate a specific narrative from artifacts if available
            descriptions: list[str] = []
            for art in artifacts:
                if (
                    art.artifact_type in (PythonArtifactType.SCALAR, PythonArtifactType.TEXT)
                    and art.payload is not None
                ):
                    descriptions.append(
                        f"The calculated value for **{art.title}** is **{art.payload}**."
                    )
                elif (
                    art.artifact_type in (PythonArtifactType.TABLE, PythonArtifactType.DATAFRAME)
                    and art.payload is not None
                ):
                    row_cnt = (
                        len(art.payload)
                        if isinstance(art.payload, pd.DataFrame)
                        else art.metadata.get("row_count", "")
                    )
                    descriptions.append(
                        f"Generated data table **{art.title}** ({row_cnt} records)."
                    )
                elif art.artifact_type in (
                    PythonArtifactType.IMAGE,
                    PythonArtifactType.INTERACTIVE,
                ):
                    descriptions.append(f"Generated chart visualization **{art.title}**.")

            if descriptions:
                narrative = " ".join(descriptions)
            else:
                narrative = "Analysis executed successfully."
        else:
            narrative = res.error_message or "Python analysis execution failed."

    meta = dict(res.metadata)
    meta["backend"] = meta.get("backend", "python_engine")

    return AnalysisResult(
        status=status,
        narrative=narrative,
        artifacts=artifacts,
        execution_time_ms=res.execution_time_ms,
        source="python_engine",
        question=question,
        dataset_hash=dataset_hash,
        metadata=meta,
        error_type=res.error_type if not res.success else None,
        error_message=res.error_message if not res.success else None,
    )


def deterministic_result_to_analysis_result(
    res: ExecutionResult,
    capability_name: str | None = None,
    question: str | None = None,
    dataset_hash: str | None = None,
) -> AnalysisResult:
    """Convert a Stage 5 deterministic ExecutionResult into a unified AnalysisResult model.

    Args:
        res: Source deterministic ExecutionResult model.
        capability_name: Optional capability name identifier string.
        question: Optional natural-language question.
        dataset_hash: Optional SHA-256 dataset hash string.

    Returns:
        Unified AnalysisResult instance.
    """
    status = (
        AnalysisStatus.SUCCESS if res.status == ExecutionStatus.SUCCESS else AnalysisStatus.FAILED
    )
    artifacts: list[AnalysisArtifact] = []
    name_key = capability_name or "capability_output"

    if res.data is not None:
        if isinstance(res.data, pd.DataFrame):
            artifacts.append(dataframe_to_analysis_artifact(res.data, name=name_key))
        elif isinstance(res.data, pd.Series):
            df_series = res.data.reset_index()
            artifacts.append(dataframe_to_analysis_artifact(df_series, name=name_key))
        elif isinstance(res.data, (int, float, bool)):
            artifacts.append(
                AnalysisArtifact(
                    artifact_id=str(uuid.uuid4()),
                    artifact_type=PythonArtifactType.SCALAR,
                    name=name_key,
                    payload=res.data,
                    title=name_key.replace("_", " ").title(),
                )
            )
        elif isinstance(res.data, str):
            artifacts.append(
                AnalysisArtifact(
                    artifact_id=str(uuid.uuid4()),
                    artifact_type=PythonArtifactType.TEXT,
                    name=name_key,
                    payload=res.data,
                    mime_type="text/plain",
                    title=name_key.replace("_", " ").title(),
                )
            )
        elif isinstance(res.data, bytes):
            artifacts.append(
                AnalysisArtifact(
                    artifact_id=str(uuid.uuid4()),
                    artifact_type=PythonArtifactType.IMAGE,
                    name=name_key,
                    mime_type="image/png",
                    payload=res.data,
                    title=name_key.replace("_", " ").title(),
                    downloadable=True,
                )
            )
        elif isinstance(res.data, dict):
            # Dict payload (e.g. chart specification or structured result dictionary)
            dict_data = res.data
            if "image_bytes" in dict_data and isinstance(dict_data["image_bytes"], bytes):
                artifacts.append(
                    AnalysisArtifact(
                        artifact_id=str(uuid.uuid4()),
                        artifact_type=PythonArtifactType.IMAGE,
                        name=name_key,
                        mime_type="image/png",
                        payload=dict_data["image_bytes"],
                        title=name_key.replace("_", " ").title(),
                        downloadable=True,
                    )
                )
            elif "columns" in dict_data and isinstance(dict_data["columns"], list):
                # Format 'describe' schema profile dict into a clean tabular DataFrame artifact
                cols_list = dict_data["columns"]
                formatted_rows = []
                for col in cols_list:
                    num_stats = col.get("numeric_stats") or {}
                    cat_stats = col.get("categorical_stats") or {}
                    row_item = {
                        "Column": col.get("name"),
                        "Data Type": col.get("dtype"),
                        "Missing (%)": f"{col.get('missing_percentage', 0):.1f}%",
                        "Unique Values": col.get("unique_count"),
                        "Mean / Top": num_stats.get("mean")
                        if num_stats.get("mean") is not None
                        else cat_stats.get("top"),
                        "Min": num_stats.get("min"),
                        "Max": num_stats.get("max"),
                    }
                    formatted_rows.append(row_item)
                desc_df = pd.DataFrame(formatted_rows)
                artifacts.append(
                    dataframe_to_analysis_artifact(
                        desc_df,
                        name="dataset_summary",
                        title="Dataset Column Summary",
                        description="Comprehensive column schema breakdown including datatypes, missingness, and key statistics.",
                    )
                )
            else:
                artifacts.append(
                    AnalysisArtifact(
                        artifact_id=str(uuid.uuid4()),
                        artifact_type=PythonArtifactType.TABLE,
                        name=name_key,
                        mime_type="application/json",
                        payload=res.data,
                        title=name_key.replace("_", " ").title(),
                    )
                )

    narrative = res.message or (
        "Deterministic capability executed successfully."
        if status == AnalysisStatus.SUCCESS
        else "Deterministic capability execution failed."
    )
    if capability_name == "describe" and isinstance(res.data, dict) and "summary" in res.data:
        summ = res.data["summary"]
        r_cnt = summ.get("row_count", 0)
        c_cnt = summ.get("column_count", 0)
        missing_cnt = summ.get("total_missing_values", 0)
        narrative = (
            f"Here is the dataset summary overview. The dataset contains **{r_cnt:,} rows** and **{c_cnt} columns** "
            f"with **{missing_cnt:,} missing values** across all fields.\n\n"
            f"Below is the complete breakdown of column data types, missingness, and summary statistics:"
        )

    return AnalysisResult(
        status=status,
        narrative=narrative,
        artifacts=artifacts,
        execution_time_ms=res.execution_time_ms,
        source="deterministic_engine",
        question=question,
        dataset_hash=dataset_hash,
        metadata={"capability_name": name_key},
        error_type="ExecutionError" if status == AnalysisStatus.FAILED else None,
        error_message=res.message if status == AnalysisStatus.FAILED else None,
    )


__all__ = [
    "dataframe_to_analysis_artifact",
    "deterministic_result_to_analysis_result",
    "matplotlib_figure_to_analysis_artifact",
    "plotly_figure_to_analysis_artifact",
    "python_artifact_to_analysis_artifact",
    "python_result_to_analysis_result",
]
