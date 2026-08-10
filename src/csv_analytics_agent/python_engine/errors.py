"""Domain exceptions for Python Execution Engine."""

from __future__ import annotations

from csv_analytics_agent.exceptions.data_errors import CSVAnalyticsError


class PythonExecutionError(CSVAnalyticsError):
    """Base exception for all Python execution engine failures."""

    pass


class PythonValidationError(PythonExecutionError, ValueError):
    """Raised when Python execution request or code fails validation."""

    pass


class PythonTimeoutError(PythonExecutionError, TimeoutError):
    """Raised when Python execution exceeds specified timeout duration."""

    pass


class PythonOutputLimitError(PythonExecutionError, ValueError):
    """Raised when Python execution output size exceeds max_output_bytes limit."""

    pass


class PythonArtifactError(PythonExecutionError, ValueError):
    """Raised when artifact creation, extraction, or payload structure fails."""

    pass


__all__ = [
    "PythonArtifactError",
    "PythonExecutionError",
    "PythonOutputLimitError",
    "PythonTimeoutError",
    "PythonValidationError",
]
