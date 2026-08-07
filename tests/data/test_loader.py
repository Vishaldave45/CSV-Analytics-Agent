from pathlib import Path

import pandas as pd
import pytest

from csv_analytics_agent.data.loader import CSVLoader
from csv_analytics_agent.exceptions import (
    CSVEncodingError,
    CSVParsingError,
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


def test_csv_loader_header_only_empty_data(tmp_path: Path) -> None:
    csv_file = tmp_path / "header_only.csv"
    csv_file.write_text("name,age\n")

    loader = CSVLoader()
    with pytest.raises(EmptyCSVError):
        loader.load(csv_file)


def test_csv_loader_malformed_csv(tmp_path: Path) -> None:
    csv_file = tmp_path / "malformed.csv"
    # Row 1 has 2 fields, Row 2 has 3 fields to trigger pandas ParserError
    csv_file.write_text("col1,col2\n1,2\n3,4,5\n", encoding="utf-8")

    loader = CSVLoader()
    with pytest.raises(CSVParsingError):
        loader.load(csv_file)


def test_csv_loader_invalid_encoding(tmp_path: Path) -> None:
    csv_file = tmp_path / "bad_encoding.csv"
    # Write invalid UTF-8 byte sequence
    csv_file.write_bytes(b"name,age\n\x80\xff\xfe,30\n")

    loader = CSVLoader()
    with pytest.raises(CSVEncodingError):
        loader.load(csv_file)


def test_csv_loader_invalid_extension(tmp_path: Path) -> None:
    txt_file = tmp_path / "data.txt"
    txt_file.write_text("a,b,c")

    loader = CSVLoader()
    with pytest.raises(InvalidFileExtensionError):
        loader.load(txt_file)


def test_csv_loader_unexpected_exception(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_file = tmp_path / "valid.csv"
    csv_file.write_text("a,b\n1,2")

    def mock_read_csv(*args: object, **kwargs: object) -> None:
        raise RuntimeError("Unexpected OS error")

    monkeypatch.setattr(pd, "read_csv", mock_read_csv)

    loader = CSVLoader()
    with pytest.raises(CSVParsingError, match="Unexpected error loading CSV file"):
        loader.load(csv_file)


def test_csv_loader_non_existent_file(tmp_path: Path) -> None:

    missing = tmp_path / "missing.csv"

    loader = CSVLoader()
    with pytest.raises(FileValidationError):
        loader.load(missing)
