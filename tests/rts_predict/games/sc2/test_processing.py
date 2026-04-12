"""Tests for processing.py: raw_enriched view creation only.

Covers the safe subset of processing.py that survived quarantine.
All tests for assign_series_ids and get_matches_dataframe are in
_legacy/test_processing.py pending Phase 01 schema validation.
"""
import re

import duckdb
import pytest

from rts_predict.games.sc2.processing import create_raw_enriched_view


class TestCreateRawEnrichedView:
    """Test the raw_enriched view creation."""

    @pytest.fixture(autouse=True)
    def _setup_view(self, raw_table_con: duckdb.DuckDBPyConnection) -> None:
        create_raw_enriched_view(raw_table_con)
        self.con = raw_table_con

    def test_view_exists(self) -> None:
        """Scenario: create_raw_enriched_view creates the raw_enriched view."""
        row = self.con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_name = 'raw_enriched'"
        ).fetchone()
        assert row is not None
        assert row[0] > 0

    def test_tournament_dir_extracted(self) -> None:
        """Scenario: All rows have non-null tournament_dir."""
        row = self.con.execute(
            "SELECT count(*) FROM raw_enriched WHERE tournament_dir IS NULL"
        ).fetchone()
        assert row is not None
        assert row[0] == 0

    def test_replay_id_is_32_char_hex(self) -> None:
        """Scenario: All replay_ids are valid 32-char hex strings."""
        rows = self.con.execute("SELECT replay_id FROM raw_enriched").fetchall()
        for (rid,) in rows:
            assert re.fullmatch(r"[0-9a-f]{32}", rid), f"Invalid replay_id: {rid}"

    def test_preserves_all_raw_columns(self) -> None:
        """Scenario: raw_enriched has all original raw columns plus two new ones."""
        raw_cols = {
            c[0] for c in self.con.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'raw'"
            ).fetchall()
        }
        enriched_cols = {
            c[0] for c in self.con.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'raw_enriched'"
            ).fetchall()
        }
        assert raw_cols.issubset(enriched_cols)
        assert {"tournament_dir", "replay_id"}.issubset(enriched_cols)
