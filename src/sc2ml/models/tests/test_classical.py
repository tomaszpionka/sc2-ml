"""Tests for sc2ml.models.classical — subprocess-isolated.

LightGBM and PyTorch load conflicting OpenMP runtimes on macOS.
All tests here run the actual model code in a spawned subprocess
so that libomp from LightGBM never co-exists with torch's OpenMP.
"""

import multiprocessing

import pytest

# Timeout for subprocess workers (seconds)
_TIMEOUT = 120


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
class TestBuildPipelines:
    def test_build_pipelines_returns_five(self):
        """_build_model_pipelines returns 5 model pipelines."""
        from sc2ml.models.tests.helpers_classical_unit import worker_build_pipelines

        result = _run_worker(worker_build_pipelines)
        assert result["n_pipelines"] == 5

    def test_pipeline_step_names(self):
        """Each pipeline has scaler + classifier steps."""
        from sc2ml.models.tests.helpers_classical_unit import worker_build_pipelines

        result = _run_worker(worker_build_pipelines)
        for name, steps in result["step_names"].items():
            assert "scaler" in steps, f"{name} missing scaler"
            assert "classifier" in steps, f"{name} missing classifier"


@pytest.mark.slow
class TestTrainAndEvaluate:
    def test_train_evaluate_returns_tuple(self):
        """train_and_evaluate_models returns (dict, list)."""
        from sc2ml.models.tests.helpers_classical_unit import worker_train_evaluate

        result = _run_worker(worker_train_evaluate)
        assert result["type_trained"] == "dict"
        assert result["type_results"] == "list"

    def test_all_models_valid_accuracy(self):
        """Every model achieves 0 <= accuracy <= 1."""
        from sc2ml.models.tests.helpers_classical_unit import worker_train_evaluate

        result = _run_worker(worker_train_evaluate)
        for name, acc in result["accuracies"].items():
            assert 0.0 <= acc <= 1.0, f"{name} accuracy {acc} out of range"

    def test_with_val_set(self):
        """X_val/y_val triggers early stopping for XGBoost and LightGBM."""
        from sc2ml.models.tests.helpers_classical_unit import worker_train_with_val

        result = _run_worker(worker_train_with_val)
        assert result["n_models"] == 5
        assert result["n_results"] == 5
        for name, acc in result["accuracies"].items():
            assert 0.0 <= acc <= 1.0, f"{name} accuracy {acc} out of range"

    def test_with_matchup_col(self):
        """matchup_col populates per_matchup breakdown."""
        from sc2ml.models.tests.helpers_classical_unit import worker_train_with_matchup

        result = _run_worker(worker_train_with_matchup)
        assert result["n_models"] == 5
        assert result["has_matchup_breakdown"] is True
