"""Raw CTAS ingestion for aoestats into DuckDB.

Materialises three append-only raw tables from the weekly dump files:
- matches_raw   — one row per match per week, from weekly match parquets
- players_raw   — one row per player per match per week, from weekly player parquets
- overviews_raw — singleton snapshot from overview/overview.json

All tables carry a ``filename`` provenance column populated by
``filename = true`` on the source read. Removing this column in any
downstream view is forbidden (INVARIANT I7, I10).

matches_raw and players_raw use file-level batching (CREATE + INSERT BY NAME)
to avoid OOM on the full 171-file / 107.6M-row players set. Per-batch peak
RSS stays well under machine memory limits.

Invariant I10 (relative filenames) is enforced inline via ``SELECT * REPLACE``
during each batch — never via a post-load UPDATE, which would OOM on 107.6M rows.

Files follow the naming pattern: {start_date}_{end_date}_{type}.parquet
"""

import glob as glob_module
import logging
from pathlib import Path

import duckdb

logger = logging.getLogger(__name__)

# ── SQL constants ─────────────────────────────────────────────────────────────

_DROP_IF_EXISTS_QUERY = "DROP TABLE IF EXISTS {table}"

# First-batch CTAS — establishes schema from the initial file set.
# SELECT * REPLACE inlines I10 relativization: no post-load UPDATE needed.
# prefix_len = len(str(raw_dir)) + 2  (+1 for 1-based substr, +1 for trailing /)
_MATCHES_RAW_CREATE_QUERY = """
CREATE TABLE matches_raw AS
SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)
FROM read_parquet(
    {file_list},
    union_by_name = true,
    filename = true
)
"""

# Subsequent batches — BY NAME aligns columns and fills missing ones with NULL.
_MATCHES_RAW_INSERT_QUERY = """
INSERT INTO matches_raw BY NAME
SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)
FROM read_parquet(
    {file_list},
    union_by_name = true,
    filename = true
)
"""

_PLAYERS_RAW_CREATE_QUERY = """
CREATE TABLE players_raw AS
SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)
FROM read_parquet(
    {file_list},
    union_by_name = true,
    filename = true
)
"""

_PLAYERS_RAW_INSERT_QUERY = """
INSERT INTO players_raw BY NAME
SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)
FROM read_parquet(
    {file_list},
    union_by_name = true,
    filename = true
)
"""

# overviews_raw is 1 row — UPDATE-based relativization is fine here.
_OVERVIEWS_RAW_QUERY = """
CREATE TABLE overviews_raw AS
SELECT * FROM read_json_auto('{path}', filename = true)
"""

_COUNT_QUERY = "SELECT count(*) FROM {table}"

# Used only for overviews_raw (1 row — no OOM risk).
# prefix_len = len(str(raw_dir)) + 2  (+1 for 1-based substr, +1 for trailing /)
_RELATIVIZE_FILENAME_QUERY = (
    "UPDATE {table} SET filename = substr(filename, {prefix_len})"
)


def _file_list_literal(files: list[str]) -> str:
    """Format a list of file paths as a DuckDB array literal.

    Args:
        files: Absolute file paths to format.

    Returns:
        SQL array literal string e.g. ``['path/a', 'path/b']``.
    """
    quoted = ", ".join(f"'{p}'" for p in files)
    return f"[{quoted}]"


def _relativize_filenames(
    con: duckdb.DuckDBPyConnection, table: str, raw_dir: Path
) -> None:
    """Strip raw_dir prefix from the filename column to make paths relative (I10).

    Args:
        con: Active DuckDB connection.
        table: Table whose filename column to update.
        raw_dir: The raw data directory whose path to strip.
    """
    prefix_len = len(str(raw_dir)) + 2
    con.execute(_RELATIVIZE_FILENAME_QUERY.format(table=table, prefix_len=prefix_len))


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
    batch_size: int = 10,
) -> int:
    """Materialise matches_raw from all weekly match parquet files.

    Loads in file-level batches to avoid OOM on large datasets. The first
    batch creates the table; subsequent batches use INSERT BY NAME so that
    variant columns (present in some weeks but not others) are filled with
    NULL rather than causing a schema mismatch.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory (contains matches/ subdir).
        should_drop: If True, drop existing matches_raw before creating.
        batch_size: Number of parquet files to load per batch.

    Returns:
        Row count in matches_raw after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="matches_raw"))
        logger.info("Dropped existing matches_raw table.")

    files = sorted(glob_module.glob(str(raw_dir / "matches" / "*_matches.parquet")))
    if not files:
        raise FileNotFoundError(f"No match parquet files found under {raw_dir / 'matches'}")

    total = len(files)
    prefix_len = len(str(raw_dir)) + 2
    logger.info("matches_raw: loading %d files in batches of %d", total, batch_size)

    first_batch = _file_list_literal(files[:batch_size])
    con.execute(_MATCHES_RAW_CREATE_QUERY.format(file_list=first_batch, prefix_len=prefix_len))

    for start in range(batch_size, total, batch_size):
        batch = _file_list_literal(files[start:start + batch_size])
        con.execute(_MATCHES_RAW_INSERT_QUERY.format(file_list=batch, prefix_len=prefix_len))
        logger.info(
            "matches_raw: loaded files %d–%d / %d",
            start, min(start + batch_size, total), total
        )

    n = _count_rows(con, "matches_raw")
    logger.info("matches_raw: %d rows from %d files", n, total)
    return n


def load_players_raw(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    should_drop: bool = True,
    batch_size: int = 10,
) -> int:
    """Materialise players_raw from all weekly player parquet files.

    Loads in file-level batches to avoid OOM. The full 171-file / 107.6M-row
    dataset exceeds machine memory in a single CTAS. Batching of 20 files
    (~12.6M rows per batch) keeps peak RSS manageable.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory (contains players/ subdir).
        should_drop: If True, drop existing players_raw before creating.
        batch_size: Number of parquet files to load per batch.

    Returns:
        Row count in players_raw after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="players_raw"))
        logger.info("Dropped existing players_raw table.")

    files = sorted(glob_module.glob(str(raw_dir / "players" / "*_players.parquet")))
    if not files:
        raise FileNotFoundError(f"No player parquet files found under {raw_dir / 'players'}")

    total = len(files)
    prefix_len = len(str(raw_dir)) + 2
    logger.info("players_raw: loading %d files in batches of %d", total, batch_size)

    first_batch = _file_list_literal(files[:batch_size])
    con.execute(_PLAYERS_RAW_CREATE_QUERY.format(file_list=first_batch, prefix_len=prefix_len))

    for start in range(batch_size, total, batch_size):
        batch = _file_list_literal(files[start:start + batch_size])
        con.execute(_PLAYERS_RAW_INSERT_QUERY.format(file_list=batch, prefix_len=prefix_len))
        logger.info(
            "players_raw: loaded files %d–%d / %d",
            start, min(start + batch_size, total), total
        )

    n = _count_rows(con, "players_raw")
    logger.info("players_raw: %d rows from %d files", n, total)
    return n


def load_overviews_raw(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    should_drop: bool = True,
) -> int:
    """Materialise overviews_raw from the singleton overview JSON.

    Args:
        con: Active DuckDB connection.
        raw_dir: Path to the raw data directory (contains overview/ subdir).
        should_drop: If True, drop existing overviews_raw before creating.

    Returns:
        Row count in overviews_raw after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="overviews_raw"))
        logger.info("Dropped existing overviews_raw table.")

    path = str(raw_dir / "overview" / "overview.json")
    con.execute(_OVERVIEWS_RAW_QUERY.format(path=path))
    _relativize_filenames(con, "overviews_raw", raw_dir)
    n = _count_rows(con, "overviews_raw")
    logger.info("overviews_raw: %d rows from %s", n, path)
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
    counts["matches_raw"] = load_matches_raw(con, raw_dir, should_drop=should_drop)
    counts["players_raw"] = load_players_raw(con, raw_dir, should_drop=should_drop)
    counts["overviews_raw"] = load_overviews_raw(con, raw_dir, should_drop=should_drop)
    logger.info("load_all_raw_tables complete: %s", counts)
    return counts
