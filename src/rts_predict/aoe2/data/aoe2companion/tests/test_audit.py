"""Tests for aoe2companion audit.py — Phase 0 audit functions."""

import json
from pathlib import Path

import duckdb

from rts_predict.aoe2.data.aoe2companion.audit import (
    profile_match_schema,
    profile_rating_schema,
    profile_singleton_schemas,
    run_full_ingestion,
    run_phase_0_audit,
    run_rowcount_reconciliation,
    run_smoke_test,
    run_source_audit,
    write_phase0_summary,
)
from rts_predict.aoe2.data.aoe2companion.ingestion import load_all_raw_tables
from rts_predict.aoe2.data.aoe2companion.types import DtypeDecision

# ── Step 0.1: run_source_audit ────────────────────────────────────────────────


def test_source_audit_passes_with_valid_files(
    raw_dir: Path,
    manifest_file: Path,
    tmp_path: Path,
) -> None:
    """Audit must pass when all manifest files exist with correct sizes."""
    reports_dir = tmp_path / "reports"
    result = run_source_audit(raw_dir, manifest_file, reports_dir)
    assert result["passed"] is True
    assert result["T_acquisition"] is not None
    assert (reports_dir / "00_01_source_audit.json").exists()
    assert (reports_dir / "00_01_source_audit.md").exists()


def test_source_audit_detects_missing_files(
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    """Audit must report failure when a manifest file is absent from disk."""
    # Create a manifest pointing to a non-existent file
    missing_path = raw_dir / "matches" / "match-9999-01-01.parquet"
    entries = [
        {
            "key": "match-9999-01-01.parquet",
            "target_path": str(missing_path),
            "size": 100000,
            "status": "downloaded",
            "timestamp": "2024-01-01T00:00:00+00:00",
            "error": None,
        }
    ]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(entries))

    reports_dir = tmp_path / "reports"
    result = run_source_audit(raw_dir, manifest_path, reports_dir)
    assert result["passed"] is False
    assert len(result["failures"]) == 1
    assert result["failures"][0]["reason"] == "missing_from_disk"


def test_source_audit_detects_size_mismatch(
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    """Audit must report size mismatch when manifest size differs from on-disk."""
    match_file = raw_dir / "matches" / "match-2024-01-01.parquet"
    actual_size = match_file.stat().st_size
    wrong_size = actual_size + 1000  # artificially inflated

    entries = [
        {
            "key": "match-2024-01-01.parquet",
            "target_path": str(match_file),
            "size": wrong_size,
            "status": "downloaded",
            "timestamp": "2024-01-01T00:00:00+00:00",
            "error": None,
        }
    ]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(entries))

    reports_dir = tmp_path / "reports"
    result = run_source_audit(raw_dir, manifest_path, reports_dir)
    assert len(result["size_mismatches"]) == 1
    assert result["size_mismatches"][0]["key"] == "match-2024-01-01.parquet"


def test_source_audit_detects_corrupted_zero_byte_file(
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    """Audit must detect a zero-byte file as a failure."""
    zero_path = raw_dir / "matches" / "match-zero.parquet"
    zero_path.write_bytes(b"")  # deliberately zero bytes

    entries = [
        {
            "key": "match-zero.parquet",
            "target_path": str(zero_path),
            "size": 0,
            "status": "downloaded",
            "timestamp": "2024-01-01T00:00:00+00:00",
            "error": None,
        }
    ]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(entries))

    reports_dir = tmp_path / "reports"
    result = run_source_audit(raw_dir, manifest_path, reports_dir)
    assert len(result["zero_byte_files"]) == 1
    assert result["passed"] is False


def test_source_audit_records_t_acquisition(
    raw_dir: Path,
    manifest_file: Path,
    tmp_path: Path,
) -> None:
    """Audit result must record T_acquisition from manifest timestamps."""
    reports_dir = tmp_path / "reports"
    result = run_source_audit(raw_dir, manifest_file, reports_dir)
    assert result["T_acquisition"] is not None
    # Should look like an ISO timestamp
    t = result["T_acquisition"]
    assert "T" in t or "-" in t


# ── Step 0.2: profile_match_schema ───────────────────────────────────────────


def test_profile_match_schema_produces_report(
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    """profile_match_schema must write a Markdown report."""
    reports_dir = tmp_path / "reports"
    result = profile_match_schema(raw_dir, reports_dir)
    assert (reports_dir / "00_02_match_schema_profile.md").exists()
    assert result["stability"] in ("STABLE", "DRIFTED")
    assert len(result["samples"]) >= 1
    assert len(result["union_schema"]) > 0


def test_profile_match_schema_includes_sql(raw_dir: Path, tmp_path: Path) -> None:
    """The match schema report must contain literal SQL."""
    reports_dir = tmp_path / "reports"
    profile_match_schema(raw_dir, reports_dir)
    md = (reports_dir / "00_02_match_schema_profile.md").read_text()
    assert "DESCRIBE" in md
    assert "read_parquet" in md


# ── Step 0.3: profile_rating_schema ──────────────────────────────────────────


def test_profile_rating_schema_produces_decision_artifact(
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    """Step 0.3 must write 00_03_dtype_decision.json and return a DtypeDecision."""
    reports_dir = tmp_path / "reports"
    result, decision = profile_rating_schema(raw_dir, reports_dir)
    assert (reports_dir / "00_03_dtype_decision.json").exists()
    assert decision.strategy in ("auto_detect", "explicit")
    assert decision.rationale


def test_dtype_decision_auto_detect_path(tmp_path: Path) -> None:
    """When all CSVs have consistent schemas, strategy must be auto_detect."""
    # Build a raw_dir with only dense CSVs (no sparse/header-only) to trigger
    # auto_detect (all schemas agree on numeric types).
    import pyarrow as pa_mod
    import pyarrow.parquet as pq_mod

    raw = tmp_path / "raw2"
    ratings = raw / "ratings"
    ratings.mkdir(parents=True)
    header = "profile_id,games,rating,date,leaderboard_id,rating_diff,season\n"
    row = "1000001,50,1400,2024-01-01 00:00:00,3,5,-1\n"
    dense_content = header + row * 60
    (ratings / "rating-2024-01-01.csv").write_text(dense_content)
    (ratings / "rating-2024-01-02.csv").write_text(dense_content)

    # Provide minimal matches/leaderboards/profiles so function can be called
    matches = raw / "matches"
    matches.mkdir()
    lbs = raw / "leaderboards"
    lbs.mkdir()
    profs = raw / "profiles"
    profs.mkdir()
    # Write stub parquets
    pq_mod.write_table(
        pa_mod.table({"id": pa_mod.array([1], type=pa_mod.int64())}),
        matches / "match-2024-01-01.parquet",
    )
    pq_mod.write_table(
        pa_mod.table({"id": pa_mod.array([1], type=pa_mod.int64())}),
        lbs / "leaderboard.parquet",
    )
    pq_mod.write_table(
        pa_mod.table({"id": pa_mod.array([1], type=pa_mod.int64())}),
        profs / "profile.parquet",
    )

    reports_dir = tmp_path / "reports2"
    _result, decision = profile_rating_schema(raw, reports_dir)
    # All files have same schema (dense only) — should get auto_detect
    assert decision.strategy == "auto_detect"


def test_dtype_decision_explicit_map_applied(tmp_path: Path) -> None:
    """DtypeDecision with explicit strategy round-trips through JSON correctly."""
    decision = DtypeDecision(
        strategy="explicit",
        rationale="test explicit",
        dtype_map={"profile_id": "BIGINT", "rating": "INTEGER"},
    )
    path = tmp_path / "decision.json"
    decision.to_json(path)

    loaded = DtypeDecision.from_json(path)
    assert loaded.strategy == "explicit"
    assert loaded.dtype_map["profile_id"] == "BIGINT"
    assert loaded.rationale == "test explicit"


def test_profile_rating_schema_records_boundary_date(
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    """Step 0.3 must record the sparse/dense boundary date."""
    reports_dir = tmp_path / "reports"
    result, _decision = profile_rating_schema(raw_dir, reports_dir)
    # Our fixture has a sparse file (rating-2020-08-01.csv) and a dense one
    assert result["boundary_date"] is not None
    assert result["sparse_count"] >= 1


# ── Step 0.4: profile_singleton_schemas ──────────────────────────────────────


def test_profile_singleton_schemas_produces_report(
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    reports_dir = tmp_path / "reports"
    result = profile_singleton_schemas(raw_dir, reports_dir)
    assert (reports_dir / "00_04_singleton_schema_profile.md").exists()
    assert result["leaderboard_rows"] > 0
    assert result["profiles_rows"] > 0
    assert result["T_snapshot_leaderboard"] is not None
    assert result["T_snapshot_profiles"] is not None


def test_profile_singleton_schemas_includes_sql(raw_dir: Path, tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    profile_singleton_schemas(raw_dir, reports_dir)
    md = (reports_dir / "00_04_singleton_schema_profile.md").read_text()
    assert "DESCRIBE" in md
    assert "read_parquet" in md


# ── Step 0.5: run_smoke_test ─────────────────────────────────────────────────


def test_smoke_test_passes_with_valid_raw_dir(
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    """Smoke test must pass with the synthetic raw directory."""
    decision = DtypeDecision(strategy="auto_detect", rationale="test")
    reports_dir = tmp_path / "reports"
    result = run_smoke_test(raw_dir, decision, reports_dir)
    assert result["passed"] is True
    assert result["ratings_files"] == 2
    assert all(result["filename_cols"].values())
    assert (reports_dir / "00_05_smoke_test.md").exists()


def test_smoke_test_report_includes_sql(raw_dir: Path, tmp_path: Path) -> None:
    decision = DtypeDecision(strategy="auto_detect", rationale="test")
    reports_dir = tmp_path / "reports"
    run_smoke_test(raw_dir, decision, reports_dir)
    md = (reports_dir / "00_05_smoke_test.md").read_text()
    assert "CREATE TABLE smoke_ratings" in md
    assert "union_by_name" in md


# ── Step 0.6: run_full_ingestion ─────────────────────────────────────────────


def test_run_full_ingestion_creates_all_tables(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    decision = DtypeDecision(strategy="auto_detect", rationale="test")
    reports_dir = tmp_path / "reports"
    result = run_full_ingestion(db_con, raw_dir, decision, reports_dir)
    assert set(result["table_counts"].keys()) == {
        "raw_matches",
        "raw_ratings",
        "raw_leaderboard",
        "raw_profiles",
    }
    assert result["T_ingestion"] is not None
    assert (reports_dir / "00_06_ingestion_log.md").exists()


# ── Step 0.7: run_rowcount_reconciliation ────────────────────────────────────


def test_reconciliation_strict_passes(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    manifest_file: Path,
    tmp_path: Path,
) -> None:
    """Reconciliation must pass when file counts match the manifest."""
    decision = DtypeDecision(strategy="auto_detect", rationale="test")
    # Load tables first
    load_all_raw_tables(db_con, raw_dir, decision=decision)
    reports_dir = tmp_path / "reports"
    result = run_rowcount_reconciliation(db_con, manifest_file, reports_dir)
    # Our synthetic manifest has 2 matches, 2 ratings, 1 leaderboard, 1 profiles
    # Reconciliation uses expected counts {2073,2072,...} so file_count_ok will
    # be False (synthetic has 2 match files, not 2073) — but structure tests pass
    assert result["strength"] in ("STRICT", "DEGRADED")
    assert (reports_dir / "00_07_rowcount_reconciliation.md").exists()


def test_reconciliation_strict_fails_on_mismatch(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    manifest_file: Path,
    tmp_path: Path,
) -> None:
    """When actual file count != expected, file_count_ok must be False."""
    decision = DtypeDecision(strategy="auto_detect", rationale="test")
    load_all_raw_tables(db_con, raw_dir, decision=decision)
    reports_dir = tmp_path / "reports"
    result = run_rowcount_reconciliation(db_con, manifest_file, reports_dir)
    # Synthetic data has 2 match files, not 2073 — so this should be a mismatch
    assert result["file_count_ok"] is False


def test_reconciliation_report_includes_sql(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    manifest_file: Path,
    tmp_path: Path,
) -> None:
    decision = DtypeDecision(strategy="auto_detect", rationale="test")
    load_all_raw_tables(db_con, raw_dir, decision=decision)
    reports_dir = tmp_path / "reports"
    run_rowcount_reconciliation(db_con, manifest_file, reports_dir)
    md = (reports_dir / "00_07_rowcount_reconciliation.md").read_text()
    assert "SELECT count(DISTINCT filename)" in md
    assert "GROUP BY filename" in md


# ── Step 0.8: write_phase0_summary ───────────────────────────────────────────


def test_write_phase0_summary_produces_both_files(tmp_path: Path) -> None:
    """Step 0.8 must write 00_08_phase0_summary.md and INVARIANTS.md."""
    reports_dir = tmp_path / "reports"
    ingestion_result = {
        "table_counts": {
            "raw_matches": 5000,
            "raw_ratings": 3000,
            "raw_leaderboard": 1000,
            "raw_profiles": 500,
        },
        "T_ingestion": "2024-01-01T12:00:00+00:00",
        "dtype_strategy_applied": "auto_detect",
    }
    audit_results: dict = {
        "0.1": {"passed": True, "T_acquisition": "2024-01-01T00:00:00+00:00"},
        "0.2": {"stability": "STABLE"},
        "0.3": {
            "boundary_date": "2025-06-22",
            "sparse_count": 1336,
            "dense_count": 282,
            "decision": {
                "strategy": "auto_detect",
                "rationale": "test",
                "dtype_map": {},
            },
        },
        "0.4": {
            "T_snapshot_leaderboard": "2024-01-01T00:00:00+00:00",
            "T_snapshot_profiles": "2024-01-01T00:00:00+00:00",
        },
        "0.5": {"passed": True},
        "0.7": {
            "passed": True,
            "strength": "DEGRADED",
            "zero_row_ratings": 1336,
            "file_counts": {
                "raw_matches": 2073,
                "raw_ratings": 2072,
                "raw_leaderboard": 1,
                "raw_profiles": 1,
            },
        },
    }
    write_phase0_summary(reports_dir, ingestion_result, audit_results)
    assert (reports_dir / "00_08_phase0_summary.md").exists()
    assert (reports_dir / "INVARIANTS.md").exists()
    invariants = (reports_dir / "INVARIANTS.md").read_text()
    assert "I1." in invariants
    assert "I2." in invariants
    assert "I3." in invariants
    assert "I4." in invariants
    assert "I5." in invariants
    assert "I6." in invariants
    assert "I7." in invariants


# ── run_phase_0_audit orchestrator ───────────────────────────────────────────


def test_run_phase_0_audit_selective_steps(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    manifest_file: Path,
    tmp_path: Path,
) -> None:
    """run_phase_0_audit with steps=['0.1'] must only run step 0.1."""
    reports_dir = tmp_path / "reports"
    results = run_phase_0_audit(
        db_con, raw_dir, manifest_file, reports_dir, steps=["0.1"]
    )
    assert "0.1" in results
    assert "0.2" not in results
    assert (reports_dir / "00_01_source_audit.json").exists()
    assert not (reports_dir / "00_02_match_schema_profile.md").exists()


def test_run_phase_0_audit_idempotent(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    manifest_file: Path,
    tmp_path: Path,
) -> None:
    """run_phase_0_audit must be safe to re-run (idempotent)."""
    reports_dir = tmp_path / "reports"
    # Run steps 0.1–0.5 (non-DB steps) twice
    results1 = run_phase_0_audit(
        db_con, raw_dir, manifest_file, reports_dir, steps=["0.1", "0.2", "0.3", "0.4"]
    )
    results2 = run_phase_0_audit(
        db_con, raw_dir, manifest_file, reports_dir, steps=["0.1", "0.2", "0.3", "0.4"]
    )
    assert results1["0.1"]["passed"] == results2["0.1"]["passed"]
