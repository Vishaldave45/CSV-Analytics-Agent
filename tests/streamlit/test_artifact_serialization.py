"""Unit tests for Stage 8.6 serialization to Stage 8.8 rendering pipeline."""

from unittest.mock import MagicMock, patch

import pandas as pd

from csv_analytics_agent.python_engine.models import PythonArtifactType
from csv_analytics_agent.results.models import (
    AnalysisArtifact,
    AnalysisResult,
    AnalysisStatus,
)
from csv_analytics_agent.results.serializers import serialize_analysis_result
from streamlit_app.components.artifact_renderer import render_analysis_result


@patch("streamlit.dataframe")
@patch("streamlit.plotly_chart")
@patch("streamlit.markdown")
def test_serialized_result_rendering_pipeline(
    mock_markdown: MagicMock,
    mock_plotly_chart: MagicMock,
    mock_dataframe: MagicMock,
) -> None:
    """Verify serialized AnalysisResult dictionary can be rendered directly by render_analysis_result."""
    df = pd.DataFrame({"category": ["A", "B"], "sales": [100, 200]})
    art1 = AnalysisArtifact(
        artifact_type=PythonArtifactType.DATAFRAME,
        name="sales_table",
        payload=df,
    )

    art2 = AnalysisArtifact(
        artifact_type=PythonArtifactType.INTERACTIVE,
        name="sales_chart",
        payload={"data": [{"type": "bar", "x": ["A", "B"], "y": [100, 200]}]},
    )

    res = AnalysisResult(
        status=AnalysisStatus.SUCCESS,
        narrative="Category sales overview calculated.",
        artifacts=[art1, art2],
    )

    serialized_dict = serialize_analysis_result(res)

    render_analysis_result(serialized_dict)

    mock_markdown.assert_any_call("Category sales overview calculated.")
    assert mock_dataframe.called
    assert mock_plotly_chart.called
