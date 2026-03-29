import sys
import logging
from pathlib import Path

# ==========================================
# 1. KONFIGURACJA GLOBALNEGO LOGGERA NA SAMEJ GÓRZE!
# ==========================================
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_dir / "sc2_pipeline.log", mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("SC2_Pipeline")

# ==========================================
# 2. DOPIERO TERAZ IMPORTUJEMY RESZTĘ ZEWNĘTRZNYCH PACZEK I NASZE MODUŁY
# ==========================================
import pandas as pd
import duckdb
import joblib
from sklearn.metrics import accuracy_score
import torch
from config import DB_FILE
from data_ingestion import (
    slim_down_sc2_with_manifest,
    move_data_to_duck_db,
    load_map_translations,
)
from data_processing import create_ml_views, get_matches_dataframe
from ml_pipeline import perform_feature_engineering, temporal_train_test_split
from elo_system import add_elo_features
from model_training import train_and_evaluate_models
from hyperparameter_tuning import tune_random_forest
from gnn_model import SC2EdgeClassifier
from gnn_trainer import train_and_evaluate_gnn

# GNN i Node2Vec
from gnn_pipeline import build_starcraft_graph
from node2vec_embedder import train_and_get_embeddings, append_embeddings_to_df


def main():
    logger.info("Start SC2 ML Pipeline...")

    # slim_down_sc2_with_manifest()

    con = duckdb.connect(str(DB_FILE))

    try:
        # move_data_to_duck_db(con)
        # load_map_translations(con)
        # create_ml_views(con)
        raw_df = get_matches_dataframe(con)

        # ==========================================
        # KROK 1: WARIANT B (Autorski System ELO)
        # ==========================================
        logger.info("Aplikuję system relatywnego ELO...")
        df_with_elo = add_elo_features(raw_df)

        # Przygotowanie sztucznego targetu dla budowniczego grafów (przed inżynierią ML)
        df_with_elo["target"] = (df_with_elo["p1_result"] == "Win").astype(int)

        # Feature Engineering (Generuje cechy tabelaryczne i WYRZUCA nazwy graczy)
        tabular_features_df = perform_feature_engineering(df_with_elo)

        # ==========================================
        # KROK 2: GRAFY I NODE2VEC (ŚCIEŻKA 1)
        # ==========================================
        logger.info("Budowa grafu i generowanie embeddingów Node2Vec...")

        # ZMIANA TUTAJ: Przekazujemy tabelę po inżynierii cech!
        graph_data, player_to_id = build_starcraft_graph(tabular_features_df)

        # Trenujemy Node2Vec wykorzystując akcelerator MPS (lub CPU)
        embeddings_dict = train_and_get_embeddings(
            graph_data, player_to_id, embedding_dim=64
        )

        # Doklejamy embeddingi do czystego zbioru tabelarycznego
        features_df = append_embeddings_to_df(
            tabular_features_df, embeddings_dict, embedding_dim=64
        )

        # ==========================================
        # KROK 3: PODZIAŁ I EWALUACJA (Z XGBOOST / LIGHTGBM)
        # ==========================================
        X_train, X_test, y_train, y_test = temporal_train_test_split(
            features_df, test_size=0.2
        )

        logger.info(
            "Oceniamy modele: RF, XGBoost, LightGBM (Wzbogacone o wektory z grafu)..."
        )
        trained_models = train_and_evaluate_models(X_train, X_test, y_train, y_test)

        # ==========================================
        # KROK 4: ZAPIS MODELI NA DYSK
        # ==========================================
        logger.info("Zapisywanie wytrenowanych modeli na dysk...")
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)

        for name, pipeline in trained_models.items():
            safe_name = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
            joblib.dump(pipeline, models_dir / f"baseline_{safe_name}.joblib")

        logger.info(
            "Modele podstawowe z wbudowanymi wektorami Node2Vec zostały bezpiecznie zapisane!"
        )

        # ==========================================
        # KROK 5: (OPCJONALNIE) TUNING
        # ==========================================
        # Odkomentuj poniższe linie, gdy będziesz gotowy na dłuuuuugie szukanie najlepszych parametrów

        logger.info("Rozpoczynam strojenie hiperparametrów Random Forest (Tuning)...")
        best_rf_model = tune_random_forest(X_train, y_train)
        y_pred = best_rf_model.predict(X_test)
        final_acc = accuracy_score(y_test, y_pred)
        logger.info(f"OSTATECZNY WYNIK TUNINGU: {final_acc:.4f}")
        joblib.dump(best_rf_model, models_dir / "best_rf_model_tuned.joblib")

        # ==========================================
        # KROK 6: HARDCORE (End-to-End Graph Neural Network)
        # ==========================================
        logger.info("====== ROZPOCZYNAMY ŚCIEŻKĘ 2: DEEP LEARNING (GNN) ======")
        # Przekazujemy nasz stary obiekt graph_data (który zrobiliśmy przed Node2Vec)
        gnn_model, gnn_acc = train_and_evaluate_gnn(graph_data, epochs=200)

        # Zapiszmy również ten model głęboki
        torch.save(gnn_model.state_dict(), models_dir / "best_gnn_model.pt")
        logger.info("Sieć grafowa (PyTorch) zapisana w folderze 'models/'.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
    finally:
        con.close()
        logger.info("Połączenie z DuckDB zamknięte.")


if __name__ == "__main__":
    main()
