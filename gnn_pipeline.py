import logging
import torch
import numpy as np
import pandas as pd
from torch_geometric.data import Data
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

def build_starcraft_graph(df):
    logger.info("Budowanie Grafu (Node Features z cech historycznych + Edge Features)...")

    # 1. Mapowanie graczy
    unique_players = pd.concat([df['p1_name'], df['p2_name']]).unique()
    player_to_id = {name: idx for idx, name in enumerate(unique_players)}
    # DODANA LINIA: Odwracamy słownik, aby móc iterować po ID
    id_to_player = {idx: name for name, idx in player_to_id.items()}
    num_nodes = len(unique_players)

    # --- OBLICZANIE STATYSTYK WĘZŁÓW (Graczy) ---
    player_stats = {}
    
    # Wykorzystujemy cechy historyczne, które przetrwały w df
    for name in unique_players:
        p1_data = df[df['p1_name'] == name]
        p2_data = df[df['p2_name'] == name]
        
        # Agregujemy historyczne średnie (bezpieczne przed leakage)
        avg_apm = pd.concat([p1_data['p1_hist_mean_apm'], p2_data['p2_hist_mean_apm']]).mean()
        avg_sq = pd.concat([p1_data['p1_hist_mean_sq'], p2_data['p2_hist_mean_sq']]).mean()
        avg_wr = pd.concat([p1_data['p1_hist_winrate_smooth'], p2_data['p2_hist_winrate_smooth']]).mean()
        avg_exp = pd.concat([p1_data['p1_total_games_played'], p2_data['p2_total_games_played']]).max()

        player_stats[name] = [
            avg_apm if not np.isnan(avg_apm) else 150.0,
            avg_sq if not np.isnan(avg_sq) else 50.0,
            avg_wr if not np.isnan(avg_wr) else 0.5,
            float(avg_exp) if not np.isnan(avg_exp) else 0.0
        ]

    # Budujemy macierz X
    # Teraz id_to_player[i] zadziała poprawnie
    x_list = [player_stats[id_to_player[i]] for i in range(num_nodes)]
    x_np = np.array(x_list, dtype=np.float32)
    
    # Skalowanie cech węzłów
    scaler_nodes = StandardScaler()
    x_scaled = scaler_nodes.fit_transform(x_np)
    x = torch.from_numpy(np.ascontiguousarray(x_scaled)).to(torch.float32)

    # 2. Budowanie krawędzi (Edges)
    source_nodes = df['p1_name'].map(player_to_id).astype(np.int64).values
    target_nodes = df['p2_name'].map(player_to_id).astype(np.int64).values
    
    edge_index_np = np.ascontiguousarray(np.stack([source_nodes, target_nodes]))
    edge_index = torch.from_numpy(edge_index_np).to(torch.long)

    # 3. Target i Cechy Krawędzi
    y = torch.from_numpy(np.ascontiguousarray(df['target'].values.astype(np.float32)))

    edge_features_cols = [
        'diff_hist_apm', 'diff_hist_sq', 'diff_experience', 
        'elo_diff', 'expected_win_prob'
    ]
    
    scaler_edges = StandardScaler()
    edge_attr_np = np.ascontiguousarray(scaler_edges.fit_transform(df[edge_features_cols].fillna(0)).astype(np.float32))
    edge_attr = torch.from_numpy(edge_attr_np)

    # 4. Obiekt Data
    graph_data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
    graph_data.match_time = df['match_time'].values
    
    logger.info(f"Hardcore Graf zbudowany pomyślnie! Liczba cech węzła: {x.shape[1]}")
    
    return graph_data, player_to_id