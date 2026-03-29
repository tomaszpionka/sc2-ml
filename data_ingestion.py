import json
import logging
import duckdb
from config import MANIFEST_PATH, ROOT_PROJECTS_DIR, DUCKDB_TEMP_DIR

logger = logging.getLogger(__name__)

def slim_down_sc2_with_manifest():
    keys_to_remove = {"messageEvents", "gameEvents", "trackerEvents"}
    
    if MANIFEST_PATH.exists() and MANIFEST_PATH.stat().st_size > 0:
        try:
            with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            logger.info(f"Loaded manifest: {len(manifest)} files tracked.")
        except json.JSONDecodeError:
            logger.warning("Manifest was corrupted or empty. Starting fresh.")
            manifest = {}
    else:
        manifest = {}
        logger.info("No manifest found. Starting fresh.")

    total_files_processed = 0
    total_bytes_saved = 0

    try:
        for json_file in ROOT_PROJECTS_DIR.rglob("*.SC2Replay.json"):
            if json_file.name == "processing_manifest.json":
                continue

            file_key = str(json_file.relative_to(ROOT_PROJECTS_DIR))
            if manifest.get(file_key) is True:
                continue

            try:
                original_size = json_file.stat().st_size
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                found_keys = keys_to_remove.intersection(data.keys())
                if found_keys:
                    for key in found_keys:
                        data.pop(key)
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, separators=(',', ':'))
                    
                    new_size = json_file.stat().st_size
                    total_bytes_saved += (original_size - new_size)
                
                manifest[file_key] = True
                total_files_processed += 1
                
                if total_files_processed % 50 == 0:
                    logger.debug(f"Processed {total_files_processed} files...")

            except Exception as e:
                logger.error(f"Error processing {file_key}: {e}")
                manifest[file_key] = False

    finally:
        with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=4)
        logger.info("Manifest updated and saved.")

    gb_saved = total_bytes_saved / (1024**3)
    logger.info(f"New files processed: {total_files_processed}. Disk space saved: {gb_saved:.4f} GB")


def move_data_to_duck_db(con):
    logger.info("Setting up DuckDB optimizations...")
    con.execute(f"SET temp_directory='{DUCKDB_TEMP_DIR}'")
    con.execute("SET max_temp_directory_size='200GB'")
    con.execute("SET memory_limit='16GB'")
    con.execute("SET threads = 8")

    json_glob = f"{str(ROOT_PROJECTS_DIR)}/**/*.SC2Replay.json"

    con.execute("DROP TABLE IF EXISTS raw")
    logger.info("Dropped existing 'raw' table.")

    query = f"""
        CREATE OR REPLACE TABLE raw AS
        SELECT * FROM read_json(
            '{json_glob}',
            union_by_name = true, maximum_object_size = 536870912, format = 'auto', filename = true,
            columns = {{
                'header': 'JSON', 'initData': 'JSON', 'details': 'JSON', 'metadata': 'JSON',
                'ToonPlayerDescMap': 'JSON'
            }}
        )
    """
    
    logger.info(f"Scanning JSONs into DuckDB: {json_glob}")
    con.execute(query)
    row_count = con.execute("SELECT count(*) FROM raw").fetchone()[0]
    logger.info(f"DuckDB Ingestion complete. Total replays in 'raw': {row_count}")
