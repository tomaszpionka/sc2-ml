import logging
import torch
import torch.nn.functional as F
from torch.nn import Linear, Sequential, ReLU, Dropout
from torch_geometric.nn import SAGEConv

logger = logging.getLogger(__name__)


class SC2EdgeClassifier(torch.nn.Module):
    def __init__(self, node_in_dim, node_hidden_dim, edge_attr_dim):
        """
        Architektura GNN dla zadania Edge Classification.
        """
        super(SC2EdgeClassifier, self).__init__()

        # 1. Warstwy konwolucji grafowej (GraphSAGE)
        # Służą do nauki reprezentacji graczy na podstawie tego, z kim grają.
        self.conv1 = SAGEConv(node_in_dim, node_hidden_dim)
        self.conv2 = SAGEConv(node_hidden_dim, node_hidden_dim)

        # 2. Klasyfikator krawędzi (MLP - Multi-Layer Perceptron)
        # Rozmiar wejścia = (wektor P1) + (wektor P2) + (cechy tabelaryczne z Pandas)
        classifier_in_dim = (node_hidden_dim * 2) + edge_attr_dim

        self.classifier = Sequential(
            Linear(classifier_in_dim, 64),
            ReLU(),
            Dropout(0.3),  # Zapobiega overfittingowi
            Linear(64, 32),
            ReLU(),
            Linear(32, 1),  # Zwraca pojedynczą wartość (Logit przewidujący wygraną P1)
        )

    def forward(self, x, message_edge_index, query_edge_index, query_edge_attr):
        """
        Przejście w przód (Forward Pass)
        - x: Początkowe cechy węzłów
        - message_edge_index: Krawędzie używane do "rozmowy" między węzłami (Tylko dane treningowe!)
        - query_edge_index: Krawędzie meczów, których wynik chcemy przewidzieć
        - query_edge_attr: Zmienne takie jak różnica ELO dla przewidywanych meczów
        """
        # FAZA 1: Message Passing (Uczenie reprezentacji węzłów)
        h = self.conv1(x, message_edge_index)
        h = F.relu(h)
        h = F.dropout(h, p=0.3, training=self.training)
        h = self.conv2(h, message_edge_index)
        # Teraz wektor 'h' zawiera "zrozumienie" siły i stylu każdego gracza

        # FAZA 2: Budowanie cech dla konkretnego meczu
        src, dst = query_edge_index  # P1 (Source) i P2 (Destination)

        # Pobieramy wektory wyuczone w FAZIE 1
        h_src = h[src]
        h_dst = h[dst]

        # Konkatenacja wektorów graczy z cechami meczu (ELO, Różnica APM)
        edge_features = torch.cat([h_src, h_dst, query_edge_attr], dim=-1)

        # FAZA 3: Ostateczna predykcja
        return self.classifier(edge_features).squeeze()
