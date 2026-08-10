"""Integration tests for Alembic schema migrations."""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command


def test_alembic_migration_lifecycle(tmp_path: Path) -> None:
    """Verify that Alembic migrations upgrade to head and downgrade to base cleanly."""
    db_path = tmp_path / "migration_test.db"
    db_url = f"sqlite:///{db_path}"

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # 1. Upgrade schema to head
    command.upgrade(alembic_cfg, "head")

    # Verify table creation and column definitions
    engine = create_engine(db_url)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    assert "datasets" in table_names
    assert "dataset_profiles" in table_names
    assert "alembic_version" in table_names

    dataset_cols = {col["name"] for col in inspector.get_columns("datasets")}
    expected_dataset_cols = {
        "id",
        "filename",
        "content_hash",
        "row_count",
        "column_count",
        "uploaded_at",
    }
    assert expected_dataset_cols.issubset(dataset_cols)

    profile_cols = {col["name"] for col in inspector.get_columns("dataset_profiles")}
    expected_profile_cols = {"id", "dataset_id", "profile_json", "computed_at"}
    assert expected_profile_cols.issubset(profile_cols)

    # 2. Downgrade schema to base
    command.downgrade(alembic_cfg, "base")
    tables_after_downgrade = set(inspect(engine).get_table_names())
    assert "datasets" not in tables_after_downgrade
    assert "dataset_profiles" not in tables_after_downgrade

    # 3. Re-upgrade cleanly
    command.upgrade(alembic_cfg, "head")
    tables_after_reupgrade = set(inspect(engine).get_table_names())
    assert "datasets" in tables_after_reupgrade
    assert "dataset_profiles" in tables_after_reupgrade
