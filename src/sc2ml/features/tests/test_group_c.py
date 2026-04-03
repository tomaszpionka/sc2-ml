"""Tests for Group C — Matchup & map features."""

import pandas as pd
import pytest

from sc2ml.features.group_b_historical import compute_historical_features
from sc2ml.features.group_c_matchup import compute_matchup_features


@pytest.fixture
def matchup_df(sorted_df: pd.DataFrame) -> pd.DataFrame:
    # Group C needs p2_target_perspective from Group B
    df = compute_historical_features(sorted_df)
    return compute_matchup_features(df)


class TestComputeMatchupFeatures:
    def test_spawn_distance_positive(self, matchup_df: pd.DataFrame) -> None:
        assert (matchup_df["spawn_distance"] >= 0).all()

    def test_map_area_positive(self, matchup_df: pd.DataFrame) -> None:
        assert (matchup_df["map_area"] > 0).all()

    def test_race_one_hot_columns_present(self, matchup_df: pd.DataFrame) -> None:
        for race in ["Terran", "Zerg", "Protoss"]:
            assert f"p1_race_{race}" in matchup_df.columns
            assert f"p2_race_{race}" in matchup_df.columns

    def test_race_one_hot_values(self, matchup_df: pd.DataFrame) -> None:
        for col in matchup_df.filter(regex="^p[12]_race_").columns:
            assert set(matchup_df[col].unique()).issubset({0, 1})

    def test_map_race_winrate_bounds(self, matchup_df: pd.DataFrame) -> None:
        for col in ["p1_hist_winrate_map_race_smooth", "p2_hist_winrate_map_race_smooth"]:
            assert (matchup_df[col] >= 0).all()
            assert (matchup_df[col] <= 1).all()

    def test_no_nans(self, matchup_df: pd.DataFrame) -> None:
        for col in ["spawn_distance", "map_area",
                     "p1_hist_winrate_map_race_smooth", "p2_hist_winrate_map_race_smooth"]:
            assert matchup_df[col].isna().sum() == 0, f"NaN in {col}"
