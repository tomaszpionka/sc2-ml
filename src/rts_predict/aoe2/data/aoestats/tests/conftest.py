"""Fixtures for aoestats data acquisition tests."""

import json
from pathlib import Path

import pytest


@pytest.fixture()
def aoestats_manifest_entries() -> list[dict]:
    """Minimal aoestats manifest entries including a zero-match week."""
    return [
        {
            "start_date": "2023-01-01",
            "end_date": "2023-01-07",
            "num_matches": 150000,
            "num_players": 300000,
            "matches_url": "/media/db_dumps/date_range%3D2023-01-01_2023-01-07/matches.parquet",
            "players_url": "/media/db_dumps/date_range%3D2023-01-01_2023-01-07/players.parquet",
            "match_checksum": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
            "player_checksum": "f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3",
        },
        {
            "start_date": "2023-01-08",
            "end_date": "2023-01-14",
            "num_matches": 120000,
            "num_players": 250000,
            "matches_url": "/media/db_dumps/date_range%3D2023-01-08_2023-01-14/matches.parquet",
            "players_url": "/media/db_dumps/date_range%3D2023-01-08_2023-01-14/players.parquet",
            "match_checksum": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d400",
            "player_checksum": "e5d4c3b2a1f6e5d4c3b2a1f6e5d4c300",
        },
        # --- zero-match week: should be SKIPPED ---
        {
            "start_date": "2023-01-15",
            "end_date": "2023-01-21",
            "num_matches": 0,
            "num_players": 0,
            "matches_url": "/media/db_dumps/date_range%3D2023-01-15_2023-01-21/matches.parquet",
            "players_url": "/media/db_dumps/date_range%3D2023-01-15_2023-01-21/players.parquet",
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
