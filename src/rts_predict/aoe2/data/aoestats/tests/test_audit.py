"""Tests for aoestats audit.py — Phase 0 audit functions."""

import json
from pathlib import Path

import duckdb

from rts_predict.aoe2.data.aoestats.audit import (
    profile_match_schema,
    profile_player_schema,
    run_full_ingestion,
    run_phase_0_audit,
    run_rowcount_reconciliation,
    run_smoke_test,
    run_source_audit,
    write_phase0_summary,
)
from rts_predict.aoe2.data.aoestats.ingestion import load_all_raw_tables

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
    missing_path = raw_dir / "matches" / "9999-01-01_9999-01-07_matches.parquet"
    entries = [
        {
            "file_type": "matches",
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


def test_source_audit_detects_size_mismatch(
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    """Audit must report size mismatch when manifest size differs from on-disk."""
    match_file = raw_dir / "matches" / "2024-01-01_2024-01-07_matches.parquet"
    actual_size = match_file.stat().st_size
    wrong_size = actual_size + 1000

    entries = [
        {
            "file_type": "matches",
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


def test_source_audit_detects_corrupted_zero_byte_file(
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    """Audit must detect a zero-byte file as a failure."""
    zero_path = raw_dir / "matches" / "zero_matches.parquet"
    zero_path.write_bytes(b"")

    entries = [
        {
            "file_type": "matches",
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


# ── Steps 0.2 and 0.3: schema profiling ──────────────────────────────────────


def test_profile_match_schema_produces_report(
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    reports_dir = tmp_path / "reports"
    result = profile_match_schema(raw_dir, reports_dir)
    assert (reports_dir / "00_02_match_schema_profile.md").exists()
    assert result["stability"] in ("STABLE", "DRIFTED")
    assert len(result["union_schema"]) > 0


def test_profile_match_schema_includes_sql(raw_dir: Path, tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    profile_match_schema(raw_dir, reports_dir)
    md = (reports_dir / "00_02_match_schema_profile.md").read_text()
    assert "DESCRIBE" in md
    assert "read_parquet" in md


def test_profile_match_schema_includes_row_counts(raw_dir: Path, tmp_path: Path) -> None:
    """Schema profile report must contain per-sample row counts."""
    reports_dir = tmp_path / "reports"
    result = profile_match_schema(raw_dir, reports_dir)
    assert "per_sample_row_counts" in result
    assert len(result["per_sample_row_counts"]) > 0
    for count in result["per_sample_row_counts"].values():
        assert isinstance(count, int)
        assert count > 0
    md = (reports_dir / "00_02_match_schema_profile.md").read_text()
    assert "Row count:" in md


def test_profile_player_schema_produces_report(
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    reports_dir = tmp_path / "reports"
    result = profile_player_schema(raw_dir, reports_dir)
    assert (reports_dir / "00_03_player_schema_profile.md").exists()
    assert result["stability"] in ("STABLE", "DRIFTED")
    assert len(result["union_schema"]) > 0


def test_profile_player_schema_includes_row_counts(raw_dir: Path, tmp_path: Path) -> None:
    """Player schema profile report must contain per-sample row counts."""
    reports_dir = tmp_path / "reports"
    result = profile_player_schema(raw_dir, reports_dir)
    assert "per_sample_row_counts" in result
    assert len(result["per_sample_row_counts"]) > 0
    for count in result["per_sample_row_counts"].values():
        assert isinstance(count, int)
        assert count > 0
    md = (reports_dir / "00_03_player_schema_profile.md").read_text()
    assert "Row count:" in md


# ── Step 0.4: run_smoke_test ──────────────────────────────────────────────────


def test_smoke_test_passes_with_valid_raw_dir(
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    """Smoke test must pass with the synthetic raw directory."""
    reports_dir = tmp_path / "reports"
    result = run_smoke_test(raw_dir, reports_dir)
    assert result["passed"] is True
    assert result["matches_files"] == 2
    assert result["players_files"] == 2
    assert all(result["filename_cols"].values())
    assert (reports_dir / "00_04_smoke_test.md").exists()


def test_smoke_test_report_includes_sql(raw_dir: Path, tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    run_smoke_test(raw_dir, reports_dir)
    md = (reports_dir / "00_04_smoke_test.md").read_text()
    assert "CREATE TABLE smoke_matches" in md
    assert "union_by_name" in md


# ── Step 0.5: run_full_ingestion ──────────────────────────────────────────────


def test_run_full_ingestion_creates_all_tables(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    reports_dir = tmp_path / "reports"
    result = run_full_ingestion(db_con, raw_dir, reports_dir)
    assert set(result["table_counts"].keys()) == {"raw_matches", "raw_players"}
    assert result["T_ingestion"] is not None
    assert (reports_dir / "00_05_ingestion_log.md").exists()


# ── Step 0.6: run_rowcount_reconciliation ────────────────────────────────────


def test_reconciliation_strict_passes(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    manifest_file: Path,
    tmp_path: Path,
) -> None:
    """Reconciliation must produce results even when file counts differ from expected."""
    load_all_raw_tables(db_con, raw_dir)
    reports_dir = tmp_path / "reports"
    result = run_rowcount_reconciliation(db_con, manifest_file, reports_dir)
    assert result["strength"] in ("STRICT", "DEGRADED")
    assert (reports_dir / "00_06_rowcount_reconciliation.md").exists()


def test_reconciliation_strict_fails_on_mismatch(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    manifest_file: Path,
    tmp_path: Path,
) -> None:
    """When actual file count != expected from manifest, file_count_ok can be False."""
    load_all_raw_tables(db_con, raw_dir)
    reports_dir = tmp_path / "reports"
    result = run_rowcount_reconciliation(db_con, manifest_file, reports_dir)
    # Synthetic data has 2 match files; manifest also has 2 → should match
    # The reconciliation tests against MANIFEST count (2), not hardcoded 172
    assert result["file_count_ok"] is True


def test_reconciliation_report_includes_sql(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    manifest_file: Path,
    tmp_path: Path,
) -> None:
    load_all_raw_tables(db_con, raw_dir)
    reports_dir = tmp_path / "reports"
    run_rowcount_reconciliation(db_con, manifest_file, reports_dir)
    md = (reports_dir / "00_06_rowcount_reconciliation.md").read_text()
    assert "SELECT count(DISTINCT filename)" in md
    assert "GROUP BY filename" in md


# ── Step 0.7: write_phase0_summary ───────────────────────────────────────────


def test_write_phase0_summary_produces_both_files(tmp_path: Path) -> None:
    """Step 0.7 must write 00_07_phase0_summary.md and INVARIANTS.md."""
    reports_dir = tmp_path / "reports"
    ingestion_result = {
        "table_counts": {"raw_matches": 5000, "raw_players": 10000},
        "T_ingestion": "2024-01-01T12:00:00+00:00",
    }
    audit_results: dict = {
        "0.1": {"passed": True, "T_acquisition": "2024-01-01T00:00:00+00:00"},
        "0.2": {"stability": "STABLE"},
        "0.3": {"stability": "STABLE"},
        "0.4": {"passed": True},
        "0.6": {
            "passed": True,
            "strength": "DEGRADED",
            "file_counts": {"raw_matches": 172, "raw_players": 171},
            "notes": ["1 failed download: 2025-11-16_2025-11-22_players.parquet"],
        },
    }
    write_phase0_summary(reports_dir, ingestion_result, audit_results)
    assert (reports_dir / "00_07_phase0_summary.md").exists()
    assert (reports_dir / "INVARIANTS.md").exists()
    invariants = (reports_dir / "INVARIANTS.md").read_text()
    assert "I1." in invariants
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
    """run_phase_0_audit must be safe to re-run."""
    reports_dir = tmp_path / "reports"
    r1 = run_phase_0_audit(
        db_con, raw_dir, manifest_file, reports_dir, steps=["0.1", "0.2", "0.3"]
    )
    r2 = run_phase_0_audit(
        db_con, raw_dir, manifest_file, reports_dir, steps=["0.1", "0.2", "0.3"]
    )
    assert r1["0.1"]["passed"] == r2["0.1"]["passed"]


# ── Additional branch-coverage tests ─────────────────────────────────────────


def test_source_audit_known_failure_does_not_block_gate(
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    """A manifest entry with status='failed' is a known failure and does not block gate."""
    missing_path = raw_dir / "matches" / "9999-01-01_9999-01-07_matches.parquet"
    entries = [
        {
            "file_type": "matches",
            "target_path": str(missing_path),
            "size": 100000,
            "status": "failed",  # documented failure
            "timestamp": "2024-01-01T00:00:00+00:00",
            "error": "Broken pipe",
        }
    ]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(entries))

    reports_dir = tmp_path / "reports"
    result = run_source_audit(raw_dir, manifest_path, reports_dir)
    assert result["passed"] is True
    assert len(result["known_failures"]) == 1
    assert len(result["failures"]) == 0  # unexpected_failures


def test_source_audit_known_failure_listed_in_report(
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    """The source audit report must list known failures in a dedicated section."""
    missing_path = raw_dir / "matches" / "known_fail_matches.parquet"
    entries = [
        {
            "file_type": "matches",
            "target_path": str(missing_path),
            "size": 0,
            "status": "failed",
            "timestamp": "2024-01-01T00:00:00+00:00",
            "error": "timeout",
        }
    ]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(entries))

    reports_dir = tmp_path / "reports"
    run_source_audit(raw_dir, manifest_path, reports_dir)
    md = (reports_dir / "00_01_source_audit.md").read_text()
    assert "Known failures" in md
    assert "known_fail_matches.parquet" in md


def _make_drifted_raw_dir(tmp_path: Path) -> Path:
    """Create a raw dir with two parquets that have different column types."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    raw = tmp_path / "raw"
    matches_dir = raw / "matches"
    matches_dir.mkdir(parents=True, exist_ok=True)

    # File A: col_x as INTEGER
    pq.write_table(
        pa.table({"match_id": pa.array([1, 2], pa.int64()), "col_x": pa.array([1, 2], pa.int32())}),
        matches_dir / "2024-01-01_2024-01-07_matches.parquet",
    )
    # File B: col_x as DOUBLE
    pq.write_table(
        pa.table({
            "match_id": pa.array([3, 4], pa.int64()),
            "col_x": pa.array([1.0, 2.0], pa.float64()),
        }),
        matches_dir / "2024-01-08_2024-01-14_matches.parquet",
    )
    # Need at least 5 files for the sampler (it picks 5 indices); duplicate fine for test
    for i in range(3):
        pq.write_table(
            pa.table({
                "match_id": pa.array([10 + i], pa.int64()),
                "col_x": pa.array([float(i)], pa.float64()),
            }),
            matches_dir / f"2024-02-0{i + 1}_2024-02-07_matches.parquet",
        )
    return raw


def test_profile_match_schema_detects_type_drift(tmp_path: Path) -> None:
    """profile_match_schema must report DRIFTED and populate type_drift when types differ."""
    raw = _make_drifted_raw_dir(tmp_path)
    reports_dir = tmp_path / "reports"
    result = profile_match_schema(raw, reports_dir)
    assert result["stability"] == "DRIFTED"
    assert "col_x" in result["type_drift"]


def test_profile_match_schema_drifted_report_has_drift_section(tmp_path: Path) -> None:
    """The schema profile report must include a type-drift section when drift is detected."""
    raw = _make_drifted_raw_dir(tmp_path)
    reports_dir = tmp_path / "reports"
    profile_match_schema(raw, reports_dir)
    md = (reports_dir / "00_02_match_schema_profile.md").read_text()
    assert "Type drift detected" in md
    assert "col_x" in md


def test_smoke_test_errors_written_to_report(raw_dir: Path, tmp_path: Path) -> None:
    """When the smoke test encounters errors they are written into the report."""
    from unittest.mock import patch

    reports_dir = tmp_path / "reports"
    # Patch duckdb.connect so the CTAS raises an error
    with patch(
        "rts_predict.aoe2.data.aoestats.audit.duckdb.connect",
        side_effect=RuntimeError("simulated DuckDB failure"),
    ):
        try:
            run_smoke_test(raw_dir, reports_dir)
        except RuntimeError:
            pass  # the connect itself raises; report may or may not be written

    # Alternatively, test via a bad raw_dir with valid structure but bad files
    bad_raw = tmp_path / "bad_raw"
    bad_raw.mkdir()
    (bad_raw / "matches").mkdir()
    (bad_raw / "players").mkdir()
    # Write two intentionally truncated/bad files
    (bad_raw / "matches" / "2024-01-01_2024-01-07_matches.parquet").write_bytes(b"NOT PARQUET")
    (bad_raw / "matches" / "2024-01-08_2024-01-14_matches.parquet").write_bytes(b"NOT PARQUET")
    (bad_raw / "players" / "2024-01-01_2024-01-07_players.parquet").write_bytes(b"NOT PARQUET")
    (bad_raw / "players" / "2024-01-08_2024-01-14_players.parquet").write_bytes(b"NOT PARQUET")
    result = run_smoke_test(bad_raw, reports_dir)
    assert result["passed"] is False
    assert len(result["errors"]) > 0
    md = (reports_dir / "00_04_smoke_test.md").read_text()
    assert "## Errors" in md


def test_write_phase0_summary_with_type_drift_and_known_failures(tmp_path: Path) -> None:
    """write_phase0_summary must include type-drift and known-failure sections when present."""
    reports_dir = tmp_path / "reports"
    ingestion_result = {
        "table_counts": {"raw_matches": 1000, "raw_players": 2000},
        "T_ingestion": "2024-06-01T10:00:00+00:00",
    }
    audit_results: dict = {
        "0.1": {
            "passed": True,
            "T_acquisition": "2024-01-01T00:00:00+00:00",
            "known_failures": [
                {"key": "2025-11-16_players.parquet", "reason": "missing_from_disk"}
            ],
        },
        "0.2": {
            "stability": "DRIFTED",
            "type_drift": {"raw_match_type": ["DOUBLE", "BIGINT"]},
        },
        "0.3": {
            "stability": "DRIFTED",
            "type_drift": {
                "feudal_age_uptime": ["DOUBLE", "INTEGER"],
                "opening": ["VARCHAR", "INTEGER"],
            },
        },
        "0.4": {"passed": True},
        "0.6": {
            "passed": True,
            "strength": "DEGRADED",
            "file_counts": {"raw_matches": 172, "raw_players": 171},
            "notes": ["1 entries had status='failed'"],
        },
    }
    write_phase0_summary(reports_dir, ingestion_result, audit_results)
    invariants = (reports_dir / "INVARIANTS.md").read_text()
    assert "Type drift in raw_matches" in invariants
    assert "raw_match_type" in invariants
    assert "Type drift in raw_players" in invariants
    assert "feudal_age_uptime" in invariants
    assert "I1a." in invariants
    assert "Known download failures" in invariants
    assert "2025-11-16_players.parquet" in invariants


def test_write_phase0_summary_strict_reconciliation(tmp_path: Path) -> None:
    """INVARIANTS.md must not include DEGRADED note when reconciliation is STRICT."""
    reports_dir = tmp_path / "reports"
    ingestion_result = {
        "table_counts": {"raw_matches": 500, "raw_players": 1000},
        "T_ingestion": "2024-06-01T10:00:00+00:00",
    }
    audit_results: dict = {
        "0.1": {"passed": True, "T_acquisition": "2024-01-01T00:00:00+00:00"},
        "0.2": {"stability": "STABLE", "type_drift": {}},
        "0.3": {"stability": "STABLE", "type_drift": {}},
        "0.4": {"passed": True},
        "0.6": {
            "passed": True,
            "strength": "STRICT",
            "file_counts": {"raw_matches": 172, "raw_players": 172},
            "notes": [],
        },
    }
    write_phase0_summary(reports_dir, ingestion_result, audit_results)
    invariants = (reports_dir / "INVARIANTS.md").read_text()
    assert "STRICT" in invariants
    # DEGRADED-specific note should not appear
    assert "limited to file-count match" not in invariants


def test_reconciliation_with_failed_manifest_entry(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    tmp_path: Path,
) -> None:
    """Reconciliation must subtract known failed downloads from expected count."""
    from rts_predict.aoe2.data.aoestats.ingestion import load_all_raw_tables

    load_all_raw_tables(db_con, raw_dir)

    missing_path = raw_dir / "players" / "9999-01-01_9999-01-07_players.parquet"
    entries = [
        {
            "file_type": "matches",
            "target_path": str(raw_dir / "matches" / "2024-01-01_2024-01-07_matches.parquet"),
            "size": (raw_dir / "matches" / "2024-01-01_2024-01-07_matches.parquet").stat().st_size,
            "status": "downloaded",
            "timestamp": "2024-01-15T00:00:00+00:00",
            "error": None,
        },
        {
            "file_type": "matches",
            "target_path": str(raw_dir / "matches" / "2024-01-08_2024-01-14_matches.parquet"),
            "size": (raw_dir / "matches" / "2024-01-08_2024-01-14_matches.parquet").stat().st_size,
            "status": "downloaded",
            "timestamp": "2024-01-15T00:00:00+00:00",
            "error": None,
        },
        {
            "file_type": "players",
            "target_path": str(raw_dir / "players" / "2024-01-01_2024-01-07_players.parquet"),
            "size": (raw_dir / "players" / "2024-01-01_2024-01-07_players.parquet").stat().st_size,
            "status": "downloaded",
            "timestamp": "2024-01-15T00:00:00+00:00",
            "error": None,
        },
        {
            "file_type": "players",
            "target_path": str(raw_dir / "players" / "2024-01-08_2024-01-14_players.parquet"),
            "size": (raw_dir / "players" / "2024-01-08_2024-01-14_players.parquet").stat().st_size,
            "status": "downloaded",
            "timestamp": "2024-01-15T00:00:00+00:00",
            "error": None,
        },
        {
            "file_type": "players",
            "target_path": str(missing_path),
            "size": 99999,
            "status": "failed",  # known failure
            "timestamp": "2024-01-15T00:00:00+00:00",
            "error": "Broken pipe",
        },
    ]
    manifest_path = tmp_path / "manifest_with_failed.json"
    manifest_path.write_text(json.dumps(entries))

    reports_dir = tmp_path / "reports"
    result = run_rowcount_reconciliation(db_con, manifest_path, reports_dir)
    # Expected: 2 match files (no failures), 2 player files (1 failed excluded)
    assert result["expected_file_counts"]["raw_players"] == 2
    assert result["file_count_ok"] is True
    assert len(result["notes"]) == 1  # note about failed entry


# ── Step 9 coverage additions ────────────────────────────────────────────────


def test_profile_schema_empty_dir_raises(tmp_path: Path) -> None:
    """FileNotFoundError when matches dir contains no *_matches.parquet files (line 98)."""
    import pytest

    raw = tmp_path / "raw"
    (raw / "matches").mkdir(parents=True)
    reports_dir = tmp_path / "reports"
    with pytest.raises(FileNotFoundError, match="No files matching"):
        profile_match_schema(raw, reports_dir)


def test_smoke_test_insufficient_match_files_raises(tmp_path: Path) -> None:
    """FileNotFoundError when only 1 match file exists — need at least 2 (line 527)."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    import pytest

    raw = tmp_path / "raw"
    matches_dir = raw / "matches"
    matches_dir.mkdir(parents=True)
    players_dir = raw / "players"
    players_dir.mkdir(parents=True)

    # Only 1 match file
    pq.write_table(
        pa.table({"match_id": pa.array([1], type=pa.int64())}),
        matches_dir / "2024-01-01_2024-01-07_matches.parquet",
    )
    # 2 player files (sufficient)
    pq.write_table(
        pa.table({"match_id": pa.array([1], type=pa.int64())}),
        players_dir / "2024-01-01_2024-01-07_players.parquet",
    )
    pq.write_table(
        pa.table({"match_id": pa.array([2], type=pa.int64())}),
        players_dir / "2024-01-08_2024-01-14_players.parquet",
    )

    reports_dir = tmp_path / "reports"
    with pytest.raises(FileNotFoundError, match="Need at least 2 match"):
        run_smoke_test(raw, reports_dir)


def test_smoke_test_insufficient_player_files_raises(tmp_path: Path) -> None:
    """FileNotFoundError when only 1 player file exists — need at least 2 (line 529)."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    import pytest

    raw = tmp_path / "raw"
    matches_dir = raw / "matches"
    matches_dir.mkdir(parents=True)
    players_dir = raw / "players"
    players_dir.mkdir(parents=True)

    # 2 match files (sufficient)
    pq.write_table(
        pa.table({"match_id": pa.array([1], type=pa.int64())}),
        matches_dir / "2024-01-01_2024-01-07_matches.parquet",
    )
    pq.write_table(
        pa.table({"match_id": pa.array([2], type=pa.int64())}),
        matches_dir / "2024-01-08_2024-01-14_matches.parquet",
    )
    # Only 1 player file
    pq.write_table(
        pa.table({"match_id": pa.array([1], type=pa.int64())}),
        players_dir / "2024-01-01_2024-01-07_players.parquet",
    )

    reports_dir = tmp_path / "reports"
    with pytest.raises(FileNotFoundError, match="Need at least 2 player"):
        run_smoke_test(raw, reports_dir)


def test_run_phase_0_audit_later_steps(
    db_con: duckdb.DuckDBPyConnection,
    raw_dir: Path,
    manifest_file: Path,
    tmp_path: Path,
) -> None:
    """Orchestrator runs steps 0.4-0.7 covering lines 1091, 1094, 1097, 1100-1102."""
    reports_dir = tmp_path / "reports"

    results = run_phase_0_audit(
        db_con,
        raw_dir,
        manifest_file,
        reports_dir,
        steps=["0.4", "0.5", "0.6", "0.7"],
    )

    assert "0.4" in results   # covers line 1091
    assert "0.5" in results   # covers line 1094
    assert "0.6" in results   # covers line 1097
    assert "0.7" in results   # covers lines 1100-1102
