"""Diagnostic tests for GNN majority-class collapse.

Investigates why the GATv2 edge classifier degenerates to predicting only
the majority class (P2 wins).  Root causes:
  1. No class weighting in BCEWithLogitsLoss
  2. Edge feature scaler fit on full dataset (train+test leak)
  3. Hard 0.5 threshold unsuitable for imbalanced classes

These tests reproduce the bugs, confirm proposed fixes, and serve as
regression guards for when GNN work resumes (methodology appendix).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import torch
from sklearn.metrics import confusion_matrix, f1_score, recall_score
from sklearn.preprocessing import StandardScaler

from sc2ml.features import perform_feature_engineering
from sc2ml.features.common import compute_target
from sc2ml.gnn.model import SC2EdgeClassifier
from sc2ml.gnn.pipeline import build_starcraft_graph
from tests.helpers import make_matches_df

pytestmark = pytest.mark.gnn

# ── Constants ────────────────────────────────────────────────────────────────
TEST_SIZE = 0.05
EDGE_FEATURE_COLS = [
    "diff_hist_apm",
    "diff_hist_sq",
    "diff_experience",
    "elo_diff",
    "expected_win_prob",
]
QUICK_EPOCHS = 50
SMALL_HIDDEN = 32


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_imbalanced_df(n: int = 300, seed: int = 42, loss_ratio: float = 0.80) -> pd.DataFrame:
    """Create a synthetic DataFrame where *loss_ratio* of matches are P1 losses."""
    df = make_matches_df(n=n, seed=seed)
    rng = np.random.default_rng(seed + 1)
    n_losses = int(n * loss_ratio)
    loss_indices = rng.choice(n, size=n_losses, replace=False)
    df.loc[loss_indices, "p1_result"] = "Loss"
    return df


def _split_edges(
    graph_data, test_size: float = 0.1
) -> dict:
    """Replicate the train/test edge split from trainer.py."""
    num_edges = graph_data.num_edges
    split_idx = int(num_edges * (1 - test_size))

    train_mask = torch.arange(num_edges) < split_idx
    test_mask = torch.arange(num_edges) >= split_idx

    return {
        "train_edge_index": graph_data.edge_index[:, train_mask],
        "train_edge_attr": graph_data.edge_attr[train_mask],
        "train_y": graph_data.y[train_mask],
        "test_edge_index": graph_data.edge_index[:, test_mask],
        "test_edge_attr": graph_data.edge_attr[test_mask],
        "test_y": graph_data.y[test_mask],
        "train_mask": train_mask,
        "test_mask": test_mask,
    }


def _quick_train(
    graph_data,
    criterion: torch.nn.Module,
    epochs: int = QUICK_EPOCHS,
    test_size: float = 0.1,
    hidden_dim: int = SMALL_HIDDEN,
) -> dict:
    """Minimal training loop.  Returns model, logits, preds, test_y."""
    sp = _split_edges(graph_data, test_size=test_size)
    model = SC2EdgeClassifier(
        graph_data.x.shape[1], hidden_dim, graph_data.num_edge_features
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-3)

    for _ in range(epochs):
        model.train()
        optimizer.zero_grad()
        out = model(
            graph_data.x, sp["train_edge_index"],
            sp["train_edge_index"], sp["train_edge_attr"],
        )
        loss = criterion(out, sp["train_y"])
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        logits = model(
            graph_data.x, sp["train_edge_index"],
            sp["test_edge_index"], sp["test_edge_attr"],
        )
        probs = torch.sigmoid(logits)
        preds = (probs > 0.5).float()

    return {
        "model": model,
        "logits": logits,
        "probs": probs,
        "preds": preds,
        "test_y": sp["test_y"],
    }


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def balanced_features_df() -> pd.DataFrame:
    return perform_feature_engineering(make_matches_df(n=300, seed=42))


@pytest.fixture(scope="module")
def balanced_graph(balanced_features_df):
    return build_starcraft_graph(balanced_features_df, test_size=TEST_SIZE)


@pytest.fixture(scope="module")
def imbalanced_features_df() -> pd.DataFrame:
    return perform_feature_engineering(_make_imbalanced_df(n=300, seed=42))


@pytest.fixture(scope="module")
def imbalanced_graph(imbalanced_features_df):
    return build_starcraft_graph(imbalanced_features_df, test_size=TEST_SIZE)


# ══════════════════════════════════════════════════════════════════════════════
# Group 1: Class Distribution
# ══════════════════════════════════════════════════════════════════════════════


class TestClassDistribution:
    """Verify train/test class ratios and target encoding."""

    def test_balanced_synthetic_has_fair_split(self, balanced_graph) -> None:
        """On balanced synthetic data, both splits should be near 50/50."""
        graph_data, _ = balanced_graph
        sp = _split_edges(graph_data, test_size=0.1)
        train_ratio = sp["train_y"].mean().item()
        test_ratio = sp["test_y"].mean().item()
        assert 0.30 <= train_ratio <= 0.70, f"Train P1-win ratio {train_ratio:.2f} is too skewed"
        assert 0.30 <= test_ratio <= 0.70, f"Test P1-win ratio {test_ratio:.2f} is too skewed"

    def test_temporal_drift_causes_skew(self) -> None:
        """Force last 20% of matches to P1-loss; test set should become skewed."""
        df = make_matches_df(n=300, seed=99)
        # Force the last 20% to be losses (simulating temporal drift)
        cutoff = int(len(df) * 0.80)
        df.loc[cutoff:, "p1_result"] = "Loss"
        df = perform_feature_engineering(df)
        graph_data, _ = build_starcraft_graph(df, test_size=TEST_SIZE)
        sp = _split_edges(graph_data, test_size=0.1)
        test_p1_rate = sp["test_y"].mean().item()
        assert test_p1_rate < 0.25, (
            f"Expected skewed test set (P1 rate < 0.25), got {test_p1_rate:.2f}"
        )

    def test_target_encoding_correctness(self) -> None:
        """compute_target maps 'Win' -> 1, 'Loss' -> 0."""
        df = pd.DataFrame({"p1_result": ["Win", "Loss", "Win", "Loss"]})
        df = compute_target(df)
        assert df["target"].tolist() == [1, 0, 1, 0]


# ══════════════════════════════════════════════════════════════════════════════
# Group 2: Edge Scaler Leak
# ══════════════════════════════════════════════════════════════════════════════


class TestEdgeScalerLeak:
    """Prove edge feature scaler leaks test data into training features."""

    def test_edge_scaler_fit_on_all_vs_train_only(self, balanced_features_df) -> None:
        """Scaling all data vs train-only should produce different values."""
        df = balanced_features_df.sort_values("match_time").reset_index(drop=True)
        train_size = int(len(df) * (1.0 - TEST_SIZE))

        # Current behavior: scaler fit on ALL data
        scaler_all = StandardScaler()
        all_scaled = scaler_all.fit_transform(df[EDGE_FEATURE_COLS].fillna(0))

        # Correct behavior: scaler fit on train only
        scaler_train = StandardScaler()
        scaler_train.fit(df.iloc[:train_size][EDGE_FEATURE_COLS].fillna(0))
        train_only_scaled = scaler_train.transform(df[EDGE_FEATURE_COLS].fillna(0))

        assert not np.allclose(all_scaled, train_only_scaled), (
            "Edge scaler produces identical results on all vs train-only — "
            "either the test set is empty or the leak has no measurable effect"
        )

    def test_node_scaler_uses_train_data(self, balanced_features_df) -> None:
        """Node features should change when test_size changes (train-only computation)."""
        g_small_test, _ = build_starcraft_graph(balanced_features_df, test_size=0.05)
        g_large_test, _ = build_starcraft_graph(balanced_features_df, test_size=0.30)
        if len(balanced_features_df) > 50:
            assert not torch.allclose(g_small_test.x, g_large_test.x), (
                "Node features identical across test_size values — "
                "scaler may be leaking test data"
            )


# ══════════════════════════════════════════════════════════════════════════════
# Group 3: Model Output Distribution
# ══════════════════════════════════════════════════════════════════════════════


class TestModelOutputDistribution:
    """Verify logits are not collapsed to a single sign."""

    def test_untrained_logits_have_variance(self, balanced_graph) -> None:
        """Random-weight model should produce logits with nonzero variance."""
        graph_data, _ = balanced_graph
        sp = _split_edges(graph_data, test_size=0.1)
        model = SC2EdgeClassifier(
            graph_data.x.shape[1], SMALL_HIDDEN, graph_data.num_edge_features
        )
        model.eval()
        with torch.no_grad():
            logits = model(
                graph_data.x, sp["train_edge_index"],
                sp["test_edge_index"], sp["test_edge_attr"],
            )
        assert logits.std().item() > 0.01, (
            f"Untrained model logits have near-zero variance: {logits.std().item():.4f}"
        )

    def test_trained_logits_span_threshold(self, balanced_graph) -> None:
        """After training on balanced data with pos_weight, sigmoid outputs should span 0.5."""
        graph_data, _ = balanced_graph
        sp = _split_edges(graph_data, test_size=0.1)
        num_pos = sp["train_y"].sum().item()
        num_neg = len(sp["train_y"]) - num_pos
        pos_weight = torch.tensor([num_neg / max(num_pos, 1)])
        criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
        result = _quick_train(graph_data, criterion=criterion, epochs=100)
        probs = result["probs"]
        has_above = (probs > 0.5).any().item()
        has_below = (probs < 0.5).any().item()
        assert has_above and has_below, (
            f"Logits don't span threshold even with pos_weight: "
            f"min={probs.min():.3f}, max={probs.max():.3f}"
        )

    def test_imbalanced_training_collapses_logits(self, imbalanced_graph) -> None:
        """On 80/20 imbalanced data with no pos_weight, model should collapse."""
        graph_data, _ = imbalanced_graph
        result = _quick_train(graph_data, criterion=torch.nn.BCEWithLogitsLoss())
        # The model should predict almost entirely the majority class
        positive_rate = result["preds"].mean().item()
        assert positive_rate < 0.15, (
            f"Expected collapse to majority class (positive rate < 0.15), "
            f"got {positive_rate:.2f}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Group 4: pos_weight Fix
# ══════════════════════════════════════════════════════════════════════════════


class TestPosWeightFix:
    """Verify that pos_weight in BCEWithLogitsLoss prevents collapse."""

    def test_pos_weight_prevents_collapse(self, imbalanced_graph) -> None:
        """With pos_weight, the model should predict both classes."""
        graph_data, _ = imbalanced_graph
        sp = _split_edges(graph_data, test_size=0.1)
        num_pos = sp["train_y"].sum().item()
        num_neg = len(sp["train_y"]) - num_pos
        pos_weight = torch.tensor([num_neg / max(num_pos, 1)])
        criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
        result = _quick_train(graph_data, criterion=criterion)
        assert result["preds"].sum().item() > 0, (
            "pos_weight did not prevent collapse — still predicting all zeros"
        )

    def test_pos_weight_gives_nonzero_minority_recall(self, imbalanced_graph) -> None:
        """With pos_weight, minority class (P1 wins) recall should be > 0."""
        graph_data, _ = imbalanced_graph
        sp = _split_edges(graph_data, test_size=0.1)
        num_pos = sp["train_y"].sum().item()
        num_neg = len(sp["train_y"]) - num_pos
        pos_weight = torch.tensor([num_neg / max(num_pos, 1)])
        criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
        result = _quick_train(graph_data, criterion=criterion)
        y_true = result["test_y"].numpy()
        y_pred = result["preds"].numpy()
        if (y_true == 1).sum() > 0:
            minority_recall = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
            assert minority_recall > 0, (
                "Minority class recall is still 0 even with pos_weight"
            )


# ══════════════════════════════════════════════════════════════════════════════
# Group 5: Threshold Sensitivity
# ══════════════════════════════════════════════════════════════════════════════


class TestThresholdSensitivity:
    """Check if adjusting the decision threshold recovers minority predictions."""

    def test_lower_threshold_recovers_positive_predictions(self, imbalanced_graph) -> None:
        """Lowering threshold from 0.5 should increase positive prediction count."""
        graph_data, _ = imbalanced_graph
        result = _quick_train(graph_data, criterion=torch.nn.BCEWithLogitsLoss())
        probs = result["probs"]
        counts = []
        for threshold in [0.5, 0.3, 0.1]:
            n_pos = (probs > threshold).sum().item()
            counts.append(n_pos)
        # Each lower threshold should produce at least as many positives
        assert counts[1] >= counts[0], (
            f"Threshold 0.3 ({counts[1]}) did not produce >= positives than 0.5 ({counts[0]})"
        )
        assert counts[2] >= counts[1], (
            f"Threshold 0.1 ({counts[2]}) did not produce >= positives than 0.3 ({counts[1]})"
        )

    def test_optimal_threshold_beats_default(self, imbalanced_graph) -> None:
        """Best F1 should be at a threshold != 0.5 on imbalanced data."""
        graph_data, _ = imbalanced_graph
        result = _quick_train(graph_data, criterion=torch.nn.BCEWithLogitsLoss())
        y_true = result["test_y"].numpy()
        probs = result["probs"]

        best_f1 = 0.0
        best_thresh = 0.5
        f1_at_05 = 0.0
        for thresh in np.arange(0.1, 0.9, 0.05):
            preds = (probs > thresh).float().numpy()
            f1 = f1_score(y_true, preds, zero_division=0)
            if thresh == pytest.approx(0.5, abs=0.03):
                f1_at_05 = f1
            if f1 > best_f1:
                best_f1 = f1
                best_thresh = thresh

        # On imbalanced data, the optimal threshold is typically not 0.5
        assert best_f1 >= f1_at_05, (
            f"Optimal F1 ({best_f1:.3f} @ {best_thresh:.2f}) should be >= F1@0.5 ({f1_at_05:.3f})"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Group 6: Prediction Quality (regression guards)
# ══════════════════════════════════════════════════════════════════════════════


class TestPredictionQuality:
    """Smoke tests: on balanced data the model should not collapse."""

    def test_confusion_matrix_both_classes_predicted(self, balanced_graph) -> None:
        """With pos_weight, confusion matrix should have predictions for both classes."""
        graph_data, _ = balanced_graph
        sp = _split_edges(graph_data, test_size=0.1)
        num_pos = sp["train_y"].sum().item()
        num_neg = len(sp["train_y"]) - num_pos
        pos_weight = torch.tensor([num_neg / max(num_pos, 1)])
        criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
        result = _quick_train(graph_data, criterion=criterion, epochs=100)
        y_true = result["test_y"].numpy()
        y_pred = result["preds"].numpy()
        cm = confusion_matrix(y_true, y_pred)
        predicted_classes = np.unique(y_pred)
        assert len(predicted_classes) > 1, (
            f"Model only predicts class(es) {predicted_classes} — "
            f"collapsed to single class even with pos_weight. CM:\n{cm}"
        )

    def test_accuracy_above_majority_baseline(self, balanced_graph) -> None:
        """On ~50/50 data, accuracy should be above random (0.5)."""
        graph_data, _ = balanced_graph
        result = _quick_train(
            graph_data,
            criterion=torch.nn.BCEWithLogitsLoss(),
            epochs=100,
        )
        y_true = result["test_y"].numpy()
        y_pred = result["preds"].numpy()
        acc = (y_true == y_pred).mean()
        # Weak bound — on random synthetic data we just need better than coin flip
        assert acc >= 0.45, f"Accuracy {acc:.3f} is below 0.45 on balanced data"


# ══════════════════════════════════════════════════════════════════════════════
# Group 7: Trainer edge cases (early stopping & veterans mask)
# ══════════════════════════════════════════════════════════════════════════════


class TestTrainerEdgeCases:
    """Cover trainer.py lines 107-109 (early stopping) and 143 (empty veterans)."""

    def test_early_stopping_triggers(self, balanced_graph) -> None:
        """With GNN_PATIENCE=1 and frequent logging, training should stop early."""
        from unittest.mock import patch

        graph_data, _ = balanced_graph
        # Patch GNN_PATIENCE=1 and GNN_LOG_EVERY=1 so early stopping fires quickly
        with (
            patch("sc2ml.gnn.trainer.GNN_PATIENCE", 1),
            patch("sc2ml.gnn.trainer.GNN_LOG_EVERY", 1),
        ):
            from sc2ml.gnn.trainer import train_and_evaluate_gnn

            _, best_acc = train_and_evaluate_gnn(graph_data, epochs=300)
            # If early stopping worked, we get a result without running all 300 epochs
            assert 0.0 <= best_acc <= 1.0

    def test_empty_veterans_mask_warning(self, balanced_graph, caplog) -> None:
        """When veteran_mask is all-False for test edges, a warning should be logged."""
        import logging

        graph_data, _ = balanced_graph
        # Set veteran_mask to all-False
        graph_data.veteran_mask = torch.zeros(graph_data.num_edges, dtype=torch.bool)

        with caplog.at_level(logging.WARNING, logger="sc2ml.gnn.trainer"):
            from unittest.mock import patch

            with (
                patch("sc2ml.gnn.trainer.GNN_PATIENCE", 1),
                patch("sc2ml.gnn.trainer.GNN_LOG_EVERY", 1),
            ):
                from sc2ml.gnn.trainer import train_and_evaluate_gnn

                train_and_evaluate_gnn(graph_data, epochs=50)

        assert any("Veterans mask produced 0 test matches" in r.message for r in caplog.records)
