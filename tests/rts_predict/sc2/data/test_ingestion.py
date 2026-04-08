"""Tests for in-game event extraction pipeline (Path B).

Uses the sample replay file (sOs vs ByuN) shipped in samples/raw/ to verify:
- Raw event extraction produces correct counts and structure
- Parquet round-trip preserves data
- DuckDB loading creates expected tables and views
- PlayerStats view returns typed columns for all 39 fields
- move_data_to_duck_db loads JSON replays into DuckDB
"""
import json
import logging
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import duckdb
import pytest

from rts_predict.sc2.data.ingestion import (
    PLAYER_STATS_FIELD_MAP,
    _build_game_event_rows,
    _build_metadata_rows,
    _build_tracker_rows,
    _collect_pending_files,
    _load_manifest,
    _save_manifest,
    audit_raw_data_availability,
    extract_raw_events_from_file,
    ingest_map_alias_files,
    load_in_game_data_to_duckdb,
    move_data_to_duck_db,
    run_in_game_extraction,
    save_raw_events_to_parquet,
)


class TestExtractRawEvents:
    """Test extract_raw_events_from_file with the sample replay."""

    def test_returns_dict_for_valid_file(self, sample_replay_path: Path) -> None:
        """
        Scenario: Valid replay file produces a non-None dict result.
        Preconditions: Sample sOs vs ByuN replay with full event data.
        Assertions: Result is a non-None dict.
        """
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None
        assert isinstance(result, dict)

    def test_returns_none_for_stripped_file(self, tmp_path: Path) -> None:
        """
        Scenario: Stripped replay (no event arrays) returns None.
        Preconditions: JSON file with only header and ToonPlayerDescMap keys.
        Assertions: Result is None.
        """
        stripped = tmp_path / "stripped.SC2Replay.json"
        stripped.write_text(json.dumps({"header": {}, "ToonPlayerDescMap": {}}))
        result = extract_raw_events_from_file(stripped)
        assert result is None

    def test_tracker_events_count(self, sample_replay_path: Path) -> None:
        """
        Scenario: Tracker events extracted with correct count from sample replay.
        Preconditions: Sample sOs vs ByuN replay.
        Assertions: Exactly 528 tracker events extracted.
        """
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None
        assert len(result["tracker_events"]) == 528

    def test_game_events_count(self, sample_replay_path: Path) -> None:
        """
        Scenario: Game events extracted with correct count from sample replay.
        Preconditions: Sample sOs vs ByuN replay.
        Assertions: Exactly 9038 game events extracted.
        """
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None
        assert len(result["game_events"]) == 9038

    def test_player_map_has_two_players(self, sample_replay_path: Path) -> None:
        """
        Scenario: Player map contains exactly two entries for a 1v1 match.
        Preconditions: Sample sOs vs ByuN replay.
        Assertions: player_map has 2 entries.
        """
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None
        pmap = result["player_map"]
        assert len(pmap) == 2

    def test_player_map_userid_to_playerid(self, sample_replay_path: Path) -> None:
        """
        Scenario: Player map correctly maps userId to playerID and nickname.
        Preconditions: Sample replay with ByuN (userId=2) and sOs (userId=5).
        Assertions: userId 2 maps to playerID 1 / ByuN, userId 5 maps to playerID 2 / sOs.
        """
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None
        pmap = result["player_map"]
        # userId=2 → playerID=1 (ByuN), userId=5 → playerID=2 (sOs)
        assert pmap[2]["playerID"] == 1
        assert pmap[2]["nickname"] == "ByuN"
        assert pmap[5]["playerID"] == 2
        assert pmap[5]["nickname"] == "sOs"

    def test_total_game_loops(self, sample_replay_path: Path) -> None:
        """
        Scenario: Total game loops is a positive integer.
        Preconditions: Sample sOs vs ByuN replay.
        Assertions: total_game_loops > 0.
        """
        result = extract_raw_events_from_file(sample_replay_path)
        assert result is not None
        assert result["total_game_loops"] > 0

    def test_match_id_is_string(self, sample_replay_path: Path) -> None:
        """
        Scenario: Match ID is a string ending with the replay file extension.
        Preconditions: Sample sOs vs ByuN replay.
        Assertions: match_id is str and ends with ".SC2Replay.json".
        """
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
        """
        Scenario: Tracker row builder produces one row per tracker event.
        Preconditions: Extracted result from sample replay (528 tracker events).
        Assertions: 528 rows returned.
        """
        rows = _build_tracker_rows(extracted["match_id"], extracted["tracker_events"])
        assert len(rows) == 528

    def test_tracker_row_keys(self, extracted: dict) -> None:
        """
        Scenario: Each tracker row has the expected schema keys.
        Preconditions: Extracted result from sample replay.
        Assertions: Row keys match {match_id, event_type, game_loop, player_id, event_data}.
        """
        rows = _build_tracker_rows(extracted["match_id"], extracted["tracker_events"])
        expected_keys = {"match_id", "event_type", "game_loop", "player_id", "event_data"}
        assert set(rows[0].keys()) == expected_keys

    def test_game_event_rows_count(self, extracted: dict) -> None:
        """
        Scenario: Game event row builder produces one row per game event.
        Preconditions: Extracted result from sample replay (9038 game events).
        Assertions: 9038 rows returned.
        """
        rows = _build_game_event_rows(
            extracted["match_id"], extracted["game_events"], extracted["player_map"]
        )
        assert len(rows) == 9038

    def test_game_event_row_has_player_id(self, extracted: dict) -> None:
        """
        Scenario: Game event rows have userId mapped to playerID via player_map.
        Preconditions: Extracted result with player_map mapping userIds to playerIDs.
        Assertions: At least some rows have player_id in {1, 2}.
        """
        rows = _build_game_event_rows(
            extracted["match_id"], extracted["game_events"], extracted["player_map"]
        )
        # At least some rows should have mapped player_id (1 or 2)
        mapped = [r for r in rows if r["player_id"] in (1, 2)]
        assert len(mapped) > 0

    def test_metadata_rows(self, extracted: dict) -> None:
        """
        Scenario: Metadata builder produces one row per player.
        Preconditions: Extracted result with 2-player map.
        Assertions: 2 rows returned with player_ids {1, 2}.
        """
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
        """
        Scenario: Parquet write/read round-trip preserves event counts.
        Preconditions: Extracted events from sample replay, written to tmp_path as batch 0.
        Assertions: 3 Parquet files created; tracker has 528 rows, game has 9038 rows.
        """
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
        row = con.execute(
            f"SELECT count(*) FROM read_parquet('{tracker_files[0]}')"
        ).fetchone()
        assert row is not None
        assert row[0] == 528

        row = con.execute(
            f"SELECT count(*) FROM read_parquet('{game_files[0]}')"
        ).fetchone()
        assert row is not None
        assert row[0] == 9038
        con.close()


class TestDuckDBLoading:
    """Test loading Parquet files into DuckDB tables and views."""

    @pytest.fixture()
    def loaded_con(
        self, sample_replay_path: Path, tmp_path: Path
    ) -> Generator[duckdb.DuckDBPyConnection, None, None]:
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
        """
        Scenario: DuckDB loading creates tracker_events_raw table.
        Preconditions: Parquet files loaded into in-memory DuckDB via load_in_game_data_to_duckdb.
        Assertions: tracker_events_raw table exists in information_schema.
        """
        tables = loaded_con.execute(
            "SELECT table_name FROM information_schema.tables"
        ).fetchall()
        table_names = {t[0] for t in tables}
        assert "tracker_events_raw" in table_names

    def test_game_events_raw_table_exists(
        self, loaded_con: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: DuckDB loading creates game_events_raw table.
        Preconditions: Parquet files loaded into in-memory DuckDB.
        Assertions: game_events_raw table exists.
        """
        tables = loaded_con.execute(
            "SELECT table_name FROM information_schema.tables"
        ).fetchall()
        table_names = {t[0] for t in tables}
        assert "game_events_raw" in table_names

    def test_match_player_map_table_exists(
        self, loaded_con: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: DuckDB loading creates match_player_map table.
        Preconditions: Parquet files loaded into in-memory DuckDB.
        Assertions: match_player_map table exists.
        """
        tables = loaded_con.execute(
            "SELECT table_name FROM information_schema.tables"
        ).fetchall()
        table_names = {t[0] for t in tables}
        assert "match_player_map" in table_names

    def test_player_stats_view_exists(
        self, loaded_con: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: DuckDB loading creates the player_stats view.
        Preconditions: Parquet files loaded into in-memory DuckDB.
        Assertions: player_stats view exists in information_schema.
        """
        # Views show up in information_schema.tables with type VIEW
        row = loaded_con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_name = 'player_stats'"
        ).fetchone()
        assert row is not None
        assert row[0] > 0

    def test_player_stats_row_count(
        self, loaded_con: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: player_stats view has correct row count from sample replay.
        Preconditions: Sample replay loaded (48 game loops x 2 players, +1 extra snapshot).
        Assertions: 97 rows in player_stats.
        """
        # 48 unique game loops × 2 players, but player 1 has one extra snapshot
        # at the first loop → 97 total PlayerStats events
        row = loaded_con.execute("SELECT count(*) FROM player_stats").fetchone()
        assert row is not None
        assert row[0] == 97

    def test_player_stats_has_all_39_fields(
        self, loaded_con: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: player_stats view exposes all 39 stat columns plus key columns.
        Preconditions: Sample replay loaded into DuckDB.
        Assertions: Key columns and all 39 PLAYER_STATS_FIELD_MAP values present.
        """
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
        """
        Scenario: Player stats values are typed as numeric (int or float).
        Preconditions: Sample replay loaded into DuckDB.
        Assertions: minerals_current, vespene_current, workers_active_count are int or float.
        """
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
        """
        Scenario: match_player_map contains exactly 2 distinct players for a 1v1 replay.
        Preconditions: Sample sOs vs ByuN replay loaded.
        Assertions: 2 distinct player_id values.
        """
        row = loaded_con.execute(
            "SELECT count(DISTINCT player_id) FROM match_player_map"
        ).fetchone()
        assert row is not None
        assert row[0] == 2


class TestPlayerStatsFieldMap:
    """Verify the PLAYER_STATS_FIELD_MAP constant."""

    def test_has_39_fields(self) -> None:
        """
        Scenario: Field map has exactly 39 entries (one per PlayerStats score field).
        Preconditions: PLAYER_STATS_FIELD_MAP constant.
        Assertions: len == 39.
        """
        assert len(PLAYER_STATS_FIELD_MAP) == 39

    def test_all_values_are_snake_case(self) -> None:
        """
        Scenario: All mapped column names follow snake_case convention.
        Preconditions: PLAYER_STATS_FIELD_MAP constant.
        Assertions: Every value is lowercase with no spaces.
        """
        for src, dst in PLAYER_STATS_FIELD_MAP.items():
            assert dst == dst.lower(), f"{dst} is not lowercase"
            assert " " not in dst, f"{dst} contains spaces"

    def test_source_keys_match_sample(self, sample_replay_path: Path) -> None:
        """
        Scenario: Field map keys match the actual PlayerStats event keys in sample replay.
        Preconditions: Sample sOs vs ByuN replay with trackerEvents.
        Assertions: Mapped keys exactly equal the stats keys from first PlayerStats event.
        """
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
        """
        Scenario: Loading a nonexistent manifest returns empty dict.
        Preconditions: Path points to a file that does not exist.
        Assertions: Returns {}.
        """
        manifest = _load_manifest(tmp_path / "nonexistent.json")
        assert manifest == {}

    def test_load_manifest_valid(self, tmp_path: Path) -> None:
        """
        Scenario: Loading a valid manifest returns its contents.
        Preconditions: JSON file with {"file_a": True, "file_b": False}.
        Assertions: Loaded dict matches written content.
        """
        path = tmp_path / "manifest.json"
        path.write_text(json.dumps({"file_a": True, "file_b": False}))
        manifest = _load_manifest(path)
        assert manifest == {"file_a": True, "file_b": False}

    def test_load_manifest_corrupted(self, tmp_path: Path) -> None:
        """
        Scenario: Corrupted manifest file gracefully returns empty dict.
        Preconditions: File contains invalid JSON.
        Assertions: Returns {} instead of raising.
        """
        path = tmp_path / "manifest.json"
        path.write_text("not valid json{{{")
        manifest = _load_manifest(path)
        assert manifest == {}

    def test_save_manifest_roundtrip(self, tmp_path: Path) -> None:
        """
        Scenario: Saved manifest can be read back identically.
        Preconditions: Dict {"file_x": True} saved to tmp_path.
        Assertions: JSON.loads of written file matches original dict.
        """
        path = tmp_path / "manifest.json"
        data = {"file_x": True}
        _save_manifest(data, path)
        loaded = json.loads(path.read_text())
        assert loaded == data


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

    @patch("rts_predict.sc2.data.ingestion.DUCKDB_TEMP_DIR")
    @patch("rts_predict.sc2.data.ingestion.REPLAYS_SOURCE_DIR")
    def test_loads_replays_into_raw_table(
        self, mock_source: Path, mock_temp: Path, tmp_path: Path
    ) -> None:
        """
        Scenario: move_data_to_duck_db loads JSON replays into the raw table.
        Preconditions: 3 synthetic stripped replay files in tmp_path.
        Assertions: raw table has 3 rows.
        """
        source = self._create_replay_dir(tmp_path)
        temp_dir = tmp_path / "duckdb_tmp"
        temp_dir.mkdir()

        con = duckdb.connect(":memory:")
        with patch("rts_predict.sc2.data.ingestion.REPLAYS_SOURCE_DIR", source), \
             patch("rts_predict.sc2.data.ingestion.DUCKDB_TEMP_DIR", temp_dir):
            move_data_to_duck_db(con, should_drop=True)

        row = con.execute("SELECT count(*) FROM raw").fetchone()
        assert row is not None
        assert row[0] == 3
        con.close()

    @patch("rts_predict.sc2.data.ingestion.DUCKDB_TEMP_DIR")
    @patch("rts_predict.sc2.data.ingestion.REPLAYS_SOURCE_DIR")
    def test_raw_table_has_expected_columns(
        self, mock_source: Path, mock_temp: Path, tmp_path: Path
    ) -> None:
        """
        Scenario: raw table schema includes all expected JSON top-level keys.
        Preconditions: 3 synthetic replays loaded into DuckDB.
        Assertions: Columns include header, initData, details, metadata, ToonPlayerDescMap.
        """
        source = self._create_replay_dir(tmp_path)
        temp_dir = tmp_path / "duckdb_tmp"
        temp_dir.mkdir()

        con = duckdb.connect(":memory:")
        with patch("rts_predict.sc2.data.ingestion.REPLAYS_SOURCE_DIR", source), \
             patch("rts_predict.sc2.data.ingestion.DUCKDB_TEMP_DIR", temp_dir):
            move_data_to_duck_db(con, should_drop=True)

        columns = con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'raw'"
        ).fetchall()
        col_names = {c[0] for c in columns}
        expected = {"header", "initData", "details", "metadata", "ToonPlayerDescMap"}
        assert expected.issubset(col_names)
        con.close()

    @patch("rts_predict.sc2.data.ingestion.DUCKDB_TEMP_DIR")
    @patch("rts_predict.sc2.data.ingestion.REPLAYS_SOURCE_DIR")
    def test_should_drop_recreates_table(
        self, mock_source: Path, mock_temp: Path, tmp_path: Path
    ) -> None:
        """
        Scenario: should_drop=True recreates table instead of appending.
        Preconditions: move_data_to_duck_db called twice with should_drop=True.
        Assertions: raw table has 3 rows (not 6).
        """
        source = self._create_replay_dir(tmp_path)
        temp_dir = tmp_path / "duckdb_tmp"
        temp_dir.mkdir()

        con = duckdb.connect(":memory:")
        with patch("rts_predict.sc2.data.ingestion.REPLAYS_SOURCE_DIR", source), \
             patch("rts_predict.sc2.data.ingestion.DUCKDB_TEMP_DIR", temp_dir):
            move_data_to_duck_db(con, should_drop=True)
            move_data_to_duck_db(con, should_drop=True)

        row = con.execute("SELECT count(*) FROM raw").fetchone()
        assert row is not None
        assert row[0] == 3  # Not doubled
        con.close()


class TestAuditRawDataAvailability:
    """Test audit_raw_data_availability with synthetic replay directories."""

    def test_empty_dir_returns_zero_counts(self, tmp_path: Path) -> None:
        """
        Scenario: Empty replay directory returns all-zero audit counts.
        Preconditions: Empty replays directory.
        Assertions: All count fields are 0.
        """
        source = tmp_path / "replays"
        source.mkdir()

        with patch("rts_predict.sc2.data.ingestion.REPLAYS_SOURCE_DIR", source):
            counts = audit_raw_data_availability()

        assert counts["total"] == 0
        assert counts["has_tracker"] == 0
        assert counts["has_game"] == 0
        assert counts["has_both"] == 0
        assert counts["stripped"] == 0

    def test_mixed_files(self, tmp_path: Path) -> None:
        """
        Scenario: Audit correctly categorizes files with different event combinations.
        Preconditions: 3 files — one with both events, one tracker-only, one stripped.
        Assertions: total=3, has_both=1, has_tracker=2, has_game=1, stripped=1.
        """
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

        with patch("rts_predict.sc2.data.ingestion.REPLAYS_SOURCE_DIR", tmp_path / "replays"):
            counts = audit_raw_data_availability()

        assert counts["total"] == 3
        assert counts["has_both"] == 1
        assert counts["has_tracker"] == 2
        assert counts["has_game"] == 1
        assert counts["stripped"] == 1


class TestIngestMapAliasFiles:
    """Tests for ingest_map_alias_files — row-per-file ingestion with SHA1."""

    def _make_alias_file(self, tourn_dir: Path, content: str) -> Path:
        """Write a map alias JSON file into a tournament subdirectory."""
        tourn_dir.mkdir(parents=True, exist_ok=True)
        alias_path = tourn_dir / "map_foreign_to_english_mapping.json"
        alias_path.write_text(content, encoding="utf-8")
        return alias_path

    def test_ingest_map_alias_files_inserts_one_row_per_file(
        self, tmp_path: Path, in_memory_duckdb: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: 3 fake tournament dirs, each with a distinct JSON file.
        Preconditions: 3 alias JSON files, each with different content.
        Assertions: row count == 3, distinct tournament_dir count == 3,
                    distinct byte_sha1 >= 1.
        """
        raw_dir = tmp_path / "raw"
        contents = [
            '{"MapA": "Map A LE"}',
            '{"MapB": "Map B LE"}',
            '{"MapC": "Map C LE"}',
        ]
        for i, content in enumerate(contents):
            self._make_alias_file(raw_dir / f"2023_Tournament_{i}", content)

        n_inserted = ingest_map_alias_files(in_memory_duckdb, raw_dir)

        assert n_inserted == 3
        row = in_memory_duckdb.execute(
            "SELECT COUNT(*) FROM raw_map_alias_files"
        ).fetchone()
        assert row is not None
        assert row[0] == 3

        row = in_memory_duckdb.execute(
            "SELECT COUNT(DISTINCT tournament_dir) FROM raw_map_alias_files"
        ).fetchone()
        assert row is not None
        assert row[0] == 3

        row = in_memory_duckdb.execute(
            "SELECT COUNT(DISTINCT byte_sha1) FROM raw_map_alias_files"
        ).fetchone()
        assert row is not None
        assert row[0] >= 1

    def test_ingest_map_alias_files_preserves_raw_json_bytes(
        self, tmp_path: Path, in_memory_duckdb: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: One tournament dir with known JSON content.
        Preconditions: Alias JSON file with known exact text.
        Assertions: raw_json column matches original file text byte-for-byte.
        """
        raw_dir = tmp_path / "raw"
        known_content = '{"AlphaKR": "Alpha LE", "BetaKR": "Beta LE"}'
        self._make_alias_file(raw_dir / "2024_GSL_S1", known_content)

        ingest_map_alias_files(in_memory_duckdb, raw_dir)

        row = in_memory_duckdb.execute(
            "SELECT raw_json FROM raw_map_alias_files"
        ).fetchone()
        assert row is not None
        assert row[0] == known_content

    def test_ingest_map_alias_files_raises_on_empty_root(
        self, tmp_path: Path, in_memory_duckdb: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: Empty tmp_path with no alias files.
        Preconditions: tmp_path contains no map_foreign_to_english_mapping.json.
        Assertions: ValueError is raised.
        """
        raw_dir = tmp_path / "empty_raw"
        raw_dir.mkdir()

        with pytest.raises(ValueError):
            ingest_map_alias_files(in_memory_duckdb, raw_dir)


class TestCollectPendingFiles:
    """Test _collect_pending_files with manifest filtering."""

    def test_filters_already_done(self, tmp_path: Path) -> None:
        """
        Scenario: Files already in manifest are excluded from pending list.
        Preconditions: 2 files on disk, 1 already in manifest.
        Assertions: Only 1 pending file returned (pending.SC2Replay.json).
        """
        data_dir = tmp_path / "replays" / "tourn" / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "done.SC2Replay.json").write_text("{}")
        (data_dir / "pending.SC2Replay.json").write_text("{}")

        manifest = {"tourn/data/done.SC2Replay.json": True}

        with patch("rts_predict.sc2.data.ingestion.REPLAYS_SOURCE_DIR", tmp_path / "replays"):
            pending = _collect_pending_files(manifest)

        assert len(pending) == 1
        assert pending[0].name == "pending.SC2Replay.json"


class TestRunInGameExtraction:
    """Test run_in_game_extraction with mocked Pool."""

    @patch("rts_predict.sc2.data.ingestion.save_raw_events_to_parquet")
    @patch("rts_predict.sc2.data.ingestion._save_manifest")
    @patch("rts_predict.sc2.data.ingestion._collect_pending_files")
    @patch("rts_predict.sc2.data.ingestion._load_manifest", return_value={})
    def test_mock_pool_batches(
        self, m_load, m_collect, m_save_manifest, m_save_parquet, tmp_path: Path
    ) -> None:
        """
        Scenario: Multiprocessing extraction batches results correctly.
        Preconditions: 3 fake pending files, batch_size=2, mocked Pool.
        Assertions: save_raw_events_to_parquet called twice (batch of 2, then 1).
        """
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

        manifest_path = tmp_path / "manifest.json"
        with (
            patch("rts_predict.sc2.data.ingestion.multiprocessing.Pool", return_value=mock_pool),
            patch("rts_predict.sc2.data.ingestion.IN_GAME_MANIFEST_PATH", manifest_path),
        ):
            run_in_game_extraction(
                parquet_dir=tmp_path / "parquet", max_workers=1, batch_size=2,
            )

        # 3 results with batch_size=2 → 2 calls to save_parquet (batch of 2, then 1)
        assert m_save_parquet.call_count == 2

    @patch("rts_predict.sc2.data.ingestion._collect_pending_files", return_value=[])
    @patch("rts_predict.sc2.data.ingestion._load_manifest", return_value={})
    def test_empty_pending_returns_early(self, m_load, m_collect, tmp_path: Path) -> None:
        """
        Scenario: No pending files means Pool is never created.
        Preconditions: _collect_pending_files returns empty list.
        Assertions: multiprocessing.Pool not called.
        """
        manifest_path = tmp_path / "manifest.json"
        with (
            patch("rts_predict.sc2.data.ingestion.multiprocessing.Pool") as m_pool,
            patch("rts_predict.sc2.data.ingestion.IN_GAME_MANIFEST_PATH", manifest_path),
        ):
            run_in_game_extraction(parquet_dir=tmp_path / "parquet")

        m_pool.assert_not_called()


# ── Exception-path coverage ──────────────────────────────────────────────────




class TestAuditRawDataAvailabilityExceptionPath:
    """Test the exception-handling branch in audit_raw_data_availability."""

    def test_corrupt_replay_file_logs_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """When a replay JSON file is corrupt, an error must be logged."""
        monkeypatch.setattr("rts_predict.sc2.data.ingestion.REPLAYS_SOURCE_DIR", tmp_path)

        # Write a corrupt SC2Replay JSON file
        corrupt_file = tmp_path / "aabbccdd11223344556677889900aa00.SC2Replay.json"
        corrupt_file.write_text("NOT_VALID_JSON{")

        with caplog.at_level(logging.ERROR):
            result = audit_raw_data_availability()

        assert result["total"] == 1
        assert any("Error reading" in msg for msg in caplog.messages)


class TestRunInGameExtractionNoneResult:
    """Test that None results from pool are handled (skipped file path)."""

    @patch("rts_predict.sc2.data.ingestion.save_raw_events_to_parquet")
    @patch("rts_predict.sc2.data.ingestion._save_manifest")
    @patch("rts_predict.sc2.data.ingestion._collect_pending_files")
    @patch("rts_predict.sc2.data.ingestion._load_manifest", return_value={})
    def test_none_results_are_skipped(
        self, m_load, m_collect, m_save_manifest, m_save_parquet, tmp_path: Path
    ) -> None:
        """None results from the extraction pool must increment skipped count."""
        from rts_predict.sc2.data.ingestion import run_in_game_extraction

        fake_paths = [tmp_path / f"f{i}.json" for i in range(2)]
        m_collect.return_value = fake_paths

        # One valid result, one None (stripped file)
        fake_results = [
            {"match_id": "m0", "tracker_events": [], "game_events": [], "player_map": {}},
            None,
        ]

        mock_pool = MagicMock()
        mock_pool.__enter__ = MagicMock(return_value=mock_pool)
        mock_pool.__exit__ = MagicMock(return_value=False)
        mock_pool.imap_unordered.return_value = iter(fake_results)

        manifest_path = tmp_path / "manifest.json"
        with (
            patch("rts_predict.sc2.data.ingestion.multiprocessing.Pool", return_value=mock_pool),
            patch("rts_predict.sc2.data.ingestion.IN_GAME_MANIFEST_PATH", manifest_path),
        ):
            run_in_game_extraction(parquet_dir=tmp_path / "parquet", max_workers=1, batch_size=10)

        # Only 1 real result, so save_parquet called once (leftover buffer at end)
        assert m_save_parquet.call_count == 1

    @patch("rts_predict.sc2.data.ingestion.save_raw_events_to_parquet")
    @patch("rts_predict.sc2.data.ingestion._save_manifest")
    @patch("rts_predict.sc2.data.ingestion._collect_pending_files")
    @patch("rts_predict.sc2.data.ingestion._load_manifest", return_value={})
    def test_progress_log_triggered(
        self, m_load, m_collect, m_save_manifest, m_save_parquet, tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Progress log must appear when total_processed hits EXTRACTION_LOG_INTERVAL."""
        from rts_predict.sc2.data.ingestion import run_in_game_extraction

        fake_paths = [tmp_path / "f0.json"]
        m_collect.return_value = fake_paths

        fake_results = [
            {"match_id": "m0", "tracker_events": [], "game_events": [], "player_map": {}}
        ]

        mock_pool = MagicMock()
        mock_pool.__enter__ = MagicMock(return_value=mock_pool)
        mock_pool.__exit__ = MagicMock(return_value=False)
        mock_pool.imap_unordered.return_value = iter(fake_results)

        manifest_path = tmp_path / "manifest.json"
        with (
            patch("rts_predict.sc2.data.ingestion.multiprocessing.Pool", return_value=mock_pool),
            patch("rts_predict.sc2.data.ingestion.IN_GAME_MANIFEST_PATH", manifest_path),
            patch("rts_predict.sc2.data.ingestion.EXTRACTION_LOG_INTERVAL", 1),
            caplog.at_level(logging.INFO),
        ):
            run_in_game_extraction(
                parquet_dir=tmp_path / "parquet", max_workers=1, batch_size=10,
            )

        assert any("Progress:" in msg for msg in caplog.messages)
