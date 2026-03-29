import logging

logger = logging.getLogger(__name__)


def create_ml_views(con):
    logger.info("Tworzenie zaktualizowanych widoków ML w DuckDB (nowe cechy: czas, supply, clan, mapa)...")
    
    # 1. Rozszerzony widok flat_players
    query_flat_players = """
    CREATE OR REPLACE VIEW flat_players AS
    SELECT 
        filename AS match_id,
        (details->>'$.timeUTC')::TIMESTAMP AS match_time,
        
        -- Cechy ogólnogrowe (z header, metadata i initData)
        (header->>'$.elapsedGameLoops')::INTEGER AS game_loops,
        (initData->>'$.gameDescription.mapSizeX')::INTEGER AS map_size_x,
        (initData->>'$.gameDescription.mapSizeY')::INTEGER AS map_size_y,
        metadata->>'$.dataBuild' AS data_build,
        
        -- Cechy konkretnego gracza
        entry.key AS toon_id,
        entry.value->>'$.race' AS race,
        (entry.value->>'$.startLocX')::INTEGER AS startLocX,
        (entry.value->>'$.startLocY')::INTEGER AS startLocY,
        (entry.value->>'$.APM')::INTEGER AS apm,
        (entry.value->>'$.SQ')::INTEGER AS sq,
        (entry.value->>'$.supplyCappedPercent')::INTEGER AS supply_capped_pct,
        (entry.value->>'$.isInClan')::BOOLEAN AS is_in_clan,
        
        entry.value->>'$.result' AS result
    FROM raw, 
         LATERAL json_each(ToonPlayerDescMap) AS entry
    """
    con.execute(query_flat_players)

    # 2. Łączenie w pary z uwzględnieniem nowych cech
    query_matches = """
    CREATE OR REPLACE VIEW matches_flat AS
    SELECT 
        p1.match_id,
        p1.match_time,
        
        -- Wspólne dla meczu (bierzemy z p1, bo dla p2 są identyczne)
        p1.game_loops,
        p1.map_size_x,
        p1.map_size_y,
        p1.data_build,
        
        -- Informacje o graczach
        p1.toon_id AS p1_id,
        p2.toon_id AS p2_id,
        
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
    JOIN flat_players p2 ON p1.match_id = p2.match_id AND p1.toon_id != p2.toon_id
    """
    con.execute(query_matches)
    logger.info("Widok 'matches_flat' gotowy.")


def get_matches_dataframe(con):
    logger.info("Pobieranie danych do Pandas...")
    query = "SELECT * FROM matches_flat WHERE match_time IS NOT NULL ORDER BY match_time ASC"
    return con.execute(query).df()