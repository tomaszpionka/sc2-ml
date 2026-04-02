"""Shared fixtures for feature group tests."""

import pandas as pd
import pytest

from sc2ml.features import build_features
from sc2ml.features.common import compute_target, ensure_sorted
from tests.helpers import make_matches_df, make_series_df


@pytest.fixture
def raw_df() -> pd.DataFrame:
    """Synthetic matches_flat-like DataFrame (200 rows)."""
    return make_matches_df(n=200, seed=42)


@pytest.fixture
def sorted_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Sorted + target-enriched DataFrame ready for group compute functions."""
    df = ensure_sorted(raw_df)
    df = compute_target(df)
    return df


@pytest.fixture
def series_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Synthetic series assignments for Group E tests."""
    return make_series_df(raw_df)


@pytest.fixture
def features_all(raw_df: pd.DataFrame, series_df: pd.DataFrame) -> pd.DataFrame:
    """Full feature DataFrame with all groups applied."""
    return build_features(raw_df, series_df=series_df)
