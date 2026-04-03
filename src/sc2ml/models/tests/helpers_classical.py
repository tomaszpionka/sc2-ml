"""Isolated worker for classical model reproducibility checks.

This module intentionally does NOT import torch or PyTorch Geometric
so it can be spawned via ``multiprocessing`` without loading a second
``libomp.dylib`` that conflicts with LightGBM's Homebrew OpenMP.
"""

import warnings

import numpy as np


def classical_repro_worker(model_name: str, result_queue) -> None:
    """Train *model_name* twice and push whether predictions match."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    from sc2ml.features import perform_feature_engineering, temporal_train_test_split
    from sc2ml.models.classical import train_and_evaluate_models
    from tests.helpers import make_matches_df

    raw = make_matches_df(n=300, seed=42)
    features_df = perform_feature_engineering(raw)
    X_train, X_test, y_train, y_test = temporal_train_test_split(
        features_df, test_size=0.2
    )
    str_cols = X_train.select_dtypes(include=["object", "string"]).columns
    X_train = X_train.drop(columns=str_cols)
    X_test = X_test.drop(columns=str_cols)

    models1, _ = train_and_evaluate_models(X_train, X_test, y_train, y_test, compute_ci=False)
    models2, _ = train_and_evaluate_models(X_train, X_test, y_train, y_test, compute_ci=False)

    preds1 = models1[model_name].predict(X_test)
    preds2 = models2[model_name].predict(X_test)

    result_queue.put({
        "match": bool(np.array_equal(preds1, preds2)),
        "preds1_head": preds1[:5].tolist(),
        "preds2_head": preds2[:5].tolist(),
    })
