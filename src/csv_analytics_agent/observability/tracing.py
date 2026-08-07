"""LangSmith Tracing configuration and graceful environment setup."""

from __future__ import annotations

import logging
import os
from typing import Any

from csv_analytics_agent.observability.callbacks import (
    AgentTracingCallbackHandler,
    register_callback,
)
from csv_analytics_agent.observability.config import (
    ObservabilitySettings,
    get_observability_settings,
)

logger = logging.getLogger("csv_analytics_agent.observability")


def configure_langsmith(
    settings: ObservabilitySettings | None = None,
) -> bool:
    """Configure LangSmith environment variables and callback handlers gracefully.

    If LangSmith is disabled or API key is missing, logs a warning and returns False
    without crashing the application.

    Args:
        settings: Optional ObservabilitySettings instance.

    Returns:
        True if LangSmith tracing was successfully enabled, False otherwise.
    """
    obs_settings = settings or get_observability_settings()

    # Check if tracing is explicitly enabled in config or env
    tracing_enabled = obs_settings.tracing_v2 or os.getenv("LANGCHAIN_TRACING_V2") == "true"
    if not tracing_enabled:
        logger.info("LangSmith tracing is disabled (LANGCHAIN_TRACING_V2=false).")
        return False

    api_key = obs_settings.api_key or os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        logger.warning(
            "LangSmith tracing enabled, but no LANGCHAIN_API_KEY provided. "
            "Disabling tracing to prevent runtime errors."
        )
        return False

    try:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = obs_settings.project
        os.environ["LANGCHAIN_ENDPOINT"] = obs_settings.endpoint
        os.environ["LANGCHAIN_SESSION"] = obs_settings.session

        if obs_settings.tags:
            os.environ["LANGCHAIN_TAGS"] = ",".join(obs_settings.tags)

        # Register default tracing callback handler
        register_callback(AgentTracingCallbackHandler(logger_instance=logger))
        logger.info(
            "LangSmith tracing enabled for project '%s' (Endpoint: %s)",
            obs_settings.project,
            obs_settings.endpoint,
        )
        return True

    except Exception as err:
        logger.error("Failed to configure LangSmith tracing gracefully: %s", err)
        return False


def get_traced_metadata(
    thread_id: str,
    dataset_name: str = "dataset.csv",
    dataset_hash: str | None = None,
    model_name: str = "gemini-2.5-flash",
) -> dict[str, Any]:
    """Construct centralized run metadata payload for traced graph executions.

    Args:
        thread_id: Current session thread identifier string.
        dataset_name: Name of target CSV dataset.
        dataset_hash: Optional MD5/SHA256 hash string of dataset content.
        model_name: Name of active LLM model.

    Returns:
        Dictionary payload containing execution metadata fields.
    """
    return {
        "thread_id": thread_id,
        "dataset_name": dataset_name,
        "dataset_hash": dataset_hash or "unhashed",
        "model_name": model_name,
        "planner_version": "v0.7.6",
        "execution_framework_version": "v0.5.0",
        "agent_version": "v0.7.9",
    }


__all__ = [
    "configure_langsmith",
    "get_traced_metadata",
]
