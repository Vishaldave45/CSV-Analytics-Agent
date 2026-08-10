"""Visualization adapter engine.

This module adapts Stage 4 visualization recommendations and rendering capabilities
into the Stage 5 Execution Engine Framework without modifying Stage 4.
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
    ExecutionStatus,
    ProviderMetadata,
)
from csv_analytics_agent.profiler.models import DatasetProfile
from csv_analytics_agent.visualization import (
    ChartSpecification,
    VisualizationPlan,
    recommend_visualizations,
    render_chart,
)


class VisualizationProvider(BaseProvider):
    """Provider adapting Stage 4 recommendation and rendering implementations."""

    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name="visualization_adapter",
            version="1.0.0",
            description="Adapter provider bridging Stage 4 visualization engine.",
        )

    def supports(self, capability: str) -> bool:
        return capability in ("recommend_visualization", "render_visualization")

    def execute(self, request: ExecutionRequest, df: pd.DataFrame) -> ExecutionResult:
        if request.capability_name == "recommend_visualization":
            profile: DatasetProfile | None = request.context_metadata.get("profile")
            if profile is None:
                from csv_analytics_agent.profiler.profiler import DatasetProfiler

                profile = DatasetProfiler().profile(df)
            plan: VisualizationPlan = recommend_visualizations(profile)
            chart_name = plan.primary.chart_type.value
            msg = f"Generated visualization plan with primary chart '{chart_name}'."
            return ExecutionResult(
                capability_name=request.capability_name,
                status=ExecutionStatus.SUCCESS,
                message=msg,
                data=plan,
            )
        elif request.capability_name == "render_visualization":
            spec_dict = request.parameters.get("spec")
            spec: ChartSpecification
            if isinstance(spec_dict, ChartSpecification):
                spec = spec_dict
            else:
                raw_spec = (
                    dict(spec_dict) if isinstance(spec_dict, dict) else dict(request.parameters)
                )

                # Target columns fallback if x_axis / y_axis omitted
                if "x_axis" not in raw_spec and request.target_columns:
                    raw_spec["x_axis"] = request.target_columns[0]
                    if len(request.target_columns) > 1 and "y_axis" not in raw_spec:
                        raw_spec["y_axis"] = request.target_columns[1]

                # Convert string x_axis/y_axis to dicts
                if isinstance(raw_spec.get("x_axis"), str):
                    raw_spec["x_axis"] = {"column": raw_spec["x_axis"]}
                if isinstance(raw_spec.get("y_axis"), str):
                    raw_spec["y_axis"] = {"column": raw_spec["y_axis"]}

                chart_type_val = str(raw_spec.get("chart_type", "line")).lower()
                raw_spec["chart_type"] = chart_type_val

                if "title" not in raw_spec or not raw_spec["title"]:
                    x_col = (
                        raw_spec.get("x_axis", {}).get("column", "")
                        if isinstance(raw_spec.get("x_axis"), dict)
                        else ""
                    )
                    y_col = (
                        raw_spec.get("y_axis", {}).get("column", "")
                        if isinstance(raw_spec.get("y_axis"), dict)
                        else ""
                    )
                    raw_spec["title"] = f"{chart_type_val.title()} Chart ({y_col or x_col})"

                if "description" not in raw_spec or not raw_spec["description"]:
                    raw_spec["description"] = f"Rendered {chart_type_val} visualization chart."

                try:
                    spec = ChartSpecification.model_validate(raw_spec)
                except Exception as err:
                    raise ProviderError(
                        f"Capability 'render_visualization' failed with invalid spec: {err}"
                    ) from err

            save_path = request.parameters.get("save_path")
            img_bytes = render_chart(spec, df, save_path=save_path)
            return ExecutionResult(
                capability_name=request.capability_name,
                status=ExecutionStatus.SUCCESS,
                message=f"Rendered chart '{spec.chart_type.value}' into PNG bytes.",
                data=img_bytes,
                metadata={"chart_type": spec.chart_type.value, "title": spec.title},
            )
        else:
            raise ProviderError(
                f"Unsupported visualization capability '{request.capability_name}'."
            )


class VisualizationEngine(BaseEngine):
    """Domain engine adapting Stage 4 visualization capabilities."""

    def __init__(self, provider: BaseProvider | None = None) -> None:
        self._provider = provider or VisualizationProvider()

    @property
    def metadata(self) -> EngineMetadata:
        return EngineMetadata(
            name="visualization",
            version="1.0.0",
            supported_capabilities=["recommend_visualization", "render_visualization"],
        )

    def list_capabilities(self) -> list[CapabilityDescriptor]:
        return [
            CapabilityDescriptor(
                name="recommend_visualization",
                description=(
                    "Generates a deterministic VisualizationPlan with chart recommendations "
                    "for the dataset."
                ),
                parameters_schema={
                    "type": "object",
                    "properties": {},
                },
                provider_name="visualization_adapter",
            ),
            CapabilityDescriptor(
                name="render_visualization",
                description=(
                    "Renders a visualization chart (line, bar, histogram, scatter, boxplot, "
                    "pie, heatmap) into PNG image bytes. Parameters: chart_type, x_axis, "
                    "y_axis, title."
                ),
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "chart_type": {
                            "type": "string",
                            "enum": [
                                "line",
                                "bar",
                                "histogram",
                                "scatter",
                                "boxplot",
                                "pie",
                                "heatmap",
                            ],
                            "description": "Type of visualization chart.",
                        },
                        "x_axis": {
                            "type": "string",
                            "description": "Column name for primary X-axis.",
                        },
                        "y_axis": {
                            "type": "string",
                            "description": "Optional column name for Y-axis.",
                        },
                        "title": {
                            "type": "string",
                            "description": "Optional title of the chart.",
                        },
                        "spec": {
                            "type": "object",
                            "description": "Optional nested ChartSpecification object.",
                        },
                        "save_path": {
                            "type": "string",
                            "description": "Optional output PNG file path.",
                        },
                    },
                },
                provider_name="visualization_adapter",
            ),
        ]

    def execute_capability(
        self,
        request: ExecutionRequest,
        df: pd.DataFrame,
    ) -> ExecutionResult:
        if request.capability_name not in self.metadata.supported_capabilities:
            raise EngineValidationError(
                f"VisualizationEngine does not handle capability '{request.capability_name}'."
            )
        return self._provider.execute(request, df)
