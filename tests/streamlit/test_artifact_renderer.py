"""Unit tests for central Streamlit artifact renderer dispatcher."""

from unittest.mock import MagicMock, patch

import pandas as pd

from csv_analytics_agent.python_engine.models import PythonArtifactType
from csv_analytics_agent.results.models import (
    AnalysisArtifact,
    AnalysisResult,
    AnalysisStatus,
)
from streamlit_app.components.artifact_renderer import (
    render_analysis_result,
    render_artifact,
)


@patch("streamlit.markdown")
def test_render_text_artifact(mock_markdown: MagicMock) -> None:
    """Verify render_text artifact dispatcher."""
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.TEXT,
        name="notes",
        title="Analysis Notes",
        payload="Summary content",
    )
    render_artifact(art)
    assert mock_markdown.called


@patch("streamlit.metric")
def test_render_scalar_artifact(mock_metric: MagicMock) -> None:
    """Verify render_scalar artifact dispatcher."""
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.SCALAR,
        name="avg_sales",
        title="Average Sales",
        payload=1234.56,
    )
    render_artifact(art)
    mock_metric.assert_called_once_with(label="Average Sales", value="1,234.56")


@patch("streamlit_app.components.artifact_renderer.render_table")
def test_render_dataframe_artifact(mock_render_table: MagicMock) -> None:
    """Verify render_artifact dispatches DATAFRAME to render_table."""
    df = pd.DataFrame({"a": [1, 2]})
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.DATAFRAME,
        name="sales_df",
        payload=df,
    )
    render_artifact(art)
    mock_render_table.assert_called_once_with(art)


@patch("streamlit_app.components.artifact_renderer.render_interactive")
def test_render_interactive_artifact(mock_render_chart: MagicMock) -> None:
    """Verify render_artifact dispatches INTERACTIVE to render_interactive."""
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.INTERACTIVE,
        name="chart",
        payload={"data": []},
    )
    render_artifact(art)
    mock_render_chart.assert_called_once_with(art)


@patch("streamlit_app.components.artifact_renderer.render_image")
def test_render_image_artifact(mock_render_image: MagicMock) -> None:
    """Verify render_artifact dispatches IMAGE to render_image."""
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.IMAGE,
        name="plot",
        payload=b"fake_png",
    )
    render_artifact(art)
    mock_render_image.assert_called_once_with(art)


@patch("streamlit_app.components.artifact_renderer.render_file")
def test_render_file_artifact(mock_render_file: MagicMock) -> None:
    """Verify render_artifact dispatches FILE to render_file."""
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.FILE,
        name="report.pdf",
        payload=b"pdf_content",
    )
    render_artifact(art)
    mock_render_file.assert_called_once_with(art)


@patch("streamlit_app.components.artifact_renderer.render_diagram")
def test_render_diagram_artifact(mock_render_diagram: MagicMock) -> None:
    """Verify render_artifact dispatches DIAGRAM to render_diagram."""
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.DIAGRAM,
        name="flowchart",
        payload="graph TD; A-->B;",
    )
    render_artifact(art)
    mock_render_diagram.assert_called_once_with(art)


@patch("streamlit.markdown")
@patch("streamlit_app.components.artifact_renderer.render_artifact")
def test_render_analysis_result_flow(
    mock_render_art: MagicMock,
    mock_markdown: MagicMock,
) -> None:
    """Verify render_analysis_result renders narrative and iterates through artifacts in order."""
    art1 = AnalysisArtifact(
        artifact_type=PythonArtifactType.SCALAR,
        name="s1",
        payload=10,
    )
    art2 = AnalysisArtifact(
        artifact_type=PythonArtifactType.TEXT,
        name="t1",
        payload="Hello",
    )
    res = AnalysisResult(
        status=AnalysisStatus.SUCCESS,
        narrative="Completed analysis.",
        artifacts=[art1, art2],
    )

    render_analysis_result(res)
    mock_markdown.assert_called_with("Completed analysis.")
    assert mock_render_art.call_count == 2


@patch("streamlit.error")
@patch("streamlit.expander")
def test_render_analysis_result_failure(
    mock_expander: MagicMock,
    mock_error: MagicMock,
) -> None:
    """Verify FAILED AnalysisResult displays user friendly error message."""
    res = AnalysisResult.failure(
        error_type="ZeroDivisionError",
        error_message="division by zero",
    )
    render_analysis_result(res)
    mock_error.assert_called_once_with("I couldn't complete that analysis.")
