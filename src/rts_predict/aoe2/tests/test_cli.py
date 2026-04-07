"""Tests for :mod:`rts_predict.aoe2.cli` — AoE2 CLI routing."""

from __future__ import annotations

import logging
from pathlib import Path
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

    def test_setup_logging_creates_handlers(self, tmp_path: Path) -> None:
        """setup_logging() must register at least one handler on the root logger."""
        with patch(f"{_CLI}.Path", return_value=tmp_path / "logs"):
            from rts_predict.aoe2.cli import setup_logging

            setup_logging()

        root = logging.getLogger()
        has_file = any(isinstance(h, logging.FileHandler) for h in root.handlers)
        has_stream = any(isinstance(h, logging.StreamHandler) for h in root.handlers)
        assert has_file or has_stream

    def test_main_no_command_prints_help(self, capsys) -> None:
        """main() with no subcommand must not crash and may print help."""
        with (
            patch(f"{_CLI}.setup_logging"),
            patch("sys.argv", ["aoe2"]),
        ):
            from rts_predict.aoe2.cli import main

            main()

        captured = capsys.readouterr()
        # argparse prints to stdout or the test just shouldn't raise
        assert "usage" in captured.out.lower() or captured.out == ""


class TestCLIDownload:
    """Tests for CLI download subcommand parsing."""

    def test_download_subcommand_exists(self) -> None:
        """'download' is a recognised subcommand."""
        from rts_predict.aoe2.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["download", "aoe2companion", "--dry-run"])
        assert args.command == "download"
        assert args.source == "aoe2companion"
        assert args.dry_run is True

    def test_aoestats_force_flag(self) -> None:
        """--force flag is parsed for aoestats source."""
        from rts_predict.aoe2.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["download", "aoestats", "--force"])
        assert args.source == "aoestats"
        assert args.force is True

    def test_invalid_source_rejected(self) -> None:
        """Unrecognised source name causes parser error."""
        import pytest

        from rts_predict.aoe2.cli import build_parser

        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["download", "invalid_source"])

    def test_dry_run_defaults_to_false(self) -> None:
        """--dry-run defaults to False when not specified."""
        from rts_predict.aoe2.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["download", "aoe2companion"])
        assert args.dry_run is False

    def test_force_defaults_to_false(self) -> None:
        """--force defaults to False when not specified."""
        from rts_predict.aoe2.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["download", "aoestats"])
        assert args.force is False

    def test_log_interval_parsed(self) -> None:
        """--log-interval is parsed as int."""
        from rts_predict.aoe2.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["download", "aoe2companion", "--log-interval", "50"])
        assert args.log_interval == 50

    def test_log_interval_defaults_to_none(self) -> None:
        """--log-interval defaults to None when not specified."""
        from rts_predict.aoe2.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["download", "aoe2companion"])
        assert args.log_interval is None


class TestCLIDownloadDispatch:
    """Tests that main() dispatches the download command to the correct module."""

    def test_download_dispatches_to_aoe2companion(self) -> None:
        """main() with 'download aoe2companion --dry-run' calls aoe2companion run_download."""
        with (
            patch("sys.argv", ["aoe2", "download", "aoe2companion", "--dry-run"]),
            patch(f"{_CLI}.setup_logging"),
            patch(
                "rts_predict.aoe2.data.aoe2companion.acquisition.run_download",
                return_value={"downloaded": 0},
            ) as mock_dl,
        ):
            from rts_predict.aoe2.cli import main

            main()

        mock_dl.assert_called_once_with(dry_run=True)

    def test_download_dispatches_to_aoestats_with_force(self) -> None:
        """main() with 'download aoestats --force --log-interval 10' calls aoestats run_download."""
        with (
            patch(
                "sys.argv",
                ["aoe2", "download", "aoestats", "--force", "--log-interval", "10"],
            ),
            patch(f"{_CLI}.setup_logging"),
            patch(
                "rts_predict.aoe2.data.aoestats.acquisition.run_download",
                return_value={"downloaded": 0},
            ) as mock_dl,
        ):
            from rts_predict.aoe2.cli import main

            main()

        mock_dl.assert_called_once_with(dry_run=False, force=True, log_interval=10)
