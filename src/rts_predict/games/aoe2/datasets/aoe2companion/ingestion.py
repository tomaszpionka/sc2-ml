"""Raw CTAS ingestion for aoe2companion into DuckDB.

Materialises four append-only raw tables from the source files:
- matches_raw      — one row per match-player, from daily match Parquets
- ratings_raw      — one row per rating record, from daily rating CSVs
- leaderboards_raw — singleton snapshot (leaderboard.parquet)
- profiles_raw     — singleton snapshot (profile.parquet)

Every table carries a ``filename`` provenance column populated by
``filename = true`` on the source read. Removing this column in any
downstream view is forbidden (INVARIANT I7, I10).

Invariant I10 (relative filenames) is enforced inline via ``SELECT * REPLACE``
in every CTAS — never via a post-load UPDATE, which would OOM on large tables.
prefix_len = len(str(raw_dir)) + 2  (+1 for 1-based substr, +1 for trailing /)

The dtype strategy for ratings_raw is supplied as a DtypeDecision
dataclass (from types.py) — callers must not hard-code an alternative.
"""

import logging
from pathlib import Path

import duckdb

from rts_predict.games.aoe2.datasets.aoe2companion.types import DtypeDecision

logger = logging.getLogger(__name__)

# ── SQL constants ─────────────────────────────────────────────────────────────

_DROP_IF_EXISTS_QUERY = "DROP TABLE IF EXISTS {table}"

# binary_as_string=true is required: match, leaderboard, and profile Parquet
# files contain 22, 4, and 11 unannotated BYTE_ARRAY columns respectively
# (no logical/converted type annotation). Without this flag DuckDB raises a
# cast error. Confirmed in Step 01_02_01 binary_column_inspection artifact.
_MATCHES_RAW_QUERY = """
CREATE TABLE matches_raw AS
SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)
FROM read_parquet(
    '{glob}',
    union_by_name = true,
    filename = true,
    binary_as_string = true
)
"""

_RATINGS_RAW_AUTO_QUERY = """
CREATE TABLE ratings_raw AS
SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)
FROM read_csv(
    '{glob}',
    union_by_name = true,
    auto_detect = true,
    filename = true
)
"""

_RATINGS_RAW_EXPLICIT_QUERY = """
CREATE TABLE ratings_raw AS
SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)
FROM read_csv(
    '{glob}',
    union_by_name = true,
    dtypes = {dtype_map},
    filename = true
)
"""

_LEADERBOARDS_RAW_QUERY = """
CREATE TABLE leaderboards_raw AS
SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)
FROM read_parquet('{path}', filename = true, binary_as_string = true)
"""

_PROFILES_RAW_QUERY = """
CREATE TABLE profiles_raw AS
SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)
FROM read_parquet('{path}', filename = true, binary_as_string = true)
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


def load_matches_raw(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    should_drop: bool = True,
) -> int:
    """Materialise matches_raw from all daily match Parquet files.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory (contains matches/ subdir).
        should_drop: If True, drop existing matches_raw before creating.

    Returns:
        Row count in matches_raw after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="matches_raw"))
        logger.info("Dropped existing matches_raw table.")

    glob = str(raw_dir / "matches" / "match-*.parquet")
    prefix_len = len(str(raw_dir)) + 2
    con.execute(_MATCHES_RAW_QUERY.format(glob=glob, prefix_len=prefix_len))
    n = _count_rows(con, "matches_raw")
    logger.info("matches_raw: %d rows from %s", n, glob)
    return n


def load_ratings_raw(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    decision: DtypeDecision,
    should_drop: bool = True,
) -> int:
    """Materialise ratings_raw from all daily rating CSV files.

    The dtype strategy (auto_detect or explicit) is taken from the
    DtypeDecision produced in Step 01_02_01 — no other path is permitted.
    Step 01_02_01 established that read_csv_auto infers all columns as
    VARCHAR at scale (2,072 files), so the explicit strategy is required
    in production.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory (contains ratings/ subdir).
        decision: DtypeDecision dataclass from Step 01_02_01.
        should_drop: If True, drop existing ratings_raw before creating.

    Returns:
        Row count in ratings_raw after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="ratings_raw"))
        logger.info("Dropped existing ratings_raw table.")

    glob = str(raw_dir / "ratings" / "rating-*.csv")
    prefix_len = len(str(raw_dir)) + 2

    if decision.strategy == "auto_detect":
        con.execute(_RATINGS_RAW_AUTO_QUERY.format(glob=glob, prefix_len=prefix_len))
    elif decision.strategy == "explicit":
        dtype_literal = (
            "{"
            + ", ".join(f"'{k}': '{v}'" for k, v in decision.dtype_map.items())
            + "}"
        )
        con.execute(_RATINGS_RAW_EXPLICIT_QUERY.format(
            glob=glob, prefix_len=prefix_len, dtype_map=dtype_literal
        ))
    else:
        raise ValueError(f"Unknown dtype strategy: {decision.strategy!r}")

    n = _count_rows(con, "ratings_raw")
    logger.info("ratings_raw: %d rows from %s (strategy=%s)", n, glob, decision.strategy)
    return n


def load_leaderboards_raw(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    should_drop: bool = True,
) -> int:
    """Materialise leaderboards_raw from the singleton leaderboard Parquet.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory.
        should_drop: If True, drop existing leaderboards_raw before creating.

    Returns:
        Row count in leaderboards_raw after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="leaderboards_raw"))
        logger.info("Dropped existing leaderboards_raw table.")

    path = str(raw_dir / "leaderboards" / "leaderboard.parquet")
    prefix_len = len(str(raw_dir)) + 2
    con.execute(_LEADERBOARDS_RAW_QUERY.format(path=path, prefix_len=prefix_len))
    n = _count_rows(con, "leaderboards_raw")
    logger.info("leaderboards_raw: %d rows", n)
    return n


def load_profiles_raw(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    should_drop: bool = True,
) -> int:
    """Materialise profiles_raw from the singleton profile Parquet.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory.
        should_drop: If True, drop existing profiles_raw before creating.

    Returns:
        Row count in profiles_raw after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="profiles_raw"))
        logger.info("Dropped existing profiles_raw table.")

    path = str(raw_dir / "profiles" / "profile.parquet")
    prefix_len = len(str(raw_dir)) + 2
    con.execute(_PROFILES_RAW_QUERY.format(path=path, prefix_len=prefix_len))
    n = _count_rows(con, "profiles_raw")
    logger.info("profiles_raw: %d rows", n)
    return n


def load_all_raw_tables(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    decision: DtypeDecision,
    should_drop: bool = True,
) -> dict[str, int]:
    """Materialise all four raw tables in the aoe2companion DuckDB.

    Convenience wrapper that calls all four load_*_raw functions in the
    canonical ingestion order: matches, ratings, leaderboards, profiles.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory.
        decision: DtypeDecision for rating CSVs (from Step 01_02_01).
        should_drop: Passed through to each individual loader.

    Returns:
        Dict mapping table name to row count.
    """
    counts: dict[str, int] = {}
    counts["matches_raw"] = load_matches_raw(con, raw_dir, should_drop=should_drop)
    counts["ratings_raw"] = load_ratings_raw(
        con, raw_dir, decision=decision, should_drop=should_drop
    )
    counts["leaderboards_raw"] = load_leaderboards_raw(con, raw_dir, should_drop=should_drop)
    counts["profiles_raw"] = load_profiles_raw(con, raw_dir, should_drop=should_drop)
    logger.info("load_all_raw_tables complete: %s", counts)
    return counts
