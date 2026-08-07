"""Capability matcher for validating parsed intents against CapabilityRegistry."""

from __future__ import annotations

from typing import Any

from csv_analytics_agent.execution.models import CapabilityDescriptor
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.planner.models import IntentType, ParsedIntent


class CapabilityMatcher:
    """Matches ParsedIntent objects against descriptors in CapabilityRegistry."""

    def match(
        self,
        intent: ParsedIntent,
        registry: CapabilityRegistry,
    ) -> tuple[CapabilityDescriptor | None, dict[str, Any], list[str]]:
        """Match ParsedIntent against registered capabilities in CapabilityRegistry.

        Args:
            intent: Structured intent payload from QueryParser.
            registry: CapabilityRegistry instance.

        Returns:
            Tuple of (matched CapabilityDescriptor or None, validated parameters, reasoning trace).
        """
        trace: list[str] = [
            f"Matching intent '{intent.intent_type.value}' against CapabilityRegistry"
        ]

        if intent.intent_type == IntentType.UNKNOWN:
            trace.append("Intent type is UNKNOWN; no capability matched")
            return None, {}, trace

        target_cap_name = intent.intent_type.value
        available_descriptors = registry.discover()
        registered_names = [d.name for d in available_descriptors]

        if target_cap_name not in registered_names:
            err_msg = (
                f"Capability '{target_cap_name}' is not registered "
                f"in CapabilityRegistry (registered: {registered_names})"
            )
            trace.append(err_msg)
            return None, {}, trace

        reg = registry.get(target_cap_name)
        descriptor = reg.descriptor
        bound_msg = (
            f"Discovered registered capability '{descriptor.name}' "
            f"bound to provider '{descriptor.provider_name}'"
        )
        trace.append(bound_msg)

        parameters = dict(intent.parameters)
        return descriptor, parameters, trace


__all__ = ["CapabilityMatcher"]
