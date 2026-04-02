import logging
import pandas as pd
import networkx as nx
from node2vec import Node2Vec
from config import (
    NODE2VEC_WALK_LENGTH,
    NODE2VEC_NUM_WALKS,
    NODE2VEC_WORKERS,
    NODE2VEC_WINDOW,
    NODE2VEC_EMBEDDING_DIM,
)

logger = logging.getLogger(__name__)


def train_and_get_embeddings(
    graph_data: "torch_geometric.data.Data",  # type: ignore[name-defined]
    player_to_id: dict[str, int],
    embedding_dim: int = NODE2VEC_EMBEDDING_DIM,
) -> dict[str, list[float]]:
    """Train Node2Vec embeddings using the NetworkX/Gensim backend.

    Converts the PyG edge_index to a NetworkX graph, runs Node2Vec random
    walks, and trains a Word2Vec model (via Gensim) on the walk sequences.

    The NetworkX/Gensim backend is used instead of PyG's Node2Vec because it
    avoids MPS sparse tensor issues on Apple Silicon.

    Args:
        graph_data: PyG Data object with edge_index.
        player_to_id: Mapping from player name to node index.
        embedding_dim: Dimensionality of the output embeddings.

    Returns:
        Dictionary mapping player name to embedding vector.
    """
    logger.info("Starting Node2Vec training (NetworkX/Gensim backend)...")

    # edge_index has shape [2, num_edges] — transpose to list of (src, dst) pairs
    edges = graph_data.edge_index.t().tolist()

    G = nx.Graph()
    G.add_edges_from(edges)

    node2vec_model = Node2Vec(
        G,
        dimensions=embedding_dim,
        walk_length=NODE2VEC_WALK_LENGTH,
        num_walks=NODE2VEC_NUM_WALKS,
        workers=NODE2VEC_WORKERS,
        quiet=False,
    )

    logger.info("Generating random walks and training Word2Vec model...")
    model = node2vec_model.fit(window=NODE2VEC_WINDOW, min_count=1, batch_words=4)

    # Node2Vec treats node IDs as strings in the Gensim vocabulary
    id_to_player: dict[int, str] = {v: k for k, v in player_to_id.items()}
    embeddings_dict: dict[str, list[float]] = {}
    zero_vector = [0.0] * embedding_dim

    for i in range(len(id_to_player)):
        node_str = str(i)
        if node_str in model.wv:
            embeddings_dict[id_to_player[i]] = model.wv[node_str]
        else:
            # Fallback for isolated nodes with no walk coverage
            embeddings_dict[id_to_player[i]] = zero_vector

    logger.info(f"Node2Vec embeddings generated. Embedded {len(embeddings_dict)} players.")
    return embeddings_dict


def append_embeddings_to_df(
    df: pd.DataFrame,
    embeddings_dict: dict[str, list[float]],
    embedding_dim: int = NODE2VEC_EMBEDDING_DIM,
) -> pd.DataFrame:
    """Append Node2Vec player embeddings as new columns to the feature dataframe.

    Adds p1_emb_0 ... p1_emb_{embedding_dim-1} and equivalent p2_ columns.
    Players not found in embeddings_dict receive zero vectors.

    Args:
        df: Feature dataframe with p1_name and p2_name columns.
        embeddings_dict: Output of train_and_get_embeddings.
        embedding_dim: Dimensionality of the embedding vectors.

    Returns:
        Extended dataframe with embedding columns appended.
    """
    logger.info("Appending graph embeddings to feature dataframe...")

    zero_vector = [0.0] * embedding_dim
    p1_embs = [embeddings_dict.get(row["p1_name"], zero_vector) for _, row in df.iterrows()]
    p2_embs = [embeddings_dict.get(row["p2_name"], zero_vector) for _, row in df.iterrows()]

    p1_emb_df = pd.DataFrame(p1_embs, columns=[f"p1_emb_{i}" for i in range(embedding_dim)])
    p2_emb_df = pd.DataFrame(p2_embs, columns=[f"p2_emb_{i}" for i in range(embedding_dim)])

    df = df.reset_index(drop=True)
    features_df = pd.concat([df, p1_emb_df, p2_emb_df], axis=1)

    logger.info(f"Embeddings appended. New feature count: {features_df.shape[1]}")
    return features_df
