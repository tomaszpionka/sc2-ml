"""Tests for baseline classifiers (majority class, Elo-only, LR on Elo diff)."""

import numpy as np
import pandas as pd
import pytest

from sc2ml.models.baselines import (
    EloLRBaseline,
    EloOnlyBaseline,
    MajorityClassBaseline,
    build_baselines,
)


@pytest.fixture()
def sample_data():
    """Synthetic data with elo_diff and expected_win_prob columns."""
    rng = np.random.default_rng(42)
    n = 200
    elo_diff = rng.normal(0, 150, n)
    expected_win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
    y = (rng.uniform(0, 1, n) < expected_win_prob).astype(int)

    X = pd.DataFrame({
        "elo_diff": elo_diff,
        "expected_win_prob": expected_win_prob,
        "other_feature": rng.normal(0, 1, n),
    })
    return X, pd.Series(y, name="target")


# ---------------------------------------------------------------------------
# MajorityClassBaseline
# ---------------------------------------------------------------------------

class TestMajorityClassBaseline:
    def test_always_predicts_majority(self, sample_data):
        X, y = sample_data
        model = MajorityClassBaseline()
        model.fit(X, y)
        preds = model.predict(X)
        assert np.all(preds == model.majority_class_)

    def test_predict_proba_shape(self, sample_data):
        X, y = sample_data
        model = MajorityClassBaseline()
        model.fit(X, y)
        proba = model.predict_proba(X)
        assert proba.shape == (len(X), 2)

    def test_predict_proba_sums_to_one(self, sample_data):
        X, y = sample_data
        model = MajorityClassBaseline()
        model.fit(X, y)
        proba = model.predict_proba(X)
        np.testing.assert_allclose(proba.sum(axis=1), 1.0)

    def test_majority_fraction_matches_data(self):
        y = pd.Series([1, 1, 1, 0])  # 75% class 1
        X = pd.DataFrame({"x": [0, 0, 0, 0]})
        model = MajorityClassBaseline()
        model.fit(X, y)
        assert model.majority_class_ == 1
        assert model.majority_frac_ == 0.75

    def test_all_same_class(self):
        y = pd.Series([0, 0, 0, 0])
        X = pd.DataFrame({"x": [0, 0, 0, 0]})
        model = MajorityClassBaseline()
        model.fit(X, y)
        assert model.majority_class_ == 0
        preds = model.predict(X)
        assert np.all(preds == 0)


# ---------------------------------------------------------------------------
# EloOnlyBaseline
# ---------------------------------------------------------------------------

class TestEloOnlyBaseline:
    def test_predicts_from_expected_win_prob(self, sample_data):
        X, y = sample_data
        model = EloOnlyBaseline()
        model.fit(X, y)
        preds = model.predict(X)
        expected = (X["expected_win_prob"].values >= 0.5).astype(int)
        np.testing.assert_array_equal(preds, expected)

    def test_predict_proba_uses_elo_prob(self, sample_data):
        X, y = sample_data
        model = EloOnlyBaseline()
        model.fit(X, y)
        proba = model.predict_proba(X)
        # Column 1 should be expected_win_prob
        np.testing.assert_allclose(proba[:, 1], X["expected_win_prob"].values)

    def test_predict_proba_sums_to_one(self, sample_data):
        X, y = sample_data
        model = EloOnlyBaseline()
        model.fit(X, y)
        proba = model.predict_proba(X)
        np.testing.assert_allclose(proba.sum(axis=1), 1.0)

    def test_raises_on_missing_column(self):
        X = pd.DataFrame({"other_col": [1, 2, 3]})
        y = pd.Series([0, 1, 0])
        model = EloOnlyBaseline()
        with pytest.raises(ValueError, match="expected_win_prob"):
            model.fit(X, y)

    def test_custom_column_name(self, sample_data):
        X, y = sample_data
        X = X.rename(columns={"expected_win_prob": "my_prob"})
        model = EloOnlyBaseline(prob_col="my_prob")
        model.fit(X, y)
        preds = model.predict(X)
        assert len(preds) == len(X)


# ---------------------------------------------------------------------------
# EloLRBaseline
# ---------------------------------------------------------------------------

class TestEloLRBaseline:
    def test_trains_on_single_column(self, sample_data):
        X, y = sample_data
        model = EloLRBaseline()
        model.fit(X, y)
        preds = model.predict(X)
        assert len(preds) == len(X)
        assert set(np.unique(preds)).issubset({0, 1})

    def test_predict_proba_shape(self, sample_data):
        X, y = sample_data
        model = EloLRBaseline()
        model.fit(X, y)
        proba = model.predict_proba(X)
        assert proba.shape == (len(X), 2)

    def test_predict_proba_sums_to_one(self, sample_data):
        X, y = sample_data
        model = EloLRBaseline()
        model.fit(X, y)
        proba = model.predict_proba(X)
        np.testing.assert_allclose(proba.sum(axis=1), 1.0)

    def test_positive_elo_diff_higher_prob(self, sample_data):
        X, y = sample_data
        model = EloLRBaseline()
        model.fit(X, y)
        proba = model.predict_proba(X)[:, 1]
        # Players with positive elo_diff should generally have higher win prob
        pos_mask = X["elo_diff"] > 100
        neg_mask = X["elo_diff"] < -100
        assert proba[pos_mask].mean() > proba[neg_mask].mean()

    def test_raises_on_missing_column(self):
        X = pd.DataFrame({"other_col": [1, 2, 3]})
        y = pd.Series([0, 1, 0])
        model = EloLRBaseline()
        with pytest.raises(ValueError, match="elo_diff"):
            model.fit(X, y)


# ---------------------------------------------------------------------------
# build_baselines
# ---------------------------------------------------------------------------

class TestBuildBaselines:
    def test_returns_three_baselines(self):
        baselines = build_baselines()
        assert len(baselines) == 3
        assert "Majority Class" in baselines
        assert "Elo Only" in baselines
        assert "LR (Elo diff)" in baselines

    def test_all_have_predict_proba(self, sample_data):
        X, y = sample_data
        baselines = build_baselines()
        for name, model in baselines.items():
            model.fit(X, y)
            proba = model.predict_proba(X)
            assert proba.shape == (len(X), 2), f"{name} predict_proba wrong shape"
