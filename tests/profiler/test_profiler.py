import pandas as pd

from csv_analytics_agent.profiler import DatasetProfiler, StatisticsEngine


def test_profile_summary() -> None:
    dataframe = pd.DataFrame(
        {
            "age": [20, 30],
            "city": ["A", "B"],
        }
    )

    profiler = DatasetProfiler()
    profile = profiler.profile(dataframe)

    assert profile.summary.row_count == 2
    assert profile.summary.column_count == 2
    assert profile.missing.total_missing_values == 0
    assert profile.duplicates.duplicate_rows == 0

    assert len(profile.columns) == 2
    assert profile.columns[0].info.name == "age"
    assert profile.columns[0].numeric is not None
    assert profile.columns[0].numeric.mean == 25.0

    assert profile.columns[1].info.name == "city"
    assert profile.columns[1].numeric is None


def test_numeric_statistics_computation() -> None:
    engine = StatisticsEngine()
    series = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])

    stats = engine.compute(series)
    assert stats is not None
    assert stats.mean == 30.0
    assert stats.median == 30.0
    assert stats.minimum == 10.0
    assert stats.maximum == 50.0
    assert stats.q1 == 20.0
    assert stats.q3 == 40.0


def test_non_numeric_statistics_returns_none() -> None:
    engine = StatisticsEngine()
    series = pd.Series(["apple", "banana", "cherry"])

    stats = engine.compute(series)
    assert stats is None
