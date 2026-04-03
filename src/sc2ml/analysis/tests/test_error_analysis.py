"""Tests for error analysis subgroup classification."""

import numpy as np
import pandas as pd
import pytest

from sc2ml.analysis.error_analysis import (
    classify_error_subgroups,
    error_subgroup_report,
)


@pytest.fixture()
def sample_predictions():
    """Synthetic predictions with varied matchups and Elo diffs."""
    rng = np.random.default_rng(42)
    n = 200
    y_true = rng.integers(0, 2, n)
    y_prob = np.clip(y_true * 0.6 + 0.2 + rng.normal(0, 0.15, n), 0.01, 0.99)
    y_pred = (y_prob >= 0.5).astype(int)

    matchup_col = pd.Series(
        rng.choice(["PvT", "TvZ", "PvZ", "TvT", "PvP", "ZvZ"], n)
    )
    elo_diff = rng.normal(0, 150, n)
    game_loops = rng.uniform(2000, 40000, n)  # mix of short and long

    return y_true, y_pred, y_prob, matchup_col, elo_diff, game_loops


class TestClassifyErrorSubgroups:
    def test_always_returns_all_subgroup(self, sample_predictions):
        y_true, y_pred, y_prob, *_ = sample_predictions
        subgroups = classify_error_subgroups(y_true, y_pred, y_prob)
        assert "all" in subgroups
        assert len(subgroups["all"]["y_true"]) == len(y_true)

    def test_mirror_subgroup_correct(self, sample_predictions):
        y_true, y_pred, y_prob, matchup_col, _, _ = sample_predictions
        subgroups = classify_error_subgroups(
            y_true, y_pred, y_prob, matchup_col=matchup_col,
        )
        assert "mirrors" in subgroups
        mirror_mask = subgroups["mirrors"]["mask"]
        for i in range(len(matchup_col)):
            if mirror_mask[i]:
                assert matchup_col.iloc[i] in {"TvT", "PvP", "ZvZ"}

    def test_upset_subgroup(self, sample_predictions):
        y_true, y_pred, y_prob, _, elo_diff, _ = sample_predictions
        subgroups = classify_error_subgroups(
            y_true, y_pred, y_prob, elo_diff=elo_diff,
        )
        assert "upsets" in subgroups
        # Upsets: favored player lost
        for i in range(len(subgroups["upsets"]["y_true"])):
            mask = subgroups["upsets"]["mask"]
            idx = np.where(mask)[0][i]
            if elo_diff[idx] > 0:
                assert y_true[idx] == 0  # p1 favored but lost
            else:
                assert y_true[idx] == 1  # p2 favored but lost

    def test_close_elo_subgroup(self, sample_predictions):
        y_true, y_pred, y_prob, _, elo_diff, _ = sample_predictions
        subgroups = classify_error_subgroups(
            y_true, y_pred, y_prob, elo_diff=elo_diff,
        )
        assert "close_elo" in subgroups
        close_mask = subgroups["close_elo"]["mask"]
        assert np.all(np.abs(elo_diff[close_mask]) < 50)

    def test_game_length_subgroups(self, sample_predictions):
        y_true, y_pred, y_prob, _, _, game_loops = sample_predictions
        subgroups = classify_error_subgroups(
            y_true, y_pred, y_prob, game_loops=game_loops,
        )
        # With uniform(2000, 40000), should have both short and long
        assert "short_games" in subgroups or "long_games" in subgroups

    def test_subgroups_dont_double_count(self, sample_predictions):
        y_true, y_pred, y_prob, matchup_col, _, _ = sample_predictions
        subgroups = classify_error_subgroups(
            y_true, y_pred, y_prob, matchup_col=matchup_col,
        )
        if "mirrors" in subgroups and "cross_race" in subgroups:
            mirror_mask = subgroups["mirrors"]["mask"]
            cross_mask = subgroups["cross_race"]["mask"]
            overlap = np.sum(mirror_mask & cross_mask)
            assert overlap == 0
            # Together they should cover all samples
            assert np.sum(mirror_mask | cross_mask) == len(y_true)


class TestErrorSubgroupReport:
    def test_report_shape(self, sample_predictions):
        y_true, y_pred, y_prob, matchup_col, elo_diff, game_loops = sample_predictions
        subgroups = classify_error_subgroups(
            y_true, y_pred, y_prob,
            matchup_col=matchup_col,
            elo_diff=elo_diff,
            game_loops=game_loops,
        )
        report = error_subgroup_report(subgroups)
        assert "subgroup" in report.columns
        assert "accuracy" in report.columns
        assert "auc_roc" in report.columns
        assert "n_samples" in report.columns
        assert len(report) == len(subgroups)

    def test_accuracy_in_range(self, sample_predictions):
        y_true, y_pred, y_prob, *_ = sample_predictions
        subgroups = classify_error_subgroups(y_true, y_pred, y_prob)
        report = error_subgroup_report(subgroups)
        assert all(0 <= acc <= 1 for acc in report["accuracy"])

    def test_error_rate_complement(self, sample_predictions):
        y_true, y_pred, y_prob, *_ = sample_predictions
        subgroups = classify_error_subgroups(y_true, y_pred, y_prob)
        report = error_subgroup_report(subgroups)
        np.testing.assert_allclose(
            report["accuracy"] + report["error_rate"], 1.0
        )

    def test_error_subgroup_report_single_class_auc_nan(self):
        """When all y_true are the same class, auc_roc should be NaN."""
        y_true = np.ones(10, dtype=int)
        y_pred = np.ones(10, dtype=int)
        y_prob = np.full(10, 0.9)
        subgroups = classify_error_subgroups(y_true, y_pred, y_prob)
        report = error_subgroup_report(subgroups)
        assert np.isnan(report.loc[report["subgroup"] == "all", "auc_roc"].iloc[0])
