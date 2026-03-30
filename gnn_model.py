import torch
import torch.nn.functional as F
from torch.nn import Linear, Sequential, ReLU, Dropout
from torch_geometric.nn import GATv2Conv # Używamy mechanizmu uwagi (Attention)

class SC2EdgeClassifier(torch.nn.Module):
    def __init__(self, node_in_dim, node_hidden_dim, edge_attr_dim):
        super(SC2EdgeClassifier, self).__init__()
        
        # Warstwy uwagi - model uczy się, którzy przeciwnicy są ważniejsi
        self.conv1 = GATv2Conv(node_in_dim, node_hidden_dim, heads=4, concat=True)
        self.conv2 = GATv2Conv(node_hidden_dim * 4, node_hidden_dim, heads=1, concat=False)

        classifier_in_dim = (node_hidden_dim * 2) + edge_attr_dim
        
        self.classifier = Sequential(
            Linear(classifier_in_dim, 128),
            ReLU(),
            Dropout(0.4),
            Linear(128, 64),
            ReLU(),
            Linear(64, 1)
        )

    def forward(self, x, message_edge_index, query_edge_index, query_edge_attr):
        # x: Atrybuty węzłów (APM, WR, itp.)
        h = self.conv1(x, message_edge_index)
        h = F.elu(h) # GAT lepiej działa z aktywacją ELU
        h = F.dropout(h, p=0.4, training=self.training)
        
        h = self.conv2(h, message_edge_index)
        h = F.elu(h)

        src, dst = query_edge_index
        edge_features = torch.cat([h[src], h[dst], query_edge_attr], dim=-1)

        return self.classifier(edge_features).squeeze()