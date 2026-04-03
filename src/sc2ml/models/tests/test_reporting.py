"""Tests for ExperimentReport JSON and Markdown generation."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sc2ml.models.evaluation import ModelResults
from sc2ml.models.reporting import ExperimentReport

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_model_result(
    name: str = "LogisticRegression",
    accuracy: float = 0.72,
    auc_roc: float = 0.78,
) -> ModelResults:
    """Create a minimal ModelResults for testing."""
    return ModelResults(
        model_name=name,
        accuracy=accuracy,
        auc_roc=auc_roc,
        brier_score=0.20,
        log_loss_val=0.55,
        accuracy_ci=(0.70, 0.74),
        auc_roc_ci=(0.76, 0.80),
        brier_score_ci=(0.18, 0.22),
        log_loss_ci=(0.52, 0.58),
        y_true=np.array([0, 1, 1, 0]),
        y_pred=np.array([0, 1, 0, 0]),
        y_prob=np.array([0.3, 0.8, 0.4, 0.2]),
        per_matchup={
            "PvT": {"accuracy": 0.75, "auc_roc": 0.80, "n_samples": 50},
        },
        veterans={"accuracy": 0.74, "auc_roc": 0.79},
    )


@pytest.fixture()
def report_with_all(tmp_path: Path) -> tuple[ExperimentReport, Path]:
    """A fully populated ExperimentReport plus a tmp directory."""
    lr = _make_model_result("LogisticRegression", 0.72, 0.78)
    rf = _make_model_result("RandomForest", 0.74, 0.81)

    comparisons = pd.DataFrame([{
        "model_a": "LogisticRegression",
        "model_b": "RandomForest",
        "acc_diff": -0.02,
        "mcnemar_p": 0.045,
        "auc_diff": -0.03,
        "delong_p": 0.032,
    }])

    ablation = [
        {
            "groups_included": ["A"],
            "n_columns": 5,
            "metrics": {"accuracy": 0.68, "auc_roc": 0.72},
            "lift": {"accuracy": 0.0},
            "model_result": lr,
        },
        {
            "groups_included": ["A", "B"],
            "n_columns": 12,
            "metrics": {"accuracy": 0.72, "auc_roc": 0.78},
            "lift": {"accuracy": 0.04},
            "model_result": lr,
        },
    ]

    error_df = pd.DataFrame([{
        "subgroup": "mirror_matchup",
        "n_samples": 40,
        "accuracy": 0.60,
        "auc_roc": 0.65,
        "error_rate": 0.40,
    }])

    patch_drift = {
        "old_to_new": lr,
        "mixed_model": rf,
        "accuracy_drop": 0.03,
    }

    report = ExperimentReport(
        model_results=[lr, rf],
        comparisons=comparisons,
        ablation_results=ablation,
        patch_drift=patch_drift,
        error_analysis=error_df,
    )
    return report, tmp_path


# ---------------------------------------------------------------------------
# JSON tests
# ---------------------------------------------------------------------------


class TestToJson:
    def test_to_json_creates_file(self, report_with_all: tuple[ExperimentReport, Path]):
        report, tmp = report_with_all
        out = report.to_json(tmp / "result.json")
        assert out.exists()

    def test_to_json_default_path(self):
        """to_json without explicit path uses RESULTS_DIR."""
        report = ExperimentReport(model_results=[_make_model_result()])
        path = report.to_json()
        assert path.exists()
        assert "results" in str(path)
        path.unlink()  # cleanup

    def test_to_json_model_results_structure(
        self, report_with_all: tuple[ExperimentReport, Path]
    ):
        report, tmp = report_with_all
        path = report.to_json(tmp / "r.json")
        data = json.loads(path.read_text())
        assert "models" in data
        m = data["models"][0]
        assert "name" in m
        assert "accuracy" in m
        assert "auc_roc" in m
        assert "per_matchup" in m
        assert "veterans" in m

    def test_to_json_comparisons_serialized(
        self, report_with_all: tuple[ExperimentReport, Path]
    ):
        report, tmp = report_with_all
        data = json.loads(report.to_json(tmp / "r.json").read_text())
        assert "comparisons" in data
        assert len(data["comparisons"]) == 1
        assert data["comparisons"][0]["model_a"] == "LogisticRegression"

    def test_to_json_ablation_results(
        self, report_with_all: tuple[ExperimentReport, Path]
    ):
        report, tmp = report_with_all
        data = json.loads(report.to_json(tmp / "r.json").read_text())
        assert "ablation" in data
        # model_result key should be excluded
        for step in data["ablation"]:
            assert "model_result" not in step

    def test_to_json_patch_drift_with_model_results(
        self, report_with_all: tuple[ExperimentReport, Path]
    ):
        """ModelResults objects in patch_drift are serialized to dicts."""
        report, tmp = report_with_all
        data = json.loads(report.to_json(tmp / "r.json").read_text())
        drift = data["patch_drift"]
        assert isinstance(drift["old_to_new"], dict)
        assert "accuracy" in drift["old_to_new"]

    def test_to_json_patch_drift_with_dict(self, tmp_path: Path):
        """Plain dicts in patch_drift are preserved as-is."""
        report = ExperimentReport(
            model_results=[_make_model_result()],
            patch_drift={
                "old_to_new": {"accuracy": 0.70, "auc_roc": 0.75},
                "mixed_model": {"accuracy": 0.72, "auc_roc": 0.77},
            },
        )
        data = json.loads(report.to_json(tmp_path / "r.json").read_text())
        assert data["patch_drift"]["old_to_new"]["accuracy"] == 0.70


# ---------------------------------------------------------------------------
# Markdown tests
# ---------------------------------------------------------------------------


class TestToMarkdown:
    def test_to_markdown_creates_file(
        self, report_with_all: tuple[ExperimentReport, Path]
    ):
        report, tmp = report_with_all
        out = report.to_markdown(tmp / "report.md")
        assert out.exists()

    def test_to_markdown_default_path(self):
        """to_markdown without explicit path uses reports/ default."""
        report = ExperimentReport(model_results=[_make_model_result()])
        path = report.to_markdown()
        assert path.exists()
        assert path.name == "10_classical_evaluation.md"
        path.unlink()  # cleanup

    def test_to_markdown_model_comparison_table(
        self, report_with_all: tuple[ExperimentReport, Path]
    ):
        report, tmp = report_with_all
        text = report.to_markdown(tmp / "report.md").read_text()
        assert "## Model Comparison" in text
        assert "LogisticRegression" in text
        assert "RandomForest" in text

    def test_to_markdown_statistical_comparisons(
        self, report_with_all: tuple[ExperimentReport, Path]
    ):
        report, tmp = report_with_all
        text = report.to_markdown(tmp / "report.md").read_text()
        assert "## Statistical Comparisons" in text
        assert "McNemar" in text

    def test_to_markdown_ablation_section(
        self, report_with_all: tuple[ExperimentReport, Path]
    ):
        report, tmp = report_with_all
        text = report.to_markdown(tmp / "report.md").read_text()
        assert "## Feature Group Ablation" in text
        assert "A+B" in text

    def test_to_markdown_per_matchup_breakdown(
        self, report_with_all: tuple[ExperimentReport, Path]
    ):
        report, tmp = report_with_all
        text = report.to_markdown(tmp / "report.md").read_text()
        assert "Per-Matchup Breakdown" in text
        assert "PvT" in text

    def test_to_markdown_error_analysis(
        self, report_with_all: tuple[ExperimentReport, Path]
    ):
        report, tmp = report_with_all
        text = report.to_markdown(tmp / "report.md").read_text()
        assert "## Error Analysis by Subgroup" in text
        assert "mirror_matchup" in text

    def test_to_markdown_patch_drift(
        self, report_with_all: tuple[ExperimentReport, Path]
    ):
        report, tmp = report_with_all
        text = report.to_markdown(tmp / "report.md").read_text()
        assert "## Patch Drift Analysis" in text
        assert "Old→New accuracy" in text
