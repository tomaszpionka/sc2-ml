"""Subprocess worker for classical model unit tests.

This module intentionally does NOT import torch or PyTorch Geometric
so it can be spawned via ``multiprocessing`` without loading a second
``libomp.dylib`` that conflicts with LightGBM's Homebrew OpenMP.
"""

import warnings

import numpy as np
import pandas as pd


def _make_synthetic_data(n: int = 80, seed: int = 42):
    """Create minimal synthetic train/test data for classical models."""
    rng = np.random.default_rng(seed)
    n_features = 10

    X = pd.DataFrame(
        rng.normal(0, 1, (n, n_features)),
        columns=[f"feat_{i}" for i in range(n_features)],
    )
    # Add columns needed for veterans mask
    X["p1_total_games_played"] = rng.integers(0, 20, n)
    X["p2_total_games_played"] = rng.integers(0, 20, n)

    y = pd.Series(rng.integers(0, 2, n), name="target")

    split = int(n * 0.7)
    val_split = int(n * 0.85)

    X_train, X_val, X_test = X.iloc[:split], X.iloc[split:val_split], X.iloc[val_split:]
    y_train, y_val, y_test = y.iloc[:split], y.iloc[split:val_split], y.iloc[val_split:]

    return X_train, X_val, X_test, y_train, y_val, y_test


def worker_build_pipelines(result_queue) -> None:
    """Check that _build_model_pipelines returns expected structure."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    from sc2ml.models.classical import _build_model_pipelines

    pipelines = _build_model_pipelines()

    result_queue.put({
        "n_pipelines": len(pipelines),
        "names": sorted(pipelines.keys()),
        "step_names": {
            name: [step_name for step_name, _ in pipe.steps]
            for name, pipe in pipelines.items()
        },
    })


def worker_train_evaluate(result_queue) -> None:
    """Train and evaluate all models on synthetic data."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    from sc2ml.models.classical import train_and_evaluate_models

    X_train, _, X_test, y_train, _, y_test = _make_synthetic_data()

    trained, results = train_and_evaluate_models(
        X_train, X_test, y_train, y_test, compute_ci=False,
    )

    result_queue.put({
        "type_trained": type(trained).__name__,
        "type_results": type(results).__name__,
        "n_models": len(trained),
        "n_results": len(results),
        "accuracies": {r.model_name: r.accuracy for r in results},
    })


def worker_train_with_val(result_queue) -> None:
    """Train with validation set for early stopping."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    from sc2ml.models.classical import train_and_evaluate_models

    X_train, X_val, X_test, y_train, y_val, y_test = _make_synthetic_data()

    trained, results = train_and_evaluate_models(
        X_train, X_test, y_train, y_test,
        X_val=X_val, y_val=y_val,
        compute_ci=False,
    )

    result_queue.put({
        "n_models": len(trained),
        "n_results": len(results),
        "accuracies": {r.model_name: r.accuracy for r in results},
    })


def worker_train_with_matchup(result_queue) -> None:
    """Train with matchup_col for per-matchup breakdown."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    from sc2ml.models.classical import train_and_evaluate_models

    X_train, _, X_test, y_train, _, y_test = _make_synthetic_data(n=120)

    rng = np.random.default_rng(42)
    matchup_col = pd.Series(
        rng.choice(["PvT", "TvZ", "PvZ"], len(X_test)),
        index=X_test.index,
    )

    trained, results = train_and_evaluate_models(
        X_train, X_test, y_train, y_test,
        matchup_col=matchup_col, compute_ci=False,
    )

    has_matchup = any(len(r.per_matchup) > 0 for r in results)

    result_queue.put({
        "n_models": len(trained),
        "has_matchup_breakdown": has_matchup,
    })
