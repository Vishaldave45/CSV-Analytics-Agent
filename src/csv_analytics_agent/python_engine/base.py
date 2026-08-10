"""Abstract base interface for Python execution engines."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from csv_analytics_agent.python_engine.models import (
    PythonExecutionRequest,
    PythonExecutionResult,
)


class BasePythonExecutor(ABC):
    """Provider-independent abstract contract for executing generated Python code."""

    @property
    @abstractmethod
    def executor_name(self) -> str:
        """Return programmatic name identifier of the executor implementation."""
        ...

    @abstractmethod
    def execute(
        self,
        request: PythonExecutionRequest,
        dataframe: pd.DataFrame,
    ) -> PythonExecutionResult:
        """Execute Python code against target DataFrame within sandbox boundary.

        Args:
            request: PythonExecutionRequest containing code and execution options.
            dataframe: Target pandas DataFrame context.

        Returns:
            PythonExecutionResult containing success status, outputs, and artifacts.
        """
        ...


__all__ = ["BasePythonExecutor"]
