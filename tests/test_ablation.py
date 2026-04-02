"""Tests for the feature ablation runner."""

import pytest

from tests.helpers import make_matches_df, make_series_df


def _ablation_worker(result_queue) -> None:
    """Run ablation in subprocess to avoid LightGBM/PyTorch OpenMP conflict."""
    import warnings

    warnings.filterwarnings("ignore", category=DeprecationWarning)

    from sc2ml.models.evaluation import run_feature_ablation

    raw_df = make_matches_df(n=300, seed=42)
    # Add split column (needed by split_for_ml)
    n = len(raw_df)
    n_train = int(n * 0.8)
    n_val = int(n * 0.15)
    splits = ["train"] * n_train + ["val"] * n_val + ["test"] * (n - n_train - n_val)
    raw_df["split"] = splits

    series_df = make_series_df(raw_df, series_size=3)

    results = run_feature_ablation(raw_df, series_df=series_df, compute_ci=False)

    result_queue.put({
        "n_steps": len(results),
        "groups": [r["group"] for r in results],
        "n_columns": [r["n_columns"] for r in results],
        "accuracies": [r["metrics"]["accuracy"] for r in results],
        "has_lift": [bool(r["lift"]) for r in results],
    })


def _run_in_subprocess():
    """Run the ablation worker in a subprocess."""
    import multiprocessing
    ctx = multiprocessing.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=_ablation_worker, args=(q,))
    p.start()
    p.join(timeout=120)
    assert p.exitcode == 0, f"Ablation subprocess failed with exit code {p.exitcode}"
    return q.get()


@pytest.mark.slow
class TestFeatureAblation:
    def test_ablation_returns_five_steps(self):
        result = _run_in_subprocess()
        assert result["n_steps"] == 5

    def test_ablation_groups_in_order(self):
        result = _run_in_subprocess()
        assert result["groups"] == ["A", "B", "C", "D", "E"]

    def test_columns_monotonically_increase(self):
        result = _run_in_subprocess()
        cols = result["n_columns"]
        for i in range(1, len(cols)):
            assert cols[i] >= cols[i - 1], (
                f"Column count decreased from step {i-1} ({cols[i-1]}) "
                f"to step {i} ({cols[i]})"
            )

    def test_first_step_has_no_lift(self):
        result = _run_in_subprocess()
        assert result["has_lift"][0] is False

    def test_subsequent_steps_have_lift(self):
        result = _run_in_subprocess()
        for i in range(1, len(result["has_lift"])):
            assert result["has_lift"][i] is True

    def test_accuracies_are_valid(self):
        result = _run_in_subprocess()
        for acc in result["accuracies"]:
            assert 0.0 <= acc <= 1.0
