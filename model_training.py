import logging
import pandas as pd
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


def train_and_evaluate_models(X_train, X_test, y_train, y_test):
    models = {
        "Logistic Regression": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
            ]
        ),
        "Random Forest": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=200,
                        max_depth=8,
                        min_samples_split=5,
                        random_state=42,
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
                        max_iter=200, learning_rate=0.05, random_state=42
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
                        n_estimators=200,
                        max_depth=6,
                        learning_rate=0.05,
                        random_state=42,
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
                        n_estimators=200,
                        max_depth=6,
                        learning_rate=0.05,
                        random_state=42,
                        verbose=-1,
                    ),
                ),
            ]
        ),
    }

    trained_models = {}

    # Filtrujemy zbiór testowy, aby wyciągnąć mecze, w których obaj gracze mają już historię.
    # Ustawiamy próg: minimum 3 rozegrane mecze w historii przed obecnym starciem.
    veterans_mask = (X_test["p1_total_games_played"] >= 3) & (
        X_test["p2_total_games_played"] >= 3
    )

    X_test_veterans = X_test[veterans_mask]
    y_test_veterans = y_test[veterans_mask]

    for name, pipeline in models.items():
        logger.info(f"Trenowanie modelu: {name}...")

        # Uczymy model na pełnym zbiorze treningowym
        pipeline.fit(X_train, y_train)

        # 1. Predykcja na CAŁYM zbiorze testowym (zawiera "Nieznajomych")
        y_pred_all = pipeline.predict(X_test)
        acc_all = accuracy_score(y_test, y_pred_all)

        # 2. Predykcja TYLKO na zbiorze "Weteranów"
        acc_vet = 0.0
        if not X_test_veterans.empty:
            y_pred_vet = pipeline.predict(X_test_veterans)
            acc_vet = accuracy_score(y_test_veterans, y_pred_vet)

        logger.info(f"\n{'='*55}")
        logger.info(f"Wyniki: {name}")
        logger.info(f"-> Accuracy (Cały zbiór testowy, N={len(X_test)}): {acc_all:.4f}")
        if not X_test_veterans.empty:
            logger.info(
                f"-> Accuracy (Tylko Weterani, N={len(X_test_veterans)}):   {acc_vet:.4f}"
            )
        else:
            logger.info(
                "-> Brak weteranów w zbiorze testowym przy obecnych kryteriach (N=0)."
            )
        logger.info(f"{'='*55}")

        trained_models[name] = pipeline

    # Wypisujemy Feature Importance z Random Forest
    rf_pipeline = trained_models.get("Random Forest")
    if rf_pipeline:
        rf_model = rf_pipeline.named_steps["classifier"]
        importances = rf_model.feature_importances_
        fi_df = pd.DataFrame({"Feature": X_train.columns, "Importance": importances})
        fi_df = fi_df.sort_values(by="Importance", ascending=False).head(10)

        logger.info(f"\n--- Top 10 najważniejszych cech (Random Forest) ---")
        logger.info(fi_df.to_string(index=False))

    return trained_models
