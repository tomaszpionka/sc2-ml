"""Shared test utilities for the SC2 ML pipeline test suite."""
import numpy as np
import pandas as pd


def make_matches_df(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """Build a minimal synthetic matches_flat-like DataFrame for unit tests.

    Column set mirrors what ``get_matches_dataframe()`` returns (i.e., the
    output of the SQL views).

    The first 5 matches for Player_0 are forced to be consecutive wins so
    that streak / momentum tests have deterministic data to check against.
    """
    rng = np.random.default_rng(seed)

    # Simulate 20 unique players paired across n matches
    players = [f"Player_{i}" for i in range(20)]
    races = ["Terran", "Zerg", "Protoss"]

    p1_idx = rng.integers(0, 20, n)
    p2_idx = rng.integers(0, 20, n)
    # Avoid self-matches
    same = p1_idx == p2_idx
    p2_idx[same] = (p2_idx[same] + 1) % 20

    base_time = pd.Timestamp("2023-01-01")
    match_times = [base_time + pd.Timedelta(hours=int(i)) for i in range(n)]

    results = rng.choice(["Win", "Loss"], n).tolist()

    # Force Player_0 to be p1 and win the first 5 matches for streak tests
    for i in range(min(5, n)):
        p1_idx[i] = 0
        if p2_idx[i] == 0:
            p2_idx[i] = 1
        results[i] = "Win"

    df = pd.DataFrame(
        {
            "match_id": [f"match_{i:04d}" for i in range(n)],
            "match_time": match_times,
            "p1_name": [players[i] for i in p1_idx],
            "p2_name": [players[i] for i in p2_idx],
            "p1_race": rng.choice(races, n),
            "p2_race": rng.choice(races, n),
            "p1_result": results,
            "p1_apm": rng.uniform(80, 350, n).astype(float),
            "p2_apm": rng.uniform(80, 350, n).astype(float),
            "p1_sq": rng.uniform(30, 100, n).astype(float),
            "p2_sq": rng.uniform(30, 100, n).astype(float),
            "p1_supply_capped_pct": rng.uniform(0, 0.3, n).astype(float),
            "p2_supply_capped_pct": rng.uniform(0, 0.3, n).astype(float),
            "game_loops": rng.integers(3000, 20000, n).astype(float),
            "p1_startLocX": rng.integers(10, 100, n).astype(float),
            "p1_startLocY": rng.integers(10, 100, n).astype(float),
            "p2_startLocX": rng.integers(10, 100, n).astype(float),
            "p2_startLocY": rng.integers(10, 100, n).astype(float),
            "map_size_x": rng.integers(100, 200, n).astype(float),
            "map_size_y": rng.integers(100, 200, n).astype(float),
            "map_name": rng.choice(["Altitude", "Berlingrad", "Equilibrium"], n),
            "tournament_name": rng.choice(["GSL", "ESL", "IEM"], n),
            "data_build": rng.choice(["50011", "50012", "50013"], n),
            "game_version": rng.choice(["5.0.11.50011", "5.0.12.50012", "5.0.13.50013"], n),
            "elo_diff": rng.uniform(-300, 300, n).astype(float),
            "expected_win_prob": rng.uniform(0.3, 0.7, n).astype(float),
        }
    )
    return df


def make_series_df(match_df: pd.DataFrame, series_size: int = 3) -> pd.DataFrame:
    """Generate synthetic series assignments for the given match DataFrame.

    Groups every *series_size* consecutive matches into one series.
    Returns a DataFrame with columns ``[match_id, series_id]``.
    """
    match_ids = match_df["match_id"].tolist()
    series_ids = []
    for i, mid in enumerate(match_ids):
        series_ids.append(f"series_{i // series_size:04d}")
    return pd.DataFrame({"match_id": match_ids, "series_id": series_ids})
