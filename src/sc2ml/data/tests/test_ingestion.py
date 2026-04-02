"""Tests for in-game event extraction pipeline (Path B).

Uses the sample replay file (sOs vs ByuN) shipped in samples/raw/ to verify:
- Raw event extraction produces correct counts and structure
- Parquet round-trip preserves data
- DuckDB loading creates expected tables and views
- PlayerStats view returns typed columns for all 39 fields
"""
import json
from pathlib import Path

import duckdb
import pytest

from sc2ml.data.ingestion import (
    PLAYER_STATS_FIELD_MAP,
    _build_game_event_rows,
    _build_metadata_rows,
    _build_tracker_rows,
    extract_raw_events_from_file,
    load_in_game_data_to_duckdb,
    save_raw_events_to_parquet,
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
