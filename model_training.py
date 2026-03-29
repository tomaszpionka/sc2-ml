import logging
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

logger = logging.getLogger(__name__)

def train_and_evaluate_models(X_train, X_test, y_train, y_test):
    # Inicjalizacja modeli
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    }

    trained_models = {}

    for name, model in models.items():
        logger.info(f"Trenowanie modelu: {name}...")
        
        # Trening
        model.fit(X_train, y_train)
        
        # Predykcja
        y_pred = model.predict(X_test)
        
        # Ewaluacja
        acc = accuracy_score(y_test, y_pred)
        logger.info(f"{name} - Accuracy na zbiorze testowym: {acc:.4f}")
        
        print(f"\n{'='*40}")
        print(f"Raport Klasyfikacji: {name}")
        print(f"{'='*40}")
        print(classification_report(y_test, y_pred))
        
        trained_models[name] = model

    # Opcjonalnie: Wyświetlenie Feature Importance dla Random Forest
    rf_model = trained_models.get("Random Forest")
    if rf_model:
        importances = rf_model.feature_importances_
        feature_names = X_train.columns
        fi_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
        fi_df = fi_df.sort_values(by='Importance', ascending=False).head(10)
        
        print(f"\n--- Top 10 najważniejszych cech (Random Forest) ---")
        print(fi_df.to_string(index=False))

    return trained_models