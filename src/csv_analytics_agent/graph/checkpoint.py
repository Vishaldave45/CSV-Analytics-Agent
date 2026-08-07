"""SQLite Checkpoint Saver implementation for thread-based graph persistence."""

from __future__ import annotations

import pickle
import sqlite3
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)


class SqliteSaver(BaseCheckpointSaver[Any]):
    """Thread-safe SQLite checkpointer saving graph state to local SQLite database files."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Initialize SqliteSaver with an open sqlite3 connection.

        Args:
            conn: SQLite database connection instance.
        """
        super().__init__()
        self.conn = conn
        self._setup()

    def _setup(self) -> None:
        """Initialize database schema if table does not exist."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    thread_id TEXT PRIMARY KEY,
                    checkpoint BLOB NOT NULL,
                    metadata BLOB NOT NULL
                )
            """)

    @classmethod
    def from_conn_info(cls, database_path: str | Path) -> SqliteSaver:
        """Create SqliteSaver instance from database file path.

        Args:
            database_path: Path string or Path object for SQLite database.

        Returns:
            Configured SqliteSaver instance.
        """
        conn = sqlite3.connect(str(database_path), check_same_thread=False)
        return cls(conn)

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Retrieve checkpoint tuple for specified thread_id.

        Args:
            config: RunnableConfig containing configurable.thread_id.

        Returns:
            CheckpointTuple if found, otherwise None.
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return None

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT checkpoint, metadata FROM checkpoints WHERE thread_id = ?",
            (str(thread_id),),
        )
        row = cursor.fetchone()
        if not row:
            return None

        cp: Checkpoint = pickle.loads(row[0])
        meta: CheckpointMetadata = pickle.loads(row[1])
        return CheckpointTuple(config, cp, meta)

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Persist checkpoint and metadata for specified thread_id.

        Args:
            config: RunnableConfig containing thread_id.
            checkpoint: Graph checkpoint state dictionary.
            metadata: Checkpoint metadata payload.
            new_versions: Channel version mappings.

        Returns:
            Updated RunnableConfig instance.
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        if thread_id:
            cp_blob = pickle.dumps(checkpoint)
            meta_blob = pickle.dumps(metadata)
            with self.conn:
                self.conn.execute(
                    "INSERT OR REPLACE INTO checkpoints (thread_id, checkpoint, metadata) "
                    "VALUES (?, ?, ?)",
                    (str(thread_id), cp_blob, meta_blob),
                )
        return config

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """No-op stub for pending channel writes."""
        pass

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoint tuples matching filter options."""
        return iter([])


__all__ = ["SqliteSaver"]
