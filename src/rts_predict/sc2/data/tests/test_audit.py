"""Tests for audit.py: Phase 0 ingestion audit functions.

All tests use synthetic data, in-memory DuckDB, and tmp_path fixtures.
"""
import json
from collections.abc import Generator
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from rts_predict.sc2.data.audit import (
    _REPLAY_ID_REGEX,
    run_source_audit,
    validate_map_translation_coverage,
    validate_path_a_b_join,
    validate_tournament_name_extraction,
    write_replay_id_spec,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _create_synthetic_replay_file(path: Path, has_events: bool = True) -> None:
    """Create a minimal synthetic SC2Replay JSON file."""
    data = {
        "header": {"elapsedGameLoops": 10000},
        "initData": {"gameDescription": {"mapSizeX": 200, "mapSizeY": 200}},
        "details": {"timeUTC": "2023-06-01T12:00:00"},
        "metadata": {"dataBuild": "50012", "gameVersion": "5.0.12", "mapName": "TestMap"},
        "ToonPlayerDescMap": {
            "toon-1": {
                "nickname": "Alpha",
                "playerID": 1,
                "userID": 1,
                "race": "Terr",
                "APM": 0,
                "MMR": 0,
                "SQ": 80,
                "result": "Win",
                "isInClan": False,
                "supplyCappedPercent": 5,
                "startLocX": 40,
                "startLocY": 20,
            },
            "toon-2": {
                "nickname": "Beta",
                "playerID": 2,
                "userID": 2,
                "race": "Prot",
                "APM": 0,
                "MMR": 0,
                "SQ": 75,
                "result": "Loss",
                "isInClan": False,
                "supplyCappedPercent": 8,
                "startLocX": 130,
                "startLocY": 150,
            },
        },
    }
    if has_events:
        data["trackerEvents"] = [{"evtTypeName": "PlayerStats", "loop": 100}]
        data["gameEvents"] = [{"evtTypeName": "CameraUpdate", "loop": 50}]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _build_synthetic_replays_dir(
    tmp_path: Path, *, use_data_subdir: bool = False,
) -> Path:
    """Create a synthetic replays directory with tournament structure.

    Args:
        use_data_subdir: If True, use ``{tourn}/data/`` (matches
            ``audit_raw_data_availability`` glob).  If False, use
            ``{tourn}/{tourn}_data/`` (matches ``split_part(filename, '/', -3)``
            for tournament_dir extraction).
    """
    replays_dir = tmp_path / "replays"
    tournaments = ["2023_GSL_S1", "2023_IEM_Katowice", "2024_ESL_Pro"]
    hex_ids = [
        "aabbccdd11223344556677889900aa00",
        "aabbccdd11223344556677889900aa01",
        "aabbccdd11223344556677889900aa02",
    ]

    for i, tourn in enumerate(tournaments):
        subdir = "data" if use_data_subdir else f"{tourn}_data"
        for j, hid in enumerate(hex_ids):
            has_events = not (i == 0 and j == 2)  # One stripped file
            _create_synthetic_replay_file(
                replays_dir / tourn / subdir / f"{hid}.SC2Replay.json",
                has_events=has_events,
            )

    return replays_dir


# ── TestRunSourceAudit ───────────────────────────────────────────────────────


class TestRunSourceAudit:
    """Test run_source_audit (Step 0.1)."""

    def test_writes_json_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Scenario: Creates JSON report with correct keys."""
        replays_dir = _build_synthetic_replays_dir(tmp_path, use_data_subdir=True)
        monkeypatch.setattr("rts_predict.sc2.data.ingestion.REPLAYS_SOURCE_DIR", replays_dir)

        output = tmp_path / "audit.json"
        result = run_source_audit(replays_dir=replays_dir, output_path=output)

        assert output.exists()
        data = json.loads(output.read_text())
        assert "total" in data
        assert "has_tracker" in data
        assert "stripped" in data
        assert result["total"] == 9  # 3 tournaments x 3 files


# ── TestValidateTournamentNameExtraction ─────────────────────────────────────


class TestValidateTournamentNameExtraction:
    """Test validate_tournament_name_extraction (Step 0.2)."""

    def test_correct_extraction(self, tmp_path: Path) -> None:
        """Scenario: All tournament name extractions are correct."""
        replays_dir = _build_synthetic_replays_dir(tmp_path)
        output = tmp_path / "validation.txt"

        results = validate_tournament_name_extraction(
            replays_dir=replays_dir,
            n_tournaments=3,
            n_files_per_tournament=3,
            output_path=output,
        )

        assert output.exists()
        assert all(r["match"] for r in results)

    def test_deterministic_with_seed(self, tmp_path: Path) -> None:
        """Scenario: Two calls produce identical samples."""
        replays_dir = _build_synthetic_replays_dir(tmp_path)

        results1 = validate_tournament_name_extraction(
            replays_dir=replays_dir,
            output_path=tmp_path / "v1.txt",
        )
        results2 = validate_tournament_name_extraction(
            replays_dir=replays_dir,
            output_path=tmp_path / "v2.txt",
        )

        assert [r["file_path"] for r in results1] == [r["file_path"] for r in results2]


# ── TestWriteReplayIdSpec ────────────────────────────────────────────────────


class TestWriteReplayIdSpec:
    """Test write_replay_id_spec (Step 0.3)."""

    def test_path_a_b_produce_same_id(self, tmp_path: Path) -> None:
        """Scenario: Absolute and relative paths yield the same replay_id."""
        import re

        replays_dir = _build_synthetic_replays_dir(tmp_path)
        files = list(replays_dir.rglob("*.SC2Replay.json"))

        for f in files:
            abs_match = re.search(_REPLAY_ID_REGEX, str(f))
            rel_match = re.search(_REPLAY_ID_REGEX, str(f.relative_to(replays_dir)))
            assert abs_match and rel_match
            assert abs_match.group(1) == rel_match.group(1)

    def test_writes_markdown_report(self, tmp_path: Path) -> None:
        """Scenario: Output file exists and contains spec sections."""
        replays_dir = _build_synthetic_replays_dir(tmp_path)
        output = tmp_path / "spec.md"

        md = write_replay_id_spec(replays_dir=replays_dir, output_path=output)

        assert output.exists()
        assert "replay_id" in md
        assert "regexp_extract" in md
        assert "Worked Examples" in md


# ── TestRunPathASmokeTest ────────────────────────────────────────────────────


class TestRunPathASmokeTest:
    """Test run_path_a_smoke_test (Step 0.4).

    Uses a synthetic tournament directory in tmp_path.
    """

    def test_smoke_test_with_synthetic_data(self, tmp_path: Path) -> None:
        """Scenario: Smoke test runs on a synthetic tournament directory."""
        from rts_predict.sc2.data.audit import run_path_a_smoke_test

        replays_dir = _build_synthetic_replays_dir(tmp_path)
        tourn = "2023_GSL_S1"
        output = tmp_path / "smoke.md"

        result = run_path_a_smoke_test(
            tournament_name=tourn,
            replays_dir=replays_dir,
            output_path=output,
        )

        assert output.exists()
        assert result["tournament"] == tourn
        assert result["row_count"] == result["file_count"]
        assert result["row_count"] == 3


# ── TestValidatePathAbJoin ───────────────────────────────────────────────────


class TestValidatePathAbJoin:
    """Test validate_path_a_b_join (Step 0.8)."""

    @pytest.fixture()
    def _join_con(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """DuckDB with synthetic raw and tracker_events_raw tables."""
        con = duckdb.connect(":memory:")

        # Raw table with 3 replay IDs
        raw_df = pd.DataFrame({  # noqa: F841
            "filename": [
                f"T/T_data/{rid}.SC2Replay.json"
                for rid in [
                    "aabbccdd11223344556677889900aa00",
                    "aabbccdd11223344556677889900aa01",
                    "aabbccdd11223344556677889900aa02",
                ]
            ]
        })
        con.execute("CREATE TABLE raw AS SELECT * FROM raw_df")

        # Tracker with matching IDs
        tracker_df = pd.DataFrame({  # noqa: F841
            "match_id": [
                f"T/T_data/{rid}.SC2Replay.json"
                for rid in [
                    "aabbccdd11223344556677889900aa00",
                    "aabbccdd11223344556677889900aa01",
                    "aabbccdd11223344556677889900aa02",
                ]
            ]
        })
        con.execute("CREATE TABLE tracker_events_raw AS SELECT * FROM tracker_df")

        yield con
        con.close()

    def test_clean_join(self, _join_con: duckdb.DuckDBPyConnection, tmp_path: Path) -> None:
        """Scenario: All replay_ids match between raw and tracker → join_clean=True."""
        result = validate_path_a_b_join(_join_con, output_path=tmp_path / "join.md")

        assert result["join_clean"] is True
        assert result["orphans_in_tracker_not_raw"] == 0

    def test_orphan_detection(
        self, _join_con: duckdb.DuckDBPyConnection, tmp_path: Path
    ) -> None:
        """Scenario: Extra replay_id in tracker → reported as orphan."""
        orphan_df = pd.DataFrame({  # noqa: F841
            "match_id": ["T/T_data/deadbeef00112233445566778899aabb.SC2Replay.json"]
        })
        _join_con.execute("INSERT INTO tracker_events_raw SELECT * FROM orphan_df")

        result = validate_path_a_b_join(_join_con, output_path=tmp_path / "join.md")

        assert result["join_clean"] is False
        assert result["orphans_in_tracker_not_raw"] == 1


# ── TestValidateMapTranslationCoverage ───────────────────────────────────────


class TestValidateMapTranslationCoverage:
    """Test validate_map_translation_coverage (Step 0.9)."""

    @pytest.fixture()
    def _map_con(self, tmp_path: Path) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """DuckDB with raw table containing map names."""
        con = duckdb.connect(":memory:")

        raw_df = pd.DataFrame({  # noqa: F841
            "filename": ["a.json", "b.json", "c.json"],
            "metadata": [
                json.dumps({"mapName": "MapA"}),
                json.dumps({"mapName": "MapB"}),
                json.dumps({"mapName": "MapC"}),
            ],
        })
        con.execute("CREATE TABLE raw AS SELECT * FROM raw_df")
        con.execute("""
            CREATE OR REPLACE TABLE raw AS
            SELECT filename, metadata::JSON AS metadata FROM raw
        """)

        yield con
        con.close()

    def test_full_coverage(
        self, _map_con: duckdb.DuckDBPyConnection, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: All maps translated → untranslated_count=0."""
        # Provide translations for all maps
        monkeypatch.setattr("rts_predict.sc2.data.ingestion.REPLAYS_SOURCE_DIR", tmp_path)
        map_file = tmp_path / "map_foreign_to_english_mapping.json"
        map_file.write_text(json.dumps({
            "MapA": "Map A English",
            "MapB": "Map B English",
            "MapC": "Map C English",
        }))

        result = validate_map_translation_coverage(
            _map_con, output_path=tmp_path / "coverage.csv"
        )

        assert result["untranslated_count"] == 0

    def test_partial_coverage(
        self, _map_con: duckdb.DuckDBPyConnection, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: Some maps untranslated → correct count and list."""
        monkeypatch.setattr("rts_predict.sc2.data.ingestion.REPLAYS_SOURCE_DIR", tmp_path)
        map_file = tmp_path / "map_foreign_to_english_mapping.json"
        map_file.write_text(json.dumps({"MapA": "Map A English"}))

        result = validate_map_translation_coverage(
            _map_con, output_path=tmp_path / "coverage.csv"
        )

        assert result["untranslated_count"] == 2
        assert set(result["untranslated_names"]) == {"MapB", "MapC"}
