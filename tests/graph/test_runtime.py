"""Unit tests for Agent Runtime and in-memory LangGraph checkpointing."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest
from langchain_core.messages import AIMessage, BaseMessage
from langgraph.checkpoint.memory import InMemorySaver

from csv_analytics_agent.config.setting import Settings
from csv_analytics_agent.execution.registry import CapabilityRegistry
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
def runtime_instance(sample_df: pd.DataFrame) -> AgentRuntime:
    mock_llm = MockLLM()
    mock_registry = MagicMock(spec=CapabilityRegistry)
    mock_registry.discover.return_value = []
    mock_memory = MagicMock(spec=MemoryService)

    return AgentRuntime(
        llm=mock_llm,
        registry=mock_registry,
        memory_service=mock_memory,
        dataframe=sample_df,
        settings=Settings(default_thread_id="t_test"),
        checkpointer=InMemorySaver(),
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


def test_inmemory_saver_operations(tmp_path: Path) -> None:
    """Verify in-memory saver put, get_tuple, put_writes, list, and delete_thread."""
    saver = InMemorySaver()

    cfg_t1 = {
        "configurable": {"thread_id": "thread_1", "checkpoint_ns": "", "checkpoint_id": "cp_1"}
    }
    cfg_t2 = {
        "configurable": {"thread_id": "thread_2", "checkpoint_ns": "", "checkpoint_id": "cp_2"}
    }

    cp1 = {
        "v": 1,
        "id": "cp_1",
        "ts": "",
        "channel_values": {"val": 100},
        "channel_versions": {},
        "versions_seen": {},
        "updated_channels": [],
    }
    cp2 = {
        "v": 1,
        "id": "cp_2",
        "ts": "",
        "channel_values": {"val": 200},
        "channel_versions": {},
        "versions_seen": {},
        "updated_channels": [],
    }

    saver.put(cfg_t1, cp1, {"source": "update", "step": 1, "parents": {}}, {})
    saver.put(cfg_t2, cp2, {"source": "update", "step": 1, "parents": {}}, {})

    t1_tuple = saver.get_tuple(cfg_t1)
    assert t1_tuple is not None
    assert t1_tuple.checkpoint["id"] == "cp_1"

    t2_tuple = saver.get_tuple(cfg_t2)
    assert t2_tuple is not None
    assert t2_tuple.checkpoint["id"] == "cp_2"

    t1_list = list(saver.list(cfg_t1))
    assert len(t1_list) == 1
    assert t1_list[0].checkpoint["id"] == "cp_1"

    saver.put_writes(cfg_t1, [("channel_a", "payload_a")], task_id="task_1")
    t1_tuple_with_writes = saver.get_tuple(cfg_t1)
    assert t1_tuple_with_writes is not None
    assert len(t1_tuple_with_writes.pending_writes) == 1

    saver.delete_thread("thread_1")
    assert saver.get_tuple(cfg_t1) is None
    assert saver.get_tuple(cfg_t2) is not None


def test_runtime_configuration_passthrough(sample_df: pd.DataFrame) -> None:
    """Verify Settings configuration (model_name, max_iterations) reaches AgentRuntime."""
    settings = Settings(
        default_thread_id="t_cfg",
        max_iterations=12,
    )
    mock_llm = MockLLM()
    mock_registry = MagicMock(spec=CapabilityRegistry)
    mock_memory = MagicMock(spec=MemoryService)

    runtime = AgentRuntime(
        llm=mock_llm,
        registry=mock_registry,
        memory_service=mock_memory,
        dataframe=sample_df,
        settings=settings,
        checkpointer=InMemorySaver(),
    )

    assert runtime._settings.max_iterations == 12
    assert runtime._llm.model_name == "mock_runtime_llm"
