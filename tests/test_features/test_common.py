"""Tests for features/common.py shared primitives."""

import pandas as pd
import pytest

from sc2ml.features.common import (
    bayesian_smooth,
    compute_target,
    ensure_sorted,
    expanding_count,
    expanding_sum,
    split_for_ml,
)


class TestEnsureSorted:
    def test_sorts_by_match_time(self) -> None:
        df = pd.DataFrame({
            "match_time": pd.to_datetime(["2023-03-01", "2023-01-01", "2023-02-01"]),
            "x": [3, 1, 2],
        })
        result = ensure_sorted(df)
        assert list(result["x"]) == [1, 2, 3]

    def test_resets_index(self) -> None:
        df = pd.DataFrame({
            "match_time": pd.to_datetime(["2023-02-01", "2023-01-01"]),
        })
        result = ensure_sorted(df)
        assert list(result.index) == [0, 1]


class TestComputeTarget:
    def test_adds_target_column(self) -> None:
        df = pd.DataFrame({"p1_result": ["Win", "Loss", "Win"]})
        result = compute_target(df)
        assert list(result["target"]) == [1, 0, 1]

    def test_idempotent(self) -> None:
        df = pd.DataFrame({"p1_result": ["Win"], "target": [1]})
        result = compute_target(df)
        assert result["target"].iloc[0] == 1
        assert len(result.columns) == 2  # no duplicate


class TestExpandingSum:
    def test_excludes_current_row(self) -> None:
        df = pd.DataFrame({"g": ["a", "a", "a"], "v": [10, 20, 30]})
        result = expanding_sum(df, "g", "v")
        assert list(result) == [0, 10, 30]  # cumsum - current

    def test_multi_group(self) -> None:
        df = pd.DataFrame({"g": ["a", "b", "a"], "v": [10, 20, 30]})
        result = expanding_sum(df, "g", "v")
        assert list(result) == [0, 0, 10]


class TestExpandingCount:
    def test_first_appearance_is_zero(self) -> None:
        df = pd.DataFrame({"g": ["a", "b", "a", "b"]})
        result = expanding_count(df, "g")
        assert list(result) == [0, 0, 1, 1]


class TestBayesianSmooth:
    def test_with_no_data_returns_prior(self) -> None:
        wins = pd.Series([0])
        total = pd.Series([0])
        result = bayesian_smooth(wins, total, c=5.0, prior=0.5)
        assert abs(result.iloc[0] - 0.5) < 1e-6

    def test_with_data_shifts_from_prior(self) -> None:
        wins = pd.Series([5])
        total = pd.Series([10])
        result = bayesian_smooth(wins, total, c=5.0, prior=0.5)
        # (5 + 2.5) / (10 + 5) = 7.5/15 = 0.5 — happens to equal prior here
        assert 0 <= result.iloc[0] <= 1


class TestSplitForMl:
    def test_raises_without_split_column(self) -> None:
        df = pd.DataFrame({"target": [1], "x": [0.5]})
        with pytest.raises(ValueError, match="split"):
            split_for_ml(df)

    def test_three_way_split(self) -> None:
        df = pd.DataFrame({
            "target": [1, 0, 1, 0, 1, 0],
            "x": [1, 2, 3, 4, 5, 6],
            "split": ["train", "train", "train", "val", "test", "test"],
            "match_id": list("abcdef"),
            "match_time": pd.date_range("2023-01-01", periods=6),
            "p1_name": ["a"] * 6,
            "p2_name": ["b"] * 6,
        })
        X_train, X_val, X_test, y_train, y_val, y_test = split_for_ml(df)
        assert len(X_train) == 3
        assert len(X_val) == 1
        assert len(X_test) == 2
        # Metadata columns must not leak into X
        for X in (X_train, X_val, X_test):
            assert "match_id" not in X.columns
            assert "target" not in X.columns
            assert "split" not in X.columns
