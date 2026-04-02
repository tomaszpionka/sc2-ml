"""Error analysis across match subgroups (methodology Section 8.2).

Identifies where models fail by breaking down predictions across:
- Mirror matchups (TvT, PvP, ZvZ)
- Upsets (lower-Elo player wins)
- Close Elo games (diff < 50)
- Short games (<8 min)
- Long games (>20 min)
- Patch transitions
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)

# SC2 runs at ~22.4 game loops per second
_LOOPS_PER_SECOND = 22.4
_SHORT_GAME_THRESHOLD = 8 * 60 * _LOOPS_PER_SECOND   # 8 minutes
_LONG_GAME_THRESHOLD = 20 * 60 * _LOOPS_PER_SECOND    # 20 minutes
_CLOSE_ELO_THRESHOLD = 50


def classify_error_subgroups(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    matchup_col: "pd.Series | None" = None,
    elo_diff: np.ndarray | None = None,
    game_loops: np.ndarray | None = None,
) -> dict[str, dict[str, np.ndarray]]:
    """Categorize predictions into error subgroups.

    Parameters
    ----------
    y_true, y_pred, y_prob : arrays of true labels, predictions, and probs
    matchup_col : Series of canonical matchup types (e.g. "PvT")
    elo_diff : array of Elo differences (p1 - p2)
    game_loops : array of game lengths in game loops (from raw data)

    Returns
    -------
    dict mapping subgroup name to dict with keys:
    'y_true', 'y_pred', 'y_prob', 'mask'
    """
    n = len(y_true)
    subgroups: dict[str, dict[str, np.ndarray]] = {}

    # All test set (reference)
    subgroups["all"] = {
        "y_true": y_true,
        "y_pred": y_pred,
        "y_prob": y_prob,
        "mask": np.ones(n, dtype=bool),
    }

    # Mirror matchups
    if matchup_col is not None:
        mirrors = {"PvP", "TvT", "ZvZ"}
        mirror_mask = np.array([m in mirrors for m in matchup_col])
        if mirror_mask.sum() > 0:
            subgroups["mirrors"] = {
                "y_true": y_true[mirror_mask],
                "y_pred": y_pred[mirror_mask],
                "y_prob": y_prob[mirror_mask],
                "mask": mirror_mask,
            }

        # Non-mirror (cross-race)
        non_mirror_mask = ~mirror_mask
        if non_mirror_mask.sum() > 0:
            subgroups["cross_race"] = {
                "y_true": y_true[non_mirror_mask],
                "y_pred": y_pred[non_mirror_mask],
                "y_prob": y_prob[non_mirror_mask],
                "mask": non_mirror_mask,
            }

    # Elo-based subgroups
    if elo_diff is not None:
        elo = np.asarray(elo_diff)

        # Upsets: lower-Elo player won
        # If elo_diff > 0, p1 is favored; upset = p2 wins (y_true=0)
        # If elo_diff < 0, p2 is favored; upset = p1 wins (y_true=1)
        upset_mask = ((elo > 0) & (y_true == 0)) | ((elo < 0) & (y_true == 1))
        if upset_mask.sum() > 0:
            subgroups["upsets"] = {
                "y_true": y_true[upset_mask],
                "y_pred": y_pred[upset_mask],
                "y_prob": y_prob[upset_mask],
                "mask": upset_mask,
            }

        # Close Elo
        close_mask = np.abs(elo) < _CLOSE_ELO_THRESHOLD
        if close_mask.sum() > 0:
            subgroups["close_elo"] = {
                "y_true": y_true[close_mask],
                "y_pred": y_pred[close_mask],
                "y_prob": y_prob[close_mask],
                "mask": close_mask,
            }

    # Game length subgroups
    if game_loops is not None:
        gl = np.asarray(game_loops)

        short_mask = gl < _SHORT_GAME_THRESHOLD
        if short_mask.sum() > 0:
            subgroups["short_games"] = {
                "y_true": y_true[short_mask],
                "y_pred": y_pred[short_mask],
                "y_prob": y_prob[short_mask],
                "mask": short_mask,
            }

        long_mask = gl > _LONG_GAME_THRESHOLD
        if long_mask.sum() > 0:
            subgroups["long_games"] = {
                "y_true": y_true[long_mask],
                "y_pred": y_pred[long_mask],
                "y_prob": y_prob[long_mask],
                "mask": long_mask,
            }

    return subgroups


def error_subgroup_report(
    subgroups: dict[str, dict[str, np.ndarray]],
) -> "pd.DataFrame":
    """Compute accuracy and AUC-ROC per subgroup.

    Returns DataFrame with columns: subgroup, n_samples, accuracy, auc_roc,
    error_rate
    """
    import pandas as pd

    rows = []
    for name, data in subgroups.items():
        yt = data["y_true"]
        yp = data["y_pred"]
        yprob = data["y_prob"]
        n = len(yt)

        acc = float(accuracy_score(yt, yp))

        # AUC requires both classes
        if len(np.unique(yt)) >= 2:
            auc = float(roc_auc_score(yt, yprob))
        else:
            auc = float("nan")

        rows.append({
            "subgroup": name,
            "n_samples": n,
            "accuracy": acc,
            "auc_roc": auc,
            "error_rate": 1.0 - acc,
        })

    return pd.DataFrame(rows)
