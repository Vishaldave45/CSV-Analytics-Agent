"""Unit tests for callback handlers and registry."""

from unittest.mock import MagicMock

from csv_analytics_agent.observability.callbacks import (
    AgentTracingCallbackHandler,
    EvaluationDatasetPlaceholder,
    clear_callbacks,
    get_callbacks,
    register_callback,
)


def test_callback_registration_and_clearing() -> None:
    """Verify callback registration, get_callbacks, and clear_callbacks."""
    clear_callbacks()
    assert len(get_callbacks()) == 0

    handler = AgentTracingCallbackHandler()
    register_callback(handler)
    assert len(get_callbacks()) == 1
    assert get_callbacks()[0] is handler

    clear_callbacks()
    assert len(get_callbacks()) == 0


def test_agent_tracing_callback_handler_events() -> None:
    """Verify AgentTracingCallbackHandler logs lifecycle events without crashing."""
    mock_logger = MagicMock()
    handler = AgentTracingCallbackHandler(logger_instance=mock_logger)

    handler.on_llm_start({"name": "ChatGoogleGenerativeAI"}, ["Prompt text"])
    mock_logger.info.assert_called()

    handler.on_llm_end(response=None)
    handler.on_tool_start({"name": "aggregate"}, "target_columns=['salary']")
    handler.on_tool_end(output="result_data")

    assert mock_logger.info.call_count >= 3


def test_evaluation_dataset_placeholder() -> None:
    """Verify EvaluationDatasetPlaceholder method execution."""
    eval_stub = EvaluationDatasetPlaceholder(dataset_name="eval_set")
    assert eval_stub.dataset_name == "eval_set"
    eval_stub.record_example(inputs={"q": "salary"}, outputs={"ans": "50000"})
