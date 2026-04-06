"""AoE2 CLI — add `init`, `audit`, `explore` subcommands as data acquisition phases complete."""

import argparse
import logging
import sys
from pathlib import Path

from rts_predict.aoe2.config import DATASETS, DEFAULT_DATASET
from rts_predict.common.db_cli import add_db_subparser, handle_db_command

logger = logging.getLogger("AoE2_Pipeline")


def setup_logging() -> None:
    """Configure root logger with file and console handlers."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_dir / "aoe2_pipeline.log", mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def build_parser() -> argparse.ArgumentParser:
    """Build and return the AoE2 CLI argument parser."""
    parser = argparse.ArgumentParser(description="AoE2-ML pipeline")
    subparsers = parser.add_subparsers(dest="command")
    add_db_subparser(subparsers, DATASETS, DEFAULT_DATASET)
    return parser


def main() -> None:
    """Entry point for the AoE2 CLI."""
    setup_logging()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "db":
        handle_db_command(args, DATASETS)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
