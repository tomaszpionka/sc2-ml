"""DuckDB view orchestration for the SC2 ML feature pipeline.

Provides utilities over the raw ingestion tables:

1. ``raw_enriched`` view — adds ``tournament_dir`` and ``replay_id`` columns
   to the ``raw`` table.
2. ``match_series`` — Best-of series grouping via a time-gap heuristic, ensuring
   no series is split across temporal folds.
3. ``match_split`` — Temporal train/val/test assignment with tournament-level
   boundaries and series integrity constraints.

Note: ``flat_players`` and ``matches_flat`` views were removed in PR #62.
Map-name resolution and race normalisation are Phase 1/2 concerns; the
``matches`` view family will be rebuilt once cleaning rules are established.
"""

import logging

import duckdb
import pandas as pd

from rts_predict.sc2.config import SERIES_GAP_SECONDS

logger = logging.getLogger(__name__)

# ── SQL query constants ───────────────────────────────────────────────────────

_RAW_ENRICHED_VIEW_QUERY = """
    CREATE OR REPLACE VIEW raw_enriched AS
    SELECT
        *,
        split_part(filename, '/', -3) AS tournament_dir,
        regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id
    FROM raw
"""

_MATCHES_WITH_SPLIT_QUERY = """
    SELECT m.*, ms.split
    FROM matches_flat m
    JOIN match_split ms ON m.match_id = ms.match_id
    {where_clause}
    ORDER BY m.match_time ASC
"""

_MATCHES_WITHOUT_SPLIT_QUERY = (
    "SELECT * FROM matches_flat WHERE match_time IS NOT NULL ORDER BY match_time ASC"
)

_SERIES_ASSIGNMENT_QUERY = """
    CREATE TABLE match_series AS
    WITH unique_matches AS (
        SELECT DISTINCT
            match_id,
            tournament_name,
            match_time,
            LEAST(p1_name, p2_name) AS player_a,
            GREATEST(p1_name, p2_name) AS player_b
        FROM matches_flat
        WHERE match_time IS NOT NULL
          AND p1_name < p2_name
    ),
    with_pair AS (
        SELECT
            *,
            player_a || '|' || player_b AS player_pair
        FROM unique_matches
    ),
    with_lag AS (
        SELECT
            match_id,
            tournament_name,
            player_pair,
            match_time,
            LAG(match_time) OVER (
                PARTITION BY tournament_name, player_pair
                ORDER BY match_time
            ) AS prev_match_time
        FROM with_pair
    ),
    with_boundary AS (
        SELECT
            match_id,
            tournament_name,
            player_pair,
            CASE
                WHEN prev_match_time IS NULL
                    OR DATEDIFF('second', prev_match_time, match_time) > {series_gap_seconds}
                THEN 1
                ELSE 0
            END AS is_new_series
        FROM with_lag
    ),
    with_series_group AS (
        SELECT
            match_id,
            tournament_name,
            player_pair,
            SUM(is_new_series) OVER (
                PARTITION BY tournament_name, player_pair
                ORDER BY match_id
                ROWS UNBOUNDED PRECEDING
            ) AS series_group
        FROM with_boundary
    )
    SELECT
        match_id,
        tournament_name || '|' || player_pair || '|' || series_group::VARCHAR
            AS series_id
    FROM with_series_group
"""

_SERIES_OTHER_PERSPECTIVE_QUERY = """
    INSERT INTO match_series
    SELECT DISTINCT m.match_id, ms.series_id
    FROM matches_flat m
    JOIN match_series ms ON m.match_id = ms.match_id
    WHERE m.match_id NOT IN (SELECT match_id FROM match_series)
"""

def create_raw_enriched_view(con: duckdb.DuckDBPyConnection) -> None:
    """Create the raw_enriched view with tournament_dir and replay_id columns."""
    con.execute(_RAW_ENRICHED_VIEW_QUERY)
    logger.info("Created raw_enriched view.")


def get_matches_dataframe(
    con: duckdb.DuckDBPyConnection,
    split: str | None = None,
) -> pd.DataFrame:
    """Fetch matches_flat into a Pandas DataFrame, sorted by match time.

    If the ``match_split`` table exists and ``split`` is provided, only rows
    belonging to that split are returned.  If ``split`` is ``None`` but the
    table exists, a ``split`` column is attached to every row.

    Args:
        con: DuckDB connection.
        split: Optional split filter (``'train'``, ``'val'``, or ``'test'``).
    """
    # Check whether the match_split table exists
    row = con.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_name = 'match_split'"
    ).fetchone()
    assert row is not None
    has_split_table = row[0] > 0

    _VALID_SPLITS = {"train", "val", "test"}

    params: list[str] = []
    if has_split_table:
        if split is not None:
            if split not in _VALID_SPLITS:
                raise ValueError(
                    f"Invalid split '{split}', must be one of {sorted(_VALID_SPLITS)}"
                )
            where_clause = "WHERE m.match_time IS NOT NULL AND ms.split = ?"
            params = [split]
        else:
            where_clause = "WHERE m.match_time IS NOT NULL"
        query = _MATCHES_WITH_SPLIT_QUERY.format(where_clause=where_clause)
    else:
        if split is not None:
            logger.warning(
                "match_split table does not exist — ignoring split filter. "
                "Run create_temporal_split() first."
            )
        query = _MATCHES_WITHOUT_SPLIT_QUERY

    logger.info(f"Loading matches_flat into Pandas (split={split})...")
    return con.execute(query, params).df()


def assign_series_ids(con: duckdb.DuckDBPyConnection) -> None:
    """Create a ``match_series`` table assigning each match to a best-of series.

    Uses a heuristic: matches between the same two players within the same
    tournament, with ``match_time`` gaps under ``SERIES_GAP_SECONDS`` (2 h),
    belong to the same series.  The canonical player pair is ordered
    alphabetically so that (A, B) and (B, A) are treated identically.

    Requires the ``matches_flat`` view to exist (including ``match_time``).
    """
    logger.info("Assigning series IDs to matches...")

    con.execute("DROP TABLE IF EXISTS match_series")
    con.execute(_SERIES_ASSIGNMENT_QUERY.format(series_gap_seconds=SERIES_GAP_SECONDS))
    con.execute(_SERIES_OTHER_PERSPECTIVE_QUERY)

    row = con.execute(
        "SELECT count(DISTINCT series_id) FROM match_series"
    ).fetchone()
    assert row is not None
    series_count = row[0]
    row = con.execute("SELECT count(*) FROM match_series").fetchone()
    assert row is not None
    match_count = row[0]
    logger.info(
        f"Series assignment complete: {match_count} matches in {series_count} series."
    )


