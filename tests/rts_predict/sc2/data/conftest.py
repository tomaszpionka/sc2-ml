"""Shared fixtures for rts_predict.sc2.data tests."""
import json
from collections.abc import Generator
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd
import pytest

from rts_predict.sc2.config import DATA_DIR

SYNTHETIC_REPLAY_IDS = [
    "aabbccdd11223344556677889900aa00",
    "aabbccdd11223344556677889900aa01",
    "aabbccdd11223344556677889900aa02",
    "aabbccdd11223344556677889900aa03",
    "aabbccdd11223344556677889900aa04",
]

# Sample replay file shipped with the repository
SAMPLE_REPLAY_PATH = (
    DATA_DIR / "samples" / "raw"
    / "0e0b1a550447f0b0a616e48224b31bd9.SC2Replay.json"
)


@pytest.fixture()
def sample_replay_path() -> Path:
    """Path to the raw sample SC2Replay JSON (sOs vs ByuN)."""
    assert SAMPLE_REPLAY_PATH.exists(), f"Sample replay not found: {SAMPLE_REPLAY_PATH}"
    return SAMPLE_REPLAY_PATH


@pytest.fixture()
def duckdb_con() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """In-memory DuckDB connection for testing."""
    con = duckdb.connect(":memory:")
    yield con
    con.close()


@pytest.fixture()
def in_memory_duckdb() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Fresh in-memory DuckDB connection for ingest_map_alias_files tests."""
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
    races = ["Terran", "Protoss", "Zerg"]
    tournaments = ["2023_GSL_S1", "2023_IEM_Katowice", "2024_ESL_Pro"]
    maps = ["Altitude LE", "Berlingrad LE", "Equilibrium LE"]

    n = 100
    rows: list[dict[str, Any]] = []
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
                "data_build": "50012",
                "game_version": "5.0.12.50012",
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

    df = pd.DataFrame(rows)  # noqa: F841 — referenced by DuckDB SQL below

    # Register as a view so processing functions can query it
    duckdb_con.execute("CREATE TABLE matches_flat AS SELECT * FROM df")
    return duckdb_con


def _build_toon_player_desc_map(
    p1_name: str,
    p2_name: str,
    p1_race: str,
    p2_race: str,
    p1_result: str,
) -> str:
    """Build a ToonPlayerDescMap JSON string for two players."""
    p2_result = "Loss" if p1_result == "Win" else "Win"
    tpdm = {
        "toon-1": {
            "nickname": p1_name,
            "playerID": 1,
            "userID": 1,
            "SQ": 80,
            "supplyCappedPercent": 5,
            "startLocX": 40,
            "startLocY": 20,
            "race": p1_race,
            "APM": 0,
            "MMR": 0,
            "result": p1_result,
            "isInClan": False,
        },
        "toon-2": {
            "nickname": p2_name,
            "playerID": 2,
            "userID": 2,
            "SQ": 75,
            "supplyCappedPercent": 8,
            "startLocX": 130,
            "startLocY": 150,
            "race": p2_race,
            "APM": 0,
            "MMR": 0,
            "result": p2_result,
            "isInClan": False,
        },
    }
    return json.dumps(tpdm)


@pytest.fixture()
def raw_table_con(duckdb_con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    """DuckDB connection with a synthetic ``raw`` table.

    Creates 5 matches mimicking the structure produced by ``move_data_to_duck_db``,
    suitable for testing view-creation helpers in processing.py.
    """
    matches = [
        ("GSL_S1", "Alpha", "Beta", "Terr", "Prot", "Win", "Altitude LE"),
        ("GSL_S1", "Gamma", "Delta", "Zerg", "Terr", "Loss", "Berlingrad LE"),
        ("IEM_Katowice", "Alpha", "Gamma", "Prot", "Zerg", "Win", "MapKorean"),
        ("IEM_Katowice", "Beta", "Delta", "Terr", "Terr", "Win", "Altitude LE"),
        ("ESL_Pro", "Alpha", "Delta", "Zerg", "Prot", "Loss", "Equilibrium LE"),
    ]

    rows = []
    base_ts = pd.Timestamp("2023-06-01 12:00:00")
    for i, (tourn, p1, p2, r1, r2, result, map_name) in enumerate(matches):
        ts = base_ts + pd.Timedelta(days=i * 7)
        tpdm = _build_toon_player_desc_map(p1, p2, r1, r2, result)
        rows.append({
            "filename": f"{tourn}/{tourn}_data/{SYNTHETIC_REPLAY_IDS[i]}.SC2Replay.json",
            "header": json.dumps({"elapsedGameLoops": 8000 + i * 500}),
            "initData": json.dumps({
                "gameDescription": {"mapSizeX": 200, "mapSizeY": 200},
            }),
            "details": json.dumps({"timeUTC": ts.isoformat()}),
            "metadata": json.dumps({
                "dataBuild": "50012",
                "gameVersion": "5.0.12.50012",
                "mapName": map_name,
            }),
            "ToonPlayerDescMap": tpdm,
        })

    df = pd.DataFrame(rows)  # noqa: F841 — referenced by DuckDB SQL below
    duckdb_con.execute("CREATE TABLE raw AS SELECT * FROM df")

    # Cast JSON columns — DuckDB read_json produces JSON type, but our synthetic
    # data comes as VARCHAR; cast to JSON so ->> operator works.
    duckdb_con.execute("""
        CREATE OR REPLACE TABLE raw AS
        SELECT
            filename,
            header::JSON AS header,
            "initData"::JSON AS "initData",
            details::JSON AS details,
            metadata::JSON AS metadata,
            "ToonPlayerDescMap"::JSON AS "ToonPlayerDescMap"
        FROM raw
    """)

    return duckdb_con
