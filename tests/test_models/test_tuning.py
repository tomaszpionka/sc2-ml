"""Tests for sc2ml.models.tuning — subprocess-isolated.

LightGBM and PyTorch load conflicting OpenMP runtimes on macOS.
All tests here run the actual tuning code in a spawned subprocess.
"""

import multiprocessing

import pytest

_TIMEOUT = 180  # Tuning can take longer


def _run_worker(worker_fn):
    """Run a worker function in a spawned subprocess and return its result."""
    ctx = multiprocessing.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=worker_fn, args=(q,))
    p.start()
    p.join(timeout=_TIMEOUT)
    assert p.exitcode == 0, f"Subprocess exited with code {p.exitcode}"
    assert not q.empty(), "Worker produced no result"
    return q.get(timeout=5)


@pytest.mark.slow
class TestTuning:
    def test_tune_random_forest(self):
        """tune_random_forest returns a fitted RandomForestClassifier."""
        from tests.helpers_tuning import worker_tune_random_forest

        result = _run_worker(worker_tune_random_forest)
        assert result["is_rf"] is True

    def test_tune_lgbm_optuna(self):
        """tune_lgbm_optuna returns a fitted Pipeline with n_trials=2."""
        from tests.helpers_tuning import worker_tune_lgbm_optuna

        result = _run_worker(worker_tune_lgbm_optuna)
        assert result["is_pipeline"] is True
        assert "scaler" in result["step_names"]
        assert "classifier" in result["step_names"]

    def test_tune_xgb_optuna(self):
        """tune_xgb_optuna returns a fitted Pipeline with n_trials=2."""
        from tests.helpers_tuning import worker_tune_xgb_optuna

        result = _run_worker(worker_tune_xgb_optuna)
        assert result["is_pipeline"] is True
        assert "scaler" in result["step_names"]
        assert "classifier" in result["step_names"]

    def test_tune_lr_grid(self):
        """tune_lr_grid returns a fitted Pipeline."""
        from tests.helpers_tuning import worker_tune_lr_grid

        result = _run_worker(worker_tune_lr_grid)
        assert result["is_pipeline"] is True
        assert "scaler" in result["step_names"]
        assert "classifier" in result["step_names"]
