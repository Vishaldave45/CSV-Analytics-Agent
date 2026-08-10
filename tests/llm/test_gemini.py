"""Unit tests and integration smoke tests for GeminiLLM provider."""

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from csv_analytics_agent.llm.gemini import _TRANSIENT_EXCEPTIONS, GeminiLLM


def test_gemini_llm_mocked_invocation() -> None:
    """Test GeminiLLM wrapping a mocked Runnable/Chat model."""
    mock_runnable = MagicMock()
    mock_runnable.invoke.return_value = AIMessage(content="Mocked Gemini response")
    mock_runnable.bind_tools.return_value = mock_runnable

    gemini = GeminiLLM(model_name="gemini-2.0-flash", llm_instance=mock_runnable)
    assert gemini.model_name == "gemini-2.0-flash"

    bound_gemini = gemini.bind_tools([])
    assert bound_gemini.model_name == "gemini-2.0-flash"

    res = bound_gemini.invoke([HumanMessage(content="Test prompt")])
    assert res.content == "Mocked Gemini response"
    mock_runnable.invoke.assert_called_once()


def test_gemini_no_retry_on_invalid_api_key() -> None:
    """Test that auth/API key errors immediately raise ValueError without retrying."""
    mock_runnable = MagicMock()
    mock_runnable.invoke.side_effect = Exception("API_KEY_INVALID: Invalid key provided")

    gemini = GeminiLLM(model_name="gemini-2.0-flash", llm_instance=mock_runnable)

    with pytest.raises(ValueError, match="Invalid Google Gemini API Key"):
        gemini.invoke([HumanMessage(content="Test prompt")])

    assert mock_runnable.invoke.call_count == 1


def test_gemini_retry_on_transient_error() -> None:
    """Test that transient SDK/network errors are retried up to success."""
    if not _TRANSIENT_EXCEPTIONS:
        pytest.skip("No transient exception types registered in environment")

    transient_cls = _TRANSIENT_EXCEPTIONS[0]

    def _instantiate_err() -> Exception:
        try:
            return transient_cls("Transient error")
        except TypeError:
            try:
                return transient_cls(429, "Rate limit exceeded", {})  # type: ignore[call-arg]
            except Exception:
                return transient_cls()

    mock_runnable = MagicMock()
    mock_runnable.invoke.side_effect = [
        _instantiate_err(),
        _instantiate_err(),
        AIMessage(content="Recovered after retries"),
    ]

    gemini = GeminiLLM(model_name="gemini-2.0-flash", llm_instance=mock_runnable)
    res = gemini.invoke([HumanMessage(content="Test prompt")])

    assert res.content == "Recovered after retries"
    assert mock_runnable.invoke.call_count == 3


@pytest.mark.llm
def test_gemini_real_api_smoke_test() -> None:
    """Smoke test against live Gemini API (marked with pytest.mark.llm)."""
    gemini = GeminiLLM(model_name="gemini-2.0-flash")
    response = gemini.invoke("Say 'hello' in one word.")
    assert isinstance(response, AIMessage)
    assert len(response.content) > 0
