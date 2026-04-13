"""Tests for aoestats ingestion.py — CTAS functions."""

from pathlib import Path

import duckdb
import pytest

from rts_predict.games.aoe2.datasets.aoestats.ingestion import (
    load_all_raw_tables,
    load_raw_matches,
    load_raw_overviews,
    load_raw_players,
)


def test_load_raw_matches_creates_table_with_filename(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """raw_matches table must exist and have a 'filename' column."""
    n = load_raw_matches(db_con, raw_dir)
    assert n > 0
    tables = [row[0] for row in db_con.execute("SHOW TABLES").fetchall()]
    assert "raw_matches" in tables
    cols = [row[0] for row in db_con.execute("DESCRIBE raw_matches").fetchall()]
    assert "filename" in cols


def test_load_raw_matches_idempotent(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """Running load_raw_matches twice with should_drop=True gives same row count."""
    n1 = load_raw_matches(db_con, raw_dir, should_drop=True)
    n2 = load_raw_matches(db_con, raw_dir, should_drop=True)
    assert n1 == n2
    assert n1 > 0


def test_load_raw_matches_no_drop_raises_on_existing(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """With should_drop=False, a second call raises because table already exists."""
    load_raw_matches(db_con, raw_dir, should_drop=True)
    with pytest.raises(Exception):
        load_raw_matches(db_con, raw_dir, should_drop=False)


def test_load_raw_players_creates_table_with_filename(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """raw_players table must exist and have a 'filename' column."""
    n = load_raw_players(db_con, raw_dir)
    assert n > 0
    cols = [row[0] for row in db_con.execute("DESCRIBE raw_players").fetchall()]
    assert "filename" in cols


def test_load_raw_overviews_creates_table_with_filename(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """raw_overviews table must exist and have a 'filename' column."""
    n = load_raw_overviews(db_con, raw_dir)
    assert n > 0
    cols = [row[0] for row in db_con.execute("DESCRIBE raw_overviews").fetchall()]
    assert "filename" in cols


def test_load_all_raw_tables_returns_per_table_counts(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
) -> None:
    """load_all_raw_tables must return a dict with all three table names."""
    counts = load_all_raw_tables(db_con, raw_dir)
    assert set(counts.keys()) == {"raw_matches", "raw_players", "raw_overviews"}
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
        "SELECT count(DISTINCT filename) FROM raw_matches"
    ).fetchone()
    assert row is not None
    assert row[0] == 2
