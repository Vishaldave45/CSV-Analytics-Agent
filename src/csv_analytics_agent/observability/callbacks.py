"""Callback handlers and global callback registry for LangSmith tracing."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger("csv_analytics_agent.observability")

_GLOBAL_CALLBACKS: list[BaseCallbackHandler] = []


class AgentTracingCallbackHandler(BaseCallbackHandler):
    """Custom callback handler capturing graph transitions, tool calls, and execution metrics."""

    def __init__(self, logger_instance: logging.Logger | None = None) -> None:
        """Initialize callback handler.

        Args:
            logger_instance: Optional custom logger instance.
        """
        super().__init__()
        self.logger = logger_instance or logger

    def on_llm_start(self, serialized: dict[str, Any] | None, prompts: list[str] | None, **kwargs: Any) -> None:
        """Triggered when LLM invocation begins."""
        model_name = serialized.get("name", "LLM") if isinstance(serialized, dict) else "LLM"
        prompt_count = len(prompts) if isinstance(prompts, list) else 0
        self.logger.info("LLM Invocation Started: %s (Prompts: %d)", model_name, prompt_count)

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Triggered when LLM invocation completes."""
        self.logger.info("LLM Invocation Completed Successfully.")

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        """Triggered when LLM encounters an exception."""
        self.logger.error("LLM Invocation Failed: %s", error)

    def on_tool_start(self, serialized: dict[str, Any] | None, input_str: str | None, **kwargs: Any) -> None:
        """Triggered when tool execution starts."""
        tool_name = serialized.get("name", "unknown_tool") if isinstance(serialized, dict) else "unknown_tool"
        self.logger.info("Tool Execution Started: '%s' with input: %s", tool_name, input_str)

    def on_tool_end(self, output: Any, **kwargs: Any) -> None:
        """Triggered when tool execution completes."""
        output_size = 0
        if isinstance(output, str):
            output_size = len(output)
        elif output is not None:
            output_size = len(str(output))
        self.logger.info("Tool Execution Completed: Payload size %d bytes", output_size)

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        """Triggered when tool execution fails."""
        self.logger.error("Tool Execution Failed: %s", error)

    def on_chain_start(
        self, serialized: dict[str, Any] | None, inputs: dict[str, Any] | None, **kwargs: Any
    ) -> None:
        """Triggered when graph node or chain starts."""
        name = serialized.get("name", "Node/Chain") if isinstance(serialized, dict) else "Node/Chain"
        self.logger.debug("Graph Step Started: '%s'", name)

    def on_chain_end(self, outputs: dict[str, Any], **kwargs: Any) -> None:
        """Triggered when graph node or chain ends."""
        self.logger.debug("Graph Step Completed Successfully.")


def register_callback(handler: BaseCallbackHandler) -> None:
    """Register a new callback handler into the global registry.

    Args:
        handler: BaseCallbackHandler instance to register.
    """
    if handler not in _GLOBAL_CALLBACKS:
        _GLOBAL_CALLBACKS.append(handler)
        logger.info("Registered callback handler: %s", handler.__class__.__name__)


def clear_callbacks() -> None:
    """Clear all registered callback handlers from the global registry."""
    _GLOBAL_CALLBACKS.clear()
    logger.info("Cleared all registered callback handlers.")


def get_callbacks() -> list[BaseCallbackHandler]:
    """Return a copy of all registered callback handlers.

    Returns:
        List of BaseCallbackHandler instances.
    """
    return list(_GLOBAL_CALLBACKS)


class EvaluationDatasetPlaceholder:
    """Placeholder for future LangSmith Evaluation Dataset integrations."""

    def __init__(self, dataset_name: str = "csv_analytics_eval_v1") -> None:
        self.dataset_name = dataset_name

    def record_example(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> None:
        """Placeholder method for recording evaluation examples."""
        logger.debug(
            "Recorded evaluation example for dataset '%s': inputs=%s",
            self.dataset_name,
            list(inputs.keys()),
        )


__all__ = [
    "AgentTracingCallbackHandler",
    "EvaluationDatasetPlaceholder",
    "clear_callbacks",
    "get_callbacks",
    "register_callback",
]
