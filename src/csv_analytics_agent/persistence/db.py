"""Database engine and session factory for application metadata persistence."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from csv_analytics_agent.persistence.models import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def init_db(database_url: str = "sqlite:///app_metadata.db") -> None:
    """Initialize database engine and sessionmaker.

    Args:
        database_url: Database connection string (defaults to local SQLite file).
    """
    global _engine, _SessionLocal
    connect_args: dict[str, Any] = {}
    if "sqlite" in database_url:
        connect_args["check_same_thread"] = False

    _engine = create_engine(database_url, connect_args=connect_args)
    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
    Base.metadata.create_all(_engine)


def get_engine() -> Engine:
    """Get the current active database engine."""
    global _engine
    if _engine is None:
        init_db()
    assert _engine is not None
    return _engine


def get_session() -> Session:
    """Acquire a new SQLAlchemy database session."""
    global _SessionLocal
    if _SessionLocal is None:
        init_db()
    assert _SessionLocal is not None
    return _SessionLocal()
