import logging

import pandas as pd

from sc2ml.config import ELO_K_NEW, ELO_K_THRESHOLD, ELO_K_VETERAN

logger = logging.getLogger(__name__)


def add_elo_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute pre-match ELO ratings with a dynamic K-factor and add them to the dataframe.

    Uses a two-pass approach:
      Phase 1 — Record each player's ELO at the time of every match they played
                 (before any updates for that match).
      Phase 2 — Update ELO ratings in chronological order, processing each unique
                 match_id exactly once (the paired-row layout of matches_flat would
                 cause double-updates without this guard).

    ELO starts at 1500. K-factor is ELO_K_NEW for new players (< ELO_K_THRESHOLD games)
    and ELO_K_VETERAN for veterans.
    """
    logger.info("Computing custom ELO ratings (dynamic K-factor)...")

    df = df.sort_values("match_time").reset_index(drop=True)

    elo_dict: dict[str, float] = {}
    games_played_dict: dict[str, int] = {}
    pre_match_elos: dict[str, dict[str, float]] = {}

    # Phase 1: snapshot each player's ELO before their match is processed
    for row in df.itertuples():
        match_id = row.match_id
        p1 = row.p1_name
        p2 = row.p2_name

        if match_id not in pre_match_elos:
            pre_match_elos[match_id] = {}

        for p in [p1, p2]:
            if p not in elo_dict:
                elo_dict[p] = 1500.0
                games_played_dict[p] = 0
            if p not in pre_match_elos[match_id]:
                pre_match_elos[match_id][p] = elo_dict[p]

    # Phase 2: update ELO ratings once per unique match
    processed_matches: set[str] = set()
    for row in df.itertuples():
        match_id = row.match_id

        if match_id in processed_matches:
            continue

        p1 = row.p1_name
        p2 = row.p2_name
        target = 1 if row.p1_result == "Win" else 0

        # Expected win probability for p1 using the standard ELO formula
        e1 = 1 / (1 + 10 ** ((elo_dict[p2] - elo_dict[p1]) / 400))

        k1 = ELO_K_NEW if games_played_dict[p1] < ELO_K_THRESHOLD else ELO_K_VETERAN
        k2 = ELO_K_NEW if games_played_dict[p2] < ELO_K_THRESHOLD else ELO_K_VETERAN

        elo_dict[p1] += k1 * (target - e1)
        elo_dict[p2] += k2 * ((1 - target) - (1 - e1))

        games_played_dict[p1] += 1
        games_played_dict[p2] += 1

        processed_matches.add(match_id)

    logger.info("Mapping pre-match ELO scores back to the main dataset...")

    df["p1_pre_match_elo"] = df.apply(
        lambda x: pre_match_elos[x["match_id"]][x["p1_name"]], axis=1
    )
    df["p2_pre_match_elo"] = df.apply(
        lambda x: pre_match_elos[x["match_id"]][x["p2_name"]], axis=1
    )

    df["elo_diff"] = df["p1_pre_match_elo"] - df["p2_pre_match_elo"]
    df["expected_win_prob"] = 1 / (1 + 10 ** (-df["elo_diff"] / 400))

    return df
