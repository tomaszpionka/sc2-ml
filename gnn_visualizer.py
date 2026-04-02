import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from config import (
    TSNE_N_COMPONENTS,
    TSNE_PERPLEXITY,
    TSNE_N_ITER,
    RANDOM_SEED,
    VIZ_DPI,
    GNN_VIZ_OUTPUT_PATH,
)

logger = logging.getLogger(__name__)

# SC2 pros to annotate on the map
TOP_PLAYERS = [
    "Serral", "Maru", "Clem", "Reynor", "Dark", "Rogue", "Stats", "Classic", "ByuN",
]

RACE_COLORS = {
    "Zerg": "#b300b3",
    "Terran": "#0066ff",
    "Protoss": "#ffcc00",
    "Unknown": "#cccccc",
}


def visualize_gnn_space(
    model: "SC2EdgeClassifier",  # type: ignore[name-defined]
    graph_data: "torch_geometric.data.Data",  # type: ignore[name-defined]
    player_to_id: dict[str, int],
    features_df: pd.DataFrame,
    test_size: float = 0.05,
    output_path: Path = GNN_VIZ_OUTPUT_PATH,
) -> None:
    """Generate a t-SNE visualization of the GNN's learned player embedding space.

    Extracts node embeddings after the two GATv2 layers, reduces to 2D via t-SNE,
    and colors each player point by their most frequently played race. Known top
    pros are annotated by name.

    Args:
        model: Trained SC2EdgeClassifier.
        graph_data: PyG Data object from build_starcraft_graph.
        player_to_id: Mapping from player name to node index.
        features_df: Feature dataframe with race one-hot columns.
        test_size: Fraction used as test edges (determines training edge boundary).
        output_path: Path where the PNG will be saved.
    """
    logger.info("Generating GNN embedding space visualization (t-SNE)...")

    model.eval()
    with torch.no_grad():
        # Extract node embeddings from the GATv2 layers using training edges only
        num_edges = graph_data.num_edges
        train_mask = torch.arange(num_edges) < int(num_edges * (1.0 - test_size))
        train_edges = graph_data.edge_index[:, train_mask]

        h = model.conv1(graph_data.x, train_edges)
        h = F.elu(h)
        h = model.conv2(h, train_edges)
        embeddings = h.cpu().numpy()

    logger.info("Computing t-SNE dimensionality reduction (this may take a moment)...")
    tsne = TSNE(
        n_components=TSNE_N_COMPONENTS,
        perplexity=TSNE_PERPLEXITY,
        n_iter=TSNE_N_ITER,
        random_state=RANDOM_SEED,
        init="pca",
    )
    z = tsne.fit_transform(embeddings)

    # Map each player to their most frequently played race in this dataset
    id_to_player: dict[int, str] = {v: k for k, v in player_to_id.items()}
    player_races: dict[str, str] = {}
    for _, row in features_df.iterrows():
        if row["p1_name"] not in player_races:
            if row.get("p1_race_Zerg", 0):
                player_races[row["p1_name"]] = "Zerg"
            elif row.get("p1_race_Terran", 0):
                player_races[row["p1_name"]] = "Terran"
            elif row.get("p1_race_Protoss", 0):
                player_races[row["p1_name"]] = "Protoss"

    # Plot
    plt.figure(figsize=(14, 10), facecolor="#1a1a1a")
    ax = plt.gca()
    ax.set_facecolor("#1a1a1a")

    for race, color in RACE_COLORS.items():
        indices = [
            i for i, name in id_to_player.items()
            if player_races.get(name, "Unknown") == race
        ]
        if indices:
            plt.scatter(
                z[indices, 0], z[indices, 1],
                c=color, label=race, alpha=0.6, s=25, edgecolors="none",
            )

    # Annotate known top players (case-insensitive match)
    for i, name in id_to_player.items():
        matches = [tp for tp in TOP_PLAYERS if tp.lower() == name.lower()]
        if matches:
            plt.scatter(z[i, 0], z[i, 1], c="white", s=100, edgecolors="red", linewidth=2)
            plt.annotate(
                matches[0],
                (z[i, 0], z[i, 1]),
                color="white",
                fontsize=12,
                fontweight="bold",
                xytext=(5, 5),
                textcoords="offset points",
                bbox=dict(boxstyle="round,pad=0.3", fc="black", ec="red", alpha=0.7),
            )

    plt.title(
        "StarCraft II player embedding space: GNN (GATv2)",
        color="white", fontsize=16, pad=20,
    )
    legend = plt.legend(title="Race", loc="best", facecolor="#333333", edgecolor="white")
    plt.setp(legend.get_texts(), color="white")
    plt.setp(legend.get_title(), color="white")

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=VIZ_DPI, facecolor="#1a1a1a")
    logger.info(f"Visualization saved to: {output_path}")
