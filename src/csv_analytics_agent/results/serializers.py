"""Explicit JSON-compatible serializers and bounded result transformers."""

from __future__ import annotations

import base64
import io
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from csv_analytics_agent.python_engine.models import PythonArtifactType
from csv_analytics_agent.results.models import AnalysisArtifact, AnalysisResult

MAX_PREVIEW_ROWS: int = 100
MAX_PREVIEW_COLUMNS: int = 50


class SerializedArtifact(BaseModel):
    """JSON-compatible serialized representation of an AnalysisArtifact.

    Attributes:
        artifact_id: Unique artifact identifier string.
        artifact_type: PythonArtifactType classification enum.
        name: Short programmatic name identifier.
        mime_type: Optional MIME type string.
        title: Optional human-readable display title.
        description: Optional description string.
        payload: JSON-serializable payload (primitive, dict, list, string, or None).
        metadata: Metadata dictionary.
        downloadable: Flag indicating downloadability.
    """

    model_config = ConfigDict(frozen=True)

    artifact_id: str = Field(..., description="Artifact UUID identifier.")
    artifact_type: PythonArtifactType = Field(..., description="Artifact type classification.")
    name: str = Field(..., description="Programmatic name key.")
    mime_type: str | None = Field(default=None, description="MIME media type string.")
    title: str | None = Field(default=None, description="Human readable title.")
    description: str | None = Field(default=None, description="Textual description.")
    payload: Any = Field(default=None, description="JSON-compatible payload value.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary.")
    downloadable: bool = Field(default=False, description="Downloadable flag.")


def _clean_json_value(obj: Any) -> Any:
    """Recursively convert object to JSON-safe primitives."""
    if obj is None or isinstance(obj, (int, float, bool, str)):
        return obj
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, dict):
        return {str(k): _clean_json_value(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, pd.Index)):
        return [_clean_json_value(item) for item in obj]
    return str(obj)


def _serialize_dataframe_payload(
    df_val: pd.DataFrame,
    max_preview_rows: int = MAX_PREVIEW_ROWS,
    max_preview_columns: int = MAX_PREVIEW_COLUMNS,
) -> dict[str, Any]:
    """Convert pandas DataFrame to bounded JSON-compatible metadata and preview structure."""
    total_rows = len(df_val)
    total_cols = len(df_val.columns)

    # Bounded preview slice
    preview_df = df_val.iloc[:max_preview_rows, :max_preview_columns]

    preview_dict = {
        "columns": [str(c) for c in preview_df.columns],
        "index": [str(i) for i in preview_df.index],
        "data": _clean_json_value(preview_df.values.tolist()),
    }

    dtypes_dict = {str(col): str(dtype) for col, dtype in df_val.dtypes.items()}

    return {
        "row_count": total_rows,
        "column_count": total_cols,
        "columns": [str(c) for c in df_val.columns],
        "dtypes": dtypes_dict,
        "preview": preview_dict,
        "truncated": total_rows > max_preview_rows or total_cols > max_preview_columns,
    }


def _serialize_series_payload(
    series_val: pd.Series,
    max_preview_rows: int = MAX_PREVIEW_ROWS,
) -> dict[str, Any]:
    """Convert pandas Series to bounded tabular dictionary representation."""
    total_rows = len(series_val)
    preview_series = series_val.iloc[:max_preview_rows]

    return {
        "name": str(series_val.name or "series"),
        "dtype": str(series_val.dtype),
        "row_count": total_rows,
        "index": _clean_json_value(list(preview_series.index)),
        "data": _clean_json_value(list(preview_series.values)),
        "truncated": total_rows > max_preview_rows,
    }


def serialize_artifact(
    artifact: AnalysisArtifact,
    max_preview_rows: int = MAX_PREVIEW_ROWS,
    max_preview_columns: int = MAX_PREVIEW_COLUMNS,
) -> SerializedArtifact:
    """Transform runtime AnalysisArtifact into a JSON-compatible SerializedArtifact.

    Args:
        artifact: Source AnalysisArtifact instance.
        max_preview_rows: Maximum preview row count limit.
        max_preview_columns: Maximum preview column count limit.

    Returns:
        SerializedArtifact model containing JSON-safe payload.
    """
    payload_raw = artifact.payload
    serialized_payload: Any = None
    mime_type = artifact.mime_type

    # 1. Pandas DataFrame / Series
    if isinstance(payload_raw, pd.DataFrame):
        serialized_payload = _serialize_dataframe_payload(
            payload_raw, max_preview_rows, max_preview_columns
        )
        mime_type = mime_type or "application/json"

    elif isinstance(payload_raw, pd.Series):
        serialized_payload = _serialize_series_payload(payload_raw, max_preview_rows)
        mime_type = mime_type or "application/json"

    # 2. Plotly Figure
    elif hasattr(payload_raw, "to_dict") and callable(payload_raw.to_dict):
        try:
            serialized_payload = _clean_json_value(payload_raw.to_dict())
            mime_type = mime_type or "application/json+plotly"
        except Exception:
            serialized_payload = str(payload_raw)

    # 3. Matplotlib Figure
    elif hasattr(payload_raw, "savefig") and callable(payload_raw.savefig):
        try:
            img_buf = io.BytesIO()
            payload_raw.savefig(img_buf, format="png", bbox_inches="tight")
            b64_str = base64.b64encode(img_buf.getvalue()).decode("utf-8")
            serialized_payload = f"data:image/png;base64,{b64_str}"
            mime_type = mime_type or "image/png"
        except Exception:
            serialized_payload = f"[Matplotlib Figure: {artifact.name}]"

    # 4. Binary Image Bytes
    elif isinstance(payload_raw, bytes):
        b64_str = base64.b64encode(payload_raw).decode("utf-8")
        serialized_payload = f"data:{mime_type or 'image/png'};base64,{b64_str}"

    # 5. Primitives & Containers
    else:
        serialized_payload = _clean_json_value(payload_raw)

    return SerializedArtifact(
        artifact_id=artifact.artifact_id,
        artifact_type=artifact.artifact_type,
        name=artifact.name,
        mime_type=mime_type,
        title=artifact.title,
        description=artifact.description,
        payload=serialized_payload,
        metadata=_clean_json_value(artifact.metadata),
        downloadable=artifact.downloadable,
    )


def serialize_analysis_result(
    result: AnalysisResult,
    max_preview_rows: int = MAX_PREVIEW_ROWS,
    max_preview_columns: int = MAX_PREVIEW_COLUMNS,
) -> dict[str, Any]:
    """Serialize complete AnalysisResult into a JSON-compatible dictionary representation.

    Args:
        result: Source AnalysisResult model.
        max_preview_rows: Maximum preview row limit.
        max_preview_columns: Maximum preview column limit.

    Returns:
        JSON-compatible dictionary.
    """
    serialized_artifacts = [
        serialize_artifact(art, max_preview_rows, max_preview_columns).model_dump()
        for art in result.artifacts
    ]

    return {
        "status": result.status.value,
        "narrative": result.narrative,
        "artifacts": serialized_artifacts,
        "execution_time_ms": result.execution_time_ms,
        "source": result.source,
        "question": result.question,
        "dataset_hash": result.dataset_hash,
        "metadata": _clean_json_value(result.metadata),
        "error_type": result.error_type,
        "error_message": result.error_message,
    }


__all__ = [
    "MAX_PREVIEW_COLUMNS",
    "MAX_PREVIEW_ROWS",
    "SerializedArtifact",
    "serialize_analysis_result",
    "serialize_artifact",
]
