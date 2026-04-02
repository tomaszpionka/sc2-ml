"""Tests for model reproducibility with fixed random seed.

Covers:
- Classical ML models produce identical predictions across two runs with seed=42
- GNN training produces identical best accuracy across two runs with seed=42
"""
import numpy as np
import pytest
import torch

from sc2ml.features.engineering import perform_feature_engineering, temporal_train_test_split
from sc2ml.gnn.pipeline import build_starcraft_graph
from sc2ml.gnn.trainer import train_and_evaluate_gnn
from sc2ml.models.classical import train_and_evaluate_models
from tests.helpers import make_matches_df


@pytest.fixture(scope="module")
def train_test_data():
    raw = make_matches_df(n=300, seed=42)
    features_df = perform_feature_engineering(raw)
    X_train, X_test, y_train, y_test = temporal_train_test_split(features_df, test_size=0.2)
    # Drop non-numeric columns that survive temporal_train_test_split but
    # cannot be consumed by sklearn models (e.g. patch version strings).
    str_cols = X_train.select_dtypes(include=["object", "string"]).columns
    X_train = X_train.drop(columns=str_cols)
    X_test = X_test.drop(columns=str_cols)
    return X_train, X_test, y_train, y_test


def test_logistic_regression_is_deterministic(train_test_data) -> None:
    X_train, X_test, y_train, y_test = train_test_data
    models1 = train_and_evaluate_models(X_train, X_test, y_train, y_test)
    models2 = train_and_evaluate_models(X_train, X_test, y_train, y_test)
    preds1 = models1["Logistic Regression"].predict(X_test)
    preds2 = models2["Logistic Regression"].predict(X_test)
    np.testing.assert_array_equal(
        preds1, preds2, err_msg="Logistic Regression predictions are not deterministic"
    )


def test_random_forest_is_deterministic(train_test_data) -> None:
    X_train, X_test, y_train, y_test = train_test_data
    models1 = train_and_evaluate_models(X_train, X_test, y_train, y_test)
    models2 = train_and_evaluate_models(X_train, X_test, y_train, y_test)
    preds1 = models1["Random Forest"].predict(X_test)
    preds2 = models2["Random Forest"].predict(X_test)
    np.testing.assert_array_equal(
        preds1, preds2, err_msg="Random Forest predictions are not deterministic"
    )


def test_gnn_training_is_deterministic() -> None:
    """GNN training with the same seed should produce same best accuracy."""
    torch.manual_seed(42)
    raw = make_matches_df(n=200, seed=42)
    features_df = perform_feature_engineering(raw)
    graph_data, _ = build_starcraft_graph(features_df, test_size=0.1)

    torch.manual_seed(42)
    _, acc1 = train_and_evaluate_gnn(graph_data, epochs=20, test_size=0.1)

    torch.manual_seed(42)
    _, acc2 = train_and_evaluate_gnn(graph_data, epochs=20, test_size=0.1)

    assert acc1 == acc2, (
        f"GNN training is not deterministic: run1={acc1:.4f}, run2={acc2:.4f}. "
        "Check that torch.manual_seed(42) is set before each call."
    )
