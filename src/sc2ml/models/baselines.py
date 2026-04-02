"""Baseline classifiers for pre-match prediction (methodology Section 5.2).

Three baselines that establish the floor for model comparison:
- MajorityClassBaseline: always predicts the majority class
- EloOnlyBaseline: uses expected_win_prob > 0.5
- EloLRBaseline: Logistic Regression on elo_diff only

All implement fit/predict/predict_proba for compatibility with the
evaluation module.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from sc2ml.config import RANDOM_SEED

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


class MajorityClassBaseline:
    """Always predicts the majority class from training data.

    ``predict_proba`` returns the training majority fraction for every sample,
    enabling Brier score and log loss computation.
    """

    def __init__(self) -> None:
        self.majority_class_: int = 1
        self.majority_frac_: float = 0.5

    def fit(self, X: pd.DataFrame, y: pd.Series) -> MajorityClassBaseline:
        y_arr = np.asarray(y)
        self.majority_frac_ = float(np.mean(y_arr))
        self.majority_class_ = int(self.majority_frac_ >= 0.5)
        logger.info(
            f"MajorityClassBaseline: majority_class={self.majority_class_}, "
            f"fraction={self.majority_frac_:.4f}"
        )
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.full(len(X), self.majority_class_, dtype=int)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        p = self.majority_frac_
        return np.column_stack([np.full(len(X), 1 - p), np.full(len(X), p)])


class EloOnlyBaseline:
    """Predicts p1 wins if ``expected_win_prob > 0.5``.

    Uses the Elo expected win probability directly as the predicted
    probability -- no model fitting required.
    """

    def __init__(self, prob_col: str = "expected_win_prob") -> None:
        self.prob_col = prob_col

    def fit(self, X: pd.DataFrame, y: pd.Series) -> EloOnlyBaseline:
        if self.prob_col not in X.columns:
            raise ValueError(
                f"Column '{self.prob_col}' not found in X. "
                f"Available: {list(X.columns)}"
            )
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return (X[self.prob_col].values >= 0.5).astype(int)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        p = X[self.prob_col].values.astype(float)
        return np.column_stack([1 - p, p])


class EloLRBaseline:
    """Logistic Regression on ``elo_diff`` only.

    Minimal statistical model -- isolates the predictive power of the
    Elo rating difference without any other features.
    """

    def __init__(
        self,
        diff_col: str = "elo_diff",
        seed: int = RANDOM_SEED,
    ) -> None:
        self.diff_col = diff_col
        self.scaler_ = StandardScaler()
        self.model_ = LogisticRegression(
            max_iter=1000,
            random_state=seed,
        )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> EloLRBaseline:
        if self.diff_col not in X.columns:
            raise ValueError(
                f"Column '{self.diff_col}' not found in X. "
                f"Available: {list(X.columns)}"
            )
        x = X[[self.diff_col]].values
        x_scaled = self.scaler_.fit_transform(x)
        self.model_.fit(x_scaled, y)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        x = X[[self.diff_col]].values
        x_scaled = self.scaler_.transform(x)
        return self.model_.predict(x_scaled)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        x = X[[self.diff_col]].values
        x_scaled = self.scaler_.transform(x)
        return self.model_.predict_proba(x_scaled)


def build_baselines() -> dict[str, MajorityClassBaseline | EloOnlyBaseline | EloLRBaseline]:
    """Return dict of named baseline instances (unfitted)."""
    return {
        "Majority Class": MajorityClassBaseline(),
        "Elo Only": EloOnlyBaseline(),
        "LR (Elo diff)": EloLRBaseline(),
    }
