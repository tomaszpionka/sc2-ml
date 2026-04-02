"""Backward-compatible wrappers for the legacy feature engineering API.

These functions allow existing code (cli.py, tests, GNN pipeline) to
continue importing from ``sc2ml.features.engineering`` or
``sc2ml.features.elo`` without changes during the migration period.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


def perform_feature_engineering(df: "pd.DataFrame") -> "pd.DataFrame":
    """Drop-in replacement for the old monolithic function.

    Calls :func:`build_features` with all groups (A–E), then ensures the
    output column set is a superset of the old output.
    """
    from sc2ml.features import build_features

    return build_features(df)


def temporal_train_test_split(
    df: "pd.DataFrame",
    test_size: float = 0.2,
) -> "tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]":
    """Deprecated — use :func:`split_for_ml` with the ``split`` column instead.

    Preserved so that existing callers do not break.  Performs a simple
    chronological split without series awareness.
    """
    warnings.warn(
        "temporal_train_test_split() is deprecated.  Use split_for_ml() with "
        "the 'split' column from data/processing.py instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    split_index = int(len(df) * (1 - test_size))
    train_df = df.iloc[:split_index]
    test_df = df.iloc[split_index:]

    cols_to_drop = ["target", "match_time", "match_id", "p1_name", "p2_name"]
    drop_cols = [c for c in cols_to_drop if c in train_df.columns]

    X_train = train_df.drop(columns=drop_cols)
    y_train = train_df["target"]
    X_test = test_df.drop(columns=drop_cols)
    y_test = test_df["target"]

    return X_train, X_test, y_train, y_test
