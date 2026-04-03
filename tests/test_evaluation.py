"""Tests for the evaluation module: metrics, bootstrap CI, McNemar, DeLong."""

import multiprocessing

import numpy as np
import pandas as pd
import pytest

from sc2ml.models.evaluation import (
    ModelResults,
    bootstrap_ci,
    calibration_curve_data,
    compare_models,
    compute_metrics,
    delong_test,
    evaluate_all_models,
    evaluate_model,
    mcnemar_test,
    run_permutation_importance,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def perfect_predictions():
    """y_true and y_prob where the model is perfect."""
    y_true = np.array([0, 0, 0, 1, 1, 1, 0, 1, 0, 1])
    y_prob = np.array([0.1, 0.2, 0.1, 0.9, 0.8, 0.95, 0.05, 0.85, 0.15, 0.9])
    return y_true, y_prob


@pytest.fixture()
def noisy_predictions():
    """Moderate-quality predictions with some errors."""
    rng = np.random.default_rng(42)
    n = 200
    y_true = rng.integers(0, 2, n)
    # Add noise to probabilities
    y_prob = y_true * 0.6 + (1 - y_true) * 0.4 + rng.normal(0, 0.15, n)
    y_prob = np.clip(y_prob, 0.01, 0.99)
    return y_true, y_prob


# ---------------------------------------------------------------------------
# compute_metrics
# ---------------------------------------------------------------------------

class TestComputeMetrics:
    def test_perfect_accuracy(self, perfect_predictions):
        y_true, y_prob = perfect_predictions
        metrics = compute_metrics(y_true, y_prob)
        assert metrics["accuracy"] == 1.0

    def test_perfect_auc(self, perfect_predictions):
        y_true, y_prob = perfect_predictions
        metrics = compute_metrics(y_true, y_prob)
        assert metrics["auc_roc"] == 1.0

    def test_contains_all_keys(self, noisy_predictions):
        y_true, y_prob = noisy_predictions
        metrics = compute_metrics(y_true, y_prob)
        assert set(metrics.keys()) == {"accuracy", "auc_roc", "brier_score", "log_loss"}

    def test_brier_score_range(self, noisy_predictions):
        y_true, y_prob = noisy_predictions
        metrics = compute_metrics(y_true, y_prob)
        assert 0.0 <= metrics["brier_score"] <= 1.0

    def test_random_predictions_low_accuracy(self):
        rng = np.random.default_rng(123)
        y_true = rng.integers(0, 2, 1000)
        y_prob = rng.uniform(0, 1, 1000)
        metrics = compute_metrics(y_true, y_prob)
        # Random should be near 50%
        assert 0.4 <= metrics["accuracy"] <= 0.6

    def test_custom_threshold(self, noisy_predictions):
        y_true, y_prob = noisy_predictions
        m1 = compute_metrics(y_true, y_prob, threshold=0.3)
        m2 = compute_metrics(y_true, y_prob, threshold=0.7)
        # Lower threshold -> more positive predictions -> different accuracy
        assert m1["accuracy"] != m2["accuracy"]


# ---------------------------------------------------------------------------
# bootstrap_ci
# ---------------------------------------------------------------------------

class TestBootstrapCI:
    def test_ci_contains_point_estimate(self, noisy_predictions):
        y_true, y_prob = noisy_predictions
        from sklearn.metrics import roc_auc_score
        point = roc_auc_score(y_true, y_prob)
        lo, hi = bootstrap_ci(y_true, y_prob, roc_auc_score, n_iterations=500)
        assert lo <= point <= hi

    def test_ci_width_positive(self, noisy_predictions):
        y_true, y_prob = noisy_predictions
        from sklearn.metrics import roc_auc_score
        lo, hi = bootstrap_ci(y_true, y_prob, roc_auc_score, n_iterations=200)
        assert hi > lo

    def test_perfect_model_tight_ci(self, perfect_predictions):
        y_true, y_prob = perfect_predictions
        from sklearn.metrics import roc_auc_score
        lo, hi = bootstrap_ci(y_true, y_prob, roc_auc_score, n_iterations=200)
        # Perfect model should have very tight CI near 1.0
        assert lo >= 0.95


# ---------------------------------------------------------------------------
# mcnemar_test
# ---------------------------------------------------------------------------

class TestMcNemarTest:
    def test_identical_models_high_pvalue(self, noisy_predictions):
        y_true, _ = noisy_predictions
        y_pred = np.ones(len(y_true), dtype=int)
        result = mcnemar_test(y_true, y_pred, y_pred)
        assert result["p_value"] == 1.0

    def test_uses_exact_when_few_discordant(self):
        y_true = np.array([1, 1, 0, 0, 0, 0, 1, 1, 0, 0])
        y_pred_a = np.array([1, 0, 0, 0, 0, 0, 1, 1, 0, 0])
        y_pred_b = np.array([1, 1, 1, 0, 0, 0, 1, 1, 0, 0])
        result = mcnemar_test(y_true, y_pred_a, y_pred_b)
        assert result["method"] == "exact_binomial"

    def test_uses_chi2_when_many_discordant(self):
        rng = np.random.default_rng(42)
        n = 500
        y_true = rng.integers(0, 2, n)
        y_pred_a = rng.integers(0, 2, n)
        y_pred_b = rng.integers(0, 2, n)
        result = mcnemar_test(y_true, y_pred_a, y_pred_b)
        # With random predictions on 500 samples, expect many discordant pairs
        assert result["method"] == "chi_squared"

    def test_returns_required_keys(self):
        y_true = np.array([1, 0, 1, 0, 1])
        y_pred_a = np.array([1, 0, 0, 0, 1])
        y_pred_b = np.array([1, 1, 1, 0, 0])
        result = mcnemar_test(y_true, y_pred_a, y_pred_b)
        assert "p_value" in result
        assert "statistic" in result
        assert "n_discordant" in result
        assert "b01" in result
        assert "b10" in result


# ---------------------------------------------------------------------------
# delong_test
# ---------------------------------------------------------------------------

class TestDeLongTest:
    def test_identical_models_high_pvalue(self, noisy_predictions):
        y_true, y_prob = noisy_predictions
        result = delong_test(y_true, y_prob, y_prob)
        assert result["p_value"] >= 0.99
        assert abs(result["auc_diff"]) < 1e-10

    def test_better_model_positive_diff(self, noisy_predictions):
        y_true, y_prob_good = noisy_predictions
        # Create a worse model by adding more noise
        rng = np.random.default_rng(99)
        y_prob_bad = np.clip(y_prob_good + rng.normal(0, 0.3, len(y_prob_good)), 0.01, 0.99)
        result = delong_test(y_true, y_prob_good, y_prob_bad)
        # Good model should have higher AUC
        assert result["auc_a"] >= result["auc_b"]
        assert result["auc_diff"] >= 0

    def test_returns_required_keys(self, noisy_predictions):
        y_true, y_prob = noisy_predictions
        result = delong_test(y_true, y_prob, y_prob)
        assert set(result.keys()) == {"z_stat", "p_value", "auc_a", "auc_b", "auc_diff"}

    def test_handles_single_class(self):
        y_true = np.array([1, 1, 1, 1])
        y_prob_a = np.array([0.9, 0.8, 0.7, 0.6])
        y_prob_b = np.array([0.5, 0.5, 0.5, 0.5])
        result = delong_test(y_true, y_prob_a, y_prob_b)
        # Should handle gracefully
        assert result["p_value"] == 1.0


# ---------------------------------------------------------------------------
# calibration_curve_data
# ---------------------------------------------------------------------------

class TestCalibrationCurve:
    def test_returns_arrays(self, noisy_predictions):
        y_true, y_prob = noisy_predictions
        frac_pos, mean_pred = calibration_curve_data(y_true, y_prob, n_bins=5)
        assert isinstance(frac_pos, np.ndarray)
        assert isinstance(mean_pred, np.ndarray)
        assert len(frac_pos) == len(mean_pred)

    def test_values_in_range(self, noisy_predictions):
        y_true, y_prob = noisy_predictions
        frac_pos, mean_pred = calibration_curve_data(y_true, y_prob)
        assert np.all(frac_pos >= 0) and np.all(frac_pos <= 1)
        assert np.all(mean_pred >= 0) and np.all(mean_pred <= 1)


# ---------------------------------------------------------------------------
# evaluate_model
# ---------------------------------------------------------------------------

class TestEvaluateModel:
    def test_returns_model_results(self, noisy_predictions):
        y_true, y_prob = noisy_predictions
        X_test = pd.DataFrame({
            "f1": np.random.default_rng(42).normal(0, 1, len(y_true)),
            "f2": np.random.default_rng(43).normal(0, 1, len(y_true)),
        })

        class _DummyModel:
            def predict_proba(self, X):
                return np.column_stack([1 - y_prob, y_prob])

        result = evaluate_model(
            _DummyModel(), X_test, pd.Series(y_true), "Dummy",
            compute_ci=False,
        )
        assert isinstance(result, ModelResults)
        assert result.model_name == "Dummy"
        assert 0 < result.accuracy < 1
        assert 0 < result.auc_roc <= 1

    def test_per_matchup_breakdown(self, noisy_predictions):
        y_true, y_prob = noisy_predictions
        n = len(y_true)
        X_test = pd.DataFrame({"f1": np.zeros(n)})
        matchup_col = pd.Series(
            np.random.default_rng(42).choice(["PvT", "TvZ", "PvZ"], n)
        )

        class _DummyModel:
            def predict_proba(self, X):
                return np.column_stack([1 - y_prob, y_prob])

        result = evaluate_model(
            _DummyModel(), X_test, pd.Series(y_true), "Dummy",
            matchup_col=matchup_col, compute_ci=False,
        )
        assert len(result.per_matchup) > 0
        for matchup, metrics in result.per_matchup.items():
            assert "accuracy" in metrics
            assert "auc_roc" in metrics


# ---------------------------------------------------------------------------
# compare_models
# ---------------------------------------------------------------------------

class TestCompareModels:
    def test_pairwise_comparison(self, noisy_predictions):
        y_true, y_prob = noisy_predictions
        rng = np.random.default_rng(99)
        y_prob_b = np.clip(y_prob + rng.normal(0, 0.1, len(y_prob)), 0.01, 0.99)

        r1 = ModelResults(
            model_name="A", accuracy=0.7, auc_roc=0.75,
            brier_score=0.2, log_loss_val=0.5,
            y_true=y_true, y_pred=(y_prob >= 0.5).astype(int), y_prob=y_prob,
        )
        r2 = ModelResults(
            model_name="B", accuracy=0.65, auc_roc=0.70,
            brier_score=0.25, log_loss_val=0.55,
            y_true=y_true, y_pred=(y_prob_b >= 0.5).astype(int), y_prob=y_prob_b,
        )

        df = compare_models([r1, r2])
        assert len(df) == 1  # one pair
        assert "mcnemar_p" in df.columns
        assert "delong_p" in df.columns
        assert df.iloc[0]["model_a"] == "A"
        assert df.iloc[0]["model_b"] == "B"

    def test_three_models_three_pairs(self, noisy_predictions):
        y_true, y_prob = noisy_predictions
        results = []
        for name in ["A", "B", "C"]:
            results.append(ModelResults(
                model_name=name, accuracy=0.6, auc_roc=0.65,
                brier_score=0.25, log_loss_val=0.6,
                y_true=y_true, y_pred=(y_prob >= 0.5).astype(int), y_prob=y_prob,
            ))
        df = compare_models(results)
        assert len(df) == 3  # C(3,2) = 3 pairs


# ---------------------------------------------------------------------------
# delong_test — scalar covariance edge case (lines 284-287)
# ---------------------------------------------------------------------------

class TestDeLongScalarCovariance:
    def test_delong_m1_does_not_crash(self):
        """m=1 positive sample → function returns without crashing."""
        y_true = np.array([1, 0, 0, 0, 0])
        y_prob_a = np.array([0.9, 0.3, 0.2, 0.4, 0.1])
        y_prob_b = np.array([0.8, 0.2, 0.3, 0.5, 0.15])
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            result = delong_test(y_true, y_prob_a, y_prob_b)
        assert "p_value" in result
        assert "auc_a" in result

    def test_delong_n1_does_not_crash(self):
        """n=1 negative sample → function returns without crashing."""
        y_true = np.array([1, 1, 1, 1, 0])
        y_prob_a = np.array([0.9, 0.8, 0.7, 0.6, 0.2])
        y_prob_b = np.array([0.85, 0.75, 0.65, 0.55, 0.3])
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            result = delong_test(y_true, y_prob_a, y_prob_b)
        assert "p_value" in result
        assert "auc_a" in result

    def test_delong_var_diff_zero(self):
        """Identical predictions → var_diff <= 0 → p_value=1.0 (line 294-301)."""
        y_true = np.array([0, 0, 1, 1, 0, 1, 0, 1, 1, 0])
        y_prob = np.array([0.3, 0.2, 0.8, 0.9, 0.1, 0.7, 0.4, 0.6, 0.85, 0.15])
        result = delong_test(y_true, y_prob, y_prob)
        assert result["p_value"] >= 0.99
        assert result["auc_diff"] == 0.0


# ---------------------------------------------------------------------------
# evaluate_model — additional coverage (lines 370, 379-402)
# ---------------------------------------------------------------------------

class TestEvaluateModelExtended:
    def test_evaluate_model_1d_prob(self):
        """Model returning 1D predict_proba triggers the ndim!=2 path."""
        rng = np.random.default_rng(42)
        n = 100
        y_true = rng.integers(0, 2, n)
        y_prob = y_true * 0.6 + (1 - y_true) * 0.4 + rng.normal(0, 0.1, n)
        y_prob = np.clip(y_prob, 0.01, 0.99)
        X_test = pd.DataFrame({"f1": rng.normal(0, 1, n)})

        class _Model1D:
            def predict_proba(self, X):
                return y_prob  # 1D, not 2D

        result = evaluate_model(
            _Model1D(), X_test, pd.Series(y_true), "1D",
            compute_ci=False,
        )
        assert isinstance(result, ModelResults)
        assert 0 < result.accuracy <= 1

    def test_evaluate_model_bootstrap_ci(self):
        """compute_ci=True exercises the bootstrap CI paths."""
        rng = np.random.default_rng(42)
        n = 200
        y_true = rng.integers(0, 2, n)
        # Add enough noise so accuracy is not perfect
        y_prob = y_true * 0.6 + (1 - y_true) * 0.4 + rng.normal(0, 0.2, n)
        y_prob = np.clip(y_prob, 0.01, 0.99)
        X_test = pd.DataFrame({"f1": rng.normal(0, 1, n)})

        class _Dummy:
            def predict_proba(self, X):
                return np.column_stack([1 - y_prob, y_prob])

        result = evaluate_model(
            _Dummy(), X_test, pd.Series(y_true), "CI",
            compute_ci=True,
        )
        assert result.accuracy_ci[0] < result.accuracy_ci[1]
        assert result.auc_roc_ci[0] < result.auc_roc_ci[1]

    def test_evaluate_model_veterans_metrics(self):
        """Pass veterans_mask with True values → veterans dict populated."""
        rng = np.random.default_rng(42)
        n = 100
        y_true = rng.integers(0, 2, n)
        y_prob = y_true * 0.7 + (1 - y_true) * 0.3 + rng.normal(0, 0.1, n)
        y_prob = np.clip(y_prob, 0.01, 0.99)
        X_test = pd.DataFrame({"f1": rng.normal(0, 1, n)})
        # Half are veterans
        vet_mask = pd.Series([i < 50 for i in range(n)])

        class _Dummy:
            def predict_proba(self, X):
                return np.column_stack([1 - y_prob, y_prob])

        result = evaluate_model(
            _Dummy(), X_test, pd.Series(y_true), "Vets",
            veterans_mask=vet_mask, compute_ci=False,
        )
        assert "accuracy" in result.veterans
        assert result.veterans["n_samples"] == 50

    def test_evaluate_model_veterans_empty(self):
        """All-False veterans mask → empty dict."""
        rng = np.random.default_rng(42)
        n = 50
        y_true = rng.integers(0, 2, n)
        y_prob = np.clip(y_true * 0.7 + rng.normal(0, 0.1, n), 0.01, 0.99)
        X_test = pd.DataFrame({"f1": rng.normal(0, 1, n)})
        vet_mask = pd.Series([False] * n)

        class _Dummy:
            def predict_proba(self, X):
                return np.column_stack([1 - y_prob, y_prob])

        result = evaluate_model(
            _Dummy(), X_test, pd.Series(y_true), "NoVets",
            veterans_mask=vet_mask, compute_ci=False,
        )
        assert result.veterans == {}


# ---------------------------------------------------------------------------
# evaluate_all_models (lines 481-492)
# ---------------------------------------------------------------------------

class TestEvaluateAllModels:
    def test_evaluate_all_models(self):
        """2 fitted models → list of results + comparison DataFrame."""
        rng = np.random.default_rng(42)
        n = 100
        y_true = rng.integers(0, 2, n)
        y_prob = np.clip(y_true * 0.7 + rng.normal(0, 0.1, n), 0.01, 0.99)
        X_test = pd.DataFrame({"f1": rng.normal(0, 1, n)})

        class _DummyA:
            def predict_proba(self, X):
                return np.column_stack([1 - y_prob, y_prob])

        class _DummyB:
            def predict_proba(self, X):
                noise = rng.normal(0, 0.05, len(X))
                p = np.clip(y_prob + noise, 0.01, 0.99)
                return np.column_stack([1 - p, p])

        results, comparisons = evaluate_all_models(
            {"ModelA": _DummyA(), "ModelB": _DummyB()},
            X_test, pd.Series(y_true), compute_ci=False,
        )
        assert len(results) == 2
        assert isinstance(comparisons, pd.DataFrame)
        assert len(comparisons) == 1  # C(2,2)=1 pair

    def test_evaluate_all_models_comparison_count(self):
        """3 models → n*(n-1)/2 = 3 comparison rows."""
        rng = np.random.default_rng(42)
        n = 50
        y_true = rng.integers(0, 2, n)
        y_prob = np.clip(y_true * 0.7 + rng.normal(0, 0.1, n), 0.01, 0.99)
        X_test = pd.DataFrame({"f1": rng.normal(0, 1, n)})

        class _Dummy:
            def predict_proba(self, X):
                return np.column_stack([1 - y_prob, y_prob])

        models = {f"M{i}": _Dummy() for i in range(3)}
        results, comparisons = evaluate_all_models(
            models, X_test, pd.Series(y_true), compute_ci=False,
        )
        assert len(comparisons) == 3


# ---------------------------------------------------------------------------
# run_permutation_importance (lines 625-640)
# ---------------------------------------------------------------------------

class TestPermutationImportance:
    def test_run_permutation_importance(self):
        """Fitted LR + test data → DataFrame with feature importance."""
        from sklearn.linear_model import LogisticRegression

        rng = np.random.default_rng(42)
        n = 100
        X = pd.DataFrame({
            "f1": rng.normal(0, 1, n),
            "f2": rng.normal(0, 1, n),
            "f3": rng.normal(0, 1, n),
        })
        y = pd.Series((X["f1"] > 0).astype(int))

        model = LogisticRegression(max_iter=200, random_state=42)
        model.fit(X, y)

        result = run_permutation_importance(model, X, y, n_repeats=5)
        assert isinstance(result, pd.DataFrame)
        assert "feature" in result.columns
        assert "importance_mean" in result.columns
        assert len(result) == 3

    def test_run_permutation_importance_sorted(self):
        """Result should be sorted descending by importance_mean."""
        from sklearn.linear_model import LogisticRegression

        rng = np.random.default_rng(42)
        n = 100
        X = pd.DataFrame({
            "strong": rng.normal(0, 1, n),
            "noise": rng.normal(0, 0.01, n),
        })
        y = pd.Series((X["strong"] > 0).astype(int))

        model = LogisticRegression(max_iter=200, random_state=42)
        model.fit(X, y)

        result = run_permutation_importance(model, X, y, n_repeats=5)
        vals = result["importance_mean"].values
        assert all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1))


# ---------------------------------------------------------------------------
# compare_models — single model edge case
# ---------------------------------------------------------------------------

class TestCompareModelsSingle:
    def test_compare_models_single(self):
        """1 model → empty comparisons DataFrame."""
        y = np.array([0, 1, 0, 1])
        r1 = ModelResults(
            model_name="Only", accuracy=0.75, auc_roc=0.8,
            brier_score=0.15, log_loss_val=0.4,
            y_true=y, y_pred=y, y_prob=np.array([0.1, 0.9, 0.2, 0.8]),
        )
        df = compare_models([r1])
        assert len(df) == 0


# ---------------------------------------------------------------------------
# Feature ablation — subprocess-isolated (lines 499-606)
# ---------------------------------------------------------------------------

_SUBPROCESS_TIMEOUT = 180


def _run_worker(worker_fn):
    """Run a worker function in a spawned subprocess and return its result."""
    ctx = multiprocessing.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=worker_fn, args=(q,))
    p.start()
    p.join(timeout=_SUBPROCESS_TIMEOUT)
    assert p.exitcode == 0, f"Subprocess exited with code {p.exitcode}"
    assert not q.empty(), "Worker produced no result"
    return q.get(timeout=5)


@pytest.mark.slow
class TestFeatureAblationSubprocess:
    def test_run_feature_ablation_subprocess(self):
        """Feature ablation returns one step per FeatureGroup."""
        from tests.helpers_evaluation import worker_feature_ablation

        result = _run_worker(worker_feature_ablation)
        assert result["n_steps"] == 5  # Groups A through E
        assert result["has_metrics"] is True
        assert result["has_lift"] is True
        assert result["first_lift_empty"] is True  # First group has no previous


@pytest.mark.slow
class TestPatchDriftSubprocess:
    def test_run_patch_drift_subprocess(self):
        """Patch drift returns old→new and mixed model results."""
        from tests.helpers_evaluation import worker_patch_drift

        result = _run_worker(worker_patch_drift)
        assert result["has_old_to_new"] is True
        assert result["has_mixed"] is True
        assert result["has_per_patch"] is True
        assert 0.0 <= result["old_to_new_acc"] <= 1.0
        assert 0.0 <= result["mixed_acc"] <= 1.0
        assert result["n_old_patches"] > 0
        assert result["n_new_patches"] > 0

    def test_run_patch_drift_no_column_raises(self):
        """ValueError raised when no patch column in features DataFrame."""
        from tests.helpers_evaluation import worker_patch_drift_no_column

        result = _run_worker(worker_patch_drift_no_column)
        assert result["raised"] is True
        assert "patch column" in result["error"].lower()
