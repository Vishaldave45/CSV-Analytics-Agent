"""Pandas execution provider implementation.

This module encapsulates pandas DataFrame operations behind the BaseProvider interface,
hiding raw pandas APIs from higher-level domain engines.
"""

from __future__ import annotations

import time
from typing import Any

import pandas as pd

from csv_analytics_agent.execution.base import BaseProvider
from csv_analytics_agent.execution.exceptions import ProviderError
from csv_analytics_agent.execution.models import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ProviderMetadata,
)

SUPPORTED_CAPABILITIES: set[str] = {
    "describe",
    "aggregate",
    "filter",
    "group",
    "sort",
    "top_n",
}


class PandasProvider(BaseProvider):
    """Execution provider implementation using pandas DataFrames."""

    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name="pandas",
            version="1.0.0",
            description="Pandas in-memory execution provider.",
        )

    def supports(self, capability: str) -> bool:
        return capability in SUPPORTED_CAPABILITIES

    def execute(self, request: ExecutionRequest, df: pd.DataFrame) -> ExecutionResult:
        """Execute capability request using pandas DataFrame operations.

        Args:
            request: Validated execution request payload.
            df: Target pandas DataFrame.

        Returns:
            ExecutionResult payload.

        Raises:
            ProviderError: If capability is unsupported or execution fails.
        """
        if not self.supports(request.capability_name):
            raise ProviderError(
                f"PandasProvider does not support capability '{request.capability_name}'."
            )

        start_time = time.perf_counter()
        try:
            if request.capability_name == "describe":
                data, msg = self._execute_describe(df, request)
            elif request.capability_name == "aggregate":
                data, msg = self._execute_aggregate(df, request)
            elif request.capability_name == "filter":
                data, msg = self._execute_filter(df, request)
            elif request.capability_name == "group":
                data, msg = self._execute_group(df, request)
            elif request.capability_name == "sort":
                data, msg = self._execute_sort(df, request)
            elif request.capability_name == "top_n":
                data, msg = self._execute_top_n(df, request)
            else:
                raise ProviderError(f"Unhandled capability '{request.capability_name}'.")

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ExecutionResult(
                capability_name=request.capability_name,
                status=ExecutionStatus.SUCCESS,
                message=msg,
                data=data,
                execution_time_ms=round(elapsed_ms, 2),
            )

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            if isinstance(exc, ProviderError):
                raise
            raise ProviderError(f"PandasProvider execution failed: {exc}") from exc

    def _execute_aggregate(self, df: pd.DataFrame, request: ExecutionRequest) -> tuple[Any, str]:
        if not request.target_columns:
            raise ProviderError("Aggregate capability requires a target column.")

        column = request.target_columns[0]
        if column not in df.columns:
            raise ProviderError(f"Column '{column}' not found in DataFrame.")

        op_param = request.parameters.get("operation")
        series = df[column].dropna()

        if series.empty and op_param != "count":
            raise ProviderError(f"Column '{column}' contains no non-null values for aggregation.")

        is_numeric = pd.api.types.is_numeric_dtype(series)
        if op_param:
            op = str(op_param).lower()
        else:
            op = "mean" if is_numeric else "count"

        # Coerce numeric if user requested mean/sum/median/std on non-numeric column
        if op in ("mean", "sum", "median", "std", "var", "variance") and not is_numeric:
            coerced = pd.to_numeric(series, errors="coerce").dropna()
            if not coerced.empty and len(coerced) > len(series) * 0.5:
                series = coerced
                is_numeric = True
            else:
                op = "count"

        val: Any = None
        if op == "mean":
            val = float(series.mean())
        elif op == "sum":
            val = float(series.sum())
        elif op == "median":
            val = float(series.median())
        elif op == "min":
            val = float(series.min()) if is_numeric else str(series.min())
        elif op == "max":
            val = float(series.max()) if is_numeric else str(series.max())
        elif op == "count":
            val = float(len(series))
        elif op == "std":
            val = float(series.std())
        elif op in ("variance", "var"):
            val = float(series.var())
        elif op == "mode":
            val = str(series.mode().iloc[0]) if not series.mode().empty else None
        else:
            raise ProviderError(f"Unsupported aggregate operation '{op}'.")

        return val, f"Calculated {op} on column '{column}': {val}"

    def _execute_filter(
        self, df: pd.DataFrame, request: ExecutionRequest
    ) -> tuple[pd.DataFrame, str]:
        if not request.target_columns:
            raise ProviderError("Filter capability requires a target column.")

        column = request.target_columns[0]
        if column not in df.columns:
            raise ProviderError(f"Column '{column}' not found in DataFrame.")

        operator = str(request.parameters.get("operator", "eq")).lower()
        value = request.parameters.get("value")

        if operator in ("eq", "=="):
            res_df = df[df[column] == value]
        elif operator in ("ne", "!="):
            res_df = df[df[column] != value]
        elif operator in ("gt", ">"):
            res_df = df[df[column] > value]
        elif operator in ("gte", ">="):
            res_df = df[df[column] >= value]
        elif operator in ("lt", "<"):
            res_df = df[df[column] < value]
        elif operator in ("lte", "<="):
            res_df = df[df[column] <= value]
        elif operator == "in":
            if not isinstance(value, (list, tuple, set)):
                raise ProviderError("Operator 'in' requires a list or set value.")
            res_df = df[df[column].isin(value)]
        elif operator == "not_in":
            if not isinstance(value, (list, tuple, set)):
                raise ProviderError("Operator 'not_in' requires a list or set value.")
            res_df = df[~df[column].isin(value)]
        else:
            raise ProviderError(f"Unsupported filter operator '{operator}'.")

        return res_df, f"Filtered '{column}' {operator} {value}. Rows returned: {len(res_df)}"

    def _execute_group(
        self, df: pd.DataFrame, request: ExecutionRequest
    ) -> tuple[dict[str, Any], str]:
        by_col = request.parameters.get("by")
        target_col = request.parameters.get("target")

        # Fallback to target_columns if by or target omitted
        if not by_col and request.target_columns:
            by_col = request.target_columns[0]
            if len(request.target_columns) > 1 and not target_col:
                target_col = request.target_columns[1]
        elif by_col and not target_col and request.target_columns:
            for tc in request.target_columns:
                if tc != by_col:
                    target_col = tc
                    break

        if not by_col:
            raise ProviderError("Group capability requires 'by' column parameter.")
        if not target_col:
            target_col = by_col

        if by_col not in df.columns or target_col not in df.columns:
            raise ProviderError(f"Columns '{by_col}' and '{target_col}' must exist in DataFrame.")

        is_numeric = pd.api.types.is_numeric_dtype(df[target_col])
        op_param = request.parameters.get("operation")
        if op_param:
            op = str(op_param).lower()
        else:
            op = "mean" if (is_numeric and target_col != by_col) else "count"

        # Coerce or fallback to count for non-numeric target columns
        if op in ("mean", "sum", "min", "max") and not is_numeric:
            coerced = pd.to_numeric(df[target_col], errors="coerce")
            if coerced.notna().sum() > len(df) * 0.5:
                temp_df = df[[by_col]].copy()
                temp_df[target_col] = coerced
                grouped = temp_df.groupby(by_col)[target_col]
            else:
                op = "count"
                grouped = df.groupby(by_col)[target_col]
        else:
            grouped = df.groupby(by_col)[target_col]

        if op == "mean":
            res_series = grouped.mean()
        elif op == "sum":
            res_series = grouped.sum()
        elif op == "count":
            res_series = grouped.count()
        elif op == "min":
            res_series = grouped.min()
        elif op == "max":
            res_series = grouped.max()
        else:
            raise ProviderError(f"Unsupported group aggregation operation '{op}'.")

        res_dict = {
            str(k): float(v) if pd.notna(v) else 0.0 for k, v in res_series.to_dict().items()
        }
        msg = f"Grouped by '{by_col}' calculating {op} on '{target_col}' ({len(res_dict)} groups)."
        return res_dict, msg

    def _execute_sort(
        self, df: pd.DataFrame, request: ExecutionRequest
    ) -> tuple[pd.DataFrame, str]:
        if not request.target_columns:
            raise ProviderError("Sort capability requires at least one target column.")

        cols = request.target_columns
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ProviderError(f"Column(s) {missing} not found in DataFrame.")

        order = str(request.parameters.get("order", "asc")).lower()
        ascending = order in ("asc", "ascending", "true")
        sorted_df = df.sort_values(by=cols, ascending=ascending)

        return sorted_df, f"Sorted DataFrame by {cols} ({order})."

    def _execute_top_n(
        self, df: pd.DataFrame, request: ExecutionRequest
    ) -> tuple[pd.DataFrame, str]:
        if not request.target_columns:
            raise ProviderError("Top N capability requires a target column.")

        column = request.target_columns[0]
        if column not in df.columns:
            raise ProviderError(f"Column '{column}' not found in DataFrame.")

        n = int(request.parameters.get("n", 5))
        ascending = str(request.parameters.get("order", "desc")).lower() == "asc"
        top_df = df.sort_values(by=column, ascending=ascending).head(n)

        return top_df, f"Retrieved top {n} rows sorted by '{column}'."

    def _execute_describe(self, df: pd.DataFrame, request: ExecutionRequest) -> tuple[dict[str, Any], str]:
        profile = request.context_metadata.get("profile") if request.context_metadata else None
        if profile is None:
            from csv_analytics_agent.profiler.profiler import DatasetProfiler

            profile = DatasetProfiler().profile(df)

        column_summaries: list[dict[str, Any]] = []
        for column in profile.columns:
            column_summaries.append(
                {
                    "name": column.name,
                    "dtype": column.dtype,
                    "missing_percentage": column.missing_percentage,
                    "unique_count": column.unique_count,
                    "numeric_stats": column.numeric.dict() if column.numeric else None,
                    "categorical_stats": column.categorical.dict() if column.categorical else None,
                    "datetime_stats": column.datetime.dict() if column.datetime else None,
                }
            )

        result = {
            "summary": {
                "row_count": profile.summary.row_count,
                "column_count": profile.summary.column_count,
                "memory_usage_bytes": profile.summary.memory_usage_bytes,
                "total_missing_values": profile.missing.total_missing_values,
                "duplicate_rows": profile.duplicates.duplicate_rows,
            },
            "columns": column_summaries,
        }
        return result, "Described dataset schema, types, missing values, and duplicates."
