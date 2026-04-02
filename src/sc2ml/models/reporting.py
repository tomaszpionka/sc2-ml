"""Report generation for classical ML experiments.

Produces machine-readable (JSON) and thesis-ready (Markdown) reports
from evaluation results.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sc2ml.config import RESULTS_DIR
from sc2ml.models.evaluation import ModelResults

logger = logging.getLogger(__name__)


@dataclass
class ExperimentReport:
    """Collects all results for final reporting."""

    model_results: list[ModelResults] = field(default_factory=list)
    comparisons: Any = None  # pd.DataFrame
    ablation_results: list[dict[str, Any]] = field(default_factory=list)
    patch_drift: dict[str, Any] = field(default_factory=dict)
    shap_paths: dict[str, Path] = field(default_factory=dict)
    error_analysis: Any = None  # pd.DataFrame

    def to_json(self, path: Path | None = None) -> Path:
        """Write machine-readable JSON report."""
        if path is None:
            RESULTS_DIR.mkdir(parents=True, exist_ok=True)
            path = RESULTS_DIR / "experiment_results.json"

        data: dict[str, Any] = {}

        # Model results
        data["models"] = []
        for r in self.model_results:
            data["models"].append({
                "name": r.model_name,
                "accuracy": r.accuracy,
                "accuracy_ci": list(r.accuracy_ci),
                "auc_roc": r.auc_roc,
                "auc_roc_ci": list(r.auc_roc_ci),
                "brier_score": r.brier_score,
                "brier_score_ci": list(r.brier_score_ci),
                "log_loss": r.log_loss_val,
                "log_loss_ci": list(r.log_loss_ci),
                "per_matchup": r.per_matchup,
                "veterans": r.veterans,
            })

        # Comparisons
        if self.comparisons is not None:
            data["comparisons"] = self.comparisons.to_dict(orient="records")

        # Ablation
        if self.ablation_results:
            data["ablation"] = [
                {k: v for k, v in step.items() if k != "model_result"}
                for step in self.ablation_results
            ]

        # Patch drift
        if self.patch_drift:
            drift = dict(self.patch_drift)
            for key in ("old_to_new", "mixed_model"):
                if key in drift and isinstance(drift[key], ModelResults):
                    drift[key] = {
                        "accuracy": drift[key].accuracy,
                        "auc_roc": drift[key].auc_roc,
                    }
            data["patch_drift"] = drift

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"JSON report saved to {path}")
        return path

    def to_markdown(self, path: Path | None = None) -> Path:
        """Write thesis-ready Markdown report."""
        if path is None:
            path = Path("reports") / "10_classical_evaluation.md"

        lines: list[str] = []
        lines.append("# Classical ML Evaluation Report\n")

        # Model comparison table
        if self.model_results:
            lines.append("## Model Comparison\n")
            lines.append(
                "| Model | Accuracy | 95% CI | AUC-ROC | Brier | Log Loss |"
            )
            lines.append("|-------|----------|--------|---------|-------|----------|")
            for r in self.model_results:
                ci = f"[{r.accuracy_ci[0]:.4f}, {r.accuracy_ci[1]:.4f}]"
                lines.append(
                    f"| {r.model_name} | {r.accuracy:.4f} | {ci} | "
                    f"{r.auc_roc:.4f} | {r.brier_score:.4f} | "
                    f"{r.log_loss_val:.4f} |"
                )
            lines.append("")

        # Statistical comparisons
        if self.comparisons is not None and len(self.comparisons) > 0:
            lines.append("## Statistical Comparisons\n")
            lines.append(
                "| Model A | Model B | Acc Diff | McNemar p | AUC Diff | DeLong p |"
            )
            lines.append("|---------|---------|----------|-----------|----------|----------|")
            for _, row in self.comparisons.iterrows():
                lines.append(
                    f"| {row['model_a']} | {row['model_b']} | "
                    f"{row['acc_diff']:+.4f} | {row['mcnemar_p']:.4f} | "
                    f"{row['auc_diff']:+.4f} | {row['delong_p']:.4f} |"
                )
            lines.append("")

        # Ablation results
        if self.ablation_results:
            lines.append("## Feature Group Ablation\n")
            lines.append(
                "| Groups | Columns | Accuracy | AUC-ROC | Lift (Acc) |"
            )
            lines.append("|--------|---------|----------|---------|------------|")
            for step in self.ablation_results:
                groups = "+".join(step["groups_included"])
                lift = step["lift"].get("accuracy", 0) if step["lift"] else 0
                lines.append(
                    f"| {groups} | {step['n_columns']} | "
                    f"{step['metrics']['accuracy']:.4f} | "
                    f"{step['metrics']['auc_roc']:.4f} | "
                    f"{lift:+.4f} |"
                )
            lines.append("")

        # Per-matchup breakdown
        if self.model_results:
            best = max(self.model_results, key=lambda r: r.auc_roc)
            if best.per_matchup:
                lines.append(f"## Per-Matchup Breakdown ({best.model_name})\n")
                lines.append("| Matchup | N | Accuracy | AUC-ROC |")
                lines.append("|---------|---|----------|---------|")
                for matchup, metrics in sorted(best.per_matchup.items()):
                    lines.append(
                        f"| {matchup} | {metrics.get('n_samples', '?')} | "
                        f"{metrics['accuracy']:.4f} | {metrics['auc_roc']:.4f} |"
                    )
                lines.append("")

        # Error analysis
        if self.error_analysis is not None and len(self.error_analysis) > 0:
            lines.append("## Error Analysis by Subgroup\n")
            lines.append("| Subgroup | N | Accuracy | AUC-ROC | Error Rate |")
            lines.append("|----------|---|----------|---------|------------|")
            for _, row in self.error_analysis.iterrows():
                auc_val = row['auc_roc']
                auc = "N/A" if str(auc_val).startswith("nan") else f"{auc_val:.4f}"
                lines.append(
                    f"| {row['subgroup']} | {row['n_samples']} | "
                    f"{row['accuracy']:.4f} | {auc} | "
                    f"{row['error_rate']:.4f} |"
                )
            lines.append("")

        # Patch drift
        if self.patch_drift:
            lines.append("## Patch Drift Analysis\n")
            drift = self.patch_drift
            if "old_to_new" in drift and "mixed_model" in drift:
                otn = drift["old_to_new"]
                mix = drift["mixed_model"]
                acc_otn = (
                    otn.accuracy if isinstance(otn, ModelResults) else otn.get("accuracy", "?")
                )
                acc_mix = (
                    mix.accuracy if isinstance(mix, ModelResults) else mix.get("accuracy", "?")
                )
                lines.append(f"- Old→New accuracy: {acc_otn:.4f}")
                lines.append(f"- Mixed model accuracy: {acc_mix:.4f}")
                lines.append(f"- Accuracy drop: {drift.get('accuracy_drop', '?'):.4f}")
            lines.append("")

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write("\n".join(lines))

        logger.info(f"Markdown report saved to {path}")
        return path
