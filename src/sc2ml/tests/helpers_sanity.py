"""Isolated worker for LightGBM-based sanity validation checks.

This module intentionally does NOT import torch or PyTorch Geometric
so it can be spawned via ``multiprocessing`` without loading a second
``libomp.dylib`` that conflicts with LightGBM's Homebrew OpenMP.

Same isolation pattern as ``helpers_classical.py``.
"""

import warnings


def lgbm_sanity_worker(
    check_name: str,
    X_train_dict: dict,
    X_test_dict: dict,
    y_train_list: list,
    y_test_list: list,
    matchup_col_list: list | None,
    result_queue,
) -> None:
    """Run a LightGBM-based sanity check in an isolated process.

    Data is passed as dicts/lists (pickle-safe) and reconstructed as DataFrames.
    """
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    import pandas as pd

    X_train = pd.DataFrame(X_train_dict)
    X_test = pd.DataFrame(X_test_dict)
    y_train = pd.Series(y_train_list, name="target")
    y_test = pd.Series(y_test_list, name="target")
    matchup_col = pd.Series(matchup_col_list) if matchup_col_list is not None else None

    from sc2ml.validation import (
        check_lgbm_accuracy_range,
        check_lgbm_top_features,
        check_no_matchup_above_threshold,
        check_train_test_accuracy_gap,
    )

    check_fn = {
        "lgbm_accuracy_range": lambda: check_lgbm_accuracy_range(
            X_train, X_test, y_train, y_test
        ),
        "no_matchup_above_threshold": lambda: check_no_matchup_above_threshold(
            X_train, X_test, y_train, y_test, matchup_col
        ),
        "lgbm_top_features": lambda: check_lgbm_top_features(X_train, y_train),
        "train_test_accuracy_gap": lambda: check_train_test_accuracy_gap(
            X_train, X_test, y_train, y_test
        ),
    }

    check = check_fn[check_name]()
    result_queue.put({
        "passed": check.passed,
        "detail": check.detail,
        "name": check.name,
    })
