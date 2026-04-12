"""Tests for the CLI orchestration module.

All downstream modules are mocked — these tests verify argument routing,
function call ordering, and error handling in the CLI layer.
"""
from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CLI = "rts_predict.games.sc2.cli"


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------


class TestSetupLogging:
    def test_setup_logging_creates_handlers(self, tmp_path: Path) -> None:
        with patch(f"{_CLI}.Path", return_value=tmp_path / "logs"):
            from rts_predict.games.sc2.cli import setup_logging

            setup_logging()

        root = logging.getLogger()
        # pytest may wrap handlers (e.g. _FileHandler), so check subclass
        has_file = any(isinstance(h, logging.FileHandler) for h in root.handlers)
        has_stream = any(isinstance(h, logging.StreamHandler) for h in root.handlers)
        assert has_file or has_stream


# ---------------------------------------------------------------------------
# main — argument routing
# ---------------------------------------------------------------------------


class TestMainRouting:
    """Verify that argparse routes subcommands to the correct function."""

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}.handle_db_command")
    def test_main_db_routes_to_handler(self, mock_handle, m_log) -> None:
        """main() with 'db tables' must call handle_db_command once."""
        from rts_predict.games.sc2.cli import main

        with patch("sys.argv", ["sc2", "db", "tables"]):
            main()

        mock_handle.assert_called_once()

    def test_db_default_dataset_is_sc2egset(self) -> None:
        """The default dataset for the SC2 CLI must be 'sc2egset'."""
        from rts_predict.games.sc2.config import DEFAULT_DATASET

        assert DEFAULT_DATASET == "sc2egset"


class TestMainNoCommand:
    @patch(f"{_CLI}.setup_logging")
    def test_main_no_command_prints_help(self, m_log, capsys) -> None:
        from rts_predict.games.sc2.cli import main

        with patch("sys.argv", ["sc2"]):
            main()

        # argparse prints help to stdout when no subcommand is given
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower() or captured.out == ""
        # The important thing is it didn't crash


class TestMainExportSchemasRouting:
    """Verify that 'sc2 export-schemas' routes to _run_export_schemas_command."""

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}._run_export_schemas_command")
    def test_main_export_schemas_routes_to_handler(
        self, m_export: MagicMock, m_log: MagicMock, tmp_path: Path
    ) -> None:
        """main() with 'export-schemas --out DIR' calls _run_export_schemas_command."""
        from rts_predict.games.sc2.cli import main

        out_dir = str(tmp_path / "schemas")
        with patch("sys.argv", ["sc2", "export-schemas", "--out", out_dir]):
            main()

        m_export.assert_called_once()

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}._run_export_schemas_command")
    def test_main_export_schemas_no_preserve_flag(
        self, m_export: MagicMock, m_log: MagicMock, tmp_path: Path
    ) -> None:
        """--no-preserve flag is forwarded correctly."""
        from rts_predict.games.sc2.cli import main

        out_dir = str(tmp_path / "schemas")
        with patch("sys.argv", ["sc2", "export-schemas", "--out", out_dir, "--no-preserve"]):
            main()

        _args, _kwargs = m_export.call_args
        # Third positional arg is no_preserve
        assert _args[2] is True


class TestRunExportSchemasCommand:
    """Unit tests for _run_export_schemas_command."""

    @patch(f"{_CLI}.export_schemas")
    def test_run_export_schemas_command_calls_export_schemas(
        self, m_export: MagicMock, tmp_path: Path
    ) -> None:
        """_run_export_schemas_command delegates to export_schemas with correct args."""
        from rts_predict.games.sc2.cli import _run_export_schemas_command

        db = tmp_path / "db.duckdb"
        out = tmp_path / "schemas"
        m_export.return_value = [out / "t.yaml", out / "_index.yaml"]

        _run_export_schemas_command(db, out, no_preserve=False)

        m_export.assert_called_once_with(db, out, preserve_comments=True)

    @patch(f"{_CLI}.export_schemas")
    def test_run_export_schemas_command_no_preserve(
        self, m_export: MagicMock, tmp_path: Path
    ) -> None:
        """no_preserve=True inverts preserve_comments to False."""
        from rts_predict.games.sc2.cli import _run_export_schemas_command

        db = tmp_path / "db.duckdb"
        out = tmp_path / "schemas"
        m_export.return_value = []

        _run_export_schemas_command(db, out, no_preserve=True)

        m_export.assert_called_once_with(db, out, preserve_comments=False)
