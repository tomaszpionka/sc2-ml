"""Raw CTAS ingestion for aoestats into DuckDB.

Materialises three append-only raw tables from the weekly dump files:
- raw_matches   — one row per match per week, from weekly match parquets
- raw_players   — one row per player per match per week, from weekly player parquets
- raw_overviews — singleton snapshot from overview/overview.json

All tables carry a ``filename`` provenance column populated by
``filename = true`` on the source read. Removing this column in any
downstream view is forbidden (INVARIANT I7).

Files follow the naming pattern: {start_date}_{end_date}_{type}.parquet
"""

import logging
from pathlib import Path

import duckdb

logger = logging.getLogger(__name__)

# ── SQL constants ─────────────────────────────────────────────────────────────

_DROP_IF_EXISTS_QUERY = "DROP TABLE IF EXISTS {table}"

_RAW_MATCHES_QUERY = """
CREATE TABLE raw_matches AS
SELECT * FROM read_parquet(
    '{glob}',
    union_by_name = true,
    filename = true
)
"""

_RAW_PLAYERS_QUERY = """
CREATE TABLE raw_players AS
SELECT * FROM read_parquet(
    '{glob}',
    union_by_name = true,
    filename = true
)
"""

_RAW_OVERVIEWS_QUERY = """
CREATE TABLE raw_overviews AS
SELECT * FROM read_json_auto('{path}', filename = true)
"""

_COUNT_QUERY = "SELECT count(*) FROM {table}"


def _count_rows(con: duckdb.DuckDBPyConnection, table: str) -> int:
    """Return the row count for a table.

    Args:
        con: Active DuckDB connection.
        table: Table name to count.

    Returns:
        Integer row count.
    """
    row = con.execute(_COUNT_QUERY.format(table=table)).fetchone()
    assert row is not None
    return int(row[0])


def load_raw_matches(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    should_drop: bool = True,
) -> int:
    """Materialise raw_matches from all weekly match parquet files.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory (contains matches/ subdir).
        should_drop: If True, drop existing raw_matches before creating.

    Returns:
        Row count in raw_matches after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="raw_matches"))
        logger.info("Dropped existing raw_matches table.")

    glob = str(raw_dir / "matches" / "*_matches.parquet")
    con.execute(_RAW_MATCHES_QUERY.format(glob=glob))
    n = _count_rows(con, "raw_matches")
    logger.info("raw_matches: %d rows from %s", n, glob)
    return n


def load_raw_players(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    should_drop: bool = True,
) -> int:
    """Materialise raw_players from all weekly player parquet files.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory (contains players/ subdir).
        should_drop: If True, drop existing raw_players before creating.

    Returns:
        Row count in raw_players after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="raw_players"))
        logger.info("Dropped existing raw_players table.")

    glob = str(raw_dir / "players" / "*_players.parquet")
    con.execute(_RAW_PLAYERS_QUERY.format(glob=glob))
    n = _count_rows(con, "raw_players")
    logger.info("raw_players: %d rows from %s", n, glob)
    return n


def load_raw_overviews(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    should_drop: bool = True,
) -> int:
    """Materialise raw_overviews from the singleton overview JSON.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory (contains overview/ subdir).
        should_drop: If True, drop existing raw_overviews before creating.

    Returns:
        Row count in raw_overviews after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="raw_overviews"))
        logger.info("Dropped existing raw_overviews table.")

    path = str(raw_dir / "overview" / "overview.json")
    con.execute(_RAW_OVERVIEWS_QUERY.format(path=path))
    n = _count_rows(con, "raw_overviews")
    logger.info("raw_overviews: %d rows from %s", n, path)
    return n


def load_all_raw_tables(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    should_drop: bool = True,
) -> dict[str, int]:
    """Materialise all three raw tables in the aoestats DuckDB.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory.
        should_drop: Passed through to each individual loader.

    Returns:
        Dict mapping table name to row count.
    """
    counts: dict[str, int] = {}
    counts["raw_matches"] = load_raw_matches(con, raw_dir, should_drop=should_drop)
    counts["raw_players"] = load_raw_players(con, raw_dir, should_drop=should_drop)
    counts["raw_overviews"] = load_raw_overviews(con, raw_dir, should_drop=should_drop)
    logger.info("load_all_raw_tables complete: %s", counts)
    return counts
