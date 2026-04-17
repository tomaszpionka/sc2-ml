"""Unit tests for rts_predict.common.missingness_audit.

Uses in-memory DuckDB fixtures to achieve 100% line coverage of the module
without touching any real dataset files.
"""
from __future__ import annotations

import duckdb
import pandas as pd
import pytest

from rts_predict.common.missingness_audit import (
    _build_sentinel_predicate,
    _consolidate_ledger,
    _detect_constants,
    _recommend,
    _sentinel_census,  # noqa: PLC2701
    build_audit_views_block,
)

# ---------------------------------------------------------------------------
# Module-level fixture: in-memory DuckDB with VIEW test_view
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def audit_con() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB connection with VIEW test_view.

    Schema (5 rows):
        id     BIGINT   — identity, never NULL
        score  INTEGER  — some NULLs
        tag    VARCHAR  — sentinel 'unknown'
        flag   BOOLEAN  — all same value (true constant = TRUE)
        result VARCHAR  — target column, one NULL row
    """
    con = duckdb.connect()
    con.execute("""
        CREATE VIEW test_view AS
        SELECT * FROM (VALUES
            (1, 10,        'good',    TRUE, 'Win'),
            (2, NULL,      'unknown', TRUE, 'Loss'),
            (3, 30,        'good',    TRUE, 'Win'),
            (4, NULL,      'unknown', TRUE, NULL),
            (5, 50,        'good',    TRUE, 'Win')
        ) t(id, score, tag, flag, result)
    """)
    return con


# ---------------------------------------------------------------------------
# Tests for _build_sentinel_predicate
# ---------------------------------------------------------------------------

class TestBuildSentinelPredicate:
    def test_none_sentinel_returns_none_pair(self):
        pred, rep = _build_sentinel_predicate("col", None)
        assert pred is None
        assert rep is None

    def test_integer_sentinel(self):
        pred, rep = _build_sentinel_predicate("col", 0)
        assert pred == "= 0"
        assert rep == "0"

    def test_string_sentinel(self):
        pred, rep = _build_sentinel_predicate("col", "val")
        assert pred == "= 'val'"
        assert rep == "'val'"

    def test_string_sentinel_with_single_quote(self):
        pred, rep = _build_sentinel_predicate("col", "it's")
        assert pred == "= 'it''s'"
        # repr("it's") → '"it\'s"' — verify the string value contains the apostrophe
        assert "it's" in rep

    def test_list_of_ints(self):
        pred, rep = _build_sentinel_predicate("col", [0, 1])
        assert pred == "IN (0, 1)"
        assert rep == "[0, 1]"

    def test_list_of_strings(self):
        pred, rep = _build_sentinel_predicate("col", ["a", "b"])
        assert pred == "IN ('a', 'b')"
        assert rep == "['a', 'b']"


# ---------------------------------------------------------------------------
# Tests for _sentinel_census
# ---------------------------------------------------------------------------

class TestSentinelCensus:
    def test_happy_path_returns_correct_counts(self, audit_con):
        spec = {
            "tag": {
                "sentinel_value": "unknown",
                "mechanism": "MCAR",
                "justification": "test",
                "carries_semantic_content": False,
                "is_primary_feature": False,
            }
        }
        rows = _sentinel_census("test_view", 5, spec, audit_con)
        assert len(rows) == 1
        row = rows[0]
        assert row["column"] == "tag"
        assert row["n_sentinel"] == 2
        assert row["pct_sentinel"] == pytest.approx(40.0)

    def test_empty_spec_returns_empty_list(self, audit_con):
        rows = _sentinel_census("test_view", 5, {}, audit_con)
        assert rows == []

    def test_column_absent_from_view_returns_zero(self, audit_con):
        """Column in spec but not in VIEW — except Exception guard fires."""
        spec = {
            "nonexistent_col": {
                "sentinel_value": -1,
                "mechanism": "MAR",
                "justification": "test",
                "carries_semantic_content": False,
                "is_primary_feature": False,
            }
        }
        rows = _sentinel_census("test_view", 5, spec, audit_con)
        assert len(rows) == 1
        assert rows[0]["n_sentinel"] == 0

    def test_none_sentinel_value_returns_zero(self, audit_con):
        """Spec entry with sentinel_value=None → predicate is None → n_sentinel=0."""
        spec = {
            "score": {
                "sentinel_value": None,
                "mechanism": "MAR",
                "justification": "test",
                "carries_semantic_content": False,
                "is_primary_feature": False,
            }
        }
        rows = _sentinel_census("test_view", 5, spec, audit_con)
        assert len(rows) == 1
        assert rows[0]["n_sentinel"] == 0
        assert rows[0]["sentinel_value"] is None

    def test_total_rows_zero_no_division_error(self, audit_con):
        spec = {
            "tag": {
                "sentinel_value": "unknown",
                "mechanism": "MCAR",
                "justification": "test",
                "carries_semantic_content": False,
                "is_primary_feature": False,
            }
        }
        # total_rows=0: pct should be 0.0 without ZeroDivisionError
        rows = _sentinel_census("test_view", 0, spec, audit_con)
        assert rows[0]["pct_sentinel"] == 0.0


# ---------------------------------------------------------------------------
# Tests for _detect_constants
# ---------------------------------------------------------------------------

class TestDetectConstants:
    def test_non_identity_column_returns_n_distinct(self, audit_con):
        result = _detect_constants("test_view", ["score"], audit_con)
        # score has values: 10, NULL, 30, NULL, 50 → 3 distinct non-NULL values
        # COUNT(DISTINCT) in DuckDB excludes NULLs
        assert "score" in result
        assert result["score"] == 3

    def test_identity_column_returns_none(self, audit_con):
        result = _detect_constants(
            "test_view", ["id"], audit_con, identity_cols=frozenset({"id"})
        )
        assert result["id"] is None

    def test_empty_columns_returns_empty_dict(self, audit_con):
        result = _detect_constants("test_view", [], audit_con)
        assert result == {}


# ---------------------------------------------------------------------------
# Tests for _recommend
# ---------------------------------------------------------------------------

class TestRecommend:
    def test_w3_sentinel_only_low_rate(self):
        """W3 branch: n_sentinel > 0 and n_null == 0 and pct < 5."""
        code, just = _recommend("col", "MCAR", 2.0, False, n_null=0, n_sentinel=10)
        assert code == "CONVERT_SENTINEL_TO_NULL"
        assert "NULLIF" in just

    def test_f1_zero_missingness(self):
        """F1: pct == 0.0 → RETAIN_AS_IS."""
        code, just = _recommend("col", "N/A", 0.0, False, n_null=0, n_sentinel=0)
        assert code == "RETAIN_AS_IS"

    def test_high_rate_drop(self):
        """pct > 80.0 → DROP_COLUMN."""
        code, just = _recommend("col", "MAR", 85.0, False, n_null=1000, n_sentinel=0)
        assert code == "DROP_COLUMN"
        assert "80%" in just

    def test_mid_mnar_drop(self):
        """pct > 40.0, mechanism=MNAR → DROP_COLUMN."""
        code, just = _recommend("col", "MNAR", 55.0, False, n_null=500, n_sentinel=0)
        assert code == "DROP_COLUMN"
        assert "MNAR" in just

    def test_mid_primary_flag(self):
        """pct > 40.0, is_primary=True, MAR → FLAG_FOR_IMPUTATION."""
        code, just = _recommend("col", "MAR", 55.0, True, n_null=500, n_sentinel=0)
        assert code == "FLAG_FOR_IMPUTATION"

    def test_mid_non_primary_drop(self):
        """pct > 40.0, is_primary=False, MAR → DROP_COLUMN."""
        code, just = _recommend("col", "MAR", 55.0, False, n_null=500, n_sentinel=0)
        assert code == "DROP_COLUMN"

    def test_mid_low_rate_flag(self):
        """5.0 < pct <= 40.0 → FLAG_FOR_IMPUTATION."""
        code, just = _recommend("col", "MAR", 20.0, False, n_null=200, n_sentinel=0)
        assert code == "FLAG_FOR_IMPUTATION"

    def test_low_with_nulls_retain(self):
        """pct < 5.0, n_null > 0 (not W3 — has NULLs) → RETAIN_AS_IS."""
        code, just = _recommend("col", "MAR", 2.0, False, n_null=5, n_sentinel=0)
        assert code == "RETAIN_AS_IS"
        assert "5%" in just


# ---------------------------------------------------------------------------
# Tests for _consolidate_ledger
# ---------------------------------------------------------------------------

def _make_null_df(col_names_nulls: list[tuple[str, int]], total: int) -> pd.DataFrame:
    """Build a minimal null-census DataFrame for _consolidate_ledger."""
    return pd.DataFrame(
        [
            {
                "column_name": col,
                "null_count": nc,
                "null_pct": round(100.0 * nc / total, 4) if total > 0 else 0.0,
            }
            for col, nc in col_names_nulls
        ]
    )


class TestConsolidateLedger:
    VIEW = "test_view"
    TOTAL = 5
    DTYPE_MAP = {
        "id": "BIGINT",
        "score": "INTEGER",
        "tag": "VARCHAR",
        "flag": "BOOLEAN",
        "result": "VARCHAR",
    }

    def _run(
        self,
        col_nulls: list[tuple[str, int]],
        sentinel_rows: list[dict],
        spec: dict,
        constants_map: dict,
        target_cols: set,
        identity_cols: frozenset = frozenset(),
    ) -> pd.DataFrame:
        df_null = _make_null_df(col_nulls, self.TOTAL)
        return _consolidate_ledger(
            self.VIEW,
            df_null,
            sentinel_rows,
            spec,
            self.DTYPE_MAP,
            self.TOTAL,
            constants_map,
            target_cols,
            identity_cols,
        )

    def test_identity_column(self):
        df = self._run(
            [("id", 0)],
            [],
            {},
            {"id": None},
            set(),
            frozenset({"id"}),
        )
        row = df.iloc[0]
        assert row["mechanism"] == "N/A"
        assert row["recommendation"] == "RETAIN_AS_IS"
        assert row["n_distinct"] is None

    def test_true_constant_column(self):
        """n_distinct=1, n_null=0, n_sentinel=0 → DROP_COLUMN, mechanism=N/A."""
        df = self._run(
            [("flag", 0)],
            [],
            {},
            {"flag": 1},
            set(),
        )
        row = df.iloc[0]
        assert row["mechanism"] == "N/A"
        assert row["recommendation"] == "DROP_COLUMN"

    def test_zero_missingness_with_spec(self):
        """Zero missingness + spec → RETAIN_AS_IS; spec fields preserved."""
        spec = {
            "tag": {
                "mechanism": "MCAR",
                "justification": "test",
                "sentinel_value": "unknown",
                "carries_semantic_content": True,
                "is_primary_feature": True,
            }
        }
        df = self._run(
            [("tag", 0)],
            [],
            spec,
            {"tag": 3},
            set(),
        )
        row = df.iloc[0]
        assert row["mechanism"] == "N/A"
        assert row["recommendation"] == "RETAIN_AS_IS"
        assert row["carries_semantic_content"] == True  # noqa: E712

    def test_zero_missingness_column_not_in_spec(self):
        """F1 branch with spec_entry is None — covers the spec_entry=None sub-branch."""
        df = self._run(
            [("score", 0)],
            [],
            {},
            {"score": 10},
            set(),
        )
        row = df.iloc[0]
        assert row["mechanism"] == "N/A"
        assert row["recommendation"] == "RETAIN_AS_IS"
        assert row["carries_semantic_content"] == False  # noqa: E712
        assert row["is_primary_feature"] == False  # noqa: E712

    def test_spec_entry_with_missingness(self):
        spec = {
            "score": {
                "mechanism": "MAR",
                "justification": "random missing",
                "sentinel_value": None,
                "carries_semantic_content": False,
                "is_primary_feature": False,
            }
        }
        df = self._run(
            [("score", 2)],
            [],
            spec,
            {"score": 3},
            set(),
        )
        row = df.iloc[0]
        assert row["mechanism"] == "MAR"
        # pct = 40.0 → mid-low → FLAG_FOR_IMPUTATION
        assert row["recommendation"] == "FLAG_FOR_IMPUTATION"

    def test_no_spec_with_missingness_fallback_mar(self):
        """No spec entry → conservative MAR assumption."""
        df = self._run(
            [("score", 2)],
            [],
            {},
            {"score": 3},
            set(),
        )
        row = df.iloc[0]
        assert row["mechanism"] == "MAR"
        assert row["recommendation"] == "FLAG_FOR_IMPUTATION"

    def test_target_column_with_missingness(self):
        """Target column with NULL → EXCLUDE_TARGET_NULL_ROWS (B4)."""
        df = self._run(
            [("result", 1)],
            [],
            {},
            {"result": 3},
            {"result"},
        )
        row = df.iloc[0]
        assert row["recommendation"] == "EXCLUDE_TARGET_NULL_ROWS"

    def test_target_column_without_missingness(self):
        """Target column with 0 NULLs → F1 fires first → RETAIN_AS_IS."""
        df = self._run(
            [("result", 0)],
            [],
            {},
            {"result": 3},
            {"result"},
        )
        row = df.iloc[0]
        assert row["recommendation"] == "RETAIN_AS_IS"

    def test_output_has_exactly_17_columns(self):
        df = self._run(
            [("id", 0)],
            [],
            {},
            {"id": None},
            set(),
            frozenset({"id"}),
        )
        expected_cols = {
            "view", "column", "dtype",
            "n_total", "n_null", "pct_null",
            "sentinel_value", "n_sentinel", "pct_sentinel",
            "pct_missing_total",
            "n_distinct",
            "mechanism", "mechanism_justification",
            "recommendation", "recommendation_justification",
            "carries_semantic_content",
            "is_primary_feature",
        }
        assert set(df.columns) == expected_cols

    def test_constant_and_target_conflict_constant_wins(self):
        """W7/B5 constant branch wins over B4 target override."""
        df = self._run(
            [("result", 0)],
            [],
            {},
            {"result": 1},  # n_distinct=1 → constant branch
            {"result"},     # also a target
        )
        row = df.iloc[0]
        # Constant branch (n_distinct=1, n_null=0, n_sentinel=0) fires first → DROP_COLUMN
        # B4 target override only fires when n_total_missing > 0; here it's 0.
        assert row["mechanism"] == "N/A"
        assert row["recommendation"] == "DROP_COLUMN"


# ---------------------------------------------------------------------------
# Tests for build_audit_views_block
# ---------------------------------------------------------------------------

class TestBuildAuditViewsBlock:
    def _make_df(self, n_rows: int) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "view": "v",
                    "column": f"col_{i}",
                    "dtype": "INTEGER",
                    "n_total": 100,
                    "n_null": 0,
                    "pct_null": 0.0,
                    "sentinel_value": None,
                    "n_sentinel": 0,
                    "pct_sentinel": 0.0,
                    "pct_missing_total": 0.0,
                    "n_distinct": 5,
                    "mechanism": "N/A",
                    "mechanism_justification": "test",
                    "recommendation": "RETAIN_AS_IS",
                    "recommendation_justification": "test",
                    "carries_semantic_content": False,
                    "is_primary_feature": False,
                }
                for i in range(n_rows)
            ]
        )

    def test_two_views_correct_keys(self):
        df_a = self._make_df(3)
        df_b = self._make_df(5)
        result = build_audit_views_block(
            {
                "view_a": {"total_rows": 100, "df_ledger": df_a},
                "view_b": {"total_rows": 200, "df_ledger": df_b},
            }
        )
        assert "views" in result
        assert "view_a" in result["views"]
        assert "view_b" in result["views"]

    def test_columns_audited_matches_df_len(self):
        df = self._make_df(7)
        result = build_audit_views_block(
            {"my_view": {"total_rows": 50, "df_ledger": df}}
        )
        assert result["views"]["my_view"]["columns_audited"] == 7

    def test_empty_dataframe_produces_empty_ledger(self):
        df = self._make_df(0)
        result = build_audit_views_block(
            {"empty_view": {"total_rows": 0, "df_ledger": df}}
        )
        assert result["views"]["empty_view"]["ledger"] == []
        assert result["views"]["empty_view"]["columns_audited"] == 0

    def test_empty_view_ledgers_dict(self):
        """Edge case: empty input → returns {"views": {}}."""
        result = build_audit_views_block({})
        assert result == {"views": {}}
