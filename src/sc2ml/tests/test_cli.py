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

_CLI = "sc2ml.cli"


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------


class TestSetupLogging:
    def test_setup_logging_creates_handlers(self, tmp_path: Path) -> None:
        with patch(f"{_CLI}.Path", return_value=tmp_path / "logs"):
            from sc2ml.cli import setup_logging

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
    @patch(f"{_CLI}.assign_series_ids")
    @patch(f"{_CLI}.create_ml_views")
    @patch(f"{_CLI}.load_map_translations")
    @patch(f"{_CLI}.create_raw_enriched_view")
    @patch(f"{_CLI}.move_data_to_duck_db")
    def test_calls_five_steps_in_order(
        self, m_move, m_enrich, m_maps, m_views, m_series
    ) -> None:
        from sc2ml.cli import init_database

        con = MagicMock()
        init_database(con)

        m_move.assert_called_once_with(con, should_drop=False)
        m_enrich.assert_called_once_with(con)
        m_maps.assert_called_once_with(con)
        m_views.assert_called_once_with(con)
        m_series.assert_called_once_with(con)

    @patch(f"{_CLI}.assign_series_ids")
    @patch(f"{_CLI}.create_ml_views")
    @patch(f"{_CLI}.load_map_translations")
    @patch(f"{_CLI}.create_raw_enriched_view")
    @patch(f"{_CLI}.move_data_to_duck_db")
    def test_should_drop_forwarded(
        self, m_move, m_enrich, m_maps, m_views, m_series
    ) -> None:
        from sc2ml.cli import init_database

        con = MagicMock()
        init_database(con, should_drop=True)

        m_move.assert_called_once_with(con, should_drop=True)


# ---------------------------------------------------------------------------
# main — argument routing
# ---------------------------------------------------------------------------


class TestMainRouting:
    """Verify that argparse routes subcommands to the correct function."""

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}.duckdb")
    @patch(f"{_CLI}.init_database")
    def test_main_init(self, m_init, m_duckdb, m_log) -> None:
        from sc2ml.cli import main

        m_con = MagicMock()
        m_duckdb.connect.return_value = m_con

        with patch("sys.argv", ["sc2ml", "init"]):
            main()

        m_init.assert_called_once_with(m_con, should_drop=False)
        m_con.close.assert_called_once()

    @patch(f"{_CLI}.setup_logging")
    @patch(f"{_CLI}.duckdb")
    @patch(f"{_CLI}.init_database")
    def test_main_init_force(self, m_init, m_duckdb, m_log) -> None:
        from sc2ml.cli import main

        m_con = MagicMock()
        m_duckdb.connect.return_value = m_con

        with patch("sys.argv", ["sc2ml", "init", "--force"]):
            main()

        m_init.assert_called_once_with(m_con, should_drop=True)

