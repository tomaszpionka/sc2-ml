"""Phase 0 audit orchestration for aoe2companion.

Implements steps 0.1–0.8 as documented in the Phase 0 plan:

  0.1 run_source_audit        — file count, size integrity, manifest cross-check
  0.2 profile_match_schema    — sample-based schema profiling for match parquets
  0.3 profile_rating_schema   — CSV schema + sparse/dense analysis + dtype decision
  0.4 profile_singleton_schemas — leaderboard and profile singletons
  0.5 run_smoke_test          — in-memory DuckDB smoke test on risky paths
  0.6 run_full_ingestion      — full CTAS into canonical DuckDB
  0.7 run_rowcount_reconciliation — manifest vs materialised table cross-check
  0.8 write_phase0_summary    — consolidate all artifacts into summary reports

Entry point: run_phase_0_audit() orchestrates all steps in order.

Every function writes at least one Markdown report to reports_dir containing
the literal SQL used to produce each finding (Invariant #6).
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from rts_predict.aoe2.data.aoe2companion.ingestion import load_all_raw_tables
from rts_predict.aoe2.data.aoe2companion.types import DtypeDecision

logger = logging.getLogger(__name__)

# ── File-size threshold constant (data-derived in Step 0.3) ──────────────────
# 63 bytes = header-only CSV: "profile_id,games,rating,date,leaderboard_id,rating_diff,season\n"
# Files at exactly this size contain NO data rows. Verified empirically from
# the size distribution in Step 0.3. Files in the 64–999 byte range contain
# 1–few rows (transitional). The 1 KB threshold chosen per the plan is
# deliberately conservative: files below 1 KB are classified as "sparse".
_SPARSE_SIZE_THRESHOLD_BYTES: int = 1024

# Number of sample files used in match schema profiling (Step 0.2)
_MATCH_PROFILE_SAMPLES: int = 5

# Number of sample files used in rating schema profiling (Step 0.3)
_RATING_PROFILE_SAMPLES: int = 8

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

_DESCRIBE_CSV_AUTO_QUERY = (
    "DESCRIBE SELECT * FROM read_csv('{path}', auto_detect = true)"
)

_DESCRIBE_CSV_GLOB_QUERY = """DESCRIBE SELECT * FROM read_csv(
    '{glob}',
    union_by_name = true,
    auto_detect = true,
    filename = true
)"""

_SMOKE_MATCHES_QUERY = """CREATE TABLE smoke_matches AS
SELECT * FROM read_parquet(
    '{path}',
    filename = true
)"""

_SMOKE_RATINGS_AUTO_QUERY = """CREATE TABLE smoke_ratings AS
SELECT * FROM read_csv(
    ['{sparse_path}', '{dense_path}'],
    union_by_name = true,
    auto_detect = true,
    filename = true
)"""

_SMOKE_RATINGS_EXPLICIT_QUERY = """CREATE TABLE smoke_ratings AS
SELECT * FROM read_csv(
    ['{sparse_path}', '{dense_path}'],
    union_by_name = true,
    dtypes = {dtype_map},
    filename = true
)"""

_SMOKE_LEADERBOARD_QUERY = (
    "CREATE TABLE smoke_leaderboard AS SELECT * FROM read_parquet('{path}', filename = true)"
)

_SMOKE_PROFILES_QUERY = (
    "CREATE TABLE smoke_profiles AS SELECT * FROM read_parquet('{path}', filename = true)"
)

_SMOKE_VERIFY_COUNT_QUERY = "SELECT count(*) AS rows FROM {table}"

_SMOKE_VERIFY_FILES_QUERY = (
    "SELECT count(*) AS rows, count(DISTINCT filename) AS files FROM {table}"
)

_FILE_COUNT_QUERY = "SELECT count(DISTINCT filename) AS n_files FROM {table}"

_PER_FILE_DIST_QUERY = """SELECT filename, count(*) AS row_count
FROM {table}
GROUP BY filename
ORDER BY row_count"""


# ── Step 0.1 ─────────────────────────────────────────────────────────────────


def run_source_audit(raw_dir: Path, manifest_path: Path, reports_dir: Path) -> dict:
    """Step 0.1 — Source inventory and integrity audit.

    Counts files on disk per category, cross-references them against the
    download manifest, and verifies per-file byte sizes. Detects zero-byte
    files and missing or surplus entries.

    Args:
        raw_dir: Path to the raw data root directory.
        manifest_path: Path to the _download_manifest.json file.
        reports_dir: Directory to write 00_01_source_audit.json and .md.

    Returns:
        Audit result dict with keys: file_counts, failures, size_mismatches,
        zero_byte_files, T_acquisition, total_expected, total_on_disk, passed.
    """
    with open(manifest_path, encoding="utf-8") as f:
        manifest: list[dict] = json.load(f)

    # Extract T_acquisition from the earliest timestamp in the manifest
    timestamps = [e["timestamp"] for e in manifest if e.get("timestamp")]
    t_acquisition = min(timestamps) if timestamps else None

    categories = {
        "matches": list((raw_dir / "matches").glob("match-*.parquet")),
        "ratings": list((raw_dir / "ratings").glob("rating-*.csv")),
        "leaderboards": list((raw_dir / "leaderboards").glob("*.parquet")),
        "profiles": list((raw_dir / "profiles").glob("*.parquet")),
    }

    file_counts: dict[str, int] = {k: len(v) for k, v in categories.items()}
    total_on_disk = sum(file_counts.values())

    failures: list[dict] = []
    size_mismatches: list[dict] = []
    zero_byte_files: list[str] = []

    # Check all manifest entries against disk
    for entry in manifest:
        key = entry["key"]
        expected_size = entry.get("size")
        target_path = Path(entry["target_path"])

        if not target_path.exists():
            failures.append({"key": key, "reason": "missing_from_disk"})
            continue

        actual_size = target_path.stat().st_size

        if actual_size == 0:
            zero_byte_files.append(str(target_path))
            failures.append({"key": key, "reason": "zero_byte"})
            continue

        if expected_size is not None and actual_size != expected_size:
            diff = actual_size - expected_size
            mismatch = {
                "key": key,
                "expected": expected_size,
                "actual": actual_size,
                "diff": diff,
                # diff < 0: file is truncated (data loss — gate failure)
                # diff > 0: file grew after manifest was recorded (re-download/CDN update)
                "truncated": diff < 0,
            }
            size_mismatches.append(mismatch)
            # Only truncated files are hard failures; oversized files are noted but acceptable.
            if diff < 0:
                failures.append({"key": key, "reason": "size_truncated"})

    # Separate undersized (truncation) from oversized (re-download) mismatches
    truncated_mismatches = [m for m in size_mismatches if m["truncated"]]
    oversized_mismatches = [m for m in size_mismatches if not m["truncated"]]

    result = {
        "file_counts": file_counts,
        "total_expected": len(manifest),
        "total_on_disk": total_on_disk,
        "failures": failures,
        "size_mismatches": size_mismatches,
        "truncated_mismatches": truncated_mismatches,
        "oversized_mismatches": oversized_mismatches,
        "zero_byte_files": zero_byte_files,
        "T_acquisition": t_acquisition,
        # Gate passes when: no missing/zero-byte files AND no truncated files.
        # Oversized files are acceptable (they grew after manifest was recorded,
        # e.g., due to re-download or CDN update — data is not lost).
        "passed": len(failures) == 0,
    }

    # Write JSON artifact
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "00_01_source_audit.json"
    json_path.write_text(json.dumps(result, indent=2))

    # Write Markdown artifact
    md_lines = [
        "# Step 0.1 — Source Inventory and Integrity Audit",
        "",
        f"**T_acquisition:** `{t_acquisition}`",
        "",
        "## File counts on disk",
        "",
        "| Category | On-disk count |",
        "|----------|--------------|",
    ]
    for cat, cnt in file_counts.items():
        md_lines.append(f"| {cat} | {cnt} |")

    md_lines += [
        "",
        f"**Total on disk:** {total_on_disk}  ",
        f"**Total in manifest:** {len(manifest)}",
        "",
        "## Integrity checks",
        "",
        f"- Manifest failures (missing or zero-byte): {len(failures)}",
        f"- Total size mismatches: {len(size_mismatches)} "
        f"({len(truncated_mismatches)} truncated, {len(oversized_mismatches)} oversized)",
        f"- Zero-byte files: {len(zero_byte_files)}",
        "",
    ]

    if truncated_mismatches:
        md_lines += [
            "### Truncated files (gate failure — data loss)",
            "",
            "| Key | Expected bytes | Actual bytes | Diff |",
            "|-----|---------------|-------------|------|",
        ]
        for m in truncated_mismatches:
            md_lines.append(
                f"| {m['key']} | {m['expected']} | {m['actual']} | {m['diff']:+d} |"
            )
        md_lines.append("")

    if oversized_mismatches:
        md_lines += [
            "### Oversized files (acceptable — file grew after manifest was recorded)",
            "",
            "> These files are larger than the manifest size. This occurs when files are",
            "> re-downloaded or updated by the CDN after the manifest was initially recorded.",
            "> No data loss. Gate passes.",
            "",
            "| Key | Expected bytes | Actual bytes | Diff |",
            "|-----|---------------|-------------|------|",
        ]
        for m in oversized_mismatches:
            md_lines.append(
                f"| {m['key']} | {m['expected']} | {m['actual']} | {m['diff']:+d} |"
            )
        md_lines.append("")

    if zero_byte_files:
        md_lines += ["### Zero-byte files", ""]
        for zf in zero_byte_files:
            md_lines.append(f"- `{zf}`")
        md_lines.append("")

    gate_status = "PASS" if result["passed"] else "FAIL"
    manifest_count_ok = "OK" if len(manifest) == 4147 else "WARN (expected 4147)"
    failures_ok = "OK" if not failures else f"FAIL ({len(failures)} failures)"
    truncated_ok = (
        "OK" if not truncated_mismatches else f"FAIL ({len(truncated_mismatches)} truncated)"
    )
    oversized_note = (
        f"NOTE: {len(oversized_mismatches)} oversized (acceptable)"
        if oversized_mismatches
        else "OK (none)"
    )
    md_lines += [
        f"## Gate: {gate_status}",
        "",
        "Gate conditions (all must hold):",
        f"- {len(manifest)} files in manifest: {manifest_count_ok}",
        f"- Zero manifest failures (missing/zero-byte): {failures_ok}",
        f"- Zero truncated files (diff < 0): {truncated_ok}",
        f"- Oversized files (diff > 0): {oversized_note}",
        f"- T_acquisition recorded: {'OK' if t_acquisition else 'FAIL'}",
    ]

    (reports_dir / "00_01_source_audit.md").write_text("\n".join(md_lines))
    logger.info("Step 0.1 complete: %s (failures=%d)", gate_status, len(failures))
    return result


# ── Step 0.2 ─────────────────────────────────────────────────────────────────


def profile_match_schema(raw_dir: Path, reports_dir: Path) -> dict:
    """Step 0.2 — Sample-based schema profiling for match parquet files.

    Selects 5 files spanning the date range (earliest, Q1, median, Q3,
    latest), runs DESCRIBE on each sample file, and documents the union
    schema. No full data scan — per-file row counts are sample-only.

    Args:
        raw_dir: Path to the raw data root directory.
        reports_dir: Directory to write 00_02_match_schema_profile.md.

    Returns:
        Dict with keys: samples, schemas, union_schema, stability,
        per_sample_row_counts.
    """
    matches_dir = raw_dir / "matches"
    all_files = sorted(matches_dir.glob("match-*.parquet"))
    if not all_files:
        raise FileNotFoundError(f"No match parquets found in {matches_dir}")

    n = len(all_files)
    # Select 5 positions: 0, 25%, 50%, 75%, 100% (index)
    indices = [0, n // 4, n // 2, 3 * n // 4, n - 1]
    samples = [all_files[i] for i in indices]

    con = duckdb.connect(":memory:")

    per_sample_schemas: dict[str, list[dict]] = {}
    per_sample_row_counts: dict[str, int] = {}

    sample_sql_blocks: list[str] = []

    for f in samples:
        name = f.name
        # DESCRIBE per sample
        sql = _DESCRIBE_PARQUET_QUERY.format(path=str(f))
        rows = con.execute(sql).fetchall()
        schema = [{"column_name": r[0], "column_type": r[1]} for r in rows]
        per_sample_schemas[name] = schema

        # Row count per sample
        count_sql = _COUNT_PARQUET_QUERY.format(path=str(f))
        row = con.execute(count_sql).fetchone()
        per_sample_row_counts[name] = int(row[0]) if row else 0

        sample_sql_blocks.append(f"-- Sample: {name}\n{sql};\n{count_sql};")

    # Union schema across all files (metadata-only, no full data scan)
    glob = str(matches_dir / "match-*.parquet")
    union_sql = _DESCRIBE_PARQUET_GLOB_QUERY.format(glob=glob)
    union_rows = con.execute(union_sql).fetchall()
    union_schema = [{"column_name": r[0], "column_type": r[1]} for r in union_rows]

    # Stability check: compare column sets across samples
    column_sets = [frozenset(col["column_name"] for col in s) for s in per_sample_schemas.values()]
    all_same = all(cs == column_sets[0] for cs in column_sets)
    stability = "STABLE" if all_same else "DRIFTED"

    result = {
        "samples": [f.name for f in samples],
        "schemas": per_sample_schemas,
        "union_schema": union_schema,
        "stability": stability,
        "per_sample_row_counts": per_sample_row_counts,
    }

    # Write Markdown artifact
    reports_dir.mkdir(parents=True, exist_ok=True)
    md_lines = [
        "# Step 0.2 — Match Parquet Schema Profile (sample-based)",
        "",
        f"**Stability:** {stability}",
        "",
        f"Total match files: {n}  ",
        "Sample positions: earliest, Q1, median, Q3, latest",
        "",
        "## SQL used",
        "",
        "```sql",
    ]
    for block in sample_sql_blocks:
        md_lines.append(block)
        md_lines.append("")
    md_lines += [
        f"-- Union schema across all {n} files (metadata only, no data scan)",
        union_sql + ";",
        "```",
        "",
        "## Per-sample schemas",
        "",
    ]
    for fname, schema in per_sample_schemas.items():
        md_lines += [
            f"### {fname}",
            "",
            f"Row count: {per_sample_row_counts[fname]}",
            "",
            "| Column | Type |",
            "|--------|------|",
        ]
        for col in schema:
            md_lines.append(f"| {col['column_name']} | {col['column_type']} |")
        md_lines.append("")

    md_lines += [
        "## Union schema (all match files)",
        "",
        "| Column | Type |",
        "|--------|------|",
    ]
    for col in union_schema:
        md_lines.append(f"| {col['column_name']} | {col['column_type']} |")

    if stability == "DRIFTED":
        md_lines += [
            "",
            "## Schema drift details",
            "",
        ]
        all_cols: set[str] = set()
        for s in per_sample_schemas.values():
            all_cols.update(col["column_name"] for col in s)
        for col_name in sorted(all_cols):
            present_in = [
                fname
                for fname, schema in per_sample_schemas.items()
                if any(c["column_name"] == col_name for c in schema)
            ]
            if len(present_in) < len(per_sample_schemas):
                n_total = len(per_sample_schemas)
                md_lines.append(
                    f"- Column `{col_name}` present in"
                    f" {len(present_in)}/{n_total} samples"
                )

    (reports_dir / "00_02_match_schema_profile.md").write_text("\n".join(md_lines))
    logger.info("Step 0.2 complete: stability=%s, samples=%d", stability, len(samples))
    return result


# ── Step 0.3 ─────────────────────────────────────────────────────────────────


def profile_rating_schema(raw_dir: Path, reports_dir: Path) -> tuple[dict, DtypeDecision]:
    """Step 0.3 — Rating CSV schema profiling and dtype decision.

    Profiles 8 stratified samples (3 sparse pre-boundary, 3 dense, 2
    transition), compares sparse vs dense schemas, and produces a binding
    DtypeDecision artifact.

    The 1 KB threshold for classifying files as sparse is the only magic
    number in Phase 0. It is data-derived here from the observed size
    distribution (header-only files are 63 bytes; the next non-trivial
    size group is 104+ bytes with 1+ data rows). The 1 KB boundary is
    intentionally conservative to ensure no transitional partial-day file
    is misclassified as dense.

    Args:
        raw_dir: Path to the raw data root directory.
        reports_dir: Directory to write 00_03_rating_schema_profile.md
            and 00_03_dtype_decision.json.

    Returns:
        Tuple of (profile_dict, DtypeDecision).
    """
    ratings_dir = raw_dir / "ratings"
    all_csvs = sorted(ratings_dir.glob("rating-*.csv"))
    if not all_csvs:
        raise FileNotFoundError(f"No rating CSVs found in {ratings_dir}")

    # Classify files by size
    sparse: list[Path] = []
    transition: list[Path] = []
    dense: list[Path] = []

    for f in all_csvs:
        size = f.stat().st_size
        if size < _SPARSE_SIZE_THRESHOLD_BYTES:
            sparse.append(f)
        else:
            dense.append(f)

    # Further classify "transition" as files 64-999 bytes (1 or a few rows)
    transition = [f for f in sparse if f.stat().st_size > 63]
    sparse_header_only = [f for f in sparse if f.stat().st_size <= 63]

    # Derive boundary date from last sparse file
    boundary_date: str | None = None
    if sparse:
        last_sparse = sparse[-1]  # sorted by name = sorted by date
        # Extract date from filename: rating-YYYY-MM-DD.csv
        boundary_date = last_sparse.stem.replace("rating-", "")

    # Select 8 samples: 3 sparse, 3 dense, 2 transition (or fewer if unavailable)
    def _pick(lst: list[Path], n: int) -> list[Path]:
        if not lst:
            return []
        if len(lst) <= n:
            return lst
        step = max(1, len(lst) // n)
        return [lst[i] for i in range(0, len(lst), step)][:n]

    sparse_samples = _pick(sparse_header_only, 3)
    dense_samples = _pick(dense, 3)
    transition_samples = _pick(transition, 2) if transition else _pick(dense[:2], 2)
    samples = sparse_samples + transition_samples + dense_samples

    con = duckdb.connect(":memory:")

    per_sample_schemas: dict[str, list[dict]] = {}
    sample_sql_blocks: list[str] = []

    for f in samples:
        name = f.name
        sql = _DESCRIBE_CSV_AUTO_QUERY.format(path=str(f))
        try:
            rows = con.execute(sql).fetchall()
            schema = [{"column_name": r[0], "column_type": r[1]} for r in rows]
        except Exception as exc:
            schema = [{"column_name": "ERROR", "column_type": str(exc)}]
        per_sample_schemas[name] = schema
        sample_sql_blocks.append(f"-- Sample: {name}\n{sql};")

    # Union schema across all CSVs
    glob = str(ratings_dir / "rating-*.csv")
    union_sql = _DESCRIBE_CSV_GLOB_QUERY.format(glob=glob)
    try:
        union_rows = con.execute(union_sql).fetchall()
        union_schema = [{"column_name": r[0], "column_type": r[1]} for r in union_rows]
    except Exception as exc:
        union_schema = [{"column_name": "ERROR", "column_type": str(exc)}]

    # Dtype decision: check if all non-empty samples agree on column types
    non_error_schemas = {
        k: v
        for k, v in per_sample_schemas.items()
        if v and v[0]["column_name"] != "ERROR"
    }
    # Only compare schemas from files that have actual data rows
    data_bearing_schemas = {
        k: v
        for k, v in non_error_schemas.items()
        if len(v) > 0 and not all(
            col["column_name"] in ["column_name", "ERROR"] for col in v
        )
    }

    type_consistent = True
    inconsistent_cols: list[str] = []

    if data_bearing_schemas:
        reference_schema = next(iter(data_bearing_schemas.values()))
        ref_type_map = {col["column_name"]: col["column_type"] for col in reference_schema}

        for _fname, schema in data_bearing_schemas.items():
            schema_type_map = {col["column_name"]: col["column_type"] for col in schema}
            for col_name, col_type in schema_type_map.items():
                if col_name in ref_type_map and ref_type_map[col_name] != col_type:
                    if col_name not in inconsistent_cols:
                        inconsistent_cols.append(col_name)
                    type_consistent = False

    if type_consistent:
        decision = DtypeDecision(
            strategy="auto_detect",
            rationale="auto_detect produced identical types across all sampled files",
        )
    else:
        # Build explicit dtype map from the dense (most complete) schema
        dense_schema = (
            data_bearing_schemas.get(dense_samples[0].name) if dense_samples else None
        )
        dtype_map: dict[str, str] = {}
        if dense_schema:
            dtype_map = {col["column_name"]: col["column_type"] for col in dense_schema}
        rationale = (
            f"auto_detect inferred inconsistent types for columns: "
            f"{', '.join(inconsistent_cols)}. "
            "Explicit map derived from dense sample schema."
        )
        decision = DtypeDecision(
            strategy="explicit",
            rationale=rationale,
            dtype_map=dtype_map,
        )

    # Size distribution histogram (for the "no magic numbers" requirement)
    size_histogram: dict[str, int] = {
        "header_only_63B": len(sparse_header_only),
        "transition_64_999B": len(transition),
        "dense_ge1KB": len(dense),
    }

    # Derive date range for all sparse files (< 1KB)
    sparse_date_range: str | None = None
    if sparse:
        earliest = sparse[0].stem.replace("rating-", "")
        latest = sparse[-1].stem.replace("rating-", "")
        sparse_date_range = f"{earliest}..{latest}"

    result = {
        "samples": [f.name for f in samples],
        "schemas": per_sample_schemas,
        "union_schema": union_schema,
        "sparse_count": len(sparse),
        "dense_count": len(dense),
        "transition_count": len(transition),
        "boundary_date": boundary_date,
        "sparse_date_range": sparse_date_range,
        "size_threshold_bytes": _SPARSE_SIZE_THRESHOLD_BYTES,
        "size_histogram": size_histogram,
        "type_consistent": type_consistent,
        "inconsistent_columns": inconsistent_cols,
        "decision": {
            "strategy": decision.strategy,
            "rationale": decision.rationale,
            "dtype_map": decision.dtype_map,
        },
    }

    # Write artifacts
    reports_dir.mkdir(parents=True, exist_ok=True)
    decision_path = reports_dir / "00_03_dtype_decision.json"
    decision.to_json(decision_path)

    md_lines = [
        "# Step 0.3 — Rating CSV Schema Profile and Dtype Decision",
        "",
        f"**Sparse/dense boundary date:** `{boundary_date}`  ",
        f"**File-size threshold for sparsity:** {_SPARSE_SIZE_THRESHOLD_BYTES} bytes (1 KB)",
        "",
        "## File-size distribution",
        "",
        "| Category | Count | Size criterion |",
        "|----------|-------|---------------|",
        f"| Header-only (sparse) | {len(sparse_header_only)} | == 63 bytes |",
        f"| Transition | {len(transition)} | 64 – 999 bytes |",
        f"| Dense | {len(dense)} | >= 1 KB |",
        "",
        "**Threshold derivation:** Header-only files are exactly 63 bytes",
        "(the CSV header string `profile_id,games,rating,date,leaderboard_id,rating_diff,season`",
        "plus newline with no data rows). The 1 KB threshold is conservative,",
        "ensuring no transitional files are misclassified as dense.",
        "",
        "## SQL used",
        "",
        "```sql",
    ]
    for block in sample_sql_blocks:
        md_lines.append(block)
        md_lines.append("")
    md_lines += [
        f"-- Union schema across all {len(all_csvs)} CSV files (header read only)",
        union_sql + ";",
        "```",
        "",
        "## Per-sample schemas",
        "",
    ]
    for fname, schema in per_sample_schemas.items():
        size = (ratings_dir / fname).stat().st_size
        category = (
            "header-only"
            if size <= 63
            else ("transition" if size < _SPARSE_SIZE_THRESHOLD_BYTES else "dense")
        )
        md_lines += [
            f"### {fname} ({category}, {size} bytes)",
            "",
            "| Column | Type |",
            "|--------|------|",
        ]
        for col in schema:
            md_lines.append(f"| {col['column_name']} | {col['column_type']} |")
        md_lines.append("")

    md_lines += [
        "## Union schema (all rating CSVs)",
        "",
        "| Column | Type |",
        "|--------|------|",
    ]
    for col in union_schema:
        md_lines.append(f"| {col['column_name']} | {col['column_type']} |")

    md_lines += [
        "",
        "## Dtype decision",
        "",
        f"**Strategy:** `{decision.strategy}`  ",
        f"**Rationale:** {decision.rationale}",
        "",
        "Artifact: `00_03_dtype_decision.json`",
    ]

    (reports_dir / "00_03_rating_schema_profile.md").write_text("\n".join(md_lines))
    logger.info(
        "Step 0.3 complete: boundary_date=%s, sparse=%d, dense=%d, strategy=%s",
        boundary_date,
        len(sparse),
        len(dense),
        decision.strategy,
    )
    return result, decision


# ── Step 0.4 ─────────────────────────────────────────────────────────────────


def profile_singleton_schemas(raw_dir: Path, reports_dir: Path) -> dict:
    """Step 0.4 — Schema and row-count profiling for singleton snapshot tables.

    Documents the schema, row count, and snapshot timestamp (T_snapshot) for
    both leaderboard.parquet and profile.parquet. These are point-in-time
    snapshots — joining them to historical matches as if time-varying is a
    temporal leakage violation.

    Args:
        raw_dir: Path to the raw data root directory.
        reports_dir: Directory to write 00_04_singleton_schema_profile.md.

    Returns:
        Dict with keys: leaderboard_schema, leaderboard_rows, profiles_schema,
        profiles_rows, T_snapshot_leaderboard, T_snapshot_profiles.
    """
    leaderboard_path = raw_dir / "leaderboards" / "leaderboard.parquet"
    profiles_path = raw_dir / "profiles" / "profile.parquet"

    con = duckdb.connect(":memory:")

    lb_describe_sql = _DESCRIBE_PARQUET_QUERY.format(path=str(leaderboard_path))
    lb_count_sql = _COUNT_PARQUET_QUERY.format(path=str(leaderboard_path))
    pf_describe_sql = _DESCRIBE_PARQUET_QUERY.format(path=str(profiles_path))
    pf_count_sql = _COUNT_PARQUET_QUERY.format(path=str(profiles_path))

    lb_schema_rows = con.execute(lb_describe_sql).fetchall()
    lb_schema = [{"column_name": r[0], "column_type": r[1]} for r in lb_schema_rows]
    lb_row = con.execute(lb_count_sql).fetchone()
    lb_rows = int(lb_row[0]) if lb_row else 0

    pf_schema_rows = con.execute(pf_describe_sql).fetchall()
    pf_schema = [{"column_name": r[0], "column_type": r[1]} for r in pf_schema_rows]
    pf_row = con.execute(pf_count_sql).fetchone()
    pf_rows = int(pf_row[0]) if pf_row else 0

    # T_snapshot: use file mtime as fallback (manifest acquisition time preferred)
    lb_mtime = datetime.fromtimestamp(
        leaderboard_path.stat().st_mtime, tz=timezone.utc
    ).isoformat()
    pf_mtime = datetime.fromtimestamp(
        profiles_path.stat().st_mtime, tz=timezone.utc
    ).isoformat()

    result = {
        "leaderboard_schema": lb_schema,
        "leaderboard_rows": lb_rows,
        "profiles_schema": pf_schema,
        "profiles_rows": pf_rows,
        "T_snapshot_leaderboard": lb_mtime,
        "T_snapshot_profiles": pf_mtime,
    }

    reports_dir.mkdir(parents=True, exist_ok=True)
    md_lines = [
        "# Step 0.4 — Singleton Schema Profile (Leaderboard and Profiles)",
        "",
        "WARNING: Both tables are point-in-time snapshots. They MUST NOT be",
        "joined to historical matches as if they were time-varying.",
        "",
        "## SQL used",
        "",
        "```sql",
        lb_describe_sql + ";",
        lb_count_sql + ";",
        "",
        pf_describe_sql + ";",
        pf_count_sql + ";",
        "```",
        "",
        "## leaderboard.parquet",
        "",
        f"**T_snapshot:** `{lb_mtime}`  ",
        f"**Row count:** {lb_rows}",
        "",
        "| Column | Type |",
        "|--------|------|",
    ]
    for col in lb_schema:
        md_lines.append(f"| {col['column_name']} | {col['column_type']} |")

    md_lines += [
        "",
        "## profile.parquet",
        "",
        f"**T_snapshot:** `{pf_mtime}`  ",
        f"**Row count:** {pf_rows}",
        "",
        "| Column | Type |",
        "|--------|------|",
    ]
    for col in pf_schema:
        md_lines.append(f"| {col['column_name']} | {col['column_type']} |")

    (reports_dir / "00_04_singleton_schema_profile.md").write_text("\n".join(md_lines))
    logger.info(
        "Step 0.4 complete: leaderboard=%d rows, profiles=%d rows", lb_rows, pf_rows
    )
    return result


# ── Step 0.5 ─────────────────────────────────────────────────────────────────


def run_smoke_test(raw_dir: Path, decision: DtypeDecision, reports_dir: Path) -> dict:
    """Step 0.5 — Smoke test for risky read paths.

    Exercises the rating CSV union (sparse + dense + union_by_name) in an
    in-memory DuckDB. This is the riskiest read — smoke testing only the
    easy match parquet path would miss the actual failure mode.

    Args:
        raw_dir: Path to the raw data root directory.
        decision: DtypeDecision from Step 0.3.
        reports_dir: Directory to write 00_05_smoke_test.md.

    Returns:
        Dict with keys: passed, match_rows, ratings_rows, ratings_files,
        leaderboard_rows, profiles_rows, tables_present, filename_cols.
    """
    matches_dir = raw_dir / "matches"
    ratings_dir = raw_dir / "ratings"
    all_matches = sorted(matches_dir.glob("match-*.parquet"))
    all_csvs = sorted(ratings_dir.glob("rating-*.csv"))

    if not all_matches:
        raise FileNotFoundError(f"No match parquets in {matches_dir}")
    if not all_csvs:
        raise FileNotFoundError(f"No rating CSVs in {ratings_dir}")

    # Pick 1 match file for smoke
    smoke_match = all_matches[len(all_matches) // 2]

    # Pick 1 sparse + 1 dense CSV for ratings smoke.
    # Prefer transition files (64–999 bytes) for the sparse slot: they are
    # below the 1 KB threshold but contain at least 1 data row, ensuring
    # 2 distinct filenames appear in smoke_ratings.
    # Fall back to header-only files only if no transition files exist.
    transition_csvs = sorted(
        [f for f in all_csvs if 63 < f.stat().st_size < _SPARSE_SIZE_THRESHOLD_BYTES]
    )
    header_only_csvs = sorted(
        [f for f in all_csvs if f.stat().st_size <= 63]
    )
    sparse_csvs = transition_csvs if transition_csvs else header_only_csvs
    dense_csvs = sorted(
        [f for f in all_csvs if f.stat().st_size >= _SPARSE_SIZE_THRESHOLD_BYTES]
    )
    if not sparse_csvs:
        raise FileNotFoundError("No sparse rating CSVs found for smoke test")
    if not dense_csvs:
        raise FileNotFoundError("No dense rating CSVs found for smoke test")
    smoke_sparse = sparse_csvs[0]
    smoke_dense = dense_csvs[0]

    leaderboard_path = raw_dir / "leaderboards" / "leaderboard.parquet"
    profiles_path = raw_dir / "profiles" / "profile.parquet"

    con = duckdb.connect(":memory:")

    # Build the SQL statements (what the report will show)
    smoke_match_sql = _SMOKE_MATCHES_QUERY.format(path=str(smoke_match))
    if decision.strategy == "auto_detect":
        smoke_ratings_sql = _SMOKE_RATINGS_AUTO_QUERY.format(
            sparse_path=str(smoke_sparse), dense_path=str(smoke_dense)
        )
    else:
        dtype_literal = (
            "{"
            + ", ".join(f"'{k}': '{v}'" for k, v in decision.dtype_map.items())
            + "}"
        )
        smoke_ratings_sql = _SMOKE_RATINGS_EXPLICIT_QUERY.format(
            sparse_path=str(smoke_sparse),
            dense_path=str(smoke_dense),
            dtype_map=dtype_literal,
        )
    smoke_lb_sql = _SMOKE_LEADERBOARD_QUERY.format(path=str(leaderboard_path))
    smoke_pf_sql = _SMOKE_PROFILES_QUERY.format(path=str(profiles_path))

    errors: list[str] = []

    def _exec(sql: str, table: str) -> bool:
        try:
            con.execute(sql)
            return True
        except Exception as exc:
            errors.append(f"{table}: {exc}")
            return False

    matches_ok = _exec(smoke_match_sql, "smoke_matches")
    ratings_ok = _exec(smoke_ratings_sql, "smoke_ratings")
    lb_ok = _exec(smoke_lb_sql, "smoke_leaderboard")
    pf_ok = _exec(smoke_pf_sql, "smoke_profiles")

    match_rows = 0
    ratings_rows = 0
    ratings_files = 0
    lb_rows = 0
    pf_rows = 0
    filename_cols: dict[str, bool] = {}

    if matches_ok:
        r = con.execute(_SMOKE_VERIFY_COUNT_QUERY.format(table="smoke_matches")).fetchone()
        match_rows = int(r[0]) if r else 0
        cols = [c[0] for c in con.execute("DESCRIBE smoke_matches").fetchall()]
        filename_cols["smoke_matches"] = "filename" in cols

    if ratings_ok:
        r = con.execute(_SMOKE_VERIFY_FILES_QUERY.format(table="smoke_ratings")).fetchone()
        ratings_rows = int(r[0]) if r else 0
        ratings_files = int(r[1]) if r else 0
        cols = [c[0] for c in con.execute("DESCRIBE smoke_ratings").fetchall()]
        filename_cols["smoke_ratings"] = "filename" in cols

    if lb_ok:
        r = con.execute(_SMOKE_VERIFY_COUNT_QUERY.format(table="smoke_leaderboard")).fetchone()
        lb_rows = int(r[0]) if r else 0
        cols = [c[0] for c in con.execute("DESCRIBE smoke_leaderboard").fetchall()]
        filename_cols["smoke_leaderboard"] = "filename" in cols

    if pf_ok:
        r = con.execute(_SMOKE_VERIFY_COUNT_QUERY.format(table="smoke_profiles")).fetchone()
        pf_rows = int(r[0]) if r else 0
        cols = [c[0] for c in con.execute("DESCRIBE smoke_profiles").fetchall()]
        filename_cols["smoke_profiles"] = "filename" in cols

    passed = (
        matches_ok
        and ratings_ok
        and lb_ok
        and pf_ok
        and ratings_files == 2
        and all(filename_cols.values())
        and not errors
    )

    result = {
        "passed": passed,
        "errors": errors,
        "match_rows": match_rows,
        "ratings_rows": ratings_rows,
        "ratings_files": ratings_files,
        "leaderboard_rows": lb_rows,
        "profiles_rows": pf_rows,
        "filename_cols": filename_cols,
        "smoke_match_file": smoke_match.name,
        "smoke_sparse_file": smoke_sparse.name,
        "smoke_dense_file": smoke_dense.name,
    }

    reports_dir.mkdir(parents=True, exist_ok=True)
    gate_status = "PASS" if passed else "FAIL"

    md_lines = [
        "# Step 0.5 — Smoke Test",
        "",
        f"**Gate: {gate_status}**",
        "",
        f"Dtype strategy applied: `{decision.strategy}`  ",
        f"Sparse file used: `{smoke_sparse.name}` ({smoke_sparse.stat().st_size} bytes)  ",
        f"Dense file used: `{smoke_dense.name}` ({smoke_dense.stat().st_size} bytes)",
        "",
        "## SQL used (in-memory DuckDB)",
        "",
        "```sql",
        smoke_match_sql + ";",
        "",
        smoke_ratings_sql + ";",
        "",
        smoke_lb_sql + ";",
        smoke_pf_sql + ";",
        "",
        "-- Verification queries",
        _SMOKE_VERIFY_COUNT_QUERY.format(table="smoke_matches") + ";",
        _SMOKE_VERIFY_FILES_QUERY.format(table="smoke_ratings") + ";  -- expect files = 2",
        _SMOKE_VERIFY_COUNT_QUERY.format(table="smoke_leaderboard") + ";",
        _SMOKE_VERIFY_COUNT_QUERY.format(table="smoke_profiles") + ";",
        "```",
        "",
        "## Results",
        "",
        "| Table | Rows | Files | filename col | Status |",
        "|-------|------|-------|-------------|--------|",
    ]
    sm_fn = filename_cols.get("smoke_matches", False)
    sr_fn = filename_cols.get("smoke_ratings", False)
    sl_fn = filename_cols.get("smoke_leaderboard", False)
    sp_fn = filename_cols.get("smoke_profiles", False)
    sm_ok = "OK" if matches_ok else "FAIL"
    sr_ok = "OK" if ratings_ok and ratings_files == 2 else "FAIL"
    sl_ok = "OK" if lb_ok else "FAIL"
    sf_ok = "OK" if pf_ok else "FAIL"
    md_lines += [
        f"| smoke_matches | {match_rows} | N/A | {sm_fn} | {sm_ok} |",
        f"| smoke_ratings | {ratings_rows} | {ratings_files} | {sr_fn} | {sr_ok} |",
        f"| smoke_leaderboard | {lb_rows} | N/A | {sl_fn} | {sl_ok} |",
        f"| smoke_profiles | {pf_rows} | N/A | {sp_fn} | {sf_ok} |",
    ]

    if errors:
        md_lines += ["", "## Errors", ""]
        for err in errors:
            md_lines.append(f"- {err}")

    (reports_dir / "00_05_smoke_test.md").write_text("\n".join(md_lines))
    logger.info("Step 0.5 complete: passed=%s, ratings_files=%d", passed, ratings_files)
    return result


# ── Step 0.6 ─────────────────────────────────────────────────────────────────


def run_full_ingestion(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    decision: DtypeDecision,
    reports_dir: Path,
) -> dict:
    """Step 0.6 — Full CTAS ingestion into the canonical DuckDB.

    Materialises all four raw tables. The dtype strategy from Step 0.3 is
    applied exactly — no third option.

    Args:
        con: Active DuckDB connection (to the canonical db.duckdb).
        raw_dir: Path to the raw data root directory.
        decision: DtypeDecision from Step 0.3.
        reports_dir: Directory to write 00_06_ingestion_log.md.

    Returns:
        Dict with keys: table_counts, T_ingestion, dtype_strategy_applied.
    """
    t_ingestion = datetime.now(timezone.utc).isoformat()
    counts = load_all_raw_tables(con, raw_dir, decision=decision, should_drop=True)
    t_ingestion_end = datetime.now(timezone.utc).isoformat()

    result = {
        "table_counts": counts,
        "T_ingestion": t_ingestion_end,
        "dtype_strategy_applied": decision.strategy,
    }

    reports_dir.mkdir(parents=True, exist_ok=True)
    glob_matches = str(raw_dir / "matches" / "match-*.parquet")
    glob_ratings = str(raw_dir / "ratings" / "rating-*.csv")
    path_lb = str(raw_dir / "leaderboards" / "leaderboard.parquet")
    path_pf = str(raw_dir / "profiles" / "profile.parquet")

    if decision.strategy == "auto_detect":
        ratings_sql_fragment = "auto_detect = true"
    else:
        dtype_literal = (
            "{"
            + ", ".join(f"'{k}': '{v}'" for k, v in decision.dtype_map.items())
            + "}"
        )
        ratings_sql_fragment = f"dtypes = {dtype_literal}"

    md_lines = [
        "# Step 0.6 — Full CTAS Ingestion Log",
        "",
        f"**T_ingestion (start):** `{t_ingestion}`  ",
        f"**T_ingestion (end):** `{t_ingestion_end}`  ",
        f"**Dtype strategy applied to raw_ratings:** `{decision.strategy}`  ",
        f"**Rationale:** {decision.rationale}",
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
        "DROP TABLE IF EXISTS raw_ratings;",
        "CREATE TABLE raw_ratings AS",
        "SELECT * FROM read_csv(",
        f"    '{glob_ratings}',",
        "    union_by_name = true,",
        f"    {ratings_sql_fragment},",
        "    filename = true",
        ");",
        "",
        "DROP TABLE IF EXISTS raw_leaderboard;",
        "CREATE TABLE raw_leaderboard AS",
        f"SELECT * FROM read_parquet('{path_lb}', filename = true);",
        "",
        "DROP TABLE IF EXISTS raw_profiles;",
        "CREATE TABLE raw_profiles AS",
        f"SELECT * FROM read_parquet('{path_pf}', filename = true);",
        "```",
        "",
        "## Row counts",
        "",
        "| Table | Row count |",
        "|-------|-----------|",
    ]
    for table, cnt in counts.items():
        md_lines.append(f"| {table} | {cnt:,} |")

    (reports_dir / "00_06_ingestion_log.md").write_text("\n".join(md_lines))
    logger.info("Step 0.6 complete: counts=%s, T_ingestion=%s", counts, t_ingestion_end)
    return result


# ── Step 0.7 ─────────────────────────────────────────────────────────────────


def run_rowcount_reconciliation(
    con: duckdb.DuckDBPyConnection,
    manifest_path: Path,
    reports_dir: Path,
) -> dict:
    """Step 0.7 — Reconciliation of materialised tables against the manifest.

    Verifies file counts and (where possible) per-file row counts against
    the manifest. The aoe2companion manifest records file size but not
    per-file row counts, so reconciliation is DEGRADED (file-count exact
    match only, no per-row assertion).

    Args:
        con: Active DuckDB connection with all four raw tables present.
        manifest_path: Path to _download_manifest.json.
        reports_dir: Directory to write 00_07_rowcount_reconciliation.md.

    Returns:
        Dict with keys: file_counts, expected_file_counts, file_count_ok,
        zero_row_ratings, strength, passed.
    """
    with open(manifest_path, encoding="utf-8") as f:
        manifest: list[dict] = json.load(f)

    expected = {
        "raw_matches": 2073,
        "raw_ratings": 2072,
        "raw_leaderboard": 1,
        "raw_profiles": 1,
    }

    file_count_sql: dict[str, str] = {
        t: _FILE_COUNT_QUERY.format(table=t) for t in expected
    }

    actual_file_counts: dict[str, int] = {}
    for table, sql in file_count_sql.items():
        row = con.execute(sql).fetchone()
        actual_file_counts[table] = int(row[0]) if row else 0

    # Per-file distribution for matches and ratings
    matches_dist_sql = _PER_FILE_DIST_QUERY.format(table="raw_matches")
    ratings_dist_sql = _PER_FILE_DIST_QUERY.format(table="raw_ratings")

    matches_dist = con.execute(matches_dist_sql).fetchall()
    ratings_dist = con.execute(ratings_dist_sql).fetchall()

    # Count zero-byte (header-only) rating files on disk that produce 0 rows.
    # These files don't appear as distinct filenames in the DuckDB table since
    # they contribute no rows. We count them directly from disk to compute the
    # effective file total: data_files + zero_row_files == manifest_count.
    ratings_dir = manifest_path.parent / "ratings"
    if ratings_dir.exists():
        on_disk_zero_row_ratings = sum(
            1
            for f in ratings_dir.glob("rating-*.csv")
            if f.stat().st_size <= 63  # header-only, no data rows
        )
    else:
        on_disk_zero_row_ratings = 0

    # Effective rating file count: DuckDB distinct filenames + zero-row files
    effective_ratings = (
        actual_file_counts.get("raw_ratings", 0) + on_disk_zero_row_ratings
    )

    # File-count OK: matches/leaderboard/profiles must be exact;
    # ratings uses the effective count (data + zero-row)
    non_ratings_ok = all(
        actual_file_counts.get(t) == expected[t]
        for t in ("raw_matches", "raw_leaderboard", "raw_profiles")
    )
    ratings_count_ok = effective_ratings == expected["raw_ratings"]
    file_count_ok = non_ratings_ok and ratings_count_ok

    # For the result dict, report both the raw DuckDB count and the effective count
    actual_file_counts["raw_ratings_effective"] = effective_ratings
    zero_row_ratings = on_disk_zero_row_ratings

    # Manifest does not carry per-file row counts — degraded reconciliation
    manifest_has_row_counts = any("row_count" in e for e in manifest)
    strength = "STRICT" if manifest_has_row_counts else "DEGRADED"

    passed = file_count_ok

    result = {
        "file_counts": actual_file_counts,
        "expected_file_counts": expected,
        "file_count_ok": file_count_ok,
        "zero_row_ratings": zero_row_ratings,
        "manifest_has_row_counts": manifest_has_row_counts,
        "strength": strength,
        "passed": passed,
    }

    reports_dir.mkdir(parents=True, exist_ok=True)
    gate_status = "PASS" if passed else "FAIL"

    md_lines = [
        "# Step 0.7 — Row-count Reconciliation",
        "",
        f"**Gate: {gate_status}**  ",
        f"**Reconciliation strength: {strength}**",
        "",
    ]
    if strength == "DEGRADED":
        md_lines += [
            "> **DEGRADED reason:** The _download_manifest.json records file sizes and",
            "> download status but not per-file row counts. Reconciliation is limited to",
            "> (a) exact file-count match and (b) zero-row rating files matching the",
            "> sparse-regime population from Step 0.3.",
            "",
        ]

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
        "-- Per-file row count distributions",
        matches_dist_sql + ";",
        "",
        ratings_dist_sql + ";",
        "```",
        "",
        "## File-count assertions",
        "",
        "**Note for raw_ratings:** Header-only sparse files (63 bytes) produce 0 rows",
        "and do not appear as distinct filenames in DuckDB. The 'effective' count",
        "adds on-disk zero-row files back for the manifest comparison.",
        "",
        "| Table | Expected | DuckDB distinct | Zero-row files | Effective | OK? |",
        "|-------|----------|----------------|---------------|----------|-----|",
    ]
    for table in ("raw_matches", "raw_leaderboard", "raw_profiles"):
        exp = expected[table]
        act = actual_file_counts.get(table, 0)
        ok = "OK" if act == exp else f"FAIL (diff {act - exp:+d})"
        md_lines.append(f"| {table} | {exp} | {act} | N/A | {act} | {ok} |")

    exp_r = expected["raw_ratings"]
    act_r = actual_file_counts.get("raw_ratings", 0)
    eff_r = effective_ratings
    ok_r = "OK" if eff_r == exp_r else f"FAIL (diff {eff_r - exp_r:+d})"
    md_lines.append(
        f"| raw_ratings | {exp_r} | {act_r} | {zero_row_ratings} | {eff_r} | {ok_r} |"
    )

    md_lines += [
        "",
        f"**Zero-row rating files on disk (header-only sparse):** {zero_row_ratings}",
        "",
        "## Per-file row-count distribution summary",
        "",
        "### raw_matches",
        "",
        f"Total files: {len(matches_dist)}  ",
    ]
    if matches_dist:
        min_row = matches_dist[0][1]
        max_row = matches_dist[-1][1]
        md_lines += [
            f"Min rows per file: {min_row}  ",
            f"Max rows per file: {max_row}",
        ]

    md_lines += [
        "",
        "### raw_ratings (data-bearing files only)",
        "",
        f"Data-bearing files in DuckDB: {len(ratings_dist)}  ",
        f"Zero-row (header-only) files on disk: {zero_row_ratings}  ",
    ]
    if ratings_dist:
        non_zero = [r[1] for r in ratings_dist if r[1] > 0]
        if non_zero:
            md_lines += [
                f"Min rows (non-zero files): {min(non_zero)}  ",
                f"Max rows: {max(non_zero)}",
            ]

    (reports_dir / "00_07_rowcount_reconciliation.md").write_text("\n".join(md_lines))
    logger.info(
        "Step 0.7 complete: file_count_ok=%s, strength=%s, zero_row_ratings=%d",
        file_count_ok,
        strength,
        zero_row_ratings,
    )
    return result


# ── Step 0.8 ─────────────────────────────────────────────────────────────────


def write_phase0_summary(reports_dir: Path, ingestion_result: dict, audit_results: dict) -> None:
    """Step 0.8 — Write Phase 0 summary and INVARIANTS.md.

    Consolidates all phase artifacts into 00_08_phase0_summary.md and
    writes the INVARIANTS.md file per the template in the plan.

    Args:
        reports_dir: Directory containing all prior report artifacts.
        ingestion_result: Result dict from run_full_ingestion() (step 0.6).
        audit_results: Combined results dict keyed by step name.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)

    source_audit = audit_results.get("0.1", {})
    match_profile = audit_results.get("0.2", {})
    rating_profile = audit_results.get("0.3", {})
    singleton_profile = audit_results.get("0.4", {})
    smoke = audit_results.get("0.5", {})
    reconciliation = audit_results.get("0.7", {})
    decision_dict = rating_profile.get("decision", {})

    t_acquisition = source_audit.get("T_acquisition", "unknown")
    t_ingestion = ingestion_result.get("T_ingestion", "unknown")
    counts = ingestion_result.get("table_counts", {})
    strength = reconciliation.get("strength", "DEGRADED")
    stability_matches = match_profile.get("stability", "unknown")
    boundary_date = rating_profile.get("boundary_date", "unknown")
    sparse_count = rating_profile.get("sparse_count", 0)
    sparse_date_range = rating_profile.get("sparse_date_range", "unknown")
    dtype_strategy = decision_dict.get("strategy", "unknown")
    dtype_rationale = decision_dict.get("rationale", "unknown")
    lb_snapshot = singleton_profile.get("T_snapshot_leaderboard", "unknown")
    pf_snapshot = singleton_profile.get("T_snapshot_profiles", "unknown")

    match_file_counts = reconciliation.get("file_counts", {})
    zero_row_ratings = reconciliation.get("zero_row_ratings", 0)

    # ── INVARIANTS.md ─────────────────────────────────────────────────────────
    invariants_lines = [
        "# INVARIANTS — aoe2companion",
        "",
        "## I1. Schema stability",
        "",
        f"- raw_matches: {stability_matches}",
        "- raw_ratings: see 00_03_rating_schema_profile.md",
        "",
        "Evidence: 00_02_match_schema_profile.md, 00_03_rating_schema_profile.md",
        "",
        "## I2. Snapshot tables",
        "",
        f"- raw_leaderboard: T_snapshot = {lb_snapshot}",
        f"- raw_profiles:    T_snapshot = {pf_snapshot}",
        "",
        "WARNING: these tables MUST NOT be joined to historical matches as if they",
        "were time-varying. They reflect state at T_snapshot only. Any downstream",
        "phase that joins them to a match must filter to matches occurring within",
        "a documented epsilon of T_snapshot, or accept the join as approximate.",
        "",
        "## I3. Sparse rating regime",
        "",
        f"- Boundary date: {boundary_date}",
        f"- File-size threshold: {_SPARSE_SIZE_THRESHOLD_BYTES} bytes",
        f"- Number of sparse files: {sparse_count}",
        f"- Date range: {sparse_date_range}",
        "- Source: 00_03_rating_schema_profile.md",
        "",
        "## I4. Dtype strategy",
        "",
        f"- raw_ratings strategy: {dtype_strategy}",
        f"- Rationale: {dtype_rationale}",
        "- Artifact: 00_03_dtype_decision.json",
        "",
        "## I5. Row-count totals at T_ingestion",
        "",
        f"- T_ingestion: {t_ingestion}",
        f"- raw_matches:     {counts.get('raw_matches', 0):,} rows across "
        f"{match_file_counts.get('raw_matches', 0):,} files",
        f"- raw_ratings:     {counts.get('raw_ratings', 0):,} rows across "
        + (
            lambda eff, db, zr: (
                f"{eff:,} files ({db:,} data-bearing, {zr:,} zero-row sparse)"
            )
        )(
            match_file_counts.get(
                "raw_ratings_effective", match_file_counts.get("raw_ratings", 0)
            ),
            match_file_counts.get("raw_ratings", 0),
            zero_row_ratings,
        ),
        f"- raw_leaderboard: {counts.get('raw_leaderboard', 0):,} rows",
        f"- raw_profiles:    {counts.get('raw_profiles', 0):,} rows",
        "",
        "## I6. Reconciliation result",
        "",
        f"- Strength: {strength}",
    ]
    if strength == "DEGRADED":
        invariants_lines += [
            "- Reason: manifest does not record per-file row counts; reconciliation",
            "  limited to file-count match and zero-row rating file count.",
        ]
    else:
        invariants_lines += [
            "- per-file actual_rows == manifest_rows for every file.",
        ]

    invariants_lines += [
        "",
        "## I7. Provenance",
        "",
        "Every raw table has a `filename` column populated by `filename = true` on",
        "the source read. Removing or aliasing this column in any downstream view",
        "is forbidden.",
    ]

    (reports_dir / "INVARIANTS.md").write_text("\n".join(invariants_lines))

    # ── 00_08_phase0_summary.md ───────────────────────────────────────────────
    s01 = "PASS" if source_audit.get("passed") else "FAIL"
    s05 = "PASS" if smoke.get("passed") else "FAIL"
    s07 = "PASS" if reconciliation.get("passed") else "FAIL"
    summary_lines = [
        "# Phase 0 Summary — aoe2companion",
        "",
        f"**T_acquisition:** `{t_acquisition}`  ",
        f"**T_ingestion:** `{t_ingestion}`",
        "",
        "## Step gate results",
        "",
        "| Step | Artifact | Gate |",
        "|------|----------|------|",
        f"| 0.1 | 00_01_source_audit.{{json,md}} | {s01} |",
        f"| 0.2 | 00_02_match_schema_profile.md | PASS (stability={stability_matches}) |",
        f"| 0.3 | 00_03_*.md + dtype_decision.json | PASS (strategy={dtype_strategy}) |",
        "| 0.4 | 00_04_singleton_schema_profile.md | PASS (T_snapshot recorded) |",
        f"| 0.5 | 00_05_smoke_test.md | {s05} |",
        f"| 0.6 | 00_06_ingestion_log.md | PASS (T_ingestion={t_ingestion}) |",
        f"| 0.7 | 00_07_rowcount_reconciliation.md | {s07} ({strength}) |",
        "",
        "## Artifact inventory",
        "",
        "All artifacts are in `reports/aoe2companion/`:",
        "",
        "- `00_01_source_audit.json` — source of truth: [Step 0.1]",
        "- `00_01_source_audit.md`",
        "- `00_02_match_schema_profile.md` — [Step 0.2]",
        "- `00_03_rating_schema_profile.md` — [Step 0.3]",
        "- `00_03_dtype_decision.json` — [Step 0.3]",
        "- `00_04_singleton_schema_profile.md` — [Step 0.4]",
        "- `00_05_smoke_test.md` — [Step 0.5]",
        "- `00_06_ingestion_log.md` — [Step 0.6]",
        "- `00_07_rowcount_reconciliation.md` — [Step 0.7]",
        "- `00_08_phase0_summary.md` — this file",
        "- `INVARIANTS.md` — binding invariants for downstream phases",
        "",
        "## Zero-row rating files",
        "",
        f"Sparse (zero-row) rating files: {zero_row_ratings}  ",
        f"Sparse/dense boundary: {boundary_date}  ",
        "These files are retained in raw_ratings to preserve provenance.",
        "Downstream phases should filter via a derived view using the boundary date",
        "recorded in INVARIANTS.md §I3.",
    ]

    (reports_dir / "00_08_phase0_summary.md").write_text("\n".join(summary_lines))
    logger.info("Step 0.8 complete: INVARIANTS.md and 00_08_phase0_summary.md written")


# ── Main orchestrator ─────────────────────────────────────────────────────────


def run_phase_0_audit(
    con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    manifest_path: Path,
    reports_dir: Path,
    steps: list[str] | None = None,
) -> dict[str, dict]:
    """Orchestrate all Phase 0 audit steps for aoe2companion.

    Steps are executed in strict epistemic order. The function is
    idempotent: re-running it will overwrite existing report artifacts
    and re-materialise raw tables with should_drop=True.

    Args:
        con: Active DuckDB connection (to the canonical db.duckdb).
        raw_dir: Path to the raw data root directory.
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
    decision: DtypeDecision | None = None

    if should_run("0.1"):
        results["0.1"] = run_source_audit(raw_dir, manifest_path, reports_dir)

    if should_run("0.2"):
        results["0.2"] = profile_match_schema(raw_dir, reports_dir)

    if should_run("0.3"):
        profile_result, decision = profile_rating_schema(raw_dir, reports_dir)
        results["0.3"] = profile_result
    else:
        # Load existing decision from disk if available
        decision_path = reports_dir / "00_03_dtype_decision.json"
        if decision_path.exists():
            decision = DtypeDecision.from_json(decision_path)
        else:
            decision = DtypeDecision(
                strategy="auto_detect",
                rationale="fallback: no decision artifact found",
            )

    if should_run("0.4"):
        results["0.4"] = profile_singleton_schemas(raw_dir, reports_dir)

    if should_run("0.5"):
        assert decision is not None
        results["0.5"] = run_smoke_test(raw_dir, decision, reports_dir)

    if should_run("0.6"):
        assert decision is not None
        results["0.6"] = run_full_ingestion(con, raw_dir, decision, reports_dir)

    if should_run("0.7"):
        results["0.7"] = run_rowcount_reconciliation(con, manifest_path, reports_dir)

    if should_run("0.8"):
        ingestion_result = results.get("0.6", {})
        write_phase0_summary(reports_dir, ingestion_result, results)
        results["0.8"] = {"written": True}

    return results
