import torch
import torch.nn.functional as F
from torch import Tensor
from torch.nn import Dropout, Linear, ReLU, Sequential
from torch_geometric.nn import GATv2Conv

from sc2ml.config import GNN_DROPOUT, GNN_HEADS_CONV1, GNN_HEADS_CONV2, GNN_HIDDEN_DIM


class SC2EdgeClassifier(torch.nn.Module):
    """GATv2-based edge classifier for SC2 match outcome prediction.

    Architecture:
      - Two GATv2 attention convolution layers learn player node embeddings
        from the match graph structure.
      - A 3-layer MLP classifier predicts edge (match) outcomes from the
        concatenation of both player embeddings and match-level edge features.

    This is edge classification, not node classification — the target is the
    outcome of each match (edge), not a property of each player (node).
    """

    def __init__(self, node_in_dim: int, node_hidden_dim: int, edge_attr_dim: int) -> None:
        super(SC2EdgeClassifier, self).__init__()

        # Attention layers: GATv2 learns which opponent connections matter more
        self.conv1 = GATv2Conv(
            node_in_dim, node_hidden_dim, heads=GNN_HEADS_CONV1, concat=True
        )
        self.conv2 = GATv2Conv(
            node_hidden_dim * GNN_HEADS_CONV1, node_hidden_dim, heads=GNN_HEADS_CONV2, concat=False
        )

        classifier_in_dim = (node_hidden_dim * 2) + edge_attr_dim

        self.classifier = Sequential(
            Linear(classifier_in_dim, GNN_HIDDEN_DIM * 2),
            ReLU(),
            Dropout(GNN_DROPOUT),
            Linear(GNN_HIDDEN_DIM * 2, GNN_HIDDEN_DIM),
            ReLU(),
            Linear(GNN_HIDDEN_DIM, 1),
        )

    def forward(
        self,
        x: Tensor,
        message_edge_index: Tensor,
        query_edge_index: Tensor,
        query_edge_attr: Tensor,
    ) -> Tensor:
        """Compute match outcome logits for each query edge.

        Args:
            x: Node feature matrix [num_nodes, node_in_dim].
            message_edge_index: Edge index used for neighborhood aggregation (training edges).
            query_edge_index: Edge index for which to predict outcomes.
            query_edge_attr: Edge feature matrix [num_query_edges, edge_attr_dim].

        Returns:
            Logits tensor of shape [num_query_edges].
        """
        # ELU activation works better than ReLU for GAT layers
        h = self.conv1(x, message_edge_index)
        h = F.elu(h)
        h = F.dropout(h, p=GNN_DROPOUT, training=self.training)

        h = self.conv2(h, message_edge_index)
        h = F.elu(h)

        src, dst = query_edge_index
        edge_features = torch.cat([h[src], h[dst], query_edge_attr], dim=-1)

        return self.classifier(edge_features).squeeze()
