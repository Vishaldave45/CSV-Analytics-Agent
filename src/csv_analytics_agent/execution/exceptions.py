"""Exceptions for the Stage 5 Execution Engine Framework."""

from csv_analytics_agent.exceptions.data_errors import CSVAnalyticsError


class ExecutionError(CSVAnalyticsError):
    """Base exception for all execution engine and provider failures."""

    pass


class ProviderError(ExecutionError):
    """Base exception for errors originating inside execution providers."""

    pass


class CapabilityNotFoundError(ExecutionError, KeyError):
    """Raised when a requested capability is not registered in the CapabilityRegistry."""

    pass


class EngineValidationError(ExecutionError, ValueError):
    """Raised when an execution request fails parameter or column validation."""

    pass


__all__ = [
    "CapabilityNotFoundError",
    "EngineValidationError",
    "ExecutionError",
    "ProviderError",
]
