"""Group E — Context features.

Patch version encoding, tournament match position, and best-of series
position.  Series data is optional — when absent, series features default
to 0.
"""

import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)


def _parse_patch_version(build: str) -> int:
    """Convert a ``data_build`` string like ``"5.0.11"`` to a sortable int.

    ``"5.0.11"`` → ``5 * 10_000 + 0 * 100 + 11 = 50011``.
    Returns 0 for malformed or missing values.
    """
    if not isinstance(build, str):
        return 0
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", build)
    if not match:
        return 0
    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    return major * 10_000 + minor * 100 + patch


def compute_context_features(
    df: pd.DataFrame,
    series_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Add context features: patch version, tournament position, series position.

    Parameters
    ----------
    df : pd.DataFrame
        Match DataFrame sorted by ``match_time`` with ``data_build`` and
        ``tournament_name`` columns.
    series_df : pd.DataFrame | None
        Optional DataFrame with columns ``[match_id, series_id]`` from the
        ``match_series`` table.  When ``None``, series features are 0.
    """
    logger.info("Computing Group E: context features...")

    # --- patch version as a sortable integer ---
    # Prefer game_version ("3.1.1.39948") which has X.Y.Z format;
    # fall back to data_build ("39948") which is a plain build number.
    if "game_version" in df.columns:
        df["patch_version_numeric"] = df["game_version"].apply(_parse_patch_version)
    elif "data_build" in df.columns:
        df["patch_version_numeric"] = df["data_build"].apply(_parse_patch_version)
    else:
        df["patch_version_numeric"] = 0

    # --- tournament match position (ordinal index within tournament) ---
    if "tournament_name" in df.columns:
        df["tournament_match_position"] = (
            df.groupby("tournament_name").cumcount() + 1
        )
    else:
        df["tournament_match_position"] = 0

    # --- series features ---
    if series_df is not None and len(series_df) > 0:
        # Deduplicate series_df — match_series may have one row per perspective
        series_dedup = series_df.drop_duplicates(subset=["match_id"])

        df = df.merge(series_dedup[["match_id", "series_id"]], on="match_id", how="left")

        # Within each series, compute the game number (1-indexed)
        df["series_game_number"] = (
            df.groupby("series_id").cumcount() + 1
        )
        df["series_length_so_far"] = df["series_game_number"] - 1

        # Clean up the join column
        df.drop(columns=["series_id"], inplace=True)

        # Fill NaN for matches that didn't join (shouldn't happen, but safety)
        df["series_game_number"] = df["series_game_number"].fillna(0).astype(int)
        df["series_length_so_far"] = df["series_length_so_far"].fillna(0).astype(int)
    else:
        df["series_game_number"] = 0
        df["series_length_so_far"] = 0

    return df
