from pathlib import Path

import pandas as pd
import pytest

from csv_analytics_agent.data.loader import CSVLoader
from csv_analytics_agent.exceptions import (
    EmptyCSVError,
    FileValidationError,
    InvalidFileExtensionError,
)


def test_csv_loader_valid_file(tmp_path: Path) -> None:
    csv_file = tmp_path / "valid.csv"
    csv_file.write_text("name,age\nAlice,30\nBob,25")

    loader = CSVLoader()
    df = loader.load(csv_file)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ["name", "age"]


def test_csv_loader_empty_file(tmp_path: Path) -> None:
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("")

    loader = CSVLoader()
    with pytest.raises(EmptyCSVError):
        loader.load(csv_file)


def test_csv_loader_invalid_extension(tmp_path: Path) -> None:
    txt_file = tmp_path / "data.txt"
    txt_file.write_text("a,b,c")

    loader = CSVLoader()
    with pytest.raises(InvalidFileExtensionError):
        loader.load(txt_file)


def test_csv_loader_non_existent_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.csv"

    loader = CSVLoader()
    with pytest.raises(FileValidationError):
        loader.load(missing)
