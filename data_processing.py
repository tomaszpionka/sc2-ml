import logging

logger = logging.getLogger(__name__)


def create_ml_views(con):
    logger.info(
        "Tworzenie zaktualizowanych widoków ML w DuckDB (tłumaczenia map i unifikacja nicków)..."
    )

    # Rozszerzony widok (Teraz z LEFT JOIN do słownika map!)
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
      AND (entry.value->>'$.result') IN ('Win', 'Loss') -- <--- KLUCZOWA POPRAWKA: Tnie casterów!
    """
    con.execute(query_flat_players)

    # 2. Łączenie w pary
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
    logger.info("Widok 'matches_flat' gotowy.")


def get_matches_dataframe(con):
    logger.info("Pobieranie danych do Pandas...")
    query = "SELECT * FROM matches_flat WHERE match_time IS NOT NULL ORDER BY match_time ASC"
    return con.execute(query).df()


def validate_data_split_sql(con, split_ratio=0.8):
    logger.info(f"====== WALIDACJA STRUKTURY DANYCH (Split {int(split_ratio*100)}/{int((1-split_ratio)*100)}) ======")    
    # 1. Rozkład czasowy meczów
    query_dist = """
    SELECT 
        EXTRACT(year FROM match_time) as year,
        COUNT(*) as total_matches,
        ROUND(COUNT(*) * 100.0 / (SUM(COUNT(*)) OVER()), 2) as pct_of_total
    FROM matches_flat
    GROUP BY year ORDER BY year;
    """
    dist_df = con.execute(query_dist).df()
    logger.info(f"\nRozkład roczny danych:\n{dist_df.to_string(index=False)}")

    # 2. Walidacja Time-Leakage
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
    
    valid = leakage_res['is_chronological_valid'].iloc[0]
    logger.info(f"Podział rzeczywisty: Train={leakage_res['train_count'].iloc[0]}, Test={leakage_res['test_count'].iloc[0]}")
    logger.info(f"Walidacja chronologii: {'ZALICZONA' if valid else 'BŁĄD!'}")
    logger.info(f"Ostatni mecz treningowy: {leakage_res['max_train_time'].iloc[0]}")
    logger.info(f"Pierwszy mecz testowy: {leakage_res['min_test_time'].iloc[0]}")
    
    # 3. Rozkład wersji gry
    # query_data_build = """
    #     SELECT 
    #         data_build as patch,
    #         COUNT(*) as num_matches,
    #         MIN(match_time) as patch_start,
    #         MAX(match_time) as patch_end,
    #         ROUND(COUNT(*) * 100.0 / (SUM(COUNT(*)) OVER()), 2) as pct_of_total
    #     FROM matches_flat
    #     GROUP BY data_build
    #     ORDER BY patch_start;
    # """
    # data_build_res = con.execute(query_data_build).df()
    # logger.info(f"\nRozkład danych według patcha:\n{data_build_res.to_string(index=False)}")
    logger.info("======================================================")
