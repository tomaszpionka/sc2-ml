"""Tests for model reproducibility with fixed random seed.

Covers:
- Classical ML models produce identical predictions across two runs with seed=42
- GNN training produces identical best accuracy across two runs with seed=42

**macOS note:** LightGBM (via Homebrew libomp) and PyTorch ship separate
OpenMP runtimes.  Loading both in the same process causes a segfault at
shutdown.  Classical model tests therefore run in a child process via
``multiprocessing`` to isolate the two runtimes — the same approach used
in ``test_mps.py`` for Metal/MPS isolation.

The worker function lives in ``tests/helpers_classical.py`` (which does
NOT import torch) so that the spawned child never loads PyTorch's libomp.
"""

import gc
import multiprocessing
import warnings

import pytest
import torch

from sc2ml.features import perform_feature_engineering
from sc2ml.gnn.pipeline import build_starcraft_graph
from sc2ml.gnn.trainer import train_and_evaluate_gnn
from tests.helpers import make_matches_df

# ---------------------------------------------------------------------------
# Classical model tests — run in a child process to avoid libomp clash
# ---------------------------------------------------------------------------


def _run_classical_repro_check(model_name: str) -> None:
    """Spawn a child process for *model_name* and assert determinism."""
    from tests.helpers_classical import classical_repro_worker

    ctx = multiprocessing.get_context("spawn")
    q = ctx.Queue()
    proc = ctx.Process(target=classical_repro_worker, args=(model_name, q))
    proc.start()
    proc.join(timeout=120)

    if proc.exitcode != 0:
        pytest.fail(
            f"Child process for {model_name} crashed (exit code {proc.exitcode}). "
            "Likely an OpenMP/libomp conflict — check LightGBM and PyTorch versions."
        )

    result = q.get_nowait()
    assert result["match"], (
        f"{model_name} predictions differ between runs: "
        f"head_run1={result['preds1_head']}, head_run2={result['preds2_head']}"
    )


def test_logistic_regression_is_deterministic() -> None:
    _run_classical_repro_check("Logistic Regression")


def test_random_forest_is_deterministic() -> None:
    _run_classical_repro_check("Random Forest")


# ---------------------------------------------------------------------------
# GNN test — runs in-process (torch-only, no LightGBM)
# ---------------------------------------------------------------------------


def test_gnn_training_is_deterministic() -> None:
    """GNN training with the same seed should produce same best accuracy."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    torch.manual_seed(42)
    raw = make_matches_df(n=200, seed=42)
    features_df = perform_feature_engineering(raw)
    graph_data, _ = build_starcraft_graph(features_df, test_size=0.1)

    torch.manual_seed(42)
    _, acc1 = train_and_evaluate_gnn(graph_data, epochs=20, test_size=0.1)

    torch.manual_seed(42)
    _, acc2 = train_and_evaluate_gnn(graph_data, epochs=20, test_size=0.1)

    assert acc1 == acc2, (
        f"GNN training is not deterministic: run1={acc1:.4f}, run2={acc2:.4f}. "
        "Check that torch.manual_seed(42) is set before each call."
    )

    # MPS cleanup to prevent shutdown segfault (same pattern as tests/test_mps.py)
    gc.collect()
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
