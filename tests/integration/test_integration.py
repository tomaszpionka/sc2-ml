"""Integration smoke tests: verify the full pipeline chain works end-to-end.

These tests cover the flow: ingestion → processing → feature engineering → model input.
They use both the sample replay file and synthetic fixtures.
"""

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from sc2ml.data.processing import (
    assign_series_ids,
    create_ml_views,
    create_raw_enriched_view,
    create_temporal_split,
    get_matches_dataframe,
)
from sc2ml.features import build_features, split_for_ml
from sc2ml.features.group_e_context import _parse_patch_version

SAMPLE_REPLAY_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "src" / "sc2ml" / "data" / "samples" / "raw"
    / "0e0b1a550447f0b0a616e48224b31bd9.SC2Replay.json"
)


@pytest.fixture()
def raw_con() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with sample replay loaded into a ``raw`` table."""
    con = duckdb.connect(":memory:")

    with open(SAMPLE_REPLAY_PATH) as f:
        replay = json.load(f)

    # Build a row matching the structure produced by move_data_to_duck_db
    row = {
        "filename": "2016_IEM_10_Taipei/2016_IEM_10_Taipei_data/sample.SC2Replay.json",
        "header": json.dumps(replay["header"]),
        "initData": json.dumps(replay["initData"]),
        "details": json.dumps(replay["details"]),
        "metadata": json.dumps(replay["metadata"]),
        "ToonPlayerDescMap": json.dumps(replay["ToonPlayerDescMap"]),
    }
    df = pd.DataFrame([row])  # noqa: F841
    con.execute("CREATE TABLE raw AS SELECT * FROM df")
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

    # Map translation table (empty — Central Protocol is already English)
    con.execute(
        "CREATE TABLE map_translation (foreign_name VARCHAR, english_name VARCHAR)"
    )

    create_raw_enriched_view(con)

    yield con
    con.close()


@pytest.fixture()
def synthetic_pipeline_con() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with enough synthetic matches for a full pipeline run.

    Creates 60 matches with proper raw table structure, processes through
    views, series, and temporal split.
    """
    con = duckdb.connect(":memory:")
    rng = np.random.default_rng(42)

    players = [f"player_{i}" for i in range(10)]
    races = ["Terr", "Prot", "Zerg"]  # Abbreviated — SQL view normalizes
    # 20 tournaments (3 matches each) for clean 80/15/5 tournament-level splitting
    tournaments = [f"2023_T{i:02d}" for i in range(20)]
    maps = ["Altitude LE", "Berlingrad LE"]

    rows = []
    base_time = pd.Timestamp("2023-01-01 10:00:00")
    for i in range(60):
        p1_idx = rng.integers(0, 10)
        p2_idx = (p1_idx + rng.integers(1, 10)) % 10
        p1, p2 = players[p1_idx], players[p2_idx]
        r1, r2 = rng.choice(races), rng.choice(races)
        result = rng.choice(["Win", "Loss"])
        ts = base_time + pd.Timedelta(hours=int(i * 12))
        # Assign tournaments chronologically (3 matches per tournament)
        tourn = tournaments[i // 3]
        map_name = rng.choice(maps)

        tpdm = {
            "toon-1": {
                "nickname": p1, "playerID": 1, "userID": 1,
                "SQ": int(rng.integers(30, 100)), "APM": int(rng.integers(80, 350)),
                "supplyCappedPercent": int(rng.integers(0, 30)),
                "startLocX": int(rng.integers(10, 100)),
                "startLocY": int(rng.integers(10, 100)),
                "race": r1, "MMR": 0, "result": result, "isInClan": False,
            },
            "toon-2": {
                "nickname": p2, "playerID": 2, "userID": 2,
                "SQ": int(rng.integers(30, 100)), "APM": int(rng.integers(80, 350)),
                "supplyCappedPercent": int(rng.integers(0, 30)),
                "startLocX": int(rng.integers(10, 100)),
                "startLocY": int(rng.integers(10, 100)),
                "race": r2, "MMR": 0,
                "result": "Loss" if result == "Win" else "Win",
                "isInClan": False,
            },
        }

        rows.append({
            "filename": f"{tourn}/{tourn}_data/match_{i:04d}.SC2Replay.json",
            "header": json.dumps({"elapsedGameLoops": int(rng.integers(3000, 20000))}),
            "initData": json.dumps({
                "gameDescription": {"mapSizeX": 200, "mapSizeY": 200},
            }),
            "details": json.dumps({"timeUTC": ts.isoformat()}),
            "metadata": json.dumps({
                "dataBuild": "39948",
                "gameVersion": "3.1.1.39948",
                "mapName": map_name,
            }),
            "ToonPlayerDescMap": json.dumps(tpdm),
        })

    df = pd.DataFrame(rows)  # noqa: F841
    con.execute("CREATE TABLE raw AS SELECT * FROM df")
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
    con.execute(
        "CREATE TABLE map_translation (foreign_name VARCHAR, english_name VARCHAR)"
    )

    # Run full processing chain
    create_raw_enriched_view(con)
    create_ml_views(con)
    assign_series_ids(con)
    create_temporal_split(con)

    yield con
    con.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestIngestionToProcessingChain:
    """Verify sample replay → raw table → ML views → series → split."""

    def test_create_ml_views_from_sample(self, raw_con: duckdb.DuckDBPyConnection) -> None:
        create_ml_views(raw_con)

        fp_count = raw_con.execute("SELECT count(*) FROM flat_players").fetchone()[0]
        assert fp_count == 2  # sOs + ByuN

        mf_count = raw_con.execute("SELECT count(*) FROM matches_flat").fetchone()[0]
        assert mf_count == 2  # 2 perspectives

    def test_full_chain_creates_all_tables(
        self, raw_con: duckdb.DuckDBPyConnection
    ) -> None:
        create_ml_views(raw_con)
        assign_series_ids(raw_con)
        create_temporal_split(raw_con)

        tables = raw_con.execute(
            "SELECT table_name FROM information_schema.tables"
        ).fetchall()
        table_names = {t[0] for t in tables}
        assert "flat_players" in table_names
        assert "matches_flat" in table_names
        assert "match_series" in table_names
        assert "match_split" in table_names

    def test_get_matches_dataframe_has_split(
        self, raw_con: duckdb.DuckDBPyConnection
    ) -> None:
        create_ml_views(raw_con)
        assign_series_ids(raw_con)
        create_temporal_split(raw_con)
        df = get_matches_dataframe(raw_con)
        assert "split" in df.columns


class TestRaceNormalization:
    """Verify abbreviated race names are expanded in the SQL view."""

    def test_sample_replay_races_normalized(
        self, raw_con: duckdb.DuckDBPyConnection
    ) -> None:
        create_ml_views(raw_con)
        races = raw_con.execute(
            "SELECT DISTINCT race FROM flat_players"
        ).fetchall()
        race_set = {r[0] for r in races}
        # sOs is Protoss, ByuN is Terran — both should be full names
        assert "Protoss" in race_set
        assert "Terran" in race_set
        assert "Prot" not in race_set
        assert "Terr" not in race_set

    def test_synthetic_races_normalized(
        self, synthetic_pipeline_con: duckdb.DuckDBPyConnection
    ) -> None:
        races = synthetic_pipeline_con.execute(
            "SELECT DISTINCT p1_race FROM matches_flat"
        ).fetchall()
        race_set = {r[0] for r in races}
        assert race_set.issubset({"Terran", "Protoss", "Zerg"})


class TestGameVersionParsing:
    """Verify real gameVersion format produces useful patch_version_numeric."""

    def test_real_game_version_parses(self) -> None:
        assert _parse_patch_version("3.1.1.39948") == 30101

    def test_plain_build_id_returns_zero(self) -> None:
        assert _parse_patch_version("39948") == 0

    def test_game_version_in_views(
        self, raw_con: duckdb.DuckDBPyConnection
    ) -> None:
        create_ml_views(raw_con)
        gv = raw_con.execute(
            "SELECT game_version FROM flat_players LIMIT 1"
        ).fetchone()[0]
        assert gv == "3.1.1.39948"


class TestProcessingToFeaturesColumnContract:
    """Verify matches_flat output has all columns required by feature groups."""

    def test_all_required_columns_present(
        self, synthetic_pipeline_con: duckdb.DuckDBPyConnection
    ) -> None:
        df = get_matches_dataframe(synthetic_pipeline_con)

        # Group A (Elo)
        for col in ["match_id", "p1_name", "p2_name", "p1_result", "match_time"]:
            assert col in df.columns, f"Missing Group A column: {col}"

        # Group B (Historical)
        for col in ["p1_apm", "p2_apm", "p1_sq", "p2_sq",
                     "p1_supply_capped_pct", "p2_supply_capped_pct", "game_loops"]:
            assert col in df.columns, f"Missing Group B column: {col}"

        # Group C (Matchup/Map)
        for col in ["p1_startLocX", "p1_startLocY", "p2_startLocX", "p2_startLocY",
                     "map_size_x", "map_size_y", "map_name", "p1_race", "p2_race"]:
            assert col in df.columns, f"Missing Group C column: {col}"

        # Group D (Form) — uses match_time (already checked)

        # Group E (Context)
        for col in ["data_build", "game_version", "tournament_name"]:
            assert col in df.columns, f"Missing Group E column: {col}"

    def test_build_features_completes(
        self, synthetic_pipeline_con: duckdb.DuckDBPyConnection
    ) -> None:
        df = get_matches_dataframe(synthetic_pipeline_con)
        series_df = synthetic_pipeline_con.execute(
            "SELECT match_id, series_id FROM match_series"
        ).df()
        result = build_features(df, series_df=series_df)
        assert len(result) == len(df)
        assert "target" in result.columns


class TestFeaturesToModelCompatibility:
    """Verify feature output is compatible with sklearn model training."""

    def test_split_produces_clean_matrices(
        self, synthetic_pipeline_con: duckdb.DuckDBPyConnection
    ) -> None:
        df = get_matches_dataframe(synthetic_pipeline_con)
        series_df = synthetic_pipeline_con.execute(
            "SELECT match_id, series_id FROM match_series"
        ).df()
        features_df = build_features(df, series_df=series_df)
        X_train, X_val, X_test, y_train, y_val, y_test = split_for_ml(features_df)

        # No string columns in feature matrices
        for name, X in [("train", X_train), ("val", X_val), ("test", X_test)]:
            str_cols = X.select_dtypes(include="object").columns.tolist()
            assert len(str_cols) == 0, f"String columns in X_{name}: {str_cols}"

        # No NaN/Inf
        for name, X in [("train", X_train), ("val", X_val), ("test", X_test)]:
            assert not X.isna().any().any(), f"NaN in X_{name}"
            assert np.isfinite(X.values).all(), f"Inf in X_{name}"

        # Target is binary
        for name, y in [("train", y_train), ("val", y_val), ("test", y_test)]:
            assert set(y.unique()).issubset({0, 1}), f"Non-binary target in y_{name}"

        # Column sets are identical
        assert list(X_train.columns) == list(X_val.columns)
        assert list(X_train.columns) == list(X_test.columns)


class TestFullPipelineSmoke:
    """End-to-end: raw table → features → LogisticRegression trains."""

    def test_logistic_regression_trains(
        self, synthetic_pipeline_con: duckdb.DuckDBPyConnection
    ) -> None:
        df = get_matches_dataframe(synthetic_pipeline_con)
        series_df = synthetic_pipeline_con.execute(
            "SELECT match_id, series_id FROM match_series"
        ).df()
        features_df = build_features(df, series_df=series_df)
        X_train, X_val, X_test, y_train, y_val, y_test = split_for_ml(features_df)

        lr = Pipeline([
            ("scaler", StandardScaler()),
            ("lr", LogisticRegression(max_iter=1000, random_state=42)),
        ])
        lr.fit(X_train, y_train)

        train_acc = lr.score(X_train, y_train)
        assert 0.0 <= train_acc <= 1.0

        # Model should produce predictions without error on all splits
        for X in [X_val, X_test]:
            preds = lr.predict(X)
            assert len(preds) == len(X)
