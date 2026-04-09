# Canonical Phase List

Single source of truth for the ML experiment lifecycle Phases used in this
repository. Every other file that references a Phase number does so by
pointing at this document.

This file defines Phases and their decomposition into Pipeline Sections.
It does not define Steps — Steps are dataset-scoped execution units defined
in each dataset's ROADMAP, following the rules in `docs/TAXONOMY.md`.

For terminology (what a Phase, Pipeline Section, or Step *is*), see
[`docs/TAXONOMY.md`](TAXONOMY.md). This file answers the different question
of *which* Phases exist and *what they contain*.

---

## Precedence

This file is the canonical source for the Phase list. If any other file
contradicts it, the other file is edited to match.

This file is itself derived from `docs/ml_experiment_lifecycle/` — the
numbered manuals are the methodology source. If a manual is revised and
this file drifts from it, this file is revised to match the manual, not
the reverse. The rule is **one Phase per manual** (plus the thesis writing
wrap-up marker). The rule is mechanical — no Phase is invented, merged,
or split.

---

## The 7 Phases

| # | Name | Source | Summary |
|---|------|--------|---------|
| **01** | Data Exploration | [`ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md`](ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md) | Acquisition, EDA, profiling, cleaning, temporal/panel audits, decision gates |
| **02** | Feature Engineering | [`ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md`](ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md) | Pre-/in-game boundary, symmetry, temporal features, quality, encoding, selection |
| **03** | Splitting & Baselines | [`ml_experiment_lifecycle/03_SPLITTING_AND_BASELINES_MANUAL.md`](ml_experiment_lifecycle/03_SPLITTING_AND_BASELINES_MANUAL.md) | Temporal splitting, purge/embargo, grouped splits, baseline hierarchy, statistical-comparison protocol |
| **04** | Model Training | [`ml_experiment_lifecycle/04_MODEL_TRAINING_MANUAL.md`](ml_experiment_lifecycle/04_MODEL_TRAINING_MANUAL.md) | Pipelines, GNN training, loss/early-stopping/LR, HPO, nested temporal CV, reproducibility |
| **05** | Evaluation & Analysis | [`ml_experiment_lifecycle/05_EVALUATION_AND_ANALYSIS_MANUAL.md`](ml_experiment_lifecycle/05_EVALUATION_AND_ANALYSIS_MANUAL.md) | Metrics, calibration, statistical comparison, error analysis, ablation |
| **06** | Cross-Domain Transfer | [`ml_experiment_lifecycle/06_CROSS_DOMAIN_TRANSFER_MANUAL.md`](ml_experiment_lifecycle/06_CROSS_DOMAIN_TRANSFER_MANUAL.md) | Transfer taxonomy, shared feature space, three-tier experimental design |
| **07** | Thesis Writing Wrap-up | [`thesis/THESIS_WRITING_MANUAL.md`](../thesis/THESIS_WRITING_MANUAL.md) | Gate marker — see *Phase 07 semantics* below |

---

## Phase scope

**Every Phase is dataset-scoped.** A dataset's ROADMAP at
`src/rts_predict/<game>/reports/<dataset>/ROADMAP.md` contains all 7
Phases as its own execution plan. Two datasets under the same game are
treated as independent entities; they do not share ROADMAPs, Pipeline
Sections, or Steps.

This is a deliberate choice. Datasets under a single game may differ
enough that generalising features, cleaning rules, or models across them
is not guaranteed to be possible. Whether generalisation holds is itself
a finding produced by Phase 01 and Phase 02 — not an assumption baked
into the Phase structure.

Cross-dataset or cross-game coordination (e.g., applying one dataset's
trained model to another, or conducting Phase 06 transfer experiments
that span games) is tracked in `reports/research_log.md` and the thesis
chapters, not in any ROADMAP.

---

## Pipeline Section derivation rule

Pipeline Sections within a Phase mirror the top-level sections (`##` in
the manual's markdown) of that Phase's source manual, **excluding** sections
that are methodologically informative but are not themselves work activities:

- **Framing/introductory sections** that set up the manual's argument but
  describe no concrete activity.
- **Warning/pitfall lists** (e.g., "Seven Pitfalls", "Eight Mistakes",
  "Twelve Common Training Mistakes"). These are reference material to
  consult while executing other Pipeline Sections, not Pipeline Sections
  themselves.
- **Conclusions and references.**

Decision gates (e.g., Manual 01 §6 "Decision Gates") **are** Pipeline
Sections — they are exit-criterion methodology that must be actively
executed, not passive reference.

The rule is mechanical: open the manual's table of contents, strike
through the categories above, and the remainder is the Pipeline Section
list in the manual's own order. This file enumerates them below so the
rule's output is stable and reviewable.

---

## Phase 01 — Data Exploration

Source: `01_DATA_EXPLORATION_MANUAL.md`.

| Pipeline Section | Name | Manual Part |
|---|---|---|
| `01_01` | Data Acquisition & Source Inventory | §1 |
| `01_02` | Exploratory Data Analysis (Tukey-style) | §2 |
| `01_03` | Systematic Data Profiling | §3 |
| `01_04` | Data Cleaning | §4 |
| `01_05` | Temporal & Panel EDA | §5 |
| `01_06` | Decision Gates | §6 |

Excluded as meta: §7 "Seven Pitfalls", §8 "Conclusion".

---

## Phase 02 — Feature Engineering

Source: `02_FEATURE_ENGINEERING_MANUAL.md`.

| Pipeline Section | Name | Manual Part |
|---|---|---|
| `02_01` | Pre-Game vs In-Game Boundary | §2 |
| `02_02` | Symmetry & Difference Features | §3 |
| `02_03` | Temporal Features, Windows, Decay, Cold Starts | §4 |
| `02_04` | Feature Quality Assessment | §5 |
| `02_05` | Categorical Encoding & Interactions | §6 |
| `02_06` | Feature Selection | §7 |
| `02_07` | Rating Systems & Domain Features | §9 |
| `02_08` | Feature Documentation & Catalog | §10 |

Excluded as meta: §1 (pipeline overview — framing), §8 "Eight Mistakes",
conclusion.

---

## Phase 03 — Splitting & Baselines

Source: `03_SPLITTING_AND_BASELINES_MANUAL.md`.

| Pipeline Section | Name | Manual Part |
|---|---|---|
| `03_01` | Temporal Splitting Strategies | §2 |
| `03_02` | Purge & Embargo | §3 |
| `03_03` | Grouped Splits for Panel Data | §4 |
| `03_04` | Nested Cross-Validation | §5 |
| `03_05` | Split Validation | §6 |
| `03_06` | Baseline Definitions | §7 |
| `03_07` | Elo & Domain-Specific Baselines | §8 |
| `03_08` | Shared Evaluation Protocol | §9 |
| `03_09` | Statistical-Comparison Protocol | §10 |

Excluded as meta: §1 "Why Random Splits Produce Optimistic Results"
(framing), §11 "Bet on Sparsity Principle" (framing), §12 "Common
Baseline Mistakes", conclusion.

---

## Phase 04 — Model Training

Source: `04_MODEL_TRAINING_MANUAL.md`.

| Pipeline Section | Name | Manual Part |
|---|---|---|
| `04_01` | Training Pipelines (sklearn Pipeline + ColumnTransformer) | §1 |
| `04_02` | GNN Training | §2 |
| `04_03` | Loss Functions | §3 |
| `04_04` | Early Stopping | §4 |
| `04_05` | Learning Rate Scheduling | §5 |
| `04_06` | Hyperparameter Tuning | §6 |
| `04_07` | Nested Temporal Cross-Validation | §7 |
| `04_08` | Reproducibility | §8 |

Excluded as meta: §9 "Twelve Common Training Mistakes", conclusion.

---

## Phase 05 — Evaluation & Analysis

Source: `05_EVALUATION_AND_ANALYSIS_MANUAL.md`.

This manual is organised into four Parts (I–IV), each containing
multiple §subsections. For Pipeline Section derivation, the top-level
organising unit is the **Part** — Pipeline Sections map to Parts, not
to sub-§sections, to keep Phase 05 at a consistent granularity with
the other Phases.

| Pipeline Section | Name | Manual Part |
|---|---|---|
| `05_01` | Evaluation Metrics (threshold, probabilistic, ROC/PR, calibration, sharpness) | Part I |
| `05_02` | Statistical Comparison of Classifiers | Part II |
| `05_03` | Error Analysis | Part III |
| `05_04` | Ablation Studies & Sensitivity Analysis | Part IV |

Excluded as meta: the closing "Recommended Metric and Analysis Tiers"
section and conclusion.

---

## Phase 06 — Cross-Domain Transfer

Source: `06_CROSS_DOMAIN_TRANSFER_MANUAL.md`.

| Pipeline Section | Name | Manual Part |
|---|---|---|
| `06_01` | Transfer Learning Taxonomy | §1 |
| `06_02` | Ben-David's Bound & Transfer Feasibility | §2 |
| `06_03` | Distribution Shift Between Domains | §3 |
| `06_04` | Shared Feature Space Construction | §4 |
| `06_05` | Negative Transfer | §5 |
| `06_06` | Three-Tier Experimental Design | §6 |
| `06_07` | Transfer Evaluation & Reporting | §7 |
| `06_08` | Honest Claims With Two Domains | §8 |
| `06_09` | Component Transferability Analysis | §9 |

Excluded as meta: conclusion.

---

## Phase 07 — Thesis Writing Wrap-up

Phase 07 is a **gate marker**, not a set of Pipeline Sections. In a
dataset's ROADMAP, Phase 07 is the terminal state signalling that the
dataset's contribution is complete and its findings are ready to be
incorporated into the thesis narrative.

**What Phase 07 entails in a dataset ROADMAP:**

- All prior Phases (01–06) have met their exit gates for that dataset.
- `reports/research_log.md` entries for that dataset are current and
  thesis-citable.
- All report artifacts under `reports/<dataset>/artifacts/` are present
  and referenced from the research log.

**What Phase 07 does not entail:**

- It does not own the writing of thesis chapters. Thesis writing is
  tracked by `thesis/WRITING_STATUS.md` and the `thesis/chapters/` tree.
- Thesis chapters that are not dataset-dependent (introduction, related
  work, methodology, concluding discussion) may be drafted at any point
  during the project and do not wait for any dataset's Phase 07 gate.
- Cross-dataset synthesis (comparing findings across datasets) lives in
  the thesis, not in any dataset's Phase 07.

Phase 07 has no Pipeline Sections. A dataset either has passed its
Phase 07 gate or has not; there is nothing to decompose.

---

## How this file is maintained

1. **Never invent Phases.** If a new methodology concept emerges, it is
   added to an existing manual (or a new manual is authored and this
   file adds a Phase to match). The manuals are the source.

2. **Never renumber Phases.** Once a number is assigned, it does not
   change. Downstream ROADMAPs, research log entries, and thesis
   citations use Phase numbers as stable identifiers.

3. **Pipeline Section renumbering is allowed but discouraged.** If a
   manual is restructured and a Pipeline Section must be added, removed,
   or re-ordered, update this file in the same PR that updates the
   manual. Never let the two drift apart across PRs.

4. **The exclusion lists under each Phase are part of the canonical
   record.** If someone disagrees with a specific "meta" classification
   and wants to promote an excluded section to a Pipeline Section, that
   is a change to this file and requires a PR. It is not a judgment
   call made at dataset-ROADMAP authoring time.

5. **New datasets do not trigger changes here.** Adding a dataset means
   creating a new `src/rts_predict/<game>/reports/<dataset>/ROADMAP.md`
   that implements Phases 01–07 following this file. It does not modify
   this file.
