"""Shared fixtures for sc2ml.data tests."""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pytest

# Sample replay file shipped with the repository
SAMPLE_REPLAY_PATH = (
    Path(__file__).resolve().parent.parent / "samples" / "raw"
    / "0e0b1a550447f0b0a616e48224b31bd9.SC2Replay.json"
)


@pytest.fixture()
def sample_replay_path() -> Path:
    """Path to the raw sample SC2Replay JSON (sOs vs ByuN)."""
    assert SAMPLE_REPLAY_PATH.exists(), f"Sample replay not found: {SAMPLE_REPLAY_PATH}"
    return SAMPLE_REPLAY_PATH


@pytest.fixture()
def duckdb_con() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB connection for testing."""
    con = duckdb.connect(":memory:")
    yield con
    con.close()


@pytest.fixture()
def matches_flat_con(duckdb_con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    """DuckDB connection with a synthetic ``matches_flat`` view populated.

    Creates 100 matches across 3 tournaments with realistic temporal ordering,
    including some best-of series (same player pair within short time gaps).
    """
    rng = np.random.default_rng(42)
    players = [f"player_{i}" for i in range(20)]
    races = ["Terr", "Prot", "Zerg"]
    tournaments = ["2023_GSL_S1", "2023_IEM_Katowice", "2024_ESL_Pro"]
    maps = ["Altitude LE", "Berlingrad LE", "Equilibrium LE"]

    n = 100
    rows = []
    base_time = pd.Timestamp("2023-01-01 10:00:00")

    for i in range(n):
        p1_idx = rng.integers(0, 20)
        p2_idx = (p1_idx + rng.integers(1, 20)) % 20

        # Create some series: every 5th match reuses previous pair with short gap
        if i > 0 and i % 5 == 0:
            prev = rows[-1]
            p1_name = prev["p1_name"]
            p2_name = prev["p2_name"]
            match_time = prev["match_time"] + pd.Timedelta(minutes=rng.integers(20, 60))
            tournament = prev["tournament_name"]
        else:
            p1_name = players[p1_idx]
            p2_name = players[p2_idx]
            match_time = base_time + pd.Timedelta(hours=int(i * 12 + rng.integers(0, 6)))
            tournament = rng.choice(tournaments)

        result = rng.choice(["Win", "Loss"])

        for perspective in [
            (p1_name, p2_name, 1, 2, result),
            (p2_name, p1_name, 2, 1, "Loss" if result == "Win" else "Win"),
        ]:
            rows.append({
                "match_id": f"tournament_data/match_{i:04d}.SC2Replay.json",
                "tournament_name": tournament,
                "match_time": match_time,
                "game_loops": int(rng.integers(3000, 20000)),
                "map_size_x": 200,
                "map_size_y": 200,
                "data_build": "5.0.12",
                "map_name": rng.choice(maps),
                "p1_player_id": perspective[2],
                "p2_player_id": perspective[3],
                "p1_name": perspective[0],
                "p2_name": perspective[1],
                "p1_race": rng.choice(races),
                "p2_race": rng.choice(races),
                "p1_startLocX": int(rng.integers(10, 100)),
                "p1_startLocY": int(rng.integers(10, 100)),
                "p2_startLocX": int(rng.integers(10, 100)),
                "p2_startLocY": int(rng.integers(10, 100)),
                "p1_apm": int(rng.integers(80, 350)),
                "p1_sq": int(rng.integers(30, 100)),
                "p2_apm": int(rng.integers(80, 350)),
                "p2_sq": int(rng.integers(30, 100)),
                "p1_supply_capped_pct": int(rng.integers(0, 30)),
                "p2_supply_capped_pct": int(rng.integers(0, 30)),
                "p1_is_in_clan": False,
                "p2_is_in_clan": False,
                "p1_result": perspective[4],
            })

    df = pd.DataFrame(rows)

    # Register as a view so processing functions can query it
    duckdb_con.execute("CREATE TABLE matches_flat AS SELECT * FROM df")
    return duckdb_con
