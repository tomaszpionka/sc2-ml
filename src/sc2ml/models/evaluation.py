"""Model evaluation infrastructure for classical ML models.

Provides comprehensive metrics (accuracy, AUC-ROC, Brier score, log loss),
bootstrap confidence intervals, calibration curves, and statistical
comparison tests (McNemar, DeLong) for thesis-quality model comparison.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

import numpy as np
from scipy import stats
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)

from sc2ml.config import (
    BOOTSTRAP_CI_LEVEL,
    BOOTSTRAP_N_ITER,
    CALIBRATION_N_BINS,
    RANDOM_SEED,
)

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class ModelResults:
    """Container for a single model's evaluation metrics."""

    model_name: str

    # Core metrics
    accuracy: float
    auc_roc: float
    brier_score: float
    log_loss_val: float  # 'log_loss' shadows the import

    # 95% confidence intervals (lo, hi)
    accuracy_ci: tuple[float, float] = (0.0, 0.0)
    auc_roc_ci: tuple[float, float] = (0.0, 0.0)
    brier_score_ci: tuple[float, float] = (0.0, 0.0)
    log_loss_ci: tuple[float, float] = (0.0, 0.0)

    # Raw predictions (for downstream comparison)
    y_true: np.ndarray = field(default_factory=lambda: np.array([]))
    y_pred: np.ndarray = field(default_factory=lambda: np.array([]))
    y_prob: np.ndarray = field(default_factory=lambda: np.array([]))

    # Per-matchup breakdown: matchup_type -> {metric_name: value}
    per_matchup: dict[str, dict[str, float]] = field(default_factory=dict)

    # Veterans-only metrics
    veterans: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Core metrics
# ---------------------------------------------------------------------------

def compute_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, float]:
    """Compute accuracy, AUC-ROC, Brier score, and log loss.

    Parameters
    ----------
    y_true : array of binary labels (0/1)
    y_prob : array of predicted probabilities for class 1
    threshold : decision threshold for accuracy
    """
    y_pred = (y_prob >= threshold).astype(int)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "auc_roc": float(roc_auc_score(y_true, y_prob)),
        "brier_score": float(brier_score_loss(y_true, y_prob)),
        "log_loss": float(log_loss(y_true, y_prob)),
    }


# ---------------------------------------------------------------------------
# Bootstrap confidence intervals
# ---------------------------------------------------------------------------

def bootstrap_ci(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    metric_fn: Callable[[np.ndarray, np.ndarray], float],
    n_iterations: int = BOOTSTRAP_N_ITER,
    ci_level: float = BOOTSTRAP_CI_LEVEL,
    seed: int = RANDOM_SEED,
) -> tuple[float, float]:
    """95% confidence interval via bootstrap resampling.

    Parameters
    ----------
    metric_fn : callable(y_true, y_prob) -> float
    """
    rng = np.random.default_rng(seed)
    n = len(y_true)
    scores = np.empty(n_iterations)

    for i in range(n_iterations):
        idx = rng.integers(0, n, size=n)
        y_t = y_true[idx]
        y_p = y_prob[idx]
        # Skip degenerate bootstrap samples (single class)
        if len(np.unique(y_t)) < 2:
            scores[i] = np.nan
        else:
            scores[i] = metric_fn(y_t, y_p)

    scores = scores[~np.isnan(scores)]
    alpha = 1 - ci_level
    lo = float(np.percentile(scores, 100 * alpha / 2))
    hi = float(np.percentile(scores, 100 * (1 - alpha / 2)))
    return (lo, hi)


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------

def calibration_curve_data(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = CALIBRATION_N_BINS,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (fraction_of_positives, mean_predicted_value) per bin.

    Wraps sklearn's ``calibration_curve`` with strategy='uniform'.
    """
    fraction_pos, mean_pred = calibration_curve(
        y_true, y_prob, n_bins=n_bins, strategy="uniform"
    )
    return fraction_pos, mean_pred


# ---------------------------------------------------------------------------
# Statistical comparison tests
# ---------------------------------------------------------------------------

def mcnemar_test(
    y_true: np.ndarray,
    y_pred_a: np.ndarray,
    y_pred_b: np.ndarray,
) -> dict[str, Any]:
    """McNemar's test for paired nominal data.

    Compares whether two models make different types of errors.
    Uses exact binomial test when the number of discordant pairs < 25.

    Returns
    -------
    dict with keys: statistic, p_value, n_discordant, method
    """
    correct_a = (y_pred_a == y_true)
    correct_b = (y_pred_b == y_true)

    # b01: A wrong, B right
    b01 = int(np.sum(~correct_a & correct_b))
    # b10: A right, B wrong
    b10 = int(np.sum(correct_a & ~correct_b))

    n_discordant = b01 + b10

    if n_discordant == 0:
        return {
            "statistic": 0,
            "p_value": 1.0,
            "n_discordant": 0,
            "b01": 0,
            "b10": 0,
            "method": "no_discordant",
        }

    if n_discordant < 25:
        # Exact binomial test (two-sided)
        p_value = float(stats.binomtest(b01, n_discordant, 0.5).pvalue)
        return {
            "statistic": b01,
            "p_value": p_value,
            "n_discordant": n_discordant,
            "b01": b01,
            "b10": b10,
            "method": "exact_binomial",
        }
    else:
        # Chi-squared approximation with continuity correction
        statistic = (abs(b01 - b10) - 1) ** 2 / (b01 + b10)
        p_value = float(1 - stats.chi2.cdf(statistic, df=1))
        return {
            "statistic": float(statistic),
            "p_value": p_value,
            "n_discordant": n_discordant,
            "b01": b01,
            "b10": b10,
            "method": "chi_squared",
        }


def delong_test(
    y_true: np.ndarray,
    y_prob_a: np.ndarray,
    y_prob_b: np.ndarray,
) -> dict[str, float]:
    """DeLong's test for comparing two AUC-ROC values.

    Implements the fast O(n log n) algorithm from Sun & Xu (2014).

    Returns
    -------
    dict with keys: z_stat, p_value, auc_a, auc_b, auc_diff
    """
    y_true = np.asarray(y_true, dtype=int)
    y_prob_a = np.asarray(y_prob_a, dtype=float)
    y_prob_b = np.asarray(y_prob_b, dtype=float)

    pos = np.where(y_true == 1)[0]
    neg = np.where(y_true == 0)[0]
    m = len(pos)
    n = len(neg)

    if m == 0 or n == 0:
        return {
            "z_stat": 0.0,
            "p_value": 1.0,
            "auc_a": 0.5,
            "auc_b": 0.5,
            "auc_diff": 0.0,
        }

    # Compute structural components for each model
    def _placement_values(y_prob: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Compute placement values V10 (for positives) and V01 (for negatives)."""
        scores_pos = y_prob[pos]
        scores_neg = y_prob[neg]

        # V10[i] = fraction of negatives with score < scores_pos[i]
        #        + 0.5 * fraction of negatives with score == scores_pos[i]
        v10 = np.empty(m)
        for i in range(m):
            v10[i] = (np.sum(scores_neg < scores_pos[i])
                       + 0.5 * np.sum(scores_neg == scores_pos[i])) / n

        # V01[j] = fraction of positives with score > scores_neg[j]
        #        + 0.5 * fraction of positives with score == scores_neg[j]
        v01 = np.empty(n)
        for j in range(n):
            v01[j] = (np.sum(scores_pos > scores_neg[j])
                       + 0.5 * np.sum(scores_pos == scores_neg[j])) / m

        return v10, v01

    v10_a, v01_a = _placement_values(y_prob_a)
    v10_b, v01_b = _placement_values(y_prob_b)

    auc_a = float(np.mean(v10_a))
    auc_b = float(np.mean(v10_b))

    # Covariance matrix of (AUC_a, AUC_b)
    # S10 = cov matrix from positive class placement values
    s10 = np.cov(np.stack([v10_a, v10_b]))
    # S01 = cov matrix from negative class placement values
    s01 = np.cov(np.stack([v01_a, v01_b]))

    # Handle scalar return from np.cov when m=1 or n=1
    if s10.ndim == 0:
        s10 = np.array([[float(s10), 0.0], [0.0, float(s10)]])
    if s01.ndim == 0:
        s01 = np.array([[float(s01), 0.0], [0.0, float(s01)]])

    s = s10 / m + s01 / n

    # Variance of AUC_a - AUC_b
    var_diff = s[0, 0] + s[1, 1] - 2 * s[0, 1]

    if var_diff <= 0:
        return {
            "z_stat": 0.0,
            "p_value": 1.0,
            "auc_a": auc_a,
            "auc_b": auc_b,
            "auc_diff": auc_a - auc_b,
        }

    z_stat = (auc_a - auc_b) / np.sqrt(var_diff)
    p_value = float(2 * stats.norm.sf(abs(z_stat)))  # two-sided

    return {
        "z_stat": float(z_stat),
        "p_value": p_value,
        "auc_a": auc_a,
        "auc_b": auc_b,
        "auc_diff": auc_a - auc_b,
    }


# ---------------------------------------------------------------------------
# Per-matchup evaluation
# ---------------------------------------------------------------------------

def _compute_per_matchup(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    matchup_col: "pd.Series",
) -> dict[str, dict[str, float]]:
    """Compute metrics per matchup type (TvZ, PvT, etc.)."""
    results: dict[str, dict[str, float]] = {}
    for matchup in sorted(matchup_col.unique()):
        mask = matchup_col == matchup
        yt = y_true[mask]
        yp = y_prob[mask]
        if len(yt) < 2 or len(np.unique(yt)) < 2:
            continue
        metrics = compute_metrics(yt, yp)
        metrics["n_samples"] = int(mask.sum())
        results[matchup] = metrics
    return results


# ---------------------------------------------------------------------------
# High-level evaluation
# ---------------------------------------------------------------------------

def evaluate_model(
    model: Any,
    X_test: "pd.DataFrame",
    y_test: "pd.Series",
    model_name: str,
    matchup_col: "pd.Series | None" = None,
    veterans_mask: "pd.Series | None" = None,
    compute_ci: bool = True,
) -> ModelResults:
    """Full evaluation of a single model with all metrics, CIs, and breakdowns.

    Parameters
    ----------
    model : fitted sklearn-compatible estimator with predict_proba
    X_test, y_test : test data
    model_name : human-readable model name
    matchup_col : Series of matchup types (e.g. "PvT") aligned with X_test
    veterans_mask : boolean Series indicating veteran matches
    compute_ci : whether to compute bootstrap CIs (slow)
    """
    y_true = np.asarray(y_test)

    # Get probability predictions
    y_prob_raw = model.predict_proba(X_test)
    # Handle both 1D (custom baselines) and 2D (sklearn) output
    if y_prob_raw.ndim == 2:
        y_prob = y_prob_raw[:, 1]
    else:
        y_prob = np.asarray(y_prob_raw)

    y_pred = (y_prob >= 0.5).astype(int)

    # Core metrics
    metrics = compute_metrics(y_true, y_prob)

    # Bootstrap CIs
    if compute_ci:
        acc_ci = bootstrap_ci(
            y_true, y_prob,
            lambda yt, yp: float(accuracy_score(yt, (yp >= 0.5).astype(int))),
        )
        auc_ci = bootstrap_ci(y_true, y_prob, roc_auc_score)
        brier_ci = bootstrap_ci(y_true, y_prob, brier_score_loss)
        ll_ci = bootstrap_ci(y_true, y_prob, log_loss)
    else:
        acc_ci = auc_ci = brier_ci = ll_ci = (0.0, 0.0)

    # Per-matchup breakdown
    per_matchup: dict[str, dict[str, float]] = {}
    if matchup_col is not None:
        per_matchup = _compute_per_matchup(y_true, y_prob, matchup_col)

    # Veterans-only metrics
    vets: dict[str, float] = {}
    if veterans_mask is not None:
        vm = np.asarray(veterans_mask)
        yt_v = y_true[vm]
        yp_v = y_prob[vm]
        if len(yt_v) >= 2 and len(np.unique(yt_v)) >= 2:
            vets = compute_metrics(yt_v, yp_v)
            vets["n_samples"] = int(vm.sum())

    result = ModelResults(
        model_name=model_name,
        accuracy=metrics["accuracy"],
        auc_roc=metrics["auc_roc"],
        brier_score=metrics["brier_score"],
        log_loss_val=metrics["log_loss"],
        accuracy_ci=acc_ci,
        auc_roc_ci=auc_ci,
        brier_score_ci=brier_ci,
        log_loss_ci=ll_ci,
        y_true=y_true,
        y_pred=y_pred,
        y_prob=y_prob,
        per_matchup=per_matchup,
        veterans=vets,
    )

    logger.info(
        f"{model_name}: acc={metrics['accuracy']:.4f} "
        f"[{acc_ci[0]:.4f}, {acc_ci[1]:.4f}], "
        f"AUC={metrics['auc_roc']:.4f}, "
        f"Brier={metrics['brier_score']:.4f}, "
        f"LogLoss={metrics['log_loss']:.4f}"
    )
    return result


def compare_models(
    results: list[ModelResults],
) -> "pd.DataFrame":
    """Pairwise McNemar and DeLong tests between all model pairs.

    Returns a DataFrame with columns:
    model_a, model_b, mcnemar_p, delong_p, auc_diff, acc_diff
    """
    import pandas as pd

    rows = []
    for i, ra in enumerate(results):
        for j, rb in enumerate(results):
            if j <= i:
                continue

            mc = mcnemar_test(ra.y_true, ra.y_pred, rb.y_pred)
            dl = delong_test(ra.y_true, ra.y_prob, rb.y_prob)

            rows.append({
                "model_a": ra.model_name,
                "model_b": rb.model_name,
                "acc_a": ra.accuracy,
                "acc_b": rb.accuracy,
                "acc_diff": ra.accuracy - rb.accuracy,
                "mcnemar_p": mc["p_value"],
                "mcnemar_method": mc["method"],
                "auc_a": dl["auc_a"],
                "auc_b": dl["auc_b"],
                "auc_diff": dl["auc_diff"],
                "delong_p": dl["p_value"],
            })

    return pd.DataFrame(rows)


def evaluate_all_models(
    trained_models: dict[str, Any],
    X_test: "pd.DataFrame",
    y_test: "pd.Series",
    matchup_col: "pd.Series | None" = None,
    veterans_mask: "pd.Series | None" = None,
    compute_ci: bool = True,
) -> tuple[list[ModelResults], "pd.DataFrame"]:
    """Evaluate all models and run pairwise comparisons.

    Returns
    -------
    (list of ModelResults, comparison DataFrame)
    """
    all_results = []
    for name, model in trained_models.items():
        result = evaluate_model(
            model, X_test, y_test, name,
            matchup_col=matchup_col,
            veterans_mask=veterans_mask,
            compute_ci=compute_ci,
        )
        all_results.append(result)

    comparisons = compare_models(all_results)
    return all_results, comparisons


# ---------------------------------------------------------------------------
# Feature ablation (methodology Section 7.1)
# ---------------------------------------------------------------------------

def run_feature_ablation(
    raw_df: "pd.DataFrame",
    series_df: "pd.DataFrame | None" = None,
    compute_ci: bool = True,
) -> list[dict[str, Any]]:
    """Run the incremental feature group ablation protocol.

    For each cumulative group (A, A+B, ..., A+B+C+D+E):
    1. ``build_features()`` with that group subset
    2. ``split_for_ml()``
    3. Train LightGBM with defaults
    4. ``evaluate_model()`` with full metrics
    5. Compute marginal lift from previous step

    Parameters
    ----------
    raw_df : DataFrame from ``get_matches_dataframe()`` (pre-feature-engineering)
    series_df : optional series assignment DataFrame for Group E

    Returns
    -------
    list of dicts with keys: group, groups_included, n_columns, metrics,
    lift (dict of metric deltas from previous step)
    """
    from lightgbm import LGBMClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    from sc2ml.config import HGB_LEARNING_RATE, RF_N_ESTIMATORS
    from sc2ml.features import FeatureGroup, build_features
    from sc2ml.features.common import split_for_ml

    results: list[dict[str, Any]] = []
    prev_metrics: dict[str, float] | None = None

    for group in FeatureGroup:
        logger.info(f"Ablation: training with groups up to {group.name}...")

        # Build features for this group subset
        feat_df = build_features(raw_df.copy(), groups=group, series_df=series_df)

        # Split
        X_train, X_val, X_test, y_train, y_val, y_test = split_for_ml(feat_df)

        # Train LightGBM with defaults
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LGBMClassifier(
                n_estimators=RF_N_ESTIMATORS,
                max_depth=6,
                learning_rate=HGB_LEARNING_RATE,
                random_state=RANDOM_SEED,
                verbose=-1,
            )),
        ])

        # Use val set for early stopping
        scaler = pipeline.named_steps["scaler"]
        clf = pipeline.named_steps["classifier"]
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        clf.fit(X_train_scaled, y_train, eval_set=[(X_val_scaled, y_val)])

        # Evaluate
        model_result = evaluate_model(
            pipeline, X_test, y_test,
            model_name=f"LightGBM (up to {group.name})",
            compute_ci=compute_ci,
        )

        metrics = {
            "accuracy": model_result.accuracy,
            "auc_roc": model_result.auc_roc,
            "brier_score": model_result.brier_score,
            "log_loss": model_result.log_loss_val,
        }

        # Marginal lift
        lift: dict[str, float] = {}
        if prev_metrics is not None:
            lift = {
                k: metrics[k] - prev_metrics[k]
                for k in metrics
            }

        from sc2ml.features.registry import get_groups
        groups_included = [g.name for g in get_groups(group)]

        step = {
            "group": group.name,
            "groups_included": groups_included,
            "n_columns": X_train.shape[1],
            "metrics": metrics,
            "lift": lift,
            "model_result": model_result,
        }
        results.append(step)
        prev_metrics = metrics

        logger.info(
            f"  Group {group.name}: {len(groups_included)} groups, "
            f"{X_train.shape[1]} cols, "
            f"acc={metrics['accuracy']:.4f}, "
            f"AUC={metrics['auc_roc']:.4f}"
            + (f", lift_acc={lift.get('accuracy', 0):+.4f}" if lift else "")
        )

    return results


# ---------------------------------------------------------------------------
# Permutation importance
# ---------------------------------------------------------------------------

def run_permutation_importance(
    model: Any,
    X_test: "pd.DataFrame",
    y_test: "pd.Series",
    n_repeats: int = 10,
    scoring: str = "accuracy",
    seed: int = RANDOM_SEED,
) -> "pd.DataFrame":
    """Permutation importance via sklearn.

    Returns DataFrame with columns: feature, importance_mean, importance_std.
    """
    import pandas as pd
    from sklearn.inspection import permutation_importance

    result = permutation_importance(
        model, X_test, y_test,
        n_repeats=n_repeats,
        scoring=scoring,
        random_state=seed,
    )

    df = pd.DataFrame({
        "feature": X_test.columns,
        "importance_mean": result.importances_mean,
        "importance_std": result.importances_std,
    })
    return df.sort_values("importance_mean", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Patch drift experiment (methodology Section 10)
# ---------------------------------------------------------------------------

def run_patch_drift_experiment(
    raw_df: "pd.DataFrame",
    series_df: "pd.DataFrame | None" = None,
    train_patch_frac: float = 0.8,
    compute_ci: bool = True,
) -> dict[str, Any]:
    """Train on older patches, test on newer patch block.

    Parameters
    ----------
    raw_df : DataFrame from ``get_matches_dataframe()``
    series_df : optional series assignment for Group E
    train_patch_frac : fraction of patches used for training (by time)
    compute_ci : whether to compute bootstrap CIs

    Returns
    -------
    dict with old_patch_results, new_patch_results, mixed_model_results,
    per_patch_breakdown
    """
    from lightgbm import LGBMClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    from sc2ml.config import HGB_LEARNING_RATE, PATCH_MIN_MATCHES, RF_N_ESTIMATORS
    from sc2ml.features import build_features
    from sc2ml.features.common import split_for_ml

    logger.info("Running patch drift experiment...")

    # Build features with all groups
    feat_df = build_features(raw_df.copy(), series_df=series_df)

    # Get unique patches sorted chronologically
    if "game_version" in feat_df.columns:
        patch_col = "game_version"
    elif "data_build" in feat_df.columns:
        patch_col = "data_build"
    else:
        raise ValueError("No patch column found in features DataFrame")

    # Sort patches by their first appearance time
    patch_first_seen = feat_df.groupby(patch_col)["match_time"].min().sort_values()
    patches = patch_first_seen.index.tolist()

    # Split patches into old and new
    cutoff_idx = int(len(patches) * train_patch_frac)
    old_patches = set(patches[:cutoff_idx])
    new_patches = set(patches[cutoff_idx:])

    logger.info(
        f"Patch drift: {len(old_patches)} old patches, "
        f"{len(new_patches)} new patches"
    )

    # Standard split (mixed patches) for reference
    X_train_std, _, X_test_std, y_train_std, _, y_test_std = split_for_ml(feat_df)

    # Patch-based split
    old_mask = feat_df[patch_col].isin(old_patches)
    new_mask = feat_df[patch_col].isin(new_patches)

    drop_cols = [c for c in feat_df.columns if c in (
        "target", "match_id", "match_time", "p1_name", "p2_name",
        "p1_race", "p2_race", "data_build", "game_version",
        "map_name", "tournament_name", "matchup_type", "split",
    )]

    old_df = feat_df[old_mask]
    new_df = feat_df[new_mask]

    X_old = old_df.drop(columns=[c for c in drop_cols if c in old_df.columns])
    y_old = old_df["target"]
    X_new = new_df.drop(columns=[c for c in drop_cols if c in new_df.columns])
    y_new = new_df["target"]

    def _train_and_eval(X_tr, y_tr, X_te, y_te, name):
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LGBMClassifier(
                n_estimators=RF_N_ESTIMATORS,
                max_depth=6,
                learning_rate=HGB_LEARNING_RATE,
                random_state=RANDOM_SEED,
                verbose=-1,
            )),
        ])
        pipeline.fit(X_tr, y_tr)
        return evaluate_model(pipeline, X_te, y_te, name, compute_ci=compute_ci)

    # Train on old patches, test on new
    old_to_new = _train_and_eval(X_old, y_old, X_new, y_new, "old→new")

    # Standard mixed model for reference
    mixed = _train_and_eval(X_train_std, y_train_std, X_test_std, y_test_std, "mixed")

    # Per-patch accuracy on new patches
    per_patch: list[dict[str, Any]] = []
    for patch in sorted(new_patches):
        patch_mask = new_df[patch_col] == patch
        if patch_mask.sum() < PATCH_MIN_MATCHES:
            continue
        X_p = X_new[patch_mask]
        y_p = y_new[patch_mask]
        if len(np.unique(y_p)) < 2:
            continue

        # Use the old→new trained model
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LGBMClassifier(
                n_estimators=RF_N_ESTIMATORS,
                max_depth=6,
                learning_rate=HGB_LEARNING_RATE,
                random_state=RANDOM_SEED,
                verbose=-1,
            )),
        ])
        pipeline.fit(X_old, y_old)
        result = evaluate_model(
            pipeline, X_p, y_p, f"patch_{patch}",
            compute_ci=False,
        )
        per_patch.append({
            "patch": patch,
            "n_samples": int(patch_mask.sum()),
            "accuracy": result.accuracy,
            "auc_roc": result.auc_roc,
        })

    return {
        "old_to_new": old_to_new,
        "mixed_model": mixed,
        "per_patch": per_patch,
        "n_old_patches": len(old_patches),
        "n_new_patches": len(new_patches),
        "accuracy_drop": mixed.accuracy - old_to_new.accuracy,
    }
