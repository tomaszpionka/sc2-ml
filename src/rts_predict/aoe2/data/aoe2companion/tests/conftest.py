"""Fixtures for aoe2companion data acquisition tests."""

import json
from pathlib import Path

import pytest


@pytest.fixture()
def aoe2companion_manifest_entries() -> list[dict]:
    """Minimal aoe2companion manifest entries covering all categories + skips."""
    return [
        {
            "key": "match-2024-01-01.parquet",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": '"abc123"-16',
            "size": 500000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/match-2024-01-01.parquet",
        },
        {
            "key": "leaderboard.parquet",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": '"def456"-8',
            "size": 87000000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/leaderboard.parquet",
        },
        {
            "key": "profile.parquet",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": '"ghi789"-4',
            "size": 170000000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/profile.parquet",
        },
        {
            "key": "rating-2024-01-01.csv",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": '"jkl012"',
            "size": 1000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/rating-2024-01-01.csv",
        },
        # --- entries that should be SKIPPED ---
        {
            "key": "match-2024-01-01.csv",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": '"skip1"',
            "size": 3000000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/match-2024-01-01.csv",
        },
        {
            "key": "leaderboard.csv",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": '"skip2"',
            "size": 700000000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/leaderboard.csv",
        },
        {
            "key": "profile.csv",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": '"skip3"',
            "size": 600000000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/profile.csv",
        },
        {
            "key": "test-match-2022-09-09.parquet",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": '"skip4"',
            "size": 5000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/test-match-2022-09-09.parquet",
        },
        {
            "key": "test2-match-2022-10-07.parquet",
            "lastModified": "2024-01-02T00:00:00.000Z",
            "eTag": '"skip5"',
            "size": 5000,
            "storageClass": "STANDARD",
            "url": "https://dump.cdn.aoe2companion.com/test2-match-2022-10-07.parquet",
        },
    ]


@pytest.fixture()
def aoe2companion_manifest_file(
    tmp_path: Path, aoe2companion_manifest_entries: list[dict]
) -> Path:
    """Write fixture entries to a temporary manifest JSON file."""
    manifest_path = tmp_path / "api_dump_list.json"
    manifest_path.write_text(json.dumps(aoe2companion_manifest_entries))
    return manifest_path
