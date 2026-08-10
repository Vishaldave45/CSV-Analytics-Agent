"""Unified AnalysisResult and AnalysisArtifact protocol package."""

from csv_analytics_agent.results.converters import (
    dataframe_to_analysis_artifact,
    deterministic_result_to_analysis_result,
    matplotlib_figure_to_analysis_artifact,
    plotly_figure_to_analysis_artifact,
    python_artifact_to_analysis_artifact,
    python_result_to_analysis_result,
)
from csv_analytics_agent.results.models import (
    AnalysisArtifact,
    AnalysisResult,
    AnalysisStatus,
)
from csv_analytics_agent.results.serializers import (
    MAX_PREVIEW_COLUMNS,
    MAX_PREVIEW_ROWS,
    SerializedArtifact,
    serialize_analysis_result,
    serialize_artifact,
)

__all__ = [
    "MAX_PREVIEW_COLUMNS",
    "MAX_PREVIEW_ROWS",
    "AnalysisArtifact",
    "AnalysisResult",
    "AnalysisStatus",
    "SerializedArtifact",
    "dataframe_to_analysis_artifact",
    "deterministic_result_to_analysis_result",
    "matplotlib_figure_to_analysis_artifact",
    "plotly_figure_to_analysis_artifact",
    "python_artifact_to_analysis_artifact",
    "python_result_to_analysis_result",
    "serialize_analysis_result",
    "serialize_artifact",
]
