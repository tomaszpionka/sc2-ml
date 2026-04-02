import logging

import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
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

logger = logging.getLogger(__name__)


def train_and_evaluate_models(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    X_val: pd.DataFrame | None = None,
    y_val: pd.Series | None = None,
) -> dict[str, Pipeline]:
    """Train all classical ML models and report accuracy on full and veteran-only test sets.

    Veterans are matches where both players have at least VETERAN_MIN_GAMES of
    recorded history — this subset is expected to be more predictable and serves
    as a secondary benchmark alongside the full test set accuracy.

    Parameters
    ----------
    X_val, y_val : optional
        Validation set.  When provided, XGBoost and LightGBM use it for early
        stopping and validation accuracy is reported for all models.
    """
    models: dict[str, Pipeline] = {
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

    trained_models: dict[str, Pipeline] = {}

    # Veteran subset: matches where both players have enough prior history
    veterans_mask = (X_test["p1_total_games_played"] >= VETERAN_MIN_GAMES) & (
        X_test["p2_total_games_played"] >= VETERAN_MIN_GAMES
    )
    X_test_veterans = X_test[veterans_mask]
    y_test_veterans = y_test[veterans_mask]

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

        # Full test set accuracy
        y_pred_all = pipeline.predict(X_test)
        acc_all = accuracy_score(y_test, y_pred_all)

        # Validation accuracy
        if has_val:
            y_pred_val = pipeline.predict(X_val)
            acc_val = accuracy_score(y_val, y_pred_val)

        # Veterans-only accuracy
        acc_vet = 0.0
        if not X_test_veterans.empty:
            y_pred_vet = pipeline.predict(X_test_veterans)
            acc_vet = accuracy_score(y_test_veterans, y_pred_vet)

        logger.info(f"\n{'=' * 55}")
        logger.info(f"Results: {name}")
        if has_val:
            assert X_val is not None  # for mypy; guarded by has_val
            logger.info(f"-> Accuracy (val, N={len(X_val)}): {acc_val:.4f}")
        logger.info(f"-> Accuracy (all test, N={len(X_test)}): {acc_all:.4f}")
        logger.info(f"\nConfusion Matrix:\n{confusion_matrix(y_test, y_pred_all)}")
        logger.info(
            f"\nClassification Report:\n"
            f"{classification_report(y_test, y_pred_all, target_names=['P2 wins', 'P1 wins'])}"
        )
        if not X_test_veterans.empty:
            logger.info(
                f"-> Accuracy (veterans only, N={len(X_test_veterans)}): {acc_vet:.4f}"
            )
            logger.info(
                f"\nVeterans Classification Report:\n"
                f"{classification_report(y_test_veterans, y_pred_vet, target_names=['P2 wins', 'P1 wins'])}"  # noqa: E501
            )
        else:
            logger.info("-> No veterans in test set at current threshold (N=0).")
        logger.info(f"{'=' * 55}")

        trained_models[name] = pipeline

    # Log feature importances from the Random Forest
    rf_pipeline = trained_models.get("Random Forest")
    if rf_pipeline:
        rf_model = rf_pipeline.named_steps["classifier"]
        importances = rf_model.feature_importances_
        fi_df = pd.DataFrame({"Feature": X_train.columns, "Importance": importances})
        fi_df = fi_df.sort_values(by="Importance", ascending=False).head(10)
        logger.info("\n--- Top 10 features (Random Forest) ---")
        logger.info(fi_df.to_string(index=False))

    return trained_models
