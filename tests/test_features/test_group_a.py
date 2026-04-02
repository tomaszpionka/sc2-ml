"""Tests for Group A — Elo features."""

import pandas as pd
import pytest

from sc2ml.features.group_a_elo import OUTPUT_COLUMNS, compute_elo_features


@pytest.fixture
def elo_df(sorted_df: pd.DataFrame) -> pd.DataFrame:
    return compute_elo_features(sorted_df)


class TestComputeEloFeatures:
    def test_output_columns_present(self, elo_df: pd.DataFrame) -> None:
        for col in OUTPUT_COLUMNS:
            assert col in elo_df.columns, f"Missing: {col}"

    def test_elo_diff_is_difference(self, elo_df: pd.DataFrame) -> None:
        diff = elo_df["p1_pre_match_elo"] - elo_df["p2_pre_match_elo"]
        pd.testing.assert_series_equal(elo_df["elo_diff"], diff, check_names=False)

    def test_expected_win_prob_bounds(self, elo_df: pd.DataFrame) -> None:
        assert (elo_df["expected_win_prob"] >= 0).all()
        assert (elo_df["expected_win_prob"] <= 1).all()

    def test_first_match_starts_at_1500(self, sorted_df: pd.DataFrame) -> None:
        result = compute_elo_features(sorted_df)
        # All players start at 1500, so the very first match should have 1500 vs 1500
        assert result.iloc[0]["p1_pre_match_elo"] == 1500.0
        assert result.iloc[0]["p2_pre_match_elo"] == 1500.0

    def test_no_nans(self, elo_df: pd.DataFrame) -> None:
        for col in OUTPUT_COLUMNS:
            assert elo_df[col].isna().sum() == 0, f"NaN in {col}"
