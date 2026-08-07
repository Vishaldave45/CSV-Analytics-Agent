"""Unit tests for Phase 2 execution exceptions."""

from csv_analytics_agent.exceptions.data_errors import CSVAnalyticsError
from csv_analytics_agent.execution.exceptions import (
    CapabilityNotFoundError,
    EngineValidationError,
    ExecutionError,
    ProviderError,
)


def test_exception_inheritance() -> None:
    """Verify execution exceptions inherit correctly from CSVAnalyticsError."""
    assert issubclass(ExecutionError, CSVAnalyticsError)
    assert issubclass(ProviderError, ExecutionError)
    assert issubclass(CapabilityNotFoundError, ExecutionError)
    assert issubclass(CapabilityNotFoundError, KeyError)
    assert issubclass(EngineValidationError, ExecutionError)
    assert issubclass(EngineValidationError, ValueError)
