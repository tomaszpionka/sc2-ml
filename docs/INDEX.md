# Documentation Index

> **Single entry point for all project documentation.** Claude Code agents
> should read this file to locate the relevant manual for the current phase.

---

## ML Experiment Lifecycle Manuals

Six methodology manuals covering the full pipeline from raw data to
cross-domain transfer. Each is a standalone reference with academic citations.

| Manual | File | Lifecycle phases covered |
|--------|------|------------------------|
| **01 — Data Exploration** | `ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md` | Data Acquisition & Source Inventory, Data Profiling, EDA, Data Cleaning & Validation |
| **02 — Feature Engineering** | `ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md` | Pre-game vs. in-game boundary, symmetry features, temporal windows, target encoding, feature selection |
| **03 — Splitting & Baselines** | `ml_experiment_lifecycle/03_SPLITTING_AND_BASELINES_MANUAL.md` | Temporal train/val/test splitting, purge & embargo, grouped splits, baseline hierarchy (Dummy→Elo→LR) |
| **04 — Model Training** | `ml_experiment_lifecycle/04_MODEL_TRAINING_MANUAL.md` | sklearn Pipelines, GNN training loops, loss functions, early stopping, LR scheduling, Optuna HPO, reproducibility |
| **05 — Evaluation & Analysis** | `ml_experiment_lifecycle/05_EVALUATION_AND_ANALYSIS_MANUAL.md` | Metrics (probabilistic + threshold), calibration, statistical comparison (Demšar/Bayesian), SHAP, ablation studies |
| **06 — Cross-Domain Transfer** | `ml_experiment_lifecycle/06_CROSS_DOMAIN_TRANSFER_MANUAL.md` | SC2↔AoE2 transfer taxonomy, shared feature space, negative transfer, three-tier experimental design |

### Which manual to consult by current phase

| `PHASE_STATUS.yaml` value | Primary manual | Secondary |
|---------------------------|---------------|-----------|
| Phase 0–1 (acquisition, ingestion) | 01 | — |
| Phase 2 (profiling, EDA) | 01 | — |
| Phase 3 (cleaning, validation) | 01 | — |
| Phase 4 (feature engineering) | 02 | 01 (for feature profiling) |
| Phase 5 (splitting, baselines) | 03 | — |
| Phase 6–7 (training, tuning) | 04 | 03 (for temporal CV) |
| Phase 8 (evaluation, comparison) | 05 | 04 (for reproducibility) |
| Phase 9 (error analysis, ablation) | 05 | 02 (for feature ablation context) |
| Phase 10 (cross-domain transfer) | 06 | 03, 05 (for shared eval protocol) |
| Phase 11 (thesis writing) | Thesis Writing Manual | 05 (for results presentation) |

---

## Thesis Documentation

| Document | File | Purpose |
|----------|------|---------|
| **Thesis Writing Manual** | `thesis/THESIS_WRITING_MANUAL.md` | Academic writing standards, chapter structure, statistical reporting, iterative workflow |
| **PJAIT Requirements** | `thesis/PJAIT_THESIS_REQUIREMENTS.md` | Institutional formatting, submission process, defense structure, grading, GenAI policy |

Connected tracking files (outside `docs/`):

| Tracker | Location | Purpose |
|---------|----------|---------|
| Chapter progress | `thesis/WRITING_STATUS.md` | Per-section SKELETON → FINAL status |
| Chapter structure | `thesis/THESIS_STRUCTURE.md` | Section outline with scope definitions |
| Review queue | `thesis/chapters/REVIEW_QUEUE.md` | Pass 1 → Pass 2 handoff tracking |
| Formatting rules | `.claude/thesis-formatting-rules.yaml` | Machine-readable PJAIT thresholds |

---

## Agent & Infrastructure Documentation

| Document | File | Purpose |
|----------|------|---------|
| **Agent Manual** | `agents/AGENT_MANUAL.md` | Sub-agent architecture, invocation patterns, troubleshooting |

---

## Citation Convention

All manuals use **reference-style markdown links** with a `## References` section
at the bottom containing full URLs, author names, titles, and publication venues.
This convention is enforced across all research outputs for source traceability.
