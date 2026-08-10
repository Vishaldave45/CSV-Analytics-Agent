"""Central registry for capability discovery and LLM schema export."""

from __future__ import annotations

from typing import Any

from csv_analytics_agent.execution.base import BaseEngine
from csv_analytics_agent.execution.exceptions import CapabilityNotFoundError
from csv_analytics_agent.execution.models import (
    CapabilityDescriptor,
    CapabilityRegistration,
)
from csv_analytics_agent.logging_config import get_logger

logger = get_logger(__name__)


class CapabilityRegistry:
    """Central authority for registering, discovering, and exporting capability metadata.

    This class strictly manages metadata registration and schema discovery.
    It performs NO execution operations.
    """

    def __init__(self) -> None:
        self._registrations: dict[str, CapabilityRegistration] = {}
        self._bound_engines: dict[str, BaseEngine] = {}

    def register(
        self,
        descriptor: CapabilityDescriptor,
        engine: BaseEngine,
        priority: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a capability descriptor bound to a domain engine.

        Args:
            descriptor: Capability descriptor metadata.
            engine: Bound domain engine instance handling the capability.
            priority: Rank priority (default 0).
            metadata: Optional registration metadata.
        """
        reg = CapabilityRegistration(
            descriptor=descriptor,
            priority=priority,
            metadata=metadata or {},
        )
        self._registrations[descriptor.name] = reg
        self._bound_engines[descriptor.name] = engine
        logger.debug("capability_registered", name=descriptor.name, priority=priority)

    def unregister(self, name: str) -> None:
        """Unregister a capability by name.

        Args:
            name: Capability identifier.

        Raises:
            CapabilityNotFoundError: If capability is not registered.
        """
        if name not in self._registrations:
            raise CapabilityNotFoundError(f"Capability '{name}' is not registered.")
        del self._registrations[name]
        del self._bound_engines[name]

    def get(self, name: str) -> CapabilityRegistration:
        """Retrieve capability registration metadata by name.

        Args:
            name: Capability identifier.

        Returns:
            CapabilityRegistration container.

        Raises:
            CapabilityNotFoundError: If capability is not registered.
        """
        if name not in self._registrations:
            raise CapabilityNotFoundError(f"Capability '{name}' is not registered.")
        return self._registrations[name]

    def get_engine(self, name: str) -> BaseEngine:
        """Retrieve the domain engine bound to a capability.

        Args:
            name: Capability identifier.

        Returns:
            BaseEngine bound to the capability.

        Raises:
            CapabilityNotFoundError: If capability is not registered.
        """
        if name not in self._bound_engines:
            raise CapabilityNotFoundError(f"Capability '{name}' is not registered.")
        return self._bound_engines[name]

    def list_capabilities(self) -> list[str]:
        """List names of all registered capabilities.

        Returns:
            List of capability names sorted alphabetically.
        """
        return sorted(self._registrations.keys())

    def discover(self, capability_prefix: str | None = None) -> list[CapabilityDescriptor]:
        """Discover capability descriptors matching an optional prefix filter.

        Args:
            capability_prefix: Optional string prefix filter (e.g. 'analytics').

        Returns:
            List of matching CapabilityDescriptors sorted by registration priority.
        """
        regs = list(self._registrations.values())
        if capability_prefix:
            regs = [r for r in regs if r.descriptor.name.startswith(capability_prefix)]

        sorted_regs = sorted(regs, key=lambda r: r.priority, reverse=True)
        descriptors = [r.descriptor for r in sorted_regs]
        logger.debug("capability_discovered", count=len(descriptors), prefix=capability_prefix)
        return descriptors

    def export_llm_schema(self) -> list[dict[str, Any]]:
        """Export OpenAI/Anthropic/Gemini function calling schemas for all capabilities.

        Returns:
            List of function definitions structured for LLM function calling.
        """
        tools: list[dict[str, Any]] = []
        for reg in self._registrations.values():
            desc = reg.descriptor
            tool_schema = {
                "type": "function",
                "function": {
                    "name": desc.name,
                    "description": desc.description,
                    "parameters": desc.parameters_schema
                    or {
                        "type": "object",
                        "properties": {
                            "target_columns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Target dataset column names.",
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Capability execution parameters.",
                            },
                        },
                    },
                },
            }
            tools.append(tool_schema)
        return tools
