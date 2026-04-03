"""Subprocess workers for evaluation tests that use LightGBM.

This module intentionally does NOT import torch or PyTorch Geometric
so it can be spawned via ``multiprocessing`` without loading a second
``libomp.dylib`` that conflicts with LightGBM's Homebrew OpenMP.
"""

import warnings


def _make_raw_df_with_split(n: int = 200, seed: int = 42):
    """Create a synthetic raw DataFrame with a split column for ablation/drift tests."""
    from tests.helpers import make_matches_df

    df = make_matches_df(n=n, seed=seed)

    # Add split column (80/15/5 split)
    n_train = int(n * 0.80)
    n_val = int(n * 0.15)
    splits = ["train"] * n_train + ["val"] * n_val + ["test"] * (n - n_train - n_val)
    df["split"] = splits

    return df


def worker_feature_ablation(result_queue) -> None:
    """Run feature ablation with small synthetic data."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)

    from sc2ml.models.evaluation import run_feature_ablation

    raw_df = _make_raw_df_with_split(n=200)
    results = run_feature_ablation(raw_df, compute_ci=False)

    result_queue.put({
        "n_steps": len(results),
        "groups": [r["group"] for r in results],
        "has_metrics": all("metrics" in r for r in results),
        "has_lift": all("lift" in r for r in results),
        "first_lift_empty": results[0]["lift"] == {} if results else True,
    })


def worker_patch_drift(result_queue) -> None:
    """Run patch drift experiment with synthetic data."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)

    from sc2ml.models.evaluation import run_patch_drift_experiment

    raw_df = _make_raw_df_with_split(n=300)

    result = run_patch_drift_experiment(raw_df, compute_ci=False)

    result_queue.put({
        "has_old_to_new": "old_to_new" in result,
        "has_mixed": "mixed_model" in result,
        "has_per_patch": "per_patch" in result,
        "old_to_new_acc": result["old_to_new"].accuracy,
        "mixed_acc": result["mixed_model"].accuracy,
        "n_old_patches": result["n_old_patches"],
        "n_new_patches": result["n_new_patches"],
    })


def worker_patch_drift_no_column(result_queue) -> None:
    """Patch drift with no patch column should raise ValueError."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)

    from sc2ml.models.evaluation import run_patch_drift_experiment

    raw_df = _make_raw_df_with_split(n=200)
    # Remove both patch columns before feature engineering
    raw_df = raw_df.drop(columns=["data_build", "game_version"])

    try:
        run_patch_drift_experiment(raw_df, compute_ci=False)
        result_queue.put({"raised": False, "error": ""})
    except ValueError as e:
        result_queue.put({"raised": True, "error": str(e)})
    except Exception as e:
        result_queue.put({"raised": False, "error": f"Wrong exception: {type(e).__name__}: {e}"})
