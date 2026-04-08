"""Fixtures for aoestats ingestion and audit tests.

Uses synthetic data generated in-memory. Also provides backward-compatible
fixtures for test_acquisition.py (aoestats_manifest_entries, aoestats_manifest_file).
"""

import json
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

# ── Synthetic parquet helpers ─────────────────────────────────────────────────


def _write_matches_parquet(path: Path, n_rows: int = 5) -> None:
    """Write a minimal synthetic weekly matches parquet."""
    table = pa.table(
        {
            "match_id": pa.array(list(range(n_rows)), type=pa.int64()),
            "map_name": pa.array(["Arabia"] * n_rows, type=pa.string()),
            "started": pa.array(["2024-01-01T10:00:00"] * n_rows, type=pa.string()),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


def _write_players_parquet(path: Path, n_rows: int = 10) -> None:
    """Write a minimal synthetic weekly players parquet."""
    table = pa.table(
        {
            "match_id": pa.array(list(range(n_rows)), type=pa.int64()),
            "profile_id": pa.array([1000 + i for i in range(n_rows)], type=pa.int64()),
            "rating": pa.array([1400 + i * 10 for i in range(n_rows)], type=pa.int64()),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


# ── Raw directory layout fixture ─────────────────────────────────────────────


@pytest.fixture()
def raw_dir(tmp_path: Path) -> Path:
    """Create a minimal synthetic aoestats raw directory.

    Layout:
        raw/
            matches/
                2024-01-01_2024-01-07_matches.parquet  (5 rows)
                2024-01-08_2024-01-14_matches.parquet  (5 rows)
            players/
                2024-01-01_2024-01-07_players.parquet  (10 rows)
                2024-01-08_2024-01-14_players.parquet  (10 rows)
    """
    raw = tmp_path / "raw"

    _write_matches_parquet(raw / "matches" / "2024-01-01_2024-01-07_matches.parquet")
    _write_matches_parquet(raw / "matches" / "2024-01-08_2024-01-14_matches.parquet")
    _write_players_parquet(raw / "players" / "2024-01-01_2024-01-07_players.parquet")
    _write_players_parquet(raw / "players" / "2024-01-08_2024-01-14_players.parquet")

    return raw


@pytest.fixture()
def db_con() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB connection."""
    return duckdb.connect(":memory:")


@pytest.fixture()
def manifest_file(tmp_path: Path, raw_dir: Path) -> Path:
    """Minimal manifest referencing the synthetic raw dir files."""
    entries = []
    for fname, ftype in [
        ("2024-01-01_2024-01-07_matches.parquet", "matches"),
        ("2024-01-01_2024-01-07_players.parquet", "players"),
        ("2024-01-08_2024-01-14_matches.parquet", "matches"),
        ("2024-01-08_2024-01-14_players.parquet", "players"),
    ]:
        subdir = "matches" if ftype == "matches" else "players"
        fpath = raw_dir / subdir / fname
        entries.append({
            "start_date": "2024-01-01",
            "end_date": "2024-01-07" if "01-07" in fname else "2024-01-14",
            "file_type": ftype,
            "url": f"https://aoestats.io/media/{fname}",
            "target_path": str(fpath),
            "checksum": "abc123",
            "size": fpath.stat().st_size,
            "status": "downloaded",
            "timestamp": "2024-01-15T00:00:00+00:00",
            "error": None,
        })
    manifest_path = tmp_path / "_download_manifest.json"
    manifest_path.write_text(json.dumps(entries, indent=2))
    return manifest_path


# ── Backward-compatible fixtures for test_acquisition.py ─────────────────────


@pytest.fixture()
def aoestats_manifest_entries() -> list[dict]:
    """Minimal aoestats manifest entries including a zero-match week."""
    return [
        {
            "start_date": "2023-01-01",
            "end_date": "2023-01-07",
            "num_matches": 150000,
            "num_players": 300000,
            "matches_url": (
                "/media/db_dumps/date_range%3D2023-01-01_2023-01-07/matches.parquet"
            ),
            "players_url": (
                "/media/db_dumps/date_range%3D2023-01-01_2023-01-07/players.parquet"
            ),
            "match_checksum": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
            "player_checksum": "f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3",
        },
        {
            "start_date": "2023-01-08",
            "end_date": "2023-01-14",
            "num_matches": 120000,
            "num_players": 250000,
            "matches_url": (
                "/media/db_dumps/date_range%3D2023-01-08_2023-01-14/matches.parquet"
            ),
            "players_url": (
                "/media/db_dumps/date_range%3D2023-01-08_2023-01-14/players.parquet"
            ),
            "match_checksum": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d400",
            "player_checksum": "e5d4c3b2a1f6e5d4c3b2a1f6e5d4c300",
        },
        {
            "start_date": "2023-01-15",
            "end_date": "2023-01-21",
            "num_matches": 0,
            "num_players": 0,
            "matches_url": (
                "/media/db_dumps/date_range%3D2023-01-15_2023-01-21/matches.parquet"
            ),
            "players_url": (
                "/media/db_dumps/date_range%3D2023-01-15_2023-01-21/players.parquet"
            ),
            "match_checksum": "00000000000000000000000000000000",
            "player_checksum": "00000000000000000000000000000000",
        },
    ]


@pytest.fixture()
def aoestats_manifest_file(
    tmp_path: Path, aoestats_manifest_entries: list[dict]
) -> Path:
    """Write fixture entries to a temporary aoestats manifest JSON file."""
    manifest_path = tmp_path / "db_dump_list.json"
    manifest_path.write_text(json.dumps({"db_dumps": aoestats_manifest_entries}))
    return manifest_path
