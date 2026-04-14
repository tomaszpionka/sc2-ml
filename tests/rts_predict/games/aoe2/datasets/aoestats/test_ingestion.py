"""Tests for aoestats ingestion.py — CTAS functions."""

from pathlib import Path

import duckdb
import pytest

from rts_predict.games.aoe2.datasets.aoestats.ingestion import (
    load_all_raw_tables,
    load_matches_raw,
    load_overviews_raw,
    load_players_raw,
)


def test_load_matches_raw_creates_table_with_filename(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """matches_raw table must exist and have a 'filename' column."""
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


def test_load_players_raw_creates_table_with_filename(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """players_raw table must exist and have a 'filename' column."""
    n = load_players_raw(db_con, raw_dir)
    assert n > 0
    cols = [row[0] for row in db_con.execute("DESCRIBE players_raw").fetchall()]
    assert "filename" in cols


def test_load_overviews_raw_creates_table_with_filename(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """overviews_raw table must exist and have a 'filename' column."""
    n = load_overviews_raw(db_con, raw_dir)
    assert n > 0
    cols = [row[0] for row in db_con.execute("DESCRIBE overviews_raw").fetchall()]
    assert "filename" in cols


def test_load_all_raw_tables_returns_per_table_counts(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """load_all_raw_tables must return a dict with all three table names."""
    counts = load_all_raw_tables(db_con, raw_dir)
    assert set(counts.keys()) == {"matches_raw", "players_raw", "overviews_raw"}
    tables = [row[0] for row in db_con.execute("SHOW TABLES").fetchall()]
    for table in counts:
        assert table in tables


def test_load_all_raw_tables_filename_distinct(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """Both synthetic parquet files must appear as distinct filenames."""
    load_all_raw_tables(db_con, raw_dir)
    row = db_con.execute(
        "SELECT count(DISTINCT filename) FROM matches_raw"
    ).fetchone()
    assert row is not None
    assert row[0] == 2
