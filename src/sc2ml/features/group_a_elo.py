"""Group A — Dynamic K-factor Elo ratings.

Computes pre-match Elo for both players using a two-pass approach that
guarantees no look-ahead bias.  K-factor adapts based on each player's
experience (number of games played).
"""

import logging

import pandas as pd

from sc2ml.config import ELO_K_NEW, ELO_K_THRESHOLD, ELO_K_VETERAN

logger = logging.getLogger(__name__)

#: Columns added by this group.
OUTPUT_COLUMNS: list[str] = [
    "p1_pre_match_elo",
    "p2_pre_match_elo",
    "elo_diff",
    "expected_win_prob",
]


def compute_elo_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add pre-match Elo ratings, Elo difference, and expected win probability.

    The DataFrame must already be sorted by ``match_time``.

    Two-pass algorithm:
      Phase 1 — snapshot each player's Elo *before* the match is processed.
      Phase 2 — update Elo once per unique ``match_id`` (the paired-row layout
                would cause double-updates without the dedup guard).
    """
    logger.info("Computing Group A: Elo features (dynamic K-factor)...")

    elo_dict: dict[str, float] = {}
    games_played: dict[str, int] = {}
    pre_match_elos: dict[str, dict[str, float]] = {}

    # Phase 1: record each player's Elo at the time of every match
    for row in df.itertuples():
        match_id: str = row.match_id
        p1: str = row.p1_name
        p2: str = row.p2_name

        if match_id not in pre_match_elos:
            pre_match_elos[match_id] = {}

        for p in (p1, p2):
            if p not in elo_dict:
                elo_dict[p] = 1500.0
                games_played[p] = 0
            if p not in pre_match_elos[match_id]:
                pre_match_elos[match_id][p] = elo_dict[p]

    # Phase 2: update Elo once per unique match
    processed: set[str] = set()
    for row in df.itertuples():
        match_id = row.match_id
        if match_id in processed:
            continue

        p1 = row.p1_name
        p2 = row.p2_name
        target = 1 if row.p1_result == "Win" else 0

        e1 = 1 / (1 + 10 ** ((elo_dict[p2] - elo_dict[p1]) / 400))

        k1 = ELO_K_NEW if games_played[p1] < ELO_K_THRESHOLD else ELO_K_VETERAN
        k2 = ELO_K_NEW if games_played[p2] < ELO_K_THRESHOLD else ELO_K_VETERAN

        elo_dict[p1] += k1 * (target - e1)
        elo_dict[p2] += k2 * ((1 - target) - (1 - e1))

        games_played[p1] += 1
        games_played[p2] += 1
        processed.add(match_id)

    # Map pre-match Elo back to the DataFrame
    df["p1_pre_match_elo"] = df.apply(
        lambda x: pre_match_elos[x["match_id"]][x["p1_name"]], axis=1
    )
    df["p2_pre_match_elo"] = df.apply(
        lambda x: pre_match_elos[x["match_id"]][x["p2_name"]], axis=1
    )
    df["elo_diff"] = df["p1_pre_match_elo"] - df["p2_pre_match_elo"]
    df["expected_win_prob"] = 1 / (1 + 10 ** (-df["elo_diff"] / 400))

    return df
