"""Unit tests for Stage 8.11 Streamlit AI Analytics Workspace components."""

from __future__ import annotations

from streamlit_app.components.suggested_questions import (
    INITIAL_PROMPT_SUGGESTIONS,
    generate_contextual_followups,
)


def test_initial_prompt_suggestions_structure() -> None:
    """Verify initial prompt suggestions are populated with non-empty labels and queries."""
    assert len(INITIAL_PROMPT_SUGGESTIONS) >= 4
    for label, prompt_text in INITIAL_PROMPT_SUGGESTIONS:
        assert isinstance(label, str) and label.strip()
        assert isinstance(prompt_text, str) and prompt_text.strip()


def test_generate_contextual_followups_category() -> None:
    """Verify contextual follow-up suggestions generated for category queries."""
    text = "Electronics generated the highest revenue in the dataset."
    followups = generate_contextual_followups(text)
    assert len(followups) >= 3
    assert any("electronics" in f.lower() or "category" in f.lower() for f in followups)


def test_generate_contextual_followups_revenue() -> None:
    """Verify contextual follow-up suggestions generated for revenue/units queries."""
    text = "Total revenue equals $756,000.0 across all orders."
    followups = generate_contextual_followups(text)
    assert len(followups) >= 3
    assert any("units sold" in f.lower() or "correlation" in f.lower() for f in followups)


def test_generate_contextual_followups_fallback() -> None:
    """Verify contextual follow-up suggestions fallback gracefully for arbitrary answers."""
    text = "Analysis completed successfully."
    followups = generate_contextual_followups(text)
    assert len(followups) == 3
