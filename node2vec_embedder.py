import logging
import pandas as pd
import networkx as nx
from node2vec import Node2Vec

logger = logging.getLogger(__name__)


def train_and_get_embeddings(graph_data, player_to_id, embedding_dim=64):
    logger.info(
        "Rozpoczynam trening Node2Vec (tryb NetworkX/Gensim - Bulletproof dla Maca)..."
    )

    # 1. Konwersja krawędzi z formatu PyTorch na listę dla NetworkX
    # edge_index ma wymiar [2, num_edges], transponujemy go i zamieniamy na Pythonowe listy
    edges = graph_data.edge_index.t().tolist()

    # 2. Budowa grafu w NetworkX
    G = nx.Graph()
    G.add_edges_from(edges)

    # 3. Konfiguracja Node2Vec (z dedykowanego pakietu)
    # workers=4 bezpiecznie wykorzysta wielowątkowość Twojego M4 Max!
    node2vec_model = Node2Vec(
        G,
        dimensions=embedding_dim,
        walk_length=20,
        num_walks=10,
        workers=4,
        quiet=False,
    )

    # 4. Trening modelu (bazującego na silniku Word2Vec z Gensim)
    logger.info("Generowanie spacerów losowych i trening modelu...")
    model = node2vec_model.fit(window=10, min_count=1, batch_words=4)

    # 5. Wyciąganie wygenerowanych wektorów
    id_to_player = {v: k for k, v in player_to_id.items()}
    embeddings_dict = {}

    # Zapisujemy wektory (node2vec traktuje ID węzłów jako stringi)
    for i in range(len(id_to_player)):
        node_str = str(i)
        if node_str in model.wv:
            embeddings_dict[id_to_player[i]] = model.wv[node_str]
        else:
            # Fallback dla skrajnie odizolowanych węzłów
            embeddings_dict[id_to_player[i]] = [0.0] * embedding_dim

    logger.info("Embeddingi Node2Vec wygenerowane pomyślnie za pomocą silnika Gensim.")
    return embeddings_dict


def append_embeddings_to_df(df, embeddings_dict, embedding_dim=64):
    logger.info("Doklejanie embeddingów grafowych do głównego zbioru Pandas...")

    p1_embs = []
    p2_embs = []
    zeros = [0.0] * embedding_dim

    for _, row in df.iterrows():
        p1_embs.append(embeddings_dict.get(row["p1_name"], zeros))
        p2_embs.append(embeddings_dict.get(row["p2_name"], zeros))

    p1_emb_df = pd.DataFrame(
        p1_embs, columns=[f"p1_emb_{i}" for i in range(embedding_dim)]
    )
    p2_emb_df = pd.DataFrame(
        p2_embs, columns=[f"p2_emb_{i}" for i in range(embedding_dim)]
    )

    df = df.reset_index(drop=True)
    features_df = pd.concat([df, p1_emb_df, p2_emb_df], axis=1)

    logger.info(f"Zbiór danych powiększony! Nowa liczba cech: {features_df.shape[1]}")
    return features_df
