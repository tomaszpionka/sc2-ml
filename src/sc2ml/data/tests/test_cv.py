"""Tests for the expanding-window temporal cross-validator."""

import numpy as np
import pytest

from sc2ml.data.cv import ExpandingWindowCV


@pytest.fixture()
def sample_data():
    """100-sample array for CV splitting."""
    return np.arange(100).reshape(-1, 1)


class TestExpandingWindowCV:
    def test_returns_correct_number_of_splits(self, sample_data):
        """
        Scenario: CV splitter produces the requested number of folds.
        Preconditions: 100-sample array, n_splits=5, min_train_frac=0.3.
        Assertions: Exactly 5 (train, val) pairs returned.
        """
        cv = ExpandingWindowCV(n_splits=5, min_train_frac=0.3)
        splits = list(cv.split(sample_data))
        assert len(splits) == 5

    def test_get_n_splits(self):
        """
        Scenario: get_n_splits returns the configured fold count.
        Preconditions: ExpandingWindowCV with n_splits=3.
        Assertions: get_n_splits() == 3.
        """
        cv = ExpandingWindowCV(n_splits=3)
        assert cv.get_n_splits() == 3

    def test_training_windows_grow_monotonically(self, sample_data):
        """
        Scenario: Each fold's training set is strictly larger than the previous.
        Preconditions: 100-sample array, 5 splits with expanding window.
        Assertions: len(train) increases across consecutive folds.
        """
        cv = ExpandingWindowCV(n_splits=5, min_train_frac=0.3)
        splits = list(cv.split(sample_data))
        prev_train_size = 0
        for train_idx, val_idx in splits:
            assert len(train_idx) > prev_train_size
            prev_train_size = len(train_idx)

    def test_no_overlap_between_train_and_val(self, sample_data):
        """
        Scenario: Train and validation indices are disjoint in every fold.
        Preconditions: 100-sample array, 5 splits.
        Assertions: Intersection of train and val indices is empty per fold.
        """
        cv = ExpandingWindowCV(n_splits=5, min_train_frac=0.3)
        for train_idx, val_idx in cv.split(sample_data):
            overlap = np.intersect1d(train_idx, val_idx)
            assert len(overlap) == 0

    def test_val_comes_after_train(self, sample_data):
        """
        Scenario: Validation window is strictly after training window (temporal order).
        Preconditions: 100-sample array, 5 splits.
        Assertions: Last train index < first val index per fold.
        """
        cv = ExpandingWindowCV(n_splits=5, min_train_frac=0.3)
        for train_idx, val_idx in cv.split(sample_data):
            assert train_idx[-1] < val_idx[0]

    def test_non_empty_splits(self, sample_data):
        """
        Scenario: Neither train nor val is empty in any fold.
        Preconditions: 100-sample array, 5 splits.
        Assertions: Both train and val have at least one index per fold.
        """
        cv = ExpandingWindowCV(n_splits=5, min_train_frac=0.3)
        for train_idx, val_idx in cv.split(sample_data):
            assert len(train_idx) > 0
            assert len(val_idx) > 0

    def test_min_train_frac_respected(self, sample_data):
        """
        Scenario: First fold's training set meets the minimum fraction constraint.
        Preconditions: 100-sample array, min_train_frac=0.4, 3 splits.
        Assertions: First fold train size >= 40% of total samples.
        """
        min_frac = 0.4
        cv = ExpandingWindowCV(n_splits=3, min_train_frac=min_frac)
        splits = list(cv.split(sample_data))
        first_train = splits[0][0]
        assert len(first_train) >= int(len(sample_data) * min_frac)


class TestExpandingWindowCVWithSeries:
    def test_series_boundary_respected(self):
        """
        Scenario: Train/val split never falls within a series.
        Preconditions: 100 samples grouped into 20 series of size 5.
        Assertions: Last train sample and first val sample belong to different series.
        """
        n = 100
        X = np.arange(n).reshape(-1, 1)
        # Create series of size 5: [0,0,0,0,0,1,1,1,1,1,...]
        series_ids = np.repeat(np.arange(n // 5), 5)

        cv = ExpandingWindowCV(
            n_splits=3, min_train_frac=0.3,
            series_ids=series_ids,
        )

        for train_idx, val_idx in cv.split(X):
            # Last training index and first val index should be at a boundary
            if len(train_idx) > 0 and len(val_idx) > 0:
                train_end = train_idx[-1]
                val_start = val_idx[0]
                # They should be in different series
                assert series_ids[train_end] != series_ids[val_start], (
                    f"Train ends in series {series_ids[train_end]}, "
                    f"val starts in series {series_ids[val_start]}"
                )


class TestExpandingWindowCVValidation:
    def test_raises_on_invalid_min_train_frac(self):
        """
        Scenario: Out-of-range min_train_frac rejected at construction.
        Preconditions: min_train_frac=0.0 and min_train_frac=1.0 (both invalid).
        Assertions: ValueError raised with "min_train_frac" in message.
        """
        with pytest.raises(ValueError, match="min_train_frac"):
            ExpandingWindowCV(min_train_frac=0.0)
        with pytest.raises(ValueError, match="min_train_frac"):
            ExpandingWindowCV(min_train_frac=1.0)

    def test_raises_on_too_few_splits(self):
        """
        Scenario: n_splits < 2 rejected at construction.
        Preconditions: n_splits=1.
        Assertions: ValueError raised with "n_splits" in message.
        """
        with pytest.raises(ValueError, match="n_splits"):
            ExpandingWindowCV(n_splits=1)

    def test_raises_on_no_X(self):
        """
        Scenario: Calling split(None) raises immediately.
        Preconditions: Valid CV object, X=None.
        Assertions: ValueError raised with "X must be provided" in message.
        """
        cv = ExpandingWindowCV(n_splits=3)
        with pytest.raises(ValueError, match="X must be provided"):
            list(cv.split(None))

    def test_raises_on_too_little_data(self):
        """
        Scenario: Data too small for requested splits raises at split time.
        Preconditions: 10 samples, n_splits=10, min_train_frac=0.9.
        Assertions: ValueError raised with "Not enough data" in message.
        """
        cv = ExpandingWindowCV(n_splits=10, min_train_frac=0.9)
        X = np.arange(10).reshape(-1, 1)
        with pytest.raises(ValueError, match="Not enough data"):
            list(cv.split(X))


class TestExpandingWindowCVDegenerateFolds:
    def test_expanding_window_skips_degenerate_fold(self):
        """
        Scenario: Folds where series snapping makes val empty are silently skipped.
        Preconditions: 20 samples all in one series, n_splits=5, min_train_frac=0.5.
        Assertions: Fewer than 5 folds returned (degenerate ones dropped).
        """
        n = 20
        X = np.arange(n).reshape(-1, 1)
        # All samples in the same series — snapping always pushes to end
        series_ids = np.zeros(n, dtype=int)

        cv = ExpandingWindowCV(
            n_splits=5, min_train_frac=0.5,
            series_ids=series_ids,
        )
        splits = list(cv.split(X))
        # With all samples in one series, snapping pushes boundaries to n-1,
        # so some folds become degenerate and are skipped
        assert len(splits) < 5


class TestExpandingWindowCVSklearnCompat:
    def test_works_with_cross_val_score(self):
        """
        Scenario: ExpandingWindowCV integrates with sklearn's cross_val_score.
        Preconditions: 100-sample classification dataset, 3 folds, LogisticRegression.
        Assertions: 3 accuracy scores returned, all in [0, 1].
        """
        from sklearn.datasets import make_classification
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_score

        X, y = make_classification(n_samples=100, random_state=42)
        cv = ExpandingWindowCV(n_splits=3, min_train_frac=0.3)
        scores = cross_val_score(
            LogisticRegression(max_iter=200), X, y,
            cv=cv, scoring="accuracy",
        )
        assert len(scores) == 3
        assert all(0 <= s <= 1 for s in scores)
