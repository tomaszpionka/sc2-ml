"""Tests for data structure and schema validation.

These tests do NOT require a live DuckDB connection — they validate
in-memory DataFrames produced by the pipeline stages.

Covers:
- Output schema of perform_feature_engineering()
- Row count sanity (matches_flat ~2x raw, feature df same as input)
- Target is binary
- match_time is parseable as datetime
- ELO columns present after elo stage
"""
import pandas as pd
import pytest

from sc2ml.features import perform_feature_engineering, temporal_train_test_split
from tests.helpers import make_matches_df

REQUIRED_OUTPUT_COLS = [
    "match_id",
    "match_time",
    "p1_name",
    "p2_name",
    "target",
    "p1_total_games_played",
    "p2_total_games_played",
    "p1_hist_winrate_smooth",
    "p2_hist_winrate_smooth",
    "p1_hist_mean_apm",
    "p2_hist_mean_apm",
    "diff_experience",
    "elo_diff",
    "expected_win_prob",
]


@pytest.fixture(scope="module")
def features_df() -> pd.DataFrame:
    raw = make_matches_df(n=200, seed=42)
    return perform_feature_engineering(raw)


def test_required_columns_present(features_df: pd.DataFrame) -> None:
    """
    Scenario: Feature engineering output contains all required columns.
    Preconditions: 200-row synthetic DataFrame through perform_feature_engineering().
    Assertions: Every column in REQUIRED_OUTPUT_COLS exists in the output.
    """
    missing = [c for c in REQUIRED_OUTPUT_COLS if c not in features_df.columns]
    assert not missing, f"Missing required columns: {missing}"


def test_row_count_preserved(features_df: pd.DataFrame) -> None:
    """
    Scenario: Feature engineering preserves row count (no rows added or dropped).
    Preconditions: 200-row input, same seed as fixture.
    Assertions: Output length equals input length.
    """
    raw = make_matches_df(n=200, seed=42)
    assert len(features_df) == len(raw), (
        "perform_feature_engineering() should not change the row count"
    )


def test_target_is_binary(features_df: pd.DataFrame) -> None:
    """
    Scenario: Target column contains only valid binary labels.
    Preconditions: Feature-engineered DataFrame.
    Assertions: target values are a subset of {0, 1}.
    """
    assert set(features_df["target"].unique()).issubset({0, 1}), (
        "target column contains values other than 0 and 1"
    )


def test_match_time_is_datetime(features_df: pd.DataFrame) -> None:
    """
    Scenario: match_time column is parseable as datetime.
    Preconditions: Feature-engineered DataFrame.
    Assertions: pd.to_datetime succeeds without exception.
    """
    try:
        pd.to_datetime(features_df["match_time"])
    except Exception as e:
        pytest.fail(f"match_time cannot be parsed as datetime: {e}")


def test_no_duplicate_match_ids(features_df: pd.DataFrame) -> None:
    """
    Scenario: No duplicate match_ids in the output.
    Preconditions: Synthetic fixture with unique match_ids per row.
    Assertions: No match_id appears more than once.
    """
    # In matches_flat there are 2 rows per match (p1/p2 and p2/p1 perspective).
    # But our synthetic fixture generates unique match_ids, so duplicates = error here.
    counts = features_df["match_id"].value_counts()
    dupes = counts[counts > 1]
    assert dupes.empty, f"Duplicate match_ids found: {dupes.index.tolist()[:5]}"


def test_elo_columns_present(features_df: pd.DataFrame) -> None:
    """
    Scenario: Elo-derived columns exist after feature engineering.
    Preconditions: Feature-engineered DataFrame.
    Assertions: elo_diff and expected_win_prob columns present.
    """
    assert "elo_diff" in features_df.columns, "elo_diff column missing"
    assert "expected_win_prob" in features_df.columns, "expected_win_prob column missing"


def test_player_names_not_null(features_df: pd.DataFrame) -> None:
    """
    Scenario: Player name columns have no null values.
    Preconditions: Feature-engineered DataFrame.
    Assertions: Zero NaN values in p1_name and p2_name.
    """
    assert features_df["p1_name"].isna().sum() == 0, "p1_name has NaN values"
    assert features_df["p2_name"].isna().sum() == 0, "p2_name has NaN values"


def test_games_played_non_negative(features_df: pd.DataFrame) -> None:
    """
    Scenario: Games-played counters are never negative.
    Preconditions: Feature-engineered DataFrame.
    Assertions: p1_total_games_played >= 0 and p2_total_games_played >= 0 for all rows.
    """
    assert (features_df["p1_total_games_played"] >= 0).all(), (
        "p1_total_games_played has negative values"
    )
    assert (features_df["p2_total_games_played"] >= 0).all(), (
        "p2_total_games_played has negative values"
    )


def test_temporal_split_produces_nonempty_sets(features_df: pd.DataFrame) -> None:
    """
    Scenario: Temporal train/test split yields non-empty sets.
    Preconditions: Feature-engineered DataFrame, test_size=0.2.
    Assertions: Both train and test sets have rows; label counts match feature counts.
    """
    X_train, X_test, y_train, y_test = temporal_train_test_split(features_df, test_size=0.2)
    assert len(X_train) > 0, "Train set is empty"
    assert len(X_test) > 0, "Test set is empty"
    assert len(y_train) == len(X_train)
    assert len(y_test) == len(X_test)


def test_winrate_smooth_within_bounds(features_df: pd.DataFrame) -> None:
    """
    Scenario: Smoothed win-rate columns are bounded in [0, 1].
    Preconditions: Feature-engineered DataFrame.
    Assertions: All non-NaN values of p1/p2_hist_winrate_smooth are in [0, 1].
    """
    for col in ["p1_hist_winrate_smooth", "p2_hist_winrate_smooth"]:
        vals = features_df[col].dropna()
        assert (vals >= 0).all() and (vals <= 1).all(), (
            f"{col} has values outside [0, 1]: min={vals.min():.4f}, max={vals.max():.4f}"
        )
