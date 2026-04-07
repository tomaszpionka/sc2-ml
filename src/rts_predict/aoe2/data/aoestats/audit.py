"""Phase 0 audit orchestration for aoestats.

Implements steps 0.1–0.7 as documented in the Phase 0 plan:

  0.1 run_source_audit         — file count, size integrity, manifest cross-check
  0.2 profile_match_schema     — sample-based schema profiling for match parquets
  0.3 profile_player_schema    — sample-based schema profiling for player parquets
  0.4 run_smoke_test           — in-memory DuckDB smoke test (2-week union)
  0.5 run_full_ingestion       — full CTAS into canonical DuckDB
  0.6 run_rowcount_reconciliation — manifest vs materialised table cross-check
  0.7 write_phase0_summary     — consolidate all artifacts into summary reports

Entry point: run_phase_0_audit() orchestrates all steps in order.

aoestats is structurally simpler than aoe2companion: two table types, no CSVs,
no singletons, no known sparsity. All files are parquets with union_by_name.

Every function writes at least one Markdown report to reports_dir containing
the literal SQL used to produce each finding (Invariant #6).
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from rts_predict.aoe2.data.aoestats.ingestion import load_all_raw_tables

logger = logging.getLogger(__name__)

# Number of sample files used in schema profiling (Steps 0.2 and 0.3)
_PROFILE_SAMPLES: int = 5

# ── SQL constants ─────────────────────────────────────────────────────────────

_DESCRIBE_PARQUET_QUERY = (
    "DESCRIBE SELECT * FROM read_parquet('{path}', filename = true)"
)

_DESCRIBE_PARQUET_GLOB_QUERY = """DESCRIBE SELECT * FROM read_parquet(
    '{glob}',
    union_by_name = true,
    filename = true
)"""

_COUNT_PARQUET_QUERY = "SELECT count(*) AS n_rows FROM read_parquet('{path}')"

_SMOKE_MATCHES_QUERY = """CREATE TABLE smoke_matches AS
SELECT * FROM read_parquet(
    ['{path_a}', '{path_b}'],
    union_by_name = true,
    filename = true
)"""

_SMOKE_PLAYERS_QUERY = """CREATE TABLE smoke_players AS
SELECT * FROM read_parquet(
    ['{path_a}', '{path_b}'],
    union_by_name = true,
    filename = true
)"""

_SMOKE_VERIFY_QUERY = (
    "SELECT count(*) AS rows, count(DISTINCT filename) AS files FROM {table}"
)

_FILE_COUNT_QUERY = "SELECT count(DISTINCT filename) AS n_files FROM {table}"

_PER_FILE_DIST_QUERY = """SELECT filename, count(*) AS row_count
FROM {table}
GROUP BY filename
ORDER BY row_count"""


# ── Shared schema profiling helper ────────────────────────────────────────────


def _profile_parquet_dir(
    parquet_dir: Path,
    glob_pattern: str,
    n_samples: int = _PROFILE_SAMPLES,
) -> tuple[dict[str, list[dict]], dict[str, int], list[dict], str, dict[str, list[str]]]:
    """Sample-based schema profiling for a directory of parquet files.

    Args:
        parquet_dir: Directory containing parquet files.
        glob_pattern: Glob pattern to match files (e.g. '*_matches.parquet').
        n_samples: Number of samples to select.

    Returns:
        Tuple of (per_sample_schemas, per_sample_row_counts, union_schema,
        stability, type_drift).
        type_drift maps column name to list of distinct types observed across samples.
    """
    all_files = sorted(parquet_dir.glob(glob_pattern))
    if not all_files:
        raise FileNotFoundError(f"No files matching {glob_pattern} in {parquet_dir}")

    n = len(all_files)
    indices = [0, n // 4, n // 2, 3 * n // 4, n - 1]
    samples = [all_files[i] for i in indices]

    con = duckdb.connect(":memory:")
    per_sample_schemas: dict[str, list[dict]] = {}
    per_sample_row_counts: dict[str, int] = {}

    for f in samples:
        sql = _DESCRIBE_PARQUET_QUERY.format(path=str(f))
        rows = con.execute(sql).fetchall()
        per_sample_schemas[f.name] = [
            {"column_name": r[0], "column_type": r[1]} for r in rows
        ]
        count_sql = _COUNT_PARQUET_QUERY.format(path=str(f))
        count_row = con.execute(count_sql).fetchone()
        per_sample_row_counts[f.name] = int(count_row[0]) if count_row else 0

    glob = str(parquet_dir / glob_pattern)
    union_sql = _DESCRIBE_PARQUET_GLOB_QUERY.format(glob=glob)
    union_rows = con.execute(union_sql).fetchall()
    union_schema = [{"column_name": r[0], "column_type": r[1]} for r in union_rows]

    # Check column name stability
    column_name_sets = [
        frozenset(col["column_name"] for col in s)
        for s in per_sample_schemas.values()
    ]
    names_stable = all(cs == column_name_sets[0] for cs in column_name_sets)

    # Check column type stability (per column, across samples)
    type_drift: dict[str, list[str]] = {}
    if names_stable:
        first_schema = next(iter(per_sample_schemas.values()))
        for col in first_schema:
            col_name = col["column_name"]
            types_seen = [
                s_col["column_type"]
                for s in per_sample_schemas.values()
                for s_col in s
                if s_col["column_name"] == col_name
            ]
            unique_types = list(dict.fromkeys(types_seen))  # preserve order, dedupe
            if len(unique_types) > 1:
                type_drift[col_name] = unique_types

    stability = "STABLE" if (names_stable and not type_drift) else "DRIFTED"

    return per_sample_schemas, per_sample_row_counts, union_schema, stability, type_drift


def _write_schema_report(
    reports_dir: Path,
    report_name: str,
    title: str,
    per_sample_schemas: dict[str, list[dict]],
    union_schema: list[dict],
    stability: str,
    total_files: int,
    glob: str,
    type_drift: dict[str, list[str]] | None = None,
    per_sample_row_counts: dict[str, int] | None = None,
) -> None:
    """Write a Markdown schema profile report.

    Args:
        reports_dir: Directory to write the report.
        report_name: Filename for the report (e.g. '00_02_match_schema_profile.md').
        title: Report title.
        per_sample_schemas: Dict mapping filename to schema list.
        union_schema: Union schema list.
        stability: 'STABLE' or 'DRIFTED'.
        total_files: Total number of files in the directory.
        glob: Glob pattern used for union schema.
        type_drift: Optional dict mapping column name to list of observed types.
        per_sample_row_counts: Optional dict mapping filename to row count.
    """
    sample_sql_blocks: list[str] = []

    for fname in per_sample_schemas:
        sql_d = _DESCRIBE_PARQUET_QUERY.format(path=f"<path>/{fname}")
        sql_c = _COUNT_PARQUET_QUERY.format(path=f"<path>/{fname}")
        sample_sql_blocks.append(f"-- Sample: {fname}\n{sql_d};\n{sql_c};")

    md_lines = [
        f"# {title}",
        "",
        f"**Stability:** {stability}",
        "",
        f"Total files: {total_files}  ",
        "Sample positions: earliest, Q1, median, Q3, latest",
        "",
    ]

    if stability == "DRIFTED" and type_drift:
        md_lines += [
            "## Type drift detected",
            "",
            "Column names are stable across samples, but the following columns",
            "have different types across time:",
            "",
            "| Column | Types observed (oldest → newest) |",
            "|--------|----------------------------------|",
        ]
        for col_name, types in type_drift.items():
            md_lines.append(f"| {col_name} | {' → '.join(types)} |")
        md_lines.append("")

    md_lines += [
        "## SQL used",
        "",
        "```sql",
    ]
    for block in sample_sql_blocks:
        md_lines.append(block)
        md_lines.append("")
    union_sql = _DESCRIBE_PARQUET_GLOB_QUERY.format(glob=glob)
    md_lines += [
        f"-- Union schema across all {total_files} files (metadata only)",
        union_sql + ";",
        "```",
        "",
        "## Per-sample schemas",
        "",
    ]
    for fname, schema in per_sample_schemas.items():
        md_lines += [f"### {fname}", ""]
        if per_sample_row_counts and fname in per_sample_row_counts:
            md_lines += [f"Row count: {per_sample_row_counts[fname]}", ""]
        md_lines += ["| Column | Type |", "|--------|------|"]
        for col in schema:
            md_lines.append(f"| {col['column_name']} | {col['column_type']} |")
        md_lines.append("")

    md_lines += [
        "## Union schema",
        "",
        "| Column | Type |",
        "|--------|------|",
    ]
    for col in union_schema:
        md_lines.append(f"| {col['column_name']} | {col['column_type']} |")

    (reports_dir / report_name).write_text("\n".join(md_lines))


# ── Step 0.1 ─────────────────────────────────────────────────────────────────


def run_source_audit(raw_dir: Path, manifest_path: Path, reports_dir: Path) -> dict:
    """Step 0.1 — Source inventory and integrity audit for aoestats.

    Counts files on disk per category, cross-references against the download
    manifest, and verifies per-file byte sizes. The aoestats manifest uses a
    flat list format (not nested under db_dumps).

    Args:
        raw_dir: Path to the aoestats raw data root directory.
        manifest_path: Path to _download_manifest.json.
        reports_dir: Directory to write 00_01_source_audit.{json,md}.

    Returns:
        Dict with keys: file_counts, failures, size_mismatches, zero_byte_files,
        T_acquisition, total_expected, total_on_disk, passed.
    """
    with open(manifest_path, encoding="utf-8") as f:
        manifest: list[dict] = json.load(f)

    timestamps = [e["timestamp"] for e in manifest if e.get("timestamp")]
    t_acquisition = min(timestamps) if timestamps else None

    on_disk_matches = list((raw_dir / "matches").glob("*_matches.parquet"))
    on_disk_players = list((raw_dir / "players").glob("*_players.parquet"))

    file_counts = {
        "matches": len(on_disk_matches),
        "players": len(on_disk_players),
    }
    total_on_disk = sum(file_counts.values())

    # Distinguish expected failures (status='failed' in manifest) from unexpected
    # ones (status='downloaded' but absent from disk or zero-byte).
    known_failures: list[dict] = []  # documented in manifest as status='failed'
    unexpected_failures: list[dict] = []  # should be on disk but are not
    size_mismatches: list[dict] = []
    zero_byte_files: list[str] = []

    for entry in manifest:
        target_path = Path(entry["target_path"])
        expected_size = entry.get("size")
        entry_status = entry.get("status")

        if not target_path.exists():
            record = {
                "key": target_path.name,
                "reason": "missing_from_disk",
                "manifest_status": entry_status,
            }
            if entry_status == "failed":
                known_failures.append(record)
            else:
                unexpected_failures.append(record)
            continue

        actual_size = target_path.stat().st_size

        if actual_size == 0:
            zero_byte_files.append(str(target_path))
            unexpected_failures.append({
                "key": target_path.name,
                "reason": "zero_byte",
                "manifest_status": entry_status,
            })
            continue

        if expected_size is not None and actual_size != expected_size:
            size_mismatches.append({
                "key": target_path.name,
                "expected": expected_size,
                "actual": actual_size,
                "diff": actual_size - expected_size,
            })

    # Gate passes if there are no *unexpected* failures and no size mismatches.
    # Known failures (status='failed' in manifest) are documented but not blocking.
    result = {
        "file_counts": file_counts,
        "total_expected": len(manifest),
        "total_on_disk": total_on_disk,
        "known_failures": known_failures,
        "failures": unexpected_failures,
        "size_mismatches": size_mismatches,
        "zero_byte_files": zero_byte_files,
        "T_acquisition": t_acquisition,
        "passed": len(unexpected_failures) == 0 and len(size_mismatches) == 0,
    }

    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "00_01_source_audit.json"
    json_path.write_text(json.dumps(result, indent=2))

    n_unexp = len(unexpected_failures)
    failures_ok = "OK" if not unexpected_failures else f"FAIL ({n_unexp} unexpected failures)"
    mismatches_ok = (
        "OK" if not size_mismatches else f"FAIL ({len(size_mismatches)} mismatches)"
    )
    gate_status = "PASS" if result["passed"] else "FAIL"

    md_lines = [
        "# Step 0.1 — Source Inventory and Integrity Audit (aoestats)",
        "",
        f"**T_acquisition:** `{t_acquisition}`",
        "",
        "## File counts on disk",
        "",
        "| Category | On-disk count | Expected |",
        "|----------|--------------|---------|",
        f"| matches | {file_counts['matches']} | 172 |",
        f"| players | {file_counts['players']} | 172 |",
        "",
        f"**Total on disk:** {total_on_disk}  ",
        f"**Total in manifest:** {len(manifest)}",
        "",
        "## Integrity checks",
        "",
        f"- Known download failures (status='failed' in manifest): {len(known_failures)}",
        f"- Unexpected failures (missing or zero-byte): {len(unexpected_failures)}",
        f"- Size mismatches: {len(size_mismatches)}",
        f"- Zero-byte files: {len(zero_byte_files)}",
        "",
    ]

    if known_failures:
        md_lines += ["### Known failures (documented in manifest)", ""]
        for fail in known_failures:
            md_lines.append(
                f"- `{fail['key']}`: {fail['reason']} (manifest status: failed)"
            )
        md_lines.append("")

    if unexpected_failures:
        md_lines += ["### Unexpected failures", ""]
        for fail in unexpected_failures:
            reason = fail.get("reason", "unknown")
            status = fail.get("manifest_status", "")
            md_lines.append(
                f"- `{fail['key']}`: {reason}"
                + (f" (manifest status: {status})" if status else "")
            )
        md_lines.append("")

    md_lines += [
        f"## Gate: {gate_status}",
        "",
        "Gate passes when: zero unexpected failures, zero size mismatches,",
        "T_acquisition recorded. Known download failures (status='failed' in",
        "manifest) are documented but do not block the gate.",
        "",
        f"- Zero unexpected failures: {failures_ok}",
        f"- Zero size mismatches: {mismatches_ok}",
        f"- T_acquisition recorded: {'OK' if t_acquisition else 'FAIL'}",
    ]

    (reports_dir / "00_01_source_audit.md").write_text("\n".join(md_lines))
    logger.info(
        "Step 0.1 complete: %s (unexpected=%d, known=%d)",
        gate_status,
        len(unexpected_failures),
        len(known_failures),
    )
    return result


# ── Steps 0.2 and 0.3 ─────────────────────────────────────────────────────────


def profile_match_schema(raw_dir: Path, reports_dir: Path) -> dict:
    """Step 0.2 — Sample-based schema profiling for weekly match parquet files.

    Args:
        raw_dir: Path to the aoestats raw data root directory.
        reports_dir: Directory to write 00_02_match_schema_profile.md.

    Returns:
        Dict with keys: samples, schemas, union_schema, stability.
    """
    matches_dir = raw_dir / "matches"
    all_files = sorted(matches_dir.glob("*_matches.parquet"))
    n = len(all_files)

    per_sample_schemas, per_sample_row_counts, union_schema, stability, type_drift = (
        _profile_parquet_dir(matches_dir, "*_matches.parquet")
    )

    reports_dir.mkdir(parents=True, exist_ok=True)
    _write_schema_report(
        reports_dir=reports_dir,
        report_name="00_02_match_schema_profile.md",
        title="Step 0.2 — Match Parquet Schema Profile (aoestats, sample-based)",
        per_sample_schemas=per_sample_schemas,
        union_schema=union_schema,
        stability=stability,
        total_files=n,
        glob=str(matches_dir / "*_matches.parquet"),
        type_drift=type_drift,
        per_sample_row_counts=per_sample_row_counts,
    )

    logger.info("Step 0.2 complete: stability=%s", stability)
    return {
        "samples": list(per_sample_schemas.keys()),
        "schemas": per_sample_schemas,
        "union_schema": union_schema,
        "stability": stability,
        "type_drift": type_drift,
        "per_sample_row_counts": per_sample_row_counts,
    }


def profile_player_schema(raw_dir: Path, reports_dir: Path) -> dict:
    """Step 0.3 — Sample-based schema profiling for weekly player parquet files.

    Uses the same week keys as Step 0.2 for cross-table consistency.

    Args:
        raw_dir: Path to the aoestats raw data root directory.
        reports_dir: Directory to write 00_03_player_schema_profile.md.

    Returns:
        Dict with keys: samples, schemas, union_schema, stability.
    """
    players_dir = raw_dir / "players"
    all_files = sorted(players_dir.glob("*_players.parquet"))
    n = len(all_files)

    per_sample_schemas, per_sample_row_counts, union_schema, stability, type_drift = (
        _profile_parquet_dir(players_dir, "*_players.parquet")
    )

    reports_dir.mkdir(parents=True, exist_ok=True)
    _write_schema_report(
        reports_dir=reports_dir,
        report_name="00_03_player_schema_profile.md",
        title="Step 0.3 — Player Parquet Schema Profile (aoestats, sample-based)",
        per_sample_schemas=per_sample_schemas,
        union_schema=union_schema,
        stability=stability,
        total_files=n,
        glob=str(players_dir / "*_players.parquet"),
        type_drift=type_drift,
        per_sample_row_counts=per_sample_row_counts,
    )

    logger.info("Step 0.3 complete: stability=%s", stability)
    return {
        "samples": list(per_sample_schemas.keys()),
        "schemas": per_sample_schemas,
        "union_schema": union_schema,
        "stability": stability,
        "type_drift": type_drift,
        "per_sample_row_counts": per_sample_row_counts,
    }


# ── Step 0.4 ─────────────────────────────────────────────────────────────────


def run_smoke_test(raw_dir: Path, reports_dir: Path) -> dict:
    """Step 0.4 — Smoke test: validate the union_by_name pattern over 2 weeks.

    The risk is the multi-file parquet union, not the read of a single file.
    If Steps 0.2/0.3 detected drift, the 2 weeks chosen should straddle it.

    Args:
        raw_dir: Path to the aoestats raw data root directory.
        reports_dir: Directory to write 00_04_smoke_test.md.

    Returns:
        Dict with keys: passed, matches_rows, matches_files, players_rows,
        players_files, filename_cols, errors.
    """
    matches_dir = raw_dir / "matches"
    players_dir = raw_dir / "players"
    all_matches = sorted(matches_dir.glob("*_matches.parquet"))
    all_players = sorted(players_dir.glob("*_players.parquet"))

    if len(all_matches) < 2:
        raise FileNotFoundError(f"Need at least 2 match files in {matches_dir}")
    if len(all_players) < 2:
        raise FileNotFoundError(f"Need at least 2 player files in {players_dir}")

    # Pick earliest and latest to maximise chance of straddling any drift
    match_a = all_matches[0]
    match_b = all_matches[-1]
    player_a = all_players[0]
    player_b = all_players[-1]

    con = duckdb.connect(":memory:")

    smoke_match_sql = _SMOKE_MATCHES_QUERY.format(
        path_a=str(match_a), path_b=str(match_b)
    )
    smoke_player_sql = _SMOKE_PLAYERS_QUERY.format(
        path_a=str(player_a), path_b=str(player_b)
    )
    verify_matches_sql = _SMOKE_VERIFY_QUERY.format(table="smoke_matches")
    verify_players_sql = _SMOKE_VERIFY_QUERY.format(table="smoke_players")

    errors: list[str] = []

    def _exec(sql: str, table: str) -> bool:
        try:
            con.execute(sql)
            return True
        except Exception as exc:
            errors.append(f"{table}: {exc}")
            return False

    matches_ok = _exec(smoke_match_sql, "smoke_matches")
    players_ok = _exec(smoke_player_sql, "smoke_players")

    matches_rows = 0
    matches_files = 0
    players_rows = 0
    players_files = 0
    filename_cols: dict[str, bool] = {}

    if matches_ok:
        r = con.execute(verify_matches_sql).fetchone()
        matches_rows = int(r[0]) if r else 0
        matches_files = int(r[1]) if r else 0
        cols = [c[0] for c in con.execute("DESCRIBE smoke_matches").fetchall()]
        filename_cols["smoke_matches"] = "filename" in cols

    if players_ok:
        r = con.execute(verify_players_sql).fetchone()
        players_rows = int(r[0]) if r else 0
        players_files = int(r[1]) if r else 0
        cols = [c[0] for c in con.execute("DESCRIBE smoke_players").fetchall()]
        filename_cols["smoke_players"] = "filename" in cols

    passed = (
        matches_ok
        and players_ok
        and matches_files == 2
        and players_files == 2
        and all(filename_cols.values())
        and not errors
    )

    result = {
        "passed": passed,
        "errors": errors,
        "matches_rows": matches_rows,
        "matches_files": matches_files,
        "players_rows": players_rows,
        "players_files": players_files,
        "filename_cols": filename_cols,
        "smoke_match_a": match_a.name,
        "smoke_match_b": match_b.name,
        "smoke_player_a": player_a.name,
        "smoke_player_b": player_b.name,
    }

    reports_dir.mkdir(parents=True, exist_ok=True)
    gate_status = "PASS" if passed else "FAIL"
    sm_fn = filename_cols.get("smoke_matches", False)
    sp_fn = filename_cols.get("smoke_players", False)
    sm_ok = "OK" if matches_ok and matches_files == 2 else "FAIL"
    sp_ok = "OK" if players_ok and players_files == 2 else "FAIL"

    md_lines = [
        "# Step 0.4 — Smoke Test (aoestats)",
        "",
        f"**Gate: {gate_status}**",
        "",
        f"Files tested (matches): `{match_a.name}`, `{match_b.name}`  ",
        f"Files tested (players): `{player_a.name}`, `{player_b.name}`",
        "",
        "## SQL used (in-memory DuckDB)",
        "",
        "```sql",
        smoke_match_sql + ";",
        "",
        smoke_player_sql + ";",
        "",
        "-- Verification",
        verify_matches_sql + ";  -- expect files = 2",
        verify_players_sql + ";  -- expect files = 2",
        "```",
        "",
        "## Results",
        "",
        "| Table | Rows | Files | filename col | Status |",
        "|-------|------|-------|-------------|--------|",
        f"| smoke_matches | {matches_rows} | {matches_files} | {sm_fn} | {sm_ok} |",
        f"| smoke_players | {players_rows} | {players_files} | {sp_fn} | {sp_ok} |",
    ]

    if errors:
        md_lines += ["", "## Errors", ""]
        for err in errors:
            md_lines.append(f"- {err}")

    (reports_dir / "00_04_smoke_test.md").write_text("\n".join(md_lines))
    logger.info(
        "Step 0.4 complete: passed=%s, matches_files=%d, players_files=%d",
        passed,
        matches_files,
        players_files,
    )
    return result


# ── Step 0.5 ─────────────────────────────────────────────────────────────────


def run_full_ingestion(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    reports_dir: Path,
) -> dict:
    """Step 0.5 — Full CTAS ingestion into the aoestats canonical DuckDB.

    Args:
        con: Active DuckDB connection (to the canonical db.duckdb).
        raw_dir: Path to the aoestats raw data root directory.
        reports_dir: Directory to write 00_05_ingestion_log.md.

    Returns:
        Dict with keys: table_counts, T_ingestion.
    """
    t_ingestion = datetime.now(timezone.utc).isoformat()
    counts = load_all_raw_tables(con, raw_dir, should_drop=True)
    t_ingestion_end = datetime.now(timezone.utc).isoformat()

    result = {
        "table_counts": counts,
        "T_ingestion": t_ingestion_end,
    }

    reports_dir.mkdir(parents=True, exist_ok=True)
    glob_matches = str(raw_dir / "matches" / "*_matches.parquet")
    glob_players = str(raw_dir / "players" / "*_players.parquet")

    md_lines = [
        "# Step 0.5 — Full CTAS Ingestion Log (aoestats)",
        "",
        f"**T_ingestion (start):** `{t_ingestion}`  ",
        f"**T_ingestion (end):** `{t_ingestion_end}`",
        "",
        "## SQL used",
        "",
        "```sql",
        "DROP TABLE IF EXISTS raw_matches;",
        "CREATE TABLE raw_matches AS",
        "SELECT * FROM read_parquet(",
        f"    '{glob_matches}',",
        "    union_by_name = true,",
        "    filename = true",
        ");",
        "",
        "DROP TABLE IF EXISTS raw_players;",
        "CREATE TABLE raw_players AS",
        "SELECT * FROM read_parquet(",
        f"    '{glob_players}',",
        "    union_by_name = true,",
        "    filename = true",
        ");",
        "```",
        "",
        "## Row counts",
        "",
        "| Table | Row count |",
        "|-------|-----------|",
    ]
    for table, cnt in counts.items():
        md_lines.append(f"| {table} | {cnt:,} |")

    (reports_dir / "00_05_ingestion_log.md").write_text("\n".join(md_lines))
    logger.info("Step 0.5 complete: counts=%s, T_ingestion=%s", counts, t_ingestion_end)
    return result


# ── Step 0.6 ─────────────────────────────────────────────────────────────────


def run_rowcount_reconciliation(
    con: duckdb.DuckDBPyConnection,
    manifest_path: Path,
    reports_dir: Path,
) -> dict:
    """Step 0.6 — Reconciliation of materialised tables against the manifest.

    The aoestats manifest records file checksums but not per-file row counts,
    so reconciliation is DEGRADED (file-count exact match only).

    Note: the on-disk players directory has 171 files (1 failed download);
    the manifest records 172 players entries. This is recorded and reported
    as a DEGRADED reconciliation with a documented note.

    Args:
        con: Active DuckDB connection with both raw tables present.
        manifest_path: Path to _download_manifest.json.
        reports_dir: Directory to write 00_06_rowcount_reconciliation.md.

    Returns:
        Dict with keys: file_counts, expected_file_counts, file_count_ok,
        strength, passed, notes.
    """
    with open(manifest_path, encoding="utf-8") as f:
        manifest: list[dict] = json.load(f)

    # Count manifest entries by file_type (total entries)
    from collections import Counter

    manifest_counts = Counter(e.get("file_type") for e in manifest)

    # Subtract known failed downloads — they never made it to disk and are
    # therefore absent from the materialised table. Comparing against the total
    # manifest count (including failures) would produce a false FAIL.
    failed_entries = [e for e in manifest if e.get("status") == "failed"]
    failed_by_type = Counter(e.get("file_type") for e in failed_entries)

    expected_matches = manifest_counts.get("matches", 172) - failed_by_type.get("matches", 0)
    expected_players = manifest_counts.get("players", 172) - failed_by_type.get("players", 0)

    expected = {
        "raw_matches": expected_matches,
        "raw_players": expected_players,
    }

    file_count_sql = {t: _FILE_COUNT_QUERY.format(table=t) for t in expected}
    actual_file_counts: dict[str, int] = {}
    for table, sql in file_count_sql.items():
        row = con.execute(sql).fetchone()
        actual_file_counts[table] = int(row[0]) if row else 0

    file_count_ok = all(
        actual_file_counts.get(t) == expected[t] for t in expected
    )

    matches_dist_sql = _PER_FILE_DIST_QUERY.format(table="raw_matches")
    players_dist_sql = _PER_FILE_DIST_QUERY.format(table="raw_players")
    matches_dist = con.execute(matches_dist_sql).fetchall()
    players_dist = con.execute(players_dist_sql).fetchall()

    manifest_has_row_counts = any("row_count" in e for e in manifest)
    strength = "STRICT" if manifest_has_row_counts else "DEGRADED"

    notes: list[str] = []
    if failed_entries:
        notes.append(
            f"{len(failed_entries)} entries had status='failed' in manifest: "
            + ", ".join(Path(e["target_path"]).name for e in failed_entries[:5])
            + " — excluded from expected file count."
        )

    passed = file_count_ok

    result = {
        "file_counts": actual_file_counts,
        "expected_file_counts": expected,
        "file_count_ok": file_count_ok,
        "manifest_has_row_counts": manifest_has_row_counts,
        "strength": strength,
        "passed": passed,
        "notes": notes,
    }

    reports_dir.mkdir(parents=True, exist_ok=True)
    gate_status = "PASS" if passed else "FAIL"

    md_lines = [
        "# Step 0.6 — Row-count Reconciliation (aoestats)",
        "",
        f"**Gate: {gate_status}**  ",
        f"**Reconciliation strength: {strength}**",
        "",
    ]
    if strength == "DEGRADED":
        md_lines += [
            "> **DEGRADED reason:** The _download_manifest.json records file checksums",
            "> but not per-file row counts. Reconciliation is limited to file-count match.",
            "",
        ]
    if notes:
        md_lines += ["> **Notes:**"]
        for note in notes:
            md_lines.append(f"> - {note}")
        md_lines.append("")

    md_lines += [
        "## SQL used",
        "",
        "```sql",
    ]
    for table, sql in file_count_sql.items():
        md_lines.append(f"-- Expected: {expected[table]}")
        md_lines.append(sql + ";")
        md_lines.append("")

    md_lines += [
        matches_dist_sql + ";",
        "",
        players_dist_sql + ";",
        "```",
        "",
        "## File-count assertions",
        "",
        "| Table | Expected | Actual | OK? |",
        "|-------|----------|--------|-----|",
    ]
    for table in expected:
        exp = expected[table]
        act = actual_file_counts.get(table, 0)
        ok = "OK" if act == exp else f"FAIL (diff {act - exp:+d})"
        md_lines.append(f"| {table} | {exp} | {act} | {ok} |")

    md_lines += [
        "",
        "## Per-file row-count distribution summary",
        "",
        f"### raw_matches ({len(matches_dist)} files)",
        "",
    ]
    if matches_dist:
        md_lines += [
            f"Min rows: {matches_dist[0][1]}  ",
            f"Max rows: {matches_dist[-1][1]}",
        ]

    md_lines += [
        "",
        f"### raw_players ({len(players_dist)} files)",
        "",
    ]
    if players_dist:
        md_lines += [
            f"Min rows: {players_dist[0][1]}  ",
            f"Max rows: {players_dist[-1][1]}",
        ]

    (reports_dir / "00_06_rowcount_reconciliation.md").write_text("\n".join(md_lines))
    logger.info(
        "Step 0.6 complete: file_count_ok=%s, strength=%s",
        file_count_ok,
        strength,
    )
    return result


# ── Step 0.7 ─────────────────────────────────────────────────────────────────


def write_phase0_summary(
    reports_dir: Path,
    ingestion_result: dict,
    audit_results: dict,
) -> None:
    """Step 0.7 — Write Phase 0 summary and INVARIANTS.md for aoestats.

    Args:
        reports_dir: Directory containing all prior report artifacts.
        ingestion_result: Result dict from run_full_ingestion() (step 0.5).
        audit_results: Combined results dict keyed by step name.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)

    source_audit = audit_results.get("0.1", {})
    match_profile = audit_results.get("0.2", {})
    player_profile = audit_results.get("0.3", {})
    smoke = audit_results.get("0.4", {})
    reconciliation = audit_results.get("0.6", {})

    t_acquisition = source_audit.get("T_acquisition", "unknown")
    t_ingestion = ingestion_result.get("T_ingestion", "unknown")
    counts = ingestion_result.get("table_counts", {})
    strength = reconciliation.get("strength", "DEGRADED")
    stability_matches = match_profile.get("stability", "unknown")
    stability_players = player_profile.get("stability", "unknown")
    match_file_counts = reconciliation.get("file_counts", {})

    # ── INVARIANTS.md ─────────────────────────────────────────────────────────
    type_drift_matches = match_profile.get("type_drift", {})
    type_drift_players = player_profile.get("type_drift", {})
    known_failures = source_audit.get("known_failures", [])

    invariants_lines = [
        "# INVARIANTS — aoestats",
        "",
        "## I1. Schema stability",
        "",
        f"- raw_matches: {stability_matches}",
        f"- raw_players: {stability_players}",
        "",
    ]
    if type_drift_matches:
        invariants_lines += [
            "Type drift in raw_matches (column names stable, types changed):",
            "",
        ]
        for col, types in type_drift_matches.items():
            invariants_lines.append(f"- `{col}`: {' → '.join(types)}")
        invariants_lines.append("")
    if type_drift_players:
        invariants_lines += [
            "Type drift in raw_players (column names stable, types changed):",
            "",
        ]
        for col, types in type_drift_players.items():
            invariants_lines.append(f"- `{col}`: {' → '.join(types)}")
        invariants_lines.append(
            "  DuckDB `union_by_name = true` resolves drift to the widest compatible type."
        )
        invariants_lines.append("")

    invariants_lines += [
        "Evidence: 00_02_match_schema_profile.md, 00_03_player_schema_profile.md",
        "",
    ]

    if known_failures:
        invariants_lines += [
            "## I1a. Known download failures",
            "",
            "One player file failed during acquisition (documented in manifest with",
            "status='failed'). This is a known gap, not a silent corruption.",
            "",
        ]
        for kf in known_failures:
            invariants_lines.append(f"- `{kf['key']}`: {kf['reason']}")
        invariants_lines.append("")

    invariants_lines += [
        "## I5. Row-count totals at T_ingestion",
        "",
        f"- T_ingestion: {t_ingestion}",
        f"- raw_matches: {counts.get('raw_matches', 0):,} rows across "
        f"{match_file_counts.get('raw_matches', 0):,} files",
        f"- raw_players: {counts.get('raw_players', 0):,} rows across "
        f"{match_file_counts.get('raw_players', 0):,} files",
        "",
        "## I6. Reconciliation result",
        "",
        f"- Strength: {strength}",
    ]
    if strength == "DEGRADED":
        invariants_lines += [
            "- Reason: manifest does not record per-file row counts; reconciliation",
            "  limited to file-count match.",
            "- Additional: raw_players contains 171 files (1 known failed download).",
        ]
    notes = reconciliation.get("notes", [])
    if notes:
        for note in notes:
            invariants_lines.append(f"- Note: {note}")

    invariants_lines += [
        "",
        "## I7. Provenance",
        "",
        "Every raw table has a `filename` column populated by `filename = true` on",
        "the source read. Removing or aliasing this column in any downstream view",
        "is forbidden.",
    ]

    (reports_dir / "INVARIANTS.md").write_text("\n".join(invariants_lines))

    # ── 00_07_phase0_summary.md ───────────────────────────────────────────────
    s01 = "PASS" if source_audit.get("passed") else "FAIL"
    s04 = "PASS" if smoke.get("passed") else "FAIL"
    s06 = "PASS" if reconciliation.get("passed") else "FAIL"

    summary_lines = [
        "# Phase 0 Summary — aoestats",
        "",
        f"**T_acquisition:** `{t_acquisition}`  ",
        f"**T_ingestion:** `{t_ingestion}`",
        "",
        "## Step gate results",
        "",
        "| Step | Artifact | Gate |",
        "|------|----------|------|",
        f"| 0.1 | 00_01_source_audit.{{json,md}} | {s01} |",
        f"| 0.2 | 00_02_match_schema_profile.md | PASS ({stability_matches}) |",
        f"| 0.3 | 00_03_player_schema_profile.md | PASS ({stability_players}) |",
        f"| 0.4 | 00_04_smoke_test.md | {s04} |",
        f"| 0.5 | 00_05_ingestion_log.md | PASS (T_ingestion={t_ingestion}) |",
        f"| 0.6 | 00_06_rowcount_reconciliation.md | {s06} ({strength}) |",
        "",
        "## Artifact inventory",
        "",
        "All artifacts are in `reports/aoestats/`:",
        "",
        "- `00_01_source_audit.json` — [Step 0.1]",
        "- `00_01_source_audit.md`",
        "- `00_02_match_schema_profile.md` — [Step 0.2]",
        "- `00_03_player_schema_profile.md` — [Step 0.3]",
        "- `00_04_smoke_test.md` — [Step 0.4]",
        "- `00_05_ingestion_log.md` — [Step 0.5]",
        "- `00_06_rowcount_reconciliation.md` — [Step 0.6]",
        "- `00_07_phase0_summary.md` — this file",
        "- `INVARIANTS.md` — binding invariants for downstream phases",
    ]

    (reports_dir / "00_07_phase0_summary.md").write_text("\n".join(summary_lines))
    logger.info("Step 0.7 complete: INVARIANTS.md and 00_07_phase0_summary.md written")


# ── Main orchestrator ─────────────────────────────────────────────────────────


def run_phase_0_audit(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    manifest_path: Path,
    reports_dir: Path,
    steps: list[str] | None = None,
) -> dict[str, dict]:
    """Orchestrate all Phase 0 audit steps for aoestats.

    Steps are executed in strict epistemic order. Idempotent: re-running
    overwrites existing report artifacts and re-materialises raw tables.

    Args:
        con: Active DuckDB connection (to the canonical db.duckdb).
        raw_dir: Path to the aoestats raw data root directory.
        manifest_path: Path to _download_manifest.json.
        reports_dir: Directory to write all report artifacts.
        steps: Optional list of step IDs to run (e.g., ["0.1", "0.2"]).
            If None, all steps are run.

    Returns:
        Dict mapping step ID to step result dict.
    """
    run_all = steps is None
    should_run = lambda s: run_all or s in (steps or [])  # noqa: E731

    results: dict[str, dict] = {}

    if should_run("0.1"):
        results["0.1"] = run_source_audit(raw_dir, manifest_path, reports_dir)

    if should_run("0.2"):
        results["0.2"] = profile_match_schema(raw_dir, reports_dir)

    if should_run("0.3"):
        results["0.3"] = profile_player_schema(raw_dir, reports_dir)

    if should_run("0.4"):
        results["0.4"] = run_smoke_test(raw_dir, reports_dir)

    if should_run("0.5"):
        results["0.5"] = run_full_ingestion(con, raw_dir, reports_dir)

    if should_run("0.6"):
        results["0.6"] = run_rowcount_reconciliation(con, manifest_path, reports_dir)

    if should_run("0.7"):
        ingestion_result = results.get("0.5", {})
        write_phase0_summary(reports_dir, ingestion_result, results)
        results["0.7"] = {"written": True}

    return results
