"""Visualization adapter engine.

This module adapts Stage 4 visualization recommendations and rendering capabilities
into the Stage 5 Execution Engine Framework without modifying Stage 4.
"""

from __future__ import annotations

from typing import Any

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

    def execute(self, request: ExecutionRequest, df: pd.DataFrame) -> ExecutionResult[Any]:
        if request.capability_name == "recommend_visualization":
            profile: DatasetProfile | None = request.context_metadata.get("profile")
            if profile is None:
                raise ProviderError(
                    "Capability 'recommend_visualization' requires 'profile' in context_metadata."
                )
            plan: VisualizationPlan = recommend_visualizations(profile)
            chart_name = plan.primary.chart_type.value
            msg = f"Generated visualization plan with primary chart '{chart_name}'."
            return ExecutionResult[VisualizationPlan](
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
            elif isinstance(spec_dict, dict):
                spec = ChartSpecification.model_validate(spec_dict)
            else:
                raise ProviderError(
                    "Capability 'render_visualization' requires a valid 'spec' parameter."
                )

            save_path = request.parameters.get("save_path")
            img_bytes = render_chart(spec, df, save_path=save_path)
            return ExecutionResult[bytes](
                capability_name=request.capability_name,
                status=ExecutionStatus.SUCCESS,
                message=f"Rendered chart '{spec.chart_type.value}' into PNG bytes.",
                data=img_bytes,
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
                description="Generates a deterministic VisualizationPlan for a DatasetProfile.",
                parameters_schema={
                    "type": "object",
                    "properties": {},
                },
                provider_name="visualization_adapter",
            ),
            CapabilityDescriptor(
                name="render_visualization",
                description="Renders a ChartSpecification and DataFrame into PNG image bytes.",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "spec": {
                            "type": "object",
                            "description": "ChartSpecification definition.",
                        },
                        "save_path": {
                            "type": "string",
                            "description": "Optional output PNG file path.",
                        },
                    },
                    "required": ["spec"],
                },
                provider_name="visualization_adapter",
            ),
        ]

    def execute_capability(
        self,
        request: ExecutionRequest,
        df: pd.DataFrame,
    ) -> ExecutionResult[Any]:
        if request.capability_name not in self.metadata.supported_capabilities:
            raise EngineValidationError(
                f"VisualizationEngine does not handle capability '{request.capability_name}'."
            )
        return self._provider.execute(request, df)
