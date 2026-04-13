"""Tests for sc2egset ingestion.py — CTAS functions and event extraction."""

import json
from pathlib import Path

import duckdb
import pytest

from rts_predict.games.sc2.datasets.sc2egset.ingestion import (
    extract_events_to_parquet,
    load_all_raw_tables,
    load_map_aliases,
    load_replay_players,
    load_replays_meta,
)

# ── Synthetic fixture helpers ────────────────────────────────────────────────


def _make_replay_json(path: Path, *, n_events: int = 5) -> None:
    """Write a minimal synthetic SC2Replay.json file."""
    data = {
        "ToonPlayerDescMap": {
            "1-S2-1-100": {
                "nickname": "Player1",
                "playerID": 1,
                "userID": 100,
                "SQ": 80,
                "supplyCappedPercent": 5,
                "startDir": 0,
                "startLocX": 10,
                "startLocY": 20,
                "race": "Terran",
                "selectedRace": "Terran",
                "APM": 200,
                "MMR": 5000,
                "result": "Win",
                "region": "US",
                "realm": "1",
                "highestLeague": "Master",
                "isInClan": False,
                "clanTag": "",
                "handicap": 100,
                "color": {"a": 255, "b": 0, "g": 0, "r": 255},
            },
            "2-S2-1-200": {
                "nickname": "Player2",
                "playerID": 2,
                "userID": 200,
                "SQ": 70,
                "supplyCappedPercent": 8,
                "startDir": 4,
                "startLocX": 90,
                "startLocY": 80,
                "race": "Protoss",
                "selectedRace": "Protoss",
                "APM": 250,
                "MMR": 5200,
                "result": "Loss",
                "region": "US",
                "realm": "1",
                "highestLeague": "GrandMaster",
                "isInClan": True,
                "clanTag": "ROOT",
                "handicap": 100,
                "color": {"a": 255, "b": 255, "g": 0, "r": 0},
            },
        },
        "header": {"elapsedGameLoops": 10000, "version": "5.0.0"},
        "initData": {"gameDescription": {"gameSpeed": "Faster"}},
        "details": {
            "gameSpeed": "Faster",
            "isBlizzardMap": True,
            "timeUTC": "2024-01-01T10:00:00",
        },
        "metadata": {
            "baseBuild": "12345",
            "dataBuild": "12345",
            "gameVersion": "5.0.0",
            "mapName": "Oceanborn LE",
        },
        "gameEvents": [
            {"evtTypeName": "NNet.Game.SGameUserJoinEvent", "id": i, "loop": i * 10}
            for i in range(n_events)
        ],
        "trackerEvents": [
            {"evtTypeName": "NNet.Replay.Tracker.SPlayerSetupEvent", "id": i, "loop": 0}
            for i in range(max(1, n_events // 5))
        ],
        "messageEvents": [
            {"evtTypeName": "NNet.Game.SChatMessage", "id": 0, "loop": 0}
        ],
        "gameEventsErr": False,
        "messageEventsErr": False,
        "trackerEvtsErr": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _make_mapping_json(path: Path, *, n_keys: int = 3) -> None:
    """Write a synthetic map_foreign_to_english_mapping.json."""
    data = {f"MapName_{i}": f"English Map {i}" for i in range(n_keys)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def sc2_raw_dir(tmp_path: Path) -> Path:
    """Create synthetic sc2egset raw directory with 2 tournaments."""
    raw = tmp_path / "raw"

    for tournament in ["2020_Tournament_A", "2021_Tournament_B"]:
        data_dir = raw / tournament / f"{tournament}_data"
        for i in range(3):
            _make_replay_json(
                data_dir / f"replay_{i:02d}.SC2Replay.json",
                n_events=5 + i * 10,
            )
        _make_mapping_json(raw / tournament / "map_foreign_to_english_mapping.json")

    return raw


@pytest.fixture()
def sc2_db_con() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB connection."""
    return duckdb.connect(":memory:")


# ── Tests: load_replays_meta ─────────────────────────────────────────────────


class TestLoadReplaysMeta:
    """Tests for load_replays_meta."""

    def test_creates_table_with_filename(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """replays_meta table must exist and contain a 'filename' column."""
        n = load_replays_meta(sc2_db_con, sc2_raw_dir)
        assert n > 0
        tables = [row[0] for row in sc2_db_con.execute("SHOW TABLES").fetchall()]
        assert "replays_meta" in tables
        cols = [row[0] for row in sc2_db_con.execute("DESCRIBE replays_meta").fetchall()]
        assert "filename" in cols

    def test_row_count_matches_files(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """Should have one row per replay file (2 tournaments x 3 files = 6)."""
        n = load_replays_meta(sc2_db_con, sc2_raw_dir)
        assert n == 6  # noqa: PLR2004

    def test_tpdm_is_varchar(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """ToonPlayerDescMap column must be VARCHAR (JSON text blob)."""
        load_replays_meta(sc2_db_con, sc2_raw_dir)
        type_map = {
            row[0]: row[1]
            for row in sc2_db_con.execute("DESCRIBE replays_meta").fetchall()
        }
        assert type_map["ToonPlayerDescMap"] == "VARCHAR"

    def test_excludes_event_arrays(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """replays_meta must NOT contain gameEvents/trackerEvents/messageEvents columns."""
        load_replays_meta(sc2_db_con, sc2_raw_dir)
        cols = {row[0] for row in sc2_db_con.execute("DESCRIBE replays_meta").fetchall()}
        assert "gameEvents" not in cols
        assert "trackerEvents" not in cols
        assert "messageEvents" not in cols

    def test_contains_metadata_struct_columns(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """replays_meta must contain details, header, initData, metadata columns."""
        load_replays_meta(sc2_db_con, sc2_raw_dir)
        cols = {row[0] for row in sc2_db_con.execute("DESCRIBE replays_meta").fetchall()}
        for expected in ("details", "header", "initData", "metadata"):
            assert expected in cols

    def test_idempotent(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """Running load_replays_meta twice with should_drop=True gives same count."""
        n1 = load_replays_meta(sc2_db_con, sc2_raw_dir, should_drop=True)
        n2 = load_replays_meta(sc2_db_con, sc2_raw_dir, should_drop=True)
        assert n1 == n2


# ── Tests: load_replay_players ───────────────────────────────────────────────


class TestLoadReplayPlayers:
    """Tests for load_replay_players."""

    def test_creates_table_with_filename(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """replay_players table must exist and contain a 'filename' column."""
        n = load_replay_players(sc2_db_con, sc2_raw_dir)
        assert n > 0
        tables = [row[0] for row in sc2_db_con.execute("SHOW TABLES").fetchall()]
        assert "replay_players" in tables
        cols = [row[0] for row in sc2_db_con.execute("DESCRIBE replay_players").fetchall()]
        assert "filename" in cols

    def test_normalises_to_one_row_per_player(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """Each replay has 2 players, 6 replays -> 12 rows."""
        n = load_replay_players(sc2_db_con, sc2_raw_dir)
        assert n == 12  # noqa: PLR2004

    def test_has_toon_id_column(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """replay_players must have a toon_id column (MAP key from ToonPlayerDescMap)."""
        load_replay_players(sc2_db_con, sc2_raw_dir)
        cols = {row[0] for row in sc2_db_con.execute("DESCRIBE replay_players").fetchall()}
        assert "toon_id" in cols

    def test_has_all_player_fields(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """replay_players must have all expected player fields."""
        load_replay_players(sc2_db_con, sc2_raw_dir)
        cols = {row[0] for row in sc2_db_con.execute("DESCRIBE replay_players").fetchall()}
        expected_fields = {
            "toon_id", "nickname", "playerID", "userID", "isInClan", "clanTag",
            "MMR", "race", "selectedRace", "handicap", "region", "realm",
            "highestLeague", "result", "APM", "SQ", "supplyCappedPercent",
            "startDir", "startLocX", "startLocY",
            "color_a", "color_b", "color_g", "color_r",
        }
        for field in expected_fields:
            assert field in cols, f"Missing field: {field}"

    def test_player_data_values_correct(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """Spot-check that extracted player data values are correct."""
        load_replay_players(sc2_db_con, sc2_raw_dir)
        df = sc2_db_con.execute(
            "SELECT * FROM replay_players WHERE toon_id = '1-S2-1-100' LIMIT 1"
        ).df()
        assert len(df) == 1
        row = df.iloc[0]
        assert row["nickname"] == "Player1"
        assert row["MMR"] == 5000  # noqa: PLR2004
        assert row["race"] == "Terran"
        assert row["result"] == "Win"

    def test_idempotent(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """Running load_replay_players twice with should_drop=True gives same count."""
        n1 = load_replay_players(sc2_db_con, sc2_raw_dir, should_drop=True)
        n2 = load_replay_players(sc2_db_con, sc2_raw_dir, should_drop=True)
        assert n1 == n2


# ── Tests: extract_events_to_parquet ─────────────────────────────────────────


class TestExtractEventsToParquet:
    """Tests for extract_events_to_parquet."""

    def test_creates_parquet_files(
        self, sc2_raw_dir: Path, tmp_path: Path
    ) -> None:
        """Should create Parquet files for all 3 event types."""
        output_dir = tmp_path / "events"
        counts = extract_events_to_parquet(sc2_raw_dir, output_dir, batch_size=10)

        for et in ("gameEvents", "trackerEvents", "messageEvents"):
            assert et in counts
            assert counts[et] > 0
            parquet_path = output_dir / f"{et}.parquet"
            assert parquet_path.exists()

    def test_parquet_has_expected_columns(
        self, sc2_raw_dir: Path, tmp_path: Path
    ) -> None:
        """Each Parquet file must have filename, loop, evtTypeName, event_data."""
        import pyarrow.parquet as pq

        output_dir = tmp_path / "events"
        extract_events_to_parquet(sc2_raw_dir, output_dir, batch_size=10)

        for et in ("gameEvents", "trackerEvents", "messageEvents"):
            schema = pq.read_schema(output_dir / f"{et}.parquet")
            col_names = set(schema.names)
            assert {"filename", "loop", "evtTypeName", "event_data"} <= col_names

    def test_returns_correct_counts(
        self, sc2_raw_dir: Path, tmp_path: Path
    ) -> None:
        """Row counts should match the number of events in synthetic data."""
        output_dir = tmp_path / "events"
        counts = extract_events_to_parquet(sc2_raw_dir, output_dir, batch_size=10)

        # 6 files with n_events: 5,15,25,5,15,25 -> gameEvents = 90
        # trackerEvents: max(1,n//5) = 1,3,5,1,3,5 = 18
        # messageEvents: 1 per file = 6
        assert counts["gameEvents"] == 90  # noqa: PLR2004
        assert counts["trackerEvents"] == 18  # noqa: PLR2004
        assert counts["messageEvents"] == 6  # noqa: PLR2004


# ── Tests: load_map_aliases ──────────────────────────────────────────────────


class TestLoadMapAliases:
    """Tests for load_map_aliases."""

    def test_creates_table_with_tournament_column(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """map_aliases table must exist and contain tournament + filename columns."""
        n = load_map_aliases(sc2_db_con, sc2_raw_dir)
        assert n > 0
        cols = {row[0] for row in sc2_db_con.execute("DESCRIBE map_aliases").fetchall()}
        assert "tournament" in cols
        assert "foreign_name" in cols
        assert "english_name" in cols
        assert "filename" in cols

    def test_row_count_from_two_tournaments(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """2 tournaments x 3 keys each = 6 rows."""
        n = load_map_aliases(sc2_db_con, sc2_raw_dir)
        assert n == 6  # noqa: PLR2004

    def test_tournament_provenance(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """Each row must have the correct tournament name."""
        load_map_aliases(sc2_db_con, sc2_raw_dir)
        tournaments = sc2_db_con.execute(
            "SELECT DISTINCT tournament FROM map_aliases ORDER BY tournament"
        ).fetchall()
        assert [t[0] for t in tournaments] == [
            "2020_Tournament_A",
            "2021_Tournament_B",
        ]

    def test_idempotent(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """Running load_map_aliases twice with should_drop=True gives same count."""
        n1 = load_map_aliases(sc2_db_con, sc2_raw_dir, should_drop=True)
        n2 = load_map_aliases(sc2_db_con, sc2_raw_dir, should_drop=True)
        assert n1 == n2


# ── Tests: load_all_raw_tables ───────────────────────────────────────────────


class TestLoadAllRawTables:
    """Tests for load_all_raw_tables."""

    def test_returns_all_table_counts(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """load_all_raw_tables must return a dict with all three table names."""
        counts = load_all_raw_tables(sc2_db_con, sc2_raw_dir)
        assert set(counts.keys()) == {"replays_meta", "replay_players", "map_aliases"}
        tables = [row[0] for row in sc2_db_con.execute("SHOW TABLES").fetchall()]
        for table in counts:
            assert table in tables

    def test_all_tables_have_rows(
        self, sc2_db_con: duckdb.DuckDBPyConnection, sc2_raw_dir: Path
    ) -> None:
        """All tables must have at least one row."""
        counts = load_all_raw_tables(sc2_db_con, sc2_raw_dir)
        for table, count in counts.items():
            assert count > 0, f"Table {table} has no rows"
