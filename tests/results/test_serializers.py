"""Unit tests for AnalysisResult and AnalysisArtifact JSON serializers."""

import json
from typing import Any

import pandas as pd

from csv_analytics_agent.python_engine.models import PythonArtifactType
from csv_analytics_agent.results.models import (
    AnalysisArtifact,
    AnalysisResult,
    AnalysisStatus,
)
from csv_analytics_agent.results.serializers import (
    serialize_analysis_result,
    serialize_artifact,
)


def test_serialize_scalar_artifact() -> None:
    """Verify scalar artifact serialization."""
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.SCALAR,
        name="total_count",
        payload=150,
    )
    ser = serialize_artifact(art)
    assert ser.payload == 150
    assert ser.artifact_type == PythonArtifactType.SCALAR


def test_serialize_dataframe_bounded_preview() -> None:
    """Verify large DataFrame is bounded by max_preview_rows in serialized payload."""
    large_df = pd.DataFrame({"col_a": range(1000), "col_b": range(1000)})
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.DATAFRAME,
        name="large_dataset",
        payload=large_df,
    )

    ser = serialize_artifact(art, max_preview_rows=25, max_preview_columns=10)
    p = ser.payload

    assert p["row_count"] == 1000
    assert p["column_count"] == 2
    assert len(p["preview"]["data"]) == 25  # Bounded preview!
    assert p["truncated"] is True


def test_serialize_series_artifact() -> None:
    """Verify pandas Series serialization."""
    s = pd.Series([10, 20, 30], index=["a", "b", "c"], name="counts")
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.TABLE,
        name="counts_series",
        payload=s,
    )
    ser = serialize_artifact(art)
    p = ser.payload
    assert p["name"] == "counts"
    assert p["row_count"] == 3
    assert p["data"] == [10, 20, 30]


def test_serialize_plotly_figure() -> None:
    """Verify Plotly figure serialization preserves data and layout structure."""

    class MockPlotlyFig:
        def __module__(self) -> str:
            return "plotly.graph_objects"

        def to_dict(self) -> dict[str, Any]:
            return {"data": [{"type": "bar", "x": [1, 2], "y": [3, 4]}], "layout": {"title": "Bar"}}

    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.INTERACTIVE,
        name="plotly_bar",
        payload=MockPlotlyFig(),
    )
    ser = serialize_artifact(art)
    assert ser.payload["data"][0]["type"] == "bar"
    assert ser.payload["layout"]["title"] == "Bar"


def test_serialize_image_bytes() -> None:
    """Verify raw image bytes serialization into base64 data URL."""
    fake_png = b"\x89PNG\r\n\x1a\nfake_image_bytes"
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.IMAGE,
        name="png_chart",
        mime_type="image/png",
        payload=fake_png,
    )
    ser = serialize_artifact(art)
    assert str(ser.payload).startswith("data:image/png;base64,")


def test_serialize_analysis_result_json_compatibility() -> None:
    """Verify complete AnalysisResult serialization produces valid JSON string."""
    df = pd.DataFrame({"sales": [10, 20, 30]})
    art1 = AnalysisArtifact(
        artifact_type=PythonArtifactType.DATAFRAME,
        name="df_art",
        payload=df,
    )
    art2 = AnalysisArtifact(
        artifact_type=PythonArtifactType.SCALAR,
        name="total_sales",
        payload=60,
    )

    res = AnalysisResult(
        status=AnalysisStatus.SUCCESS,
        narrative="Calculated total sales and returned table.",
        artifacts=[art1, art2],
        execution_time_ms=12.5,
        source="python_engine",
        question="Total sales?",
    )

    ser_dict = serialize_analysis_result(res)
    json_str = json.dumps(ser_dict)

    assert json_str != ""
    parsed = json.loads(json_str)
    assert parsed["status"] == "success"
    assert len(parsed["artifacts"]) == 2
    assert parsed["artifacts"][0]["payload"]["row_count"] == 3
    assert parsed["artifacts"][1]["payload"] == 60
