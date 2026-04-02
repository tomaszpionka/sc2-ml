import json
import logging
import multiprocessing
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from sc2ml.config import (
    DUCKDB_TEMP_DIR,
    IN_GAME_BATCH_SIZE,
    IN_GAME_MANIFEST_PATH,
    IN_GAME_PARQUET_DIR,
    IN_GAME_WORKERS,
    MANIFEST_PATH,
    REPLAYS_SOURCE_DIR,
)

logger = logging.getLogger(__name__)


def slim_down_sc2_with_manifest(dry_run: bool = True) -> None:
    """Strip heavy event arrays from SC2Replay JSON files to reduce disk usage.

    Processes only files not already recorded in the manifest. Skips
    messageEvents, gameEvents, and trackerEvents — none are used by the
    pre-match ML pipeline (Path A). In-game models (Path B) need these
    events, so use dry_run=True (default) to preview without modifying files.

    Args:
        dry_run: If True, log what would be stripped but do not modify files.
    """
    keys_to_remove = {"messageEvents", "gameEvents", "trackerEvents"}

    if dry_run:
        logger.warning(
            "dry_run=True — files will NOT be modified. "
            "Pass dry_run=False to actually strip events."
        )

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
                    if dry_run:
                        logger.debug(f"Would strip {found_keys} from {file_key}")
                    else:
                        for key in found_keys:
                            data.pop(key)
                        with open(json_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, separators=(",", ":"))

                        new_size = json_file.stat().st_size
                        total_bytes_saved += original_size - new_size

                if not dry_run:
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


# ── Path B: In-game event extraction ─────────────────────────────────────────

# All 39 PlayerStats score fields mapped to snake_case column names.
# Source: trackerEvents where evtTypeName == "PlayerStats", nested under "stats".
PLAYER_STATS_FIELD_MAP: dict[str, str] = {
    "scoreValueFoodMade": "food_made",
    "scoreValueFoodUsed": "food_used",
    "scoreValueMineralsCollectionRate": "minerals_collection_rate",
    "scoreValueMineralsCurrent": "minerals_current",
    "scoreValueMineralsFriendlyFireArmy": "minerals_friendly_fire_army",
    "scoreValueMineralsFriendlyFireEconomy": "minerals_friendly_fire_economy",
    "scoreValueMineralsFriendlyFireTechnology": "minerals_friendly_fire_technology",
    "scoreValueMineralsKilledArmy": "minerals_killed_army",
    "scoreValueMineralsKilledEconomy": "minerals_killed_economy",
    "scoreValueMineralsKilledTechnology": "minerals_killed_technology",
    "scoreValueMineralsLostArmy": "minerals_lost_army",
    "scoreValueMineralsLostEconomy": "minerals_lost_economy",
    "scoreValueMineralsLostTechnology": "minerals_lost_technology",
    "scoreValueMineralsUsedActiveForces": "minerals_used_active_forces",
    "scoreValueMineralsUsedCurrentArmy": "minerals_used_current_army",
    "scoreValueMineralsUsedCurrentEconomy": "minerals_used_current_economy",
    "scoreValueMineralsUsedCurrentTechnology": "minerals_used_current_technology",
    "scoreValueMineralsUsedInProgressArmy": "minerals_used_in_progress_army",
    "scoreValueMineralsUsedInProgressEconomy": "minerals_used_in_progress_economy",
    "scoreValueMineralsUsedInProgressTechnology": "minerals_used_in_progress_technology",
    "scoreValueVespeneCollectionRate": "vespene_collection_rate",
    "scoreValueVespeneCurrent": "vespene_current",
    "scoreValueVespeneFriendlyFireArmy": "vespene_friendly_fire_army",
    "scoreValueVespeneFriendlyFireEconomy": "vespene_friendly_fire_economy",
    "scoreValueVespeneFriendlyFireTechnology": "vespene_friendly_fire_technology",
    "scoreValueVespeneKilledArmy": "vespene_killed_army",
    "scoreValueVespeneKilledEconomy": "vespene_killed_economy",
    "scoreValueVespeneKilledTechnology": "vespene_killed_technology",
    "scoreValueVespeneLostArmy": "vespene_lost_army",
    "scoreValueVespeneLostEconomy": "vespene_lost_economy",
    "scoreValueVespeneLostTechnology": "vespene_lost_technology",
    "scoreValueVespeneUsedActiveForces": "vespene_used_active_forces",
    "scoreValueVespeneUsedCurrentArmy": "vespene_used_current_army",
    "scoreValueVespeneUsedCurrentEconomy": "vespene_used_current_economy",
    "scoreValueVespeneUsedCurrentTechnology": "vespene_used_current_technology",
    "scoreValueVespeneUsedInProgressArmy": "vespene_used_in_progress_army",
    "scoreValueVespeneUsedInProgressEconomy": "vespene_used_in_progress_economy",
    "scoreValueVespeneUsedInProgressTechnology": "vespene_used_in_progress_technology",
    "scoreValueWorkersActiveCount": "workers_active_count",
}


def audit_raw_data_availability() -> dict[str, int]:
    """Scan replay files and report how many still contain in-game event data.

    Checks for the presence of ``trackerEvents`` and ``gameEvents`` keys
    without fully parsing each file.  Run this before Path B extraction to
    determine whether raw data needs to be re-acquired from the original
    SC2EGSet ZIPs.

    Returns:
        Dict with keys ``total``, ``has_tracker``, ``has_game``,
        ``has_both``, ``stripped``.
    """
    counts = {"total": 0, "has_tracker": 0, "has_game": 0, "has_both": 0, "stripped": 0}

    for json_file in REPLAYS_SOURCE_DIR.rglob("*/data/*.SC2Replay.json"):
        counts["total"] += 1
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            has_tracker = "trackerEvents" in data
            has_game = "gameEvents" in data
            if has_tracker:
                counts["has_tracker"] += 1
            if has_game:
                counts["has_game"] += 1
            if has_tracker and has_game:
                counts["has_both"] += 1
            if not has_tracker and not has_game:
                counts["stripped"] += 1
        except Exception as e:
            logger.error(f"Error reading {json_file}: {e}")

        if counts["total"] % 500 == 0:
            logger.info(f"Audited {counts['total']} files...")

    logger.info(
        f"Audit complete: {counts['total']} files scanned. "
        f"has_both={counts['has_both']}, stripped={counts['stripped']}"
    )
    return counts


def extract_raw_events_from_file(json_path: Path) -> dict | None:
    """Extract raw event arrays from a single SC2Replay JSON file.

    This is a **pure function** (no DB access, no side effects) designed to
    run in worker processes.  It reads one replay file and returns the raw
    ``trackerEvents`` and ``gameEvents`` arrays together with the player
    mapping needed to resolve ``userId`` → ``playerID``.

    Args:
        json_path: Absolute path to an ``*.SC2Replay.json`` file.

    Returns:
        A dict with keys ``match_id``, ``tracker_events``, ``game_events``,
        ``player_map``, and ``total_game_loops``; or ``None`` if the file
        lacks ``trackerEvents``.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "trackerEvents" not in data:
        return None

    # Build userId → player metadata from ToonPlayerDescMap
    player_map: dict[int, dict] = {}
    toon_map = data.get("ToonPlayerDescMap", {})
    for toon_info in toon_map.values():
        uid = toon_info.get("userID")
        if uid is not None:
            player_map[uid] = {
                "playerID": toon_info.get("playerID"),
                "nickname": toon_info.get("nickname", ""),
                "race": toon_info.get("race", ""),
            }

    total_loops = 0
    header = data.get("header", {})
    if isinstance(header, dict):
        total_loops = header.get("elapsedGameLoops", 0)

    try:
        match_id = str(json_path.relative_to(REPLAYS_SOURCE_DIR))
    except ValueError:
        # File is outside REPLAYS_SOURCE_DIR (e.g., sample data in tests)
        match_id = json_path.name

    return {
        "match_id": match_id,
        "tracker_events": data["trackerEvents"],
        "game_events": data.get("gameEvents", []),
        "player_map": player_map,
        "total_game_loops": total_loops,
    }


def _build_tracker_rows(
    match_id: str,
    tracker_events: list[dict],
) -> list[dict]:
    """Flatten tracker events into row dicts for Parquet."""
    rows: list[dict] = []
    for evt in tracker_events:
        rows.append(
            {
                "match_id": match_id,
                "event_type": evt.get("evtTypeName", ""),
                "game_loop": evt.get("loop", 0),
                "player_id": evt.get("playerId", 0),
                "event_data": json.dumps(evt, separators=(",", ":")),
            }
        )
    return rows


def _build_game_event_rows(
    match_id: str,
    game_events: list[dict],
    player_map: dict[int, dict],
) -> list[dict]:
    """Flatten game events into row dicts for Parquet."""
    uid_to_pid: dict[int, int] = {
        uid: info["playerID"] for uid, info in player_map.items()
    }
    rows: list[dict] = []
    for evt in game_events:
        user_id_obj = evt.get("userid")
        user_id = user_id_obj.get("userId", 0) if isinstance(user_id_obj, dict) else 0
        rows.append(
            {
                "match_id": match_id,
                "event_type": evt.get("evtTypeName", ""),
                "game_loop": evt.get("loop", 0),
                "user_id": user_id,
                "player_id": uid_to_pid.get(user_id, 0),
                "event_data": json.dumps(evt, separators=(",", ":")),
            }
        )
    return rows


def _build_metadata_rows(
    match_id: str,
    player_map: dict[int, dict],
    total_game_loops: int,
) -> list[dict]:
    """Build per-player metadata rows for Parquet."""
    rows: list[dict] = []
    for uid, info in player_map.items():
        rows.append(
            {
                "match_id": match_id,
                "player_id": info["playerID"],
                "user_id": uid,
                "nickname": info["nickname"],
                "race": info["race"],
                "total_game_loops": total_game_loops,
            }
        )
    return rows


_TRACKER_SCHEMA = pa.schema(
    [
        pa.field("match_id", pa.string()),
        pa.field("event_type", pa.string()),
        pa.field("game_loop", pa.int32()),
        pa.field("player_id", pa.int8()),
        pa.field("event_data", pa.string()),
    ]
)

_GAME_EVENT_SCHEMA = pa.schema(
    [
        pa.field("match_id", pa.string()),
        pa.field("event_type", pa.string()),
        pa.field("game_loop", pa.int32()),
        pa.field("user_id", pa.int32()),
        pa.field("player_id", pa.int8()),
        pa.field("event_data", pa.string()),
    ]
)

_METADATA_SCHEMA = pa.schema(
    [
        pa.field("match_id", pa.string()),
        pa.field("player_id", pa.int8()),
        pa.field("user_id", pa.int32()),
        pa.field("nickname", pa.string()),
        pa.field("race", pa.string()),
        pa.field("total_game_loops", pa.int32()),
    ]
)


def save_raw_events_to_parquet(
    events_batch: list[dict],
    output_dir: Path,
    batch_number: int,
) -> None:
    """Write a batch of extracted replay data to Parquet files.

    Produces three files per batch:
    - ``tracker_events_batch_{N}.parquet`` — one row per trackerEvent
    - ``game_events_batch_{N}.parquet`` — one row per gameEvent
    - ``match_metadata_batch_{N}.parquet`` — player mapping per match

    Args:
        events_batch: List of dicts returned by ``extract_raw_events_from_file``.
        output_dir: Directory to write Parquet files into.
        batch_number: Sequential batch index for file naming.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    tracker_rows: list[dict] = []
    game_rows: list[dict] = []
    meta_rows: list[dict] = []

    for result in events_batch:
        mid = result["match_id"]
        tracker_rows.extend(_build_tracker_rows(mid, result["tracker_events"]))
        game_rows.extend(
            _build_game_event_rows(mid, result["game_events"], result["player_map"])
        )
        meta_rows.extend(
            _build_metadata_rows(mid, result["player_map"], result["total_game_loops"])
        )

    suffix = f"batch_{batch_number:05d}"

    if tracker_rows:
        table = pa.Table.from_pylist(tracker_rows, schema=_TRACKER_SCHEMA)
        pq.write_table(table, output_dir / f"tracker_events_{suffix}.parquet")

    if game_rows:
        table = pa.Table.from_pylist(game_rows, schema=_GAME_EVENT_SCHEMA)
        pq.write_table(table, output_dir / f"game_events_{suffix}.parquet")

    if meta_rows:
        table = pa.Table.from_pylist(meta_rows, schema=_METADATA_SCHEMA)
        pq.write_table(table, output_dir / f"match_metadata_{suffix}.parquet")

    logger.debug(
        f"Batch {batch_number}: {len(tracker_rows)} tracker rows, "
        f"{len(game_rows)} game event rows, {len(meta_rows)} metadata rows"
    )


def run_in_game_extraction(
    parquet_dir: Path = IN_GAME_PARQUET_DIR,
    max_workers: int = IN_GAME_WORKERS,
    batch_size: int = IN_GAME_BATCH_SIZE,
) -> None:
    """Extract raw in-game events from all replay files using multiprocessing.

    Workers read individual JSON files and return raw event arrays.  The main
    process batches results and writes Parquet files.  Progress is tracked via
    a manifest so extraction can resume after interruption.

    Args:
        parquet_dir: Directory to write Parquet output files.
        max_workers: Number of parallel worker processes.
        batch_size: Number of files to accumulate before flushing a Parquet batch.
    """
    # Load or create manifest
    if IN_GAME_MANIFEST_PATH.exists() and IN_GAME_MANIFEST_PATH.stat().st_size > 0:
        try:
            with open(IN_GAME_MANIFEST_PATH, "r", encoding="utf-8") as f:
                manifest: dict[str, bool] = json.load(f)
            logger.info(f"Loaded in-game manifest: {len(manifest)} files tracked.")
        except json.JSONDecodeError:
            logger.warning("In-game manifest corrupted. Starting fresh.")
            manifest = {}
    else:
        manifest = {}
        logger.info("No in-game manifest found. Starting fresh.")

    # Collect files to process
    all_files = sorted(REPLAYS_SOURCE_DIR.rglob("*/data/*.SC2Replay.json"))
    pending_files = [
        f
        for f in all_files
        if manifest.get(str(f.relative_to(REPLAYS_SOURCE_DIR))) is not True
    ]
    logger.info(
        f"In-game extraction: {len(pending_files)} files to process "
        f"({len(all_files) - len(pending_files)} already done)."
    )

    if not pending_files:
        logger.info("Nothing to extract — all files already processed.")
        return

    parquet_dir.mkdir(parents=True, exist_ok=True)

    # Determine starting batch number from existing parquet files
    existing_batches = sorted(parquet_dir.glob("tracker_events_batch_*.parquet"))
    batch_number = len(existing_batches)

    total_processed = 0
    total_skipped = 0
    total_errors = 0
    buffer: list[dict] = []

    def _flush_batch() -> None:
        nonlocal batch_number, buffer
        if not buffer:
            return
        save_raw_events_to_parquet(buffer, parquet_dir, batch_number)
        batch_number += 1
        buffer = []

    def _save_manifest() -> None:
        with open(IN_GAME_MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f)

    with multiprocessing.Pool(max_workers) as pool:
        for result in pool.imap_unordered(extract_raw_events_from_file, pending_files):
            if result is None:
                total_skipped += 1
                continue

            file_key = result["match_id"]

            # Check for extraction errors (extract function returns None on missing data,
            # but pool may also propagate exceptions as results via error_callback)
            buffer.append(result)
            manifest[file_key] = True
            total_processed += 1

            if len(buffer) >= batch_size:
                _flush_batch()
                _save_manifest()

            if total_processed % 200 == 0:
                logger.info(
                    f"Progress: {total_processed} extracted, "
                    f"{total_skipped} skipped (no events), {total_errors} errors"
                )

    # Flush remaining buffer
    _flush_batch()
    _save_manifest()

    logger.info(
        f"In-game extraction complete: {total_processed} files extracted, "
        f"{total_skipped} skipped, {total_errors} errors, "
        f"{batch_number} Parquet batches written to {parquet_dir}"
    )


def load_tracker_events_to_duckdb(
    con: duckdb.DuckDBPyConnection,
    parquet_dir: Path = IN_GAME_PARQUET_DIR,
    should_drop: bool = False,
) -> None:
    """Load tracker event Parquet files into DuckDB and create a typed PlayerStats view.

    Creates:
    - ``tracker_events_raw`` table — all tracker events with raw JSON in ``event_data``
    - ``player_stats`` view — only PlayerStats events with the 39 economic fields
      extracted as typed FLOAT columns

    Args:
        con: DuckDB connection to the in-game database.
        parquet_dir: Directory containing ``tracker_events_batch_*.parquet`` files.
        should_drop: If True, drop existing table before creating.
    """
    glob_pattern = str(parquet_dir / "tracker_events_batch_*.parquet")

    if should_drop:
        con.execute("DROP VIEW IF EXISTS player_stats")
        con.execute("DROP TABLE IF EXISTS tracker_events_raw")
        logger.info("Dropped existing tracker_events_raw table and player_stats view.")

    con.execute(f"""
        CREATE TABLE IF NOT EXISTS tracker_events_raw AS
        SELECT * FROM read_parquet('{glob_pattern}')
    """)

    row_count = con.execute("SELECT count(*) FROM tracker_events_raw").fetchone()[0]
    logger.info(f"Loaded {row_count} tracker events into tracker_events_raw.")

    # Build the player_stats view with all 39 typed columns
    field_extracts = ",\n        ".join(
        f"CAST(json_extract(event_data, '$.stats.{src}') AS FLOAT) AS {dst}"
        for src, dst in PLAYER_STATS_FIELD_MAP.items()
    )

    con.execute(f"""
        CREATE OR REPLACE VIEW player_stats AS
        SELECT
            match_id,
            game_loop,
            player_id,
            {field_extracts}
        FROM tracker_events_raw
        WHERE event_type = 'PlayerStats'
    """)
    logger.info("Created player_stats view with 39 typed economic fields.")


def load_game_events_to_duckdb(
    con: duckdb.DuckDBPyConnection,
    parquet_dir: Path = IN_GAME_PARQUET_DIR,
    should_drop: bool = False,
) -> None:
    """Load game event and match metadata Parquet files into DuckDB.

    Creates:
    - ``game_events_raw`` table — all game events with raw JSON
    - ``match_player_map`` table — per-match userId ↔ playerID resolution

    Args:
        con: DuckDB connection to the in-game database.
        parquet_dir: Directory containing Parquet files.
        should_drop: If True, drop existing tables before creating.
    """
    game_glob = str(parquet_dir / "game_events_batch_*.parquet")
    meta_glob = str(parquet_dir / "match_metadata_batch_*.parquet")

    if should_drop:
        con.execute("DROP TABLE IF EXISTS game_events_raw")
        con.execute("DROP TABLE IF EXISTS match_player_map")
        logger.info("Dropped existing game_events_raw and match_player_map tables.")

    con.execute(f"""
        CREATE TABLE IF NOT EXISTS game_events_raw AS
        SELECT * FROM read_parquet('{game_glob}')
    """)
    game_count = con.execute("SELECT count(*) FROM game_events_raw").fetchone()[0]
    logger.info(f"Loaded {game_count} game events into game_events_raw.")

    con.execute(f"""
        CREATE TABLE IF NOT EXISTS match_player_map AS
        SELECT DISTINCT * FROM read_parquet('{meta_glob}')
    """)
    meta_count = con.execute("SELECT count(*) FROM match_player_map").fetchone()[0]
    logger.info(f"Loaded {meta_count} player mappings into match_player_map.")


def load_in_game_data_to_duckdb(
    con: duckdb.DuckDBPyConnection,
    parquet_dir: Path = IN_GAME_PARQUET_DIR,
    should_drop: bool = False,
) -> None:
    """Load all in-game Parquet data into DuckDB tables and views.

    Convenience wrapper that calls ``load_tracker_events_to_duckdb`` and
    ``load_game_events_to_duckdb``.
    """
    load_tracker_events_to_duckdb(con, parquet_dir, should_drop)
    load_game_events_to_duckdb(con, parquet_dir, should_drop)
