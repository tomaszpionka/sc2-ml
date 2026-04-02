"""Tests for Node2Vec embedder (NetworkX/Gensim backend)."""

from __future__ import annotations

import pandas as pd
import pytest
import torch
from torch_geometric.data import Data

from sc2ml.config import NODE2VEC_EMBEDDING_DIM
from sc2ml.gnn.embedder import append_embeddings_to_df, train_and_get_embeddings

pytestmark = pytest.mark.gnn


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def small_graph() -> tuple[Data, dict[str, int]]:
    """5-node graph with known connectivity (node 4 is isolated)."""
    edge_index = torch.tensor(
        [[0, 1, 1, 2, 2, 3], [1, 0, 2, 1, 3, 2]], dtype=torch.long
    )
    player_to_id = {
        "alice": 0,
        "bob": 1,
        "carol": 2,
        "dave": 3,
        "eve": 4,  # isolated — no edges
    }
    data = Data(edge_index=edge_index, num_nodes=5)
    return data, player_to_id


@pytest.fixture()
def embeddings_dict(small_graph: tuple[Data, dict[str, int]]) -> dict[str, list[float]]:
    """Pre-trained embeddings from the small graph (dim=8 for speed)."""
    graph_data, player_to_id = small_graph
    return train_and_get_embeddings(graph_data, player_to_id, embedding_dim=8)


# ---------------------------------------------------------------------------
# train_and_get_embeddings tests
# ---------------------------------------------------------------------------


class TestTrainAndGetEmbeddings:
    def test_train_returns_dict(self, embeddings_dict: dict[str, list[float]]):
        assert isinstance(embeddings_dict, dict)

    def test_embeddings_correct_dim(self, embeddings_dict: dict[str, list[float]]):
        for vec in embeddings_dict.values():
            assert len(vec) == 8

    def test_all_players_present(
        self,
        small_graph: tuple[Data, dict[str, int]],
        embeddings_dict: dict[str, list[float]],
    ):
        _, player_to_id = small_graph
        for name in player_to_id:
            assert name in embeddings_dict

    def test_isolated_node_zero_vector(self, embeddings_dict: dict[str, list[float]]):
        """Isolated node (eve) should get the zero fallback vector."""
        eve_vec = embeddings_dict["eve"]
        assert all(v == 0.0 for v in eve_vec)


# ---------------------------------------------------------------------------
# append_embeddings_to_df tests
# ---------------------------------------------------------------------------


class TestAppendEmbeddings:
    @pytest.fixture()
    def features_df(self) -> pd.DataFrame:
        return pd.DataFrame({
            "p1_name": ["alice", "bob", "carol"],
            "p2_name": ["bob", "carol", "dave"],
            "some_feature": [1.0, 2.0, 3.0],
        })

    def test_append_creates_columns(
        self, features_df: pd.DataFrame, embeddings_dict: dict[str, list[float]]
    ):
        result = append_embeddings_to_df(features_df, embeddings_dict, embedding_dim=8)
        assert "p1_emb_0" in result.columns
        assert "p2_emb_0" in result.columns
        assert "p1_emb_7" in result.columns
        assert "p2_emb_7" in result.columns

    def test_append_preserves_rows(
        self, features_df: pd.DataFrame, embeddings_dict: dict[str, list[float]]
    ):
        result = append_embeddings_to_df(features_df, embeddings_dict, embedding_dim=8)
        assert len(result) == len(features_df)

    def test_append_unknown_player_zeros(self, embeddings_dict: dict[str, list[float]]):
        """Player not in embeddings_dict gets zero vector."""
        df = pd.DataFrame({
            "p1_name": ["unknown_player"],
            "p2_name": ["alice"],
            "feat": [1.0],
        })
        result = append_embeddings_to_df(df, embeddings_dict, embedding_dim=8)
        p1_cols = [c for c in result.columns if c.startswith("p1_emb_")]
        assert all(result[c].iloc[0] == 0.0 for c in p1_cols)
