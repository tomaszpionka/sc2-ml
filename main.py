import logging
import duckdb
from config import DB_FILE
from data_ingestion import slim_down_sc2_with_manifest, move_data_to_duck_db
from data_processing import create_ml_views, get_matches_dataframe
from ml_pipeline import perform_feature_engineering, temporal_train_test_split
from model_training import train_and_evaluate_models # <-- Nowy import

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("SC2_Pipeline")

def main():
    logger.info("Start SC2 ML Pipeline...")

    # Zostaw to odkomentowane, jeśli chcesz najpierw przetworzyć nowe powtórki:
    # slim_down_sc2_with_manifest()
    
    con = duckdb.connect(str(DB_FILE))
    
    try:
        # Zostaw odkomentowane, jeśli masz nowe dane do zrzucenia do DuckDB:
        # move_data_to_duck_db(con)
        
        create_ml_views(con)
        raw_df = get_matches_dataframe(con)
        
        features_df = perform_feature_engineering(raw_df)
        X_train, X_test, y_train, y_test = temporal_train_test_split(features_df, test_size=0.2)
        
        logger.info("Dane gotowe. Uruchamiam trenowanie i ewaluację modeli...")
        trained_models = train_and_evaluate_models(X_train, X_test, y_train, y_test)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
    finally:
        con.close()
        logger.info("Połączenie z DuckDB zamknięte.")

if __name__ == "__main__":
    main()