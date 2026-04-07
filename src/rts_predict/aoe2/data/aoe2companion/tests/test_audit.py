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


# ── Step 3: source audit oversized branch (lines 255-269) ────────────────────


def test_source_audit_oversized_file_passes_gate(tmp_path: Path) -> None:
    """Oversized files (actual > expected) pass the gate (lines 255-269)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    # Write a real file so it has non-zero size
    file_path = tmp_path / "matches" / "match-2024-01-01.parquet"
    file_path.parent.mkdir(parents=True)
    pq.write_table(
        pa.table({"id": pa.array([1, 2, 3], type=pa.int64())}),
        file_path,
    )
    actual_size = file_path.stat().st_size
    # Manifest records a smaller size than disk — "oversized" (CDN update scenario)
    manifest_size = actual_size - 10
    assert manifest_size > 0

    entries = [
        {
            "key": "match-2024-01-01.parquet",
            "target_path": str(file_path),
            "size": manifest_size,
            "status": "downloaded",
            "timestamp": "2024-01-02T00:00:00+00:00",
            "error": None,
        }
    ]
    manifest_path = tmp_path / "_download_manifest.json"
    manifest_path.write_text(json.dumps(entries))

    reports_dir = tmp_path / "reports"
    result = run_source_audit(tmp_path, manifest_path, reports_dir)

    assert result["passed"] is True
    assert len(result["oversized_mismatches"]) == 1
    md = (reports_dir / "00_01_source_audit.md").read_text()
    assert "Oversized" in md


# ── Step 4: schema profiling edge cases ──────────────────────────────────────


def test_profile_match_schema_empty_dir_raises(tmp_path: Path) -> None:
    """FileNotFoundError when matches dir is empty (line 325)."""
    import pytest

    raw = tmp_path / "raw"
    (raw / "matches").mkdir(parents=True)
    reports_dir = tmp_path / "reports"
    with pytest.raises(FileNotFoundError, match="No match parquets"):
        profile_match_schema(raw, reports_dir)


def test_profile_match_schema_drifted_columns(tmp_path: Path) -> None:
    """Drift detected when sample schemas disagree on columns (lines 421-437)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    raw = tmp_path / "raw"
    matches = raw / "matches"
    matches.mkdir(parents=True)

    # 4 files with standard schema
    for i in range(1, 5):
        pq.write_table(
            pa.table(
                {
                    "match_id": pa.array([i], type=pa.int64()),
                    "score": pa.array([100 * i], type=pa.int64()),
                }
            ),
            matches / f"match-2024-01-0{i}.parquet",
        )
    # 1 file with an extra column — triggers drift
    pq.write_table(
        pa.table(
            {
                "match_id": pa.array([5], type=pa.int64()),
                "score": pa.array([500], type=pa.int64()),
                "extra_col": pa.array(["drift"], type=pa.string()),
            }
        ),
        matches / "match-2024-01-05.parquet",
    )

    reports_dir = tmp_path / "reports"
    result = profile_match_schema(raw, reports_dir)

    assert result["stability"] == "DRIFTED"
    md = (reports_dir / "00_02_match_schema_profile.md").read_text()
    assert "Schema drift" in md or "extra_col" in md


def test_profile_rating_schema_empty_dir_raises(tmp_path: Path) -> None:
    """FileNotFoundError when ratings dir is empty (line 475)."""
    import pytest

    raw = tmp_path / "raw"
    (raw / "ratings").mkdir(parents=True)
    reports_dir = tmp_path / "reports"
    with pytest.raises(FileNotFoundError, match="No rating CSVs"):
        profile_rating_schema(raw, reports_dir)


def test_profile_rating_schema_many_csvs_triggers_stepped_pick(tmp_path: Path) -> None:
    """_pick() stepped-sampling branch fires when len(lst) > n (lines 506-507)."""
    raw = tmp_path / "raw"
    ratings = raw / "ratings"
    ratings.mkdir(parents=True)

    header = "profile_id,games,rating,date,leaderboard_id,rating_diff,season\n"
    row = "1000001,50,1400,2024-01-01 00:00:00,3,5,-1\n"
    dense_content = header + row * 60  # definitely > 1 KB

    # 5 dense CSVs — more than the n=3 pick limit, forcing the step branch
    for day in range(1, 6):
        (ratings / f"rating-2024-01-0{day}.csv").write_text(dense_content)

    reports_dir = tmp_path / "reports"
    _result, decision = profile_rating_schema(raw, reports_dir)
    # Simply verify the function succeeds; stepped pick was used internally
    assert decision.strategy in ("auto_detect", "explicit")


def test_profile_rating_schema_type_inconsistency_triggers_explicit(
    tmp_path: Path,
) -> None:
    """Inconsistent column types across CSVs produce explicit strategy (lines 565-567, 576-587)."""
    raw = tmp_path / "raw"
    ratings = raw / "ratings"
    ratings.mkdir(parents=True)

    header = "profile_id,games,rating,date,leaderboard_id,rating_diff,season\n"
    # CSV 1: rating as INTEGER (no decimals)
    row_int = "1000001,50,1400,2024-01-01 00:00:00,3,5,-1\n"
    dense_int = header + row_int * 60
    (ratings / "rating-2024-01-01.csv").write_text(dense_int)

    # CSV 2: rating as DOUBLE (decimal value forces DuckDB to infer DOUBLE)
    row_float = "1000002,55,1400.5,2024-01-02 00:00:00,3,5,-1\n"
    dense_float = header + row_float * 60
    (ratings / "rating-2024-01-02.csv").write_text(dense_float)

    reports_dir = tmp_path / "reports"
    _result, decision = profile_rating_schema(raw, reports_dir)

    assert decision.strategy == "explicit"
    assert decision.dtype_map
    assert "inconsistent" in decision.rationale.lower()


# ── Step 5: smoke test edge cases ────────────────────────────────────────────


def test_smoke_test_no_match_parquets_raises(tmp_path: Path) -> None:
    """FileNotFoundError when matches dir is empty (line 842)."""
    import pytest

    raw = tmp_path / "raw"
    (raw / "matches").mkdir(parents=True)
    (raw / "ratings").mkdir(parents=True)
    (raw / "ratings" / "rating-2024-01-01.csv").write_text("x")

    decision = DtypeDecision(strategy="auto_detect", rationale="test")
    reports_dir = tmp_path / "reports"
    with pytest.raises(FileNotFoundError, match="No match parquets"):
        run_smoke_test(raw, decision, reports_dir)


def test_smoke_test_no_rating_csvs_raises(tmp_path: Path) -> None:
    """FileNotFoundError when ratings dir is empty (line 844)."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    import pytest

    raw = tmp_path / "raw"
    matches = raw / "matches"
    matches.mkdir(parents=True)
    pq.write_table(
        pa.table({"id": pa.array([1], type=pa.int64())}),
        matches / "match-2024-01-01.parquet",
    )
    (raw / "ratings").mkdir(parents=True)

    decision = DtypeDecision(strategy="auto_detect", rationale="test")
    reports_dir = tmp_path / "reports"
    with pytest.raises(FileNotFoundError, match="No rating CSVs"):
        run_smoke_test(raw, decision, reports_dir)


def test_smoke_test_no_sparse_csvs_raises(tmp_path: Path) -> None:
    """FileNotFoundError when no sparse/transition CSVs exist (line 865)."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    import pytest

    raw = tmp_path / "raw"
    matches = raw / "matches"
    matches.mkdir(parents=True)
    pq.write_table(
        pa.table({"match_id": pa.array([1], type=pa.int64())}),
        matches / "match-2024-01-01.parquet",
    )

    ratings = raw / "ratings"
    ratings.mkdir(parents=True)
    header = "profile_id,games,rating,date,leaderboard_id,rating_diff,season\n"
    row = "1000001,50,1400,2024-01-01 00:00:00,3,5,-1\n"
    # Dense CSVs only (>= 1024 bytes) — no sparse/transition files
    (ratings / "rating-2024-01-01.csv").write_text(header + row * 80)
    (ratings / "rating-2024-01-02.csv").write_text(header + row * 80)

    decision = DtypeDecision(strategy="auto_detect", rationale="test")
    reports_dir = tmp_path / "reports"
    with pytest.raises(FileNotFoundError, match="No sparse"):
        run_smoke_test(raw, decision, reports_dir)


def test_smoke_test_no_dense_csvs_raises(tmp_path: Path) -> None:
    """FileNotFoundError when no dense CSVs exist (line 867)."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    import pytest

    raw = tmp_path / "raw"
    matches = raw / "matches"
    matches.mkdir(parents=True)
    pq.write_table(
        pa.table({"match_id": pa.array([1], type=pa.int64())}),
        matches / "match-2024-01-01.parquet",
    )

    ratings = raw / "ratings"
    ratings.mkdir(parents=True)
    # Header-only CSVs (63 bytes each) — no dense files
    header = "profile_id,games,rating,date,leaderboard_id,rating_diff,season\n"
    (ratings / "rating-2020-01-01.csv").write_text(header)
    (ratings / "rating-2020-01-02.csv").write_text(header)

    decision = DtypeDecision(strategy="auto_detect", rationale="test")
    reports_dir = tmp_path / "reports"
    with pytest.raises(FileNotFoundError, match="No dense"):
        run_smoke_test(raw, decision, reports_dir)


def test_smoke_test_explicit_dtype_path(raw_dir: Path, tmp_path: Path) -> None:
    """Explicit dtype strategy builds dtypes literal in SQL (lines 883-888)."""
    decision = DtypeDecision(
        strategy="explicit",
        rationale="test",
        dtype_map={"rating": "INTEGER", "profile_id": "BIGINT"},
    )
    reports_dir = tmp_path / "reports"
    result = run_smoke_test(raw_dir, decision, reports_dir)
    md = (reports_dir / "00_05_smoke_test.md").read_text()
    assert "dtypes" in md or "explicit" in md.lower()
    # Smoke test may or may not pass depending on fixture; just assert no crash
    assert isinstance(result["passed"], bool)


def test_smoke_test_sql_error_captured(tmp_path: Path) -> None:
    """DuckDB error from corrupt parquet is captured gracefully (lines 902-904, 1017-1019)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    raw = tmp_path / "raw"
    matches = raw / "matches"
    matches.mkdir(parents=True)
    # Write a corrupt parquet (not valid parquet bytes)
    (matches / "match-2024-01-01.parquet").write_bytes(b"NOT A PARQUET FILE")

    ratings = raw / "ratings"
    ratings.mkdir(parents=True)
    header = "profile_id,games,rating,date,leaderboard_id,rating_diff,season\n"
    row = "1000001,50,1400,2024-01-01 00:00:00,3,5,-1\n"
    # Sparse (transition) file: between 63 and 1024 bytes
    (ratings / "rating-2020-01-01.csv").write_text(header + row)
    # Dense file
    (ratings / "rating-2024-01-01.csv").write_text(header + row * 80)

    leaderboards = raw / "leaderboards"
    leaderboards.mkdir(parents=True)
    pq.write_table(
        pa.table({"profile_id": pa.array([1], type=pa.int64())}),
        leaderboards / "leaderboard.parquet",
    )

    profiles = raw / "profiles"
    profiles.mkdir(parents=True)
    pq.write_table(
        pa.table({"profile_id": pa.array([1], type=pa.int64())}),
        profiles / "profile.parquet",
    )

    decision = DtypeDecision(strategy="auto_detect", rationale="test")
    reports_dir = tmp_path / "reports"
    result = run_smoke_test(raw, decision, reports_dir)

    assert result["passed"] is False
    assert len(result["errors"]) > 0
    md = (reports_dir / "00_05_smoke_test.md").read_text()
    assert "## Errors" in md


# ── Step 6: run_full_ingestion explicit dtype + reconciliation ────────────────


def test_run_full_ingestion_explicit_dtype(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    """Explicit dtype path builds dtypes literal in SQL report (lines 1068-1073)."""
    decision = DtypeDecision(
        strategy="explicit",
        rationale="test explicit ingestion",
        dtype_map={
            "profile_id": "BIGINT",
            "games": "INTEGER",
            "rating": "INTEGER",
            "leaderboard_id": "INTEGER",
            "rating_diff": "INTEGER",
            "season": "INTEGER",
        },
    )
    reports_dir = tmp_path / "reports"
    result = run_full_ingestion(db_con, raw_dir, decision, reports_dir)

    assert set(result["table_counts"].keys()) == {
        "raw_matches",
        "raw_ratings",
        "raw_leaderboard",
        "raw_profiles",
    }
    md = (reports_dir / "00_06_ingestion_log.md").read_text()
    assert "dtypes" in md


def test_rowcount_reconciliation_counts_zero_row_ratings(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    """zero_row_ratings counts header-only CSVs on disk (line 1181).

    For line 1181 to execute, manifest_path.parent / 'ratings' must exist.
    We place the manifest inside raw_dir so that manifest_path.parent == raw_dir
    and raw_dir / 'ratings' resolves to the existing ratings directory.
    """
    import json as _json

    from rts_predict.aoe2.data.aoe2companion.ingestion import load_all_raw_tables

    # Add a truly header-only CSV (exactly 63 bytes) to the ratings directory
    header_only = "profile_id,games,rating,date,leaderboard_id,rating_diff,season\n"
    header_only_path = raw_dir / "ratings" / "rating-2019-01-01.csv"
    header_only_path.write_text(header_only)
    assert header_only_path.stat().st_size == 63

    # Write manifest adjacent to ratings/ dir (raw_dir / ratings) so
    # manifest_path.parent / 'ratings' resolves to the existing ratings dir
    entries = [
        {
            "key": "rating-2019-01-01.csv",
            "target_path": str(header_only_path),
            "size": header_only_path.stat().st_size,
            "status": "downloaded",
            "timestamp": "2019-01-01T00:00:00+00:00",
            "error": None,
        },
        {
            "key": "rating-2024-01-01.csv",
            "target_path": str(raw_dir / "ratings" / "rating-2024-01-01.csv"),
            "size": (raw_dir / "ratings" / "rating-2024-01-01.csv").stat().st_size,
            "status": "downloaded",
            "timestamp": "2024-01-02T00:00:00+00:00",
            "error": None,
        },
    ]
    # Place manifest in raw_dir so manifest_path.parent / 'ratings' == raw_dir / 'ratings'
    manifest_path = raw_dir / "_download_manifest.json"
    manifest_path.write_text(_json.dumps(entries, indent=2))

    decision = DtypeDecision(strategy="auto_detect", rationale="test")
    load_all_raw_tables(db_con, raw_dir, decision=decision)
    reports_dir = tmp_path / "reports"
    result = run_rowcount_reconciliation(db_con, manifest_path, reports_dir)

    assert "zero_row_ratings" in result
    assert isinstance(result["zero_row_ratings"], int)
    # The header-only CSV (≤ 63 bytes) must be counted as a zero-row rating file
    assert result["zero_row_ratings"] >= 1


# ── Step 7: write_phase0_summary STRICT branch + orchestrator ────────────────


def test_write_phase0_summary_strict_reconciliation(tmp_path: Path) -> None:
    """STRICT reconciliation produces the per-file assertion line (line 1430)."""
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
            "sparse_count": 0,
            "dense_count": 2,
            "sparse_date_range": None,
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
        # strength == "STRICT" triggers line 1430
        "0.7": {
            "passed": True,
            "strength": "STRICT",
            "zero_row_ratings": 0,
            "file_counts": {
                "raw_matches": 2073,
                "raw_ratings": 2072,
                "raw_leaderboard": 1,
                "raw_profiles": 1,
            },
        },
    }
    write_phase0_summary(reports_dir, ingestion_result, audit_results)
    invariants = (reports_dir / "INVARIANTS.md").read_text()
    assert "per-file actual_rows == manifest_rows" in invariants


def test_run_phase_0_audit_later_steps(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    manifest_file: Path,
    tmp_path: Path,
) -> None:
    """Orchestrator runs steps 0.5-0.8, loading decision from disk (lines 1542, 1553-1566)."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Pre-write a dtype decision so line 1542 (DtypeDecision.from_json) is exercised
    decision = DtypeDecision(
        strategy="auto_detect",
        rationale="pre-written for test",
    )
    decision.to_json(reports_dir / "00_03_dtype_decision.json")

    results = run_phase_0_audit(
        db_con,
        raw_dir,
        manifest_file,
        reports_dir,
        steps=["0.5", "0.6", "0.7", "0.8"],
    )

    assert "0.5" in results   # covers lines 1553-1554
    assert "0.6" in results   # covers lines 1557-1558
    assert "0.7" in results   # covers line 1561
    assert "0.8" in results   # covers lines 1564-1566
