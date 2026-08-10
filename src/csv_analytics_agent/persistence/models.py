"""SQLAlchemy ORM models for dataset registry and profile cache."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    """Base declarative class for application metadata models."""

    pass


class Dataset(Base):
    """Dataset registry entity tracking uploaded CSV metadata and content hash."""

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    profile_cache: Mapped[DatasetProfileCache | None] = relationship(
        "DatasetProfileCache",
        back_populates="dataset",
        uselist=False,
        cascade="all, delete-orphan",
    )


class DatasetProfileCache(Base):
    """Cached DatasetProfile (Pydantic model serialized as JSON) keyed to a Dataset."""

    __tablename__ = "dataset_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("datasets.id"), unique=True, nullable=False
    )
    profile_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="profile_cache")
