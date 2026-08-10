"""Unit tests for DatasetRepository with in-memory SQLite isolation."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from csv_analytics_agent.persistence.hashing import compute_content_hash
from csv_analytics_agent.persistence.models import Base
from csv_analytics_agent.persistence.repository import DatasetRepository
from csv_analytics_agent.profiler.models import DatasetProfile
from csv_analytics_agent.profiler.profiler import DatasetProfiler
from streamlit_app.services.backend import upload_dataset


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide an isolated, transactional in-memory SQLite database session."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Provide a multi-type test DataFrame."""
    return pd.DataFrame(
        {
            "age": [25, 30, 35, None],
            "city": ["Mumbai", "Delhi", "Bengaluru", "Mumbai"],
            "score": [88.5, 92.0, 79.5, 95.0],
        }
    )


@pytest.fixture
def sample_profile(sample_dataframe: pd.DataFrame) -> DatasetProfile:
    """Generate a real DatasetProfile from sample DataFrame."""
    profiler = DatasetProfiler()
    return profiler.profile(sample_dataframe)


def test_repository_create_and_get_by_hash(db_session: Session) -> None:
    repo = DatasetRepository(db_session)
    content_hash = "abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    filename = "sales_q1.csv"

    dataset = repo.create(
        filename=filename,
        content_hash=content_hash,
        row_count=100,
        column_count=5,
    )

    assert dataset.id is not None
    assert dataset.filename == filename
    assert dataset.content_hash == content_hash
    assert dataset.row_count == 100
    assert dataset.column_count == 5
    assert dataset.uploaded_at is not None

    # Retrieve by content_hash
    retrieved = repo.get_by_hash(content_hash)
    assert retrieved is not None
    assert retrieved.id == dataset.id
    assert retrieved.filename == filename
    assert retrieved.row_count == 100

    # Non-existent hash
    assert repo.get_by_hash("nonexistent_hash") is None


def test_repository_cache_and_retrieve_profile(
    db_session: Session, sample_profile: DatasetProfile
) -> None:
    repo = DatasetRepository(db_session)
    content_hash = "def1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

    dataset = repo.create(
        filename="metrics.csv",
        content_hash=content_hash,
        row_count=4,
        column_count=3,
    )

    # Before caching
    assert repo.get_cached_profile(content_hash) is None

    # Cache profile
    repo.cache_profile(dataset.id, sample_profile)

    # Retrieve and validate round-trip
    cached = repo.get_cached_profile(content_hash)
    assert cached is not None
    assert isinstance(cached, DatasetProfile)
    assert cached.summary.row_count == sample_profile.summary.row_count
    assert cached.summary.column_count == sample_profile.summary.column_count
    assert len(cached.columns) == len(sample_profile.columns)
    assert cached.columns[0].name == sample_profile.columns[0].name
    assert cached.missing.total_missing_values == sample_profile.missing.total_missing_values


def test_repository_cache_profile_upsert(
    db_session: Session, sample_profile: DatasetProfile
) -> None:
    repo = DatasetRepository(db_session)
    content_hash = "upsert1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    dataset = repo.create(
        filename="metrics.csv",
        content_hash=content_hash,
        row_count=4,
        column_count=3,
    )

    # Initial cache
    repo.cache_profile(dataset.id, sample_profile)
    assert repo.get_cached_profile(content_hash) is not None

    # Update cache with same or modified profile
    repo.cache_profile(dataset.id, sample_profile)
    cached_after = repo.get_cached_profile(content_hash)
    assert cached_after is not None
    assert cached_after.summary.row_count == sample_profile.summary.row_count


def test_upload_dataset_profile_cache_hit(db_session: Session) -> None:
    raw_csv = b"id,score\n1,10\n2,20\n3,30\n"
    filename = "test_cache_hit.csv"
    expected_hash = compute_content_hash(raw_csv)

    with patch("streamlit_app.services.backend.get_session", return_value=db_session):
        with patch.object(
            DatasetProfiler, "profile", wraps=DatasetProfiler().profile
        ) as spy_profile:
            # First upload: cache miss -> profiler is called
            df1, profile1, hash1 = upload_dataset(raw_csv, filename)
            assert hash1 == expected_hash
            assert len(df1) == 3
            assert profile1.summary.row_count == 3
            assert spy_profile.call_count == 1

            # Second upload with identical bytes: cache hit -> profiler is NOT called again
            df2, profile2, hash2 = upload_dataset(raw_csv, filename)
            assert hash2 == expected_hash
            assert len(df2) == 3
            assert profile2.summary.row_count == 3
            assert spy_profile.call_count == 1  # Still 1, call was skipped!
