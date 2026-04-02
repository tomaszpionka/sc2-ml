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
