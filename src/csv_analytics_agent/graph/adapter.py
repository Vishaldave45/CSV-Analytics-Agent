"""Adapter module exposing Stage 5 capability descriptors as LangChain StructuredTools.

This module provides a pure adapter converting Stage 5 CapabilityDescriptors and CapabilityRegistry
into LangChain StructuredTool objects without adding business logic or bypassing the registry.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field, create_model

from csv_analytics_agent.execution.models import (
    CapabilityDescriptor,
    ExecutionRequest,
    ExecutionResult,
)
from csv_analytics_agent.execution.registry import CapabilityRegistry


class CapabilityToolInput(BaseModel):
    """Base Pydantic input model for capability tool arguments."""

    model_config = ConfigDict(extra="allow")

    target_columns: list[str] = Field(
        default_factory=list,
        description="Target dataset column names.",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution parameters for the capability.",
    )


def _build_args_schema(descriptor: CapabilityDescriptor) -> type[BaseModel]:
    """Construct a Pydantic v2 BaseModel for StructuredTool args_schema from descriptor.

    Args:
        descriptor: Target capability descriptor metadata.

    Returns:
        Pydantic BaseModel class defining argument schema for StructuredTool.
    """
    schema_name = f"{descriptor.name.title().replace('_', '')}Args"
    model = create_model(
        schema_name,
        __config__=ConfigDict(extra="allow"),
        target_columns=(
            list[str],
            Field(default_factory=list, description="Target dataset column names."),
        ),
        parameters=(
            dict[str, Any],
            Field(default_factory=dict, description="Capability execution parameters."),
        ),
    )
    return model


def as_langchain_tool(
    descriptor: CapabilityDescriptor,
    registry: CapabilityRegistry,
    df: pd.DataFrame,
) -> StructuredTool:
    """Adapt a single CapabilityDescriptor into a LangChain StructuredTool.

    Args:
        descriptor: CapabilityDescriptor metadata.
        registry: CapabilityRegistry containing bound domain engine.
        df: Target pandas DataFrame context.

    Returns:
        StructuredTool object ready for LLM function binding.
    """
    args_schema = _build_args_schema(descriptor)

    def _tool_func(
        target_columns: list[str] | None = None,
        parameters: dict[str, Any] | None = None,
        **extra_kwargs: Any,
    ) -> ExecutionResult[Any]:
        merged_params = dict(parameters or {})
        merged_params.update(extra_kwargs)

        request = ExecutionRequest(
            capability_name=descriptor.name,
            target_columns=target_columns or [],
            parameters=merged_params,
        )
        engine = registry.get_engine(descriptor.name)
        return engine.execute_capability(request, df)

    return StructuredTool.from_function(
        func=_tool_func,
        name=descriptor.name,
        description=descriptor.description,
        args_schema=args_schema,
    )


def as_langchain_tools(
    descriptors: list[CapabilityDescriptor],
    registry: CapabilityRegistry,
    df: pd.DataFrame,
) -> list[StructuredTool]:
    """Adapt a list of CapabilityDescriptors into LangChain StructuredTool objects.

    Args:
        descriptors: List of CapabilityDescriptor objects.
        registry: CapabilityRegistry instance containing registered engines.
        df: Target pandas DataFrame context.

    Returns:
        List of StructuredTool instances.
    """
    return [as_langchain_tool(desc, registry, df) for desc in descriptors]


__all__ = [
    "CapabilityToolInput",
    "as_langchain_tool",
    "as_langchain_tools",
]
