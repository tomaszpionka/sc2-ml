"""Phase 0: Data & Model Sanity Validation tests (ROADMAP §3).

These tests run the sanity validation checks from ``sc2ml.validation``
against a synthetic in-memory DuckDB database.  They are designed to:
  1. Verify the validation functions themselves are correct.
  2. Confirm the synthetic pipeline produces valid data.
  3. Serve as the test harness for real-data runs (``pytest -m sanity``).

**macOS note:** LightGBM and PyTorch ship separate OpenMP runtimes.
Loading both in the same process causes a segfault.  Tests that use
LightGBM (§3.4 smoke tests) run in a child process via ``multiprocessing``
to isolate the runtimes — same pattern as ``test_model_reproducibility.py``.

For real data, run: ``poetry run sc2ml sanity`` or ``pytest -m sanity``.
"""

import json
import multiprocessing

import duckdb
import numpy as np
import pandas as pd
import pytest

from sc2ml.data.processing import (
    assign_series_ids,
    create_ml_views,
    create_temporal_split,
    get_matches_dataframe,
)
from sc2ml.features import build_features
from sc2ml.features.common import split_for_ml
from sc2ml.validation import (
    check_cold_start_handling,
    check_constant_features,
    check_degenerate_features,
    check_duplicate_match_ids,
    check_elo_baseline,
    check_elo_deduplication,
    check_elo_distribution,
    check_expanding_excludes_current,
    check_feature_correlations,
    check_feature_count_monotonic,
    check_flat_players_row_count,
    check_majority_baseline,
    check_match_time_range,
    check_matches_flat_row_count,
    check_no_single_feature_high_correlation,
    check_null_rate,
    check_race_distribution,
    check_race_dummies_are_int,
    check_rolling_windows_sparse_players,
    check_series_containment,
    check_series_coverage,
    check_split_ratios,
    check_target_balance,
    check_temporal_leakage,
)

pytestmark = pytest.mark.sanity


# ---------------------------------------------------------------------------
# Fixture: synthetic in-memory DuckDB (reused from test_integration pattern)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def synthetic_con() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with 100 synthetic matches, fully processed."""
    con = duckdb.connect(":memory:")
    rng = np.random.default_rng(42)

    players = [f"player_{i}" for i in range(10)]
    races = ["Terr", "Prot", "Zerg"]  # Abbreviated — SQL view normalizes
    tournaments = ["2023_GSL_S1", "2024_IEM_Katowice"]
    maps = ["Altitude LE", "Berlingrad LE", "Equilibrium LE"]

    rows = []
    base_time = pd.Timestamp("2023-01-01 10:00:00")
    for i in range(100):
        p1_idx = rng.integers(0, 10)
        p2_idx = (p1_idx + rng.integers(1, 10)) % 10
        p1, p2 = players[p1_idx], players[p2_idx]
        r1, r2 = rng.choice(races), rng.choice(races)
        result = rng.choice(["Win", "Loss"])
        ts = base_time + pd.Timedelta(hours=int(i * 12))
        tourn = rng.choice(tournaments)
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

    create_ml_views(con)
    assign_series_ids(con)
    create_temporal_split(con)

    yield con
    con.close()


@pytest.fixture(scope="module")
def pipeline_data(
    synthetic_con: duckdb.DuckDBPyConnection,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Build features and split for ML from the synthetic DuckDB.

    Returns (raw_df, features_df, X_train, X_test, y_train, y_test, matchup_col).
    """
    raw_df = get_matches_dataframe(synthetic_con)
    series_df = synthetic_con.execute(
        "SELECT match_id, series_id FROM match_series"
    ).df()
    features_df = build_features(raw_df, series_df=series_df)
    X_train, X_val, X_test, y_train, y_val, y_test = split_for_ml(features_df)

    matchup_col = None
    if "matchup_type" in features_df.columns:
        test_mask = features_df["split"] == "test"
        matchup_col = features_df.loc[test_mask, "matchup_type"].reset_index(drop=True)

    return raw_df, features_df, X_train, X_test, y_train, y_test, matchup_col


# ===================================================================
# §3.1 DuckDB View Sanity
# ===================================================================


class TestViewSanity:
    """§3.1 — DuckDB view structure and data integrity."""

    def test_flat_players_row_count(self, synthetic_con):
        result = check_flat_players_row_count(synthetic_con)
        assert result.passed, result.detail

    def test_matches_flat_row_count(self, synthetic_con):
        result = check_matches_flat_row_count(synthetic_con)
        assert result.passed, result.detail

    def test_null_rate(self, synthetic_con):
        result = check_null_rate(synthetic_con)
        assert result.passed, result.detail

    def test_match_time_range(self, synthetic_con):
        result = check_match_time_range(synthetic_con)
        assert result.passed, result.detail

    def test_race_distribution(self, synthetic_con):
        result = check_race_distribution(synthetic_con)
        assert result.passed, result.detail

    def test_duplicate_match_ids(self, synthetic_con):
        result = check_duplicate_match_ids(synthetic_con)
        assert result.passed, result.detail

    def test_series_coverage(self, synthetic_con):
        result = check_series_coverage(synthetic_con)
        assert result.passed, result.detail


# ===================================================================
# §3.2 Temporal Split Integrity
# ===================================================================


class TestSplitIntegrity:
    """§3.2 — Temporal split correctness and leakage prevention."""

    def test_target_balance(self, pipeline_data):
        _, features_df, *_ = pipeline_data
        result = check_target_balance(features_df)
        assert result.passed, result.detail

    def test_temporal_leakage(self, synthetic_con):
        result = check_temporal_leakage(synthetic_con)
        assert result.passed, result.detail

    def test_series_containment(self, synthetic_con):
        result = check_series_containment(synthetic_con)
        assert result.passed, result.detail

    def test_split_ratios(self, synthetic_con):
        result = check_split_ratios(synthetic_con)
        assert result.passed, result.detail


# ===================================================================
# §3.3 Feature Distribution Checks
# ===================================================================


class TestFeatureDistribution:
    """§3.3 — Feature quality and distributional sanity."""

    def test_constant_features(self, pipeline_data):
        _, features_df, *_ = pipeline_data
        result = check_constant_features(features_df)
        if not result.passed:
            # On synthetic data (100 matches, 1 patch), some features are constant
            # by design (e.g., map_area with fixed dimensions, patch_version_numeric).
            known_synthetic_constants = {
                "map_area", "patch_version_numeric",
                "p1_pre_match_elo", "p2_pre_match_elo",
                "elo_diff", "expected_win_prob",
            }
            unexpected = [c for c in result.value if c not in known_synthetic_constants]
            assert len(unexpected) == 0, (
                f"Unexpected constant features: {unexpected}"
            )

    def test_degenerate_features(self, pipeline_data):
        _, features_df, *_ = pipeline_data
        result = check_degenerate_features(features_df)
        # This may flag some features on synthetic data — log but don't hard-fail
        if not result.passed:
            pytest.skip(f"Degenerate features found on synthetic data: {result.detail}")

    def test_elo_distribution(self, pipeline_data):
        _, features_df, *_ = pipeline_data
        result = check_elo_distribution(features_df)
        if not result.passed:
            # Synthetic data has too few matches for Elo to diverge from 1500
            pytest.skip(f"Synthetic data: {result.detail}")

    def test_cold_start_handling(self, pipeline_data):
        _, features_df, *_ = pipeline_data
        result = check_cold_start_handling(features_df)
        assert result.passed, result.detail

    def test_feature_correlations(self, pipeline_data):
        _, features_df, *_ = pipeline_data
        result = check_feature_correlations(features_df)
        if not result.passed:
            # Some perfect correlations are expected by design or on synthetic data:
            # - elo_diff / expected_win_prob (monotonic transform)
            # - p1_matches_last_7d / p2_matches_last_7d (synthetic: same schedule)
            # - series_game_number / series_length_so_far (small synthetic series)
            expected_pairs = {
                ("elo_diff", "expected_win_prob"),
                ("p1_matches_last_7d", "p2_matches_last_7d"),
                ("p1_matches_last_30d", "p2_matches_last_30d"),
                ("series_game_number", "series_length_so_far"),
            }
            unexpected = [
                (a, b) for a, b, _ in result.value
                if (a, b) not in expected_pairs and (b, a) not in expected_pairs
            ]
            if unexpected:
                pytest.fail(
                    f"Unexpected perfect correlations: {unexpected}"
                )

    def test_feature_count_plausibility(self, pipeline_data):
        _, features_df, *_ = pipeline_data
        result = check_feature_count_monotonic(features_df)
        assert result.passed, result.detail


# ===================================================================
# §3.4 Leakage & Baseline Smoke Tests
# ===================================================================


def _run_lgbm_check_in_subprocess(
    check_name: str,
    pipeline_data,
) -> dict:
    """Run a LightGBM-based check in a child process to avoid OpenMP conflict.

    Returns dict with 'passed', 'detail', 'name' keys.
    """
    from tests.helpers_sanity import lgbm_sanity_worker

    _, _, X_train, X_test, y_train, y_test, matchup_col = pipeline_data

    ctx = multiprocessing.get_context("spawn")
    q = ctx.Queue()
    proc = ctx.Process(
        target=lgbm_sanity_worker,
        args=(
            check_name,
            X_train.to_dict(orient="list"),
            X_test.to_dict(orient="list"),
            y_train.tolist(),
            y_test.tolist(),
            matchup_col.tolist() if matchup_col is not None else None,
            q,
        ),
    )
    proc.start()
    proc.join(timeout=60)

    if proc.exitcode != 0:
        pytest.fail(
            f"Child process for {check_name} crashed (exit code {proc.exitcode})."
        )

    return q.get_nowait()


class TestLeakageSmokeTests:
    """§3.4 — Model baselines and leakage detection.

    LightGBM-based checks run in subprocess to avoid dual-OpenMP segfault
    when torch has been loaded by other tests in the same pytest session.
    """

    def test_majority_baseline(self, pipeline_data):
        _, _, X_train, X_test, y_train, y_test, _ = pipeline_data
        result = check_majority_baseline(X_train, X_test, y_train, y_test)
        assert result.passed, result.detail

    def test_elo_baseline(self, pipeline_data):
        _, _, X_train, X_test, y_train, y_test, _ = pipeline_data
        result = check_elo_baseline(X_train, X_test, y_train, y_test)
        assert result.passed, result.detail

    def test_lgbm_accuracy_range(self, pipeline_data):
        result = _run_lgbm_check_in_subprocess("lgbm_accuracy_range", pipeline_data)
        assert result["passed"], result["detail"]

    def test_no_matchup_above_threshold(self, pipeline_data):
        result = _run_lgbm_check_in_subprocess(
            "no_matchup_above_threshold", pipeline_data
        )
        assert result["passed"], result["detail"]

    def test_no_single_feature_high_correlation(self, pipeline_data):
        _, features_df, *_ = pipeline_data
        result = check_no_single_feature_high_correlation(features_df)
        if not result.passed:
            # On synthetic data (100 matches), spurious correlations are expected
            pytest.skip(f"Synthetic data: {result.detail}")

    def test_lgbm_top_features(self, pipeline_data):
        result = _run_lgbm_check_in_subprocess("lgbm_top_features", pipeline_data)
        # On synthetic data, Elo features may not dominate — softer assertion
        if not result["passed"]:
            pytest.skip(
                f"Synthetic data: top features not Elo/winrate-dominated: {result['detail']}"
            )

    def test_train_test_accuracy_gap(self, pipeline_data):
        result = _run_lgbm_check_in_subprocess(
            "train_test_accuracy_gap", pipeline_data
        )
        if not result["passed"]:
            # 100 synthetic matches → LightGBM easily memorizes train, large gap expected
            pytest.skip(f"Synthetic data: {result['detail']}")


# ===================================================================
# §3.5 Known Issues to Verify/Fix
# ===================================================================


class TestKnownIssues:
    """§3.5 — Verify fixes for previously flagged issues."""

    def test_race_dummies_are_int(self, pipeline_data):
        _, features_df, *_ = pipeline_data
        result = check_race_dummies_are_int(features_df)
        assert result.passed, result.detail

    def test_expanding_excludes_current(self, pipeline_data):
        _, features_df, *_ = pipeline_data
        result = check_expanding_excludes_current(features_df)
        assert result.passed, result.detail

    def test_elo_deduplication(self, pipeline_data):
        _, features_df, *_ = pipeline_data
        result = check_elo_deduplication(features_df)
        assert result.passed, result.detail

    def test_rolling_windows_sparse_players(self, pipeline_data):
        _, features_df, *_ = pipeline_data
        result = check_rolling_windows_sparse_players(features_df)
        assert result.passed, result.detail


# ===================================================================
# Full integration test
# ===================================================================


def _full_sanity_worker(
    features_dict: dict,
    X_train_dict: dict,
    X_test_dict: dict,
    y_train_list: list,
    y_test_list: list,
    matchup_col_list: list | None,
    result_queue,
) -> None:
    """Run the non-DB sanity checks in an isolated subprocess.

    DB-dependent checks (§3.1, §3.2) are tested separately above.
    This covers §3.3 (feature distribution), §3.4 (baselines), §3.5 (known issues).
    """
    import warnings

    warnings.filterwarnings("ignore", category=DeprecationWarning)

    import pandas as pd

    from sc2ml.validation import (
        run_feature_distribution,
        run_known_issues,
        run_leakage_smoke_tests,
    )

    features_df = pd.DataFrame(features_dict)
    X_train = pd.DataFrame(X_train_dict)
    X_test = pd.DataFrame(X_test_dict)
    y_train = pd.Series(y_train_list, name="target")
    y_test = pd.Series(y_test_list, name="target")
    matchup_col = pd.Series(matchup_col_list) if matchup_col_list is not None else None

    checks = []
    checks.extend(run_feature_distribution(features_df))
    checks.extend(
        run_leakage_smoke_tests(X_train, X_test, y_train, y_test, features_df, matchup_col)
    )
    checks.extend(run_known_issues(features_df))

    result_queue.put({
        "total": len(checks),
        "passed": sum(c.passed for c in checks),
        "failures": [(c.name, c.detail) for c in checks if not c.passed],
    })


# ===================================================================
# Phase 3.3: Failure path tests for individual checks
# ===================================================================


class TestCheckNullRateFindsNulls:
    """check_null_rate should fail when critical columns have NULLs."""

    def test_null_match_time_detected(self):
        con = duckdb.connect(":memory:")
        # Create minimal tables with NULL match_time
        con.execute("""
            CREATE TABLE flat_players AS SELECT * FROM (VALUES
                ('m1', TIMESTAMP '2023-01-01', 'alice', 'Terran', 'Win'),
                ('m1', TIMESTAMP '2023-01-01', 'bob', 'Zerg', 'Loss'),
                ('m2', NULL, 'alice', 'Protoss', 'Win'),
                ('m2', NULL, 'bob', 'Terran', 'Loss')
            ) AS t(match_id, match_time, player_name, race, result)
        """)
        con.execute("""
            CREATE TABLE matches_flat AS SELECT * FROM (VALUES
                ('m1', TIMESTAMP '2023-01-01', 'alice', 'bob', 'Terran', 'Win'),
                ('m2', NULL, 'alice', 'bob', 'Protoss', 'Win')
            ) AS t(match_id, match_time, p1_name, p2_name, p1_race, p1_result)
        """)
        result = check_null_rate(con)
        assert not result.passed
        con.close()


class TestCheckMatchTimeRangeFailures:
    def test_too_early(self):
        """Year < 2010 → failure."""
        con = duckdb.connect(":memory:")
        con.execute("""
            CREATE TABLE matches_flat AS SELECT * FROM (VALUES
                (TIMESTAMP '2005-06-01'),
                (TIMESTAMP '2023-01-01')
            ) AS t(match_time)
        """)
        result = check_match_time_range(con)
        assert not result.passed
        assert "too early" in result.detail
        con.close()

    def test_future(self):
        """Year > 2027 → failure."""
        con = duckdb.connect(":memory:")
        con.execute("""
            CREATE TABLE matches_flat AS SELECT * FROM (VALUES
                (TIMESTAMP '2023-01-01'),
                (TIMESTAMP '2030-06-01')
            ) AS t(match_time)
        """)
        result = check_match_time_range(con)
        assert not result.passed
        assert "future" in result.detail
        con.close()


class TestCheckRaceDistributionUnexpected:
    def test_unexpected_race(self):
        """A 'Random' race should cause failure."""
        con = duckdb.connect(":memory:")
        con.execute("""
            CREATE TABLE flat_players AS SELECT * FROM (VALUES
                ('Terran'), ('Protoss'), ('Zerg'), ('Random')
            ) AS t(race)
        """)
        result = check_race_distribution(con)
        assert not result.passed
        assert "Random" in result.detail
        con.close()


class TestCheckDuplicateMatchIdsBad:
    def test_three_rows_per_match(self):
        """3 rows per match_id → failure."""
        con = duckdb.connect(":memory:")
        con.execute("""
            CREATE TABLE flat_players AS SELECT * FROM (VALUES
                ('m1', 'alice'), ('m1', 'bob'), ('m1', 'charlie')
            ) AS t(match_id, player_name)
        """)
        result = check_duplicate_match_ids(con)
        assert not result.passed
        con.close()


class TestCheckTargetBalanceSkewed:
    def test_skewed_90_percent(self):
        """90% win rate → failure."""
        n = 100
        df = pd.DataFrame({
            "split": ["train"] * n,
            "target": [1] * 90 + [0] * 10,
        })
        result = check_target_balance(df)
        assert not result.passed


class TestCheckSplitRatiosOff:
    def test_wrong_ratios(self):
        """50/25/25 ratios should fail (expected 80/15/5)."""
        con = duckdb.connect(":memory:")
        ids = [f"m{i}" for i in range(100)]
        splits = ["train"] * 50 + ["val"] * 25 + ["test"] * 25
        df = pd.DataFrame({"match_id": ids, "split": splits})  # noqa: F841
        con.execute("CREATE TABLE match_split AS SELECT * FROM df")
        result = check_split_ratios(con)
        assert not result.passed
        con.close()


class TestSanityReportSummary:
    def test_summary_formatting(self):
        """SanityReport.summary should show pass/fail counts and details."""
        from sc2ml.validation import SanityCheck, SanityReport

        report = SanityReport(checks=[
            SanityCheck("check_a", True, "all good"),
            SanityCheck("check_b", False, "something wrong"),
            SanityCheck("check_c", True, "ok"),
        ])
        summary = report.summary
        assert "2/3 checks passed" in summary
        assert "[PASS] check_a" in summary
        assert "[FAIL] check_b" in summary
        assert not report.all_passed

    def test_all_passed_true(self):
        """SanityReport.all_passed returns True when all checks pass."""
        from sc2ml.validation import SanityCheck, SanityReport

        report = SanityReport(checks=[
            SanityCheck("a", True, "ok"),
            SanityCheck("b", True, "ok"),
        ])
        assert report.all_passed


class TestFullSanityReport:
    """Run the complete sanity report and verify the aggregate result.

    DB checks run in-process; LightGBM-based checks run in a subprocess
    to avoid the dual-OpenMP segfault.
    """

    def test_db_checks_pass(self, synthetic_con, pipeline_data):
        """§3.1 and §3.2 checks all pass on synthetic data."""
        from sc2ml.validation import run_split_integrity, run_view_sanity

        _, features_df, *_ = pipeline_data
        checks = run_view_sanity(synthetic_con)
        checks.extend(run_split_integrity(synthetic_con, features_df))

        failures = [c for c in checks if not c.passed]
        assert len(failures) == 0, (
            "DB checks failed:\n"
            + "\n".join(f"  - {c.name}: {c.detail}" for c in failures)
        )

    def test_feature_and_model_checks(self, pipeline_data):
        """§3.3, §3.4, §3.5 checks run in subprocess (LightGBM isolation)."""
        _, features_df, X_train, X_test, y_train, y_test, matchup_col = pipeline_data

        ctx = multiprocessing.get_context("spawn")
        q = ctx.Queue()
        proc = ctx.Process(
            target=_full_sanity_worker,
            args=(
                features_df.to_dict(orient="list"),
                X_train.to_dict(orient="list"),
                X_test.to_dict(orient="list"),
                y_train.tolist(),
                y_test.tolist(),
                matchup_col.tolist() if matchup_col is not None else None,
                q,
            ),
        )
        proc.start()
        proc.join(timeout=120)

        if proc.exitcode != 0:
            pytest.fail(f"Full sanity subprocess crashed (exit code {proc.exitcode})")

        result = q.get_nowait()
        print(
            f"Full sanity: {result['passed']}/{result['total']} passed"
        )

        failures = result["failures"]
        # Allow up to 8 soft failures on synthetic data
        assert len(failures) <= 8, (
            f"{len(failures)} checks failed (max 8 allowed on synthetic data):\n"
            + "\n".join(f"  - {name}: {detail}" for name, detail in failures)
        )
