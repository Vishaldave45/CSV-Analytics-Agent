"""Repository for Dataset and DatasetProfileCache CRUD operations."""

from __future__ import annotations

from sqlalchemy.orm import Session

from csv_analytics_agent.persistence.models import Dataset, DatasetProfileCache
from csv_analytics_agent.profiler.models import DatasetProfile


class DatasetRepository:
    """Repository handling database persistence and profile cache retrieval."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_hash(self, content_hash: str) -> Dataset | None:
        """Fetch Dataset entity by its unique content hash.

        Args:
            content_hash: SHA-256 hash string.

        Returns:
            Dataset model instance if found, otherwise None.
        """
        return self._session.query(Dataset).filter_by(content_hash=content_hash).first()

    def create(
        self,
        filename: str,
        content_hash: str,
        row_count: int,
        column_count: int,
    ) -> Dataset:
        """Create and persist a new Dataset record.

        Args:
            filename: Original uploaded file name.
            content_hash: SHA-256 content hash of file bytes.
            row_count: Number of rows in dataset.
            column_count: Number of columns in dataset.

        Returns:
            Newly created and persisted Dataset instance.
        """
        dataset = Dataset(
            filename=filename,
            content_hash=content_hash,
            row_count=row_count,
            column_count=column_count,
        )
        self._session.add(dataset)
        self._session.commit()
        self._session.refresh(dataset)
        return dataset

    def get_cached_profile(self, content_hash: str) -> DatasetProfile | None:
        """Retrieve and deserialize cached DatasetProfile by dataset content hash.

        Args:
            content_hash: SHA-256 hash string.

        Returns:
            Deserialized DatasetProfile Pydantic instance if cached, else None.
        """
        cache = (
            self._session.query(DatasetProfileCache)
            .join(Dataset, DatasetProfileCache.dataset_id == Dataset.id)
            .filter(Dataset.content_hash == content_hash)
            .first()
        )
        if cache is None:
            return None
        return DatasetProfile.model_validate(cache.profile_json)

    def cache_profile(self, dataset_id: int, profile: DatasetProfile) -> None:
        """Store or update the cached profile for a dataset.

        Args:
            dataset_id: Primary key of the Dataset entity.
            profile: DatasetProfile Pydantic model instance.
        """
        cache = self._session.query(DatasetProfileCache).filter_by(dataset_id=dataset_id).first()
        if cache is None:
            cache = DatasetProfileCache(
                dataset_id=dataset_id,
                profile_json=profile.model_dump(mode="json"),
            )
            self._session.add(cache)
        else:
            cache.profile_json = profile.model_dump(mode="json")
        self._session.commit()
