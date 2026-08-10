"""SQLAlchemy persistence layer for application metadata and profile caching."""

from __future__ import annotations

from csv_analytics_agent.persistence.db import get_engine, get_session, init_db
from csv_analytics_agent.persistence.hashing import compute_content_hash
from csv_analytics_agent.persistence.models import Base, Dataset, DatasetProfileCache
from csv_analytics_agent.persistence.repository import DatasetRepository

__all__ = [
    "Base",
    "Dataset",
    "DatasetProfileCache",
    "DatasetRepository",
    "compute_content_hash",
    "get_engine",
    "get_session",
    "init_db",
]
