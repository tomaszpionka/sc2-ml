"""Tests for the CLI orchestration module (Phase 5).

All downstream modules are mocked — these tests verify argument routing,
function call ordering, and error handling in the CLI layer.
"""
from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CLI = "sc2ml.cli"


def _fake_features_df(n: int = 50) -> pd.DataFrame:
    """Minimal features DataFrame with a 'split' column."""
    import numpy as np

    rng = np.random.default_rng(42)
    splits = ["train"] * (n - 10) + ["val"] * 5 + ["test"] * 5
    return pd.DataFrame(
        {
            "feat_a": rng.standard_normal(n),
            "feat_b": rng.standard_normal(n),
            "p1_result": rng.integers(0, 2, size=n),
            "split": splits,
        }
    )


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------


class TestSetupLogging:
    def test_setup_logging_creates_handlers(self, tmp_path: Path) -> None:
        with patch(f"{_CLI}.Path", return_value=tmp_path / "logs"):
            from sc2ml.cli import setup_logging

            setup_logging()

        root = logging.getLogger()
        # pytest may wrap handlers (e.g. _FileHandler), so check subclass
        has_file = any(isinstance(h, logging.FileHandler) for h in root.handlers)
        has_stream = any(isinstance(h, logging.StreamHandler) for h in root.handlers)
        assert has_file or has_stream


# ---------------------------------------------------------------------------
# init_database
# ---------------------------------------------------------------------------


class TestInitDatabase:
    @patch(f"{_CLI}.validate_temporal_split")
    @patch(f"{_CLI}.create_temporal_split")
    @patch(f"{_CLI}.assign_series_ids")
    @patch(f"{_CLI}.create_ml_views")
    @patch(f"{_CLI}.load_map_translations")
    @patch(f"{_CLI}.move_data_to_duck_db")
    def test_calls_six_steps_in_order(
        self, m_move, m_maps, m_views, m_series, m_split, m_validate
    ) -> None:
        from sc2ml.cli import init_database

        con = MagicMock()
        init_database(con)

        m_move.assert_called_once_with(con, should_drop=False)
        m_maps.assert_called_once_with(con)
        m_views.assert_called_once_with(con)
        m_series.assert_called_once_with(con)
        m_split.assert_called_once_with(con)
        m_validate.assert_called_once_with(con)

    @patch(f"{_CLI}.validate_temporal_split")
    @patch(f"{_CLI}.create_temporal_split")
    @patch(f"{_CLI}.assign_series_ids")
    @patch(f"{_CLI}.create_ml_views")
    @patch(f"{_CLI}.load_map_translations")
    @patch(f"{_CLI}.move_data_to_duck_db")
    def test_should_drop_forwarded(
        self, m_move, m_maps, m_views, m_series, m_split, m_validate
    ) -> None:
        from sc2ml.cli import init_database

        con = MagicMock()
        init_database(con, should_drop=True)

        m_move.assert_called_once_with(con, should_drop=True)


# ---------------------------------------------------------------------------
# main — argument routing
# ---------------------------------------------------------------------------


class TestMainRouting:
    """Verify that argparse routes subcommands to the correct function."""

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}.duckdb")
    @patch(f"{_CLI}.init_database")
    def test_main_init(self, m_init, m_duckdb, m_log) -> None:
        from sc2ml.cli import main

        m_con = MagicMock()
        m_duckdb.connect.return_value = m_con

        with patch("sys.argv", ["sc2ml", "init"]):
            main()

        m_init.assert_called_once_with(m_con, should_drop=False)
        m_con.close.assert_called_once()

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}.duckdb")
    @patch(f"{_CLI}.init_database")
    def test_main_init_force(self, m_init, m_duckdb, m_log) -> None:
        from sc2ml.cli import main

        m_con = MagicMock()
        m_duckdb.connect.return_value = m_con

        with patch("sys.argv", ["sc2ml", "init", "--force"]):
            main()

        m_init.assert_called_once_with(m_con, should_drop=True)

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}.run_pipeline")
    def test_main_run(self, m_run, m_log) -> None:
        from sc2ml.cli import main

        with patch("sys.argv", ["sc2ml", "run"]):
            main()

        m_run.assert_called_once()

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}._run_ablation_command")
    def test_main_ablation(self, m_ablation, m_log) -> None:
        from sc2ml.cli import main

        with patch("sys.argv", ["sc2ml", "ablation"]):
            main()

        m_ablation.assert_called_once()

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}._run_tune_command")
    def test_main_tune(self, m_tune, m_log) -> None:
        from sc2ml.cli import main

        with patch("sys.argv", ["sc2ml", "tune"]):
            main()

        m_tune.assert_called_once_with(n_trials=200)

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}._run_tune_command")
    def test_main_tune_custom_trials(self, m_tune, m_log) -> None:
        from sc2ml.cli import main

        with patch("sys.argv", ["sc2ml", "tune", "--trials", "50"]):
            main()

        m_tune.assert_called_once_with(n_trials=50)

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}._run_evaluate_command")
    def test_main_evaluate(self, m_eval, m_log) -> None:
        from sc2ml.cli import main

        with patch("sys.argv", ["sc2ml", "evaluate"]):
            main()

        m_eval.assert_called_once()

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}._run_sanity_command")
    def test_main_sanity(self, m_sanity, m_log) -> None:
        from sc2ml.cli import main

        with patch("sys.argv", ["sc2ml", "sanity"]):
            main()

        m_sanity.assert_called_once()

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}.run_pipeline")
    def test_main_default_runs_pipeline(self, m_run, m_log) -> None:
        from sc2ml.cli import main

        with patch("sys.argv", ["sc2ml"]):
            main()

        m_run.assert_called_once()


# ---------------------------------------------------------------------------
# run_pipeline
# ---------------------------------------------------------------------------


class TestRunPipeline:
    """Test run_pipeline with mocked downstream modules."""

    def _mock_con(self, *, has_series: bool = False) -> MagicMock:
        con = MagicMock()
        # information_schema query for match_series
        series_row = (1,) if has_series else (0,)
        con.execute.return_value.fetchone.return_value = series_row
        if has_series:
            con.execute.return_value.df.return_value = pd.DataFrame(
                {"match_id": ["m1"], "series_id": [1]}
            )
        return con

    @patch(f"{_CLI}.visualize_gnn_space")
    @patch(f"{_CLI}.train_and_evaluate_gnn", return_value=(MagicMock(), 0.65))
    @patch(f"{_CLI}.build_starcraft_graph", return_value=(MagicMock(), {"p1": 0}))
    @patch(f"{_CLI}.build_features", return_value=_fake_features_df())
    @patch(f"{_CLI}.get_matches_dataframe", return_value=pd.DataFrame())
    @patch(f"{_CLI}.validate_data_split_sql")
    @patch(f"{_CLI}.duckdb")
    @patch(f"{_CLI}.setup_logging")
    def test_run_pipeline_gnn(
        self, m_log, m_duckdb, m_validate, m_get, m_feat, m_graph, m_train, m_viz
    ) -> None:
        from sc2ml.cli import run_pipeline

        m_duckdb.connect.return_value = self._mock_con()

        with patch(f"{_CLI}.MODELS_TO_RUN", ["GNN"]), \
             patch(f"{_CLI}.EVALUATE_PER_PATCH", False):
            run_pipeline()

        m_graph.assert_called_once()
        m_train.assert_called_once()
        m_viz.assert_called_once()

    @patch(f"{_CLI}.train_and_evaluate_models", return_value=({}, []))
    @patch(f"{_CLI}.split_for_ml", return_value=(
        pd.DataFrame({"a": [1]}), pd.DataFrame({"a": [2]}),
        pd.DataFrame({"a": [3]}), pd.Series([0]), pd.Series([1]), pd.Series([0]),
    ))
    @patch(f"{_CLI}.build_features")
    @patch(f"{_CLI}.get_matches_dataframe", return_value=pd.DataFrame())
    @patch(f"{_CLI}.validate_data_split_sql")
    @patch(f"{_CLI}.duckdb")
    @patch(f"{_CLI}.setup_logging")
    def test_run_pipeline_classic(
        self, m_log, m_duckdb, m_validate, m_get, m_feat, m_split, m_train
    ) -> None:
        from sc2ml.cli import run_pipeline

        feat_df = _fake_features_df()
        m_feat.return_value = feat_df
        m_duckdb.connect.return_value = self._mock_con()

        with patch(f"{_CLI}.MODELS_TO_RUN", ["CLASSIC"]), \
             patch(f"{_CLI}.EVALUATE_PER_PATCH", False):
            run_pipeline()

        m_train.assert_called_once()

    @patch(f"{_CLI}.visualize_gnn_space")
    @patch(f"{_CLI}.train_and_evaluate_gnn", return_value=(MagicMock(), 0.60))
    @patch(f"{_CLI}.build_starcraft_graph", return_value=(MagicMock(), {"p1": 0}))
    @patch(f"{_CLI}.build_features")
    @patch(f"{_CLI}.get_matches_dataframe", return_value=pd.DataFrame())
    @patch(f"{_CLI}.validate_data_split_sql")
    @patch(f"{_CLI}.duckdb")
    @patch(f"{_CLI}.setup_logging")
    def test_run_pipeline_per_patch(
        self, m_log, m_duckdb, m_validate, m_get, m_feat, m_graph, m_train, m_viz
    ) -> None:
        import numpy as np

        from sc2ml.cli import run_pipeline

        feat_df = _fake_features_df(200)
        feat_df["data_build"] = np.repeat(["50012", "50013"], 100)
        m_feat.return_value = feat_df
        m_duckdb.connect.return_value = self._mock_con()

        with patch(f"{_CLI}.MODELS_TO_RUN", ["GNN"]), \
             patch(f"{_CLI}.EVALUATE_PER_PATCH", True), \
             patch(f"{_CLI}.PATCH_MIN_MATCHES", 50):
            run_pipeline()

        assert m_train.call_count == 2
        m_viz.assert_called_once()

    @patch(f"{_CLI}.build_features", side_effect=RuntimeError("boom"))
    @patch(f"{_CLI}.get_matches_dataframe", return_value=pd.DataFrame())
    @patch(f"{_CLI}.validate_data_split_sql")
    @patch(f"{_CLI}.duckdb")
    @patch(f"{_CLI}.setup_logging")
    def test_run_pipeline_exception_logged(
        self, m_log, m_duckdb, m_validate, m_get, m_feat, caplog
    ) -> None:
        from sc2ml.cli import run_pipeline

        m_duckdb.connect.return_value = self._mock_con()

        with patch(f"{_CLI}.MODELS_TO_RUN", ["GNN"]), \
             caplog.at_level(logging.ERROR, logger="SC2_Pipeline"):
            run_pipeline()

        assert "Pipeline failed" in caplog.text


# ---------------------------------------------------------------------------
# _load_data_and_features
# ---------------------------------------------------------------------------


class TestLoadDataAndFeatures:
    @patch(f"{_CLI}.get_matches_dataframe", return_value=pd.DataFrame({"x": [1]}))
    @patch(f"{_CLI}.duckdb")
    def test_load_data_with_series(self, m_duckdb, m_get) -> None:
        from sc2ml.cli import _load_data_and_features

        m_con = MagicMock()
        m_duckdb.connect.return_value = m_con
        # has_series = True
        m_con.execute.return_value.fetchone.return_value = (1,)
        m_con.execute.return_value.df.return_value = pd.DataFrame(
            {"match_id": ["m1"], "series_id": [1]}
        )

        raw_df, series_df = _load_data_and_features()

        assert series_df is not None
        assert "series_id" in series_df.columns
        m_con.close.assert_called_once()

    @patch(f"{_CLI}.get_matches_dataframe", return_value=pd.DataFrame({"x": [1]}))
    @patch(f"{_CLI}.duckdb")
    def test_load_data_without_series(self, m_duckdb, m_get) -> None:
        from sc2ml.cli import _load_data_and_features

        m_con = MagicMock()
        m_duckdb.connect.return_value = m_con
        m_con.execute.return_value.fetchone.return_value = (0,)

        raw_df, series_df = _load_data_and_features()

        assert series_df is None
        m_con.close.assert_called_once()
