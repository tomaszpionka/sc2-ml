import logging

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler
from torch_geometric.data import Data

from sc2ml.config import (
    NODE_FALLBACK_APM,
    NODE_FALLBACK_GAMES,
    NODE_FALLBACK_SQ,
    NODE_FALLBACK_WINRATE,
    VETERAN_MIN_GAMES,
)

logger = logging.getLogger(__name__)


def build_starcraft_graph(
    df: pd.DataFrame, test_size: float = 0.05
) -> tuple[Data, dict[str, int]]:
    """Construct a PyTorch Geometric graph from match data for GNN training.

    Node features are computed exclusively from training-set matches to prevent
    temporal leakage: test matches carry future information and must not influence
    the node embeddings seen during training.

    Args:
        df: Match dataframe with historical features (output of perform_feature_engineering).
        test_size: Fraction of matches to hold out as test edges.

    Returns:
        graph_data: PyG Data object with node features, edge index, edge attributes,
                    targets, match timestamps, and a veteran mask.
        player_to_id: Mapping from player name to integer node index.
    """
    logger.info("Building SC2 match graph (node features from historical stats + edge features)...")

    # Chronological sort is required — node feature aggregation must respect time
    df = df.sort_values("match_time").reset_index(drop=True)

    # All players become nodes, including those appearing only in test edges
    unique_players = pd.concat([df["p1_name"], df["p2_name"]]).unique()
    player_to_id: dict[str, int] = {name: idx for idx, name in enumerate(unique_players)}
    id_to_player: dict[int, str] = {idx: name for name, idx in player_to_id.items()}
    num_nodes = len(unique_players)

    # Node features aggregated from training matches only (temporal leakage prevention)
    train_size = int(len(df) * (1.0 - test_size))
    train_df = df.iloc[:train_size]
    logger.info(
        f"Node features computed from {train_size} training matches (out of {len(df)} total)"
    )

    player_stats: dict[str, list[float]] = {}
    for name in unique_players:
        p1_data = train_df[train_df["p1_name"] == name]
        p2_data = train_df[train_df["p2_name"] == name]

        # Aggregate historical averages — safe from future leakage
        avg_apm = pd.concat([p1_data["p1_hist_mean_apm"], p2_data["p2_hist_mean_apm"]]).mean()
        avg_sq = pd.concat([p1_data["p1_hist_mean_sq"], p2_data["p2_hist_mean_sq"]]).mean()
        avg_wr = pd.concat(
            [p1_data["p1_hist_winrate_smooth"], p2_data["p2_hist_winrate_smooth"]]
        ).mean()
        avg_exp = pd.concat(
            [p1_data["p1_total_games_played"], p2_data["p2_total_games_played"]]
        ).max()

        player_stats[name] = [
            avg_apm if not np.isnan(avg_apm) else NODE_FALLBACK_APM,
            avg_sq if not np.isnan(avg_sq) else NODE_FALLBACK_SQ,
            avg_wr if not np.isnan(avg_wr) else NODE_FALLBACK_WINRATE,
            float(avg_exp) if not np.isnan(avg_exp) else NODE_FALLBACK_GAMES,
        ]

    # Build node feature matrix — id_to_player maps integer index back to player name
    x_list = [player_stats[id_to_player[i]] for i in range(num_nodes)]
    x_np = np.array(x_list, dtype=np.float32)

    scaler_nodes = StandardScaler()
    x_scaled = scaler_nodes.fit_transform(x_np)
    x = torch.from_numpy(np.ascontiguousarray(x_scaled)).to(torch.float32)

    # Build edge index from match pairs
    source_nodes = df["p1_name"].map(player_to_id).astype(np.int64).values
    target_nodes = df["p2_name"].map(player_to_id).astype(np.int64).values
    edge_index_np = np.ascontiguousarray(np.stack([source_nodes, target_nodes]))
    edge_index = torch.from_numpy(edge_index_np).to(torch.long)

    # Edge targets and features
    y = torch.from_numpy(np.ascontiguousarray(df["target"].values.astype(np.float32)))

    edge_features_cols = [
        "diff_hist_apm",
        "diff_hist_sq",
        "diff_experience",
        "elo_diff",
        "expected_win_prob",
    ]
    scaler_edges = StandardScaler()
    edge_attr_np = np.ascontiguousarray(
        scaler_edges.fit_transform(df[edge_features_cols].fillna(0)).astype(np.float32)
    )
    edge_attr = torch.from_numpy(edge_attr_np)

    graph_data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
    graph_data.match_time = df["match_time"].values

    # Veteran mask: matches where both players have sufficient prior history
    veteran_mask = (
        (df["p1_total_games_played"] >= VETERAN_MIN_GAMES)
        & (df["p2_total_games_played"] >= VETERAN_MIN_GAMES)
    ).values
    graph_data.veteran_mask = torch.from_numpy(veteran_mask)

    logger.info(f"Graph built. Nodes: {num_nodes}, Edges: {len(df)}, Node features: {x.shape[1]}")

    return graph_data, player_to_id
