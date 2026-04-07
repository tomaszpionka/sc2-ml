"""Raw CTAS ingestion for aoe2companion into DuckDB.

Materialises four append-only raw tables from the source files:
- raw_matches   — one row per match-player, from daily match parquets
- raw_ratings   — one row per rating record, from daily rating CSVs
- raw_leaderboard — singleton snapshot (leaderboard.parquet)
- raw_profiles  — singleton snapshot (profile.parquet)

Every table carries a ``filename`` provenance column populated by
``filename = true`` on the source read. Removing this column in any
downstream view is forbidden (INVARIANT I7).

The dtype strategy for raw_ratings is supplied as a DtypeDecision
dataclass (from types.py) — callers must not hard-code an alternative.
"""

import logging
from pathlib import Path

import duckdb

from rts_predict.aoe2.data.aoe2companion.types import DtypeDecision

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

_RAW_RATINGS_AUTO_QUERY = """
CREATE TABLE raw_ratings AS
SELECT * FROM read_csv(
    '{glob}',
    union_by_name = true,
    auto_detect = true,
    filename = true
)
"""

_RAW_RATINGS_EXPLICIT_QUERY = """
CREATE TABLE raw_ratings AS
SELECT * FROM read_csv(
    '{glob}',
    union_by_name = true,
    dtypes = {dtype_map},
    filename = true
)
"""

_RAW_LEADERBOARD_QUERY = """
CREATE TABLE raw_leaderboard AS
SELECT * FROM read_parquet('{path}', filename = true)
"""

_RAW_PROFILES_QUERY = """
CREATE TABLE raw_profiles AS
SELECT * FROM read_parquet('{path}', filename = true)
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
    """Materialise raw_matches from all daily match parquet files.

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

    glob = str(raw_dir / "matches" / "match-*.parquet")
    con.execute(_RAW_MATCHES_QUERY.format(glob=glob))
    n = _count_rows(con, "raw_matches")
    logger.info("raw_matches: %d rows from %s", n, glob)
    return n


def load_raw_ratings(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    decision: DtypeDecision,
    should_drop: bool = True,
) -> int:
    """Materialise raw_ratings from all daily rating CSV files.

    The dtype strategy (auto_detect or explicit) is taken from the
    DtypeDecision produced in Step 0.3 — no other path is permitted.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory (contains ratings/ subdir).
        decision: DtypeDecision dataclass from profile_rating_schema().
        should_drop: If True, drop existing raw_ratings before creating.

    Returns:
        Row count in raw_ratings after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="raw_ratings"))
        logger.info("Dropped existing raw_ratings table.")

    glob = str(raw_dir / "ratings" / "rating-*.csv")

    if decision.strategy == "auto_detect":
        con.execute(_RAW_RATINGS_AUTO_QUERY.format(glob=glob))
    elif decision.strategy == "explicit":
        # Build DuckDB-compatible dtype map literal: {'col': 'TYPE', ...}
        dtype_literal = (
            "{"
            + ", ".join(f"'{k}': '{v}'" for k, v in decision.dtype_map.items())
            + "}"
        )
        con.execute(_RAW_RATINGS_EXPLICIT_QUERY.format(glob=glob, dtype_map=dtype_literal))
    else:
        raise ValueError(f"Unknown dtype strategy: {decision.strategy!r}")

    n = _count_rows(con, "raw_ratings")
    logger.info("raw_ratings: %d rows from %s (strategy=%s)", n, glob, decision.strategy)
    return n


def load_raw_leaderboard(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    should_drop: bool = True,
) -> int:
    """Materialise raw_leaderboard from the singleton leaderboard parquet.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory.
        should_drop: If True, drop existing raw_leaderboard before creating.

    Returns:
        Row count in raw_leaderboard after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="raw_leaderboard"))
        logger.info("Dropped existing raw_leaderboard table.")

    path = str(raw_dir / "leaderboards" / "leaderboard.parquet")
    con.execute(_RAW_LEADERBOARD_QUERY.format(path=path))
    n = _count_rows(con, "raw_leaderboard")
    logger.info("raw_leaderboard: %d rows", n)
    return n


def load_raw_profiles(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    should_drop: bool = True,
) -> int:
    """Materialise raw_profiles from the singleton profile parquet.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory.
        should_drop: If True, drop existing raw_profiles before creating.

    Returns:
        Row count in raw_profiles after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="raw_profiles"))
        logger.info("Dropped existing raw_profiles table.")

    path = str(raw_dir / "profiles" / "profile.parquet")
    con.execute(_RAW_PROFILES_QUERY.format(path=path))
    n = _count_rows(con, "raw_profiles")
    logger.info("raw_profiles: %d rows", n)
    return n


def load_all_raw_tables(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    decision: DtypeDecision,
    should_drop: bool = True,
) -> dict[str, int]:
    """Materialise all four raw tables in the aoe2companion DuckDB.

    Convenience wrapper that calls all four load_raw_* functions in the
    canonical ingestion order: matches, ratings, leaderboard, profiles.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory.
        decision: DtypeDecision for rating CSVs (from Step 0.3).
        should_drop: Passed through to each individual loader.

    Returns:
        Dict mapping table name to row count.
    """
    counts: dict[str, int] = {}
    counts["raw_matches"] = load_raw_matches(con, raw_dir, should_drop=should_drop)
    counts["raw_ratings"] = load_raw_ratings(
        con, raw_dir, decision=decision, should_drop=should_drop
    )
    counts["raw_leaderboard"] = load_raw_leaderboard(con, raw_dir, should_drop=should_drop)
    counts["raw_profiles"] = load_raw_profiles(con, raw_dir, should_drop=should_drop)
    logger.info("load_all_raw_tables complete: %s", counts)
    return counts
