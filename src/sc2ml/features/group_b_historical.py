"""Group B — Historical aggregates.

Per-player cumulative statistics computed strictly from *prior* matches:
means, Bayesian-smoothed win rates, variance, and pairwise differences.
"""

import logging

import numpy as np
import pandas as pd

from sc2ml.config import BAYESIAN_C, BAYESIAN_PRIOR_WR
from sc2ml.features.common import bayesian_smooth, expanding_count, expanding_sum

logger = logging.getLogger(__name__)

#: Columns added by this group.
OUTPUT_COLUMNS: list[str] = [
    # Per-player counts
    "p1_total_games_played", "p2_total_games_played",
    # Per-player means
    "p1_hist_mean_apm", "p2_hist_mean_apm",
    "p1_hist_mean_sq", "p2_hist_mean_sq",
    "p1_hist_mean_supply_block", "p2_hist_mean_supply_block",
    "p1_hist_mean_game_length", "p2_hist_mean_game_length",
    # Per-player variance (new)
    "p1_hist_std_apm", "p2_hist_std_apm",
    "p1_hist_std_sq", "p2_hist_std_sq",
    # Win rates
    "p1_hist_winrate_smooth", "p2_hist_winrate_smooth",
    "p1_hist_winrate_as_race_smooth",
    "p1_hist_winrate_vs_race_smooth",
    # Differences
    "diff_hist_apm", "diff_hist_sq",
    "diff_hist_supply_block", "diff_hist_game_length",
    "diff_experience",
]


def _expanding_std(
    df: pd.DataFrame,
    name_col: str,
    stat_col: str,
) -> pd.Series:
    """Expanding standard deviation per player, excluding the current row.

    Returns 0.0 for players with fewer than 2 prior observations.
    """
    std = (
        df.groupby(name_col)[stat_col]
        .expanding()
        .std()
        .droplevel(0)
        .shift(1)
    )
    return std.fillna(0.0)


def compute_historical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add historical aggregate features for both players.

    The DataFrame must already be sorted by ``match_time`` and have a
    ``target`` column.
    """
    logger.info("Computing Group B: historical aggregates + variance...")

    # Global means — used as fallbacks for players with no prior history
    global_mean_apm = df["p1_apm"].mean()
    global_mean_sq = df["p1_sq"].mean()
    global_mean_supply = df["p1_supply_capped_pct"].mean()
    global_mean_loops = df["game_loops"].mean()

    # --- per-player cumulative counts and means ---
    df["p1_total_games_played"] = expanding_count(df, "p1_name")
    df["p2_total_games_played"] = expanding_count(df, "p2_name")

    for prefix in ("p1", "p2"):
        gp = df[f"{prefix}_total_games_played"]

        # Historical means (APM, SQ, supply block, game length)
        hist_apm = expanding_sum(df, f"{prefix}_name", f"{prefix}_apm")
        hist_sq = expanding_sum(df, f"{prefix}_name", f"{prefix}_sq")
        hist_supply = expanding_sum(df, f"{prefix}_name", f"{prefix}_supply_capped_pct")
        hist_loops = expanding_sum(df, f"{prefix}_name", "game_loops")

        df[f"{prefix}_hist_mean_apm"] = np.where(gp > 0, hist_apm / gp, global_mean_apm)
        df[f"{prefix}_hist_mean_sq"] = np.where(gp > 0, hist_sq / gp, global_mean_sq)
        df[f"{prefix}_hist_mean_supply_block"] = np.where(
            gp > 0, hist_supply / gp, global_mean_supply
        )
        df[f"{prefix}_hist_mean_game_length"] = np.where(
            gp > 0, hist_loops / gp, global_mean_loops
        )

        # Historical std (new — variance features)
        df[f"{prefix}_hist_std_apm"] = _expanding_std(df, f"{prefix}_name", f"{prefix}_apm")
        df[f"{prefix}_hist_std_sq"] = _expanding_std(df, f"{prefix}_name", f"{prefix}_sq")

    # --- pairwise differences ---
    df["diff_hist_apm"] = df["p1_hist_mean_apm"] - df["p2_hist_mean_apm"]
    df["diff_hist_sq"] = df["p1_hist_mean_sq"] - df["p2_hist_mean_sq"]
    df["diff_hist_supply_block"] = (
        df["p1_hist_mean_supply_block"] - df["p2_hist_mean_supply_block"]
    )
    df["diff_hist_game_length"] = (
        df["p1_hist_mean_game_length"] - df["p2_hist_mean_game_length"]
    )
    df["diff_experience"] = df["p1_total_games_played"] - df["p2_total_games_played"]

    # --- Bayesian-smoothed win rates ---
    p1_prior_wins = expanding_sum(df, "p1_name", "target")
    df["p1_hist_winrate_smooth"] = bayesian_smooth(
        p1_prior_wins, df["p1_total_games_played"], BAYESIAN_C, BAYESIAN_PRIOR_WR
    )

    df["p2_target_perspective"] = 1 - df["target"]
    p2_prior_wins = (
        df.groupby("p2_name")["p2_target_perspective"].cumsum()
        - df["p2_target_perspective"]
    )
    df["p2_hist_winrate_smooth"] = bayesian_smooth(
        p2_prior_wins, df["p2_total_games_played"], BAYESIAN_C, BAYESIAN_PRIOR_WR
    )

    # Race-specific win rates (as this race, vs opponent's race)
    games_as_race = expanding_count(df, ["p1_name", "p1_race"])
    wins_as_race = expanding_sum(df, ["p1_name", "p1_race"], "target")
    df["p1_hist_winrate_as_race_smooth"] = bayesian_smooth(
        wins_as_race, games_as_race, BAYESIAN_C, BAYESIAN_PRIOR_WR
    )

    games_vs_race = expanding_count(df, ["p1_name", "p2_race"])
    wins_vs_race = expanding_sum(df, ["p1_name", "p2_race"], "target")
    df["p1_hist_winrate_vs_race_smooth"] = bayesian_smooth(
        wins_vs_race, games_vs_race, BAYESIAN_C, BAYESIAN_PRIOR_WR
    )

    return df
