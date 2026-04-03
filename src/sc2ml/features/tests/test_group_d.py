"""Tests for Group D — Form & momentum features."""

import pandas as pd
import pytest

from sc2ml.features.group_d_form import compute_form_features


@pytest.fixture
def form_df(sorted_df: pd.DataFrame) -> pd.DataFrame:
    return compute_form_features(sorted_df)


class TestStreaks:
    def test_streaks_non_negative(self, form_df: pd.DataFrame) -> None:
        for col in ["p1_win_streak", "p1_loss_streak", "p2_win_streak", "p2_loss_streak"]:
            assert (form_df[col] >= 0).all(), f"{col} has negative values"

    def test_first_match_zero_streak(self, form_df: pd.DataFrame) -> None:
        """Very first row should have 0 streaks (Player_0's first game ever)."""
        # Player_0 is forced to be p1 in match_0000 (first match overall)
        row0 = form_df.iloc[0]
        assert row0["p1_win_streak"] == 0
        assert row0["p1_loss_streak"] == 0

    def test_player_0_win_streak(self, form_df: pd.DataFrame) -> None:
        """Player_0 wins the first 5 matches as p1 — check streak builds."""
        p0_rows = form_df[form_df["p1_name"] == "Player_0"].head(6)
        # Match 0: streak=0 (first game)
        assert p0_rows.iloc[0]["p1_win_streak"] == 0
        # Match 1: streak=1 (won previous)
        assert p0_rows.iloc[1]["p1_win_streak"] == 1
        # Match 4: streak=4
        assert p0_rows.iloc[4]["p1_win_streak"] == 4


class TestEma:
    def test_ema_columns_present(self, form_df: pd.DataFrame) -> None:
        for col in ["p1_ema_apm", "p1_ema_sq", "p1_ema_winrate",
                     "p2_ema_apm", "p2_ema_sq", "p2_ema_winrate"]:
            assert col in form_df.columns

    def test_ema_winrate_bounds(self, form_df: pd.DataFrame) -> None:
        for col in ["p1_ema_winrate", "p2_ema_winrate"]:
            assert (form_df[col] >= 0).all()
            assert (form_df[col] <= 1).all()

    def test_no_nans(self, form_df: pd.DataFrame) -> None:
        for col in ["p1_ema_apm", "p2_ema_apm"]:
            assert form_df[col].isna().sum() == 0


class TestActivity:
    def test_activity_non_negative(self, form_df: pd.DataFrame) -> None:
        for col in ["p1_matches_last_7d", "p1_matches_last_30d",
                     "p2_matches_last_7d", "p2_matches_last_30d"]:
            assert (form_df[col] >= 0).all()

    def test_short_window_leq_long_window(self, form_df: pd.DataFrame) -> None:
        assert (form_df["p1_matches_last_7d"] <= form_df["p1_matches_last_30d"]).all()


class TestH2H:
    def test_h2h_columns_present(self, form_df: pd.DataFrame) -> None:
        for col in ["h2h_p1_wins", "h2h_p2_wins", "h2h_p1_winrate_smooth"]:
            assert col in form_df.columns

    def test_h2h_non_negative(self, form_df: pd.DataFrame) -> None:
        assert (form_df["h2h_p1_wins"] >= 0).all()
        assert (form_df["h2h_p2_wins"] >= 0).all()

    def test_h2h_winrate_bounds(self, form_df: pd.DataFrame) -> None:
        assert (form_df["h2h_p1_winrate_smooth"] >= 0).all()
        assert (form_df["h2h_p1_winrate_smooth"] <= 1).all()

    def test_first_meeting_is_prior(self, form_df: pd.DataFrame) -> None:
        """First meeting of any pair should have h2h wins = 0."""
        assert form_df["h2h_p1_wins"].min() == 0
