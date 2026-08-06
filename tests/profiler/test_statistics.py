import pandas as pd

from csv_analytics_agent.profiler.statistics import (
    calculate_categorical_statistics,
    calculate_datetime_statistics,
    calculate_numeric_statistics,
)


def test_calculate_numeric_statistics_happy_path() -> None:
    series = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    stats = calculate_numeric_statistics(series)

    assert stats is not None
    assert stats.mean == 30.0
    assert stats.median == 30.0
    assert stats.min == 10.0
    assert stats.max == 50.0
    assert stats.q1 == 20.0
    assert stats.q3 == 40.0
    assert stats.std is not None
    assert stats.variance is not None


def test_calculate_numeric_statistics_with_nans() -> None:
    series = pd.Series([10.0, None, 30.0, None, 50.0])
    stats = calculate_numeric_statistics(series)

    assert stats is not None
    assert stats.mean == 30.0
    assert stats.min == 10.0
    assert stats.max == 50.0


def test_calculate_numeric_statistics_single_element() -> None:
    series = pd.Series([42.0])
    stats = calculate_numeric_statistics(series)

    assert stats is not None
    assert stats.mean == 42.0
    assert stats.std == 0.0
    assert stats.variance == 0.0


def test_calculate_numeric_statistics_empty_or_non_numeric() -> None:
    empty_series = pd.Series([], dtype="float64")
    str_series = pd.Series(["a", "b", "c"])
    bool_series = pd.Series([True, False])

    assert calculate_numeric_statistics(empty_series) is None
    assert calculate_numeric_statistics(str_series) is None
    assert calculate_numeric_statistics(bool_series) is None


def test_calculate_categorical_statistics_happy_path() -> None:
    series = pd.Series(["Ahmedabad", "Surat", "Ahmedabad", "Rajkot"])
    stats = calculate_categorical_statistics(series)

    assert stats is not None
    assert stats.mode == "Ahmedabad"
    assert stats.frequency == 2
    assert stats.category_count == 3


def test_calculate_categorical_statistics_empty_and_numeric() -> None:
    empty_series = pd.Series([], dtype="object")
    num_series = pd.Series([1, 2, 3])

    empty_stats = calculate_categorical_statistics(empty_series)
    assert empty_stats is not None
    assert empty_stats.mode is None
    assert empty_stats.frequency is None
    assert empty_stats.category_count == 0

    assert calculate_categorical_statistics(num_series) is None


def test_calculate_datetime_statistics_happy_path() -> None:
    series = pd.to_datetime(pd.Series(["2026-01-01T00:00:00", "2026-12-31T23:59:59"]))
    stats = calculate_datetime_statistics(series)

    assert stats is not None
    assert stats.earliest == "2026-01-01T00:00:00"
    assert stats.latest == "2026-12-31T23:59:59"


def test_calculate_datetime_statistics_non_datetime_and_empty() -> None:
    num_series = pd.Series([1, 2, 3])
    empty_dt_series = pd.Series([], dtype="datetime64[ns]")

    assert calculate_datetime_statistics(num_series) is None
    assert calculate_datetime_statistics(empty_dt_series) is None
