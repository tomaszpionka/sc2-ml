"""Tests for Group B — Historical aggregates."""

import pandas as pd
import pytest

from sc2ml.features.group_b_historical import OUTPUT_COLUMNS, compute_historical_features


@pytest.fixture
def hist_df(sorted_df: pd.DataFrame) -> pd.DataFrame:
    return compute_historical_features(sorted_df)


class TestComputeHistoricalFeatures:
    def test_output_columns_present(self, hist_df: pd.DataFrame) -> None:
        for col in OUTPUT_COLUMNS:
            assert col in hist_df.columns, f"Missing: {col}"

    def test_first_appearance_zero_games(self, hist_df: pd.DataFrame) -> None:
        """Each player's first appearance should show 0 prior games."""
        first = hist_df.groupby("p1_name").head(1)
        assert (first["p1_total_games_played"] == 0).all()

    def test_games_played_never_negative(self, hist_df: pd.DataFrame) -> None:
        assert (hist_df["p1_total_games_played"] >= 0).all()
        assert (hist_df["p2_total_games_played"] >= 0).all()

    def test_winrate_bounds(self, hist_df: pd.DataFrame) -> None:
        for col in ["p1_hist_winrate_smooth", "p2_hist_winrate_smooth"]:
            assert (hist_df[col] >= 0).all(), f"{col} < 0"
            assert (hist_df[col] <= 1).all(), f"{col} > 1"

    def test_race_winrate_bounds(self, hist_df: pd.DataFrame) -> None:
        for col in ["p1_hist_winrate_as_race_smooth", "p1_hist_winrate_vs_race_smooth"]:
            assert (hist_df[col] >= 0).all()
            assert (hist_df[col] <= 1).all()

    def test_std_non_negative(self, hist_df: pd.DataFrame) -> None:
        for col in ["p1_hist_std_apm", "p2_hist_std_apm", "p1_hist_std_sq", "p2_hist_std_sq"]:
            assert (hist_df[col] >= 0).all(), f"{col} has negative values"

    def test_no_nans_in_key_columns(self, hist_df: pd.DataFrame) -> None:
        key = [
            "p1_total_games_played", "p2_total_games_played",
            "p1_hist_mean_apm", "p2_hist_mean_apm",
            "p1_hist_winrate_smooth", "p2_hist_winrate_smooth",
            "diff_experience",
        ]
        for col in key:
            assert hist_df[col].isna().sum() == 0, f"NaN in {col}"
