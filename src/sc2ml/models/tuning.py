"""Hyperparameter tuning for classical ML models.

Contains:
- tune_random_forest: RandomizedSearchCV (legacy)
- tune_lgbm_optuna: Optuna Bayesian optimization for LightGBM
- tune_xgb_optuna: Optuna Bayesian optimization for XGBoost
- tune_lr_grid: Grid search over C and penalty for Logistic Regression

All Optuna functions accept an ``ExpandingWindowCV`` cross-validator
for temporal CV compatibility.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import optuna
import pandas as pd
from scipy.stats import randint
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from sc2ml.config import (
    LR_GRID_C,
    LR_GRID_PENALTY,
    OPTUNA_N_TRIALS_LGBM,
    OPTUNA_N_TRIALS_XGB,
    RANDOM_SEED,
    TUNING_CV_FOLDS,
    TUNING_N_ITER,
)

if TYPE_CHECKING:
    from sc2ml.data.cv import ExpandingWindowCV

logger = logging.getLogger(__name__)

# Suppress Optuna's verbose logging
optuna.logging.set_verbosity(optuna.logging.WARNING)


def tune_random_forest(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestClassifier:
    """Run RandomizedSearchCV to find optimal Random Forest hyperparameters.

    Searches TUNING_N_ITER random combinations over the defined parameter space
    using TUNING_CV_FOLDS-fold cross-validation. Returns the best fitted estimator.
    """
    logger.info("Starting Random Forest hyperparameter tuning...")

    param_dist = {
        "n_estimators": randint(100, 500),         # Number of trees
        "max_depth": [5, 8, 12, 15, None],          # Maximum tree depth
        "min_samples_split": randint(2, 20),         # Minimum samples required to split a node
        "min_samples_leaf": randint(1, 10),          # Minimum samples in leaf (regularisation)
        "max_features": ["sqrt", "log2"],            # Features considered per split
    }

    rf = RandomForestClassifier(random_state=RANDOM_SEED)

    random_search = RandomizedSearchCV(
        estimator=rf,
        param_distributions=param_dist,
        n_iter=TUNING_N_ITER,
        cv=TUNING_CV_FOLDS,
        scoring="accuracy",
        n_jobs=-1,
        random_state=RANDOM_SEED,
        verbose=1,
    )

    random_search.fit(X_train, y_train)

    logger.info(f"Best parameters: {random_search.best_params_}")
    logger.info(f"Best CV accuracy: {random_search.best_score_:.4f}")

    return random_search.best_estimator_


# ---------------------------------------------------------------------------
# Optuna-based tuning
# ---------------------------------------------------------------------------

def tune_lgbm_optuna(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    cv: ExpandingWindowCV,
    n_trials: int = OPTUNA_N_TRIALS_LGBM,
    seed: int = RANDOM_SEED,
) -> Pipeline:
    """Optuna-tuned LightGBM with expanding-window temporal CV.

    Returns a fitted Pipeline (StandardScaler + LGBMClassifier) with the
    best hyperparameters, retrained on the full training set.
    """
    from lightgbm import LGBMClassifier

    logger.info(f"Starting LightGBM Optuna tuning ({n_trials} trials)...")

    def objective(trial: optuna.Trial) -> float:
        params = {
            "num_leaves": trial.suggest_int("num_leaves", 15, 127),
            "max_depth": trial.suggest_int("max_depth", 3, 12),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "n_estimators": trial.suggest_int("n_estimators", 50, 500),
            "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        }

        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LGBMClassifier(
                **params,
                random_state=seed,
                verbose=-1,
            )),
        ])

        scores = cross_val_score(
            pipeline, X_train, y_train,
            cv=cv, scoring="neg_log_loss", n_jobs=1,
        )
        return float(np.mean(scores))

    study = optuna.create_study(
        direction="maximize",  # neg_log_loss: higher is better
        sampler=optuna.samplers.TPESampler(seed=seed),
        pruner=optuna.pruners.MedianPruner(),
    )
    study.optimize(objective, n_trials=n_trials)

    logger.info(f"LightGBM best trial: {study.best_trial.value:.4f}")
    logger.info(f"LightGBM best params: {study.best_trial.params}")

    # Retrain with best params on full training set
    best_params = study.best_trial.params
    best_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LGBMClassifier(
            **best_params,
            random_state=seed,
            verbose=-1,
        )),
    ])
    best_pipeline.fit(X_train, y_train)
    return best_pipeline


def tune_xgb_optuna(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    cv: ExpandingWindowCV,
    n_trials: int = OPTUNA_N_TRIALS_XGB,
    seed: int = RANDOM_SEED,
) -> Pipeline:
    """Optuna-tuned XGBoost with expanding-window temporal CV.

    Returns a fitted Pipeline (StandardScaler + XGBClassifier) with the
    best hyperparameters, retrained on the full training set.
    """
    from xgboost import XGBClassifier

    logger.info(f"Starting XGBoost Optuna tuning ({n_trials} trials)...")

    def objective(trial: optuna.Trial) -> float:
        params = {
            "max_depth": trial.suggest_int("max_depth", 3, 12),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "n_estimators": trial.suggest_int("n_estimators", 50, 500),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "gamma": trial.suggest_float("gamma", 1e-8, 5.0, log=True),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        }

        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", XGBClassifier(
                **params,
                random_state=seed,
                eval_metric="logloss",
            )),
        ])

        scores = cross_val_score(
            pipeline, X_train, y_train,
            cv=cv, scoring="neg_log_loss", n_jobs=1,
        )
        return float(np.mean(scores))

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=seed),
        pruner=optuna.pruners.MedianPruner(),
    )
    study.optimize(objective, n_trials=n_trials)

    logger.info(f"XGBoost best trial: {study.best_trial.value:.4f}")
    logger.info(f"XGBoost best params: {study.best_trial.params}")

    best_params = study.best_trial.params
    best_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", XGBClassifier(
            **best_params,
            random_state=seed,
            eval_metric="logloss",
        )),
    ])
    best_pipeline.fit(X_train, y_train)
    return best_pipeline


def tune_lr_grid(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    cv: ExpandingWindowCV,
) -> Pipeline:
    """Grid search over C and penalty for Logistic Regression.

    Returns a fitted Pipeline (StandardScaler + LogisticRegression) with
    the best hyperparameters.
    """
    logger.info("Starting Logistic Regression grid search...")

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            max_iter=1000,
            random_state=RANDOM_SEED,
            solver="saga",  # supports both l1 and l2
        )),
    ])

    param_grid = {
        "classifier__C": LR_GRID_C,
        "classifier__penalty": LR_GRID_PENALTY,
    }

    grid_search = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        cv=cv,
        scoring="neg_log_loss",
        n_jobs=-1,
    )

    grid_search.fit(X_train, y_train)

    logger.info(f"LR best params: {grid_search.best_params_}")
    logger.info(f"LR best CV score: {grid_search.best_score_:.4f}")

    return grid_search.best_estimator_
