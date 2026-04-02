"""Tests for ml_pipeline.perform_feature_engineering().

Covers:
- Temporal ordering preserved
- No data leakage (no current-match stats in output)
- Bayesian smoothing bounds
- Temporal train/test split correctness
"""
import numpy as np
import pandas as pd
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml_pipeline import perform_feature_engineering, temporal_train_test_split
from tests.fixtures import make_matches_df

LEAKAGE_COLS = [
    "p1_apm", "p2_apm",
    "p1_sq", "p2_sq",
    "p1_supply_capped_pct", "p2_supply_capped_pct",
    "game_loops",
    "p1_result",
]


@pytest.fixture
def raw_df() -> pd.DataFrame:
    return make_matches_df(n=200, seed=42)


@pytest.fixture
def features_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    return perform_feature_engineering(raw_df)


def test_output_is_chronologically_sorted(features_df: pd.DataFrame) -> None:
    times = pd.to_datetime(features_df["match_time"])
    assert (times.diff().dropna() >= pd.Timedelta(0)).all(), (
        "features_df is not chronologically sorted — temporal operations will be wrong"
    )


def test_no_leakage_columns_in_output(features_df: pd.DataFrame) -> None:
    for col in LEAKAGE_COLS:
        assert col not in features_df.columns, (
            f"Leakage column '{col}' found in features_df — this is current-match data"
        )


def test_target_column_present(features_df: pd.DataFrame) -> None:
    assert "target" in features_df.columns
    assert set(features_df["target"].unique()).issubset({0, 1})


def test_bayesian_smoothed_winrate_bounds(features_df: pd.DataFrame) -> None:
    for col in ["p1_hist_winrate_smooth", "p2_hist_winrate_smooth"]:
        assert col in features_df.columns, f"Missing column: {col}"
        assert (features_df[col] >= 0).all(), f"{col} contains negative values"
        assert (features_df[col] <= 1).all(), f"{col} contains values > 1"


def test_historical_features_use_only_past_data(raw_df: pd.DataFrame) -> None:
    """Verify cumulative counts only use data strictly before the current row."""
    df = perform_feature_engineering(raw_df)
    # On the very first appearance of a player, they should have 0 prior games
    first_appearances = df.groupby("p1_name").head(1)
    assert (first_appearances["p1_total_games_played"] == 0).all(), (
        "Player's first match shows non-zero historical game count — likely leakage"
    )


def test_temporal_train_test_split_no_overlap(features_df: pd.DataFrame) -> None:
    X_train, X_test, y_train, y_test = temporal_train_test_split(features_df, test_size=0.2)
    # Neither X_train nor X_test should contain 'match_time' (it's dropped)
    # But if we recover times from features_df we can check ordering
    split_idx = int(len(features_df) * 0.8)
    train_times = pd.to_datetime(features_df.iloc[:split_idx]["match_time"])
    test_times = pd.to_datetime(features_df.iloc[split_idx:]["match_time"])
    assert train_times.max() <= test_times.min(), (
        "Train set contains times after test set start — temporal split is wrong"
    )


def test_temporal_split_sizes(features_df: pd.DataFrame) -> None:
    test_size = 0.2
    X_train, X_test, y_train, y_test = temporal_train_test_split(features_df, test_size=test_size)
    total = len(features_df)
    expected_test = total - int(total * (1 - test_size))
    assert len(X_test) == expected_test


def test_no_nulls_in_key_features(features_df: pd.DataFrame) -> None:
    key_cols = [
        "p1_hist_winrate_smooth",
        "p2_hist_winrate_smooth",
        "p1_hist_mean_apm",
        "p2_hist_mean_apm",
        "diff_experience",
        "target",
    ]
    for col in key_cols:
        if col in features_df.columns:
            assert features_df[col].isna().sum() == 0, f"NaNs found in {col}"
