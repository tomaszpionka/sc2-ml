"""Integration tests for build_features() and ablation."""

import pandas as pd
import pytest

from sc2ml.features import FeatureGroup, build_features
from tests.helpers import make_matches_df, make_series_df


@pytest.fixture
def raw_df() -> pd.DataFrame:
    return make_matches_df(n=100, seed=99)


class TestBuildFeatures:
    def test_all_groups_default(self, raw_df: pd.DataFrame) -> None:
        result = build_features(raw_df)
        assert "elo_diff" in result.columns           # Group A
        assert "p1_hist_mean_apm" in result.columns    # Group B
        assert "spawn_distance" in result.columns      # Group C
        assert "p1_win_streak" in result.columns       # Group D
        assert "patch_version_numeric" in result.columns  # Group E

    def test_group_a_only(self, raw_df: pd.DataFrame) -> None:
        result = build_features(raw_df, groups=[FeatureGroup.A])
        assert "elo_diff" in result.columns
        assert "p1_hist_mean_apm" not in result.columns

    def test_up_to_b(self, raw_df: pd.DataFrame) -> None:
        result = build_features(raw_df, groups=FeatureGroup.B)
        assert "elo_diff" in result.columns           # A included
        assert "p1_hist_mean_apm" in result.columns    # B included
        assert "spawn_distance" not in result.columns   # C not included

    def test_column_count_monotonic(self, raw_df: pd.DataFrame) -> None:
        """Each successive group should add columns."""
        prev_count = 0
        for level in FeatureGroup:
            result = build_features(raw_df.copy(), groups=level)
            assert result.shape[1] > prev_count, f"Group {level} didn't add columns"
            prev_count = result.shape[1]

    def test_leakage_columns_removed(self, raw_df: pd.DataFrame) -> None:
        result = build_features(raw_df)
        for col in ["p1_result", "p1_apm", "p2_sq", "game_loops"]:
            assert col not in result.columns, f"Leakage column {col} still present"

    def test_target_present(self, raw_df: pd.DataFrame) -> None:
        result = build_features(raw_df)
        assert "target" in result.columns
        assert set(result["target"].unique()).issubset({0, 1})

    def test_chronologically_sorted(self, raw_df: pd.DataFrame) -> None:
        result = build_features(raw_df)
        times = pd.to_datetime(result["match_time"])
        assert (times.diff().dropna() >= pd.Timedelta(0)).all()

    def test_no_nans_in_features(self, raw_df: pd.DataFrame) -> None:
        result = build_features(raw_df)
        # Exclude metadata columns
        feature_cols = [c for c in result.columns if c not in [
            "match_id", "match_time", "p1_name", "p2_name",
            "data_build", "game_version", "map_name", "tournament_name", "split",
        ]]
        for col in feature_cols:
            assert result[col].isna().sum() == 0, f"NaN in {col}"

    def test_with_series_df(self, raw_df: pd.DataFrame) -> None:
        sdf = make_series_df(raw_df)
        result = build_features(raw_df, series_df=sdf)
        assert (result["series_game_number"] > 0).any()

    def test_list_groups_order_independent(self, raw_df: pd.DataFrame) -> None:
        """Passing groups in reverse order should produce same result."""
        result_fwd = build_features(
            raw_df.copy(), groups=[FeatureGroup.A, FeatureGroup.C]
        )
        result_rev = build_features(
            raw_df.copy(), groups=[FeatureGroup.C, FeatureGroup.A]
        )
        assert set(result_fwd.columns) == set(result_rev.columns)

    def test_build_features_casts_bool_to_int(self, raw_df: pd.DataFrame) -> None:
        """build_features should cast all bool columns to int."""
        result = build_features(raw_df)
        bool_cols = result.select_dtypes(include=["bool"]).columns.tolist()
        assert bool_cols == [], f"Bool columns remain after build_features: {bool_cols}"
