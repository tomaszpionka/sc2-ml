import logging

logger = logging.getLogger(__name__)

# def create_ml_views(con):
#     logger.info("Creating flattened ML views in DuckDB...")
    
#     # Krok 1: Wypłaszczenie danych z uwzględnieniem czasu
#     query_flat_players = """
#     CREATE OR REPLACE VIEW flat_players AS
#     SELECT 
#         filename AS match_id,
#         (details->>'$.timeUTC')::TIMESTAMP AS match_time,
#         entry.key AS toon_id,
#         entry.value->>'$.race' AS race,
#         (entry.value->>'$.startLocX')::INTEGER AS startLocX,
#         (entry.value->>'$.startLocY')::INTEGER AS startLocY,
#         entry.value->>'$.result' AS result
#     FROM raw, 
#          LATERAL json_each(ToonPlayerDescMap) AS entry
#     """
#     con.execute(query_flat_players)

#     # Krok 2: Złączenie P1 z P2 (jeden mecz = jeden wiersz z perspektywy P1)
#     query_matches = """
#     CREATE OR REPLACE VIEW matches_flat AS
#     SELECT 
#         p1.match_id,
#         p1.match_time,
#         p1.toon_id AS p1_id,
#         p2.toon_id AS p2_id,
#         p1.race AS p1_race,
#         p2.race AS p2_race,
#         p1.startLocX AS p1_startLocX,
#         p1.startLocY AS p1_startLocY,
#         p2.startLocX AS p2_startLocX,
#         p2.startLocY AS p2_startLocY,
#         p1.result AS p1_result
#     FROM flat_players p1
#     JOIN flat_players p2 ON p1.match_id = p2.match_id AND p1.toon_id != p2.toon_id
#     """
#     con.execute(query_matches)
#     logger.info("View 'matches_flat' created successfully.")

# def get_matches_dataframe(con):
#     logger.info("Fetching data to Pandas DataFrame...")
#     # Pobieramy mecze, na których będziemy robić predykcje
#     query = "SELECT * FROM matches_flat WHERE match_time IS NOT NULL ORDER BY match_time ASC"
#     return con.execute(query).df()

# iter 2

def create_ml_views(con):
    logger.info("Tworzenie zaktualizowanych widoków ML w DuckDB (z APM i SQ)...")
    
    query_flat_players = """
    CREATE OR REPLACE VIEW flat_players AS
    SELECT 
        filename AS match_id,
        (details->>'$.timeUTC')::TIMESTAMP AS match_time,
        entry.key AS toon_id,
        entry.value->>'$.race' AS race,
        (entry.value->>'$.startLocX')::INTEGER AS startLocX,
        (entry.value->>'$.startLocY')::INTEGER AS startLocY,
        (entry.value->>'$.APM')::INTEGER AS apm,
        (entry.value->>'$.SQ')::INTEGER AS sq,
        entry.value->>'$.result' AS result
    FROM raw, 
         LATERAL json_each(ToonPlayerDescMap) AS entry
    """
    con.execute(query_flat_players)

    # DODANE BRAKUJĄCE KOLUMNY DLA P2 (p2.startLocX, p2.startLocY)
    query_matches = """
    CREATE OR REPLACE VIEW matches_flat AS
    SELECT 
        p1.match_id,
        p1.match_time,
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