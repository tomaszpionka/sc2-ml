"""Tests for GNN t-SNE visualizer."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest
import torch
from torch_geometric.data import Data

from sc2ml.gnn.visualizer import visualize_gnn_space

pytestmark = pytest.mark.gnn


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NUM_NODES = 50
HIDDEN_DIM = 16


@pytest.fixture()
def mock_model():
    """Mock SC2EdgeClassifier whose conv layers return deterministic tensors."""
    model = MagicMock()
    model.eval = MagicMock(return_value=model)

    h1 = torch.randn(NUM_NODES, HIDDEN_DIM)
    h2 = torch.randn(NUM_NODES, HIDDEN_DIM)

    model.conv1 = MagicMock(return_value=h1)
    model.conv2 = MagicMock(return_value=h2)

    return model


@pytest.fixture()
def graph_data() -> Data:
    """Small PyG Data with features and edges."""
    x = torch.randn(NUM_NODES, 4)
    # Chain: 0-1-2-...-9 (bidirectional)
    src = list(range(NUM_NODES - 1)) + list(range(1, NUM_NODES))
    dst = list(range(1, NUM_NODES)) + list(range(NUM_NODES - 1))
    edge_index = torch.tensor([src, dst], dtype=torch.long)
    return Data(x=x, edge_index=edge_index)


@pytest.fixture()
def player_to_id() -> dict[str, int]:
    top = [
        "serral", "maru", "clem", "reynor", "dark",
        "rogue", "stats", "classic", "byun", "neeb",
    ]
    # Pad to NUM_NODES with synthetic player names
    names = top + [f"player_{i}" for i in range(len(top), NUM_NODES)]
    return {name: i for i, name in enumerate(names)}


def _make_features_df(
    player_to_id: dict[str, int],
    races: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Build a features_df with race one-hot columns."""
    if races is None:
        races = {
            "serral": "Zerg", "maru": "Terran", "clem": "Terran",
            "reynor": "Zerg", "dark": "Zerg", "rogue": "Zerg",
            "stats": "Protoss", "classic": "Protoss", "byun": "Terran",
            "neeb": "Protoss",
        }
    rows = []
    names = list(player_to_id.keys())
    for i in range(0, len(names) - 1, 2):
        p1, p2 = names[i], names[i + 1]
        r1, r2 = races.get(p1, "Unknown"), races.get(p2, "Unknown")
        rows.append({
            "p1_name": p1,
            "p2_name": p2,
            "p1_race_Zerg": int(r1 == "Zerg"),
            "p1_race_Terran": int(r1 == "Terran"),
            "p1_race_Protoss": int(r1 == "Protoss"),
            "p2_race_Zerg": int(r2 == "Zerg"),
            "p2_race_Terran": int(r2 == "Terran"),
            "p2_race_Protoss": int(r2 == "Protoss"),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestVisualizeGnnSpace:
    def test_visualize_creates_png(
        self, mock_model, graph_data, player_to_id, tmp_path: Path
    ):
        out = tmp_path / "viz.png"
        features_df = _make_features_df(player_to_id)
        visualize_gnn_space(
            mock_model, graph_data, player_to_id, features_df, output_path=out
        )
        assert out.exists()
        assert out.stat().st_size > 0

    def test_visualize_with_top_player_annotation(
        self, mock_model, graph_data, player_to_id, tmp_path: Path
    ):
        """Should not crash when TOP_PLAYERS overlap with player_to_id."""
        out = tmp_path / "viz_top.png"
        features_df = _make_features_df(player_to_id)
        visualize_gnn_space(
            mock_model, graph_data, player_to_id, features_df, output_path=out
        )
        assert out.exists()

    def test_visualize_all_races(
        self, mock_model, graph_data, player_to_id, tmp_path: Path
    ):
        """One player per race — all three scatter groups rendered."""
        out = tmp_path / "viz_races.png"
        features_df = _make_features_df(player_to_id)
        visualize_gnn_space(
            mock_model, graph_data, player_to_id, features_df, output_path=out
        )
        assert out.exists()

    def test_visualize_no_crash_on_empty_race(
        self, mock_model, graph_data, player_to_id, tmp_path: Path
    ):
        """Race with 0 players should not crash."""
        out = tmp_path / "viz_empty_race.png"
        # All players are Zerg — no Terran or Protoss
        races = {name: "Zerg" for name in player_to_id}
        features_df = _make_features_df(player_to_id, races=races)
        visualize_gnn_space(
            mock_model, graph_data, player_to_id, features_df, output_path=out
        )
        assert out.exists()
