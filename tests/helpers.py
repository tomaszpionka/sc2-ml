"""Shared test utilities for the SC2 ML pipeline test suite."""
import numpy as np
import pandas as pd


def make_matches_df(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """Build a minimal synthetic matches_flat-like DataFrame for unit tests.

    Column set mirrors what perform_feature_engineering() expects as input
    (i.e., the output of the SQL views + ELO stage).
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

    df = pd.DataFrame(
        {
            "match_id": [f"match_{i:04d}" for i in range(n)],
            "match_time": match_times,
            "p1_name": [players[i] for i in p1_idx],
            "p2_name": [players[i] for i in p2_idx],
            "p1_race": rng.choice(races, n),
            "p2_race": rng.choice(races, n),
            "p1_result": rng.choice(["Win", "Loss"], n),
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
            "data_build": rng.choice(["5.0.11", "5.0.12", "5.0.13"], n),
            "elo_diff": rng.uniform(-300, 300, n).astype(float),
            "expected_win_prob": rng.uniform(0.3, 0.7, n).astype(float),
        }
    )
    return df
