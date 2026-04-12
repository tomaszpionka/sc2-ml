"""Shared fixtures for SC2 game-level tests."""
import json
from collections.abc import Generator

import duckdb
import pandas as pd
import pytest

SYNTHETIC_REPLAY_IDS = [
    "aabbccdd11223344556677889900aa00",
    "aabbccdd11223344556677889900aa01",
    "aabbccdd11223344556677889900aa02",
    "aabbccdd11223344556677889900aa03",
    "aabbccdd11223344556677889900aa04",
]


@pytest.fixture()
def duckdb_con() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """In-memory DuckDB connection for testing."""
    con = duckdb.connect(":memory:")
    yield con
    con.close()


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
