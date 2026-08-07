"""Unit tests and integration smoke tests for GeminiLLM provider."""

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from csv_analytics_agent.llm.gemini import GeminiLLM


def test_gemini_llm_mocked_invocation() -> None:
    """Test GeminiLLM wrapping a mocked Runnable/Chat model."""
    mock_runnable = MagicMock()
    mock_runnable.invoke.return_value = AIMessage(content="Mocked Gemini response")
    mock_runnable.bind_tools.return_value = mock_runnable

    gemini = GeminiLLM(model_name="gemini-2.5-flash", llm_instance=mock_runnable)
    assert gemini.model_name == "gemini-2.5-flash"

    bound_gemini = gemini.bind_tools([])
    assert bound_gemini.model_name == "gemini-2.5-flash"

    res = bound_gemini.invoke([HumanMessage(content="Test prompt")])
    assert res.content == "Mocked Gemini response"
    mock_runnable.invoke.assert_called_once()


@pytest.mark.llm
def test_gemini_real_api_smoke_test() -> None:
    """Smoke test against live Gemini API (marked with pytest.mark.llm)."""
    gemini = GeminiLLM(model_name="gemini-2.5-flash")
    response = gemini.invoke("Say 'hello' in one word.")
    assert isinstance(response, AIMessage)
    assert len(response.content) > 0
