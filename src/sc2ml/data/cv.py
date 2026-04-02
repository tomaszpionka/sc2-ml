"""Expanding-window temporal cross-validation with series-aware boundaries.

Implements the temporal CV protocol from methodology Section 4.2:

    Fold 1: Train [months 1-12]  -> Val [months 13-15]
    Fold 2: Train [months 1-15]  -> Val [months 16-18]
    Fold 3: Train [months 1-18]  -> Val [months 19-21]

Unlike sklearn's TimeSeriesSplit, this:
1. Grows the training window from a configurable minimum size
2. Optionally snaps fold boundaries to series boundaries
3. Implements sklearn's BaseCrossValidator protocol
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from sc2ml.config import EXPANDING_CV_MIN_TRAIN_FRAC, EXPANDING_CV_N_SPLITS

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


class ExpandingWindowCV:
    """Expanding-window temporal cross-validation.

    Assumes the data is already sorted by time. Produces ``n_splits``
    (train, val) index pairs where the training window grows monotonically
    and the validation window slides forward.

    Parameters
    ----------
    n_splits : int
        Number of CV folds.
    min_train_frac : float
        Minimum fraction of data used for the first training window.
    series_ids : array-like or None
        If provided, fold boundaries are snapped so that no series is
        split across train and validation.
    """

    def __init__(
        self,
        n_splits: int = EXPANDING_CV_N_SPLITS,
        min_train_frac: float = EXPANDING_CV_MIN_TRAIN_FRAC,
        series_ids: np.ndarray | None = None,
    ) -> None:
        if min_train_frac <= 0 or min_train_frac >= 1:
            raise ValueError("min_train_frac must be in (0, 1)")
        if n_splits < 2:
            raise ValueError("n_splits must be >= 2")

        self.n_splits = n_splits
        self.min_train_frac = min_train_frac
        self.series_ids = series_ids

    def _snap_to_series_boundary(self, idx: int, n: int) -> int:
        """Snap an index forward to the next series boundary.

        A series boundary is where series_ids[i] != series_ids[i-1].
        """
        if self.series_ids is None or idx >= n - 1:
            return idx

        # Move forward until we hit a new series
        while idx < n - 1 and self.series_ids[idx] == self.series_ids[idx - 1]:
            idx += 1
        return idx

    def split(
        self,
        X: np.ndarray | None = None,
        y: np.ndarray | None = None,
        groups: np.ndarray | None = None,
    ) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        """Yield (train_indices, val_indices) tuples.

        Parameters
        ----------
        X : array-like with shape (n_samples, ...)
            Used only to determine ``n_samples``.
        y, groups : ignored (present for sklearn compatibility)
        """
        if X is None:
            raise ValueError("X must be provided to determine n_samples")

        n = len(X)
        min_train = int(n * self.min_train_frac)
        remaining = n - min_train
        val_size = remaining // self.n_splits

        if val_size < 1:
            raise ValueError(
                f"Not enough data for {self.n_splits} splits with "
                f"min_train_frac={self.min_train_frac}. "
                f"n={n}, min_train={min_train}, remaining={remaining}"
            )

        for fold in range(self.n_splits):
            train_end = min_train + fold * val_size
            val_end = train_end + val_size

            # Snap boundaries to series boundaries if series_ids provided
            train_end = self._snap_to_series_boundary(train_end, n)
            val_end = self._snap_to_series_boundary(val_end, n)

            # Ensure val_end doesn't exceed n
            val_end = min(val_end, n)

            # Ensure non-empty sets
            if train_end >= val_end:
                continue

            train_idx = np.arange(train_end)
            val_idx = np.arange(train_end, val_end)

            yield train_idx, val_idx

    def get_n_splits(
        self,
        X: np.ndarray | None = None,
        y: np.ndarray | None = None,
        groups: np.ndarray | None = None,
    ) -> int:
        """Return the number of splitting iterations."""
        return self.n_splits
