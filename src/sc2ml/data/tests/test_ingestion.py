"""Tests for in-game event extraction pipeline (Path B).

Uses the sample replay file (sOs vs ByuN) shipped in samples/raw/ to verify:
- Raw event extraction produces correct counts and structure
- Parquet round-trip preserves data
- DuckDB loading creates expected tables and views
- PlayerStats view returns typed columns for all 39 fields
- slim_down_sc2_with_manifest strips event keys correctly
- move_data_to_duck_db loads JSON replays into DuckDB
"""
import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import duckdb
import pytest

from sc2ml.data.ingestion import (
    PLAYER_STATS_FIELD_MAP,
    _build_game_event_rows,
    _build_metadata_rows,
    _build_tracker_rows,
    _collect_pending_files,
    _load_manifest,
    _save_manifest,
    audit_raw_data_availability,
    extract_raw_events_from_file,
    load_in_game_data_to_duckdb,
    load_map_translations,
    move_data_to_duck_db,
    run_in_game_extraction,
    save_raw_events_to_parquet,
    slim_down_sc2_with_manifest,
)


class TestExtractRawEvents:
    """Test extract_raw_events_from_file with the sample replay."""

    def test_returns_dict_for_valid_file(self, sample_replay_path: Path) -> None:
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None
        assert isinstance(result, dict)

    def test_returns_none_for_stripped_file(self, tmp_path: Path) -> None:
        stripped = tmp_path / "stripped.SC2Replay.json"
        stripped.write_text(json.dumps({"header": {}, "ToonPlayerDescMap": {}}))
        result = extract_raw_events_from_file(stripped)
        assert result is None

    def test_tracker_events_count(self, sample_replay_path: Path) -> None:
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None
        assert len(result["tracker_events"]) == 528

    def test_game_events_count(self, sample_replay_path: Path) -> None:
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None
        assert len(result["game_events"]) == 9038

    def test_player_map_has_two_players(self, sample_replay_path: Path) -> None:
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None
        pmap = result["player_map"]
        assert len(pmap) == 2

    def test_player_map_userid_to_playerid(self, sample_replay_path: Path) -> None:
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None
        pmap = result["player_map"]
        # userId=2 → playerID=1 (ByuN), userId=5 → playerID=2 (sOs)
        assert pmap[2]["playerID"] == 1
        assert pmap[2]["nickname"] == "ByuN"
        assert pmap[5]["playerID"] == 2
        assert pmap[5]["nickname"] == "sOs"

    def test_total_game_loops(self, sample_replay_path: Path) -> None:
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None
        assert result["total_game_loops"] > 0

    def test_match_id_is_string(self, sample_replay_path: Path) -> None:
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None
        assert result["match_id"].endswith(".SC2Replay.json")
        assert isinstance(result["match_id"], str)


class TestBuildRows:
    """Test the row-building helpers."""

    @pytest.fixture()
    def extracted(self, sample_replay_path: Path) -> dict:
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None
        return result

    def test_tracker_rows_count(self, extracted: dict) -> None:
        rows = _build_tracker_rows(extracted["match_id"], extracted["tracker_events"])
        assert len(rows) == 528

    def test_tracker_row_keys(self, extracted: dict) -> None:
        rows = _build_tracker_rows(extracted["match_id"], extracted["tracker_events"])
        expected_keys = {"match_id", "event_type", "game_loop", "player_id", "event_data"}
        assert set(rows[0].keys()) == expected_keys

    def test_game_event_rows_count(self, extracted: dict) -> None:
        rows = _build_game_event_rows(
            extracted["match_id"], extracted["game_events"], extracted["player_map"]
        )
        assert len(rows) == 9038

    def test_game_event_row_has_player_id(self, extracted: dict) -> None:
        rows = _build_game_event_rows(
            extracted["match_id"], extracted["game_events"], extracted["player_map"]
        )
        # At least some rows should have mapped player_id (1 or 2)
        mapped = [r for r in rows if r["player_id"] in (1, 2)]
        assert len(mapped) > 0

    def test_metadata_rows(self, extracted: dict) -> None:
        rows = _build_metadata_rows(
            extracted["match_id"], extracted["player_map"], extracted["total_game_loops"]
        )
        assert len(rows) == 2
        player_ids = {r["player_id"] for r in rows}
        assert player_ids == {1, 2}


class TestParquetRoundTrip:
    """Test writing and reading Parquet files."""

    def test_write_and_read_parquet(
        self, sample_replay_path: Path, tmp_path: Path
    ) -> None:
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None

        save_raw_events_to_parquet([result], tmp_path, batch_number=0)

        # Verify files exist
        tracker_files = list(tmp_path.glob("tracker_events_batch_*.parquet"))
        game_files = list(tmp_path.glob("game_events_batch_*.parquet"))
        meta_files = list(tmp_path.glob("match_metadata_batch_*.parquet"))
        assert len(tracker_files) == 1
        assert len(game_files) == 1
        assert len(meta_files) == 1

        # Verify row counts via DuckDB
        con = duckdb.connect(":memory:")
        tracker_count = con.execute(
            f"SELECT count(*) FROM read_parquet('{tracker_files[0]}')"
        ).fetchone()[0]
        assert tracker_count == 528

        game_count = con.execute(
            f"SELECT count(*) FROM read_parquet('{game_files[0]}')"
        ).fetchone()[0]
        assert game_count == 9038
        con.close()


class TestDuckDBLoading:
    """Test loading Parquet files into DuckDB tables and views."""

    @pytest.fixture()
    def loaded_con(
        self, sample_replay_path: Path, tmp_path: Path
    ) -> duckdb.DuckDBPyConnection:
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None
        save_raw_events_to_parquet([result], tmp_path, batch_number=0)

        con = duckdb.connect(":memory:")
        load_in_game_data_to_duckdb(con, tmp_path, should_drop=True)
        yield con
        con.close()

    def test_tracker_events_raw_table_exists(
        self, loaded_con: duckdb.DuckDBPyConnection
    ) -> None:
        tables = loaded_con.execute(
            "SELECT table_name FROM information_schema.tables"
        ).fetchall()
        table_names = {t[0] for t in tables}
        assert "tracker_events_raw" in table_names

    def test_game_events_raw_table_exists(
        self, loaded_con: duckdb.DuckDBPyConnection
    ) -> None:
        tables = loaded_con.execute(
            "SELECT table_name FROM information_schema.tables"
        ).fetchall()
        table_names = {t[0] for t in tables}
        assert "game_events_raw" in table_names

    def test_match_player_map_table_exists(
        self, loaded_con: duckdb.DuckDBPyConnection
    ) -> None:
        tables = loaded_con.execute(
            "SELECT table_name FROM information_schema.tables"
        ).fetchall()
        table_names = {t[0] for t in tables}
        assert "match_player_map" in table_names

    def test_player_stats_view_exists(
        self, loaded_con: duckdb.DuckDBPyConnection
    ) -> None:
        # Views show up in information_schema.tables with type VIEW
        result = loaded_con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_name = 'player_stats'"
        ).fetchone()[0]
        assert result > 0

    def test_player_stats_row_count(
        self, loaded_con: duckdb.DuckDBPyConnection
    ) -> None:
        # 48 unique game loops × 2 players, but player 1 has one extra snapshot
        # at the first loop → 97 total PlayerStats events
        count = loaded_con.execute("SELECT count(*) FROM player_stats").fetchone()[0]
        assert count == 97

    def test_player_stats_has_all_39_fields(
        self, loaded_con: duckdb.DuckDBPyConnection
    ) -> None:
        columns = loaded_con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'player_stats' ORDER BY ordinal_position"
        ).fetchall()
        col_names = {c[0] for c in columns}

        # 3 key columns + 39 stat columns
        assert "match_id" in col_names
        assert "game_loop" in col_names
        assert "player_id" in col_names
        for snake_name in PLAYER_STATS_FIELD_MAP.values():
            assert snake_name in col_names, f"Missing column: {snake_name}"

    def test_player_stats_values_are_numeric(
        self, loaded_con: duckdb.DuckDBPyConnection
    ) -> None:
        row = loaded_con.execute(
            "SELECT minerals_current, vespene_current, workers_active_count "
            "FROM player_stats LIMIT 1"
        ).fetchone()
        assert row is not None
        for val in row:
            assert isinstance(val, (int, float))

    def test_match_player_map_has_two_players(
        self, loaded_con: duckdb.DuckDBPyConnection
    ) -> None:
        count = loaded_con.execute(
            "SELECT count(DISTINCT player_id) FROM match_player_map"
        ).fetchone()[0]
        assert count == 2


class TestPlayerStatsFieldMap:
    """Verify the PLAYER_STATS_FIELD_MAP constant."""

    def test_has_39_fields(self) -> None:
        assert len(PLAYER_STATS_FIELD_MAP) == 39

    def test_all_values_are_snake_case(self) -> None:
        for src, dst in PLAYER_STATS_FIELD_MAP.items():
            assert dst == dst.lower(), f"{dst} is not lowercase"
            assert " " not in dst, f"{dst} contains spaces"

    def test_source_keys_match_sample(self, sample_replay_path: Path) -> None:
        """Verify field map keys match actual PlayerStats event data."""
        with open(sample_replay_path) as f:
            data = json.load(f)

        # Find first PlayerStats event
        for evt in data["trackerEvents"]:
            if evt.get("evtTypeName") == "PlayerStats":
                actual_keys = set(evt["stats"].keys())
                mapped_keys = set(PLAYER_STATS_FIELD_MAP.keys())
                assert mapped_keys == actual_keys, (
                    f"Mismatch: missing={actual_keys - mapped_keys}, "
                    f"extra={mapped_keys - actual_keys}"
                )
                return

        pytest.fail("No PlayerStats event found in sample replay")


class TestManifestHelpers:
    """Test _load_manifest, _save_manifest, and _collect_pending_files."""

    def test_load_manifest_empty_path(self, tmp_path: Path) -> None:
        manifest = _load_manifest(tmp_path / "nonexistent.json")
        assert manifest == {}

    def test_load_manifest_valid(self, tmp_path: Path) -> None:
        path = tmp_path / "manifest.json"
        path.write_text(json.dumps({"file_a": True, "file_b": False}))
        manifest = _load_manifest(path)
        assert manifest == {"file_a": True, "file_b": False}

    def test_load_manifest_corrupted(self, tmp_path: Path) -> None:
        path = tmp_path / "manifest.json"
        path.write_text("not valid json{{{")
        manifest = _load_manifest(path)
        assert manifest == {}

    def test_save_manifest_roundtrip(self, tmp_path: Path) -> None:
        path = tmp_path / "manifest.json"
        data = {"file_x": True}
        _save_manifest(data, path)
        loaded = json.loads(path.read_text())
        assert loaded == data


class TestSlimDownSc2WithManifest:
    """Test slim_down_sc2_with_manifest with synthetic replay files."""

    def _create_replay_dir(self, tmp_path: Path) -> Path:
        """Create a minimal replay directory structure with 2 files."""
        replay_dir = tmp_path / "replays" / "tournament" / "data"
        replay_dir.mkdir(parents=True)
        for i in range(2):
            replay = {
                "header": {"elapsedGameLoops": 5000},
                "ToonPlayerDescMap": {},
                "trackerEvents": [{"evtTypeName": "test"}] * 100,
                "gameEvents": [{"evtTypeName": "test"}] * 200,
                "messageEvents": [{"text": "glhf"}],
            }
            (replay_dir / f"match_{i}.SC2Replay.json").write_text(json.dumps(replay))
        return tmp_path / "replays"

    @patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR")
    @patch("sc2ml.data.ingestion.MANIFEST_PATH")
    def test_dry_run_does_not_modify_files(
        self, mock_manifest: Path, mock_source: Path, tmp_path: Path
    ) -> None:
        source = self._create_replay_dir(tmp_path)
        mock_source.__class__ = type(source)
        mock_manifest.__class__ = type(tmp_path / "manifest.json")

        # Patch the actual Path values
        with patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR", source), \
             patch("sc2ml.data.ingestion.MANIFEST_PATH", tmp_path / "manifest.json"):
            slim_down_sc2_with_manifest(dry_run=True)

        # Files should still contain all keys
        data_dir = source / "tournament" / "data"
        for f in data_dir.glob("*.SC2Replay.json"):
            data = json.loads(f.read_text())
            assert "trackerEvents" in data
            assert "gameEvents" in data
            assert "messageEvents" in data

    @patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR")
    @patch("sc2ml.data.ingestion.MANIFEST_PATH")
    def test_actual_run_strips_events(
        self, mock_manifest: Path, mock_source: Path, tmp_path: Path
    ) -> None:
        source = self._create_replay_dir(tmp_path)

        with patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR", source), \
             patch("sc2ml.data.ingestion.MANIFEST_PATH", tmp_path / "manifest.json"):
            slim_down_sc2_with_manifest(dry_run=False)

        data_dir = source / "tournament" / "data"
        for f in data_dir.glob("*.SC2Replay.json"):
            data = json.loads(f.read_text())
            assert "trackerEvents" not in data
            assert "gameEvents" not in data
            assert "messageEvents" not in data
            assert "header" in data
            assert "ToonPlayerDescMap" in data

    @patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR")
    @patch("sc2ml.data.ingestion.MANIFEST_PATH")
    def test_manifest_tracks_processed_files(
        self, mock_manifest: Path, mock_source: Path, tmp_path: Path
    ) -> None:
        source = self._create_replay_dir(tmp_path)
        manifest_path = tmp_path / "manifest.json"

        with patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR", source), \
             patch("sc2ml.data.ingestion.MANIFEST_PATH", manifest_path):
            slim_down_sc2_with_manifest(dry_run=False)

        manifest = json.loads(manifest_path.read_text())
        assert len(manifest) == 2
        assert all(v is True for v in manifest.values())

    @patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR")
    @patch("sc2ml.data.ingestion.MANIFEST_PATH")
    def test_skips_already_processed_files(
        self, mock_manifest: Path, mock_source: Path, tmp_path: Path
    ) -> None:
        source = self._create_replay_dir(tmp_path)
        manifest_path = tmp_path / "manifest.json"

        with patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR", source), \
             patch("sc2ml.data.ingestion.MANIFEST_PATH", manifest_path):
            slim_down_sc2_with_manifest(dry_run=False)
            # Run again — should skip all files
            slim_down_sc2_with_manifest(dry_run=False)

        manifest = json.loads(manifest_path.read_text())
        assert len(manifest) == 2


class TestMoveDataToDuckDb:
    """Test move_data_to_duck_db with synthetic replay files."""

    def _create_replay_dir(self, tmp_path: Path) -> Path:
        """Create minimal stripped replay files for DuckDB ingestion."""
        replay_dir = tmp_path / "replays" / "tournament" / "data"
        replay_dir.mkdir(parents=True)

        for i in range(3):
            replay = {
                "header": {"elapsedGameLoops": 5000 + i * 100},
                "initData": {"gameDescription": {"mapSizeX": 200, "mapSizeY": 200}},
                "details": {"timeUTC": f"2023-0{i + 1}-01T12:00:00"},
                "metadata": {"dataBuild": "5.0.12", "mapName": "Altitude LE"},
                "ToonPlayerDescMap": {
                    "toon-1": {
                        "nickname": f"Player{i}A",
                        "playerID": 1,
                        "result": "Win",
                    },
                    "toon-2": {
                        "nickname": f"Player{i}B",
                        "playerID": 2,
                        "result": "Loss",
                    },
                },
            }
            (replay_dir / f"match_{i}.SC2Replay.json").write_text(json.dumps(replay))
        return tmp_path / "replays"

    @patch("sc2ml.data.ingestion.DUCKDB_TEMP_DIR")
    @patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR")
    def test_loads_replays_into_raw_table(
        self, mock_source: Path, mock_temp: Path, tmp_path: Path
    ) -> None:
        source = self._create_replay_dir(tmp_path)
        temp_dir = tmp_path / "duckdb_tmp"
        temp_dir.mkdir()

        con = duckdb.connect(":memory:")
        with patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR", source), \
             patch("sc2ml.data.ingestion.DUCKDB_TEMP_DIR", temp_dir):
            move_data_to_duck_db(con, should_drop=True)

        row_count = con.execute("SELECT count(*) FROM raw").fetchone()[0]
        assert row_count == 3
        con.close()

    @patch("sc2ml.data.ingestion.DUCKDB_TEMP_DIR")
    @patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR")
    def test_raw_table_has_expected_columns(
        self, mock_source: Path, mock_temp: Path, tmp_path: Path
    ) -> None:
        source = self._create_replay_dir(tmp_path)
        temp_dir = tmp_path / "duckdb_tmp"
        temp_dir.mkdir()

        con = duckdb.connect(":memory:")
        with patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR", source), \
             patch("sc2ml.data.ingestion.DUCKDB_TEMP_DIR", temp_dir):
            move_data_to_duck_db(con, should_drop=True)

        columns = con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'raw'"
        ).fetchall()
        col_names = {c[0] for c in columns}
        expected = {"header", "initData", "details", "metadata", "ToonPlayerDescMap"}
        assert expected.issubset(col_names)
        con.close()

    @patch("sc2ml.data.ingestion.DUCKDB_TEMP_DIR")
    @patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR")
    def test_should_drop_recreates_table(
        self, mock_source: Path, mock_temp: Path, tmp_path: Path
    ) -> None:
        source = self._create_replay_dir(tmp_path)
        temp_dir = tmp_path / "duckdb_tmp"
        temp_dir.mkdir()

        con = duckdb.connect(":memory:")
        with patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR", source), \
             patch("sc2ml.data.ingestion.DUCKDB_TEMP_DIR", temp_dir):
            move_data_to_duck_db(con, should_drop=True)
            move_data_to_duck_db(con, should_drop=True)

        row_count = con.execute("SELECT count(*) FROM raw").fetchone()[0]
        assert row_count == 3  # Not doubled
        con.close()


class TestAuditRawDataAvailability:
    """Test audit_raw_data_availability with synthetic replay directories."""

    def test_empty_dir_returns_zero_counts(self, tmp_path: Path) -> None:
        source = tmp_path / "replays"
        source.mkdir()

        with patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR", source):
            counts = audit_raw_data_availability()

        assert counts["total"] == 0
        assert counts["has_tracker"] == 0
        assert counts["has_game"] == 0
        assert counts["has_both"] == 0
        assert counts["stripped"] == 0

    def test_mixed_files(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "replays" / "tournament" / "data"
        data_dir.mkdir(parents=True)

        # File with both events
        (data_dir / "both.SC2Replay.json").write_text(
            json.dumps({"trackerEvents": [{}], "gameEvents": [{}]})
        )
        # File with tracker only
        (data_dir / "tracker.SC2Replay.json").write_text(
            json.dumps({"trackerEvents": [{}]})
        )
        # Stripped file
        (data_dir / "stripped.SC2Replay.json").write_text(
            json.dumps({"header": {}})
        )

        with patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR", tmp_path / "replays"):
            counts = audit_raw_data_availability()

        assert counts["total"] == 3
        assert counts["has_both"] == 1
        assert counts["has_tracker"] == 2
        assert counts["has_game"] == 1
        assert counts["stripped"] == 1


class TestLoadMapTranslations:
    """Test load_map_translations with synthetic mapping files."""

    def test_with_translation_files(self, tmp_path: Path) -> None:
        source = tmp_path / "replays" / "tourn" / "data"
        source.mkdir(parents=True)
        mapping = {"MapKorean": "Map English LE", "AltitudeKR": "Altitude LE"}
        (source / "map_foreign_to_english_mapping.json").write_text(json.dumps(mapping))

        con = duckdb.connect(":memory:")
        with patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR", tmp_path / "replays"):
            load_map_translations(con)

        count = con.execute("SELECT count(*) FROM map_translation").fetchone()[0]
        assert count == 2
        con.close()

    def test_no_translation_files_warns(self, tmp_path: Path, caplog) -> None:
        source = tmp_path / "replays"
        source.mkdir()

        con = duckdb.connect(":memory:")
        with patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR", source), \
             caplog.at_level(logging.WARNING):
            load_map_translations(con)

        assert "No map translation dictionaries found" in caplog.text
        # Table should NOT exist
        tables = con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_name = 'map_translation'"
        ).fetchall()
        assert len(tables) == 0
        con.close()


class TestCollectPendingFiles:
    """Test _collect_pending_files with manifest filtering."""

    def test_filters_already_done(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "replays" / "tourn" / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "done.SC2Replay.json").write_text("{}")
        (data_dir / "pending.SC2Replay.json").write_text("{}")

        manifest = {"tourn/data/done.SC2Replay.json": True}

        with patch("sc2ml.data.ingestion.REPLAYS_SOURCE_DIR", tmp_path / "replays"):
            pending = _collect_pending_files(manifest)

        assert len(pending) == 1
        assert pending[0].name == "pending.SC2Replay.json"


class TestRunInGameExtraction:
    """Test run_in_game_extraction with mocked Pool."""

    @patch("sc2ml.data.ingestion.save_raw_events_to_parquet")
    @patch("sc2ml.data.ingestion._save_manifest")
    @patch("sc2ml.data.ingestion._collect_pending_files")
    @patch("sc2ml.data.ingestion._load_manifest", return_value={})
    def test_mock_pool_batches(
        self, m_load, m_collect, m_save_manifest, m_save_parquet, tmp_path: Path
    ) -> None:
        # Simulate 3 pending files that each produce a result
        fake_paths = [tmp_path / f"f{i}.json" for i in range(3)]
        m_collect.return_value = fake_paths

        fake_results = [
            {"match_id": f"m{i}", "tracker_events": [], "game_events": [], "player_map": {}}
            for i in range(3)
        ]

        mock_pool = MagicMock()
        mock_pool.__enter__ = MagicMock(return_value=mock_pool)
        mock_pool.__exit__ = MagicMock(return_value=False)
        mock_pool.imap_unordered.return_value = iter(fake_results)

        with patch("sc2ml.data.ingestion.multiprocessing.Pool", return_value=mock_pool), \
             patch("sc2ml.data.ingestion.IN_GAME_MANIFEST_PATH", tmp_path / "manifest.json"):
            run_in_game_extraction(
                parquet_dir=tmp_path / "parquet", max_workers=1, batch_size=2,
            )

        # 3 results with batch_size=2 → 2 calls to save_parquet (batch of 2, then 1)
        assert m_save_parquet.call_count == 2

    @patch("sc2ml.data.ingestion._collect_pending_files", return_value=[])
    @patch("sc2ml.data.ingestion._load_manifest", return_value={})
    def test_empty_pending_returns_early(self, m_load, m_collect, tmp_path: Path) -> None:
        with patch("sc2ml.data.ingestion.multiprocessing.Pool") as m_pool, \
             patch("sc2ml.data.ingestion.IN_GAME_MANIFEST_PATH", tmp_path / "manifest.json"):
            run_in_game_extraction(parquet_dir=tmp_path / "parquet")

        m_pool.assert_not_called()
