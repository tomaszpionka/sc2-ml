import logging
import duckdb
import pandas as pd

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
        COALESCE(mt.english_name, metadata->>'$.mapName') AS map_name,

        LOWER(entry.value->>'$.nickname') AS player_name,
        entry.value->>'$.race' AS race,
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
        p1.map_name,

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


def get_matches_dataframe(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Fetch the full matches_flat view into a Pandas DataFrame, sorted by match time."""
    logger.info("Loading matches_flat into Pandas...")
    query = "SELECT * FROM matches_flat WHERE match_time IS NOT NULL ORDER BY match_time ASC"
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
