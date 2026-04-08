"""Fixtures for aoe2companion ingestion, audit, and acquisition tests.

Uses synthetic data generated in-memory to avoid depending on real raw data
in tests. Real captured fixture files (under tests/fixtures/) are used only
for the sparse/dense CSV union test.

Also provides backward-compatible fixtures for test_acquisition.py
(aoe2companion_manifest_entries, aoe2companion_manifest_file).
"""

import json
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

# ── Real fixture paths ────────────────────────────────────────────────────────
FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
SPARSE_CSV_FIXTURE: Path = FIXTURES_DIR / "rating-2020-08-01-sparse.csv"
DENSE_CSV_FIXTURE: Path = FIXTURES_DIR / "rating-2025-06-27-dense.csv"


# ── Synthetic match parquet ───────────────────────────────────────────────────


def _write_match_parquet(path: Path, n_rows: int = 3) -> None:
    """Write a minimal synthetic match parquet to path."""
    table = pa.table(
        {
            "match_id": pa.array([1001 + i for i in range(n_rows)], type=pa.int64()),
            "started": pa.array(
                ["2024-01-01T10:00:00"] * n_rows, type=pa.string()
            ),
            "map_name": pa.array(["Arabia"] * n_rows, type=pa.string()),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


# ── Synthetic rating CSVs ────────────────────────────────────────────────────

_RATING_HEADER = "profile_id,games,rating,date,leaderboard_id,rating_diff,season\n"
_RATING_ROW = "1000001,50,1400,2024-01-01 00:00:00,3,5,-1\n"
_SPARSE_CSV_CONTENT = (
    _RATING_HEADER + "912523,5,1200,2020-08-01 00:00:00,3,0,-1\n"
)  # 1 data row — still tiny but has a filename in DuckDB result
# Dense CSV must be >= 1024 bytes to be classified as dense.
# Repeat rows to ensure file size exceeds the threshold.
_DENSE_CSV_CONTENT = _RATING_HEADER + (_RATING_ROW * 60)  # ~60 rows ≈ 3 KB


# ── Synthetic leaderboard parquet ────────────────────────────────────────────


def _write_leaderboard_parquet(path: Path) -> None:
    table = pa.table(
        {
            "profile_id": pa.array([1, 2, 3], type=pa.int64()),
            "rank": pa.array([1, 2, 3], type=pa.int64()),
            "rating": pa.array([2000, 1900, 1800], type=pa.int64()),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


def _write_profiles_parquet(path: Path) -> None:
    table = pa.table(
        {
            "profile_id": pa.array([1, 2, 3], type=pa.int64()),
            "name": pa.array(["Alice", "Bob", "Carol"], type=pa.string()),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


# ── Raw directory layout fixture ─────────────────────────────────────────────


@pytest.fixture()
def raw_dir(tmp_path: Path) -> Path:
    """Create a minimal synthetic raw directory with all required files.

    Layout:
        raw/
            matches/
                match-2024-01-01.parquet  (3 rows)
                match-2024-01-02.parquet  (3 rows)
            ratings/
                rating-2020-08-01.csv     (header-only, sparse)
                rating-2024-01-01.csv     (1 data row, dense enough for tests)
            leaderboards/
                leaderboard.parquet       (3 rows)
            profiles/
                profile.parquet           (3 rows)
    """
    raw = tmp_path / "raw"

    # Matches
    _write_match_parquet(raw / "matches" / "match-2024-01-01.parquet", n_rows=3)
    _write_match_parquet(raw / "matches" / "match-2024-01-02.parquet", n_rows=3)

    # Ratings: one sparse (header-only, 63 bytes) and one dense (>= 1 KB)
    (raw / "ratings").mkdir(parents=True, exist_ok=True)
    (raw / "ratings" / "rating-2020-08-01.csv").write_text(_SPARSE_CSV_CONTENT)
    (raw / "ratings" / "rating-2024-01-01.csv").write_text(_DENSE_CSV_CONTENT)

    # Singletons
    _write_leaderboard_parquet(raw / "leaderboards" / "leaderboard.parquet")
    _write_profiles_parquet(raw / "profiles" / "profile.parquet")

    return raw


@pytest.fixture()
def db_con() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB connection for ingestion tests."""
    return duckdb.connect(":memory:")


@pytest.fixture()
def manifest_file(tmp_path: Path, raw_dir: Path) -> Path:
    """Minimal manifest referencing the synthetic raw dir files."""
    entries = [
        {
            "key": "match-2024-01-01.parquet",
            "target_path": str(raw_dir / "matches" / "match-2024-01-01.parquet"),
            "size": (raw_dir / "matches" / "match-2024-01-01.parquet").stat().st_size,
            "status": "downloaded",
            "timestamp": "2024-01-02T00:00:00+00:00",
            "error": None,
        },
        {
            "key": "match-2024-01-02.parquet",
            "target_path": str(raw_dir / "matches" / "match-2024-01-02.parquet"),
            "size": (raw_dir / "matches" / "match-2024-01-02.parquet").stat().st_size,
            "status": "downloaded",
            "timestamp": "2024-01-03T00:00:00+00:00",
            "error": None,
        },
        {
            "key": "rating-2020-08-01.csv",
            "target_path": str(raw_dir / "ratings" / "rating-2020-08-01.csv"),
            "size": (raw_dir / "ratings" / "rating-2020-08-01.csv").stat().st_size,
            "status": "downloaded",
            "timestamp": "2020-08-01T00:00:00+00:00",
            "error": None,
        },
        {
            "key": "rating-2024-01-01.csv",
            "target_path": str(raw_dir / "ratings" / "rating-2024-01-01.csv"),
            "size": (raw_dir / "ratings" / "rating-2024-01-01.csv").stat().st_size,
            "status": "downloaded",
            "timestamp": "2024-01-02T00:00:00+00:00",
            "error": None,
        },
        {
            "key": "leaderboard.parquet",
            "target_path": str(raw_dir / "leaderboards" / "leaderboard.parquet"),
            "size": (raw_dir / "leaderboards" / "leaderboard.parquet").stat().st_size,
            "status": "downloaded",
            "timestamp": "2024-01-02T00:00:00+00:00",
            "error": None,
        },
        {
            "key": "profile.parquet",
            "target_path": str(raw_dir / "profiles" / "profile.parquet"),
            "size": (raw_dir / "profiles" / "profile.parquet").stat().st_size,
            "status": "downloaded",
            "timestamp": "2024-01-02T00:00:00+00:00",
            "error": None,
        },
    ]
    manifest_path = tmp_path / "_download_manifest.json"
    manifest_path.write_text(json.dumps(entries, indent=2))
    return manifest_path


# ── Backward-compatible fixtures for test_acquisition.py ─────────────────────


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
