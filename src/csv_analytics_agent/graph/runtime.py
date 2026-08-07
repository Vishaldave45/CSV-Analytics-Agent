"""Agent Runtime module assembling dependencies, graph execution, and thread checkpointing."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pandas as pd
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver

from csv_analytics_agent.config.setting import Settings, get_settings
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.build import build_graph
from csv_analytics_agent.graph.checkpoint import SqliteSaver
from csv_analytics_agent.graph.state import AgentState, create_initial_state
from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.memory.service import MemoryService
from csv_analytics_agent.observability.callbacks import get_callbacks


class AgentRuntime:
    """Agent Runtime managing graph assembly, dependency injection, and thread execution."""

    def __init__(
        self,
        llm: BaseLLM,
        registry: CapabilityRegistry,
        memory_service: MemoryService,
        dataframe: pd.DataFrame,
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
            settings: Optional Settings instance (defaults to get_settings()).
            checkpointer: Optional BaseCheckpointSaver instance (defaults to SqliteSaver).
            callbacks: Optional list of LangChain BaseCallbackHandler instances.
        """
        self._llm = llm
        self._registry = registry
        self._memory_service = memory_service
        self._dataframe = dataframe
        self._settings = settings or get_settings()
        self._callbacks = callbacks if callbacks is not None else get_callbacks()

        if checkpointer is not None:
            self._checkpointer: BaseCheckpointSaver[Any] = checkpointer
        else:
            db_path: Path = self._settings.checkpoint_path
            self._checkpointer = SqliteSaver.from_conn_info(db_path)

        self._graph = build_graph(
            llm=self._llm,
            registry=self._registry,
            memory_service=self._memory_service,
            dataframe=self._dataframe,
            checkpointer=self._checkpointer,
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

    def run(self, prompt: str, thread_id: str | None = None) -> AgentState:
        """Execute agent workflow for a given user prompt under a thread_id session.

        Args:
            prompt: User query string.
            thread_id: Optional thread identifier (defaults to settings.default_thread_id).

        Returns:
            Updated AgentState dictionary.
        """
        tid = thread_id or self._settings.default_thread_id
        config_dict: dict[str, Any] = {"configurable": {"thread_id": tid}}
        if self._callbacks:
            config_dict["callbacks"] = self._callbacks

        config: RunnableConfig = cast(RunnableConfig, config_dict)

        initial_state = create_initial_state()
        initial_state["messages"] = [HumanMessage(content=prompt)]

        result_state = self._graph.invoke(initial_state, config=config)
        return cast(AgentState, result_state)

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
            return cast(AgentState, state_snapshot.values)

        return create_initial_state()

    def reset(self, thread_id: str | None = None) -> AgentState:
        """Reset conversation session state for a given thread_id.

        Args:
            thread_id: Optional thread identifier (defaults to settings.default_thread_id).

        Returns:
            Reset AgentState dictionary.
        """
        return self.run("reset", thread_id=thread_id)


__all__ = ["AgentRuntime"]
