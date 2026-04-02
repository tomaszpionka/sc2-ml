import logging

import duckdb
import pandas as pd

from sc2ml.config import SERIES_GAP_SECONDS, TEST_RATIO, TRAIN_RATIO, VAL_RATIO

logger = logging.getLogger(__name__)


def create_ml_views(con: duckdb.DuckDBPyConnection) -> None:
    """Create the two DuckDB views used by the ML pipeline.

    flat_players  — one row per player per match, with map translations applied
                    and casters (no Win/Loss result) excluded.
    matches_flat  — one row per player-pair perspective per match (2 rows per
                    unique match_id), used as the primary ML input table.
    """
    logger.info(
        "Creating ML views in DuckDB (map translations + player name unification)..."
    )

    # flat_players: LEFT JOIN to map_translation so foreign map names are normalised to English
    query_flat_players = """
    CREATE OR REPLACE VIEW flat_players AS
    SELECT
        filename AS match_id,
        split_part(filename, '/', -3) AS tournament_name,
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
    FROM raw
    LEFT JOIN map_translation mt ON mt.foreign_name = (metadata->>'$.mapName'),
         LATERAL json_each(ToonPlayerDescMap) AS entry
    WHERE player_name IS NOT NULL AND player_name != ''
      AND (entry.value->>'$.result') IN ('Win', 'Loss')  -- excludes casters and observers
    """
    con.execute(query_flat_players)

    # matches_flat: pair players within the same match to produce one row per perspective
    query_matches = """
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
    con.execute(query_matches)
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

    if has_split_table:
        where_clause = "WHERE m.match_time IS NOT NULL"
        if split is not None:
            if split not in _VALID_SPLITS:
                raise ValueError(
                    f"Invalid split '{split}', must be one of {sorted(_VALID_SPLITS)}"
                )
            where_clause += f" AND ms.split = '{split}'"
        query = f"""
            SELECT m.*, ms.split
            FROM matches_flat m
            JOIN match_split ms ON m.match_id = ms.match_id
            {where_clause}
            ORDER BY m.match_time ASC
        """
    else:
        if split is not None:
            logger.warning(
                "match_split table does not exist — ignoring split filter. "
                "Run create_temporal_split() first."
            )
        query = (
            "SELECT * FROM matches_flat "
            "WHERE match_time IS NOT NULL ORDER BY match_time ASC"
        )

    logger.info(f"Loading matches_flat into Pandas (split={split})...")
    return con.execute(query).df()


def validate_data_split_sql(con: duckdb.DuckDBPyConnection, split_ratio: float = 0.8) -> None:
    """Log temporal split statistics and validate chronological ordering.

    Prints the year distribution of matches and confirms that the train/test
    boundary is strictly chronological (no future data leaks into training).
    """
    logger.info(
        f"====== DATA VALIDATION (Split {int(split_ratio * 100)}/{int((1 - split_ratio) * 100)}) ======"
    )

    # Year distribution
    query_dist = """
    SELECT
        EXTRACT(year FROM match_time) as year,
        COUNT(*) as total_matches,
        ROUND(COUNT(*) * 100.0 / (SUM(COUNT(*)) OVER()), 2) as pct_of_total
    FROM matches_flat
    GROUP BY year ORDER BY year;
    """
    dist_df = con.execute(query_dist).df()
    logger.info(f"\nAnnual match distribution:\n{dist_df.to_string(index=False)}")

    # Chronological split validation
    query_leakage = f"""
    WITH split_point AS (
        SELECT match_time FROM matches_flat
        ORDER BY match_time ASC
        LIMIT 1 OFFSET (SELECT CAST(COUNT(*) * {split_ratio} AS INT) FROM matches_flat)
    )
    SELECT
        (SELECT COUNT(*) FROM matches_flat WHERE match_time < (SELECT match_time FROM split_point)) as train_count,
        (SELECT COUNT(*) FROM matches_flat WHERE match_time >= (SELECT match_time FROM split_point)) as test_count,
        (SELECT MIN(match_time) FROM matches_flat WHERE match_time >= (SELECT match_time FROM split_point)) as min_test_time,
        (SELECT MAX(match_time) FROM matches_flat WHERE match_time < (SELECT match_time FROM split_point)) as max_train_time,
        ((SELECT MIN(match_time) FROM matches_flat WHERE match_time >= (SELECT match_time FROM split_point)) >
         (SELECT MAX(match_time) FROM matches_flat WHERE match_time < (SELECT match_time FROM split_point))) as is_chronological_valid;
    """
    leakage_res = con.execute(query_leakage).df()

    valid = leakage_res["is_chronological_valid"].iloc[0]
    logger.info(
        f"Actual split: Train={leakage_res['train_count'].iloc[0]}, "
        f"Test={leakage_res['test_count'].iloc[0]}"
    )
    logger.info(f"Chronological validation: {'PASSED' if valid else 'FAILED!'}")
    logger.info(f"Last training match:  {leakage_res['max_train_time'].iloc[0]}")
    logger.info(f"First test match:     {leakage_res['min_test_time'].iloc[0]}")
    logger.info("======================================================")


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
    con.execute(f"""
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
                        OR DATEDIFF('second', prev_match_time, match_time) > {SERIES_GAP_SECONDS}
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
    """)

    # Also assign the "other perspective" rows (p2 < p1) to the same series
    con.execute("""
        INSERT INTO match_series
        SELECT DISTINCT m.match_id, ms.series_id
        FROM matches_flat m
        JOIN match_series ms ON m.match_id = ms.match_id
        WHERE m.match_id NOT IN (SELECT match_id FROM match_series)
    """)

    series_count = con.execute(
        "SELECT count(DISTINCT series_id) FROM match_series"
    ).fetchone()[0]
    match_count = con.execute("SELECT count(*) FROM match_series").fetchone()[0]
    logger.info(
        f"Series assignment complete: {match_count} matches in {series_count} series."
    )


def create_temporal_split(
    con: duckdb.DuckDBPyConnection,
    train_ratio: float = TRAIN_RATIO,
    val_ratio: float = VAL_RATIO,
    test_ratio: float = TEST_RATIO,
) -> None:
    """Create a ``match_split`` table assigning each match to train/val/test.

    The split is temporal (by ``match_time``) with series-aware boundary
    snapping: all games within the same series are guaranteed to be in the
    same split.  Requires ``match_series`` table (run ``assign_series_ids``
    first).

    Args:
        con: DuckDB connection.
        train_ratio: Fraction of matches for training.
        val_ratio: Fraction of matches for validation.
        test_ratio: Fraction of matches for testing.
    """
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        raise ValueError(
            f"Split ratios must sum to 1.0, got {train_ratio + val_ratio + test_ratio}"
        )

    logger.info(
        f"Creating temporal split: train={train_ratio}, val={val_ratio}, test={test_ratio}"
    )

    # Get series sorted by earliest match time, with match counts
    series_df = con.execute("""
        SELECT
            ms.series_id,
            MIN(m.match_time) AS first_match_time,
            COUNT(DISTINCT ms.match_id) AS match_count
        FROM match_series ms
        JOIN matches_flat m ON ms.match_id = m.match_id
        WHERE m.match_time IS NOT NULL
          AND m.p1_name < m.p2_name  -- deduplicate perspectives
        GROUP BY ms.series_id
        ORDER BY first_match_time ASC
    """).df()

    total_matches = series_df["match_count"].sum()
    train_target = int(total_matches * train_ratio)
    val_target = int(total_matches * (train_ratio + val_ratio))

    # Assign splits at series boundaries
    cumulative = 0
    split_assignments: list[tuple[str, str]] = []
    for _, row in series_df.iterrows():
        series_id = row["series_id"]
        count = row["match_count"]

        if cumulative < train_target:
            assigned_split = "train"
        elif cumulative < val_target:
            assigned_split = "val"
        else:
            assigned_split = "test"

        split_assignments.append((series_id, assigned_split))
        cumulative += count

    # Build the match_split table
    split_df = pd.DataFrame(split_assignments, columns=["series_id", "split"])

    con.execute("DROP TABLE IF EXISTS match_split")
    con.execute("""
        CREATE TABLE match_split AS
        SELECT ms.match_id, s.split
        FROM match_series ms
        JOIN split_df s ON ms.series_id = s.series_id
    """)

    # Log split statistics
    stats = con.execute("""
        SELECT
            ms.split,
            COUNT(*) AS match_count,
            MIN(m.match_time) AS earliest,
            MAX(m.match_time) AS latest
        FROM match_split ms
        JOIN matches_flat m ON ms.match_id = m.match_id
        WHERE m.p1_name < m.p2_name  -- deduplicate
        GROUP BY ms.split
        ORDER BY earliest
    """).df()
    logger.info(f"Temporal split created:\n{stats.to_string(index=False)}")


def validate_temporal_split(con: duckdb.DuckDBPyConnection) -> None:
    """Validate the ``match_split`` table for temporal ordering and leakage.

    Checks:
    1. No ``match_time`` overlap between train/val/test.
    2. All games from the same ``series_id`` are in the same split.
    3. Year distribution per split.
    4. Split size percentages.
    """
    logger.info("====== TEMPORAL SPLIT VALIDATION ======")

    # 1. Chronological ordering — no overlap between splits
    boundaries = con.execute("""
        SELECT
            ms.split,
            MIN(m.match_time) AS min_time,
            MAX(m.match_time) AS max_time,
            COUNT(DISTINCT ms.match_id) AS match_count
        FROM match_split ms
        JOIN matches_flat m ON ms.match_id = m.match_id
        WHERE m.p1_name < m.p2_name
        GROUP BY ms.split
        ORDER BY min_time
    """).df()

    logger.info(f"Split boundaries:\n{boundaries.to_string(index=False)}")

    splits = boundaries.set_index("split")
    if "train" in splits.index and "val" in splits.index:
        train_max = splits.loc["train", "max_time"]
        val_min = splits.loc["val", "min_time"]
        train_val_ok = train_max < val_min
        logger.info(
            f"Train/Val boundary: train_max={train_max}, val_min={val_min} "
            f"→ {'PASSED' if train_val_ok else 'FAILED!'}"
        )
    if "val" in splits.index and "test" in splits.index:
        val_max = splits.loc["val", "max_time"]
        test_min = splits.loc["test", "min_time"]
        val_test_ok = val_max < test_min
        logger.info(
            f"Val/Test boundary: val_max={val_max}, test_min={test_min} "
            f"→ {'PASSED' if val_test_ok else 'FAILED!'}"
        )

    # 2. Series integrity — no series spans multiple splits
    split_series_check = con.execute("""
        SELECT ms2.series_id, COUNT(DISTINCT ms1.split) AS split_count
        FROM match_split ms1
        JOIN match_series ms2 ON ms1.match_id = ms2.match_id
        GROUP BY ms2.series_id
        HAVING split_count > 1
    """).df()

    if len(split_series_check) == 0:
        logger.info("Series integrity: PASSED (no series spans multiple splits)")
    else:
        logger.warning(
            f"Series integrity: FAILED! {len(split_series_check)} series span "
            f"multiple splits:\n{split_series_check.head(10).to_string(index=False)}"
        )

    # 3. Year distribution per split
    year_dist = con.execute("""
        SELECT
            ms.split,
            EXTRACT(year FROM m.match_time) AS year,
            COUNT(*) AS matches
        FROM match_split ms
        JOIN matches_flat m ON ms.match_id = m.match_id
        WHERE m.p1_name < m.p2_name
        GROUP BY ms.split, year
        ORDER BY year, ms.split
    """).df()
    logger.info(f"Year distribution per split:\n{year_dist.to_string(index=False)}")

    # 4. Split size percentages
    total = boundaries["match_count"].sum()
    for _, row in boundaries.iterrows():
        pct = row["match_count"] / total * 100
        logger.info(f"  {row['split']}: {row['match_count']} matches ({pct:.1f}%)")

    logger.info("====== END VALIDATION ======")
