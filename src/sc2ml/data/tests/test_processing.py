"""Tests for processing.py: series grouping, temporal split, and validation.

Uses an in-memory DuckDB with synthetic matches_flat data from conftest.py.
"""
import duckdb
import pytest

from sc2ml.data.processing import (
    assign_series_ids,
    create_temporal_split,
    get_matches_dataframe,
    validate_temporal_split,
)


class TestAssignSeriesIds:
    """Test best-of series grouping heuristic."""

    def test_creates_match_series_table(
        self, matches_flat_con: duckdb.DuckDBPyConnection
    ) -> None:
        assign_series_ids(matches_flat_con)
        tables = matches_flat_con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_name = 'match_series'"
        ).fetchall()
        assert len(tables) == 1

    def test_all_matches_assigned(
        self, matches_flat_con: duckdb.DuckDBPyConnection
    ) -> None:
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
        """Our synthetic data has deliberate series — verify at least one exists."""
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
        tables = self.con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_name = 'match_split'"
        ).fetchall()
        assert len(tables) == 1

    def test_all_matches_have_split(self) -> None:
        unassigned = self.con.execute("""
            SELECT count(DISTINCT m.match_id)
            FROM matches_flat m
            LEFT JOIN match_split ms ON m.match_id = ms.match_id
            WHERE ms.split IS NULL
        """).fetchone()[0]
        assert unassigned == 0

    def test_three_splits_present(self) -> None:
        splits = self.con.execute(
            "SELECT DISTINCT split FROM match_split ORDER BY split"
        ).fetchall()
        split_names = {s[0] for s in splits}
        assert split_names == {"train", "val", "test"}

    def test_chronological_ordering(self) -> None:
        """max(train.time) < min(val.time) < min(test.time)."""
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
        """No series should span multiple splits."""
        violations = self.con.execute("""
            SELECT ms2.series_id, COUNT(DISTINCT ms1.split) AS split_count
            FROM match_split ms1
            JOIN match_series ms2 ON ms1.match_id = ms2.match_id
            GROUP BY ms2.series_id
            HAVING split_count > 1
        """).df()
        assert len(violations) == 0, f"Series span multiple splits: {violations}"

    def test_train_is_largest(self) -> None:
        counts = self.con.execute("""
            SELECT split, COUNT(DISTINCT match_id) AS cnt
            FROM match_split
            GROUP BY split
        """).df().set_index("split")
        assert counts.loc["train", "cnt"] > counts.loc["val", "cnt"]
        assert counts.loc["val", "cnt"] > counts.loc["test", "cnt"]

    def test_ratios_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="sum to 1.0"):
            create_temporal_split(self.con, 0.5, 0.5, 0.5)


class TestValidateTemporalSplit:
    """Smoke test — validate_temporal_split should not raise."""

    def test_runs_without_error(
        self, matches_flat_con: duckdb.DuckDBPyConnection
    ) -> None:
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
        df = get_matches_dataframe(self.con)
        assert "split" in df.columns
        assert set(df["split"].unique()) == {"train", "val", "test"}

    def test_filter_by_train(self) -> None:
        df = get_matches_dataframe(self.con, split="train")
        assert set(df["split"].unique()) == {"train"}

    def test_filter_by_test(self) -> None:
        df = get_matches_dataframe(self.con, split="test")
        assert set(df["split"].unique()) == {"test"}
        assert len(df) > 0

    def test_sorted_by_match_time(self) -> None:
        df = get_matches_dataframe(self.con)
        times = df["match_time"].tolist()
        assert times == sorted(times)

    def test_no_split_table_returns_all(self) -> None:
        """When match_split doesn't exist, return all rows without split column."""
        fresh_con = duckdb.connect(":memory:")
        fresh_con.execute(
            "CREATE TABLE matches_flat AS SELECT 'mid' AS match_id, "
            "TIMESTAMP '2023-01-01' AS match_time, 'a' AS p1_name"
        )
        df = get_matches_dataframe(fresh_con)
        assert "split" not in df.columns
        fresh_con.close()
