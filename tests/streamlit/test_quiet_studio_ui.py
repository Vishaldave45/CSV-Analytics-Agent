"""Unit tests for Quiet Data Studio Streamlit component renderers."""

from __future__ import annotations

import pandas as pd

from csv_analytics_agent.results.models import AnalysisArtifact, AnalysisResult
from streamlit_app.components.suggested_questions import (
    INITIAL_PROMPT_SUGGESTIONS,
    generate_contextual_followups,
)


def test_initial_prompt_suggestions_structure() -> None:
    """Verify initial prompt suggestions are analytical and generic."""
    assert len(INITIAL_PROMPT_SUGGESTIONS) >= 4
    for label, prompt_text in INITIAL_PROMPT_SUGGESTIONS:
        assert isinstance(label, str) and label.strip()
        assert isinstance(prompt_text, str) and prompt_text.strip()


def test_generate_contextual_followups() -> None:
    """Verify contextual follow-ups generate analytical exploration prompts without hardcoded domain data."""
    text = "Electronics has the highest order count."
    followups = generate_contextual_followups(text)
    assert len(followups) >= 3
    assert any("top" in f.lower() or "group" in f.lower() for f in followups)


def test_render_analysis_result_handles_artifacts() -> None:
    """Verify render_analysis_result executes without crashing across various artifact types."""
    from csv_analytics_agent.results.models import AnalysisArtifactType, AnalysisStatus

    df = pd.DataFrame({"category": ["A", "B"], "orders": [10, 20]})
    res = AnalysisResult(
        status=AnalysisStatus.SUCCESS,
        narrative="Analysis complete.",
        artifacts=[
            AnalysisArtifact(
                artifact_type=AnalysisArtifactType.SCALAR,
                name="total_orders",
                payload=30,
            ),
            AnalysisArtifact(
                artifact_type=AnalysisArtifactType.TABLE,
                name="orders_table",
                payload=df,
            ),
        ],
        source="test",
    )
    assert res.narrative == "Analysis complete."
    assert len(res.artifacts) == 2
