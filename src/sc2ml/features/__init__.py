"""Pre-match feature engineering for SC2 match prediction.

Public API
----------
- :func:`build_features` — compose feature groups on a raw matches DataFrame
- :func:`split_for_ml` — split into train/val/test using the ``split`` column
- :class:`FeatureGroup` — enum of groups A–E for ablation
- :func:`get_groups` — return ordered subset up to a given group

Backward-compatible re-exports (deprecated paths)
--------------------------------------------------
- :func:`perform_feature_engineering` — calls ``build_features(df)``
- :func:`temporal_train_test_split` — deprecated; use :func:`split_for_ml`
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sc2ml.features.common import (
    compute_target,
    drop_leakage_columns,
    ensure_sorted,
    split_for_ml,
)
from sc2ml.features.registry import (
    FEATURE_GROUPS,
    FeatureGroup,
    get_groups,
)

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)

__all__ = [
    "build_features",
    "split_for_ml",
    "FeatureGroup",
    "get_groups",
    # backward compat
    "perform_feature_engineering",
    "temporal_train_test_split",
]


def build_features(
    df: "pd.DataFrame",
    groups: list[FeatureGroup] | FeatureGroup | None = None,
    series_df: "pd.DataFrame | None" = None,
) -> "pd.DataFrame":
    """Compose requested feature groups on a raw matches DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Output of ``get_matches_dataframe()``.
    groups : list[FeatureGroup] | FeatureGroup | None
        ``None`` → all groups A–E.
        A single :class:`FeatureGroup` → "up to and including" that group.
        A list → exactly those groups.
    series_df : pd.DataFrame | None
        ``[match_id, series_id]`` for Group E.  Ignored if E is not requested.

    Returns
    -------
    pd.DataFrame
        Feature-enriched DataFrame with leakage columns removed.
    """
    # Resolve *groups* into an ordered list
    if groups is None:
        selected = list(FeatureGroup)
    elif isinstance(groups, FeatureGroup):
        selected = get_groups(groups)
    else:
        # Ensure consistent ordering even if caller shuffled the list
        ordered = list(FeatureGroup)
        selected = [g for g in ordered if g in groups]

    df = ensure_sorted(df)
    df = compute_target(df)

    for group in selected:
        spec = FEATURE_GROUPS[group]
        if group == FeatureGroup.E:
            df = spec.compute_fn(df, series_df=series_df)
        else:
            df = spec.compute_fn(df)

    df = drop_leakage_columns(df)

    # Cast any remaining bool columns to int
    for col in df.select_dtypes(include=["bool"]).columns:
        df[col] = df[col].astype(int)

    logger.info(
        f"build_features complete: {len(selected)} groups → "
        f"{df.shape[1]} columns ({df.shape[0]} rows)."
    )
    return df


# ---------------------------------------------------------------------------
# Backward-compatible re-exports
# ---------------------------------------------------------------------------

from sc2ml.features.compat import (  # noqa: E402
    perform_feature_engineering,
    temporal_train_test_split,
)
