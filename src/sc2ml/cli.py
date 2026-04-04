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
    create_raw_enriched_view,
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
    create_raw_enriched_view(con)
    load_map_translations(con)
    create_ml_views(con)
    assign_series_ids(con)
    create_temporal_split(con)
    validate_temporal_split(con)
    logger.info("=== Database initialization complete ===")


def run_pipeline() -> None:
    """Run the ML training pipeline (assumes database is already initialized)."""
    setup_logging()
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

            _trained, _results = train_and_evaluate_models(
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

    # ablation subcommand
    subparsers.add_parser("ablation", help="Run feature group ablation study")

    # tune subcommand
    tune_parser = subparsers.add_parser("tune", help="Optuna tuning for top models")
    tune_parser.add_argument(
        "--trials", type=int, default=200, help="Number of Optuna trials"
    )

    # evaluate subcommand
    subparsers.add_parser("evaluate", help="Full evaluation with all metrics")

    # sanity subcommand
    subparsers.add_parser("sanity", help="Phase 0: data & model sanity validation")

    # audit subcommand
    audit_parser = subparsers.add_parser("audit", help="Phase 0: ingestion audit")
    audit_parser.add_argument(
        "--steps", nargs="*", default=None,
        help="Steps to run (e.g. 0.1 0.2). Omit for all.",
    )

    # explore subcommand
    explore_parser = subparsers.add_parser("explore", help="Phase 1: corpus exploration")
    explore_parser.add_argument(
        "--steps", nargs="*", default=None,
        help="Steps to run (e.g. 1.1 1.3). Omit for all.",
    )

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

    elif args.command == "ablation":
        _run_ablation_command()

    elif args.command == "tune":
        _run_tune_command(n_trials=args.trials)

    elif args.command == "evaluate":
        _run_evaluate_command()

    elif args.command == "sanity":
        _run_sanity_command()

    elif args.command == "audit":
        _run_audit_command(args.steps)

    elif args.command == "explore":
        _run_explore_command(args.steps)

    else:
        # Default: run pipeline (backward-compatible)
        run_pipeline()


def _load_data_and_features():
    """Common data loading for subcommands."""
    con = duckdb.connect(str(DB_FILE))
    try:
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
        return raw_df, series_df
    finally:
        con.close()


def _run_ablation_command() -> None:
    """Run the feature group ablation study."""
    from sc2ml.models.evaluation import run_feature_ablation
    from sc2ml.models.reporting import ExperimentReport

    raw_df, series_df = _load_data_and_features()
    results = run_feature_ablation(raw_df, series_df=series_df)

    report = ExperimentReport(ablation_results=results)
    report.to_markdown(Path("reports") / "ablation_results.md")
    report.to_json()
    logger.info("Ablation study complete.")


def _run_tune_command(n_trials: int = 200) -> None:
    """Run Optuna tuning for top models."""
    from sc2ml.data.cv import ExpandingWindowCV
    from sc2ml.models.evaluation import evaluate_model
    from sc2ml.models.tuning import tune_lgbm_optuna, tune_lr_grid, tune_xgb_optuna

    raw_df, series_df = _load_data_and_features()
    features_df = build_features(raw_df, series_df=series_df)
    X_train, X_val, X_test, y_train, y_val, y_test = split_for_ml(features_df)

    # Combine train+val for CV
    X_cv = pd.concat([X_train, X_val])
    y_cv = pd.concat([y_train, y_val])

    cv = ExpandingWindowCV(n_splits=5, min_train_frac=0.3)

    logger.info("Tuning LightGBM...")
    lgbm_pipeline = tune_lgbm_optuna(X_cv, y_cv, cv, n_trials=n_trials)
    lgbm_result = evaluate_model(lgbm_pipeline, X_test, y_test, "LightGBM (tuned)")

    logger.info("Tuning XGBoost...")
    xgb_pipeline = tune_xgb_optuna(X_cv, y_cv, cv, n_trials=n_trials)
    xgb_result = evaluate_model(xgb_pipeline, X_test, y_test, "XGBoost (tuned)")

    logger.info("Tuning Logistic Regression...")
    lr_pipeline = tune_lr_grid(X_cv, y_cv, cv)
    lr_result = evaluate_model(lr_pipeline, X_test, y_test, "LR (tuned)")

    from sc2ml.models.reporting import ExperimentReport
    report = ExperimentReport(model_results=[lgbm_result, xgb_result, lr_result])
    report.to_markdown(Path("reports") / "tuning_results.md")
    report.to_json()
    logger.info("Tuning complete.")


def _run_evaluate_command() -> None:
    """Full evaluation with all models, baselines, and analysis."""
    from sc2ml.models.baselines import build_baselines
    from sc2ml.models.evaluation import compare_models, evaluate_model

    raw_df, series_df = _load_data_and_features()
    features_df = build_features(raw_df, series_df=series_df)

    # Preserve metadata before splitting
    matchup_col = features_df.get("matchup_type")

    X_train, X_val, X_test, y_train, y_val, y_test = split_for_ml(features_df)

    # Align matchup_col with test set
    if matchup_col is not None:
        test_mask = features_df["split"] == "test"
        matchup_test = matchup_col[test_mask].reset_index(drop=True)
    else:
        matchup_test = None

    from sc2ml.config import VETERAN_MIN_GAMES
    veterans_mask = None
    if "p1_total_games_played" in X_test.columns:
        veterans_mask = (
            (X_test["p1_total_games_played"] >= VETERAN_MIN_GAMES)
            & (X_test["p2_total_games_played"] >= VETERAN_MIN_GAMES)
        )

    all_results = []

    # Train and evaluate baselines
    baselines = build_baselines()
    for name, baseline in baselines.items():
        baseline.fit(X_train, y_train)
        result = evaluate_model(
            baseline, X_test, y_test, name,
            matchup_col=matchup_test, veterans_mask=veterans_mask,
        )
        all_results.append(result)

    # Train and evaluate classical models
    _trained, classical_results = train_and_evaluate_models(
        X_train, X_test, y_train, y_test,
        X_val=X_val, y_val=y_val,
        matchup_col=matchup_test,
    )
    all_results.extend(classical_results)

    # Pairwise comparisons
    comparisons = compare_models(all_results)

    from sc2ml.models.reporting import ExperimentReport
    report = ExperimentReport(
        model_results=all_results,
        comparisons=comparisons,
    )
    report.to_markdown(Path("reports") / "full_evaluation.md")
    report.to_json()
    logger.info("Full evaluation complete.")


def _run_sanity_command() -> None:
    """Phase 0: Data & Model Sanity Validation (ROADMAP §3)."""
    from sc2ml.validation import run_full_sanity

    con = duckdb.connect(str(DB_FILE))
    try:
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

        # Preserve matchup info before splitting
        matchup_col = None
        if "matchup_type" in features_df.columns:
            test_mask = features_df["split"] == "test"
            matchup_col = features_df.loc[test_mask, "matchup_type"].reset_index(
                drop=True
            )

        X_train, X_val, X_test, y_train, y_val, y_test = split_for_ml(features_df)

        report = run_full_sanity(
            con, features_df,
            X_train, X_test, y_train, y_test,
            matchup_col=matchup_col,
        )

        # Write report to file
        report_path = Path("reports") / "sanity_validation.md"
        report_path.parent.mkdir(exist_ok=True)
        report_path.write_text(report.summary + "\n")
        logger.info(f"Sanity report written to {report_path}")

        if not report.all_passed:
            failures = [c for c in report.checks if not c.passed]
            logger.warning(
                f"{len(failures)} sanity checks FAILED — "
                "investigate before running experiments."
            )
    finally:
        con.close()


def _run_explore_command(steps: list[str] | None) -> None:
    """Run Phase 1 corpus exploration."""
    from sc2ml.data.exploration import run_phase_1_exploration

    con = duckdb.connect(str(DB_FILE))
    try:
        results = run_phase_1_exploration(con, steps=steps)
        logger.info(f"Exploration complete. Steps run: {list(results.keys())}")
    finally:
        con.close()
        logger.info("DuckDB connection closed.")


def _run_audit_command(steps: list[str] | None) -> None:
    """Run Phase 0 ingestion audit."""
    from sc2ml.data.audit import run_phase_0_audit

    con = duckdb.connect(str(DB_FILE))
    try:
        results = run_phase_0_audit(con, steps=steps)
        logger.info(f"Audit complete. Steps run: {list(results.keys())}")
    finally:
        con.close()
        logger.info("DuckDB connection closed.")


if __name__ == "__main__":
    main()
