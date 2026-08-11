"""LangGraph state, adapter, router, retrieval, planner, tool, explainer, build, & runtime."""

from typing import Any

from csv_analytics_agent.graph.adapter import (
    CapabilityToolInput,
    as_langchain_tool,
    as_langchain_tools,
)
from csv_analytics_agent.graph.build import (
    build_graph,
    reset_node,
    route_after_planner,
    route_after_router,
)
from csv_analytics_agent.graph.explainer import (
    explainer_node,
    format_execution_explanation,
)
from csv_analytics_agent.graph.memory_update import memory_update_node
from csv_analytics_agent.graph.message_utils import extract_last_human_text
from csv_analytics_agent.graph.planner import (
    DEFAULT_MAX_ITERATIONS,
    planner_node,
)
from csv_analytics_agent.graph.retrieval import (
    EmptyQueryError,
    IndexNotFoundError,
    RetrievalError,
    retrieval_node,
)
from csv_analytics_agent.graph.router import (
    RouterDecision,
    RouterIntent,
    router_node,
)
from csv_analytics_agent.graph.runtime import AgentRuntime
from csv_analytics_agent.graph.state import (
    AgentState,
    FilterPayload,
    FilterValue,
    MetadataValue,
    create_initial_state,
)
from csv_analytics_agent.graph.tool_node import tool_node

# Optional imports that may be unavailable in lightweight test environments.
_GeminiLLM: type[Any] | None
try:
    from csv_analytics_agent.llm.gemini import GeminiLLM as _GeminiLLM
except ImportError:  # pragma: no cover
    _GeminiLLM = None

_MemoryService: type[Any] | None
try:
    from csv_analytics_agent.memory.service import MemoryService as _MemoryService
except ImportError:  # pragma: no cover
    _MemoryService = None

GeminiLLM: type[Any] | None = _GeminiLLM
MemoryService: type[Any] | None = _MemoryService

__all__ = [
    "DEFAULT_MAX_ITERATIONS",
    "AgentRuntime",
    "AgentState",
    "CapabilityToolInput",
    "EmptyQueryError",
    "FilterPayload",
    "FilterValue",
    "IndexNotFoundError",
    "MetadataValue",
    "RetrievalError",
    "RouterDecision",
    "RouterIntent",
    "as_langchain_tool",
    "as_langchain_tools",
    "build_graph",
    "create_initial_state",
    "explainer_node",
    "extract_last_human_text",
    "format_execution_explanation",
    "memory_update_node",
    "planner_node",
    "reset_node",
    "retrieval_node",
    "route_after_planner",
    "route_after_router",
    "router_node",
    "tool_node",
]
