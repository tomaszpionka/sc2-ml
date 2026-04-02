"""Tests for gnn_pipeline.build_starcraft_graph().

Covers:
- Node count matches unique players
- Edge count matches number of matches
- Feature dimensionality correct
- Veteran mask correct shape and type
- Node features computed only from training data (leakage guard)
"""
import pandas as pd
import pytest
import torch

from sc2ml.features import perform_feature_engineering
from sc2ml.gnn.pipeline import build_starcraft_graph
from tests.helpers import make_matches_df

TEST_SIZE = 0.05
EDGE_FEATURE_COLS = [
    "diff_hist_apm", "diff_hist_sq", "diff_experience",
    "elo_diff", "expected_win_prob",
]


@pytest.fixture(scope="module")
def features_df() -> pd.DataFrame:
    raw = make_matches_df(n=300, seed=42)
    return perform_feature_engineering(raw)


@pytest.fixture(scope="module")
def graph(features_df: pd.DataFrame):
    return build_starcraft_graph(features_df, test_size=TEST_SIZE)


def test_node_count_matches_unique_players(features_df: pd.DataFrame, graph) -> None:
    graph_data, player_to_id = graph
    unique_players = pd.concat([features_df["p1_name"], features_df["p2_name"]]).nunique()
    assert graph_data.num_nodes == unique_players, (
        f"Expected {unique_players} nodes, got {graph_data.num_nodes}"
    )


def test_edge_count_matches_matches(features_df: pd.DataFrame, graph) -> None:
    graph_data, _ = graph
    assert graph_data.num_edges == len(features_df), (
        f"Expected {len(features_df)} edges, got {graph_data.num_edges}"
    )


def test_node_feature_dimensionality(graph) -> None:
    graph_data, _ = graph
    # Node features: avg_apm, avg_sq, avg_wr, avg_exp (4 raw → standardized)
    assert graph_data.x.shape[1] == 4, (
        f"Expected 4 node features, got {graph_data.x.shape[1]}"
    )


def test_edge_feature_dimensionality(graph) -> None:
    graph_data, _ = graph
    assert graph_data.edge_attr.shape[1] == len(EDGE_FEATURE_COLS), (
        f"Expected {len(EDGE_FEATURE_COLS)} edge features, got {graph_data.edge_attr.shape[1]}"
    )


def test_player_to_id_covers_all_nodes(features_df: pd.DataFrame, graph) -> None:
    graph_data, player_to_id = graph
    assert len(player_to_id) == graph_data.num_nodes


def test_veteran_mask_shape(features_df: pd.DataFrame, graph) -> None:
    graph_data, _ = graph
    assert hasattr(graph_data, "veteran_mask"), "graph_data missing veteran_mask attribute"
    assert graph_data.veteran_mask.shape[0] == len(features_df), (
        "veteran_mask length does not match number of edges"
    )


def test_veteran_mask_is_boolean_tensor(graph) -> None:
    graph_data, _ = graph
    assert graph_data.veteran_mask.dtype == torch.bool, (
        f"veteran_mask should be bool tensor, got {graph_data.veteran_mask.dtype}"
    )


def test_no_nan_in_node_features(graph) -> None:
    graph_data, _ = graph
    assert not torch.isnan(graph_data.x).any(), "NaN found in node feature matrix"


def test_no_nan_in_edge_features(graph) -> None:
    graph_data, _ = graph
    assert not torch.isnan(graph_data.edge_attr).any(), "NaN found in edge feature matrix"


def test_node_features_use_only_train_portion(features_df: pd.DataFrame) -> None:
    """Node stats when built from train-only vs all data should differ for test-set players."""
    full_graph, _ = build_starcraft_graph(features_df, test_size=0.3)
    # test_size=0 uses all data as train
    train_graph, _ = build_starcraft_graph(features_df, test_size=0.0)
    # With test_size=0.3 some players' test-match stats are excluded → node features differ
    # They should NOT be identical (unless data is trivially tiny)
    if len(features_df) > 50:
        assert not torch.allclose(full_graph.x, train_graph.x), (
            "Node features are identical regardless of test_size — leakage guard may not be active"
        )
