"""LangSmith Tracing configuration and graceful environment setup."""

from __future__ import annotations

import logging
import os
from importlib.metadata import PackageNotFoundError, version
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
    tracing_enabled = (
        obs_settings.tracing_v2
        or os.getenv("LANGSMITH_TRACING") == "true"
        or os.getenv("LANGCHAIN_TRACING_V2") == "true"
    )
    if not tracing_enabled:
        logger.info("LangSmith tracing is disabled (LANGSMITH_TRACING=false).")
        return False

    api_key = (
        obs_settings.api_key or os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    )
    if not api_key:
        logger.warning(
            "LangSmith tracing enabled, but no LANGSMITH_API_KEY / LANGCHAIN_API_KEY provided. "
            "Disabling tracing to prevent runtime errors."
        )
        return False

    project = (
        os.getenv("LANGSMITH_PROJECT")
        or os.getenv("LANGCHAIN_PROJECT")
        or obs_settings.project
        or "csv-analytics-agent"
    )
    endpoint = (
        os.getenv("LANGSMITH_ENDPOINT")
        or os.getenv("LANGCHAIN_ENDPOINT")
        or obs_settings.endpoint
        or "https://api.smith.langchain.com"
    )

    try:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGSMITH_API_KEY"] = api_key
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGSMITH_PROJECT"] = project
        os.environ["LANGCHAIN_PROJECT"] = project
        os.environ["LANGSMITH_ENDPOINT"] = endpoint
        os.environ["LANGCHAIN_ENDPOINT"] = endpoint
        os.environ["LANGCHAIN_SESSION"] = obs_settings.session

        if obs_settings.tags:
            os.environ["LANGCHAIN_TAGS"] = ",".join(obs_settings.tags)

        # Register default tracing callback handler
        register_callback(AgentTracingCallbackHandler(logger_instance=logger))
        logger.info(
            "LangSmith tracing enabled for project '%s' (Endpoint: %s)",
            project,
            endpoint,
        )
        return True

    except Exception as err:
        logger.error("Failed to configure LangSmith tracing gracefully: %s", err)
        return False


def get_traced_metadata(
    thread_id: str,
    dataset_name: str = "dataset.csv",
    dataset_hash: str | None = None,
    model_name: str | None = None,
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
    try:
        _agent_version = version("csv-analytics-agent")
    except PackageNotFoundError:
        _agent_version = "dev"

    if model_name is None:
        model_name = os.getenv("DEFAULT_MODEL_NAME", "gemini-flash-lite-latest")

    return {
        "thread_id": thread_id,
        "dataset_name": dataset_name,
        "dataset_hash": dataset_hash or "unhashed",
        "model_name": model_name,
        "agent_version": _agent_version,
    }


__all__ = [
    "configure_langsmith",
    "get_traced_metadata",
]
