import torch
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import numpy as np
import logging

logger = logging.getLogger(__name__)

def visualize_player_embeddings(model, graph_data, player_to_id, output_path="reports/player_clusters.png"):
    logger.info("Generowanie wizualizacji embeddingów GNN...")
    
    model.eval()
    with torch.no_grad():
        # Wyciągamy wektory ukryte (h) z warstwy konwolucyjnej
        # Używamy całego grafu do wygenerowania ostatecznych reprezentacji
        h = model.conv1(graph_data.x, graph_data.edge_index)
        h = torch.relu(h)
        h = model.conv2(h, graph_data.edge_index)
        embeddings = h.cpu().numpy()

    # 1. Redukcja wymiarowości T-SNE (z 64D do 2D)
    tsne = TSNE(n_components=2, perplexity=30, n_iter=1000, random_state=42)
    embeddings_2d = tsne.fit_transform(embeddings)

    # 2. Przygotowanie listy graczy do podpisania (tylko najbardziej znani, żeby nie było tłoku)
    # Możemy wybrać np. tych, którzy mają najwięcej połączeń (krawędzi)
    id_to_player = {v: k for k, v in player_to_id.items()}
    
    # Legendarni gracze do oznaczenia
    top_pro_players = [
        "Serral", "Maru", "Reynor", "Clem", "Dark", "Rogue", "Stats", 
        "Classic", "TY", "Zest", "Innovation", "ByuN", "ShoWTimE"
    ]

    plt.figure(figsize=(12, 10))
    plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], alpha=0.5, c='gray', s=10)

    # Podpisywanie wybranych graczy
    for i, name in id_to_player.items():
        if name in top_pro_players:
            plt.scatter(embeddings_2d[i, 0], embeddings_2d[i, 1], c='red', s=50)
            plt.annotate(name, (embeddings_2d[i, 0], embeddings_2d[i, 1]), 
                         fontsize=12, fontweight='bold', xytext=(5, 2),
                         textcoords='offset points')

    plt.title("Wizualizacja Embeddingów Graczy (GNN - GraphSAGE)", fontsize=15)
    plt.xlabel("T-SNE wymiar 1")
    plt.ylabel("T-SNE wymiar 2")
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.savefig(output_path)
    logger.info(f"Wizualizacja zapisana w: {output_path}")
    plt.close()
