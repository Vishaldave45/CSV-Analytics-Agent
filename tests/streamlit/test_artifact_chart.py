"""Unit tests for Streamlit Plotly chart artifact renderer."""

from unittest.mock import MagicMock, patch

from csv_analytics_agent.python_engine.models import PythonArtifactType
from csv_analytics_agent.results.models import AnalysisArtifact
from streamlit_app.components.artifact_chart import render_interactive


@patch("streamlit.plotly_chart")
def test_render_interactive_plotly_figure_object(mock_plotly_chart: MagicMock) -> None:
    """Verify Plotly figure object is rendered via st.plotly_chart."""

    class DummyPlotlyFig:
        def to_dict(self) -> dict[str, list[str]]:
            return {"data": []}

    fig = DummyPlotlyFig()
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.INTERACTIVE,
        name="plotly_chart",
        payload=fig,
    )
    render_interactive(art)
    mock_plotly_chart.assert_called_once_with(fig, use_container_width=True)


@patch("streamlit.plotly_chart")
def test_render_interactive_plotly_dict(mock_plotly_chart: MagicMock) -> None:
    """Verify Plotly dictionary spec is rendered via st.plotly_chart."""
    plotly_dict = {
        "data": [{"type": "scatter", "x": [1, 2], "y": [3, 4]}],
        "layout": {"title": "Scatter Plot"},
    }
    art = AnalysisArtifact(
        artifact_type=PythonArtifactType.INTERACTIVE,
        name="plotly_dict_chart",
        payload=plotly_dict,
    )
    render_interactive(art)
    mock_plotly_chart.assert_called_once_with(plotly_dict, use_container_width=True)
