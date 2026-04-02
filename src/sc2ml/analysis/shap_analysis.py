"""SHAP-based model interpretability (methodology Section 8.1).

Provides:
- Global SHAP summary plots (beeswarm) for the best pre-match model
- Per-matchup SHAP comparison across the 6 race matchup types
- Feature importance tables (mean |SHAP|)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import shap

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


def compute_shap_values(
    pipeline: Any,
    X_test: "pd.DataFrame",
    max_samples: int = 1000,
) -> shap.Explanation:
    """Compute SHAP values for a trained pipeline.

    Uses TreeExplainer for tree-based models (RF, GB, XGB, LGBM) and
    LinearExplainer for linear models (LR).

    Parameters
    ----------
    pipeline : fitted sklearn Pipeline with 'scaler' and 'classifier' steps
    X_test : test features DataFrame
    max_samples : subsample size for SHAP computation (for speed)

    Returns
    -------
    shap.Explanation with feature_names set to X_test column names
    """
    scaler = pipeline.named_steps["scaler"]
    clf = pipeline.named_steps["classifier"]

    # Subsample if needed
    if len(X_test) > max_samples:
        X_sample = X_test.sample(n=max_samples, random_state=42)
    else:
        X_sample = X_test

    X_scaled = scaler.transform(X_sample)
    feature_names = X_test.columns.tolist()

    # Choose explainer based on model type
    class_name = type(clf).__name__
    if class_name in ("RandomForestClassifier", "GradientBoostingClassifier",
                      "HistGradientBoostingClassifier", "XGBClassifier",
                      "LGBMClassifier"):
        explainer = shap.TreeExplainer(clf)
        shap_values = explainer(X_scaled)
    elif class_name == "LogisticRegression":
        explainer = shap.LinearExplainer(clf, X_scaled)
        shap_values = explainer(X_scaled)
    else:
        logger.warning(
            f"Unknown model type {class_name}, falling back to KernelExplainer"
        )
        background = shap.sample(X_scaled, min(100, len(X_scaled)))
        explainer = shap.KernelExplainer(clf.predict_proba, background)
        shap_values = explainer(X_scaled)

    # For binary classification, TreeExplainer may return 3D values
    # Shape: (n_samples, n_features, n_classes) -> take class 1
    if shap_values.values.ndim == 3:
        shap_values = shap.Explanation(
            values=shap_values.values[:, :, 1],
            base_values=(
                shap_values.base_values[:, 1]
                if shap_values.base_values.ndim > 1
                else shap_values.base_values
            ),
            data=shap_values.data,
            feature_names=feature_names,
        )
    else:
        shap_values.feature_names = feature_names

    return shap_values


def plot_shap_beeswarm(
    shap_values: shap.Explanation,
    output_path: Path,
    title: str = "SHAP Feature Importance",
    max_display: int = 20,
) -> None:
    """Save SHAP beeswarm plot to file."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    shap.plots.beeswarm(shap_values, max_display=max_display, show=False)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"SHAP beeswarm saved to {output_path}")


def plot_shap_per_matchup(
    pipeline: Any,
    X_test: "pd.DataFrame",
    matchup_col: "pd.Series",
    output_dir: Path,
    max_samples_per_matchup: int = 500,
) -> None:
    """Compute and plot SHAP for each of the 6 matchup types."""
    import matplotlib
    matplotlib.use("Agg")

    output_dir.mkdir(parents=True, exist_ok=True)

    for matchup in sorted(matchup_col.unique()):
        mask = matchup_col == matchup
        X_matchup = X_test[mask]
        if len(X_matchup) < 10:
            logger.warning(f"Skipping matchup {matchup}: only {len(X_matchup)} samples")
            continue

        shap_values = compute_shap_values(
            pipeline, X_matchup,
            max_samples=max_samples_per_matchup,
        )
        path = output_dir / f"shap_{matchup}.png"
        plot_shap_beeswarm(
            shap_values, path,
            title=f"SHAP — {matchup}",
        )


def shap_feature_importance_table(
    shap_values: shap.Explanation,
) -> "pd.DataFrame":
    """Mean absolute SHAP value per feature, sorted descending."""
    import pandas as pd

    mean_abs = np.abs(shap_values.values).mean(axis=0)
    df = pd.DataFrame({
        "feature": shap_values.feature_names,
        "mean_abs_shap": mean_abs,
    })
    return df.sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
