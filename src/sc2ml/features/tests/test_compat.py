"""Tests for backward-compatible API wrappers."""

import warnings

from tests.helpers import make_matches_df


class TestPerformFeatureEngineering:
    def test_importable_from_old_path(self) -> None:
        from sc2ml.features.compat import perform_feature_engineering
        assert callable(perform_feature_engineering)

    def test_returns_expected_columns(self) -> None:
        from sc2ml.features.compat import perform_feature_engineering

        df = make_matches_df(n=50, seed=7)
        result = perform_feature_engineering(df)
        # Must have at least the columns the old API produced
        for col in [
            "target", "elo_diff", "expected_win_prob",
            "p1_hist_mean_apm", "p1_hist_winrate_smooth",
            "spawn_distance", "diff_experience",
        ]:
            assert col in result.columns, f"Missing compat column: {col}"


class TestTemporalTrainTestSplit:
    def test_emits_deprecation_warning(self) -> None:
        from sc2ml.features.compat import (
            perform_feature_engineering,
            temporal_train_test_split,
        )

        df = make_matches_df(n=50, seed=7)
        features_df = perform_feature_engineering(df)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            X_train, X_test, y_train, y_test = temporal_train_test_split(
                features_df, test_size=0.2
            )
            assert len(w) >= 1
            assert any(issubclass(x.category, DeprecationWarning) for x in w)

    def test_split_sizes(self) -> None:
        from sc2ml.features.compat import (
            perform_feature_engineering,
            temporal_train_test_split,
        )

        df = make_matches_df(n=100, seed=7)
        features_df = perform_feature_engineering(df)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            X_train, X_test, y_train, y_test = temporal_train_test_split(
                features_df, test_size=0.2
            )

        assert len(X_train) == 80
        assert len(X_test) == 20
