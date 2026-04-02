"""Group C — Matchup & map features.

Race encoding, spawn distance, map area, and historical map-race interaction
win rates.
"""

import logging

import numpy as np
import pandas as pd

from sc2ml.config import BAYESIAN_C, BAYESIAN_PRIOR_WR
from sc2ml.features.common import bayesian_smooth, expanding_count, expanding_sum

logger = logging.getLogger(__name__)


def compute_matchup_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add matchup and map features.

    The DataFrame must already be sorted by ``match_time`` and have a
    ``target`` column.

    Adds:
      - ``spawn_distance``, ``map_area`` — pre-match map geometry
      - ``p{1,2}_race_*`` — one-hot race encoding
      - ``p{1,2}_hist_winrate_map_race_smooth`` — map x race interaction
    """
    logger.info("Computing Group C: matchup & map features...")

    # --- map geometry (known before the game starts) ---
    df["spawn_distance"] = np.sqrt(
        (df["p1_startLocX"] - df["p2_startLocX"]) ** 2
        + (df["p1_startLocY"] - df["p2_startLocY"]) ** 2
    )
    df["map_area"] = df["map_size_x"] * df["map_size_y"]

    # --- map x race interaction winrate (new) ---
    for prefix in ("p1", "p2"):
        target_col = "target" if prefix == "p1" else "p2_target_perspective"
        # p2_target_perspective is created by group_b; if missing, compute it
        if target_col not in df.columns:
            if prefix == "p2":
                df["p2_target_perspective"] = 1 - df["target"]

        group_cols = [f"{prefix}_name", f"{prefix}_race", "map_name"]
        games = expanding_count(df, group_cols)
        wins = expanding_sum(df, group_cols, target_col)
        df[f"{prefix}_hist_winrate_map_race_smooth"] = bayesian_smooth(
            wins, games, BAYESIAN_C, BAYESIAN_PRIOR_WR
        )

    # --- one-hot race encoding ---
    df = pd.get_dummies(df, columns=["p1_race", "p2_race"], drop_first=False)

    # Cast bool dummies to int for model compatibility
    for col in df.select_dtypes(include=["bool"]).columns:
        df[col] = df[col].astype(int)

    return df
