"""Tests for processing.py: series grouping, temporal split, and validation.

Uses an in-memory DuckDB with synthetic matches_flat data from conftest.py.
"""
import duckdb
import pytest

from rts_predict.sc2.data.processing import (
    assign_series_ids,
    create_raw_enriched_view,
    get_matches_dataframe,
)


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
        import re

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



class TestAssignSeriesIds:
    """Test best-of series grouping heuristic."""

    def test_creates_match_series_table(
        self, matches_flat_con: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: assign_series_ids creates the match_series table.
        Preconditions: matches_flat view with 100 synthetic matches.
        Assertions: match_series table exists in information_schema.
        """
        assign_series_ids(matches_flat_con)
        tables = matches_flat_con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_name = 'match_series'"
        ).fetchall()
        assert len(tables) == 1

    def test_all_matches_assigned(
        self, matches_flat_con: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: Every match_id in matches_flat gets a series assignment.
        Preconditions: matches_flat with 100 matches, assign_series_ids() called.
        Assertions: Zero unassigned match_ids (LEFT JOIN with NULL check).
        """
        assign_series_ids(matches_flat_con)
        # Every unique match_id from matches_flat should be in match_series
        row = matches_flat_con.execute("""
            SELECT count(DISTINCT m.match_id)
            FROM matches_flat m
            LEFT JOIN match_series ms ON m.match_id = ms.match_id
            WHERE ms.match_id IS NULL
        """).fetchone()
        assert row is not None
        assert row[0] == 0

    def test_series_sizes_reasonable(
        self, matches_flat_con: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: No series is unreasonably large (max Bo7 = 7 games).
        Preconditions: matches_flat with synthetic series, assign_series_ids() called.
        Assertions: Largest series has <= 10 matches.
        """
        assign_series_ids(matches_flat_con)
        row = matches_flat_con.execute("""
            SELECT MAX(cnt) FROM (
                SELECT series_id, COUNT(*) AS cnt
                FROM match_series
                GROUP BY series_id
            )
        """).fetchone()
        assert row is not None
        # Series should not be unreasonably large (max Bo7 = 7 games)
        assert row[0] <= 10

    def test_series_have_some_multi_game(
        self, matches_flat_con: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: At least one multi-game series detected in synthetic data.
        Preconditions: Synthetic data with deliberate series (every 5th match reuses pair).
        Assertions: At least one series has count > 1.
        """
        assign_series_ids(matches_flat_con)
        row = matches_flat_con.execute("""
            SELECT count(*) FROM (
                SELECT series_id, COUNT(*) AS cnt
                FROM match_series
                GROUP BY series_id
                HAVING cnt > 1
            )
        """).fetchone()
        assert row is not None
        assert row[0] > 0


class TestGetMatchesDataframe:
    """Tests for get_matches_dataframe() — fetches matches_flat into a DataFrame."""

    def test_returns_dataframe_without_split_table(
        self, matches_flat_con: duckdb.DuckDBPyConnection
    ) -> None:
        """When no match_split table exists, returns all rows as a DataFrame."""
        df = get_matches_dataframe(matches_flat_con)
        assert len(df) == 200  # 100 matches * 2 perspectives

    def test_with_split_table_no_filter(
        self, matches_flat_con: duckdb.DuckDBPyConnection
    ) -> None:
        """When match_split exists but split=None, returns all rows with split column."""
        matches_flat_con.execute("""
            CREATE TABLE match_split AS
            SELECT DISTINCT match_id, 'train' AS split FROM matches_flat
        """)
        df = get_matches_dataframe(matches_flat_con, split=None)
        assert len(df) > 0
        assert "split" in df.columns

    def test_with_split_filter_train(
        self, matches_flat_con: duckdb.DuckDBPyConnection
    ) -> None:
        """When split='train', only train rows are returned."""
        matches_flat_con.execute("""
            CREATE TABLE match_split AS
            SELECT DISTINCT match_id,
                CASE WHEN row_number() OVER () <= 70 THEN 'train' ELSE 'test' END AS split
            FROM matches_flat
        """)
        df = get_matches_dataframe(matches_flat_con, split="train")
        assert len(df) > 0

    def test_invalid_split_raises_value_error(
        self, matches_flat_con: duckdb.DuckDBPyConnection
    ) -> None:
        """An invalid split value must raise ValueError."""
        matches_flat_con.execute("""
            CREATE TABLE match_split AS
            SELECT DISTINCT match_id, 'train' AS split FROM matches_flat
        """)
        with pytest.raises(ValueError, match="Invalid split"):
            get_matches_dataframe(matches_flat_con, split="bogus")

    def test_no_split_table_with_split_arg_warns(
        self, matches_flat_con: duckdb.DuckDBPyConnection, caplog: pytest.LogCaptureFixture
    ) -> None:
        """When no match_split table and split is given, a warning is logged."""
        import logging

        with caplog.at_level(logging.WARNING):
            df = get_matches_dataframe(matches_flat_con, split="train")
        assert any("match_split" in msg for msg in caplog.messages)
        assert len(df) > 0
