"""Tests for aoe2companion ingestion.py — CTAS functions."""

from pathlib import Path

import duckdb
import pytest

from rts_predict.games.aoe2.datasets.aoe2companion.ingestion import (
    load_all_raw_tables,
    load_leaderboards_raw,
    load_matches_raw,
    load_profiles_raw,
    load_ratings_raw,
)
from rts_predict.games.aoe2.datasets.aoe2companion.types import DtypeDecision

# ── load_matches_raw ──────────────────────────────────────────────────────────


def test_load_matches_raw_creates_table_with_filename(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """matches_raw table must exist and contain a 'filename' column."""
    n = load_matches_raw(db_con, raw_dir)
    assert n > 0
    tables = [row[0] for row in db_con.execute("SHOW TABLES").fetchall()]
    assert "matches_raw" in tables
    cols = [row[0] for row in db_con.execute("DESCRIBE matches_raw").fetchall()]
    assert "filename" in cols


def test_load_matches_raw_filename_is_relative(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """filename column must be relative (no leading /) and non-bare (contains /) — I10."""
    load_matches_raw(db_con, raw_dir)
    row = db_con.execute("""
        SELECT
            COUNT(*) FILTER (WHERE filename LIKE '/%') AS abs_count,
            COUNT(*) FILTER (WHERE filename NOT LIKE '%/%') AS bare_count
        FROM matches_raw
    """).fetchone()
    assert row is not None
    assert row[0] == 0, f"absolute paths found: {row[0]}"
    assert row[1] == 0, f"bare basenames found: {row[1]}"


def test_load_matches_raw_idempotent(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """Running load_matches_raw twice with should_drop=True gives same row count."""
    n1 = load_matches_raw(db_con, raw_dir, should_drop=True)
    n2 = load_matches_raw(db_con, raw_dir, should_drop=True)
    assert n1 == n2
    assert n1 > 0


def test_load_matches_raw_no_drop_raises_on_existing(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """With should_drop=False, a second call raises because table already exists."""
    load_matches_raw(db_con, raw_dir, should_drop=True)
    with pytest.raises(Exception):
        load_matches_raw(db_con, raw_dir, should_drop=False)


# ── load_ratings_raw ──────────────────────────────────────────────────────────


def test_load_ratings_raw_auto_detect(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """auto_detect strategy must produce a ratings_raw table with filename column."""
    decision = DtypeDecision(
        strategy="auto_detect",
        rationale="test: auto_detect",
    )
    n = load_ratings_raw(db_con, raw_dir, decision=decision)
    assert n >= 0  # sparse file may contribute 0 rows
    cols = [row[0] for row in db_con.execute("DESCRIBE ratings_raw").fetchall()]
    assert "filename" in cols


def test_load_ratings_raw_explicit_map_applied(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """Explicit dtype map is applied to ratings_raw without error."""
    decision = DtypeDecision(
        strategy="explicit",
        rationale="test: explicit",
        dtype_map={
            "profile_id": "BIGINT",
            "games": "INTEGER",
            "rating": "INTEGER",
            "date": "TIMESTAMP",
            "leaderboard_id": "INTEGER",
            "rating_diff": "INTEGER",
            "season": "INTEGER",
        },
    )
    n = load_ratings_raw(db_con, raw_dir, decision=decision)
    assert n >= 0
    cols = [row[0] for row in db_con.execute("DESCRIBE ratings_raw").fetchall()]
    assert "filename" in cols
    # Verify the explicit type was applied to profile_id
    type_map = {
        row[0]: row[1] for row in db_con.execute("DESCRIBE ratings_raw").fetchall()
    }
    assert type_map.get("profile_id") is not None


def test_load_ratings_raw_invalid_strategy_raises(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """Unknown dtype strategy must raise ValueError."""
    decision = DtypeDecision(strategy="magic", rationale="invalid")
    with pytest.raises(ValueError, match="Unknown dtype strategy"):
        load_ratings_raw(db_con, raw_dir, decision=decision)


# ── load_leaderboards_raw ─────────────────────────────────────────────────────


def test_load_leaderboards_raw_creates_table_with_filename(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    n = load_leaderboards_raw(db_con, raw_dir)
    assert n > 0
    cols = [row[0] for row in db_con.execute("DESCRIBE leaderboards_raw").fetchall()]
    assert "filename" in cols


# ── load_profiles_raw ─────────────────────────────────────────────────────────


def test_load_profiles_raw_creates_table_with_filename(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    n = load_profiles_raw(db_con, raw_dir)
    assert n > 0
    cols = [row[0] for row in db_con.execute("DESCRIBE profiles_raw").fetchall()]
    assert "filename" in cols


# ── load_all_raw_tables ───────────────────────────────────────────────────────


def test_load_all_raw_tables_returns_per_table_counts(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """load_all_raw_tables must return a dict with all four table names."""
    decision = DtypeDecision(strategy="auto_detect", rationale="test")
    counts = load_all_raw_tables(db_con, raw_dir, decision=decision)
    assert set(counts.keys()) == {
        "matches_raw",
        "ratings_raw",
        "leaderboards_raw",
        "profiles_raw",
    }
    # All tables must have been created
    tables = [row[0] for row in db_con.execute("SHOW TABLES").fetchall()]
    for table in counts:
        assert table in tables


# ── Real fixture: sparse + dense union ───────────────────────────────────────


def test_rating_csv_union_real_sparse_and_dense_files(
    db_con: duckdb.DuckDBPyConnection,
    tmp_path: Path,
) -> None:
    """Union of real sparse and dense fixture CSVs must yield 2 distinct filenames."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    sparse = fixtures_dir / "rating-2020-08-01-sparse.csv"
    dense = fixtures_dir / "rating-2025-06-27-dense.csv"

    if not sparse.exists() or not dense.exists():
        pytest.skip("Fixture files not present")

    # Copy to tmp_path so DuckDB sees unique filenames in the glob path
    import shutil

    raw = tmp_path / "raw" / "ratings"
    raw.mkdir(parents=True)
    shutil.copy(sparse, raw / "rating-2020-08-01.csv")
    shutil.copy(dense, raw / "rating-2025-06-27.csv")

    # Build a minimal raw_dir with a ratings subdir
    raw_root = tmp_path / "raw"

    decision = DtypeDecision(strategy="auto_detect", rationale="real fixture test")
    # Use a fresh connection per this test
    con = duckdb.connect(":memory:")
    load_ratings_raw(con, raw_root, decision=decision)

    row = con.execute(
        "SELECT count(DISTINCT filename) AS files FROM ratings_raw"
    ).fetchone()
    assert row is not None
    assert row[0] == 2, f"Expected 2 distinct filenames, got {row[0]}"
