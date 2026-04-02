"""Shared primitives for feature engineering.

All expanding-window helpers follow the same contract: they operate on a
DataFrame that is already sorted by ``match_time`` and return a Series
aligned with the DataFrame index.  The "current row" is always **excluded**
from the aggregate so that features are strictly backward-looking.
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DataFrame housekeeping
# ---------------------------------------------------------------------------

def ensure_sorted(df: pd.DataFrame) -> pd.DataFrame:
    """Sort by match_time and reset the index.  Idempotent."""
    return df.sort_values("match_time").reset_index(drop=True)


def compute_target(df: pd.DataFrame) -> pd.DataFrame:
    """Add a binary ``target`` column (1 = p1 wins).  No-op if already present."""
    if "target" not in df.columns:
        df = df.copy()
        df["target"] = (df["p1_result"] == "Win").astype(int)
    return df


# ---------------------------------------------------------------------------
# Expanding-window aggregation helpers
# ---------------------------------------------------------------------------

def expanding_sum(
    df: pd.DataFrame,
    groupby: str | list[str],
    value_col: str,
) -> pd.Series:
    """Cumulative sum of *value_col* per group, **excluding** the current row."""
    return df.groupby(groupby)[value_col].cumsum() - df[value_col]


def expanding_count(
    df: pd.DataFrame,
    groupby: str | list[str],
) -> pd.Series:
    """Cumulative count per group, **excluding** the current row.

    Returns 0 on a player's first appearance.
    """
    return df.groupby(groupby).cumcount()


def bayesian_smooth(
    wins: pd.Series,
    total: pd.Series,
    c: float,
    prior: float,
) -> pd.Series:
    """Bayesian-smoothed rate: ``(wins + c * prior) / (total + c)``."""
    return (wins + c * prior) / (total + c)


# ---------------------------------------------------------------------------
# Column dropping
# ---------------------------------------------------------------------------

# Post-match / in-game columns that must never be used as ML features.
_LEAKAGE_COLUMNS: list[str] = [
    "p1_result",
    "p1_startLocX", "p1_startLocY",
    "p2_startLocX", "p2_startLocY",
    "p1_apm", "p2_apm",
    "p1_sq", "p2_sq",
    "p1_supply_capped_pct", "p2_supply_capped_pct",
    "game_loops",
    "map_size_x", "map_size_y",
    "p1_is_in_clan", "p2_is_in_clan",
    "p1_player_id", "p2_player_id",
]

# Internal helper columns that may be created during feature computation.
_HELPER_COLUMNS: list[str] = [
    "p2_target_perspective",
    "p1_win_flag", "p2_win_flag",
    "_h2h_pair",
]


def drop_leakage_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove post-match stats and internal helpers.

    Keeps metadata columns that downstream code may need for analysis or
    splitting: ``match_id``, ``match_time``, ``p1_name``, ``p2_name``,
    ``data_build``, ``map_name``, ``tournament_name``, ``split``.
    Those are stripped later by :func:`split_for_ml`.
    """
    to_drop = [c for c in _LEAKAGE_COLUMNS + _HELPER_COLUMNS if c in df.columns]
    return df.drop(columns=to_drop)


# Metadata columns that are useful for analysis but are not ML features.
_METADATA_COLUMNS: list[str] = [
    "target",
    "match_id", "match_time",
    "p1_name", "p2_name",
    "data_build", "game_version", "map_name", "tournament_name",
    "split",
]


def split_for_ml(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Split a features DataFrame into train / val / test using the ``split`` column.

    The ``split`` column is set by :func:`sc2ml.data.processing.get_matches_dataframe`
    when the ``match_split`` table exists.

    Returns
    -------
    X_train, X_val, X_test, y_train, y_val, y_test
    """
    if "split" not in df.columns:
        raise ValueError(
            "DataFrame has no 'split' column. Run create_temporal_split() in "
            "data/processing.py first, then load with get_matches_dataframe()."
        )

    drop_cols = [c for c in _METADATA_COLUMNS if c in df.columns]

    train_df = df[df["split"] == "train"]
    val_df = df[df["split"] == "val"]
    test_df = df[df["split"] == "test"]

    X_train = train_df.drop(columns=drop_cols)
    X_val = val_df.drop(columns=drop_cols)
    X_test = test_df.drop(columns=drop_cols)

    y_train = train_df["target"]
    y_val = val_df["target"]
    y_test = test_df["target"]

    logger.info(
        f"split_for_ml: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}"
    )
    return X_train, X_val, X_test, y_train, y_val, y_test
