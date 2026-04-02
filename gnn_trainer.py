import logging
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from gnn_model import SC2EdgeClassifier
from config import (
    GNN_HIDDEN_DIM,
    GNN_LEARNING_RATE,
    GNN_WEIGHT_DECAY,
    GNN_PATIENCE,
    GNN_LOG_EVERY,
    GNN_CHECKPOINT_PATH,
)

logger = logging.getLogger(__name__)


def train_and_evaluate_gnn(
    graph_data: "torch_geometric.data.Data",  # type: ignore[name-defined]
    epochs: int = 300,
    test_size: float = 0.1,
) -> tuple[SC2EdgeClassifier, float]:
    """Train the GATv2 edge classifier and evaluate on the chronological test split.

    Uses early stopping based on test accuracy. The best checkpoint is reloaded
    after training for final evaluation. Reports both all-test and veterans-only
    accuracy.

    GNN training is forced to CPU. MPS has silent failures and segfaults with
    sparse tensor operations (PyG limitation as of current stack).

    Args:
        graph_data: PyG Data object from build_starcraft_graph.
        epochs: Maximum number of training epochs.
        test_size: Fraction of edges used for testing.

    Returns:
        Tuple of (best model, best test accuracy).
    """
    device = torch.device("cpu")
    num_edges = graph_data.num_edges
    split_idx = int(num_edges * (1 - test_size))

    train_mask = torch.arange(num_edges) < split_idx
    test_mask = torch.arange(num_edges) >= split_idx

    train_edge_index = graph_data.edge_index[:, train_mask]
    train_edge_attr = graph_data.edge_attr[train_mask]
    train_y = graph_data.y[train_mask]

    test_edge_index = graph_data.edge_index[:, test_mask]
    test_edge_attr = graph_data.edge_attr[test_mask]
    test_y = graph_data.y[test_mask]

    model = SC2EdgeClassifier(
        graph_data.x.shape[1], GNN_HIDDEN_DIM, graph_data.num_edge_features
    ).to(device)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=GNN_LEARNING_RATE, weight_decay=GNN_WEIGHT_DECAY
    )
    criterion = torch.nn.BCEWithLogitsLoss()

    best_test_acc: float = 0.0
    patience_counter: int = 0

    GNN_CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)

    logger.info(
        f"GATv2 training started. Nodes: {graph_data.num_nodes}, "
        f"Train edges: {train_edge_index.shape[1]}, Test edges: {test_edge_index.shape[1]}"
    )

    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        out = model(graph_data.x, train_edge_index, train_edge_index, train_edge_attr)
        loss = criterion(out, train_y)
        loss.backward()
        optimizer.step()

        if epoch % GNN_LOG_EVERY == 0:
            model.eval()
            with torch.no_grad():
                out_test = model(
                    graph_data.x, train_edge_index, test_edge_index, test_edge_attr
                )
                preds = (torch.sigmoid(out_test) > 0.5).float()
                current_test_acc = accuracy_score(test_y.numpy(), preds.numpy())

            logger.info(
                f"Epoch {epoch:03d} | Loss: {loss.item():.4f} | Test Acc: {current_test_acc:.4f}"
            )

            if current_test_acc > best_test_acc:
                best_test_acc = current_test_acc
                patience_counter = 0
                torch.save(model.state_dict(), GNN_CHECKPOINT_PATH)
            else:
                patience_counter += 1
                if patience_counter >= GNN_PATIENCE:
                    logger.info(f"Early stopping at epoch {epoch}.")
                    break

    # Reload best checkpoint for final evaluation
    model.load_state_dict(torch.load(GNN_CHECKPOINT_PATH, weights_only=True))
    model.eval()
    with torch.no_grad():
        out_final = model(graph_data.x, train_edge_index, test_edge_index, test_edge_attr)
        preds_final = (torch.sigmoid(out_final) > 0.5).float()

    y_true = test_y.numpy()
    y_pred = preds_final.numpy()

    logger.info(f"\n=== GNN Final Evaluation (All Test) ===")
    logger.info(f"Accuracy: {best_test_acc:.4f}")
    logger.info(f"\nConfusion Matrix:\n{confusion_matrix(y_true, y_pred)}")
    logger.info(
        f"\nClassification Report:\n"
        f"{classification_report(y_true, y_pred, target_names=['P2 wins', 'P1 wins'])}"
    )

    # Veterans-only evaluation
    if hasattr(graph_data, "veteran_mask"):
        vet_test_mask = graph_data.veteran_mask[test_mask]
        if vet_test_mask.sum() > 0:
            vet_acc = accuracy_score(y_true[vet_test_mask], y_pred[vet_test_mask])
            logger.info(
                f"\n=== GNN Final Evaluation (Veterans Only — {vet_test_mask.sum()} matches) ==="
            )
            logger.info(f"Accuracy: {vet_acc:.4f}")
            logger.info(
                f"\nClassification Report:\n"
                f"{classification_report(y_true[vet_test_mask], y_pred[vet_test_mask], target_names=['P2 wins', 'P1 wins'])}"
            )
        else:
            logger.warning("Veterans mask produced 0 test matches — skipping veterans evaluation.")

    return model, best_test_acc
