import logging
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score
from gnn_model import SC2EdgeClassifier

logger = logging.getLogger(__name__)


def train_and_evaluate_gnn(graph_data, epochs=200, test_size=0.2):
    logger.info("Rozpoczynam przygotowania do treningu End-to-End GNN (GraphSAGE)...")

    # 1. Zabezpieczenie urządzenia (Używamy CPU, by uniknąć problemów MPS ze sparse tensorami PyG)
    device = torch.device("cpu")
    graph_data = graph_data.to(device)

    # 2. Chronologiczny podział grafu (80% Train, 20% Test)
    # Grafy nie działają jak Pandas. Musimy przeciąć krawędzie (mecze) na indeksach.
    num_edges = graph_data.num_edges
    split_idx = int(num_edges * (1 - test_size)) # Elastyczny punkt cięcia

    # Maski logiczne określające, które mecze należą do którego zbioru
    train_mask = torch.arange(num_edges) < split_idx
    test_mask = torch.arange(num_edges) >= split_idx

    # 3. Krawędzie Treningowe (Służą do uczenia i do przekazywania wiadomości między graczami)
    train_edge_index = graph_data.edge_index[:, train_mask]
    train_edge_attr = graph_data.edge_attr[train_mask]
    train_y = graph_data.y[train_mask]

    # 4. Krawędzie Testowe (Służą TYLKO do weryfikacji predykcji na końcu)
    test_edge_index = graph_data.edge_index[:, test_mask]
    test_edge_attr = graph_data.edge_attr[test_mask]
    test_y = graph_data.y[test_mask]

    # 5. Inicjalizacja naszej Architektury
    node_in_dim = graph_data.x.shape[1]  # 1 (bo daliśmy wektory jedynek na start)
    node_hidden_dim = 64
    edge_attr_dim = graph_data.num_edge_features

    model = SC2EdgeClassifier(node_in_dim, node_hidden_dim, edge_attr_dim).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=0.005, weight_decay=1e-4)
    criterion = (
        nn.BCEWithLogitsLoss()
    )  # Idealna funkcja straty do klasyfikacji binarnej

    logger.info("Rozpoczynam pętlę uczącą PyTorch...")
    model.train()

    for epoch in range(1, epochs + 1):
        optimizer.zero_grad()

        # MAGIA GNN:
        # Przekazujemy train_edge_index PODWÓJNIE.
        # Pierwszy raz jako 'szkielet' po którym płyną wiadomości, drugi raz jako krawędzie do przewidzenia.
        out = model(graph_data.x, train_edge_index, train_edge_index, train_edge_attr)

        loss = criterion(out, train_y)
        loss.backward()
        optimizer.step()

        if epoch % 20 == 0:
            # Obliczamy tymczasowe Accuracy na zbiorze treningowym
            preds = (torch.sigmoid(out) > 0.5).float()
            train_acc = accuracy_score(train_y.cpu().numpy(), preds.cpu().numpy())
            logger.info(
                f"Epoka {epoch:03d} | Loss: {loss.item():.4f} | Train Acc: {train_acc:.4f}"
            )

    # ==========================================
    # 6. OSTATECZNA EWALUACJA (TEST)
    # ==========================================
    model.eval()
    logger.info("Ewaluacja GNN na ukrytym zbiorze testowym...")
    with torch.no_grad():
        # KLUCZOWE: Podczas testu sieć patrzy na 'test_edge_index', ale do zrozumienia graczy
        # nadal używa TYLKO szkieletu treningowego ('train_edge_index'). Brak wycieku danych!
        out_test = model(
            graph_data.x, train_edge_index, test_edge_index, test_edge_attr
        )

        preds_test = (torch.sigmoid(out_test) > 0.5).float()
        test_acc = accuracy_score(test_y.cpu().numpy(), preds_test.cpu().numpy())

    print(f"\n{'='*65}")
    print(f"OSTATECZNY WYNIK (End-to-End Graph Neural Network - GraphSAGE)")
    print(f"Accuracy na zbiorze testowym: {test_acc:.4f}")
    print(f"{'='*65}\n")

    return model, test_acc
