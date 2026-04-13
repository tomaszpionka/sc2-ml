"""Raw CTAS ingestion for sc2egset into DuckDB.

Three-stream extraction strategy:
- Stream 1 (replays_meta_raw): DuckDB table, one row per replay with metadata
  STRUCT columns and ToonPlayerDescMap stored as VARCHAR (JSON text blob).
  Event arrays EXCLUDED.
- Stream 2 (replay_players_raw): DuckDB table normalised from ToonPlayerDescMap.
  One row per (replay, player).
- Stream 3 (events): Parquet files for gameEvents, trackerEvents,
  messageEvents — NOT loaded into DuckDB.

Also: map_aliases_raw DuckDB table from tournament-level mapping files.

Every table carries a ``filename`` provenance column storing a path relative
to ``raw_dir`` (no absolute paths). Removing this column in any downstream
view is forbidden (INVARIANT I7, I10).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import duckdb

logger = logging.getLogger(__name__)

# ── SQL constants ────────────────────────────────────────────────────────────

_DROP_IF_EXISTS_QUERY = "DROP TABLE IF EXISTS {table}"

_COUNT_QUERY = "SELECT count(*) FROM {table}"

# Stream 1: replays_meta_raw — scalar metadata per replay, events excluded.
# ToonPlayerDescMap is stored as VARCHAR (JSON text) because its keys are
# dynamic player toon IDs that vary per replay.
# filename is stripped to a relative path from raw_dir via substr (I10).
#
# Loaded per-tournament to keep DuckDB memory usage within safe limits.
# A single CTAS over all 22,390 files (209 GB) exceeds ~22 GB RSS and
# triggers OS OOM kills on 36 GB machines. Per-tournament batching keeps
# peak RSS under 3 GB.
_REPLAYS_META_CREATE_QUERY = """
CREATE TABLE replays_meta_raw AS
SELECT
    substr(filename, {raw_dir_prefix_len}) AS filename,
    details,
    header,
    initData,
    metadata,
    CAST(ToonPlayerDescMap AS VARCHAR) AS ToonPlayerDescMap,
    gameEventsErr,
    messageEventsErr,
    trackerEvtsErr
FROM read_json_auto(
    '{glob}',
    union_by_name = true,
    filename = true,
    maximum_object_size = {max_object_size}
)
"""

_REPLAYS_META_INSERT_QUERY = """
INSERT INTO replays_meta_raw
SELECT
    substr(filename, {raw_dir_prefix_len}) AS filename,
    details,
    header,
    initData,
    metadata,
    CAST(ToonPlayerDescMap AS VARCHAR) AS ToonPlayerDescMap,
    gameEventsErr,
    messageEventsErr,
    trackerEvtsErr
FROM read_json_auto(
    '{glob}',
    union_by_name = true,
    filename = true,
    maximum_object_size = {max_object_size}
)
"""

# Stream 2: replay_players_raw — normalised from ToonPlayerDescMap.
# Reads each JSON file in Python, extracts ToonPlayerDescMap entries,
# and batch-inserts into DuckDB. Pure SQL unnesting is infeasible because
# DuckDB infers ToonPlayerDescMap as a STRUCT with per-replay dynamic
# field names (player toon IDs), which cannot be reliably unioned.
#
# Player field temporal annotations (for Phase 02):
#   Pre-game: MMR, selectedRace, handicap, region, realm, highestLeague
#   Post-game: result, APM, SQ, supplyCappedPercent
#   Identity: nickname, playerID, userID, isInClan, clanTag, color_*, startDir,
#             startLocX, startLocY, race

_REPLAY_PLAYERS_CREATE_QUERY = """
CREATE TABLE replay_players_raw (
    filename VARCHAR NOT NULL,
    toon_id VARCHAR NOT NULL,
    nickname VARCHAR,
    playerID INTEGER,
    userID BIGINT,
    isInClan BOOLEAN,
    clanTag VARCHAR,
    MMR INTEGER,
    race VARCHAR,
    selectedRace VARCHAR,
    handicap INTEGER,
    region VARCHAR,
    realm VARCHAR,
    highestLeague VARCHAR,
    result VARCHAR,
    APM INTEGER,
    SQ INTEGER,
    supplyCappedPercent INTEGER,
    startDir INTEGER,
    startLocX INTEGER,
    startLocY INTEGER,
    color_a INTEGER,
    color_b INTEGER,
    color_g INTEGER,
    color_r INTEGER
)
"""

_REPLAY_PLAYERS_INSERT_QUERY = """
INSERT INTO replay_players_raw VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
)
"""

# Map aliases: foreign map name -> English map name, per tournament.
# Each tournament has a map_foreign_to_english_mapping.json with
# {foreign_name: english_name} entries.
_MAP_ALIASES_CREATE_QUERY = """
CREATE TABLE map_aliases_raw (
    tournament VARCHAR NOT NULL,
    foreign_name VARCHAR NOT NULL,
    english_name VARCHAR NOT NULL,
    filename VARCHAR NOT NULL
)
"""


# ── Max object size ──────────────────────────────────────────────────────────
# SC2 replay JSONs can be very large due to event arrays. Largest file in the
# full 22,390-file corpus: 143.1 MB (observed during 01_02_02 execution).
# 160 MB provides 1.12x headroom while keeping DuckDB memory pressure
# manageable during the 209 GB single-CTAS read_json_auto scan (I7 derivation).
_DEFAULT_MAX_OBJECT_SIZE: int = 167_772_160  # 160 MB


def _count_rows(con: duckdb.DuckDBPyConnection, table: str) -> int:
    """Return the row count for a table.

    Args:
        con: Active DuckDB connection.
        table: Table name to count.

    Returns:
        Integer row count.
    """
    row = con.execute(_COUNT_QUERY.format(table=table)).fetchone()
    assert row is not None
    return int(row[0])


def _discover_tournament_dirs(raw_dir: Path) -> list[Path]:
    """Return sorted list of tournament directories in the raw data directory.

    Args:
        raw_dir: Path to sc2egset raw/ directory.

    Returns:
        Sorted list of tournament directory paths.
    """
    return sorted(
        d for d in raw_dir.iterdir()
        if d.is_dir()
    )


def load_replays_meta_raw(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    should_drop: bool = True,
    max_object_size: int = _DEFAULT_MAX_OBJECT_SIZE,
) -> int:
    """Materialise replays_meta_raw from all SC2Replay.json files.

    Creates one row per replay with metadata STRUCT columns (details,
    header, initData, metadata) and ToonPlayerDescMap as VARCHAR (JSON
    text blob). Event arrays are excluded from this table. The filename
    column stores paths relative to raw_dir (Invariant I10).

    Loads per-tournament to avoid OOM: a single CTAS over all 22,390
    files (209 GB) exceeds 22 GB RSS. Per-tournament batching keeps
    peak RSS under 3 GB per batch.

    Args:
        con: Active DuckDB connection (read-write).
        raw_dir: Path to the sc2egset raw/ directory.
        should_drop: If True, drop existing replays_meta_raw before creating.
        max_object_size: DuckDB maximum_object_size for large JSONs.

    Returns:
        Row count in replays_meta_raw after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="replays_meta_raw"))
        logger.info("Dropped existing replays_meta_raw table.")

    # raw_dir_prefix_len: len(raw_dir) + 1 for trailing '/' + 1 for 1-based substr
    raw_dir_prefix_len = len(str(raw_dir)) + 2
    fmt_params: dict[str, int | str] = {
        "max_object_size": max_object_size,
        "raw_dir_prefix_len": raw_dir_prefix_len,
    }

    tournament_dirs = _discover_tournament_dirs(raw_dir)
    table_created = False

    for t_dir in tournament_dirs:
        glob = str(t_dir / f"{t_dir.name}_data" / "*.SC2Replay.json")
        # Skip tournaments with no replay files
        if not list(t_dir.glob(f"{t_dir.name}_data/*.SC2Replay.json")):
            continue

        fmt_params["glob"] = glob
        if not table_created:
            con.execute(_REPLAYS_META_CREATE_QUERY.format(**fmt_params))
            table_created = True
        else:
            con.execute(_REPLAYS_META_INSERT_QUERY.format(**fmt_params))
        logger.info("replays_meta_raw: loaded %s", t_dir.name)

    n = _count_rows(con, "replays_meta_raw")
    logger.info("replays_meta_raw: %d total rows from %d tournaments", n, len(tournament_dirs))
    return n


def _extract_player_row(
    filename: str,
    toon_id: str,
    player: dict[str, Any],
) -> tuple[Any, ...]:
    """Extract a single player row tuple from a ToonPlayerDescMap entry.

    Args:
        filename: Replay filename for provenance.
        toon_id: Player toon ID (MAP key).
        player: Player data dictionary.

    Returns:
        Tuple matching the replay_players_raw table column order.
    """
    color = player.get("color", {})
    return (
        filename,
        toon_id,
        player.get("nickname"),
        player.get("playerID"),
        player.get("userID"),
        player.get("isInClan"),
        player.get("clanTag"),
        player.get("MMR"),
        player.get("race"),
        player.get("selectedRace"),
        player.get("handicap"),
        player.get("region"),
        player.get("realm"),
        player.get("highestLeague"),
        player.get("result"),
        player.get("APM"),
        player.get("SQ"),
        player.get("supplyCappedPercent"),
        player.get("startDir"),
        player.get("startLocX"),
        player.get("startLocY"),
        color.get("a"),
        color.get("b"),
        color.get("g"),
        color.get("r"),
    )


def load_replay_players_raw(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    should_drop: bool = True,
    batch_size: int = 500,
) -> int:
    """Materialise replay_players_raw normalised from ToonPlayerDescMap.

    Reads each JSON file in Python, extracts ToonPlayerDescMap entries,
    and batch-inserts into DuckDB. This avoids DuckDB's auto-inference
    of the dynamic-key ToonPlayerDescMap as a STRUCT type.

    The toon_id column contains the MAP key (e.g. "3-S2-1-4842177"),
    and the filename column stores the replay's path relative to raw_dir
    (Invariant I10).

    Args:
        con: Active DuckDB connection (read-write).
        raw_dir: Path to the sc2egset raw/ directory.
        should_drop: If True, drop existing replay_players_raw before creating.
        batch_size: Number of replay files to process per INSERT batch.
            Chosen to balance memory overhead and DuckDB insert throughput;
            ~1,000 player tuples per batch at typical 2-player replays.

    Returns:
        Row count in replay_players_raw after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="replay_players_raw"))
        logger.info("Dropped existing replay_players_raw table.")

    con.execute(_REPLAY_PLAYERS_CREATE_QUERY)

    replay_files = sorted(raw_dir.glob("*/*_data/*.SC2Replay.json"))
    total_files = len(replay_files)
    logger.info("load_replay_players_raw: found %d replay files", total_files)

    rows_inserted = 0
    batch_rows: list[tuple[Any, ...]] = []

    for i, fpath in enumerate(replay_files):
        try:
            with open(fpath) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Skipping %s: %s", fpath.name, e)
            continue

        tpdm = data.get("ToonPlayerDescMap", {})
        for toon_id, player_data in tpdm.items():
            batch_rows.append(
                _extract_player_row(str(fpath.relative_to(raw_dir)), toon_id, player_data)
            )

        if len(batch_rows) >= batch_size or i == total_files - 1:
            if batch_rows:
                con.executemany(_REPLAY_PLAYERS_INSERT_QUERY, batch_rows)
                rows_inserted += len(batch_rows)
                batch_rows = []

    n = _count_rows(con, "replay_players_raw")
    logger.info("replay_players_raw: %d rows from %d files", n, total_files)
    return n


def extract_events_to_parquet(
    raw_dir: Path,
    output_dir: Path,
    *,
    batch_size: int = 100,
    max_object_size: int = _DEFAULT_MAX_OBJECT_SIZE,
) -> dict[str, int]:
    """Extract event arrays from SC2Replay.json files to zstd-compressed Parquet.

    Writes one Parquet file per event type (gameEvents, trackerEvents,
    messageEvents) with columns: filename, loop (game tick),
    evtTypeName, and the full event data as a JSON VARCHAR.

    Files are partitioned by evtTypeName within each Parquet file.
    NOT loaded into DuckDB — preserved on disk for potential Phase 02 use.

    Args:
        raw_dir: Path to the sc2egset raw/ directory.
        output_dir: Directory to write Parquet files to.
        batch_size: Number of replay files to process per batch.
        max_object_size: DuckDB maximum_object_size for large JSONs.

    Returns:
        Dict mapping event type name to total row count extracted.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    output_dir.mkdir(parents=True, exist_ok=True)

    event_types = ["gameEvents", "trackerEvents", "messageEvents"]
    counts: dict[str, int] = {et: 0 for et in event_types}

    # Collect all replay files
    replay_files = sorted(raw_dir.glob("*/*_data/*.SC2Replay.json"))
    total_files = len(replay_files)
    logger.info("extract_events_to_parquet: found %d replay files", total_files)

    for et in event_types:
        writer: pq.ParquetWriter | None = None
        parquet_path = output_dir / f"{et}.parquet"

        try:
            for batch_start in range(0, total_files, batch_size):
                batch_files = replay_files[batch_start:batch_start + batch_size]
                batch_rows: list[dict[str, Any]] = []

                for fpath in batch_files:
                    try:
                        with open(fpath) as f:
                            data = json.load(f)
                    except (json.JSONDecodeError, OSError) as e:
                        logger.warning("Skipping %s: %s", fpath.name, e)
                        continue

                    events = data.get(et, [])
                    fname = fpath.name
                    for evt in events:
                        batch_rows.append({
                            "filename": fname,
                            "loop": evt.get("loop", 0),
                            "evtTypeName": evt.get("evtTypeName", ""),
                            "event_data": json.dumps(evt),
                        })

                if batch_rows:
                    table = pa.table({
                        "filename": pa.array(
                            [r["filename"] for r in batch_rows], type=pa.string()
                        ),
                        "loop": pa.array(
                            [r["loop"] for r in batch_rows], type=pa.int64()
                        ),
                        "evtTypeName": pa.array(
                            [r["evtTypeName"] for r in batch_rows], type=pa.string()
                        ),
                        "event_data": pa.array(
                            [r["event_data"] for r in batch_rows], type=pa.string()
                        ),
                    })

                    if writer is None:
                        writer = pq.ParquetWriter(
                            parquet_path,
                            table.schema,
                            compression="zstd",
                        )
                    writer.write_table(table)
                    counts[et] += len(batch_rows)

                if batch_start % (batch_size * 10) == 0 and batch_start > 0:
                    logger.info(
                        "%s: processed %d/%d files, %d rows so far",
                        et, batch_start, total_files, counts[et],
                    )
        finally:
            if writer is not None:
                writer.close()

        logger.info("%s: %d total rows -> %s", et, counts[et], parquet_path)

    return counts


def load_map_aliases_raw(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    should_drop: bool = True,
) -> int:
    """Materialise map_aliases_raw from all tournament mapping files.

    Each tournament directory may contain a map_foreign_to_english_mapping.json
    file mapping foreign map names to English map names. This function loads
    all such files into a single table with a tournament provenance column.
    The filename column stores the mapping file's path relative to raw_dir
    (Invariant I10).

    Args:
        con: Active DuckDB connection (read-write).
        raw_dir: Path to the sc2egset raw/ directory.
        should_drop: If True, drop existing map_aliases_raw before creating.

    Returns:
        Row count in map_aliases_raw after ingestion.
    """
    if should_drop:
        con.execute(_DROP_IF_EXISTS_QUERY.format(table="map_aliases_raw"))
        logger.info("Dropped existing map_aliases_raw table.")

    con.execute(_MAP_ALIASES_CREATE_QUERY)

    tournament_dirs = _discover_tournament_dirs(raw_dir)
    files_loaded = 0

    for t_dir in tournament_dirs:
        mapping_file = t_dir / "map_foreign_to_english_mapping.json"
        if not mapping_file.exists():
            continue

        tournament_name = t_dir.name
        json_content = mapping_file.read_text()
        data = json.loads(json_content)
        rows = [
            (tournament_name, foreign, english, str(mapping_file.relative_to(raw_dir)))
            for foreign, english in data.items()
        ]
        con.executemany(
            "INSERT INTO map_aliases_raw VALUES (?, ?, ?, ?)", rows
        )
        files_loaded += 1

    n = _count_rows(con, "map_aliases_raw")
    logger.info("map_aliases_raw: %d rows from %d tournament files", n, files_loaded)
    return n


def load_all_raw_tables(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    *,
    should_drop: bool = True,
    max_object_size: int = _DEFAULT_MAX_OBJECT_SIZE,
) -> dict[str, int]:
    """Materialise all DuckDB tables for sc2egset.

    Convenience wrapper that calls load_replays_meta_raw,
    load_replay_players_raw, and load_map_aliases_raw. Does NOT extract
    events to Parquet (call extract_events_to_parquet separately).

    Args:
        con: Active DuckDB connection (read-write).
        raw_dir: Path to the sc2egset raw/ directory.
        should_drop: Passed through to each individual loader.
        max_object_size: DuckDB maximum_object_size for large JSONs.

    Returns:
        Dict mapping table name to row count.
    """
    counts: dict[str, int] = {}
    counts["replays_meta_raw"] = load_replays_meta_raw(
        con, raw_dir, should_drop=should_drop, max_object_size=max_object_size
    )
    counts["replay_players_raw"] = load_replay_players_raw(
        con, raw_dir, should_drop=should_drop
    )
    counts["map_aliases_raw"] = load_map_aliases_raw(
        con, raw_dir, should_drop=should_drop
    )
    logger.info("load_all_raw_tables complete: %s", counts)
    return counts
