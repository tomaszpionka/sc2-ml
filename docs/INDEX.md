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

> The canonical Phase list and numbering live in [`docs/PHASES.md`](PHASES.md).
> The table below is a convenience lookup only — it does not define Phases.

| Active Phase | Primary manual | Secondary |
|---|---|---|
| **01** — Data Exploration | 01 | — |
| **02** — Feature Engineering | 02 | 01 (for feature profiling) |
| **03** — Splitting & Baselines | 03 | — |
| **04** — Model Training | 04 | 03 (for temporal CV) |
| **05** — Evaluation & Analysis | 05 | 04 (for reproducibility) |
| **06** — Cross-Domain Transfer | 06 | 03, 05 (for shared eval protocol) |
| **07** — Thesis Writing Wrap-up | Thesis Writing Manual | 05 (for results presentation) |

---

## Thesis Documentation

| Document | File | Purpose |
|----------|------|---------|
| **Thesis Writing Manual** | `thesis/THESIS_WRITING_MANUAL.md` | Academic writing standards, chapter structure, statistical reporting, iterative workflow |
| **PJAIT Requirements** | `thesis/PJAIT_THESIS_REQUIREMENTS.md` | Institutional formatting, submission process, defense structure, grading, GenAI policy |

Connected tracking files (outside `docs/`):

| Tracker | Location | Purpose |
|---------|----------|---------|
| Research log (index) | `reports/research_log.md` | Cross-cutting (`[CROSS]`) entries and index of per-dataset logs |
| Research log (per-dataset) | `src/rts_predict/<game>/reports/<dataset>/research_log.md` | Game/dataset-specific analytical findings per phase |
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

## Directory Map

Single lookup for any agent to find the index/README of a major project directory.

| Directory | Index | Contents |
|-----------|-------|----------|
| `.claude/` | `.claude/README.md` | Agents, rules, commands, invariants |
| `docs/templates/` | `docs/templates/README.md` | Template schemas |
| `thesis/` | `thesis/README.md` | Chapters, writing workflow |
| `scripts/` | `scripts/README.md` | Hooks, utilities, diagnostics |
| `docs/ml_experiment_lifecycle/` | `docs/ml_experiment_lifecycle/README.md` | Phase methodology manuals |
| `src/rts_predict/sc2/` | `src/rts_predict/sc2/README.md` | SC2 game package |
| `src/rts_predict/aoe2/` | `src/rts_predict/aoe2/README.md` | AoE2 game package |
| `reports/` | `reports/README.md` | Research log index + CROSS entries |
| `planning/` | `planning/INDEX.md` | Active plan, DAG, specs |

---

## Citation Convention

All manuals use **reference-style markdown links** with a `## References` section
at the bottom containing full URLs, author names, titles, and publication venues.
This convention is enforced across all research outputs for source traceability.
