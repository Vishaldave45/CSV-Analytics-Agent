"""Central logging configuration — supports structlog when available, falls back to stdlib.

Import once at process start via ``configure_logging()``. Every module should
call ``get_logger(__name__)`` to obtain a logger rather than using
``logging.getLogger`` directly so the structured / stdlib choice is centralised.

Usage::

    # In app.py (Streamlit entry point):
    from csv_analytics_agent.logging_config import configure_logging
    configure_logging(json_output=False)  # human-readable for local dev

    # In any module:
    from csv_analytics_agent.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("csv_load_start", filename="sales.csv", rows=1000)
"""

from __future__ import annotations

import logging
import sys
from typing import Any

_STRUCTLOG_AVAILABLE = False
try:
    import structlog  # pyright: ignore[reportMissingImports]

    _STRUCTLOG_AVAILABLE = True
except ModuleNotFoundError:
    pass


class _StdlibFallbackLogger:
    """Wrapper around stdlib logging.Logger supporting structlog-style keyword arguments."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def _format_event(self, event: str, kwargs: dict[str, Any]) -> str:
        ignored_keys = ("exc_info", "stack_info", "stacklevel")
        custom_kwargs = {k: v for k, v in kwargs.items() if k not in ignored_keys}
        if not custom_kwargs:
            return event
        kv_str = " ".join(f"{k}={v!r}" for k, v in custom_kwargs.items())
        return f"{event} | {kv_str}"

    def debug(self, event: str, *args: Any, **kwargs: Any) -> None:
        exc_info = kwargs.get("exc_info")
        msg = self._format_event(event, kwargs)
        self._logger.debug(msg, *args, exc_info=exc_info)

    def info(self, event: str, *args: Any, **kwargs: Any) -> None:
        exc_info = kwargs.get("exc_info")
        msg = self._format_event(event, kwargs)
        self._logger.info(msg, *args, exc_info=exc_info)

    def warning(self, event: str, *args: Any, **kwargs: Any) -> None:
        exc_info = kwargs.get("exc_info")
        msg = self._format_event(event, kwargs)
        self._logger.warning(msg, *args, exc_info=exc_info)

    def error(self, event: str, *args: Any, **kwargs: Any) -> None:
        exc_info = kwargs.get("exc_info")
        msg = self._format_event(event, kwargs)
        self._logger.error(msg, *args, exc_info=exc_info)

    def exception(self, event: str, *args: Any, **kwargs: Any) -> None:
        msg = self._format_event(event, kwargs)
        self._logger.exception(msg, *args)


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    """Configure the logging pipeline.

    When *structlog* is installed this sets up a fully structured JSON (or
    pretty-printed console) pipeline. When structlog is absent it falls back
    to a stdlib ``basicConfig`` setup so the rest of the code never needs to
    branch.

    Args:
        level: Logging level string — ``"DEBUG"``, ``"INFO"``, ``"WARNING"``, etc.
        json_output: Emit newline-delimited JSON (True) or human-readable console
            output (False). Set False when running via ``streamlit run`` locally.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )

    if not _STRUCTLOG_AVAILABLE:
        return

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """Return a structured logger for the given module name.

    Returns a structlog BoundLogger when structlog is available, otherwise
    a _StdlibFallbackLogger wrapping :class:`logging.Logger` with identical keyword-arg support.

    Args:
        name: Module name — pass ``__name__`` from the calling module.

    Returns:
        A logger instance compatible with keyword-argument log calls.
    """
    if _STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    return _StdlibFallbackLogger(logging.getLogger(name))


__all__ = ["configure_logging", "get_logger"]
