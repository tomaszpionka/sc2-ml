"""Tests for processing.py: series grouping, temporal split, and validation.

Uses an in-memory DuckDB with synthetic matches_flat data from conftest.py.
"""
import duckdb
import pytest

from sc2ml.data.processing import (
    assign_series_ids,
    create_ml_views,
    create_temporal_split,
    get_matches_dataframe,
    validate_temporal_split,
)


class TestCreateMlViews:
    """Test the flat_players and matches_flat view creation."""

    @pytest.fixture(autouse=True)
    def _setup_views(self, raw_table_con: duckdb.DuckDBPyConnection) -> None:
        create_ml_views(raw_table_con)
        self.con = raw_table_con

    def test_flat_players_view_exists(self) -> None:
        """
        Scenario: create_ml_views creates the flat_players view.
        Preconditions: raw table with 5 matches, map_translation table, create_ml_views() called.
        Assertions: flat_players exists in information_schema.
        """
        count = self.con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_name = 'flat_players'"
        ).fetchone()[0]
        assert count > 0

    def test_matches_flat_view_exists(self) -> None:
        """
        Scenario: create_ml_views creates the matches_flat view.
        Preconditions: raw table with 5 matches, create_ml_views() called.
        Assertions: matches_flat exists in information_schema.
        """
        count = self.con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_name = 'matches_flat'"
        ).fetchone()[0]
        assert count > 0

    def test_flat_players_row_count(self) -> None:
        """
        Scenario: flat_players view produces correct row count.
        Preconditions: raw table with 5 matches, create_ml_views() called.
        Assertions: flat_players has 10 rows (5 matches x 2 players).
        """
        count = self.con.execute("SELECT count(*) FROM flat_players").fetchone()[0]
        assert count == 10

    def test_matches_flat_row_count(self) -> None:
        """
        Scenario: matches_flat view has two perspective rows per match.
        Preconditions: raw table with 5 matches, create_ml_views() called.
        Assertions: matches_flat has 10 rows (5 matches x 2 perspectives).
        """
        count = self.con.execute("SELECT count(*) FROM matches_flat").fetchone()[0]
        assert count == 10

    def test_flat_players_excludes_casters(self) -> None:
        """
        Scenario: flat_players excludes non-player rows (observers/casters).
        Preconditions: raw table with Win/Loss results only, create_ml_views() called.
        Assertions: Only "Win" and "Loss" in result column.
        """
        results = self.con.execute(
            "SELECT DISTINCT result FROM flat_players"
        ).fetchall()
        result_set = {r[0] for r in results}
        assert result_set == {"Win", "Loss"}

    def test_player_names_are_lowercased(self) -> None:
        """
        Scenario: Player names are normalized to lowercase.
        Preconditions: raw table with mixed-case names, create_ml_views() called.
        Assertions: All player_name values are lowercase.
        """
        names = self.con.execute(
            "SELECT DISTINCT player_name FROM flat_players"
        ).fetchall()
        for (name,) in names:
            assert name == name.lower()

    def test_map_translation_applied(self) -> None:
        """
        Scenario: Foreign map names are translated to English via map_translation table.
        Preconditions: raw table with "MapKorean", map_translation maps it to English.
        Assertions: "Map English LE" present; "MapKorean" absent.
        """
        map_names = self.con.execute(
            "SELECT DISTINCT map_name FROM flat_players"
        ).fetchall()
        name_set = {r[0] for r in map_names}
        assert "Map English LE" in name_set
        assert "MapKorean" not in name_set

    def test_match_time_is_timestamp(self) -> None:
        """
        Scenario: match_time column is a non-null timestamp.
        Preconditions: raw table with details.timeUTC, create_ml_views() called.
        Assertions: First row's match_time is not None.
        """
        row = self.con.execute(
            "SELECT match_time FROM flat_players LIMIT 1"
        ).fetchone()
        assert row is not None
        assert row[0] is not None

    def test_matches_flat_has_expected_columns(self) -> None:
        """
        Scenario: matches_flat view schema includes all required ML columns.
        Preconditions: create_ml_views() called on raw table.
        Assertions: All expected ML columns present (IDs, names, races, APM, etc.).
        """
        columns = self.con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'matches_flat'"
        ).fetchall()
        col_names = {c[0] for c in columns}
        expected = {
            "match_id", "match_time", "tournament_name", "game_loops",
            "data_build", "game_version", "map_name",
            "p1_name", "p2_name", "p1_race", "p2_race",
            "p1_apm", "p1_sq", "p2_apm", "p2_sq", "p1_result",
        }
        assert expected.issubset(col_names)

    def test_race_names_are_normalized(self) -> None:
        """
        Scenario: Abbreviated race names expanded to full names.
        Preconditions: raw table with "Terr"/"Prot" abbreviations, create_ml_views() called.
        Assertions: Only "Terran", "Protoss", "Zerg" in race column.
        """
        races = self.con.execute(
            "SELECT DISTINCT race FROM flat_players"
        ).fetchall()
        race_set = {r[0] for r in races}
        assert race_set.issubset({"Terran", "Protoss", "Zerg"})
        assert "Terr" not in race_set
        assert "Prot" not in race_set

    def test_game_version_column_present(self) -> None:
        """
        Scenario: game_version column is available and non-null.
        Preconditions: raw table with metadata.gameVersion, create_ml_views() called.
        Assertions: First row's game_version is not None.
        """
        row = self.con.execute(
            "SELECT game_version FROM flat_players LIMIT 1"
        ).fetchone()
        assert row is not None
        assert row[0] is not None

    def test_matches_flat_both_perspectives(self) -> None:
        """
        Scenario: Each match appears exactly twice (one per player perspective).
        Preconditions: create_ml_views() called on 5-match raw table.
        Assertions: Every match_id has count == 2.
        """
        perspectives = self.con.execute("""
            SELECT match_id, count(*) AS cnt
            FROM matches_flat
            GROUP BY match_id
        """).df()
        assert (perspectives["cnt"] == 2).all()

    def test_get_matches_dataframe_invalid_split_raises(self) -> None:
        """
        Scenario: Invalid split name raises ValueError.
        Preconditions: match_split table exists with valid splits.
        Assertions: ValueError with "Invalid split" for split="invalid".
        """
        assign_series_ids(self.con)
        create_temporal_split(self.con)
        with pytest.raises(ValueError, match="Invalid split"):
            get_matches_dataframe(self.con, split="invalid")


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
        unassigned = matches_flat_con.execute("""
            SELECT count(DISTINCT m.match_id)
            FROM matches_flat m
            LEFT JOIN match_series ms ON m.match_id = ms.match_id
            WHERE ms.match_id IS NULL
        """).fetchone()[0]
        assert unassigned == 0

    def test_series_sizes_reasonable(
        self, matches_flat_con: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: No series is unreasonably large (max Bo7 = 7 games).
        Preconditions: matches_flat with synthetic series, assign_series_ids() called.
        Assertions: Largest series has <= 10 matches.
        """
        assign_series_ids(matches_flat_con)
        max_size = matches_flat_con.execute("""
            SELECT MAX(cnt) FROM (
                SELECT series_id, COUNT(*) AS cnt
                FROM match_series
                GROUP BY series_id
            )
        """).fetchone()[0]
        # Series should not be unreasonably large (max Bo7 = 7 games)
        assert max_size <= 10

    def test_series_have_some_multi_game(
        self, matches_flat_con: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: At least one multi-game series detected in synthetic data.
        Preconditions: Synthetic data with deliberate series (every 5th match reuses pair).
        Assertions: At least one series has count > 1.
        """
        assign_series_ids(matches_flat_con)
        multi = matches_flat_con.execute("""
            SELECT count(*) FROM (
                SELECT series_id, COUNT(*) AS cnt
                FROM match_series
                GROUP BY series_id
                HAVING cnt > 1
            )
        """).fetchone()[0]
        assert multi > 0


class TestCreateTemporalSplit:
    """Test 80/15/5 temporal split with series-aware boundaries."""

    @pytest.fixture(autouse=True)
    def _setup_split(self, matches_flat_con: duckdb.DuckDBPyConnection) -> None:
        assign_series_ids(matches_flat_con)
        create_temporal_split(matches_flat_con)
        self.con = matches_flat_con

    def test_match_split_table_exists(self) -> None:
        """
        Scenario: create_temporal_split creates the match_split table.
        Preconditions: matches_flat with series assigned, create_temporal_split() called.
        Assertions: match_split table exists in information_schema.
        """
        tables = self.con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_name = 'match_split'"
        ).fetchall()
        assert len(tables) == 1

    def test_all_matches_have_split(self) -> None:
        """
        Scenario: Every match_id gets assigned to a split.
        Preconditions: matches_flat with temporal split applied.
        Assertions: Zero unassigned match_ids.
        """
        unassigned = self.con.execute("""
            SELECT count(DISTINCT m.match_id)
            FROM matches_flat m
            LEFT JOIN match_split ms ON m.match_id = ms.match_id
            WHERE ms.split IS NULL
        """).fetchone()[0]
        assert unassigned == 0

    def test_three_splits_present(self) -> None:
        """
        Scenario: Temporal split produces exactly three partitions.
        Preconditions: create_temporal_split() called with default ratios.
        Assertions: Split names are exactly {"train", "val", "test"}.
        """
        splits = self.con.execute(
            "SELECT DISTINCT split FROM match_split ORDER BY split"
        ).fetchall()
        split_names = {s[0] for s in splits}
        assert split_names == {"train", "val", "test"}

    def test_chronological_ordering(self) -> None:
        """
        Scenario: Splits are strictly chronologically ordered.
        Preconditions: Temporal split applied to time-sorted matches.
        Assertions: max(train.time) < min(val.time) < min(test.time).
        """
        boundaries = self.con.execute("""
            SELECT
                ms.split,
                MIN(m.match_time) AS min_time,
                MAX(m.match_time) AS max_time
            FROM match_split ms
            JOIN matches_flat m ON ms.match_id = m.match_id
            WHERE m.p1_name < m.p2_name
            GROUP BY ms.split
            ORDER BY min_time
        """).df()
        boundaries = boundaries.set_index("split")
        assert boundaries.loc["train", "max_time"] < boundaries.loc["val", "min_time"]
        assert boundaries.loc["val", "max_time"] < boundaries.loc["test", "min_time"]

    def test_series_integrity(self) -> None:
        """
        Scenario: No best-of series is split across temporal partitions.
        Preconditions: Temporal split with series-aware boundaries.
        Assertions: Every series_id appears in exactly one split.
        """
        violations = self.con.execute("""
            SELECT ms2.series_id, COUNT(DISTINCT ms1.split) AS split_count
            FROM match_split ms1
            JOIN match_series ms2 ON ms1.match_id = ms2.match_id
            GROUP BY ms2.series_id
            HAVING split_count > 1
        """).df()
        assert len(violations) == 0, f"Series span multiple splits: {violations}"

    def test_train_is_largest(self) -> None:
        """
        Scenario: Split sizes follow train > val > test ordering.
        Preconditions: Temporal split with default 80/15/5 ratios.
        Assertions: Train match count > val > test.
        """
        counts = self.con.execute("""
            SELECT split, COUNT(DISTINCT match_id) AS cnt
            FROM match_split
            GROUP BY split
        """).df().set_index("split")
        assert counts.loc["train", "cnt"] > counts.loc["val", "cnt"]
        assert counts.loc["val", "cnt"] > counts.loc["test", "cnt"]

    def test_ratios_invalid_raises(self) -> None:
        """
        Scenario: Ratios that don't sum to 1.0 raise ValueError.
        Preconditions: create_temporal_split called with 0.5/0.5/0.5.
        Assertions: ValueError with "sum to 1.0" in message.
        """
        with pytest.raises(ValueError, match="sum to 1.0"):
            create_temporal_split(self.con, 0.5, 0.5, 0.5)


class TestValidateTemporalSplit:
    """Smoke test — validate_temporal_split should not raise."""

    def test_runs_without_error(
        self, matches_flat_con: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: validate_temporal_split completes without raising.
        Preconditions: Full pipeline: matches_flat -> series -> temporal split.
        Assertions: No exception raised.
        """
        assign_series_ids(matches_flat_con)
        create_temporal_split(matches_flat_con)
        validate_temporal_split(matches_flat_con)


class TestGetMatchesDataframe:
    """Test the updated get_matches_dataframe with split filtering."""

    @pytest.fixture(autouse=True)
    def _setup(self, matches_flat_con: duckdb.DuckDBPyConnection) -> None:
        assign_series_ids(matches_flat_con)
        create_temporal_split(matches_flat_con)
        self.con = matches_flat_con

    def test_returns_all_with_split_column(self) -> None:
        """
        Scenario: get_matches_dataframe returns all rows with split column.
        Preconditions: match_split table exists with train/val/test.
        Assertions: "split" column present; all three split values appear.
        """
        df = get_matches_dataframe(self.con)
        assert "split" in df.columns
        assert set(df["split"].unique()) == {"train", "val", "test"}

    def test_filter_by_train(self) -> None:
        """
        Scenario: Filtering by split="train" returns only train rows.
        Preconditions: match_split table exists.
        Assertions: All rows have split == "train".
        """
        df = get_matches_dataframe(self.con, split="train")
        assert set(df["split"].unique()) == {"train"}

    def test_filter_by_test(self) -> None:
        """
        Scenario: Filtering by split="test" returns only test rows.
        Preconditions: match_split table exists.
        Assertions: All rows have split == "test"; non-empty result.
        """
        df = get_matches_dataframe(self.con, split="test")
        assert set(df["split"].unique()) == {"test"}
        assert len(df) > 0

    def test_sorted_by_match_time(self) -> None:
        """
        Scenario: Returned DataFrame is sorted by match_time ascending.
        Preconditions: match_split table exists.
        Assertions: match_time values are in sorted order.
        """
        df = get_matches_dataframe(self.con)
        times = df["match_time"].tolist()
        assert times == sorted(times)

    def test_no_split_table_returns_all(self) -> None:
        """
        Scenario: Without match_split table, all rows returned without split column.
        Preconditions: Fresh DuckDB with matches_flat but no match_split.
        Assertions: DataFrame has no "split" column.
        """
        fresh_con = duckdb.connect(":memory:")
        fresh_con.execute(
            "CREATE TABLE matches_flat AS SELECT 'mid' AS match_id, "
            "TIMESTAMP '2023-01-01' AS match_time, 'a' AS p1_name"
        )
        df = get_matches_dataframe(fresh_con)
        assert "split" not in df.columns
        fresh_con.close()

    def test_no_split_table_warns_on_split_arg(self, caplog) -> None:
        """
        Scenario: Requesting a split when match_split table doesn't exist logs a warning.
        Preconditions: Fresh DuckDB with matches_flat but no match_split, split="train" requested.
        Assertions: Warning "match_split table does not exist" logged; no split column in result.
        """
        import logging

        fresh_con = duckdb.connect(":memory:")
        fresh_con.execute(
            "CREATE TABLE matches_flat AS SELECT 'mid' AS match_id, "
            "TIMESTAMP '2023-01-01' AS match_time, 'a' AS p1_name"
        )
        with caplog.at_level(logging.WARNING, logger="sc2ml.data.processing"):
            df = get_matches_dataframe(fresh_con, split="train")
        assert any("match_split table does not exist" in m for m in caplog.messages)
        assert "split" not in df.columns
        fresh_con.close()


class TestValidateDataSplitSql:
    """Tests for validate_data_split_sql (lines 166-207)."""

    def test_runs_without_error(
        self, matches_flat_con: duckdb.DuckDBPyConnection
    ) -> None:
        """
        Scenario: validate_data_split_sql completes without raising.
        Preconditions: matches_flat view with synthetic data.
        Assertions: No exception raised.
        """
        from sc2ml.data.processing import validate_data_split_sql
        validate_data_split_sql(matches_flat_con)

    def test_logs_distribution(
        self, matches_flat_con: duckdb.DuckDBPyConnection, caplog
    ) -> None:
        """
        Scenario: validate_data_split_sql logs year distribution and chronological validation.
        Preconditions: matches_flat view, INFO-level logging captured.
        Assertions: "Annual match distribution" and "Chronological validation" in log messages.
        """
        import logging

        from sc2ml.data.processing import validate_data_split_sql
        with caplog.at_level(logging.INFO, logger="sc2ml.data.processing"):
            validate_data_split_sql(matches_flat_con)
        messages = " ".join(caplog.messages)
        assert "Annual match distribution" in messages
        assert "Chronological validation" in messages


class TestValidateTemporalSplitDetailed:
    """Detailed tests for validate_temporal_split (lines 403-476)."""

    @pytest.fixture(autouse=True)
    def _setup_split(self, matches_flat_con: duckdb.DuckDBPyConnection) -> None:
        assign_series_ids(matches_flat_con)
        create_temporal_split(matches_flat_con)
        self.con = matches_flat_con

    def test_logs_boundaries(self, caplog) -> None:
        """
        Scenario: validate_temporal_split logs split boundary information.
        Preconditions: Full pipeline applied, INFO-level logging captured.
        Assertions: "Split boundaries" appears in log messages.
        """
        import logging
        with caplog.at_level(logging.INFO, logger="sc2ml.data.processing"):
            validate_temporal_split(self.con)
        messages = " ".join(caplog.messages)
        assert "Split boundaries" in messages

    def test_logs_series_integrity(self, caplog) -> None:
        """
        Scenario: validate_temporal_split logs series integrity check result.
        Preconditions: Full pipeline applied, INFO-level logging captured.
        Assertions: "Series integrity" appears in log messages.
        """
        import logging
        with caplog.at_level(logging.INFO, logger="sc2ml.data.processing"):
            validate_temporal_split(self.con)
        messages = " ".join(caplog.messages)
        assert "Series integrity" in messages

    def test_logs_year_distribution(self, caplog) -> None:
        """
        Scenario: validate_temporal_split logs year distribution per split.
        Preconditions: Full pipeline applied, INFO-level logging captured.
        Assertions: "Year distribution per split" appears in log messages.
        """
        import logging
        with caplog.at_level(logging.INFO, logger="sc2ml.data.processing"):
            validate_temporal_split(self.con)
        messages = " ".join(caplog.messages)
        assert "Year distribution per split" in messages
