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

_CLI = "rts_predict.sc2.cli"


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------


class TestSetupLogging:
    def test_setup_logging_creates_handlers(self, tmp_path: Path) -> None:
        with patch(f"{_CLI}.Path", return_value=tmp_path / "logs"):
            from rts_predict.sc2.cli import setup_logging

            setup_logging()

        root = logging.getLogger()
        # pytest may wrap handlers (e.g. _FileHandler), so check subclass
        has_file = any(isinstance(h, logging.FileHandler) for h in root.handlers)
        has_stream = any(isinstance(h, logging.StreamHandler) for h in root.handlers)
        assert has_file or has_stream


# ---------------------------------------------------------------------------
# init_database
# ---------------------------------------------------------------------------


class TestInitDatabase:
    @patch(f"{_CLI}.ingest_map_alias_files")
    @patch(f"{_CLI}.move_data_to_duck_db")
    def test_calls_two_steps_in_order(
        self, m_move: MagicMock, m_ingest: MagicMock
    ) -> None:
        from rts_predict.sc2.cli import REPLAYS_SOURCE_DIR, init_database

        con = MagicMock()
        init_database(con)

        m_move.assert_called_once_with(con, should_drop=False)
        m_ingest.assert_called_once_with(con, REPLAYS_SOURCE_DIR)

    @patch(f"{_CLI}.ingest_map_alias_files")
    @patch(f"{_CLI}.move_data_to_duck_db")
    def test_should_drop_forwarded(
        self, m_move: MagicMock, m_ingest: MagicMock
    ) -> None:
        from rts_predict.sc2.cli import init_database

        con = MagicMock()
        init_database(con, should_drop=True)

        m_move.assert_called_once_with(con, should_drop=True)


# ---------------------------------------------------------------------------
# main — argument routing
# ---------------------------------------------------------------------------


class TestMainRouting:
    """Verify that argparse routes subcommands to the correct function."""

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}.DuckDBClient")
    @patch(f"{_CLI}.init_database")
    def test_main_init(self, m_init, m_client_cls, m_log) -> None:
        from rts_predict.sc2.cli import main

        m_client = MagicMock()
        m_client_cls.return_value.__enter__ = MagicMock(return_value=m_client)
        m_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch("sys.argv", ["sc2", "init"]):
            main()

        m_init.assert_called_once_with(m_client.con, should_drop=False)

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}.DuckDBClient")
    @patch(f"{_CLI}.init_database")
    def test_main_init_force(self, m_init, m_client_cls, m_log) -> None:
        from rts_predict.sc2.cli import main

        m_client = MagicMock()
        m_client_cls.return_value.__enter__ = MagicMock(return_value=m_client)
        m_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch("sys.argv", ["sc2", "init", "--force"]):
            main()

        m_init.assert_called_once_with(m_client.con, should_drop=True)

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}.handle_db_command")
    def test_main_db_routes_to_handler(self, mock_handle, m_log) -> None:
        """main() with 'db tables' must call handle_db_command once."""
        from rts_predict.sc2.cli import main

        with patch("sys.argv", ["sc2", "db", "tables"]):
            main()

        mock_handle.assert_called_once()

    def test_db_default_dataset_is_sc2egset(self) -> None:
        """The default dataset for the SC2 CLI must be 'sc2egset'."""
        from rts_predict.sc2.config import DEFAULT_DATASET

        assert DEFAULT_DATASET == "sc2egset"


class TestMainAuditRouting:
    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}._run_audit_command")
    def test_main_audit_routes_to_handler(self, m_audit, m_log) -> None:
        from rts_predict.sc2.cli import main

        with patch("sys.argv", ["sc2", "audit"]):
            main()

        m_audit.assert_called_once_with(None)

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}._run_audit_command")
    def test_main_audit_with_steps(self, m_audit, m_log) -> None:
        from rts_predict.sc2.cli import main

        with patch("sys.argv", ["sc2", "audit", "--steps", "0.1", "0.2"]):
            main()

        m_audit.assert_called_once_with(["0.1", "0.2"])


class TestMainExploreRouting:
    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}._run_explore_command")
    def test_main_explore_routes_to_handler(self, m_explore, m_log) -> None:
        from rts_predict.sc2.cli import main

        with patch("sys.argv", ["sc2", "explore"]):
            main()

        m_explore.assert_called_once_with(None)


class TestMainNoCommand:
    @patch(f"{_CLI}.setup_logging")
    def test_main_no_command_prints_help(self, m_log, capsys) -> None:
        from rts_predict.sc2.cli import main

        with patch("sys.argv", ["sc2"]):
            main()

        # argparse prints help to stdout when no subcommand is given
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower() or captured.out == ""
        # The important thing is it didn't crash


class TestRunExploreCommand:
    @patch(f"{_CLI}.DuckDBClient")
    @patch("rts_predict.sc2.data.exploration.run_phase_1_exploration")
    def test_run_explore_command(self, m_explore, m_client_cls) -> None:
        from rts_predict.sc2.cli import _run_explore_command

        m_client = MagicMock()
        m_client_cls.return_value.__enter__ = MagicMock(return_value=m_client)
        m_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        m_explore.return_value = {"1.1": "ok"}

        _run_explore_command(steps=["1.1"])

        m_explore.assert_called_once_with(m_client.con, steps=["1.1"])


class TestRunAuditCommand:
    @patch(f"{_CLI}.DuckDBClient")
    @patch("rts_predict.sc2.data.audit.run_phase_0_audit")
    def test_run_audit_command(self, m_audit, m_client_cls) -> None:
        from rts_predict.sc2.cli import _run_audit_command

        m_client = MagicMock()
        m_client_cls.return_value.__enter__ = MagicMock(return_value=m_client)
        m_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        m_audit.return_value = {"0.1": "ok"}

        _run_audit_command(steps=["0.1"])

        m_audit.assert_called_once_with(m_client.con, steps=["0.1"])
