"""Tests for Phase 1 — Corpus Inventory and Parse Quality (exploration.py).

Uses synthetic in-memory DuckDB fixtures to validate each step function.
"""

import json
from collections.abc import Generator
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pytest

# ── Synthetic fixture ───────────────────────────────────────────────────────

SYNTHETIC_REPLAY_IDS = [
    "aabbccdd11223344556677889900aa00",
    "aabbccdd11223344556677889900aa01",
    "aabbccdd11223344556677889900aa02",
    "aabbccdd11223344556677889900aa03",
    "aabbccdd11223344556677889900aa04",
    "aabbccdd11223344556677889900aa05",
]


def _build_tpdm(
    p1_name: str,
    p2_name: str,
    p1_result: str = "Win",
    p1_apm: int = 200,
    p2_apm: int = 180,
    p1_mmr: int = 0,
    p2_mmr: int = 0,
) -> str:
    p2_result = "Loss" if p1_result == "Win" else "Win"
    return json.dumps({
        "toon-1": {
            "nickname": p1_name, "playerID": 1, "userID": 1,
            "SQ": 80, "supplyCappedPercent": 5, "startLocX": 40, "startLocY": 20,
            "race": "Terran", "APM": p1_apm, "MMR": p1_mmr, "result": p1_result,
            "isInClan": False, "highestLeague": "6",
        },
        "toon-2": {
            "nickname": p2_name, "playerID": 2, "userID": 2,
            "SQ": 75, "supplyCappedPercent": 8, "startLocX": 130, "startLocY": 150,
            "race": "Protoss", "APM": p2_apm, "MMR": p2_mmr, "result": p2_result,
            "isInClan": False, "highestLeague": "5",
        },
    })


@pytest.fixture()
def exploration_con() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """In-memory DuckDB with synthetic data for Phase 1 exploration tests.

    Creates:
    - raw table: 6 replays across 2 tournaments (2020_TestTournA, 2021_TestTournB)
    - tracker_events_raw: events for 5 of 6 replays (one missing)
    - match_player_map: 2 players per replay except one with 3 (anomaly)

    Replay layout:
    - IDs 0-2: 2020_TestTournA, year 2020
    - IDs 3-5: 2021_TestTournB, year 2021
    - ID 0 appears in BOTH tournament dirs (duplicate replay_id)
    - ID 4: both players have result = "Win" (anomaly)
    - ID 5: no tracker events (missing coverage)
    - ID 2: has 3 players in match_player_map (anomaly)
    """
    con = duckdb.connect(":memory:")

    # Raw table
    rid0 = SYNTHETIC_REPLAY_IDS[0]
    rid1 = SYNTHETIC_REPLAY_IDS[1]
    rid2 = SYNTHETIC_REPLAY_IDS[2]
    rid3 = SYNTHETIC_REPLAY_IDS[3]
    rid4 = SYNTHETIC_REPLAY_IDS[4]
    raw_rows = [
        # 2020_TestTournA — 3 replays
        {
            "filename": f"2020_TestTournA/2020_TestTournA_data/{rid0}.SC2Replay.json",
            "header": json.dumps({"elapsedGameLoops": 13440}),  # 13440 / 22.4 / 60 = 10 min
            "initData": json.dumps({"gameDescription": {"mapSizeX": 200, "mapSizeY": 200}}),
            "details": json.dumps({"timeUTC": "2020-03-15T12:00:00"}),
            "metadata": json.dumps({
                "dataBuild": "50012", "gameVersion": "5.0.12", "mapName": "Altitude LE",
            }),
            "ToonPlayerDescMap": _build_tpdm("Alpha", "Beta", "Win"),
        },
        {
            "filename": f"2020_TestTournA/2020_TestTournA_data/{rid1}.SC2Replay.json",
            "header": json.dumps({"elapsedGameLoops": 20160}),  # 20160 / 22.4 / 60 = 15 min
            "initData": json.dumps({"gameDescription": {"mapSizeX": 200, "mapSizeY": 200}}),
            "details": json.dumps({"timeUTC": "2020-03-15T13:00:00"}),
            "metadata": json.dumps({
                "dataBuild": "50012", "gameVersion": "5.0.12", "mapName": "Altitude LE",
            }),
            "ToonPlayerDescMap": _build_tpdm("Gamma", "Delta", "Loss"),
        },
        {
            "filename": f"2020_TestTournA/2020_TestTournA_data/{rid2}.SC2Replay.json",
            "header": json.dumps({"elapsedGameLoops": 6720}),  # 6720 / 22.4 / 60 = 5 min
            "initData": json.dumps({"gameDescription": {"mapSizeX": 200, "mapSizeY": 200}}),
            "details": json.dumps({"timeUTC": "2020-03-16T10:00:00"}),
            "metadata": json.dumps({
                "dataBuild": "50012", "gameVersion": "5.0.12", "mapName": "Berlingrad LE",
            }),
            "ToonPlayerDescMap": _build_tpdm("Alpha", "Gamma", "Win"),
        },
        # 2021_TestTournB — 3 replays
        {
            "filename": f"2021_TestTournB/2021_TestTournB_data/{rid3}.SC2Replay.json",
            "header": json.dumps({"elapsedGameLoops": 26880}),  # 26880 / 22.4 / 60 = 20 min
            "initData": json.dumps({"gameDescription": {"mapSizeX": 200, "mapSizeY": 200}}),
            "details": json.dumps({"timeUTC": "2021-06-01T14:00:00"}),
            "metadata": json.dumps({
                "dataBuild": "50516", "gameVersion": "5.0.5.16", "mapName": "Oxide LE",
            }),
            "ToonPlayerDescMap": _build_tpdm("Beta", "Delta", "Win"),
        },
        {
            # Anomaly: both players Win
            "filename": f"2021_TestTournB/2021_TestTournB_data/{rid4}.SC2Replay.json",
            "header": json.dumps({"elapsedGameLoops": 8064}),  # 8064 / 22.4 / 60 = 6 min
            "initData": json.dumps({"gameDescription": {"mapSizeX": 200, "mapSizeY": 200}}),
            "details": json.dumps({"timeUTC": "2021-06-02T10:00:00"}),
            "metadata": json.dumps({
                "dataBuild": "50516", "gameVersion": "5.0.5.16", "mapName": "Oxide LE",
            }),
            "ToonPlayerDescMap": _build_tpdm(
                "Alpha", "Delta", "Win", p1_apm=200, p2_apm=180
            ).replace('"result": "Loss"', '"result": "Win"'),
        },
        {
            # Replay ID 0 duplicated here (same ID, different tournament)
            "filename": f"2021_TestTournB/2021_TestTournB_data/{rid0}.SC2Replay.json",
            "header": json.dumps({"elapsedGameLoops": 16128}),  # 16128 / 22.4 / 60 = 12 min
            "initData": json.dumps({"gameDescription": {"mapSizeX": 200, "mapSizeY": 200}}),
            "details": json.dumps({"timeUTC": "2021-06-03T08:00:00"}),
            "metadata": json.dumps({
                "dataBuild": "50516", "gameVersion": "5.0.5.16", "mapName": "Altitude LE",
            }),
            "ToonPlayerDescMap": _build_tpdm("Gamma", "Beta", "Win"),
        },
    ]
    raw_df = pd.DataFrame(raw_rows)  # noqa: F841
    con.execute("CREATE TABLE raw AS SELECT * FROM raw_df")
    con.execute("""
        CREATE OR REPLACE TABLE raw AS
        SELECT
            filename,
            header::JSON AS header,
            "initData"::JSON AS "initData",
            details::JSON AS details,
            metadata::JSON AS metadata,
            "ToonPlayerDescMap"::JSON AS "ToonPlayerDescMap"
        FROM raw
    """)

    # tracker_events_raw: events for IDs 0-4, NOT for ID 5 (which is the duplicate of 0)
    # Actually ID 5 in raw_rows is replay_id aa00 again. Let's provide events for IDs 0-4
    # (unique replay IDs: aa00, aa01, aa02, aa03, aa04). Missing: the 6th raw row (aa00 duplicate)
    # has events via the first aa00 entry, so effectively 5 distinct replay IDs with events.
    tracker_rows = []
    for replay_idx in range(5):  # IDs aa00 through aa04
        rid = SYNTHETIC_REPLAY_IDS[replay_idx]
        match_id = f"tournament/data/{rid}.SC2Replay.json"
        # PlayerStats events at known intervals
        interval = 160 if replay_idx < 3 else 240  # 2020=160, 2021=240 (50% deviation)
        for player_id in [1, 2]:
            for loop in range(interval, interval * 10 + 1, interval):
                tracker_rows.append({
                    "match_id": match_id,
                    "event_type": "PlayerStats",
                    "player_id": player_id,
                    "game_loop": loop,
                    "data": "{}",
                })
        # Some UnitBorn events
        for loop in [100, 500, 1000]:
            tracker_rows.append({
                "match_id": match_id,
                "event_type": "UnitBorn",
                "player_id": 1,
                "game_loop": loop,
                "data": "{}",
            })
        # Some UnitDied events
        for loop in [600, 1200]:
            tracker_rows.append({
                "match_id": match_id,
                "event_type": "UnitDied",
                "player_id": 1,
                "game_loop": loop,
                "data": "{}",
            })

    tracker_df = pd.DataFrame(tracker_rows)  # noqa: F841
    con.execute("CREATE TABLE tracker_events_raw AS SELECT * FROM tracker_df")

    # match_player_map: 2 players per replay, except ID 2 has 3 (anomaly)
    mpm_rows = []
    for replay_idx in range(6):
        if replay_idx == 5:
            # This is the duplicate aa00 row; use same match_id pattern as raw
            mid = f"2021_TestTournB/2021_TestTournB_data/{SYNTHETIC_REPLAY_IDS[0]}.SC2Replay.json"
        else:
            mid = f"tournament/tournament_data/{SYNTHETIC_REPLAY_IDS[replay_idx]}.SC2Replay.json"
        for pid in [1, 2]:
            mpm_rows.append({"match_id": mid, "player_id": pid, "nickname": f"Player{pid}"})
        if replay_idx == 2:  # 3-player anomaly
            mpm_rows.append({"match_id": mid, "player_id": 3, "nickname": "Player3"})

    mpm_df = pd.DataFrame(mpm_rows)  # noqa: F841
    con.execute("CREATE TABLE match_player_map AS SELECT * FROM mpm_df")

    yield con
    con.close()


# ── Step 1.1 tests ──────────────────────────────────────────────────────────


class TestCorpusSummary:
    def test_corpus_dimensions(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_corpus_summary

        result = run_corpus_summary(exploration_con, output_dir=tmp_path)
        dims = result["dimensions"]
        assert dims["total_replays"] == 6
        assert dims["total_tournaments"] == 2

    def test_event_coverage(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_corpus_summary

        result = run_corpus_summary(exploration_con, output_dir=tmp_path)
        ec = result["event_coverage"]
        # 6 raw rows, all 5 distinct replay IDs have events.
        # The duplicate aa00 row also matches, so all 6 rows have events.
        assert ec["has_events"] == 6
        assert ec["missing_events"] == 0

    def test_player_count_anomalies_csv(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_corpus_summary

        result = run_corpus_summary(exploration_con, output_dir=tmp_path)
        assert result["player_count_anomalies"] > 0
        assert (tmp_path / "01_01_player_count_anomalies.csv").exists()

    def test_result_audit_contains_sql(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_corpus_summary

        run_corpus_summary(exploration_con, output_dir=tmp_path)
        md = (tmp_path / "01_01_result_field_audit.md").read_text()
        assert "```sql" in md
        assert "entry.value->>'$.result'" in md

    def test_result_anomalies_detected(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_corpus_summary

        result = run_corpus_summary(exploration_con, output_dir=tmp_path)
        anomalous = result["result_anomalous"]
        assert anomalous["multiple_winner_replays"] >= 1

    def test_duplicate_detected(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_corpus_summary

        result = run_corpus_summary(exploration_con, output_dir=tmp_path)
        assert len(result["duplicate_list"]) > 0


# ── Step 1.2 tests ──────────────────────────────────────────────────────────


class TestParseQuality:
    def test_parse_quality_csv_columns(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_parse_quality_by_tournament

        run_parse_quality_by_tournament(exploration_con, output_dir=tmp_path)
        df = pd.read_csv(tmp_path / "01_02_parse_quality_by_tournament.csv")
        expected_cols = {
            "tournament_dir", "total_replays", "has_events", "missing_events",
            "null_timestamp", "event_coverage_pct", "player_count_anomalies",
            "result_anomalies",
        }
        assert expected_cols.issubset(set(df.columns))

    def test_parse_quality_sorted_by_coverage(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_parse_quality_by_tournament

        run_parse_quality_by_tournament(exploration_con, output_dir=tmp_path)
        df = pd.read_csv(tmp_path / "01_02_parse_quality_by_tournament.csv")
        coverages = df["event_coverage_pct"].tolist()
        assert coverages == sorted(coverages)


# ── Step 1.3 tests ──────────────────────────────────────────────────────────


class TestDurationDistribution:
    def test_duration_csv_created(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_duration_distribution

        run_duration_distribution(exploration_con, output_dir=tmp_path)
        assert (tmp_path / "01_03_duration_distribution.csv").exists()

    def test_duration_png_created(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_duration_distribution

        run_duration_distribution(exploration_con, output_dir=tmp_path)
        full_png = tmp_path / "01_03_duration_distribution_full.png"
        short_png = tmp_path / "01_03_duration_distribution_short_tail.png"
        assert full_png.exists() and full_png.stat().st_size > 0
        assert short_png.exists() and short_png.stat().st_size > 0

    def test_duration_percentile_ordering(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_duration_distribution

        result = run_duration_distribution(exploration_con, output_dir=tmp_path)
        p = result["percentiles"]
        assert p["p01"] <= p["p05"] <= p["p10"] <= p["p25"]
        assert p["p25"] <= p["median"] <= p["p75"]
        assert p["p75"] <= p["p90"] <= p["p95"] <= p["p99"]

    def test_conversion_correctness(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_duration_distribution

        result = run_duration_distribution(exploration_con, output_dir=tmp_path)
        # 13440 loops / 22.4 / 60 = 10.0 min exactly
        # We have games at 5, 6, 10, 12, 15, 20 real-time minutes
        p = result["percentiles"]
        assert p["mean"] > 0
        # Median of [5, 6, 10, 12, 15, 20] = 11
        assert abs(p["median"] - 11.0) < 0.5


# ── Step 1.4 tests ──────────────────────────────────────────────────────────


class TestApmMmrAudit:
    def test_apm_mmr_md_contains_sql(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_apm_mmr_audit

        run_apm_mmr_audit(exploration_con, output_dir=tmp_path)
        md = (tmp_path / "01_04_apm_mmr_audit.md").read_text()
        assert "```sql" in md
        assert "APM" in md


# ── Step 1.5 tests ──────────────────────────────────────────────────────────


class TestPatchLandscape:
    def test_patch_landscape_csv(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_patch_landscape

        run_patch_landscape(exploration_con, output_dir=tmp_path)
        df = pd.read_csv(tmp_path / "01_05_patch_landscape.csv")
        expected_cols = {"game_version", "data_build", "replay_count", "date_min", "date_max"}
        assert expected_cols.issubset(set(df.columns))
        # 2 distinct game versions in synthetic data
        assert len(df) == 2


# ── Step 1.6 tests ──────────────────────────────────────────────────────────


class TestEventTypeInventory:
    def test_event_inventory_csv(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_event_type_inventory

        result = run_event_type_inventory(exploration_con, output_dir=tmp_path)
        inventory = result["inventory"]
        event_types = {r["event_type"] for r in inventory}
        assert "PlayerStats" in event_types
        assert "UnitBorn" in event_types
        assert "UnitDied" in event_types

    def test_zero_playerstats_detected(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_event_type_inventory

        result = run_event_type_inventory(exploration_con, output_dir=tmp_path)
        zps = result["zero_playerstats"]
        # All 5 replays with events have PlayerStats
        assert zps["zero_playerstats_replays"] == 0

    def test_event_density_by_year(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_event_type_inventory

        run_event_type_inventory(exploration_con, output_dir=tmp_path)
        df = pd.read_csv(tmp_path / "01_06_event_density_by_year.csv")
        expected_cols = {"year", "event_type", "avg_per_replay", "median_per_replay"}
        assert expected_cols.issubset(set(df.columns))
        years = set(df["year"].unique())
        assert 2020 in years or 2020.0 in years
        assert 2021 in years or 2021.0 in years

    def test_outlier_flagging(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_event_type_inventory

        run_event_type_inventory(exploration_con, output_dir=tmp_path)
        df = pd.read_csv(tmp_path / "01_06_event_density_by_tournament.csv")
        assert "is_outlier" in df.columns


# ── Step 1.7 tests ──────────────────────────────────────────────────────────


class TestPlayerStatsSampling:
    def test_sampling_deterministic(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_playerstats_sampling_check

        r1 = run_playerstats_sampling_check(exploration_con, output_dir=tmp_path)
        r2 = run_playerstats_sampling_check(exploration_con, output_dir=tmp_path)
        assert r1["per_game"] == r2["per_game"]

    def test_consistent_interval_no_flag(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_playerstats_sampling_check

        result = run_playerstats_sampling_check(exploration_con, output_dir=tmp_path)
        # 2020 games have 160-loop interval — should NOT be flagged
        flagged = result["flagged_years"]
        assert 2020 not in flagged

    def test_irregular_interval_flagged(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_playerstats_sampling_check

        result = run_playerstats_sampling_check(exploration_con, output_dir=tmp_path)
        # 2021 games have 240-loop interval — 50% deviation > 20% threshold
        flagged = result["flagged_years"]
        assert 2021 in flagged


# ── Orchestrator tests ──────────────────────────────────────────────────────


class TestOrchestrator:
    def test_orchestrator_all_steps(self, exploration_con, tmp_path):
        # Patch DATASET_REPORTS_DIR for test isolation
        import rts_predict.sc2.data.exploration as mod
        from rts_predict.sc2.data.exploration import run_phase_1_exploration
        original = mod.DATASET_REPORTS_DIR
        mod.DATASET_REPORTS_DIR = tmp_path
        try:
            results = run_phase_1_exploration(exploration_con)
            assert set(results.keys()) == {"1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7"}
        finally:
            mod.DATASET_REPORTS_DIR = original

    def test_orchestrator_selective(self, exploration_con, tmp_path):
        import rts_predict.sc2.data.exploration as mod
        from rts_predict.sc2.data.exploration import run_phase_1_exploration
        original = mod.DATASET_REPORTS_DIR
        mod.DATASET_REPORTS_DIR = tmp_path
        try:
            results = run_phase_1_exploration(exploration_con, steps=["1.1", "1.3"])
            assert set(results.keys()) == {"1.1", "1.3"}
        finally:
            mod.DATASET_REPORTS_DIR = original


# ── Edge-case coverage ───────────────────────────────────────────────────────


class TestSerializeValue:
    def test_numpy_scalar_converted(self) -> None:
        """_serialize_value must call .item() on numpy scalars."""
        from rts_predict.sc2.data.exploration import _serialize_value

        val = np.int64(42)
        result = _serialize_value(val)
        assert result == 42
        assert isinstance(result, int)

    def test_plain_python_passthrough(self) -> None:
        """_serialize_value must pass plain Python values through unchanged."""
        from rts_predict.sc2.data.exploration import _serialize_value

        assert _serialize_value(7) == 7
        assert _serialize_value("hello") == "hello"


class TestNearDuplicateDetection:
    def test_near_duplicates_included_in_md(self, tmp_path: Path) -> None:
        """When near-duplicates exist, their markdown table must appear in the report."""
        import json

        from rts_predict.sc2.data.exploration import run_corpus_summary

        con = duckdb.connect(":memory:")

        # Two rows with same players, same map, within 30s — near-duplicates
        rid_a = "aabbccdd11223344556677889900aa00"
        rid_b = "aabbccdd11223344556677889900aa01"

        raw_rows = []
        for rid, ts in [(rid_a, "2020-03-15T12:00:00"), (rid_b, "2020-03-15T12:00:25")]:
            raw_rows.append({
                "filename": f"T/T_data/{rid}.SC2Replay.json",
                "header": json.dumps({"elapsedGameLoops": 8000}),
                "initData": json.dumps({"gameDescription": {"mapSizeX": 200, "mapSizeY": 200}}),
                "details": json.dumps({"timeUTC": ts}),
                "metadata": json.dumps({
                    "dataBuild": "50012", "gameVersion": "5.0.12", "mapName": "Altitude LE"
                }),
                "ToonPlayerDescMap": _build_tpdm("Alpha", "Beta"),
            })

        raw_df = pd.DataFrame(raw_rows)  # noqa: F841
        con.execute("CREATE TABLE raw AS SELECT * FROM raw_df")
        con.execute("""
            CREATE OR REPLACE TABLE raw AS
            SELECT filename,
                header::JSON AS header,
                "initData"::JSON AS "initData",
                details::JSON AS details,
                metadata::JSON AS metadata,
                "ToonPlayerDescMap"::JSON AS "ToonPlayerDescMap"
            FROM raw
        """)

        # tracker_events_raw must exist for the query to work
        con.execute("""
            CREATE TABLE tracker_events_raw (
                match_id VARCHAR, event_type VARCHAR, player_id INTEGER, game_loop INTEGER
            )
        """)
        # match_player_map must exist
        con.execute("CREATE TABLE match_player_map (match_id VARCHAR, player_id INTEGER)")

        result = run_corpus_summary(con, output_dir=tmp_path)
        con.close()

        assert len(result["near_duplicates"]) > 0
        md = (tmp_path / "01_01_duplicate_detection.md").read_text()
        assert "Altitude LE" in md or "Alpha" in md


class TestPlayerStatsSamplingEmpty:
    def test_empty_tracker_returns_early(self, tmp_path: Path) -> None:
        """run_playerstats_sampling_check returns empty when no PlayerStats exist."""
        import json

        from rts_predict.sc2.data.exploration import run_playerstats_sampling_check

        con = duckdb.connect(":memory:")

        # raw with one replay
        rid = "aabbccdd11223344556677889900aa00"
        raw_df = pd.DataFrame([{  # noqa: F841
            "filename": f"T/T_data/{rid}.SC2Replay.json",
            "header": json.dumps({"elapsedGameLoops": 8000}),
            "initData": json.dumps({"gameDescription": {"mapSizeX": 200, "mapSizeY": 200}}),
            "details": json.dumps({"timeUTC": "2020-01-01T10:00:00"}),
            "metadata": json.dumps({
                "dataBuild": "50012", "gameVersion": "5.0.12", "mapName": "Map A"
            }),
            "ToonPlayerDescMap": json.dumps({}),
        }])
        con.execute("CREATE TABLE raw AS SELECT * FROM raw_df")
        con.execute("""
            CREATE OR REPLACE TABLE raw AS
            SELECT filename,
                header::JSON AS header,
                "initData"::JSON AS "initData",
                details::JSON AS details,
                metadata::JSON AS metadata,
                "ToonPlayerDescMap"::JSON AS "ToonPlayerDescMap"
            FROM raw
        """)
        # tracker_events_raw with no PlayerStats (only CameraUpdate)
        con.execute("""
            CREATE TABLE tracker_events_raw (
                match_id VARCHAR, event_type VARCHAR, player_id INTEGER, game_loop INTEGER
            )
        """)
        con.execute(
            "INSERT INTO tracker_events_raw VALUES "
            f"('{rid}.SC2Replay.json', 'CameraUpdate', 1, 100)"
        )

        result = run_playerstats_sampling_check(con, output_dir=tmp_path)
        con.close()

        assert result == {"per_game": [], "by_year": [], "flagged_years": []}
