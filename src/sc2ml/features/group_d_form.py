"""Group D — Form & momentum features.

Win/loss streaks, recency-weighted (EMA) stats, short- and long-term
activity levels, and head-to-head records.  All features use only data
strictly preceding the current match.
"""

import logging

import numpy as np
import pandas as pd

from sc2ml.config import (
    ACTIVITY_WINDOW_LONG,
    ACTIVITY_WINDOW_SHORT,
    BAYESIAN_PRIOR_WR,
    EMA_ALPHA,
    H2H_BAYESIAN_C,
)
from sc2ml.features.common import bayesian_smooth, expanding_count, expanding_sum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Win / loss streaks  (iterative — cannot be vectorised)
# ---------------------------------------------------------------------------

def _compute_streaks(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``p{1,2}_win_streak`` and ``p{1,2}_loss_streak``.

    Uses a single forward pass over the chronologically sorted DataFrame,
    recording each player's streak *before* the current match and then
    updating it.
    """
    win_streak: dict[str, int] = {}
    loss_streak: dict[str, int] = {}

    p1_ws = np.zeros(len(df), dtype=np.int32)
    p1_ls = np.zeros(len(df), dtype=np.int32)
    p2_ws = np.zeros(len(df), dtype=np.int32)
    p2_ls = np.zeros(len(df), dtype=np.int32)

    processed: set[str] = set()

    for idx, row in enumerate(df.itertuples()):
        p1: str = row.p1_name
        p2: str = row.p2_name

        # Record pre-match streaks
        p1_ws[idx] = win_streak.get(p1, 0)
        p1_ls[idx] = loss_streak.get(p1, 0)
        p2_ws[idx] = win_streak.get(p2, 0)
        p2_ls[idx] = loss_streak.get(p2, 0)

        # Update streaks once per unique match
        if row.match_id not in processed:
            p1_won = row.target == 1

            # Player 1
            if p1_won:
                win_streak[p1] = win_streak.get(p1, 0) + 1
                loss_streak[p1] = 0
            else:
                loss_streak[p1] = loss_streak.get(p1, 0) + 1
                win_streak[p1] = 0

            # Player 2
            if not p1_won:
                win_streak[p2] = win_streak.get(p2, 0) + 1
                loss_streak[p2] = 0
            else:
                loss_streak[p2] = loss_streak.get(p2, 0) + 1
                win_streak[p2] = 0

            processed.add(row.match_id)

    df["p1_win_streak"] = p1_ws
    df["p1_loss_streak"] = p1_ls
    df["p2_win_streak"] = p2_ws
    df["p2_loss_streak"] = p2_ls
    return df


# ---------------------------------------------------------------------------
# EMA features
# ---------------------------------------------------------------------------

def _compute_ema(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """Add EMA of APM, SQ, and win/loss for both players.

    The EMA is computed per player in chronological order and shifted by 1
    so that the current match is excluded.
    """
    for prefix in ("p1", "p2"):
        name_col = f"{prefix}_name"

        for stat, raw_col in [
            ("apm", f"{prefix}_apm"),
            ("sq", f"{prefix}_sq"),
        ]:
            ema = (
                df.groupby(name_col)[raw_col]
                .transform(lambda s: s.ewm(alpha=alpha, adjust=False).mean().shift(1))
            )
            df[f"{prefix}_ema_{stat}"] = ema.fillna(df[raw_col].mean())

        # EMA of win/loss (binary)
        if prefix == "p1":
            win_col = "target"
        else:
            if "p2_win_flag" not in df.columns:
                df["p2_win_flag"] = 1 - df["target"]
            win_col = "p2_win_flag"

        ema_wr = (
            df.groupby(name_col)[win_col]
            .transform(lambda s: s.ewm(alpha=alpha, adjust=False).mean().shift(1))
        )
        df[f"{prefix}_ema_winrate"] = ema_wr.fillna(0.5)

    return df


# ---------------------------------------------------------------------------
# Activity windows
# ---------------------------------------------------------------------------

def _compute_activity(df: pd.DataFrame) -> pd.DataFrame:
    """Add short- and long-term match activity counts for both players.

    For each match, count how many games the player had in the preceding
    N days (excluding the current match).
    """
    for prefix in ("p1", "p2"):
        name_col = f"{prefix}_name"

        # Create a temporary frame with a dummy column for counting
        tmp = df[[name_col, "match_time"]].copy()
        tmp["_one"] = 1
        tmp = tmp.set_index("match_time")

        for window_days, suffix in [
            (ACTIVITY_WINDOW_SHORT, "7d"),
            (ACTIVITY_WINDOW_LONG, "30d"),
        ]:
            col_name = f"{prefix}_matches_last_{suffix}"
            counts = (
                tmp.groupby(name_col)
                .rolling(f"{window_days}D")["_one"]
                .sum()
                .droplevel(0)
            )
            # Subtract 1 because rolling includes the current row
            counts = (counts - 1).clip(lower=0)
            df[col_name] = counts.values

    return df


# ---------------------------------------------------------------------------
# Head-to-head record
# ---------------------------------------------------------------------------

def _compute_h2h(df: pd.DataFrame) -> pd.DataFrame:
    """Add head-to-head cumulative wins and Bayesian-smoothed H2H win rate.

    Uses a canonical pair key ``(min(p1, p2), max(p1, p2))`` so that both
    perspectives of the same matchup share the same running counter.
    """
    df["_h2h_pair"] = df.apply(
        lambda r: (min(r["p1_name"], r["p2_name"]), max(r["p1_name"], r["p2_name"])),
        axis=1,
    )

    h2h_total = expanding_count(df, "_h2h_pair")
    h2h_p1_wins = expanding_sum(df, "_h2h_pair", "target")

    df["h2h_p1_wins"] = h2h_p1_wins
    df["h2h_p2_wins"] = h2h_total - h2h_p1_wins
    df["h2h_p1_winrate_smooth"] = bayesian_smooth(
        h2h_p1_wins, h2h_total, H2H_BAYESIAN_C, BAYESIAN_PRIOR_WR
    )

    return df


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compute_form_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add form & momentum features for both players.

    The DataFrame must already be sorted by ``match_time`` and have a
    ``target`` column.
    """
    logger.info("Computing Group D: form & momentum features...")

    df = _compute_streaks(df)
    df = _compute_ema(df, alpha=EMA_ALPHA)
    df = _compute_activity(df)
    df = _compute_h2h(df)

    return df
