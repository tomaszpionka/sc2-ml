# ML Experiment Lifecycle — Methodology Manuals

This directory contains six methodology manuals, one per Phase of the experiment
lifecycle. Read them in Phase order. Each manual is self-contained.

| # | Manual | Covers |
|---|--------|--------|
| 01 | [Data Exploration](01_DATA_EXPLORATION_MANUAL.md) | Schema audit, temporal coverage, class balance, leakage checks |
| 02 | [Feature Engineering](02_FEATURE_ENGINEERING_MANUAL.md) | Feature groups, temporal aggregates, Bayesian smoothing, leakage guards |
| 03 | [Splitting & Baselines](03_SPLITTING_AND_BASELINES_MANUAL.md) | Temporal split strategy, baseline models, evaluation scaffold |
| 04 | [Model Training](04_MODEL_TRAINING_MANUAL.md) | Classical ML, GNN, hyperparameter tuning, reproducibility |
| 05 | [Evaluation & Analysis](05_EVALUATION_AND_ANALYSIS_MANUAL.md) | Metrics, bootstrap CI, calibration, ablation |
| 06 | [Cross-Domain Transfer](06_CROSS_DOMAIN_TRANSFER_MANUAL.md) | SC2 → AoE2 transfer, domain adaptation, thesis synthesis |

## Usage

Start with the manual for the Phase you are entering. Each manual references
the canonical phase list at `docs/PHASES.md` and the dataset ROADMAPs under
`src/rts_predict/<game>/reports/<dataset>/ROADMAP.md`.
