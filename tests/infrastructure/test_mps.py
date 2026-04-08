"""MPS (Apple Silicon GPU) smoke tests.

All tests are skipped when MPS is not available. Use ``pytest -m mps`` to
select only these tests, or ``-m 'not mps'`` to exclude them.
"""
import gc
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor

import pytest
import torch
import torch.nn as nn
import torch.nn.functional as F

_mps_available = torch.backends.mps.is_available()
pytestmark = [
    pytest.mark.mps,
    pytest.mark.skipif(not _mps_available, reason="MPS not available"),
]


@pytest.fixture(autouse=True)
def _mps_cleanup() -> Generator[None, None, None]:
    """Flush MPS caches after each test to prevent shutdown segfaults."""
    yield
    gc.collect()
    if _mps_available:
        torch.mps.empty_cache()


@pytest.fixture()
def device() -> torch.device:
    return torch.device("mps")


def test_mps_smoke_matmul(device: torch.device) -> None:
    """Matmul + synchronize — targets crash-on-exit class."""
    a = torch.randn(512, 512, device=device)
    b = torch.randn(512, 512, device=device)
    c = a @ b
    torch.mps.synchronize()
    assert torch.isfinite(c).all().item()


def test_mps_autograd_cpu_vs_mps(device: torch.device) -> None:
    """Gradient comparison between CPU and MPS backends."""
    torch.manual_seed(0)
    x_cpu = torch.randn(128, 64, requires_grad=True)
    w_cpu = torch.randn(64, 32, requires_grad=True)

    def f(x: torch.Tensor, w: torch.Tensor) -> torch.Tensor:
        return ((x @ w).tanh() ** 2).mean()

    loss_cpu = f(x_cpu, w_cpu)
    loss_cpu.backward()
    assert x_cpu.grad is not None
    assert w_cpu.grad is not None
    gx_cpu = x_cpu.grad.detach().clone()
    gw_cpu = w_cpu.grad.detach().clone()

    x_mps = x_cpu.detach().to(device).requires_grad_(True)
    w_mps = w_cpu.detach().to(device).requires_grad_(True)
    loss_mps = f(x_mps, w_mps)
    loss_mps.backward()
    torch.mps.synchronize()

    assert x_mps.grad is not None
    assert w_mps.grad is not None
    gx_mps = x_mps.grad.detach().cpu()
    gw_mps = w_mps.grad.detach().cpu()

    assert torch.allclose(gx_cpu, gx_mps, rtol=1e-3, atol=1e-4), "grad x mismatch"
    assert torch.allclose(gw_cpu, gw_mps, rtol=1e-3, atol=1e-4), "grad w mismatch"


def test_mps_tiny_training_loop(device: torch.device) -> None:
    """Training converges — loss decreases over 300 steps."""
    torch.manual_seed(0)

    class TinyMLP(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.l1 = nn.Linear(64, 128)
            self.l2 = nn.Linear(128, 10)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.l2(F.gelu(self.l1(x)))

    model = TinyMLP().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)

    x = torch.randn(256, 64, device=device)
    y = torch.randint(0, 10, (256,), device=device)

    first_loss = None
    final_loss = None
    steps = 300

    for i in range(steps):
        opt.zero_grad(set_to_none=True)
        logits = model(x)
        loss = F.cross_entropy(logits, y)
        assert torch.isfinite(loss).item(), f"non-finite loss at step {i}"
        loss.backward()
        opt.step()

        current = float(loss.detach().cpu())
        if i == 0:
            first_loss = current
        final_loss = current

    assert first_loss is not None and final_loss is not None
    assert final_loss < first_loss, (
        f"Training did not converge: first={first_loss:.4f}, final={final_loss:.4f}"
    )


def test_mps_threaded_stress(device: torch.device) -> None:
    """Concurrent matmul stability across threads."""
    workers = 4
    iters = 20

    def worker(seed: int) -> bool:
        torch.manual_seed(seed)
        for _ in range(iters):
            a = torch.randn(256, 256, device=device)
            b = torch.randn(256, 256, device=device)
            _ = (a @ b).sum()
        return True

    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(worker, range(100, 100 + workers)))

    torch.mps.synchronize()
    assert all(results)


def test_mps_threaded_stress_with_sync(device: torch.device) -> None:
    """Sequential matmul with per-op sync — targets crash-on-exit class."""
    workers = 4
    iters = 20

    for seed in range(100, 100 + workers):
        torch.manual_seed(seed)
        for _ in range(iters):
            a = torch.randn(256, 256, device=device)
            b = torch.randn(256, 256, device=device)
            out = (a @ b).sum()
            torch.mps.synchronize()
            _ = float(out.detach().cpu())
            assert torch.isfinite(out).item(), (
                f"non-finite result in threaded stress with sync for seed {seed}"
            )
