import logging
import sys
from pathlib import Path

import duckdb
import pandas as pd

from sc2ml.config import DB_FILE, PATCH_MIN_MATCHES
from sc2ml.data.processing import get_matches_dataframe, validate_data_split_sql
from sc2ml.features.elo import add_elo_features
from sc2ml.features.engineering import perform_feature_engineering, temporal_train_test_split
from sc2ml.gnn.embedder import append_embeddings_to_df, train_and_get_embeddings
from sc2ml.gnn.pipeline import build_starcraft_graph
from sc2ml.gnn.trainer import train_and_evaluate_gnn
from sc2ml.gnn.visualizer import visualize_gnn_space
from sc2ml.models.classical import train_and_evaluate_models

logger = logging.getLogger("SC2_Pipeline")

# Pipeline configuration — edit these to control which paths run
MODELS_TO_RUN = ["GNN"]  # Options: "CLASSIC", "NODE2VEC", "GNN"
EVALUATE_PER_PATCH = False
GLOBAL_TEST_SIZE = 0.05


def setup_logging() -> None:
    """Configure root logger with file and console handlers."""
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


def main() -> None:
    setup_logging()

    logger.info(
        f"Pipeline start. Active models: {MODELS_TO_RUN}. "
        f"Test size={GLOBAL_TEST_SIZE}, per-patch evaluation={EVALUATE_PER_PATCH}"
    )
    con = duckdb.connect(str(DB_FILE))

    try:
        # Stage 0: data validation
        validate_data_split_sql(con, split_ratio=(1 - GLOBAL_TEST_SIZE))

        raw_df = get_matches_dataframe(con)
        df_with_elo = add_elo_features(raw_df)
        df_with_elo["target"] = (df_with_elo["p1_result"] == "Win").astype(int)

        # Feature engineering (date column is preserved for temporal splitting)
        features_df = perform_feature_engineering(df_with_elo)

        # Stage 1: classical / Node2Vec path
        if "CLASSIC" in MODELS_TO_RUN or "NODE2VEC" in MODELS_TO_RUN:
            if "NODE2VEC" in MODELS_TO_RUN:
                graph_data, player_to_id = build_starcraft_graph(features_df)
                embs = train_and_get_embeddings(graph_data, player_to_id)
                features_df = append_embeddings_to_df(features_df, embs)

            X_train, X_test, y_train, y_test = temporal_train_test_split(
                features_df, test_size=GLOBAL_TEST_SIZE
            )
            train_and_evaluate_models(X_train, X_test, y_train, y_test)

        # Stage 2: GNN path
        if "GNN" in MODELS_TO_RUN:
            if EVALUATE_PER_PATCH:
                logger.info("====== PER-PATCH ANALYSIS (95/5 split) ======")
                patches = sorted(features_df["data_build"].unique())

                results = []
                for patch in patches:
                    patch_df = features_df[features_df["data_build"] == patch]
                    if len(patch_df) < PATCH_MIN_MATCHES:
                        continue

                    logger.info(f"--- Patch: {patch} (matches: {len(patch_df)}) ---")
                    graph_data, player_to_id = build_starcraft_graph(
                        patch_df, test_size=GLOBAL_TEST_SIZE
                    )
                    model_patch, acc = train_and_evaluate_gnn(
                        graph_data, epochs=100, test_size=GLOBAL_TEST_SIZE
                    )
                    results.append({"patch": patch, "acc": acc, "count": len(patch_df)})

                res_df = pd.DataFrame(results)
                logger.info(f"\nPer-patch accuracy summary:\n{res_df.to_string(index=False)}")
            else:
                # Standard global run
                graph_data, player_to_id = build_starcraft_graph(
                    features_df, test_size=GLOBAL_TEST_SIZE
                )
                model_patch, acc = train_and_evaluate_gnn(
                    graph_data, epochs=200, test_size=GLOBAL_TEST_SIZE
                )

            visualize_gnn_space(
                model_patch, graph_data, player_to_id, features_df, test_size=GLOBAL_TEST_SIZE
            )

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)

    finally:
        con.close()
        logger.info("DuckDB connection closed.")


if __name__ == "__main__":
    main()
