"""Abstract base interfaces for execution providers and domain engines."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from csv_analytics_agent.execution.models import (
    CapabilityDescriptor,
    EngineMetadata,
    ExecutionRequest,
    ExecutionResult,
    ProviderMetadata,
)


class BaseProvider(ABC):
    """Abstract base class for execution providers encapsulating third-party engines."""

    @property
    @abstractmethod
    def metadata(self) -> ProviderMetadata:
        """Provider metadata descriptor."""
        pass

    @abstractmethod
    def supports(self, capability: str) -> bool:
        """Check whether provider supports executing the given capability.

        Args:
            capability: Capability name (e.g. 'aggregate', 'filter').

        Returns:
            True if supported, False otherwise.
        """
        pass

    @abstractmethod
    def execute(self, request: ExecutionRequest, df: pd.DataFrame) -> ExecutionResult:
        """Execute a capability request against a DataFrame.

        Args:
            request: Execution request payload.
            df: Target pandas DataFrame.

        Returns:
            ExecutionResult containing execution status and payload.
        """
        pass


class BaseEngine(ABC):
    """Abstract base class for domain engines orchestrating capabilities."""

    @property
    @abstractmethod
    def metadata(self) -> EngineMetadata:
        """Engine metadata descriptor."""
        pass

    @abstractmethod
    def list_capabilities(self) -> list[CapabilityDescriptor]:
        """List all capability descriptors exposed by this domain engine.

        Returns:
            List of capability descriptors.
        """
        pass

    @abstractmethod
    def execute_capability(
        self,
        request: ExecutionRequest,
        df: pd.DataFrame,
    ) -> ExecutionResult:
        """Validate and coordinate capability execution via an underlying provider.

        Args:
            request: Execution request payload.
            df: Target pandas DataFrame.

        Returns:
            ExecutionResult payload.
        """
        pass


__all__ = [
    "BaseEngine",
    "BaseProvider",
]
