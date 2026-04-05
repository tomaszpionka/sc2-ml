"""Phase 0 ingestion audit — verify raw data availability, identifier
reconciliation, and dead-field status before any downstream exploration.

Each public function maps to one roadmap step (0.1–0.9).  The orchestrator
``run_phase_0_audit`` runs them in sequence and returns a summary dict.
"""

import json
import logging
import random
import re
import time
from pathlib import Path

import duckdb

from rts_predict.sc2.config import (
    IN_GAME_MANIFEST_PATH,
    IN_GAME_PARQUET_DIR,
    REPLAYS_SOURCE_DIR,
    REPORTS_DIR,
)
from rts_predict.sc2.data.ingestion import (
    audit_raw_data_availability,
    load_in_game_data_to_duckdb,
    load_map_translations,
    move_data_to_duck_db,
    run_in_game_extraction,
)
from rts_predict.sc2.data.processing import create_raw_enriched_view

logger = logging.getLogger(__name__)

_REPLAY_ID_REGEX = r"([0-9a-f]{32})\.SC2Replay\.json$"

# ── SQL constants ────────────────────────────────────────────────────────────

_APM_MMR_ZERO_RATE_QUERY = """
    SELECT
        COUNT(*) AS total_player_slots,
        SUM(CASE WHEN (entry.value->>'$.APM')::INTEGER = 0
                  OR (entry.value->>'$.APM') IS NULL THEN 1 ELSE 0 END) AS apm_zero_or_null,
        SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER = 0
                  OR (entry.value->>'$.MMR') IS NULL THEN 1 ELSE 0 END) AS mmr_zero_or_null
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
"""

_ORPHANS_TRACKER_NOT_RAW_QUERY = """
    SELECT t.replay_id FROM (
        SELECT DISTINCT regexp_extract(match_id, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1)
            AS replay_id
        FROM tracker_events_raw
    ) t LEFT JOIN (
        SELECT DISTINCT regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1)
            AS replay_id
        FROM raw
    ) r ON t.replay_id = r.replay_id
    WHERE r.replay_id IS NULL
"""

_ORPHANS_RAW_NOT_TRACKER_QUERY = """
    SELECT r.replay_id FROM (
        SELECT DISTINCT regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1)
            AS replay_id
        FROM raw
    ) r LEFT JOIN (
        SELECT DISTINCT regexp_extract(match_id, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1)
            AS replay_id
        FROM tracker_events_raw
    ) t ON r.replay_id = t.replay_id
    WHERE t.replay_id IS NULL
"""


# ── Step 0.1 ─────────────────────────────────────────────────────────────────


def run_source_audit(
    replays_dir: Path = REPLAYS_SOURCE_DIR,
    output_path: Path | None = None,
) -> dict[str, int]:
    """Step 0.1 — Audit raw source file availability.

    Delegates to ``ingestion.audit_raw_data_availability()`` and writes
    the result as JSON to ``reports/00_source_audit.json``.
    """
    counts = audit_raw_data_availability()

    if output_path is None:
        output_path = REPORTS_DIR / "00_01_source_audit.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(counts, indent=2))
    logger.info(f"Source audit written to {output_path}")

    if counts.get("stripped", 0) > 0:
        logger.critical(
            f"{counts['stripped']} files have been stripped of event data! "
            "Recovery plan needed before proceeding."
        )

    return counts


# ── Step 0.2 ─────────────────────────────────────────────────────────────────


def validate_tournament_name_extraction(
    replays_dir: Path = REPLAYS_SOURCE_DIR,
    n_tournaments: int = 5,
    n_files_per_tournament: int = 10,
    output_path: Path | None = None,
) -> list[dict]:
    """Step 0.2 — Validate tournament name extraction from file paths.

    Samples tournament directories and checks that ``split_part(filename, '/', -3)``
    produces the correct tournament name.
    """
    rng = random.Random(42)

    tournament_dirs = [
        d for d in replays_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
    ]
    sampled_tournaments = rng.sample(tournament_dirs, min(n_tournaments, len(tournament_dirs)))

    results: list[dict] = []
    for tourn_dir in sampled_tournaments:
        files = list(tourn_dir.rglob("*_data/*.SC2Replay.json"))
        sampled_files = rng.sample(files, min(n_files_per_tournament, len(files)))

        for f in sampled_files:
            extracted = f.parts[-3]
            expected = tourn_dir.name
            results.append({
                "tournament_dir": tourn_dir.name,
                "file_path": str(f.relative_to(replays_dir)),
                "extracted_name": extracted,
                "expected_name": expected,
                "match": extracted == expected,
            })

    if output_path is None:
        output_path = REPORTS_DIR / "00_02_tournament_name_validation.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = ["Tournament Name Extraction Validation", "=" * 40, ""]
    for r in results:
        status = "OK" if r["match"] else "MISMATCH"
        lines.append(f"[{status}] {r['file_path']}")
        lines.append(f"  extracted: {r['extracted_name']}  expected: {r['expected_name']}")
    match_count = sum(1 for r in results if r["match"])
    lines.append(f"\n{match_count}/{len(results)} correct")
    output_path.write_text("\n".join(lines))
    logger.info(f"Tournament name validation written to {output_path}")

    return results


# ── Step 0.3 ─────────────────────────────────────────────────────────────────


def write_replay_id_spec(
    replays_dir: Path = REPLAYS_SOURCE_DIR,
    output_path: Path | None = None,
) -> str:
    """Step 0.3 — Write the replay_id specification with worked examples.

    Finds 3 sample files from different tournaments, computes replay_id from
    both absolute and relative paths, and confirms they match.
    """
    tournament_dirs = [
        d for d in replays_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
    ]
    samples: list[Path] = []
    for td in tournament_dirs[:3]:
        files = list(td.rglob("*_data/*.SC2Replay.json"))
        if files:
            samples.append(files[0])

    lines = [
        "# replay_id Specification",
        "",
        "## Definition",
        "",
        "`replay_id` is the 32-character MD5 hex prefix extracted from the replay filename.",
        "",
        "## Extraction",
        "",
        "**SQL:**",
        "```sql",
        "regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1)",
        "```",
        "",
        "**Python:**",
        "```python",
        "re.search(r'([0-9a-f]{32})\\.SC2Replay\\.json$', path).group(1)",
        "```",
        "",
        "## Worked Examples",
        "",
    ]

    for sample in samples:
        abs_match = re.search(_REPLAY_ID_REGEX, str(sample))
        rel_path = str(sample.relative_to(replays_dir))
        rel_match = re.search(_REPLAY_ID_REGEX, rel_path)

        abs_id = abs_match.group(1) if abs_match else "NOT FOUND"
        rel_id = rel_match.group(1) if rel_match else "NOT FOUND"

        lines.append(f"### {sample.name}")
        lines.append(f"- Absolute path ID: `{abs_id}`")
        lines.append(f"- Relative path ID: `{rel_id}`")
        lines.append(f"- Match: {'YES' if abs_id == rel_id else 'NO'}")
        lines.append("")

    md = "\n".join(lines)

    if output_path is None:
        output_path = REPORTS_DIR / "00_03_replay_id_spec.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md)
    logger.info(f"Replay ID spec written to {output_path}")

    return md


# ── Step 0.4 ─────────────────────────────────────────────────────────────────


def run_path_a_smoke_test(
    tournament_name: str = "2016_IEM_10_Taipei",
    replays_dir: Path = REPLAYS_SOURCE_DIR,
    output_path: Path | None = None,
) -> dict:
    """Step 0.4 — Single-tournament smoke test using an in-memory DuckDB.

    Ingests one tournament's data and validates schema, row counts,
    identifier extraction, and APM/MMR zero-rate.
    """
    json_glob = str(replays_dir / tournament_name / "**/*.SC2Replay.json")

    # Count files on disk
    tourn_path = replays_dir / tournament_name
    file_count = len(list(tourn_path.rglob("*.SC2Replay.json")))

    result: dict = {"tournament": tournament_name, "file_count": file_count}

    con = duckdb.connect(":memory:")
    try:
        con.execute(f"""
            CREATE TABLE raw AS
            SELECT * FROM read_json(
                '{json_glob}',
                union_by_name = true,
                filename = true,
                columns = {{
                    'header': 'JSON', 'initData': 'JSON', 'details': 'JSON',
                    'metadata': 'JSON', 'ToonPlayerDescMap': 'JSON'
                }}
            )
        """)

        # Schema
        schema = con.execute("DESCRIBE raw").df()
        result["schema"] = schema.to_dict()

        # Row count
        row = con.execute("SELECT count(*) FROM raw").fetchone()
        assert row is not None
        row_count = row[0]
        result["row_count"] = row_count
        result["row_count_matches_files"] = row_count == file_count

        # Null check
        null_df = con.execute("""
            SELECT
                SUM(CASE WHEN header IS NULL THEN 1 ELSE 0 END) AS null_header,
                SUM(CASE WHEN "initData" IS NULL THEN 1 ELSE 0 END) AS null_initData,
                SUM(CASE WHEN details IS NULL THEN 1 ELSE 0 END) AS null_details,
                SUM(CASE WHEN metadata IS NULL THEN 1 ELSE 0 END) AS null_metadata,
                SUM(CASE WHEN "ToonPlayerDescMap" IS NULL THEN 1 ELSE 0 END) AS null_tpdm
            FROM raw
        """).df()
        result["null_counts"] = null_df.iloc[0].to_dict()

        # Identifier extraction on 3 sample rows
        samples = con.execute("""
            SELECT
                filename,
                split_part(filename, '/', -3) AS tournament_dir,
                regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id
            FROM raw LIMIT 3
        """).df()
        result["identifier_samples"] = samples.to_dict()

        # APM/MMR zero-rate
        apm_mmr = con.execute(_APM_MMR_ZERO_RATE_QUERY).df()
        result["apm_mmr"] = apm_mmr.iloc[0].to_dict()

        # Spot-check 3 rows against source JSON
        spot_rows = con.execute(
            "SELECT filename, metadata->>'$.mapName' AS map_name FROM raw LIMIT 3"
        ).fetchall()
        spot_checks = []
        for fname, map_name in spot_rows:
            src_path = Path(fname)
            if src_path.exists():
                with open(src_path, "r", encoding="utf-8") as f:
                    src_data = json.load(f)
                src_map = src_data.get("metadata", {}).get("mapName", "")
                spot_checks.append({
                    "filename": fname,
                    "db_map": map_name,
                    "src_map": src_map,
                    "match": map_name == src_map,
                })
        result["spot_checks"] = spot_checks

    finally:
        con.close()

    # Write report
    if output_path is None:
        output_path = REPORTS_DIR / "00_04_path_a_smoke_test.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Path A Smoke Test — {tournament_name}",
        "",
        f"- Files on disk: {file_count}",
        f"- Rows in raw: {result.get('row_count', 'N/A')}",
        f"- Row count matches: {result.get('row_count_matches_files', 'N/A')}",
        "",
        "## APM/MMR Zero-Rate",
        "",
    ]
    apm_info = result.get("apm_mmr", {})
    for k, v in apm_info.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Identifier Samples")
    lines.append("")
    lines.append("See report dict for details.")
    output_path.write_text("\n".join(lines))
    logger.info(f"Path A smoke test written to {output_path}")

    return result


# ── Step 0.5 ─────────────────────────────────────────────────────────────────


def run_full_path_a_ingestion(
    con: duckdb.DuckDBPyConnection,
    output_path: Path | None = None,
) -> dict:
    """Step 0.5 — Full Path A ingestion with row count and APM/MMR verification."""
    start = time.time()
    move_data_to_duck_db(con, should_drop=True)
    elapsed = time.time() - start

    row = con.execute("SELECT count(*) FROM raw").fetchone()
    assert row is not None
    row_count = row[0]

    # Compare to step 0.1 audit total if available
    audit_path = REPORTS_DIR / "00_01_source_audit.json"
    audit_total = None
    if audit_path.exists():
        audit_data = json.loads(audit_path.read_text())
        audit_total = audit_data.get("total")

    # APM/MMR zero-rate on full corpus
    apm_mmr = con.execute(_APM_MMR_ZERO_RATE_QUERY).df()

    result = {
        "row_count": row_count,
        "audit_total": audit_total,
        "row_count_matches_audit": row_count == audit_total if audit_total else None,
        "elapsed_seconds": elapsed,
        "apm_mmr": apm_mmr.iloc[0].to_dict(),
    }

    if output_path is None:
        output_path = REPORTS_DIR / "00_05_full_ingestion_log.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "Full Path A Ingestion Log",
        f"Elapsed: {elapsed:.1f}s",
        f"Row count: {row_count}",
        f"Audit total: {audit_total}",
        f"Match: {result['row_count_matches_audit']}",
        "",
        "APM/MMR zero-rate:",
    ]
    for k, v in result["apm_mmr"].items():
        lines.append(f"  {k}: {v}")

    if audit_total and row_count != audit_total:
        lines.append(
            f"\nWARNING: Row count ({row_count}) differs from audit total ({audit_total}). "
            "This may be due to the glob pattern difference "
            "(move_data_to_duck_db uses **/*.SC2Replay.json vs */data/*.SC2Replay.json)."
        )

    output_path.write_text("\n".join(lines))
    logger.info(f"Full ingestion log written to {output_path}")

    return result


# ── Step 0.7 ─────────────────────────────────────────────────────────────────


def run_path_b_extraction(
    con: duckdb.DuckDBPyConnection,
    parquet_dir: Path = IN_GAME_PARQUET_DIR,
    output_path: Path | None = None,
) -> dict:
    """Step 0.7 — Run Path B extraction and load into DuckDB."""
    start_extract = time.time()
    run_in_game_extraction(parquet_dir=parquet_dir)
    extract_elapsed = time.time() - start_extract

    # Count Parquet batch files
    batch_count = len(list(parquet_dir.glob("tracker_events_batch_*.parquet")))

    start_load = time.time()
    load_in_game_data_to_duckdb(con, parquet_dir, should_drop=True)
    load_elapsed = time.time() - start_load

    # Row counts
    row = con.execute("SELECT count(*) FROM tracker_events_raw").fetchone()
    assert row is not None
    tracker_count = row[0]
    row = con.execute("SELECT count(*) FROM game_events_raw").fetchone()
    assert row is not None
    game_count = row[0]
    row = con.execute("SELECT count(*) FROM match_player_map").fetchone()
    assert row is not None
    player_map_count = row[0]

    # Manifest stats
    extracted = 0
    skipped = 0
    if IN_GAME_MANIFEST_PATH.exists():
        manifest = json.loads(IN_GAME_MANIFEST_PATH.read_text())
        extracted = sum(1 for v in manifest.values() if v is True)
        skipped = sum(1 for v in manifest.values() if v is not True)

    result = {
        "extract_elapsed_seconds": extract_elapsed,
        "load_elapsed_seconds": load_elapsed,
        "batch_count": batch_count,
        "tracker_events_count": tracker_count,
        "game_events_count": game_count,
        "match_player_map_count": player_map_count,
        "manifest_extracted": extracted,
        "manifest_skipped": skipped,
    }

    if output_path is None:
        output_path = REPORTS_DIR / "00_07_path_b_extraction_log.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "Path B Extraction Log",
        f"Extraction time: {extract_elapsed:.1f}s",
        f"Loading time: {load_elapsed:.1f}s",
        f"Parquet batches: {batch_count}",
        f"tracker_events_raw rows: {tracker_count}",
        f"game_events_raw rows: {game_count}",
        f"match_player_map rows: {player_map_count}",
        f"Manifest: {extracted} extracted, {skipped} skipped",
    ]
    output_path.write_text("\n".join(lines))
    logger.info(f"Path B extraction log written to {output_path}")

    return result


# ── Step 0.8 ─────────────────────────────────────────────────────────────────


def validate_path_a_b_join(
    con: duckdb.DuckDBPyConnection,
    output_path: Path | None = None,
) -> dict:
    """Step 0.8 — Validate that Path A (raw) and Path B (tracker) join cleanly."""
    orphans_tracker = con.execute(_ORPHANS_TRACKER_NOT_RAW_QUERY).fetchall()
    orphans_raw = con.execute(_ORPHANS_RAW_NOT_TRACKER_QUERY).fetchall()

    orphan_tracker_ids = [r[0] for r in orphans_tracker]
    orphan_raw_ids = [r[0] for r in orphans_raw]

    join_clean = len(orphan_tracker_ids) == 0

    # Cross-reference with step 0.1 audit
    audit_path = REPORTS_DIR / "00_01_source_audit.json"
    stripped_count = None
    if audit_path.exists():
        audit_data = json.loads(audit_path.read_text())
        stripped_count = audit_data.get("stripped")

    result = {
        "orphans_in_tracker_not_raw": len(orphan_tracker_ids),
        "orphans_in_raw_not_tracker": len(orphan_raw_ids),
        "join_clean": join_clean,
        "stripped_count_from_audit": stripped_count,
        "orphan_tracker_ids": orphan_tracker_ids[:20],
        "orphan_raw_ids": orphan_raw_ids[:20],
    }

    if output_path is None:
        output_path = REPORTS_DIR / "00_08_join_validation.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Path A ↔ B Join Validation",
        "",
        f"- Orphans in tracker_events_raw not in raw: {len(orphan_tracker_ids)}",
        f"- Orphans in raw not in tracker_events_raw: {len(orphan_raw_ids)}",
        f"- Join clean (no tracker orphans): **{join_clean}**",
        "",
    ]
    if stripped_count is not None:
        lines.append(
            f"Stripped files from audit: {stripped_count} "
            f"(expected ≈ orphans in raw not tracker: {len(orphan_raw_ids)})"
        )
    if orphan_tracker_ids:
        lines.append("\n## Tracker orphan IDs (first 20)")
        for oid in orphan_tracker_ids[:20]:
            lines.append(f"- `{oid}`")
    if orphan_raw_ids:
        lines.append("\n## Raw orphan IDs (first 20)")
        for oid in orphan_raw_ids[:20]:
            lines.append(f"- `{oid}`")

    output_path.write_text("\n".join(lines))
    logger.info(f"Join validation written to {output_path}")

    return result


# ── Step 0.9 ─────────────────────────────────────────────────────────────────


def validate_map_translation_coverage(
    con: duckdb.DuckDBPyConnection,
    output_path: Path | None = None,
) -> dict:
    """Step 0.9 — Check how many distinct map names have translations."""
    load_map_translations(con)

    row = con.execute("SELECT count(*) FROM map_translation").fetchone()
    assert row is not None
    translation_count = row[0]
    row = con.execute(
        "SELECT count(DISTINCT metadata->>'$.mapName') FROM raw"
    ).fetchone()
    assert row is not None
    distinct_maps = row[0]

    untranslated = con.execute("""
        SELECT DISTINCT metadata->>'$.mapName' AS map_name
        FROM raw
        WHERE (metadata->>'$.mapName') NOT IN (
            SELECT foreign_name FROM map_translation
        )
    """).fetchall()
    untranslated_names = [r[0] for r in untranslated]

    result = {
        "translation_count": translation_count,
        "distinct_map_names": distinct_maps,
        "untranslated_count": len(untranslated_names),
        "untranslated_names": untranslated_names,
    }

    if output_path is None:
        output_path = REPORTS_DIR / "00_09_map_translation_coverage.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build CSV: all distinct map names with translation status
    all_maps = con.execute("""
        SELECT DISTINCT
            r.map_name,
            CASE WHEN mt.foreign_name IS NOT NULL THEN 'yes' ELSE 'no' END AS has_translation
        FROM (SELECT DISTINCT metadata->>'$.mapName' AS map_name FROM raw) r
        LEFT JOIN map_translation mt ON mt.foreign_name = r.map_name
        ORDER BY r.map_name
    """).fetchall()

    csv_lines = ["map_name,has_translation"]
    for name, has in all_maps:
        csv_lines.append(f"{name},{has}")
    output_path.write_text("\n".join(csv_lines))
    logger.info(f"Map translation coverage written to {output_path}")

    return result


# ── Orchestrator ─────────────────────────────────────────────────────────────


def run_phase_0_audit(
    con: duckdb.DuckDBPyConnection,
    steps: list[str] | None = None,
) -> dict[str, dict]:
    """Run Phase 0 audit steps in order.

    Args:
        con: DuckDB connection (used for steps 0.5–0.9).
        steps: Optional list of step IDs (e.g. ``["0.1", "0.2"]``).
               If ``None``, runs all steps.

    Returns:
        Dict mapping step ID to result dict.
    """
    all_steps = ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9"]
    run_steps = steps if steps else all_steps

    results: dict[str, dict] = {}

    if "0.1" in run_steps:
        logger.info("=== Step 0.1: Source audit ===")
        results["0.1"] = run_source_audit()

    if "0.2" in run_steps:
        logger.info("=== Step 0.2: Tournament name validation ===")
        results["0.2"] = {"samples": validate_tournament_name_extraction()}

    if "0.3" in run_steps:
        logger.info("=== Step 0.3: Replay ID spec ===")
        results["0.3"] = {"spec": write_replay_id_spec()}

    if "0.4" in run_steps:
        logger.info("=== Step 0.4: Path A smoke test ===")
        results["0.4"] = run_path_a_smoke_test()

    if "0.5" in run_steps:
        logger.info("=== Step 0.5: Full Path A ingestion ===")
        results["0.5"] = run_full_path_a_ingestion(con)

    if "0.6" in run_steps:
        logger.info("=== Step 0.6: Create raw_enriched view ===")
        create_raw_enriched_view(con)
        results["0.6"] = {"status": "raw_enriched view created"}

    if "0.7" in run_steps:
        logger.info("=== Step 0.7: Path B extraction ===")
        results["0.7"] = run_path_b_extraction(con)

    if "0.8" in run_steps:
        logger.info("=== Step 0.8: Path A ↔ B join validation ===")
        results["0.8"] = validate_path_a_b_join(con)

    if "0.9" in run_steps:
        logger.info("=== Step 0.9: Map translation coverage ===")
        results["0.9"] = validate_map_translation_coverage(con)

    logger.info(f"Phase 0 audit complete. Steps run: {list(results.keys())}")
    return results
