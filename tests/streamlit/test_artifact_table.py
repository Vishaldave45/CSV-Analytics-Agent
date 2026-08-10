"""Unit tests for Streamlit table artifact renderer."""

from unittest.mock import MagicMock, patch

import pandas as pd

from csv_analytics_agent.python_engine.models import PythonArtifactType
from csv_analytics_agent.results.models import AnalysisArtifact
from streamlit_app.components.artifact_table import render_table


@patch("streamlit.download_button")
@patch("streamlit.dataframe")
def test_render_table_dataframe(
    mock_dataframe: MagicMock,
    mock_download: MagicMock,
) -> None:
    """Verify DataFrame rendering with st.dataframe and download button."""
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.DATAFRAME,
        name="test_table",
        payload=df,
    )

    render_table(art)
    assert mock_dataframe.called
    assert mock_download.called
    args, kwargs = mock_download.call_args
    assert kwargs["file_name"] == "test_table.csv"
    assert kwargs["mime"] == "text/csv"


@patch("streamlit.download_button")
@patch("streamlit.dataframe")
def test_render_table_dictionary_preview(
    mock_dataframe: MagicMock,
    mock_download: MagicMock,
) -> None:
    """Verify dict table preview rendering with bounded data payload."""
    dict_payload = {
        "row_count": 100,
        "column_count": 2,
        "preview": {
            "columns": ["x", "y"],
            "index": ["0", "1"],
            "data": [[1, 10], [2, 20]],
        },
    }
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.TABLE,
        name="bounded_table",
        payload=dict_payload,
    )

    render_table(art)
    assert mock_dataframe.called
    assert mock_download.called
