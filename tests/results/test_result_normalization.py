"""Unit tests verifying normalization of runtime execution results into bounded representations."""

import pandas as pd

from csv_analytics_agent.python_engine.models import PythonArtifactType
from csv_analytics_agent.results.models import AnalysisArtifact, AnalysisResult
from csv_analytics_agent.results.serializers import serialize_analysis_result


def test_serialize_analysis_result_bounds_dataframe() -> None:
    """Verify that serializing an AnalysisResult bounds large DataFrames."""
    # Create a 500-row DataFrame
    df = pd.DataFrame({"colA": range(500), "colB": range(500)})

    artifact = AnalysisArtifact(
        artifact_id="art-123",
        artifact_type=PythonArtifactType.DATAFRAME,
        name="large_df",
        payload=df,
    )
    result = AnalysisResult(
        status="success",
        narrative="Here is the data.",
        artifacts=[artifact],
        source="test",
    )

    serialized = serialize_analysis_result(result, max_preview_rows=10, max_preview_columns=5)

    assert serialized["status"] == "success"
    assert serialized["narrative"] == "Here is the data."
    assert len(serialized["artifacts"]) == 1

    art_dict = serialized["artifacts"][0]
    payload = art_dict["payload"]

    assert payload["row_count"] == 500
    assert payload["column_count"] == 2
    assert payload["truncated"] is True
    assert len(payload["preview"]["data"]) == 10  # Bounded to 10 rows


def test_serialize_analysis_result_image() -> None:
    """Verify image bytes are encoded correctly in serialized AnalysisResult."""
    img_bytes = b"fake-image-bytes"

    artifact = AnalysisArtifact(
        artifact_id="art-img",
        artifact_type=PythonArtifactType.IMAGE,
        name="chart",
        mime_type="image/png",
        payload=img_bytes,
    )
    result = AnalysisResult(
        status="success",
        narrative="Chart generated.",
        artifacts=[artifact],
        source="test",
    )

    serialized = serialize_analysis_result(result)
    art_dict = serialized["artifacts"][0]
    payload = art_dict["payload"]

    assert isinstance(payload, str)
    assert payload.startswith("data:image/png;base64,")


def test_serialize_analysis_result_plotly() -> None:
    """Verify Plotly figure-like objects are serialized cleanly."""

    class MockPlotlyFigure:
        def to_dict(self):
            return {"data": [{"x": [1, 2], "y": [3, 4]}], "layout": {}}

    artifact = AnalysisArtifact(
        artifact_id="art-plot",
        artifact_type=PythonArtifactType.INTERACTIVE,
        name="interactive_chart",
        payload=MockPlotlyFigure(),
    )
    result = AnalysisResult(
        status="success",
        narrative="Plot generated.",
        artifacts=[artifact],
        source="test",
    )

    serialized = serialize_analysis_result(result)
    art_dict = serialized["artifacts"][0]
    payload = art_dict["payload"]

    assert isinstance(payload, dict)
    assert "data" in payload
    assert "layout" in payload
