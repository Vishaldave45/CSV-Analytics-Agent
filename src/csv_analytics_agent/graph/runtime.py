"""Agent Runtime module assembling dependencies, graph execution, and thread checkpointing."""

from __future__ import annotations

from typing import Any, cast

import pandas as pd
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
)
from langgraph.checkpoint.memory import InMemorySaver

from csv_analytics_agent.config.setting import Settings, get_settings
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.build import build_graph
from csv_analytics_agent.graph.checkpoint import RuntimeArtifactStore
from csv_analytics_agent.graph.state import AgentState, create_initial_state
from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.llm.python_generator import (
    BasePythonCodeGenerator,
    GeminiPythonCodeGenerator,
)
from csv_analytics_agent.memory.service import MemoryService
from csv_analytics_agent.observability.callbacks import get_callbacks
from csv_analytics_agent.profiler.models import DatasetProfile
from csv_analytics_agent.python_engine.base import BasePythonExecutor
from csv_analytics_agent.python_engine.sandbox import create_python_executor


class AgentRuntime:
    """Agent Runtime managing graph assembly, dependency injection, and thread execution."""

    def __init__(
        self,
        llm: BaseLLM,
        registry: CapabilityRegistry,
        memory_service: MemoryService,
        dataframe: pd.DataFrame,
        python_generator: BasePythonCodeGenerator | None = None,
        python_executor: BasePythonExecutor | None = None,
        settings: Settings | None = None,
        checkpointer: BaseCheckpointSaver[Any] | None = None,
        callbacks: list[BaseCallbackHandler] | None = None,
    ) -> None:
        """Initialize AgentRuntime with dependencies and compiled graph.

        Args:
            llm: BaseLLM implementation dependency.
            registry: CapabilityRegistry instance containing domain capabilities.
            memory_service: MemoryService instance for vector retrieval/persistence.
            dataframe: Target pandas DataFrame context.
            python_generator: Optional BasePythonCodeGenerator instance.
            python_executor: Optional BasePythonExecutor instance.
            settings: Optional Settings instance (defaults to get_settings()).
            callbacks: Optional list of LangChain BaseCallbackHandler instances.
        """
        self._llm = llm
        self._registry = registry
        self._memory_service = memory_service
        self._dataframe = dataframe
        self._settings = settings or get_settings()
        self._callbacks = callbacks if callbacks is not None else get_callbacks()

        self._python_generator = python_generator or GeminiPythonCodeGenerator(llm=self._llm)
        self._python_executor = python_executor or create_python_executor(settings=self._settings)

        if checkpointer is not None:
            self._checkpointer: BaseCheckpointSaver[Any] = checkpointer
        else:
            self._checkpointer = InMemorySaver()
        self._artifact_store = RuntimeArtifactStore()

        self._graph = build_graph(
            llm=self._llm,
            registry=self._registry,
            memory_service=self._memory_service,
            dataframe=self._dataframe,
            python_generator=self._python_generator,
            python_executor=self._python_executor,
            checkpointer=self._checkpointer,
            artifact_store=self._artifact_store,
        )

    @property
    def settings(self) -> Settings:
        """Return runtime settings."""
        return self._settings

    @property
    def checkpointer(self) -> BaseCheckpointSaver[Any]:
        """Return runtime checkpointer."""
        return self._checkpointer

    @property
    def callbacks(self) -> list[BaseCallbackHandler]:
        """Return runtime callback handlers."""
        return list(self._callbacks)

    def run(
        self,
        prompt: str,
        thread_id: str | None = None,
        profile: DatasetProfile | None = None,
    ) -> AgentState:
        """Execute agent workflow for a given user prompt under a thread_id session.

        Args:
            prompt: User query string.
            thread_id: Optional thread identifier (defaults to settings.default_thread_id).
            profile: Optional DatasetProfile to seed into the AgentState so visualization
                     capabilities can access column statistics without re-profiling.

        Returns:
            Updated AgentState dictionary.
        """
        tid = thread_id or self._settings.default_thread_id
        config_dict: dict[str, Any] = {"configurable": {"thread_id": tid}}
        if self._callbacks:
            config_dict["callbacks"] = self._callbacks

        config: RunnableConfig = cast(RunnableConfig, config_dict)

        initial_state = create_initial_state(profile=profile)
        initial_state["messages"] = [HumanMessage(content=prompt)]

        result_state = self._graph.invoke(initial_state, config=config)
        return self._hydrate_runtime_state(cast(AgentState, result_state))

    def resume(self, thread_id: str | None = None) -> AgentState:
        """Resume conversation and return current checkpointed AgentState for a thread_id.

        Args:
            thread_id: Optional thread identifier (defaults to settings.default_thread_id).

        Returns:
            Checkpointed AgentState dictionary.
        """
        tid = thread_id or self._settings.default_thread_id
        config: RunnableConfig = cast(RunnableConfig, {"configurable": {"thread_id": tid}})

        state_snapshot = self._graph.get_state(config)
        if state_snapshot and state_snapshot.values:
            return self._hydrate_runtime_state(cast(AgentState, state_snapshot.values))

        return create_initial_state()

    def reset(self, thread_id: str | None = None) -> AgentState:
        """Reset conversation session state for a given thread_id.

        Args:
            thread_id: Optional thread identifier (defaults to settings.default_thread_id).

        Returns:
            Reset AgentState dictionary.
        """
        from csv_analytics_agent.graph.build import reset_node

        tid = thread_id or self._settings.default_thread_id
        clean_state = create_initial_state()
        reset_output = reset_node(clean_state)
        clean_state.update(cast(AgentState, reset_output))

        if hasattr(self._checkpointer, "delete_thread"):
            self._checkpointer.delete_thread(str(tid))
        self._artifact_store.clear()

        return clean_state

    def _hydrate_runtime_state(self, state: AgentState) -> AgentState:
        """Attach payloads only after a checkpointed state leaves the graph."""
        result = state.get("last_analysis_result")
        if result is None:
            return state
        hydrated = dict(result)
        hydrated["artifacts"] = [
            {**artifact, "payload": self._artifact_store.get(artifact["artifact_id"])}
            for artifact in result["artifacts"]
        ]
        returned = dict(state)
        returned["last_analysis_result"] = cast(Any, hydrated)
        return cast(AgentState, returned)


__all__ = ["AgentRuntime"]
