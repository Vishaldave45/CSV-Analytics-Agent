import pandas as pd

from csv_analytics_agent.profiler.profiler import DatasetProfiler


def test_dataset_profiler_multi_type_dataframe() -> None:
    df = pd.DataFrame(
        {
            "age": [20, 30, 30, None],
            "city": ["Ahmedabad", "Surat", "Ahmedabad", "Rajkot"],
            "joined_date": pd.to_datetime(["2026-01-01", "2026-06-01", "2026-06-01", "2026-12-31"]),
        }
    )

    profiler = DatasetProfiler()
    profile = profiler.profile(df)

    # Dataset Summary assertions
    assert profile.summary.row_count == 4
    assert profile.summary.column_count == 3
    assert profile.summary.memory_usage_bytes > 0

    # Missing & Duplicates assertions
    assert profile.missing.total_missing_values == 1
    assert profile.missing.columns_with_missing == 1
    assert profile.duplicates.duplicate_rows == 0

    # Column Profiles assertions
    assert len(profile.columns) == 3

    # Age (numeric)
    age_col = profile.columns[0]
    assert age_col.name == "age"
    assert age_col.missing_count == 1
    assert age_col.missing_percentage == 25.0
    assert age_col.numeric is not None
    assert age_col.numeric.mean == 26.666666666666668
    assert age_col.categorical is None

    # City (categorical)
    city_col = profile.columns[1]
    assert city_col.name == "city"
    assert city_col.missing_count == 0
    assert city_col.categorical is not None
    assert city_col.categorical.mode == "Ahmedabad"
    assert city_col.categorical.frequency == 2
    assert city_col.numeric is None

    # Joined Date (datetime)
    date_col = profile.columns[2]
    assert date_col.name == "joined_date"
    assert date_col.datetime is not None
    assert date_col.datetime.earliest == "2026-01-01T00:00:00"
    assert date_col.datetime.latest == "2026-12-31T00:00:00"


def test_dataset_profiler_duplicate_rows() -> None:
    df = pd.DataFrame(
        {
            "id": [1, 1, 2],
            "val": ["A", "A", "B"],
        }
    )
    profiler = DatasetProfiler()
    profile = profiler.profile(df)

    assert profile.duplicates.duplicate_rows == 1


def test_dataset_profiler_empty_dataframe() -> None:
    df = pd.DataFrame()
    profiler = DatasetProfiler()
    profile = profiler.profile(df)

    assert profile.summary.row_count == 0
    assert profile.summary.column_count == 0
    assert profile.missing.total_missing_values == 0
    assert profile.missing.columns_with_missing == 0
    assert profile.duplicates.duplicate_rows == 0
    assert len(profile.columns) == 0
