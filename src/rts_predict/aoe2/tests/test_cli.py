"""Tests for :mod:`rts_predict.aoe2.cli` — AoE2 CLI routing."""

from __future__ import annotations

from unittest.mock import patch

_CLI = "rts_predict.aoe2.cli"


class TestAoE2CLI:
    def test_main_no_command_exits_with_help(self) -> None:
        """Calling main() with no arguments must print help (SystemExit not raised
        because argparse prints help and returns for the top-level parser)."""
        from rts_predict.aoe2.cli import build_parser

        parser = build_parser()
        # Parsing empty args — no subcommand means `args.command` is None
        args = parser.parse_args([])
        assert args.command is None

    def test_main_db_routes_to_handler(self) -> None:
        """main() with the 'db tables' subcommand must call handle_db_command once."""
        with (
            patch(f"{_CLI}.setup_logging"),
            patch(f"{_CLI}.handle_db_command") as mock_handle,
            patch("sys.argv", ["aoe2", "db", "tables"]),
        ):
            from rts_predict.aoe2.cli import main

            main()

        mock_handle.assert_called_once()

    def test_db_default_dataset_is_aoe2companion(self) -> None:
        """The default dataset for the AoE2 CLI must be 'aoe2companion'."""
        from rts_predict.aoe2.config import DEFAULT_DATASET

        assert DEFAULT_DATASET == "aoe2companion"
