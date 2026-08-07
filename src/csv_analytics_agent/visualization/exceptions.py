"""Exceptions for visualization module."""

from csv_analytics_agent.exceptions.data_errors import CSVAnalyticsError


class VisualizationError(CSVAnalyticsError):
    """Base exception for visualization errors."""

    pass


class NoSuitableVisualizationError(VisualizationError, ValueError):
    """Raised when no suitable visualization specs can be generated for a dataset profile."""

    pass
