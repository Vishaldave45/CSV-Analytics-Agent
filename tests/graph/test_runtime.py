"""Unit tests for Stage 7.9 Agent Runtime & SQLite Checkpointer."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest
from langchain_core.messages import AIMessage, BaseMessage

from csv_analytics_agent.config.setting import Settings
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.checkpoint import SqliteSaver
from csv_analytics_agent.graph.runtime import AgentRuntime
from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.memory.service import MemoryService


class MockLLM(BaseLLM):
    """Mock LLM implementation for runtime integration testing."""

    def bind_tools(self, tools: list[Any]) -> BaseLLM:
        return self

    def invoke(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> BaseMessage:
        return AIMessage(content="Mock runtime response")

    def stream(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> Any:
        yield AIMessage(content="Mock runtime chunk")

    @property
    def model_name(self) -> str:
        return "mock_runtime_llm"


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({"salary": [50000.0, 60000.0]})


@pytest.fixture
def runtime_instance(tmp_path: Path, sample_df: pd.DataFrame) -> AgentRuntime:
    db_file = tmp_path / "test_sessions.db"
    settings = Settings(checkpoint_path=db_file, default_thread_id="t_test")
    saver = SqliteSaver.from_conn_info(db_file)

    mock_llm = MockLLM()
    mock_registry = MagicMock(spec=CapabilityRegistry)
    mock_registry.discover.return_value = []
    mock_memory = MagicMock(spec=MemoryService)

    return AgentRuntime(
        llm=mock_llm,
        registry=mock_registry,
        memory_service=mock_memory,
        dataframe=sample_df,
        settings=settings,
        checkpointer=saver,
    )


def test_agent_runtime_run_and_checkpoint(runtime_instance: AgentRuntime) -> None:
    """Verify AgentRuntime.run executes graph workflow and saves checkpoint."""
    res_state = runtime_instance.run("what capabilities", thread_id="t1")
    assert "messages" in res_state
    assert len(res_state["messages"]) > 0

    # Resume from checkpoint
    resumed = runtime_instance.resume("t1")
    assert "messages" in resumed
    assert len(resumed["messages"]) > 0


def test_agent_runtime_reset(runtime_instance: AgentRuntime) -> None:
    """Verify AgentRuntime.reset clears active_filters and session context."""
    reset_state = runtime_instance.reset("t1")
    assert reset_state["active_filters"] == []
    assert reset_state["retrieved_columns"] == []
    assert "reset" in reset_state["messages"][0].content.lower()
