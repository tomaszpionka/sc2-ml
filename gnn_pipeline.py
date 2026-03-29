import logging
import torch
import numpy as np
import pandas as pd
from torch_geometric.data import Data
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


def build_starcraft_graph(df):
    logger.info("Budowanie struktury Grafu dla GNN...")

    # 1. Mapowanie graczy
    unique_players = pd.concat([df["p1_name"], df["p2_name"]]).unique()
    player_to_id = {name: idx for idx, name in enumerate(unique_players)}
    num_nodes = len(unique_players)
    logger.info(f"Liczba węzłów (unikalnych graczy): {num_nodes}")

    # 2. Budowanie krawędzi (Edges)
    # Gwarantujemy, że wyciągamy liczby całkowite
    source_nodes = df["p1_name"].map(player_to_id).astype(np.int64).values
    target_nodes = df["p2_name"].map(player_to_id).astype(np.int64).values

    # --- NAPRAWA SEGFAULTA (Pamięć ciągła) ---
    edge_index_np = np.stack([source_nodes, target_nodes], axis=0)
    edge_index_np = np.ascontiguousarray(edge_index_np)  # Wymusza ciągły blok pamięci!
    edge_index = torch.from_numpy(edge_index_np).to(torch.long)

    # 3. Zmienna celu (Target)
    y_np = df["target"].values.astype(np.float32)
    y_np = np.ascontiguousarray(y_np)
    y = torch.from_numpy(y_np)

    # 4. Cechy krawędzi (Edge Features)
    edge_features_cols = [
        "diff_experience",
        "diff_hist_apm",
        "diff_hist_sq",
        "diff_hist_game_length",
        "elo_diff",
        "expected_win_prob",
    ]

    scaler = StandardScaler()
    edge_attr_np = scaler.fit_transform(df[edge_features_cols].fillna(0)).astype(
        np.float32
    )
    edge_attr_np = np.ascontiguousarray(edge_attr_np)
    edge_attr = torch.from_numpy(edge_attr_np)

    # 5. Cechy węzłów (Node Features)
    x = torch.ones((num_nodes, 1), dtype=torch.float32)

    # 6. Budowa obiektu Data
    graph_data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
    graph_data.match_time = df["match_time"].values

    logger.info(f"Graf zbudowany pomyślnie!")
    logger.info(f"- Węzły: {graph_data.num_nodes}")
    logger.info(f"- Krawędzie: {graph_data.num_edges}")
    logger.info(f"- Cechy krawędzi: {graph_data.num_edge_features}")

    return graph_data, player_to_id
