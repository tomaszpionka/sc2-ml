"""Tests for the evaluation module: metrics, bootstrap CI, McNemar, DeLong."""

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
    evaluate_model,
    mcnemar_test,
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
