import json
import logging
import duckdb
import pandas as pd
from config import MANIFEST_PATH, REPLAYS_SOURCE_DIR, DUCKDB_TEMP_DIR

logger = logging.getLogger(__name__)


def slim_down_sc2_with_manifest() -> None:
    """Strip heavy event arrays from SC2Replay JSON files to reduce disk usage.

    Processes only files not already recorded in the manifest. Skips
    messageEvents, gameEvents, and trackerEvents — none are used by the ML pipeline.
    """
    keys_to_remove = {"messageEvents", "gameEvents", "trackerEvents"}

    if MANIFEST_PATH.exists() and MANIFEST_PATH.stat().st_size > 0:
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
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
        # Scan only SC2Replay JSON files nested under 'data/' subdirectories
        for json_file in REPLAYS_SOURCE_DIR.rglob("*/data/*.SC2Replay.json"):
            # Manifest key is the path relative to the replays root directory
            file_key = str(json_file.relative_to(REPLAYS_SOURCE_DIR))
            if manifest.get(file_key) is True:
                continue

            try:
                original_size = json_file.stat().st_size
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                found_keys = keys_to_remove.intersection(data.keys())
                if found_keys:
                    for key in found_keys:
                        data.pop(key)
                    with open(json_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, separators=(",", ":"))

                    new_size = json_file.stat().st_size
                    total_bytes_saved += original_size - new_size

                manifest[file_key] = True
                total_files_processed += 1

                if total_files_processed % 100 == 0:
                    logger.info(f"Processed {total_files_processed} files...")

            except Exception as e:
                logger.error(f"Error processing {file_key}: {e}")
                manifest[file_key] = False

    finally:
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=4)
        logger.info("Manifest updated and saved.")

    gb_saved = total_bytes_saved / (1024**3)
    logger.info(
        f"New files processed: {total_files_processed}. Disk space saved: {gb_saved:.4f} GB"
    )


def move_data_to_duck_db(con: duckdb.DuckDBPyConnection, should_drop: bool = False) -> None:
    """Load all SC2Replay JSON files into the DuckDB 'raw' table.

    Configures DuckDB for high-memory operation (24 GB limit, 4 threads) before
    ingesting. Scans only files under REPLAYS_SOURCE_DIR/**/data/*.
    """
    logger.info("Setting up DuckDB optimizations (anti-OOM configuration)...")
    con.execute(f"SET temp_directory='{DUCKDB_TEMP_DIR}'")
    con.execute("SET max_temp_directory_size='150GB'")

    # 24 GB is safe on 36 GB M4 Max; leaves headroom for OS and other processes
    con.execute("SET memory_limit='24GB'")
    con.execute("SET threads = 4")

    # Disable insertion-order preservation so processed rows are flushed to disk
    # immediately rather than held in memory until the full scan completes
    con.execute("SET preserve_insertion_order=false")

    # Restrict reads to the expected subdirectory structure
    json_glob = f"{str(REPLAYS_SOURCE_DIR)}/**/data/*.SC2Replay.json"

    if should_drop:
        con.execute("DROP TABLE IF EXISTS raw")
        logger.info("Dropped existing 'raw' table.")

    # Omitting format='auto' is intentional — explicit column types are faster
    query = f"""
        CREATE TABLE IF NOT EXISTS raw AS
        SELECT * FROM read_json(
            '{json_glob}',
            union_by_name = true,
            maximum_object_size = 536870912,
            filename = true,
            columns = {{
                'header': 'JSON', 'initData': 'JSON', 'details': 'JSON', 'metadata': 'JSON',
                'ToonPlayerDescMap': 'JSON'
            }}
        )
    """

    logger.info(f"Scanning JSONs into DuckDB: {json_glob}")
    con.execute(query)
    row_count = con.execute("SELECT count(*) FROM raw").fetchone()[0]
    logger.info(f"DuckDB ingestion complete. Total replays in 'raw': {row_count}")


def load_map_translations(con: duckdb.DuckDBPyConnection) -> None:
    """Scan and merge all map_foreign_to_english_mapping.json files into DuckDB.

    Finds all translation dictionaries under REPLAYS_SOURCE_DIR, merges them into
    a single mapping, and loads it as the 'map_translation' table.
    DuckDB can ingest a Pandas DataFrame directly from memory.
    """
    logger.info("Searching for map translation dictionaries...")
    global_mapping: dict[str, str] = {}

    for map_file in REPLAYS_SOURCE_DIR.rglob("*map_foreign_to_english_mapping.json"):
        try:
            with open(map_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                global_mapping.update(data)
        except Exception as e:
            logger.error(f"Error reading {map_file}: {e}")

    if global_mapping:
        mapping_df = pd.DataFrame(
            list(global_mapping.items()), columns=["foreign_name", "english_name"]
        )
        con.execute("DROP TABLE IF EXISTS map_translation")
        con.execute("CREATE TABLE map_translation AS SELECT * FROM mapping_df")
        logger.info(f"Loaded {len(global_mapping)} unique map translations into DuckDB.")
    else:
        logger.warning("No map translation dictionaries found.")
