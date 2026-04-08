"""Tests for Phase 1 — Corpus Inventory and Parse Quality (exploration.py).

Uses synthetic in-memory DuckDB fixtures to validate each step function.
"""

import json
from collections.abc import Generator
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
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
            assert set(results.keys()) == {
                "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.9"
            }
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


# ── Step 1.9 tests ──────────────────────────────────────────────────────────


class TestTpdmFieldInventory:
    def test_artifact_created(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_tpdm_field_inventory

        result = run_tpdm_field_inventory(exploration_con, output_dir=tmp_path)
        assert (tmp_path / "01_09_tpdm_field_inventory.csv").exists()
        assert result["row_count"] > 0

    def test_expected_keys_present(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_tpdm_field_inventory

        result = run_tpdm_field_inventory(exploration_con, output_dir=tmp_path)
        fields = result["fields"]
        for key in ("APM", "MMR", "nickname", "race", "result"):
            assert key in fields, f"Expected TPDM key '{key}' not found"

    def test_csv_non_empty(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_tpdm_field_inventory

        run_tpdm_field_inventory(exploration_con, output_dir=tmp_path)
        df = pd.read_csv(tmp_path / "01_09_tpdm_field_inventory.csv")
        assert len(df) > 0
        assert "json_key" in df.columns

    def test_artifact_path_returned(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_tpdm_field_inventory

        result = run_tpdm_field_inventory(exploration_con, output_dir=tmp_path)
        assert result["artifact_path"].endswith("01_09_tpdm_field_inventory.csv")


class TestTpdmKeySetConstancy:
    def test_artifact_created(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_tpdm_key_set_constancy

        result = run_tpdm_key_set_constancy(exploration_con, output_dir=tmp_path)
        assert (tmp_path / "01_09_tpdm_key_set_constancy.csv").exists()
        assert result["row_count"] > 0

    def test_csv_has_expected_columns(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_tpdm_key_set_constancy

        run_tpdm_key_set_constancy(exploration_con, output_dir=tmp_path)
        df = pd.read_csv(tmp_path / "01_09_tpdm_key_set_constancy.csv")
        assert "key_list" in df.columns
        assert "n_slots" in df.columns

    def test_gate_pass_flag_present(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_tpdm_key_set_constancy

        result = run_tpdm_key_set_constancy(exploration_con, output_dir=tmp_path)
        assert "gate_pass" in result
        assert isinstance(result["gate_pass"], bool)

    def test_dominant_coverage_reasonable(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_tpdm_key_set_constancy

        result = run_tpdm_key_set_constancy(exploration_con, output_dir=tmp_path)
        # Synthetic data uses a consistent key set, so dominant variant should be 100%
        assert result["dominant_coverage_pct"] == 100.0
        assert result["gate_pass"] is True

    def test_total_slots_matches_player_slots(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_tpdm_key_set_constancy

        result = run_tpdm_key_set_constancy(exploration_con, output_dir=tmp_path)
        # 6 rows * 2 players each = 12 player slots
        assert result["total_slots"] == 12

    def test_halt_predicate_false_for_constant_keyset(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_tpdm_key_set_constancy

        result = run_tpdm_key_set_constancy(exploration_con, output_dir=tmp_path)
        assert result["halt_predicate"] is False


class TestTopLevelFieldInventory:
    def test_artifact_created(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_toplevel_field_inventory

        result = run_toplevel_field_inventory(exploration_con, output_dir=tmp_path)
        assert (tmp_path / "01_09_toplevel_field_inventory.csv").exists()
        assert result["row_count"] > 0

    def test_csv_has_expected_columns(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_toplevel_field_inventory

        run_toplevel_field_inventory(exploration_con, output_dir=tmp_path)
        df = pd.read_csv(tmp_path / "01_09_toplevel_field_inventory.csv")
        assert "source_column" in df.columns
        assert "json_key" in df.columns

    def test_all_toplevel_columns_covered(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_toplevel_field_inventory

        result = run_toplevel_field_inventory(exploration_con, output_dir=tmp_path)
        by_col = result["by_column"]
        for col in ("header", "initData", "details", "metadata"):
            assert col in by_col, f"Expected column '{col}' in by_column"
            assert len(by_col[col]) > 0, f"Column '{col}' has no keys"

    def test_known_keys_present(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_toplevel_field_inventory

        result = run_toplevel_field_inventory(exploration_con, output_dir=tmp_path)
        by_col = result["by_column"]
        assert "elapsedGameLoops" in by_col["header"]
        assert "timeUTC" in by_col["details"]
        assert "mapName" in by_col["metadata"]

    def test_nested_keys_captured(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_toplevel_field_inventory

        run_toplevel_field_inventory(exploration_con, output_dir=tmp_path)
        df = pd.read_csv(tmp_path / "01_09_toplevel_field_inventory.csv")
        # initData.gameDescription nested keys should appear
        nested_sources = df[df["source_column"].str.contains("\\.", na=False)]["source_column"]
        assert len(nested_sources) > 0

    def test_artifact_path_returned(self, exploration_con, tmp_path):
        from rts_predict.sc2.data.exploration import run_toplevel_field_inventory

        result = run_toplevel_field_inventory(exploration_con, output_dir=tmp_path)
        assert result["artifact_path"].endswith("01_09_toplevel_field_inventory.csv")


class TestStep19Orchestration:
    def test_orchestrator_runs_step_1_9(self, exploration_con, tmp_path):
        import rts_predict.sc2.data.exploration as mod
        from rts_predict.sc2.data.exploration import run_phase_1_exploration

        original = mod.DATASET_REPORTS_DIR
        mod.DATASET_REPORTS_DIR = tmp_path
        try:
            results = run_phase_1_exploration(exploration_con, steps=["1.9"])
            assert "1.9" in results
            assert "1.9A" in results["1.9"]
            assert "1.9B" in results["1.9"]
            assert "1.9C" in results["1.9"]
        finally:
            mod.DATASET_REPORTS_DIR = original

    def test_orchestrator_runs_substep_1_9a(self, exploration_con, tmp_path):
        import rts_predict.sc2.data.exploration as mod
        from rts_predict.sc2.data.exploration import run_phase_1_exploration

        original = mod.DATASET_REPORTS_DIR
        mod.DATASET_REPORTS_DIR = tmp_path
        try:
            results = run_phase_1_exploration(exploration_con, steps=["1.9A"])
            assert set(results.keys()) == {"1.9A"}
            assert results["1.9A"]["row_count"] > 0
        finally:
            mod.DATASET_REPORTS_DIR = original

    def test_three_csvs_created_by_step_1_9(self, exploration_con, tmp_path):
        import rts_predict.sc2.data.exploration as mod
        from rts_predict.sc2.data.exploration import run_phase_1_exploration

        original = mod.DATASET_REPORTS_DIR
        mod.DATASET_REPORTS_DIR = tmp_path
        try:
            run_phase_1_exploration(exploration_con, steps=["1.9"])
        finally:
            mod.DATASET_REPORTS_DIR = original

        assert (tmp_path / "01_09_tpdm_field_inventory.csv").exists()
        assert (tmp_path / "01_09_tpdm_key_set_constancy.csv").exists()
        assert (tmp_path / "01_09_toplevel_field_inventory.csv").exists()
        # All must be non-empty
        for fname in [
            "01_09_tpdm_field_inventory.csv",
            "01_09_tpdm_key_set_constancy.csv",
            "01_09_toplevel_field_inventory.csv",
        ]:
            df = pd.read_csv(tmp_path / fname)
            assert len(df) > 0, f"{fname} must be non-empty"


# ── Step 1.9D/E/F SQL builder tests ─────────────────────────────────────────


class TestBuildEventDataFieldInventoryQuery:
    def test_no_sample_when_sample_size_zero(self) -> None:
        """When sample_size=0, the SQL must not contain a USING SAMPLE clause."""
        from rts_predict.sc2.data.exploration import build_event_data_field_inventory_query

        sql = build_event_data_field_inventory_query("tracker_events_raw", sample_size=0)
        assert "USING SAMPLE" not in sql.upper()

    def test_sample_clause_present_when_nonzero(self) -> None:
        """When sample_size=50000, the SQL must contain SAMPLE."""
        from rts_predict.sc2.data.exploration import build_event_data_field_inventory_query

        sql = build_event_data_field_inventory_query(
            "tracker_events_raw", sample_size=50_000
        )
        assert "SAMPLE" in sql.upper()
        assert "50000" in sql

    def test_table_name_injected(self) -> None:
        """The generated SQL must reference the provided table name."""
        from rts_predict.sc2.data.exploration import build_event_data_field_inventory_query

        sql = build_event_data_field_inventory_query("game_events_raw", sample_size=0)
        assert "game_events_raw" in sql

    def test_output_columns_present(self) -> None:
        """The SQL must select event_type, json_key, and is_nested."""
        from rts_predict.sc2.data.exploration import build_event_data_field_inventory_query

        sql = build_event_data_field_inventory_query("tracker_events_raw", sample_size=0)
        assert "event_type" in sql
        assert "json_key" in sql
        assert "is_nested" in sql


class TestBuildEventDataKeyConstancyQuery:
    def test_event_type_string_in_sql(self) -> None:
        """The generated SQL must contain the event_type value."""
        from rts_predict.sc2.data.exploration import build_event_data_key_constancy_query

        sql = build_event_data_key_constancy_query(
            "tracker_events_raw", "PlayerStats", sample_size=0
        )
        assert "PlayerStats" in sql

    def test_no_sample_when_size_zero(self) -> None:
        """When sample_size=0, SQL should not contain a USING SAMPLE clause."""
        from rts_predict.sc2.data.exploration import build_event_data_key_constancy_query

        sql = build_event_data_key_constancy_query(
            "tracker_events_raw", "UnitBorn", sample_size=0
        )
        assert "USING SAMPLE" not in sql.upper()

    def test_output_columns_present(self) -> None:
        """SQL must return key_list, n_events, pct."""
        from rts_predict.sc2.data.exploration import build_event_data_key_constancy_query

        sql = build_event_data_key_constancy_query(
            "tracker_events_raw", "UnitBorn", sample_size=0
        )
        assert "key_list" in sql
        assert "n_events" in sql
        assert "pct" in sql


class TestBuildNestedFieldInventoryQuery:
    def test_nested_key_in_sql(self) -> None:
        """The generated SQL must reference the nested_key."""
        from rts_predict.sc2.data.exploration import build_nested_field_inventory_query

        sql = build_nested_field_inventory_query(
            "tracker_events_raw", "PlayerStats", "stats", sample_size=0
        )
        assert "stats" in sql
        assert "PlayerStats" in sql

    def test_output_column_present(self) -> None:
        """SQL must return nested_key_name."""
        from rts_predict.sc2.data.exploration import build_nested_field_inventory_query

        sql = build_nested_field_inventory_query(
            "game_events_raw", "Cmd", "abil", sample_size=0
        )
        assert "nested_key_name" in sql


# ── Step 1.9F — verify_parquet_duckdb_schema_consistency tests ───────────────


def _make_event_data_parquet(
    tmp_path: Path,
    filename: str,
    columns: list[dict[str, Any]],
) -> Path:
    """Create a synthetic Parquet file with given schema."""
    fields = [pa.field(c["name"], pa.string()) for c in columns]
    schema = pa.schema(fields)
    arrays = {c["name"]: pa.array(["val"], type=pa.string()) for c in columns}
    table = pa.Table.from_pydict(arrays, schema=schema)
    pq_path = tmp_path / filename
    pq.write_table(table, pq_path)
    return pq_path


class TestVerifyParquetDuckdbSchemaConsistency:
    def test_empty_directory_returns_zero_batches(self, tmp_path: Path) -> None:
        """Empty staging directory must return n_batches_checked=0."""
        from rts_predict.sc2.data.exploration import (
            verify_parquet_duckdb_schema_consistency,
        )

        # Use a subdirectory with no parquet files
        empty_dir = tmp_path / "empty_staging"
        empty_dir.mkdir()

        # Create a minimal DuckDB with a dummy table
        db_path = tmp_path / "test.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute("CREATE TABLE tracker_events_raw (match_id VARCHAR, event_type VARCHAR)")
        con.close()

        result = verify_parquet_duckdb_schema_consistency(
            staging_dir=empty_dir,
            db_path=db_path,
            table_name="tracker_events_raw",
            batch_prefix="tracker_events_batch_",
            n_batches=5,
        )
        assert result["n_batches_checked"] == 0
        assert result["mismatches"] == []

    def test_schema_mismatch_detected(self, tmp_path: Path) -> None:
        """A Parquet file with an extra column must produce a non-empty mismatches list."""
        from rts_predict.sc2.data.exploration import (
            verify_parquet_duckdb_schema_consistency,
        )

        staging = tmp_path / "staging"
        staging.mkdir()

        # Create Parquet with extra column
        _make_event_data_parquet(
            staging,
            "tracker_events_batch_00000.parquet",
            [
                {"name": "match_id"},
                {"name": "event_type"},
                {"name": "game_loop"},
                {"name": "player_id"},
                {"name": "event_data"},
                {"name": "extra_column"},  # not in DuckDB
            ],
        )

        db_path = tmp_path / "test.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute("""
            CREATE TABLE tracker_events_raw (
                match_id VARCHAR,
                event_type VARCHAR,
                game_loop INTEGER,
                player_id TINYINT,
                event_data VARCHAR
            )
        """)
        con.close()

        result = verify_parquet_duckdb_schema_consistency(
            staging_dir=staging,
            db_path=db_path,
            table_name="tracker_events_raw",
            batch_prefix="tracker_events_batch_",
            n_batches=5,
        )
        assert len(result["mismatches"]) > 0
        assert any("extra_column" in str(m) for m in result["mismatches"])

    def test_consistent_schema_no_mismatches(self, tmp_path: Path) -> None:
        """Matching schemas must produce empty mismatches."""
        from rts_predict.sc2.data.exploration import (
            verify_parquet_duckdb_schema_consistency,
        )

        staging = tmp_path / "staging"
        staging.mkdir()

        cols = [
            {"name": "match_id"},
            {"name": "event_type"},
            {"name": "game_loop"},
            {"name": "player_id"},
            {"name": "event_data"},
        ]
        _make_event_data_parquet(
            staging, "tracker_events_batch_00000.parquet", cols
        )

        db_path = tmp_path / "test.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute("""
            CREATE TABLE tracker_events_raw (
                match_id VARCHAR,
                event_type VARCHAR,
                game_loop INTEGER,
                player_id TINYINT,
                event_data VARCHAR
            )
        """)
        con.close()

        result = verify_parquet_duckdb_schema_consistency(
            staging_dir=staging,
            db_path=db_path,
            table_name="tracker_events_raw",
            batch_prefix="tracker_events_batch_",
            n_batches=5,
        )
        assert result["mismatches"] == []
        assert result["n_batches_checked"] == 1


# ── compile_event_schema_document tests ──────────────────────────────────────


class TestCompileEventSchemaDocument:
    def _make_inventory(
        self, event_types: list[str], keys_per_type: list[str]
    ) -> pd.DataFrame:
        rows = []
        for et in event_types:
            for k in keys_per_type:
                rows.append({"event_type": et, "json_key": k, "is_nested": False})
        return pd.DataFrame(rows)

    def _make_constancy(self, event_types: list[str]) -> pd.DataFrame:
        return pd.DataFrame([
            {"event_type": et, "key_list": "['a', 'b']", "n_events": 1000, "pct": 99.5}
            for et in event_types
        ])

    def test_all_event_types_appear_in_output(self) -> None:
        """All event types from both inventories must appear in the markdown."""
        from rts_predict.sc2.data.exploration import (
            _GAME_EVENT_TYPES_FOR_CONSTANCY,
            compile_event_schema_document,
        )

        tracker_types = ["PlayerStats", "UnitBorn", "UnitDied", "Upgrade", "PlayerSetup",
                         "UnitInit", "UnitDone", "UnitPositions", "UnitOwnerChange",
                         "UnitTypeChange"]
        tracker_inv = self._make_inventory(tracker_types, ["evtTypeName", "id", "loop"])
        tracker_con = self._make_constancy(tracker_types)

        game_inv = self._make_inventory(list(_GAME_EVENT_TYPES_FOR_CONSTANCY), ["id", "loop"])
        game_con = self._make_constancy(list(_GAME_EVENT_TYPES_FOR_CONSTANCY))

        md = compile_event_schema_document(
            tracker_inv, game_inv, tracker_con, game_con
        )

        for et in tracker_types:
            assert et in md, f"Tracker event type '{et}' not found in schema doc"
        for et in _GAME_EVENT_TYPES_FOR_CONSTANCY:
            assert et in md, f"Game event type '{et}' not found in schema doc"

    def test_dominant_coverage_included(self) -> None:
        """The dominant coverage percentage must appear in the doc."""
        from rts_predict.sc2.data.exploration import compile_event_schema_document

        inv = self._make_inventory(["PlayerStats"], ["evtTypeName", "stats"])
        inv.loc[inv["json_key"] == "stats", "is_nested"] = True
        con = self._make_constancy(["PlayerStats"])

        empty_game_inv: pd.DataFrame = pd.DataFrame(
            columns=["event_type", "json_key", "is_nested"]
        )
        empty_game_con: pd.DataFrame = pd.DataFrame(
            columns=["event_type", "key_list", "n_events", "pct"]
        )

        md = compile_event_schema_document(inv, empty_game_inv, con, empty_game_con)
        assert "99.5" in md

    def test_empty_inventories_produce_valid_markdown(self) -> None:
        """Empty DataFrames must not raise and must produce headers."""
        from rts_predict.sc2.data.exploration import compile_event_schema_document

        empty: pd.DataFrame = pd.DataFrame(
            columns=["event_type", "json_key", "is_nested"]
        )
        empty_con: pd.DataFrame = pd.DataFrame(
            columns=["event_type", "key_list", "n_events", "pct"]
        )

        md = compile_event_schema_document(empty, empty, empty_con, empty_con)
        assert "# Event Data Schema Reference" in md
        assert "Tracker Events" in md
        assert "Game Events" in md


# ── Synthetic event_data fixture ─────────────────────────────────────────────


@pytest.fixture()
def event_data_con() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """In-memory DuckDB with event_data JSON for 1.9D/E tests.

    tracker_events_raw: PlayerStats (consistent key set) + UnitBorn (consistent).
    game_events_raw: Cmd + SelectionDelta + ControlGroupUpdate + CmdUpdateTargetPoint
                     + CmdUpdateTargetUnit.
    """
    con = duckdb.connect(":memory:")

    ps_data = json.dumps({
        "evtTypeName": "PlayerStats", "id": 0, "loop": 160, "playerId": 1,
        "stats": {"scoreValueMineralsCollectionRate": 100, "scoreValueFoodMade": 15},
    })
    ub_data = json.dumps({
        "evtTypeName": "UnitBorn", "id": 1, "loop": 0,
        "unitTagIndex": 1, "unitTagRecycle": 1,
        "unitTypeName": "SCV", "controlPlayerId": 1, "upkeepPlayerId": 1,
        "x": 10, "y": 20,
    })

    tracker_rows = []
    for i in range(20):
        tracker_rows.append({"match_id": f"m{i}.json", "event_type": "PlayerStats",
                              "game_loop": 160 * (i + 1), "player_id": 1, "event_data": ps_data})
        tracker_rows.append({"match_id": f"m{i}.json", "event_type": "UnitBorn",
                              "game_loop": i * 10, "player_id": 1, "event_data": ub_data})

    tracker_df = pd.DataFrame(tracker_rows)  # noqa: F841
    con.execute("CREATE TABLE tracker_events_raw AS SELECT * FROM tracker_df")

    cmd_data = json.dumps({
        "evtTypeName": "Cmd", "id": 27, "loop": 15,
        "abil": {"abilCmdData": None, "abilCmdIndex": 0, "abilLink": 147},
        "cmdFlags": ["User"],
        "data": {"None": None},
        "otherUnit": None, "sequence": 1, "unitGroup": None,
        "userid": {"userId": 1},
    })
    sd_data = json.dumps({
        "evtTypeName": "SelectionDelta", "id": 28, "loop": 15,
        "controlGroupId": 10,
        "delta": {"addSubgroups": [], "addUnitTags": [1234], "removeMask": {"None": None},
                  "subgroupIndex": 0},
        "userid": {"userId": 1},
    })
    cg_data = json.dumps({
        "evtTypeName": "ControlGroupUpdate", "id": 29, "loop": 35,
        "controlGroupIndex": 1, "controlGroupUpdate": 0,
        "mask": {"None": None}, "userid": {"userId": 1},
    })
    cutp_data = json.dumps({
        "evtTypeName": "CmdUpdateTargetPoint", "id": 104, "loop": 41,
        "target": {"x": 71.5, "y": 74.7, "z": 5.9}, "userid": {"userId": 1},
    })
    cutu_data = json.dumps({
        "evtTypeName": "CmdUpdateTargetUnit", "id": 105, "loop": 27,
        "target": {"snapshotControlPlayerId": 0, "tag": 125, "targetUnitFlags": 111, "timer": 0},
        "userid": {"userId": 1},
    })

    game_rows = []
    for data, et in [
        (cmd_data, "Cmd"), (sd_data, "SelectionDelta"), (cg_data, "ControlGroupUpdate"),
        (cutp_data, "CmdUpdateTargetPoint"), (cutu_data, "CmdUpdateTargetUnit"),
    ]:
        for i in range(10):
            game_rows.append({
                "match_id": f"m{i}.json", "event_type": et,
                "game_loop": i * 10, "user_id": 1, "player_id": 1,
                "event_data": data,
            })

    game_df = pd.DataFrame(game_rows)  # noqa: F841
    con.execute("CREATE TABLE game_events_raw AS SELECT * FROM game_df")

    yield con
    con.close()


class TestRunTrackerEventDataInventory:
    def test_artifacts_created(self, event_data_con, tmp_path):
        """run_tracker_event_data_inventory must write all three CSVs."""
        from rts_predict.sc2.data.exploration import run_tracker_event_data_inventory

        result = run_tracker_event_data_inventory(
            event_data_con, output_dir=tmp_path, sample_size=0
        )

        assert (tmp_path / "01_09D_tracker_event_data_field_inventory.csv").exists()
        assert (tmp_path / "01_09D_tracker_event_data_key_constancy.csv").exists()
        assert (tmp_path / "01_09D_playerstats_stats_field_inventory.csv").exists()
        assert "event_types" in result
        assert "PlayerStats" in result["event_types"]

    def test_gate_pass_when_all_dominant(self, event_data_con, tmp_path):
        """With consistent key sets, gate_pass should be True."""
        from rts_predict.sc2.data.exploration import run_tracker_event_data_inventory

        result = run_tracker_event_data_inventory(
            event_data_con, output_dir=tmp_path, sample_size=0
        )
        # Synthetic data has perfectly consistent key sets
        assert result["gate_pass"] is True
        assert result["gate_violations"] == []

    def test_nested_stats_keys_found(self, event_data_con, tmp_path):
        """PlayerStats.stats nested keys must be enumerated."""
        from rts_predict.sc2.data.exploration import run_tracker_event_data_inventory

        run_tracker_event_data_inventory(
            event_data_con, output_dir=tmp_path, sample_size=0
        )
        nested_df = pd.read_csv(tmp_path / "01_09D_playerstats_stats_field_inventory.csv")
        assert len(nested_df) > 0
        assert "nested_key_name" in nested_df.columns


class TestRunGameEventDataInventory:
    def test_artifacts_created(self, event_data_con, tmp_path):
        """run_game_event_data_inventory must write both CSVs."""
        from rts_predict.sc2.data.exploration import run_game_event_data_inventory

        result = run_game_event_data_inventory(
            event_data_con, output_dir=tmp_path, sample_size=0
        )

        assert (tmp_path / "01_09E_game_event_data_field_inventory.csv").exists()
        assert (tmp_path / "01_09E_game_event_data_key_constancy.csv").exists()
        assert "gate_pass" in result

    def test_gate_pass_with_consistent_keys(self, event_data_con, tmp_path):
        """Synthetic data with consistent key sets must pass 95% gate."""
        from rts_predict.sc2.data.exploration import run_game_event_data_inventory

        result = run_game_event_data_inventory(
            event_data_con, output_dir=tmp_path, sample_size=0
        )
        assert result["gate_pass"] is True

    def test_nested_sub_objects_enumerated(self, event_data_con, tmp_path):
        """Cmd.abil and SelectionDelta.delta nested keys must appear in inventory."""
        from rts_predict.sc2.data.exploration import run_game_event_data_inventory

        run_game_event_data_inventory(
            event_data_con, output_dir=tmp_path, sample_size=0
        )
        inv = pd.read_csv(tmp_path / "01_09E_game_event_data_field_inventory.csv")
        # Nested supplement rows should include abil.* sub-keys
        cmd_rows = inv[inv["event_type"] == "Cmd"]
        assert len(cmd_rows) > 0


class TestRunParquetDuckdbReconciliation:
    def test_reconciliation_with_matching_schema(self, tmp_path):
        """Reconciliation with matching schemas must write the markdown report."""
        from rts_predict.sc2.data.exploration import run_parquet_duckdb_reconciliation

        staging = tmp_path / "staging"
        staging.mkdir()

        # Create matching tracker Parquet
        _make_event_data_parquet(
            staging,
            "tracker_events_batch_00000.parquet",
            [{"name": c} for c in ["match_id", "event_type", "game_loop", "player_id",
                                    "event_data"]],
        )
        _make_event_data_parquet(
            staging,
            "game_events_batch_00000.parquet",
            [{"name": c} for c in ["match_id", "event_type", "game_loop", "user_id",
                                    "player_id", "event_data"]],
        )

        db_path = tmp_path / "db.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute(
            "CREATE TABLE tracker_events_raw "
            "(match_id VARCHAR, event_type VARCHAR, game_loop INTEGER, "
            "player_id TINYINT, event_data VARCHAR)"
        )
        con.execute(
            "CREATE TABLE game_events_raw "
            "(match_id VARCHAR, event_type VARCHAR, game_loop INTEGER, "
            "user_id INTEGER, player_id TINYINT, event_data VARCHAR)"
        )
        con.close()

        # Monkeypatch DB_FILE and IN_GAME_PARQUET_DIR
        import rts_predict.sc2.config as cfg_mod
        import rts_predict.sc2.data.exploration as mod

        orig_db = cfg_mod.DB_FILE
        orig_staging = cfg_mod.IN_GAME_PARQUET_DIR
        cfg_mod.DB_FILE = db_path
        cfg_mod.IN_GAME_PARQUET_DIR = staging
        try:
            result = run_parquet_duckdb_reconciliation(output_dir=tmp_path)
        finally:
            cfg_mod.DB_FILE = orig_db
            cfg_mod.IN_GAME_PARQUET_DIR = orig_staging

        assert (tmp_path / "01_09F_parquet_duckdb_schema_reconciliation.md").exists()
        assert result["gate_pass"] is True
        assert result["tracker"]["n_batches_checked"] >= 1
        _ = mod  # suppress F841


class TestRunEventSchemaDocument:
    def test_schema_doc_written_from_csvs(self, tmp_path):
        """run_event_schema_document must write the reference markdown."""
        from rts_predict.sc2.data.exploration import (
            run_event_schema_document,
            run_game_event_data_inventory,
            run_tracker_event_data_inventory,
        )

        # Build synthetic DB
        con = duckdb.connect(":memory:")
        ps_data = json.dumps({"evtTypeName": "PlayerStats", "stats": {"val": 1}})
        cmd_data = json.dumps({"evtTypeName": "Cmd", "abil": {"abilLink": 1}, "loop": 1})
        sd_data = json.dumps({"evtTypeName": "SelectionDelta", "delta": {"addUnitTags": []},
                               "controlGroupId": 1, "loop": 1, "userid": {"userId": 1}})
        cg_data = json.dumps({"evtTypeName": "ControlGroupUpdate", "controlGroupIndex": 1,
                               "controlGroupUpdate": 0, "loop": 1})
        cutp_data = json.dumps({"evtTypeName": "CmdUpdateTargetPoint",
                                 "target": {"x": 1.0}, "loop": 1})
        cutu_data = json.dumps({"evtTypeName": "CmdUpdateTargetUnit",
                                 "target": {"tag": 1}, "loop": 1})

        tracker_rows = [
            {"match_id": "m.json", "event_type": "PlayerStats", "game_loop": 160,
             "player_id": 1, "event_data": ps_data},
        ]
        game_rows = [
            {"match_id": "m.json", "event_type": "Cmd", "game_loop": 1,
             "user_id": 1, "player_id": 1, "event_data": cmd_data},
            {"match_id": "m.json", "event_type": "SelectionDelta", "game_loop": 1,
             "user_id": 1, "player_id": 1, "event_data": sd_data},
            {"match_id": "m.json", "event_type": "ControlGroupUpdate", "game_loop": 1,
             "user_id": 1, "player_id": 1, "event_data": cg_data},
            {"match_id": "m.json", "event_type": "CmdUpdateTargetPoint", "game_loop": 1,
             "user_id": 1, "player_id": 1, "event_data": cutp_data},
            {"match_id": "m.json", "event_type": "CmdUpdateTargetUnit", "game_loop": 1,
             "user_id": 1, "player_id": 1, "event_data": cutu_data},
        ]
        t_df = pd.DataFrame(tracker_rows)  # noqa: F841
        g_df = pd.DataFrame(game_rows)  # noqa: F841
        con.execute("CREATE TABLE tracker_events_raw AS SELECT * FROM t_df")
        con.execute("CREATE TABLE game_events_raw AS SELECT * FROM g_df")

        run_tracker_event_data_inventory(con, output_dir=tmp_path, sample_size=0)
        run_game_event_data_inventory(con, output_dir=tmp_path, sample_size=0)
        con.close()

        result = run_event_schema_document(output_dir=tmp_path)
        assert (tmp_path / "01_09F_event_schema_reference.md").exists()
        assert result["gate_pass"] is True
        md = (tmp_path / "01_09F_event_schema_reference.md").read_text()
        assert "PlayerStats" in md
        assert "Cmd" in md
