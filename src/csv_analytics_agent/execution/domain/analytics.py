"""Analytics domain engine implementation.

This module orchestrates data manipulation capabilities (aggregate, filter, group, sort, top_n)
by validating requests and selecting an appropriate provider dynamically.
"""

from __future__ import annotations

import pandas as pd

from csv_analytics_agent.execution.base import BaseEngine, BaseProvider
from csv_analytics_agent.execution.exceptions import (
    EngineValidationError,
    ProviderError,
)
from csv_analytics_agent.execution.models import (
    CapabilityDescriptor,
    EngineMetadata,
    ExecutionRequest,
    ExecutionResult,
)


class AnalyticsEngine(BaseEngine):
    """Domain engine orchestrating analytical data capabilities."""

    def __init__(self, providers: list[BaseProvider] | None = None) -> None:
        """Initialize AnalyticsEngine with a list of available execution providers.

        Args:
            providers: List of execution providers (defaults to PandasProvider if None).
        """
        if providers is None:
            from csv_analytics_agent.execution.providers.pandas import PandasProvider

            providers = [PandasProvider()]
        self._providers = providers

    @property
    def metadata(self) -> EngineMetadata:
        return EngineMetadata(
            name="analytics",
            version="1.0.0",
            supported_capabilities=[
                "describe",
                "aggregate",
                "filter",
                "group",
                "sort",
                "top_n",
            ],
        )

    def list_capabilities(self) -> list[CapabilityDescriptor]:
        return [
            CapabilityDescriptor(
                name="describe",
                description="Provides dataset inspection metadata such as schema, data types, missing values, duplicates, and sample cardinality.",
                parameters_schema={
                    "type": "object",
                    "properties": {},
                },
                provider_name="pandas",
                preferred_execution_engine="deterministic_engine",
                fallback_execution_engine="python_engine",
                output_contract={"type": "dictionary", "structure": "dataset_profile"},
            ),
            CapabilityDescriptor(
                name="aggregate",
                description="Computes numeric summary aggregations on a target column.",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": [
                                "mean",
                                "sum",
                                "median",
                                "min",
                                "max",
                                "count",
                                "std",
                                "var",
                                "mode",
                            ],
                            "description": "Aggregation operation name.",
                        }
                    },
                    "required": ["operation"],
                },
                provider_name="pandas",
                preferred_execution_engine="deterministic_engine",
                fallback_execution_engine="python_engine",
                output_contract={"type": "scalar", "data_type": "numeric"},
            ),
            CapabilityDescriptor(
                name="filter",
                description="Filters rows in dataset based on column comparison conditions.",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "operator": {
                            "type": "string",
                            "enum": ["eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in"],
                            "description": "Comparison filter operator.",
                        },
                        "value": {"description": "Comparison target value or list."},
                    },
                    "required": ["operator", "value"],
                },
                provider_name="pandas",
                preferred_execution_engine="deterministic_engine",
                fallback_execution_engine="python_engine",
                output_contract={"type": "table", "format": "dataframe"},
            ),
            CapabilityDescriptor(
                name="group",
                description="Groups rows by category and calculates aggregated metrics.",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "by": {"type": "string", "description": "Categorical group-by column."},
                        "target": {
                            "type": "string",
                            "description": "Target numeric column.",
                        },
                        "operation": {
                            "type": "string",
                            "enum": ["mean", "sum", "count", "min", "max"],
                        },
                    },
                    "required": ["by", "target"],
                },
                provider_name="pandas",
                preferred_execution_engine="deterministic_engine",
                fallback_execution_engine="python_engine",
                output_contract={"type": "dictionary", "structure": "grouped_metric"},
            ),
            CapabilityDescriptor(
                name="sort",
                description="Sorts rows by specified column(s) in ascending or descending order.",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "order": {"type": "string", "enum": ["asc", "desc"], "default": "asc"}
                    },
                },
                provider_name="pandas",
                preferred_execution_engine="deterministic_engine",
                fallback_execution_engine="python_engine",
                output_contract={"type": "table", "format": "dataframe"},
            ),
            CapabilityDescriptor(
                name="top_n",
                description="Retrieves top N rows based on column ordering.",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "n": {"type": "integer", "default": 5},
                        "order": {"type": "string", "enum": ["desc", "asc"], "default": "desc"},
                    },
                },
                provider_name="pandas",
                preferred_execution_engine="deterministic_engine",
                fallback_execution_engine="python_engine",
                output_contract={"type": "table", "format": "dataframe"},
            ),
        ]

    def _select_provider(self, capability: str) -> BaseProvider:
        for provider in self._providers:
            if provider.supports(capability):
                return provider
        raise ProviderError(f"No provider available supporting capability '{capability}'.")

    def execute_capability(
        self,
        request: ExecutionRequest,
        df: pd.DataFrame,
    ) -> ExecutionResult:
        """Validate request and delegate execution to the best matching provider.

        Args:
            request: Execution request payload.
            df: Target pandas DataFrame.

        Returns:
            ExecutionResult payload.

        Raises:
            EngineValidationError: If request validation fails.
            ProviderError: If execution fails.
        """
        if request.capability_name not in self.metadata.supported_capabilities:
            raise EngineValidationError(
                f"AnalyticsEngine does not handle capability '{request.capability_name}'."
            )

        provider = self._select_provider(request.capability_name)
        return provider.execute(request, df)
