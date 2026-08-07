"""Stage 5 Execution Engine Framework package."""

from csv_analytics_agent.execution.base import BaseEngine, BaseProvider
from csv_analytics_agent.execution.domain.analytics import AnalyticsEngine
from csv_analytics_agent.execution.domain.visualization import VisualizationEngine
from csv_analytics_agent.execution.exceptions import (
    CapabilityNotFoundError,
    EngineValidationError,
    ExecutionError,
    ProviderError,
)
from csv_analytics_agent.execution.models import (
    CapabilityDescriptor,
    CapabilityRegistration,
    EngineMetadata,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ProviderMetadata,
)
from csv_analytics_agent.execution.providers.pandas import PandasProvider
from csv_analytics_agent.execution.registry import CapabilityRegistry

__all__ = [
    "AnalyticsEngine",
    "BaseEngine",
    "BaseProvider",
    "CapabilityDescriptor",
    "CapabilityNotFoundError",
    "CapabilityRegistration",
    "CapabilityRegistry",
    "EngineMetadata",
    "EngineValidationError",
    "ExecutionError",
    "ExecutionRequest",
    "ExecutionResult",
    "ExecutionStatus",
    "PandasProvider",
    "ProviderError",
    "ProviderMetadata",
    "VisualizationEngine",
]
