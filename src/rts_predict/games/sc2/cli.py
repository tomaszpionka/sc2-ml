from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from rts_predict.common.db_cli import add_db_subparser, handle_db_command
from rts_predict.common.schema_export import export_schemas
from rts_predict.games.sc2.config import DATASETS, DEFAULT_DATASET

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


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(description="SC2-ML pipeline")
    subparsers = parser.add_subparsers(dest="command")

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

    if args.command == "export-schemas":
        _run_export_schemas_command(args.db, args.out, args.no_preserve)

    elif args.command == "db":
        handle_db_command(args, DATASETS)

    else:
        parser.print_help()


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


if __name__ == "__main__":  # pragma: no cover
    main()
