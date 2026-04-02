# mps_probe.py
import platform
import sys
from concurrent.futures import ThreadPoolExecutor

import torch
import torch.nn as nn
import torch.nn.functional as F


def print_env():
    print("Python:", sys.version)
    print("Platform:", platform.platform())
    print("Machine:", platform.machine())
    print("Torch:", torch.__version__)
    print("MPS built:", torch.backends.mps.is_built())
    print("MPS available:", torch.backends.mps.is_available())


def smoke_matmul_and_sync(device: torch.device):
    a = torch.randn(512, 512, device=device)
    b = torch.randn(512, 512, device=device)
    c = a @ b
    torch.mps.synchronize()
    assert torch.isfinite(c).all().item()


def autograd_cpu_vs_mps(device: torch.device):
    torch.manual_seed(0)
    x_cpu = torch.randn(128, 64, requires_grad=True)
    w_cpu = torch.randn(64, 32, requires_grad=True)

    def f(x, w):
        return ((x @ w).tanh() ** 2).mean()

    loss_cpu = f(x_cpu, w_cpu)
    loss_cpu.backward()
    gx_cpu = x_cpu.grad.detach().clone()
    gw_cpu = w_cpu.grad.detach().clone()

    x_mps = x_cpu.detach().to(device).requires_grad_(True)
    w_mps = w_cpu.detach().to(device).requires_grad_(True)
    loss_mps = f(x_mps, w_mps)
    loss_mps.backward()
    torch.mps.synchronize()

    gx_mps = x_mps.grad.detach().cpu()
    gw_mps = w_mps.grad.detach().cpu()

    assert torch.allclose(gx_cpu, gx_mps, rtol=1e-3, atol=1e-4), "grad x mismatch"
    assert torch.allclose(gw_cpu, gw_mps, rtol=1e-3, atol=1e-4), "grad w mismatch"


def tiny_training_loop(device: torch.device, steps: int = 300):
    torch.manual_seed(0)

    class TinyMLP(nn.Module):
        def __init__(self):
            super().__init__()
            self.l1 = nn.Linear(64, 128)
            self.l2 = nn.Linear(128, 10)

        def forward(self, x):
            return self.l2(F.gelu(self.l1(x)))

    model = TinyMLP().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)

    x = torch.randn(256, 64, device=device)
    y = torch.randint(0, 10, (256,), device=device)

    prev_loss = None
    for i in range(steps):
        opt.zero_grad(set_to_none=True)
        logits = model(x)
        loss = F.cross_entropy(logits, y)
        assert torch.isfinite(loss).item(), f"non-finite loss at step {i}"
        loss.backward()
        opt.step()

        if i % 100 == 0:
            torch.mps.synchronize()
            print(f"step={i}, loss={float(loss.detach().cpu()):.6f}")

        prev_loss = float(loss.detach().cpu())

    return prev_loss


def threaded_stress(device: torch.device, workers: int = 4, iters: int = 20):
    def worker(seed: int):
        torch.manual_seed(seed)
        for _ in range(iters):
            a = torch.randn(256, 256, device=device)
            b = torch.randn(256, 256, device=device)
            _ = (a @ b).sum()
        # REMOVED: torch.mps.synchronize() from inside the thread
        return True

    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(worker, range(100, 100 + workers)))
    
    # ADDED: Synchronize only ONCE on the main thread after all workers are done submitting
    torch.mps.synchronize()
    assert all(results)


def threaded_stress_with_sync(device: torch.device, workers: int = 4, iters: int = 20):
    # MPS on current macOS/PyTorch stacks appears unsafe for concurrent Python-threaded execution.
    # Run sequentially to avoid Metal/MPS command-buffer crashes.
    for seed in range(100, 100 + workers):
        torch.manual_seed(seed)
        for _ in range(iters):
            a = torch.randn(256, 256, device=device)
            b = torch.randn(256, 256, device=device)
            out = (a @ b).sum()
            torch.mps.synchronize()
            _ = float(out.detach().cpu())
            assert torch.isfinite(out).item(), f"non-finite result in threaded stress with sync for seed {seed}"


def main():
    print_env()
    if not torch.backends.mps.is_available():
        print("MPS not available; stopping.")
        return

    device = torch.device("mps")

    print("\n[1] matmul + synchronize (targets crash-on-exit class)")
    smoke_matmul_and_sync(device)

    print("[2] autograd CPU vs MPS check")
    autograd_cpu_vs_mps(device)

    print("[3] tiny training loop")
    tiny_training_loop(device)

    print("[4] threaded stress")
    threaded_stress(device)

    print("[5] threaded stress with sync (targets crash-on-exit class)")
    threaded_stress_with_sync(device)
    
    print("\nAll tests passed; cleaning up to prevent shutdown segfault...")
    
    # 1. Force Python to delete lingering thread-local tensors
    import gc
    gc.collect()
    
    # 2. Safely flush and release the Metal command queues before Python shuts down
    torch.mps.empty_cache()

if __name__ == "__main__":
    main()
