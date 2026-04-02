"""Tests for Group E — Context features."""

import pandas as pd

from sc2ml.features.group_e_context import _parse_patch_version, compute_context_features
from tests.helpers import make_series_df


class TestParsePatchVersion:
    def test_standard_version(self) -> None:
        assert _parse_patch_version("5.0.11") == 50011

    def test_higher_version(self) -> None:
        assert _parse_patch_version("5.0.13") == 50013

    def test_major_version_change(self) -> None:
        assert _parse_patch_version("4.7.0") == 40700

    def test_malformed_returns_zero(self) -> None:
        assert _parse_patch_version("bad") == 0

    def test_none_returns_zero(self) -> None:
        assert _parse_patch_version(None) == 0  # type: ignore[arg-type]

    def test_ordering_preserved(self) -> None:
        versions = ["4.0.0", "4.7.0", "5.0.0", "5.0.6", "5.0.11"]
        parsed = [_parse_patch_version(v) for v in versions]
        assert parsed == sorted(parsed)


class TestComputeContextFeatures:
    def test_patch_version_numeric(self, sorted_df: pd.DataFrame) -> None:
        result = compute_context_features(sorted_df)
        assert "patch_version_numeric" in result.columns
        assert (result["patch_version_numeric"] > 0).all()

    def test_tournament_match_position(self, sorted_df: pd.DataFrame) -> None:
        result = compute_context_features(sorted_df)
        assert "tournament_match_position" in result.columns
        assert (result["tournament_match_position"] >= 1).all()

    def test_series_without_data(self, sorted_df: pd.DataFrame) -> None:
        result = compute_context_features(sorted_df, series_df=None)
        assert result["series_game_number"].eq(0).all()
        assert result["series_length_so_far"].eq(0).all()

    def test_series_with_data(self, sorted_df: pd.DataFrame) -> None:
        sdf = make_series_df(sorted_df, series_size=3)
        result = compute_context_features(sorted_df, series_df=sdf)
        # First game in each series should be 1
        assert result["series_game_number"].min() >= 1
        # series_length_so_far should be game_number - 1
        assert (result["series_length_so_far"] == result["series_game_number"] - 1).all()

    def test_no_nans(self, sorted_df: pd.DataFrame) -> None:
        result = compute_context_features(sorted_df)
        for col in ["patch_version_numeric", "tournament_match_position",
                     "series_game_number", "series_length_so_far"]:
            assert result[col].isna().sum() == 0
