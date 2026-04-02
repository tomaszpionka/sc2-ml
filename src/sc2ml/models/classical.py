import logging

import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from sc2ml.config import (
    HGB_LEARNING_RATE,
    HGB_MAX_ITER,
    LR_MAX_ITER,
    RANDOM_SEED,
    RF_MAX_DEPTH,
    RF_MIN_SAMPLES_SPLIT,
    RF_N_ESTIMATORS,
    VETERAN_MIN_GAMES,
)
from sc2ml.models.evaluation import ModelResults, evaluate_model

logger = logging.getLogger(__name__)


def _build_model_pipelines() -> dict[str, Pipeline]:
    """Create unfitted model pipelines."""
    return {
        "Logistic Regression": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("classifier", LogisticRegression(max_iter=LR_MAX_ITER, random_state=RANDOM_SEED)),
            ]
        ),
        "Random Forest": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=RF_N_ESTIMATORS,
                        max_depth=RF_MAX_DEPTH,
                        min_samples_split=RF_MIN_SAMPLES_SPLIT,
                        random_state=RANDOM_SEED,
                    ),
                ),
            ]
        ),
        "Gradient Boosting": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    HistGradientBoostingClassifier(
                        max_iter=HGB_MAX_ITER,
                        learning_rate=HGB_LEARNING_RATE,
                        random_state=RANDOM_SEED,
                    ),
                ),
            ]
        ),
        "XGBoost": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    XGBClassifier(
                        n_estimators=RF_N_ESTIMATORS,
                        max_depth=6,
                        learning_rate=HGB_LEARNING_RATE,
                        random_state=RANDOM_SEED,
                        eval_metric="logloss",
                    ),
                ),
            ]
        ),
        "LightGBM": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LGBMClassifier(
                        n_estimators=RF_N_ESTIMATORS,
                        max_depth=6,
                        learning_rate=HGB_LEARNING_RATE,
                        random_state=RANDOM_SEED,
                        verbose=-1,
                    ),
                ),
            ]
        ),
    }


def train_and_evaluate_models(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    X_val: pd.DataFrame | None = None,
    y_val: pd.Series | None = None,
    matchup_col: pd.Series | None = None,
    compute_ci: bool = True,
) -> tuple[dict[str, Pipeline], list[ModelResults]]:
    """Train all classical ML models and evaluate with full metrics.

    Parameters
    ----------
    X_val, y_val : optional
        Validation set.  When provided, XGBoost and LightGBM use it for early
        stopping and validation accuracy is reported for all models.
    matchup_col : optional
        Series of matchup types (e.g. "PvT") aligned with X_test index for
        per-matchup breakdown.
    compute_ci : bool
        Whether to compute bootstrap confidence intervals (slow).

    Returns
    -------
    (trained_models dict, list of ModelResults)
    """
    models = _build_model_pipelines()

    trained_models: dict[str, Pipeline] = {}
    all_results: list[ModelResults] = []

    # Veterans mask
    veterans_mask = (
        (X_test["p1_total_games_played"] >= VETERAN_MIN_GAMES)
        & (X_test["p2_total_games_played"] >= VETERAN_MIN_GAMES)
    ) if "p1_total_games_played" in X_test.columns else None

    # Prepare scaled validation data for early stopping (XGBoost, LightGBM)
    has_val = X_val is not None and y_val is not None

    for name, pipeline in models.items():
        logger.info(f"Training model: {name}...")

        # Early stopping for boosting models that support eval_set
        if has_val and name in ("XGBoost", "LightGBM"):
            scaler = pipeline.named_steps["scaler"]
            clf = pipeline.named_steps["classifier"]
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)
            clf.fit(
                X_train_scaled, y_train,
                eval_set=[(X_val_scaled, y_val)],
            )
        else:
            pipeline.fit(X_train, y_train)

        trained_models[name] = pipeline

        # Full evaluation via evaluation module
        result = evaluate_model(
            pipeline, X_test, y_test, name,
            matchup_col=matchup_col,
            veterans_mask=veterans_mask,
            compute_ci=compute_ci,
        )
        all_results.append(result)

        # Validation accuracy (logged only, not stored in ModelResults)
        if has_val:
            assert X_val is not None  # for mypy
            y_pred_val = pipeline.predict(X_val)
            from sklearn.metrics import accuracy_score
            acc_val = accuracy_score(y_val, y_pred_val)
            logger.info(f"  val accuracy (N={len(X_val)}): {acc_val:.4f}")

    # Log feature importances from the Random Forest
    rf_pipeline = trained_models.get("Random Forest")
    if rf_pipeline:
        rf_model = rf_pipeline.named_steps["classifier"]
        importances = rf_model.feature_importances_
        fi_df = pd.DataFrame({"Feature": X_train.columns, "Importance": importances})
        fi_df = fi_df.sort_values(by="Importance", ascending=False).head(10)
        logger.info("\n--- Top 10 features (Random Forest) ---")
        logger.info(fi_df.to_string(index=False))

    return trained_models, all_results
