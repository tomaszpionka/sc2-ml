"""AoE2 CLI — add `init`, `audit`, `explore` subcommands as data acquisition phases complete."""

import argparse
import logging
import sys
from pathlib import Path

from rts_predict.aoe2.config import DATASETS, DEFAULT_DATASET
from rts_predict.common.db_cli import add_db_subparser, handle_db_command

logger = logging.getLogger("AoE2_Pipeline")


def _handle_download(args: argparse.Namespace) -> None:
    """Dispatch the download command to the appropriate source module.

    Args:
        args: Parsed CLI arguments with source, dry_run, force, log_interval.
    """
    kwargs: dict = {"dry_run": args.dry_run}
    if args.log_interval is not None:
        kwargs["log_interval"] = args.log_interval

    if args.source == "aoe2companion":
        import rts_predict.aoe2.data.aoe2companion.acquisition as _companion

        result = _companion.run_download(**kwargs)
    else:
        import rts_predict.aoe2.data.aoestats.acquisition as _aoestats

        kwargs["force"] = args.force
        result = _aoestats.run_download(**kwargs)

    logger.info("Download result: %s", result)


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

    download_parser = subparsers.add_parser(
        "download",
        help="Download raw data from AoE2 sources",
    )
    download_parser.add_argument(
        "source",
        choices=["aoe2companion", "aoestats"],
        help="Data source to download from",
    )
    download_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="List files to download without making HTTP requests",
    )
    download_parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Force download even for deferred sources (required for aoestats)",
    )
    download_parser.add_argument(
        "--log-interval",
        type=int,
        default=None,
        help="Log progress every N files (default: source-specific)",
    )

    return parser


def main() -> None:
    """Entry point for the AoE2 CLI."""
    setup_logging()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "db":
        handle_db_command(args, DATASETS)
    elif args.command == "download":
        _handle_download(args)
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()
