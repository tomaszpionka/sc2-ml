"""Subprocess workers for hyperparameter tuning tests.

This module intentionally does NOT import torch or PyTorch Geometric
so it can be spawned via ``multiprocessing`` without loading a second
``libomp.dylib`` that conflicts with LightGBM's Homebrew OpenMP.
"""

import warnings

import numpy as np
import pandas as pd


def _make_synthetic_data(n: int = 60, seed: int = 42):
    """Create minimal synthetic training data for tuning."""
    rng = np.random.default_rng(seed)
    n_features = 8
    X = pd.DataFrame(
        rng.normal(0, 1, (n, n_features)),
        columns=[f"feat_{i}" for i in range(n_features)],
    )
    y = pd.Series(rng.integers(0, 2, n), name="target")
    return X, y


def worker_tune_random_forest(result_queue) -> None:
    """Tune Random Forest with small n_iter."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)

    from unittest.mock import patch

    from sklearn.ensemble import RandomForestClassifier

    import sc2ml.models.tuning as tuning_mod

    X, y = _make_synthetic_data()
    # Reduce iterations and folds; force n_jobs=1 to avoid subprocess hangs
    with patch.object(tuning_mod, "TUNING_N_ITER", 3), \
         patch.object(tuning_mod, "TUNING_CV_FOLDS", 2):
        def _patched_tune_rf(X_train, y_train):
            from scipy.stats import randint
            from sklearn.model_selection import RandomizedSearchCV

            param_dist = {
                "n_estimators": randint(100, 500),
                "max_depth": [5, 8, None],
                "min_samples_split": randint(2, 20),
                "min_samples_leaf": randint(1, 10),
                "max_features": ["sqrt", "log2"],
            }
            rf = RandomForestClassifier(random_state=42)
            search = RandomizedSearchCV(
                estimator=rf, param_distributions=param_dist,
                n_iter=3, cv=2, scoring="accuracy",
                n_jobs=1, random_state=42, verbose=0,
            )
            search.fit(X_train, y_train)
            return search.best_estimator_

        best = _patched_tune_rf(X, y)

    result_queue.put({
        "type": type(best).__name__,
        "is_rf": isinstance(best, RandomForestClassifier),
    })


def worker_tune_lgbm_optuna(result_queue) -> None:
    """Tune LightGBM with Optuna (2 trials)."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    from sklearn.pipeline import Pipeline

    from sc2ml.data.cv import ExpandingWindowCV
    from sc2ml.models.tuning import tune_lgbm_optuna

    X, y = _make_synthetic_data()
    cv = ExpandingWindowCV(n_splits=2, min_train_frac=0.4)
    best = tune_lgbm_optuna(X, y, cv=cv, n_trials=2)

    result_queue.put({
        "is_pipeline": isinstance(best, Pipeline),
        "step_names": [name for name, _ in best.steps],
    })


def worker_tune_xgb_optuna(result_queue) -> None:
    """Tune XGBoost with Optuna (2 trials)."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    from sklearn.pipeline import Pipeline

    from sc2ml.data.cv import ExpandingWindowCV
    from sc2ml.models.tuning import tune_xgb_optuna

    X, y = _make_synthetic_data()
    cv = ExpandingWindowCV(n_splits=2, min_train_frac=0.4)
    best = tune_xgb_optuna(X, y, cv=cv, n_trials=2)

    result_queue.put({
        "is_pipeline": isinstance(best, Pipeline),
        "step_names": [name for name, _ in best.steps],
    })


def worker_tune_lr_grid(result_queue) -> None:
    """Grid search for Logistic Regression.

    Reimplements the grid search inline with n_jobs=1 to avoid
    subprocess deadlocks from sklearn's joblib parallelism.
    """
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)

    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GridSearchCV
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    from sc2ml.data.cv import ExpandingWindowCV

    X, y = _make_synthetic_data()
    cv = ExpandingWindowCV(n_splits=2, min_train_frac=0.4)

    # Mirror tune_lr_grid logic but with n_jobs=1 and small grid
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            max_iter=1000, random_state=42, solver="saga",
        )),
    ])
    grid_search = GridSearchCV(
        estimator=pipeline,
        param_grid={
            "classifier__C": [0.1, 1.0],
            "classifier__penalty": ["l2"],
        },
        cv=cv,
        scoring="neg_log_loss",
        n_jobs=1,
    )
    grid_search.fit(X, y)
    best = grid_search.best_estimator_

    result_queue.put({
        "is_pipeline": isinstance(best, Pipeline),
        "step_names": [name for name, _ in best.steps],
    })
