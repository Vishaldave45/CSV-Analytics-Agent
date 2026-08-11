"""SQLite Checkpoint Saver implementation for thread-based graph persistence."""

from __future__ import annotations

import sqlite3
import threading
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
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer


class SqliteSaver(BaseCheckpointSaver[Any]):
    """Thread-safe SQLite checkpointer saving graph state to local SQLite database files."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Initialize SqliteSaver with an open sqlite3 connection.

        Args:
            conn: SQLite database connection instance.
        """
        super().__init__()
        self.conn = conn
        self._lock = threading.Lock()
        self._serde = JsonPlusSerializer()
        self._setup()

    def _setup(self) -> None:
        """Initialize database schema if tables do not exist."""
        with self._lock, self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    checkpoint_id TEXT NOT NULL,
                    parent_checkpoint_id TEXT,
                    type TEXT NOT NULL,
                    checkpoint BLOB NOT NULL,
                    metadata BLOB NOT NULL,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS writes (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    checkpoint_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    idx INTEGER NOT NULL,
                    channel TEXT NOT NULL,
                    type TEXT NOT NULL,
                    value BLOB NOT NULL,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
                )
            """)

    @classmethod
    def from_conn_info(cls, database_path: str | Path) -> SqliteSaver:
        """Create SqliteSaver instance from database file path."""
        conn = sqlite3.connect(str(database_path), check_same_thread=False)
        return cls(conn)

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Retrieve checkpoint tuple for specified thread_id and checkpoint_id."""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return None

        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")

        with self._lock:
            cursor = self.conn.cursor()
            if checkpoint_id:
                cursor.execute(
                    "SELECT checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata "
                    "FROM checkpoints WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?",
                    (str(thread_id), str(checkpoint_ns), str(checkpoint_id)),
                )
            else:
                cursor.execute(
                    "SELECT checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata "
                    "FROM checkpoints WHERE thread_id = ? AND checkpoint_ns = ? "
                    "ORDER BY checkpoint_id DESC LIMIT 1",
                    (str(thread_id), str(checkpoint_ns)),
                )
            row = cursor.fetchone()
            if not row:
                return None

            cid, parent_cid, type_str, cp_blob, meta_blob = row

            cp: Checkpoint = self._serde.loads_typed((type_str, cp_blob))
            meta: CheckpointMetadata = self._serde.loads_typed((type_str, meta_blob))

            cursor.execute(
                "SELECT task_id, channel, type, value FROM writes "
                "WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ? "
                "ORDER BY task_id, idx",
                (str(thread_id), str(checkpoint_ns), str(cid)),
            )
            write_rows = cursor.fetchall()
            pending_writes: list[tuple[str, str, Any]] = []
            for w_task, w_chan, w_type, w_val in write_rows:
                val = self._serde.loads_typed((w_type, w_val))
                pending_writes.append((w_task, w_chan, val))

            cfg: RunnableConfig = {
                "configurable": {
                    "thread_id": str(thread_id),
                    "checkpoint_ns": str(checkpoint_ns),
                    "checkpoint_id": str(cid),
                }
            }

            return CheckpointTuple(
                cfg,
                cp,
                meta,
                parent_config=(
                    {
                        "configurable": {
                            "thread_id": str(thread_id),
                            "checkpoint_ns": str(checkpoint_ns),
                            "checkpoint_id": str(parent_cid),
                        }
                    }
                    if parent_cid
                    else None
                ),
                pending_writes=pending_writes,
            )

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Persist checkpoint and metadata for specified thread_id."""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return config

        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        checkpoint_id = checkpoint.get("id")
        parent_id = config.get("configurable", {}).get("checkpoint_id")

        kind, cp_blob = self._serde.dumps_typed(checkpoint)
        _, meta_blob = self._serde.dumps_typed(metadata)

        with self._lock, self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO checkpoints "
                "(thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    str(thread_id),
                    str(checkpoint_ns),
                    str(checkpoint_id),
                    str(parent_id) if parent_id else None,
                    kind,
                    cp_blob,
                    meta_blob,
                ),
            )

        return {
            "configurable": {
                "thread_id": str(thread_id),
                "checkpoint_ns": str(checkpoint_ns),
                "checkpoint_id": str(checkpoint_id),
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Persist pending channel writes."""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return

        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
        if not checkpoint_id:
            return

        with self._lock, self.conn:
            for idx, (channel, val) in enumerate(writes):
                kind, val_blob = self._serde.dumps_typed(val)
                self.conn.execute(
                    "INSERT OR REPLACE INTO writes "
                    "(thread_id, checkpoint_ns, checkpoint_id, task_id, idx, channel, type, value) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(thread_id),
                        str(checkpoint_ns),
                        str(checkpoint_id),
                        str(task_id),
                        idx,
                        str(channel),
                        kind,
                        val_blob,
                    ),
                )

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoint tuples matching filter options."""
        if not config:
            return iter([])

        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return iter([])

        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")

        query = (
            "SELECT checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata "
            "FROM checkpoints WHERE thread_id = ? AND checkpoint_ns = ? "
            "ORDER BY checkpoint_id DESC"
        )
        params: list[Any] = [str(thread_id), str(checkpoint_ns)]

        if limit and limit > 0:
            query += f" LIMIT {limit}"

        tuples: list[CheckpointTuple] = []
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                cid, parent_cid, type_str, cp_blob, meta_blob = row
                cp = self._serde.loads_typed((type_str, cp_blob))
                meta = self._serde.loads_typed((type_str, meta_blob))

                cfg: RunnableConfig = {
                    "configurable": {
                        "thread_id": str(thread_id),
                        "checkpoint_ns": str(checkpoint_ns),
                        "checkpoint_id": str(cid),
                    }
                }
                tuples.append(
                    CheckpointTuple(
                        cfg,
                        cp,
                        meta,
                        parent_config=(
                            {
                                "configurable": {
                                    "thread_id": str(thread_id),
                                    "checkpoint_ns": str(checkpoint_ns),
                                    "checkpoint_id": str(parent_cid),
                                }
                            }
                            if parent_cid
                            else None
                        ),
                    )
                )

        return iter(tuples)


__all__ = ["SqliteSaver"]
