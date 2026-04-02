import argparse
import logging
import sys
from pathlib import Path

import duckdb
import pandas as pd

from sc2ml.config import DB_FILE, PATCH_MIN_MATCHES
from sc2ml.data.ingestion import load_map_translations, move_data_to_duck_db
from sc2ml.data.processing import (
    assign_series_ids,
    create_ml_views,
    create_temporal_split,
    get_matches_dataframe,
    validate_data_split_sql,
    validate_temporal_split,
)
from sc2ml.features import build_features, split_for_ml
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


def init_database(con: duckdb.DuckDBPyConnection, *, should_drop: bool = False) -> None:
    """Run the full Path A data pipeline: ingest → views → series → split.

    Parameters
    ----------
    con : duckdb.DuckDBPyConnection
        Open connection to the target DuckDB database.
    should_drop : bool
        If True, drop and recreate the raw table from scratch.
    """
    logger.info("=== Initializing database (Path A) ===")
    move_data_to_duck_db(con, should_drop=should_drop)
    load_map_translations(con)
    create_ml_views(con)
    assign_series_ids(con)
    create_temporal_split(con)
    validate_temporal_split(con)
    logger.info("=== Database initialization complete ===")


def run_pipeline() -> None:
    """Run the ML training pipeline (assumes database is already initialized)."""
    logger.info(
        f"Pipeline start. Active models: {MODELS_TO_RUN}. "
        f"Test size={GLOBAL_TEST_SIZE}, per-patch evaluation={EVALUATE_PER_PATCH}"
    )
    con = duckdb.connect(str(DB_FILE))

    try:
        # Stage 0: data validation
        validate_data_split_sql(con, split_ratio=(1 - GLOBAL_TEST_SIZE))

        # Load series data if available (for Group E context features)
        row = con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_name = 'match_series'"
        ).fetchone()
        has_series = row is not None and row[0] > 0
        series_df = (
            con.execute("SELECT match_id, series_id FROM match_series").df()
            if has_series
            else None
        )

        raw_df = get_matches_dataframe(con)
        features_df = build_features(raw_df, series_df=series_df)

        # Stage 1: classical / Node2Vec path
        if "CLASSIC" in MODELS_TO_RUN or "NODE2VEC" in MODELS_TO_RUN:
            if "NODE2VEC" in MODELS_TO_RUN:
                graph_data, player_to_id = build_starcraft_graph(features_df)
                embs = train_and_get_embeddings(graph_data, player_to_id)
                features_df = append_embeddings_to_df(features_df, embs)

            if "split" in features_df.columns:
                X_train, X_val, X_test, y_train, y_val, y_test = split_for_ml(
                    features_df
                )
            else:
                # Fallback: simple chronological split when no split table exists
                from sc2ml.features.compat import temporal_train_test_split

                X_train, X_test, y_train, y_test = temporal_train_test_split(
                    features_df, test_size=GLOBAL_TEST_SIZE
                )
                # Drop string columns that would crash sklearn
                X_train = X_train.select_dtypes(include="number")
                X_test = X_test.select_dtypes(include="number")
                X_val, y_val = None, None

            train_and_evaluate_models(
                X_train, X_test, y_train, y_test, X_val=X_val, y_val=y_val
            )

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


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(description="SC2-ML pipeline")
    subparsers = parser.add_subparsers(dest="command")

    # init subcommand
    init_parser = subparsers.add_parser(
        "init", help="Initialize DuckDB from raw replay JSON files"
    )
    init_parser.add_argument(
        "--force", action="store_true", help="Drop and recreate the raw table"
    )

    # run subcommand
    subparsers.add_parser("run", help="Run the ML training pipeline")

    args = parser.parse_args()

    if args.command == "init":
        con = duckdb.connect(str(DB_FILE))
        try:
            init_database(con, should_drop=args.force)
        finally:
            con.close()
            logger.info("DuckDB connection closed.")

    elif args.command == "run":
        run_pipeline()

    else:
        # Default: run pipeline (backward-compatible)
        run_pipeline()


if __name__ == "__main__":
    main()
