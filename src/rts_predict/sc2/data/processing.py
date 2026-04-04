"""DuckDB view orchestration for the SC2 ML feature pipeline.

Transforms raw replay JSON (loaded by ``ingestion``) into ML-ready tables:

1. ``flat_players`` — One row per player per match, with map name translations
   applied and non-player rows (casters/observers) excluded.
2. ``matches_flat`` — One row per player-pair perspective (2 rows per match),
   the primary input table for feature engineering.
3. ``match_series`` — Best-of series grouping via a time-gap heuristic, ensuring
   no series is split across temporal folds.
4. ``match_split`` — Temporal train/val/test assignment with tournament-level
   boundaries and series integrity constraints.
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

_FLAT_PLAYERS_VIEW_QUERY = """
    CREATE OR REPLACE VIEW flat_players AS
    SELECT
        filename AS match_id,
        tournament_dir AS tournament_name,
        (details->>'$.timeUTC')::TIMESTAMP AS match_time,

        (header->>'$.elapsedGameLoops')::INTEGER AS game_loops,
        (initData->>'$.gameDescription.mapSizeX')::INTEGER AS map_size_x,
        (initData->>'$.gameDescription.mapSizeY')::INTEGER AS map_size_y,
        metadata->>'$.dataBuild' AS data_build,
        metadata->>'$.gameVersion' AS game_version,
        COALESCE(mt.english_name, metadata->>'$.mapName') AS map_name,

        (entry.value->>'$.playerID')::TINYINT AS player_id,
        LOWER(entry.value->>'$.nickname') AS player_name,
        CASE entry.value->>'$.race'
            WHEN 'Terr' THEN 'Terran'
            WHEN 'Prot' THEN 'Protoss'
            ELSE entry.value->>'$.race'
        END AS race,
        (entry.value->>'$.startLocX')::INTEGER AS startLocX,
        (entry.value->>'$.startLocY')::INTEGER AS startLocY,
        (entry.value->>'$.APM')::INTEGER AS apm,
        (entry.value->>'$.SQ')::INTEGER AS sq,
        (entry.value->>'$.supplyCappedPercent')::INTEGER AS supply_capped_pct,
        (entry.value->>'$.isInClan')::BOOLEAN AS is_in_clan,

        entry.value->>'$.result' AS result
    FROM raw_enriched
    LEFT JOIN map_translation mt ON mt.foreign_name = (metadata->>'$.mapName'),
         LATERAL json_each(ToonPlayerDescMap) AS entry
    WHERE player_name IS NOT NULL AND player_name != ''
      AND (entry.value->>'$.result') IN ('Win', 'Loss')  -- excludes casters and observers
      AND (entry.value->>'$.race') NOT LIKE 'BW%'        -- excludes Brood War exhibition replays
      AND filename IN (  -- 1v1 matches only (exactly 2 Win/Loss players)
          SELECT filename FROM raw_enriched,
                 LATERAL json_each(ToonPlayerDescMap) AS e2
          WHERE (e2.value->>'$.result') IN ('Win', 'Loss')
            AND (e2.value->>'$.nickname') IS NOT NULL
            AND (e2.value->>'$.nickname') != ''
          GROUP BY filename
          HAVING COUNT(*) = 2
      )
"""

_MATCHES_FLAT_VIEW_QUERY = """
    CREATE OR REPLACE VIEW matches_flat AS
    SELECT
        p1.match_id,
        p1.match_time,
        p1.tournament_name,
        p1.game_loops,
        p1.map_size_x,
        p1.map_size_y,
        p1.data_build,
        p1.game_version,
        p1.map_name,

        p1.player_id AS p1_player_id,
        p2.player_id AS p2_player_id,

        p1.player_name AS p1_name,
        p2.player_name AS p2_name,

        p1.race AS p1_race,
        p2.race AS p2_race,

        p1.startLocX AS p1_startLocX,
        p1.startLocY AS p1_startLocY,
        p2.startLocX AS p2_startLocX,
        p2.startLocY AS p2_startLocY,

        p1.apm AS p1_apm,
        p1.sq AS p1_sq,
        p2.apm AS p2_apm,
        p2.sq AS p2_sq,

        p1.supply_capped_pct AS p1_supply_capped_pct,
        p2.supply_capped_pct AS p2_supply_capped_pct,

        p1.is_in_clan AS p1_is_in_clan,
        p2.is_in_clan AS p2_is_in_clan,

        p1.result AS p1_result
    FROM flat_players p1
    JOIN flat_players p2 ON p1.match_id = p2.match_id AND p1.player_name != p2.player_name
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

_YEAR_DISTRIBUTION_QUERY = """
    SELECT
        EXTRACT(year FROM match_time) as year,
        COUNT(*) as total_matches,
        ROUND(COUNT(*) * 100.0 / (SUM(COUNT(*)) OVER()), 2) as pct_of_total
    FROM matches_flat
    GROUP BY year ORDER BY year;
"""


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

_TOURNAMENT_GROUPING_QUERY = """
    SELECT
        tournament_name,
        MIN(match_time) AS first_match_time,
        COUNT(DISTINCT match_id) AS match_count
    FROM flat_players
    WHERE match_time IS NOT NULL
      AND result IN ('Win', 'Loss')
    GROUP BY tournament_name
    ORDER BY first_match_time ASC
"""

def create_raw_enriched_view(con: duckdb.DuckDBPyConnection) -> None:
    """Create the raw_enriched view with tournament_dir and replay_id columns."""
    con.execute(_RAW_ENRICHED_VIEW_QUERY)
    logger.info("Created raw_enriched view.")


def create_ml_views(con: duckdb.DuckDBPyConnection) -> None:
    """Create the two DuckDB views used by the ML pipeline.

    flat_players  — one row per player per match, with map translations applied
                    and casters (no Win/Loss result) excluded.
    matches_flat  — one row per player-pair perspective per match (2 rows per
                    unique match_id), used as the primary ML input table.

    Requires the ``raw_enriched`` view to exist (call
    ``create_raw_enriched_view`` first).
    """
    logger.info(
        "Creating ML views in DuckDB (map translations + player name unification)..."
    )
    con.execute(_FLAT_PLAYERS_VIEW_QUERY)
    con.execute(_MATCHES_FLAT_VIEW_QUERY)
    logger.info("View 'matches_flat' ready.")


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
    has_split_table = con.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_name = 'match_split'"
    ).fetchone()[0] > 0

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

    series_count = con.execute(
        "SELECT count(DISTINCT series_id) FROM match_series"
    ).fetchone()[0]
    match_count = con.execute("SELECT count(*) FROM match_series").fetchone()[0]
    logger.info(
        f"Series assignment complete: {match_count} matches in {series_count} series."
    )


