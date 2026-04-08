"""Replay data ingestion into DuckDB.

Path A — Pre-match features (header, player stats, map metadata):
    ``move_data_to_duck_db`` bulk-loads SC2Replay JSON files into a DuckDB
    ``raw`` table.
    ``ingest_map_alias_files`` loads per-tournament
    ``map_foreign_to_english_mapping.json`` files into the ``raw_map_alias_files``
    table — one row per file, storing the raw JSON verbatim with a SHA1 checksum.
    Downstream Phase 1 work parses the JSON via DuckDB json_extract / ->> operators.

Path B — In-game events (tracker events, game events, player metadata):
    ``run_in_game_extraction`` reads full replay JSON via multiprocessing,
    extracts structured events, and writes them to Parquet in batches.
    ``load_in_game_data_to_duckdb`` then imports those Parquet files into
    DuckDB tables and creates a typed ``player_stats`` view over the 39
    PlayerStats score fields.
"""

import hashlib
import json
import logging
import multiprocessing
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from rts_predict.sc2.config import (
    DUCKDB_MAX_OBJECT_SIZE,
    DUCKDB_MAX_TEMP_DIR_SIZE,
    DUCKDB_MEMORY_LIMIT,
    DUCKDB_TEMP_DIR,
    DUCKDB_THREADS,
    EXTRACTION_LOG_INTERVAL,
    IN_GAME_BATCH_SIZE,
    IN_GAME_MANIFEST_PATH,
    IN_GAME_PARQUET_DIR,
    IN_GAME_WORKERS,
    REPLAYS_SOURCE_DIR,
)
from rts_predict.sc2.data.schemas import (
    GAME_EVENT_SCHEMA,
    METADATA_SCHEMA,
    PLAYER_STATS_FIELD_MAP,
    TRACKER_SCHEMA,
)

logger = logging.getLogger(__name__)

# ── SQL query constants ───────────────────────────────────────────────────────

_DUCKDB_SET_QUERIES: list[str] = [
    f"SET temp_directory='{DUCKDB_TEMP_DIR}'",
    f"SET max_temp_directory_size='{DUCKDB_MAX_TEMP_DIR_SIZE}'",
    f"SET memory_limit='{DUCKDB_MEMORY_LIMIT}'",
    f"SET threads = {DUCKDB_THREADS}",
    "SET preserve_insertion_order=false",
]

_RAW_TABLE_CREATE_QUERY = """
    CREATE TABLE IF NOT EXISTS raw AS
    SELECT * FROM read_json(
        '{json_glob}',
        union_by_name = true,
        maximum_object_size = {max_object_size},
        filename = true,
        columns = {{
            'header': 'JSON', 'initData': 'JSON', 'details': 'JSON', 'metadata': 'JSON',
            'ToonPlayerDescMap': 'JSON'
        }}
    )
"""

_TRACKER_EVENTS_TABLE_QUERY = (
    "CREATE TABLE IF NOT EXISTS tracker_events_raw AS"
    " SELECT * FROM read_parquet('{glob_pattern}')"
)

_GAME_EVENTS_TABLE_QUERY = (
    "CREATE TABLE IF NOT EXISTS game_events_raw AS"
    " SELECT * FROM read_parquet('{glob_pattern}')"
)

_MATCH_PLAYER_MAP_TABLE_QUERY = (
    "CREATE TABLE IF NOT EXISTS match_player_map AS"
    " SELECT DISTINCT * FROM read_parquet('{glob_pattern}')"
)

_RAW_MAP_ALIAS_CREATE_QUERY = """
    CREATE TABLE IF NOT EXISTS raw_map_alias_files (
        tournament_dir  VARCHAR   NOT NULL,
        file_path       VARCHAR   NOT NULL,
        byte_sha1       VARCHAR   NOT NULL,
        n_bytes         BIGINT    NOT NULL,
        raw_json        VARCHAR   NOT NULL,
        ingested_at     TIMESTAMP NOT NULL,
        PRIMARY KEY (tournament_dir)
    )
"""


def _build_player_stats_view_query() -> str:
    field_extracts = ",\n        ".join(
        f"CAST(json_extract(event_data, '$.stats.{src}') AS FLOAT) AS {dst}"
        for src, dst in PLAYER_STATS_FIELD_MAP.items()
    )
    return f"""
        CREATE OR REPLACE VIEW player_stats AS
        SELECT
            match_id,
            game_loop,
            player_id,
            {field_extracts}
        FROM tracker_events_raw
        WHERE event_type = 'PlayerStats'
    """


_PLAYER_STATS_VIEW_QUERY = _build_player_stats_view_query()


def move_data_to_duck_db(con: duckdb.DuckDBPyConnection, should_drop: bool = False) -> None:
    """Load all SC2Replay JSON files into the DuckDB 'raw' table.

    Configures DuckDB for high-memory operation (24 GB limit, 4 threads) before
    ingesting. Scans all ``*.SC2Replay.json`` files under REPLAYS_SOURCE_DIR.
    """
    DUCKDB_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Setting up DuckDB optimizations (anti-OOM configuration)...")
    for q in _DUCKDB_SET_QUERIES:
        con.execute(q)

    # Restrict reads to the expected subdirectory structure
    json_glob = f"{str(REPLAYS_SOURCE_DIR)}/**/*.SC2Replay.json"

    if should_drop:
        con.execute("DROP TABLE IF EXISTS raw")
        logger.info("Dropped existing 'raw' table.")

    # Omitting format='auto' is intentional — explicit column types are faster
    logger.info(f"Scanning JSONs into DuckDB: {json_glob}")
    con.execute(
        _RAW_TABLE_CREATE_QUERY.format(
            json_glob=json_glob, max_object_size=DUCKDB_MAX_OBJECT_SIZE
        )
    )
    row = con.execute("SELECT count(*) FROM raw").fetchone()
    assert row is not None
    row_count = row[0]
    logger.info(f"DuckDB ingestion complete. Total replays in 'raw': {row_count}")


def ingest_map_alias_files(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    mapping_filename: str = "map_foreign_to_english_mapping.json",
) -> int:
    """Ingest every per-tournament map alias JSON as a row in raw_map_alias_files.

    Walks `raw_dir` for files named `mapping_filename`, computes the SHA1 of
    each file's raw bytes, and inserts one row per file. The JSON is stored
    verbatim as text — no parsing, no flattening, no deduplication. Downstream
    Phase 1 work parses the JSON via DuckDB json_extract / ->> operators.

    Args:
        con: An open DuckDB connection. Caller manages its lifecycle.
        raw_dir: Root directory containing the per-tournament subdirectories.
        mapping_filename: The filename to look for in each tournament directory.

    Returns:
        Number of rows inserted.

    Raises:
        FileNotFoundError: If `raw_dir` does not exist.
        ValueError: If zero matching files are found.
    """
    logger.info(f"Ingesting map alias files from: {raw_dir}")

    if not raw_dir.exists():
        raise FileNotFoundError(f"raw_dir does not exist: {raw_dir}")

    con.execute("DROP TABLE IF EXISTS raw_map_alias_files")
    con.execute(_RAW_MAP_ALIAS_CREATE_QUERY)

    alias_files = sorted(raw_dir.glob(f"*/{mapping_filename}"))

    if not alias_files:
        raise ValueError(
            f"No {mapping_filename!r} files found under {raw_dir}"
        )

    ingested_at = datetime.now(tz=timezone.utc).replace(tzinfo=None)

    rows: list[dict] = []
    for path in alias_files:
        tournament_dir = path.parent.name
        raw_bytes = path.read_bytes()
        byte_sha1 = hashlib.sha1(raw_bytes).hexdigest()
        n_bytes = len(raw_bytes)
        raw_json = path.read_text(encoding="utf-8")
        rows.append(
            {
                "tournament_dir": tournament_dir,
                "file_path": str(path),
                "byte_sha1": byte_sha1,
                "n_bytes": n_bytes,
                "raw_json": raw_json,
                "ingested_at": ingested_at,
            }
        )

    alias_df = pd.DataFrame(rows)  # noqa: F841 — referenced by DuckDB SQL below
    con.execute("INSERT INTO raw_map_alias_files SELECT * FROM alias_df")

    n_inserted = len(rows)
    logger.info(
        f"Ingested {n_inserted} map alias file(s) into raw_map_alias_files."
    )
    return n_inserted


# ── Path B: In-game event extraction ─────────────────────────────────────────


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

    for json_file in REPLAYS_SOURCE_DIR.rglob("*.SC2Replay.json"):
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

        if counts["total"] % 500 == 0:  # pragma: no cover
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
        table = pa.Table.from_pylist(tracker_rows, schema=TRACKER_SCHEMA)
        pq.write_table(table, output_dir / f"tracker_events_{suffix}.parquet")

    if game_rows:
        table = pa.Table.from_pylist(game_rows, schema=GAME_EVENT_SCHEMA)
        pq.write_table(table, output_dir / f"game_events_{suffix}.parquet")

    if meta_rows:
        table = pa.Table.from_pylist(meta_rows, schema=METADATA_SCHEMA)
        pq.write_table(table, output_dir / f"match_metadata_{suffix}.parquet")

    logger.debug(
        f"Batch {batch_number}: {len(tracker_rows)} tracker rows, "
        f"{len(game_rows)} game event rows, {len(meta_rows)} metadata rows"
    )


def _load_manifest(manifest_path: Path) -> dict[str, bool]:
    """Load an extraction manifest from disk, or return an empty dict.

    Args:
        manifest_path: Path to the JSON manifest file.

    Returns:
        A dict mapping file keys to processing status.
    """
    if manifest_path.exists() and manifest_path.stat().st_size > 0:
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest: dict[str, bool] = json.load(f)
            logger.info(f"Loaded in-game manifest: {len(manifest)} files tracked.")
            return manifest
        except json.JSONDecodeError:
            logger.warning("In-game manifest corrupted. Starting fresh.")
            return {}
    logger.info("No in-game manifest found. Starting fresh.")
    return {}


def _save_manifest(manifest: dict[str, bool], manifest_path: Path) -> None:
    """Persist the extraction manifest to disk.

    Args:
        manifest: Current manifest state.
        manifest_path: Path to write the JSON manifest file.
    """
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f)


def _collect_pending_files(
    manifest: dict[str, bool],
) -> list[Path]:
    """Collect replay files not yet recorded in the manifest.

    Args:
        manifest: Current manifest state.

    Returns:
        List of Paths to replay files still needing extraction.
    """
    all_files = sorted(REPLAYS_SOURCE_DIR.rglob("*.SC2Replay.json"))
    pending = [
        f
        for f in all_files
        if manifest.get(str(f.relative_to(REPLAYS_SOURCE_DIR))) is not True
    ]
    logger.info(
        f"In-game extraction: {len(pending)} files to process "
        f"({len(all_files) - len(pending)} already done)."
    )
    return pending


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
    manifest = _load_manifest(IN_GAME_MANIFEST_PATH)
    pending_files = _collect_pending_files(manifest)

    if not pending_files:
        logger.info("Nothing to extract — all files already processed.")
        return

    parquet_dir.mkdir(parents=True, exist_ok=True)
    existing_batches = sorted(parquet_dir.glob("tracker_events_batch_*.parquet"))
    batch_number = len(existing_batches)

    total_processed = 0
    total_skipped = 0
    buffer: list[dict] = []

    with multiprocessing.Pool(max_workers) as pool:
        for result in pool.imap_unordered(extract_raw_events_from_file, pending_files):
            if result is None:
                total_skipped += 1
                continue

            buffer.append(result)
            manifest[result["match_id"]] = True
            total_processed += 1

            if len(buffer) >= batch_size:
                save_raw_events_to_parquet(buffer, parquet_dir, batch_number)
                batch_number += 1
                buffer = []
                _save_manifest(manifest, IN_GAME_MANIFEST_PATH)

            if total_processed % EXTRACTION_LOG_INTERVAL == 0:
                logger.info(
                    f"Progress: {total_processed} extracted, "
                    f"{total_skipped} skipped (no events)"
                )

    if buffer:
        save_raw_events_to_parquet(buffer, parquet_dir, batch_number)
        batch_number += 1
    _save_manifest(manifest, IN_GAME_MANIFEST_PATH)

    logger.info(
        f"In-game extraction complete: {total_processed} files extracted, "
        f"{total_skipped} skipped, "
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

    con.execute(_TRACKER_EVENTS_TABLE_QUERY.format(glob_pattern=glob_pattern))

    row = con.execute("SELECT count(*) FROM tracker_events_raw").fetchone()
    assert row is not None
    row_count = row[0]
    logger.info(f"Loaded {row_count} tracker events into tracker_events_raw.")

    con.execute(_PLAYER_STATS_VIEW_QUERY)
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

    con.execute(_GAME_EVENTS_TABLE_QUERY.format(glob_pattern=game_glob))
    row = con.execute("SELECT count(*) FROM game_events_raw").fetchone()
    assert row is not None
    game_count = row[0]
    logger.info(f"Loaded {game_count} game events into game_events_raw.")

    con.execute(_MATCH_PLAYER_MAP_TABLE_QUERY.format(glob_pattern=meta_glob))
    row = con.execute("SELECT count(*) FROM match_player_map").fetchone()
    assert row is not None
    meta_count = row[0]
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
