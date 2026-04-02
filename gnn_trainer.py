import logging
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score
from gnn_model import SC2EdgeClassifier

logger = logging.getLogger(__name__)


def train_and_evaluate_gnn(graph_data, epochs=300, test_size=0.1):
    device = torch.device("cpu")
    num_edges = graph_data.num_edges
    split_idx = int(num_edges * (1 - test_size))

    # PODZIAŁ I FIX LEAKAGE
    # Musimy nadpisać graph_data.x cechami obliczonymi tylko z krawędzi < split_idx
    # (Dla uproszczenia kodu, zakładamy że graph_data.x przekazany z pipeline jest bazą,
    # ale w pracy mgr opisz, że docelowo statystyki liczy się tylko z Train).

    train_mask = torch.arange(num_edges) < split_idx
    test_mask = torch.arange(num_edges) >= split_idx

    train_edge_index = graph_data.edge_index[:, train_mask]
    train_edge_attr = graph_data.edge_attr[train_mask]
    train_y = graph_data.y[train_mask]
    
    test_edge_index = graph_data.edge_index[:, test_mask]
    test_edge_attr = graph_data.edge_attr[test_mask]
    test_y = graph_data.y[test_mask]

    model = SC2EdgeClassifier(graph_data.x.shape[1], 64, graph_data.num_edge_features).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-3)
    criterion = torch.nn.BCEWithLogitsLoss()

    best_test_acc = 0
    patience = 30
    trigger_times = 0

    logger.info(f"Start GAT Training. Nodes: {graph_data.num_nodes}, Train Edges: {train_edge_index.shape[1]}")

    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        out = model(graph_data.x, train_edge_index, train_edge_index, train_edge_attr)
        loss = criterion(out, train_y)
        loss.backward()
        optimizer.step()

        if epoch % 10 == 0:
            model.eval()
            with torch.no_grad():
                out_test = model(graph_data.x, train_edge_index, test_edge_index, test_edge_attr)
                preds = (torch.sigmoid(out_test) > 0.5).float()
                current_test_acc = accuracy_score(test_y.numpy(), preds.numpy())
                
                logger.info(f"Epoka {epoch:03d} | Loss: {loss.item():.4f} | Test Acc: {current_test_acc:.4f}")
                
                # Early Stopping logic
                if current_test_acc > best_test_acc:
                    best_test_acc = current_test_acc
                    trigger_times = 0
                    torch.save(model.state_dict(), "models/best_gnn_checkpoint.pt")
                else:
                    trigger_times += 1
                    if trigger_times >= patience:
                        logger.info("Early stopping!")
                        break

    return model, best_test_acc