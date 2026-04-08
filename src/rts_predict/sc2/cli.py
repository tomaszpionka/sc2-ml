from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import duckdb

from rts_predict.common.db import DuckDBClient
from rts_predict.common.db_cli import add_db_subparser, handle_db_command
from rts_predict.common.schema_export import export_schemas
from rts_predict.sc2.config import DATASETS, DEFAULT_DATASET, REPLAYS_SOURCE_DIR
from rts_predict.sc2.data.ingestion import (
    ingest_map_alias_files,
    load_game_events_to_duckdb,
    load_in_game_data_to_duckdb,
    load_tracker_events_to_duckdb,
    move_data_to_duck_db,
)

logger = logging.getLogger("SC2_Pipeline")


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
    """Ingest all Phase 0 raw data into DuckDB.

    Produces the following raw tables (no ML views, no derived cleaning):

    - ``raw`` — one row per SC2Replay JSON file (header/metadata fields).
    - ``raw_map_alias_files`` — verbatim map alias JSON keyed by tournament_dir.
    - ``tracker_events_raw`` — tracker events ingested from Parquet sources.
    - ``game_events_raw`` — game events ingested from Parquet sources.
    - ``match_player_map`` and ``player_stats`` — in-game player data from
      Parquet sources (via ``load_in_game_data_to_duckdb``).

    ML views (``flat_players``, ``matches_flat``) are intentionally NOT created
    here. They depend on cleaning rules and race normalisation established in
    Phase 1/2.

    Parameters
    ----------
    con : duckdb.DuckDBPyConnection
        Open connection to the target DuckDB database.
    should_drop : bool
        If True, drop and recreate the ``raw`` table from scratch.
    """
    logger.info("=== Initializing database (raw tables only) ===")
    move_data_to_duck_db(con, should_drop=should_drop)
    ingest_map_alias_files(con, REPLAYS_SOURCE_DIR)
    load_tracker_events_to_duckdb(con)
    load_game_events_to_duckdb(con)
    load_in_game_data_to_duckdb(con)
    logger.info("=== Database initialization complete ===")


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

    # export-schemas subcommand
    export_parser = subparsers.add_parser(
        "export-schemas",
        help="Export DuckDB table schemas to YAML files",
    )
    export_parser.add_argument(
        "--db",
        type=Path,
        default=DATASETS[DEFAULT_DATASET],
        help="Path to the DuckDB database file (default: sc2egset DB)",
    )
    export_parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output directory for YAML schema files",
    )
    export_parser.add_argument(
        "--no-preserve",
        action="store_true",
        help="Overwrite existing YAMLs without preserving comments and notes",
    )

    add_db_subparser(subparsers, DATASETS, DEFAULT_DATASET)

    args = parser.parse_args()

    if args.command == "init":
        with DuckDBClient(DATASETS[DEFAULT_DATASET]) as client:
            init_database(client.con, should_drop=args.force)

    elif args.command == "export-schemas":
        _run_export_schemas_command(args.db, args.out, args.no_preserve)

    elif args.command == "audit":
        _run_audit_command(args.steps)

    elif args.command == "explore":
        _run_explore_command(args.steps)

    elif args.command == "db":
        handle_db_command(args, DATASETS)

    else:
        parser.print_help()


def _run_explore_command(steps: list[str] | None) -> None:
    """Run Phase 1 corpus exploration."""
    from rts_predict.sc2.data.exploration import run_phase_1_exploration

    with DuckDBClient(DATASETS[DEFAULT_DATASET]) as client:
        results = run_phase_1_exploration(client.con, steps=steps)
        logger.info(f"Exploration complete. Steps run: {list(results.keys())}")


def _run_export_schemas_command(
    db: Path,
    out: Path,
    no_preserve: bool,
) -> None:
    """Export DuckDB table schemas to YAML files.

    Args:
        db: Path to the DuckDB database file.
        out: Output directory for YAML schema files.
        no_preserve: If True, overwrite existing YAMLs without preserving
            human-written comments and notes.
    """
    written = export_schemas(db, out, preserve_comments=not no_preserve)
    logger.info(f"export-schemas: wrote {len(written)} files to {out}")


def _run_audit_command(steps: list[str] | None) -> None:
    """Run Phase 0 ingestion audit."""
    from rts_predict.sc2.data.audit import run_phase_0_audit

    with DuckDBClient(DATASETS[DEFAULT_DATASET]) as client:
        results = run_phase_0_audit(client.con, steps=steps)
        logger.info(f"Audit complete. Steps run: {list(results.keys())}")


if __name__ == "__main__":  # pragma: no cover
    main()
