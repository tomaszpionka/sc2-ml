"""Tests for SHAP analysis module."""

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from sc2ml.analysis.shap_analysis import (
    compute_shap_values,
    shap_feature_importance_table,
)


@pytest.fixture()
def trained_rf_pipeline():
    """A small trained RandomForest pipeline for SHAP testing."""
    rng = np.random.default_rng(42)
    n = 100
    X = pd.DataFrame({
        "f1": rng.normal(0, 1, n),
        "f2": rng.normal(0, 1, n),
        "f3": rng.normal(0, 1, n),
    })
    y = (X["f1"] + X["f2"] > 0).astype(int)

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", RandomForestClassifier(
            n_estimators=10, max_depth=3, random_state=42,
        )),
    ])
    pipeline.fit(X, y)
    return pipeline, X


@pytest.fixture()
def trained_lr_pipeline():
    """A small trained LogisticRegression pipeline for SHAP testing."""
    rng = np.random.default_rng(42)
    n = 100
    X = pd.DataFrame({
        "f1": rng.normal(0, 1, n),
        "f2": rng.normal(0, 1, n),
    })
    y = (X["f1"] > 0).astype(int)

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=200, random_state=42)),
    ])
    pipeline.fit(X, y)
    return pipeline, X


class TestComputeShapValues:
    def test_returns_explanation(self, trained_rf_pipeline):
        import shap
        pipeline, X = trained_rf_pipeline
        shap_values = compute_shap_values(pipeline, X, max_samples=50)
        assert isinstance(shap_values, shap.Explanation)

    def test_correct_shape(self, trained_rf_pipeline):
        pipeline, X = trained_rf_pipeline
        shap_values = compute_shap_values(pipeline, X, max_samples=50)
        assert shap_values.values.shape == (50, 3)  # 50 samples, 3 features

    def test_feature_names_preserved(self, trained_rf_pipeline):
        pipeline, X = trained_rf_pipeline
        shap_values = compute_shap_values(pipeline, X, max_samples=50)
        assert shap_values.feature_names == ["f1", "f2", "f3"]

    def test_works_with_lr(self, trained_lr_pipeline):
        pipeline, X = trained_lr_pipeline
        shap_values = compute_shap_values(pipeline, X, max_samples=50)
        assert shap_values.values.shape[0] == 50
        assert shap_values.values.shape[1] == 2


class TestShapImportanceTable:
    def test_returns_dataframe(self, trained_rf_pipeline):
        pipeline, X = trained_rf_pipeline
        shap_values = compute_shap_values(pipeline, X, max_samples=50)
        table = shap_feature_importance_table(shap_values)
        assert isinstance(table, pd.DataFrame)
        assert "feature" in table.columns
        assert "mean_abs_shap" in table.columns

    def test_sorted_descending(self, trained_rf_pipeline):
        pipeline, X = trained_rf_pipeline
        shap_values = compute_shap_values(pipeline, X, max_samples=50)
        table = shap_feature_importance_table(shap_values)
        vals = table["mean_abs_shap"].values
        assert all(vals[i] >= vals[i+1] for i in range(len(vals)-1))

    def test_non_negative_importance(self, trained_rf_pipeline):
        pipeline, X = trained_rf_pipeline
        shap_values = compute_shap_values(pipeline, X, max_samples=50)
        table = shap_feature_importance_table(shap_values)
        assert all(table["mean_abs_shap"] >= 0)


# ---------------------------------------------------------------------------
# Additional coverage for uncovered paths
# ---------------------------------------------------------------------------

class TestComputeShapNoSubsampling:
    def test_no_subsampling_when_small(self):
        """max_samples > len(X_test) → no subsampling (line 51)."""
        rng = np.random.default_rng(42)
        n = 30
        X = pd.DataFrame({"f1": rng.normal(0, 1, n), "f2": rng.normal(0, 1, n)})
        y = (X["f1"] > 0).astype(int)
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", RandomForestClassifier(
                n_estimators=10, max_depth=3, random_state=42,
            )),
        ])
        pipeline.fit(X, y)
        shap_values = compute_shap_values(pipeline, X, max_samples=1000)
        # All 30 samples should be used (no subsampling)
        assert shap_values.values.shape[0] == 30


class TestComputeShapKernelFallback:
    def test_kernel_explainer_fallback(self):
        """Pipeline with unknown classifier type → KernelExplainer (lines 67-72)."""
        from sklearn.neighbors import KNeighborsClassifier

        rng = np.random.default_rng(42)
        n = 50
        X = pd.DataFrame({"f1": rng.normal(0, 1, n), "f2": rng.normal(0, 1, n)})
        y = (X["f1"] > 0).astype(int)
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", KNeighborsClassifier(n_neighbors=3)),
        ])
        pipeline.fit(X, y)
        # KNN is not in the known model list → should use KernelExplainer
        shap_values = compute_shap_values(pipeline, X, max_samples=20)
        assert shap_values.values.shape[0] == 20


class TestPlotShapBeeswarm:
    def test_plot_beeswarm_creates_file(self, trained_rf_pipeline, tmp_path):
        """plot_shap_beeswarm creates a PNG at the given path (lines 100-109)."""
        from sc2ml.analysis.shap_analysis import plot_shap_beeswarm

        pipeline, X = trained_rf_pipeline
        shap_values = compute_shap_values(pipeline, X, max_samples=30)
        out = tmp_path / "beeswarm.png"
        plot_shap_beeswarm(shap_values, out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_plot_beeswarm_custom_title(self, trained_rf_pipeline, tmp_path):
        """Custom title doesn't crash."""
        from sc2ml.analysis.shap_analysis import plot_shap_beeswarm

        pipeline, X = trained_rf_pipeline
        shap_values = compute_shap_values(pipeline, X, max_samples=30)
        out = tmp_path / "custom.png"
        plot_shap_beeswarm(shap_values, out, title="My Custom Title")
        assert out.exists()


class TestPlotShapPerMatchup:
    def test_plot_per_matchup_creates_files(self, trained_rf_pipeline, tmp_path):
        """2 matchup types → 2 PNGs (lines 120-137)."""
        from sc2ml.analysis.shap_analysis import plot_shap_per_matchup

        pipeline, X = trained_rf_pipeline
        rng = np.random.default_rng(42)
        matchup_col = pd.Series(
            rng.choice(["PvT", "TvZ"], len(X))
        )
        plot_shap_per_matchup(pipeline, X, matchup_col, tmp_path, max_samples_per_matchup=30)
        pngs = list(tmp_path.glob("shap_*.png"))
        assert len(pngs) == 2

    def test_plot_per_matchup_skips_small(self, trained_rf_pipeline, tmp_path):
        """Matchup with <10 samples skipped."""
        from sc2ml.analysis.shap_analysis import plot_shap_per_matchup

        pipeline, X = trained_rf_pipeline
        # Make "ZvZ" have only 3 samples
        matchup = ["PvT"] * 97 + ["ZvZ"] * 3
        matchup_col = pd.Series(matchup[:len(X)])
        plot_shap_per_matchup(pipeline, X, matchup_col, tmp_path, max_samples_per_matchup=30)
        pngs = list(tmp_path.glob("shap_*.png"))
        # Only PvT should be generated (ZvZ has <10 samples)
        assert len(pngs) == 1
        assert "PvT" in pngs[0].name
