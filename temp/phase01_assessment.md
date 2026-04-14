# Phase 01 Progress Assessment

**Date:** 2026-04-14
**Assessor:** planner-science
**Scope:** Phase 01 (Data Exploration) completion state for sc2egset, aoe2companion, aoestats
**Sources consulted:** TAXONOMY.md, PHASES.md, scientific-invariants.md, 01_DATA_EXPLORATION_MANUAL.md, per-dataset ROADMAP.md, STEP_STATUS.yaml, sandbox notebooks, report artifacts, research logs, step_template.yaml

---

## 1. SC2EGSet

### 1.1 Step Inventory Table

| Step ID | Step Name | Notebook? | Executed? | SQL present? | Magic-number clean? | Status |
|---|---|---|---|---|---|---|
| 01_01_01 | File Inventory | .py + .ipynb | Artifacts on disk; ipynb has 0 outputs | N/A (filesystem only) | N/A (full census) | Done |
| 01_01_02 | Schema Discovery | .py + .ipynb | Artifacts on disk; ipynb has 0 outputs | N/A (reads JSON files) | N/A (sampling justified) | Done |
| 01_02_01 | DuckDB Pre-Ingestion Investigation | .py + .ipynb | Artifacts on disk; ipynb has 0 outputs | Yes (27 SQL blocks in .md) | Yes | Done |
| 01_02_02 | DuckDB Ingestion | .py + .ipynb | Artifacts on disk; ipynb has 18/24 outputs | Yes | Yes | Done |
| 01_02_03 | Raw Schema DESCRIBE | .py + .ipynb | Artifacts on disk; ipynb has 4/5 outputs | Yes | Yes | Partial |
| 01_02_04 | Metadata STRUCT Extraction & Replay-Level EDA | .py + .ipynb | Artifacts on disk (910-line .md, 45KB .json, 11 plot PNGs); ipynb has 0 outputs | Yes (27 SQL blocks in .md, all with inline result tables) | Yes (22.4 loops/sec derived from 16 base x 1.4 Faster; 0.001 uniqueness threshold from EDA Manual §3.3) | Partial |

**01_02_03 Partial justification:** Step template requires a `report:` field. The ROADMAP spec for 01_02_03 omits it. Only a `.json` artifact is produced, not a `.md` report. Schema YAML files are present.

**01_02_04 Partial justification:** (a) Research log has no entry for 01_02_04 despite STEP_STATUS marking it complete. (b) ipynb has zero execution outputs — artifacts exist on disk but the notebook itself carries no inline proof of execution.

### 1.2 Pipeline Section Coverage

| Pipeline Section | Name | Steps Defined | Done | Partial | Missing | Section Exit Met? |
|---|---|---|---|---|---|---|
| 01_01 | Data Acquisition & Source Inventory | 2 | 2 | 0 | 0 | **Partially met.** File inventory and schema discovery complete. No formal Datasheet/Data Card. |
| 01_02 | Exploratory Data Analysis (Tukey-style) | 4 | 2 | 2 | 0 | **Partially met.** Univariate layer done. Bivariate and multivariate layers not started (no steps defined). |
| 01_03 | Systematic Data Profiling | 0 | 0 | 0 | 0 | **Not met.** No steps defined. |
| 01_04 | Data Cleaning | 0 | 0 | 0 | 0 | **Not met.** No steps defined. |
| 01_05 | Temporal & Panel EDA | 0 | 0 | 0 | 0 | **Not met.** No steps defined. |
| 01_06 | Decision Gates | 0 | 0 | 0 | 0 | **Not met.** No steps defined. |

### 1.3 Manual-Level Gap Analysis

| Sub-arc | Status | Notes |
|---|---|---|
| **Source inventory (Datasheets/Data Cards)** | Partial | Zenodo provenance documented in ROADMAP header. File inventory (01_01_01) and schema discovery (01_01_02) artifacts present. No formal Datasheet (Gebru et al.) or Data Card (Pushkarna et al.) produced. |
| **Column-level profiling** | Partial | NULL census complete for all 25 replay_players_raw columns (01_02_04). Cardinality, descriptive stats, distribution shape for numeric/categorical fields covered. No formal outlier flagging (IQR fences, z-scores) or format/pattern analysis for strings. |
| **Dataset-level profiling** | Partial | Row counts established. Temporal coverage (2016-2024) established. Class balance of target (result) profiled. No duplicate row detection, no completeness matrix heatmap, no correlation matrix, no memory footprint analysis. |
| **EDA layers** | Partial | **Univariate:** Done (01_02_04 covers histograms, bar charts, descriptive stats). **Bivariate:** Not started. **Multivariate:** Not started. |
| **Cleaning & validation** | Not started | No cleaning rules defined. No cleaning registry. Raw data immutability respected (all steps are read-only). No staging layer. |

### 1.4 Invariant Violations Observed

| # | File | Description |
|---|---|---|
| 6 | `STEP_STATUS.yaml` (01_02_04 marked complete) vs `research_log.md` (no 01_02_04 entry) | Step marked complete without research log entry — violates step contract in TAXONOMY.md. |
| — | `ROADMAP.md` 01_02_03 step spec | Missing required `report:` field per `docs/templates/step_template.yaml`. |

### 1.5 Distance-to-Phase-Completion Summary

**Verdict: Phase 01 partially complete.**

Remaining items in dependency order:

1. Add research log entry for 01_02_04 (step contract fulfillment).
2. Add `report:` field to 01_02_03 step spec or produce the `.md` artifact.
3. Re-execute 01_02_04 notebook to embed outputs in ipynb (audit trail).
4. Define and execute bivariate EDA step(s) under 01_02 (correlation, cross-tabulation, matchup analysis).
5. Define and execute multivariate EDA step(s) under 01_02 (pair plots, PCA, dimensionality reduction).
6. Define and execute 01_03 steps: formal column-level and dataset-level profiling (outlier detection, completeness matrix, correlation matrix, duplicate detection).
7. Define and execute 01_04 steps: cleaning registry, non-destructive cleaning rules, CONSORT-style flow diagram, post-cleaning validation.
8. Define and execute 01_05 steps: stationarity assessment, concept drift detection (patch-based), panel variance decomposition, survivorship bias check, temporal leakage audit.
9. Define and execute 01_06 steps: data dictionary, data quality report, risk register, modeling readiness decision.

**Hard blockers:** None. Raw data acquired and ingested. DuckDB tables populated.

---

## 2. aoe2companion

### 2.1 Step Inventory Table

| Step ID | Step Name | Notebook? | Executed? | SQL present? | Magic-number clean? | Status |
|---|---|---|---|---|---|---|
| 01_01_01 | File Inventory | .py + .ipynb | Artifacts on disk; ipynb has 0 outputs | N/A (filesystem only) | N/A (full census) | Done |
| 01_01_02 | Schema Discovery | .py + .ipynb | Artifacts on disk; ipynb has 0 outputs | N/A (reads file metadata) | N/A (full census) | Done |
| 01_02_01 | DuckDB Pre-Ingestion | .py + .ipynb | Artifacts on disk; ipynb has 19/21 outputs | Yes | Yes | Done |
| 01_02_02 | DuckDB Ingestion | .py + .ipynb | Artifacts on disk; ipynb has 10/11 outputs | Yes | Yes | Done |
| 01_02_03 | Raw Schema DESCRIBE | .py + .ipynb | Artifacts on disk; ipynb has 7/8 outputs | Yes | Yes | Partial |
| 01_02_04 | Univariate Census & Target Variable EDA | .py + .ipynb | Artifacts on disk (225-line .md, 75KB .json, 5 plot PNGs); ipynb has 0 outputs | Partial (16 SQL blocks; some use template variables `{col}`, `<table>`) | Yes (0.001 uniqueness threshold from EDA Manual §3.3) | Partial |

**01_02_03 Partial justification:** Missing required `report:` field in ROADMAP spec. No `.md` report artifact produced.

**01_02_04 Partial justification:** (a) Research log has no entry for 01_02_04. (b) ipynb has zero execution outputs. (c) The `.md` report artifact uses template-form SQL (e.g., `"{col}"`, `<table>`) for the numeric and categorical profile sections rather than the literal instantiated queries — borderline Invariant #6 compliance. The template is auditable in the .py source but the report artifact is not fully self-contained.

### 2.2 Pipeline Section Coverage

| Pipeline Section | Name | Steps Defined | Done | Partial | Missing | Section Exit Met? |
|---|---|---|---|---|---|---|
| 01_01 | Data Acquisition & Source Inventory | 2 | 2 | 0 | 0 | **Partially met.** Inventory and schema done. No formal Datasheet/Data Card. |
| 01_02 | Exploratory Data Analysis (Tukey-style) | 4 | 2 | 2 | 0 | **Partially met.** Univariate layer done. Bivariate and multivariate not started. |
| 01_03 | Systematic Data Profiling | 0 | 0 | 0 | 0 | **Not met.** No steps defined. |
| 01_04 | Data Cleaning | 0 | 0 | 0 | 0 | **Not met.** No steps defined. |
| 01_05 | Temporal & Panel EDA | 0 | 0 | 0 | 0 | **Not met.** No steps defined. |
| 01_06 | Decision Gates | 0 | 0 | 0 | 0 | **Not met.** No steps defined. |

### 2.3 Manual-Level Gap Analysis

| Sub-arc | Status | Notes |
|---|---|---|
| **Source inventory (Datasheets/Data Cards)** | Partial | API provenance documented in ROADMAP header and reports/README.md. File inventory and schema discovery complete. No formal Datasheet or Data Card. |
| **Column-level profiling** | Partial | NULL census covers all 55 matches_raw columns and auxiliary tables. Cardinality and descriptive stats for key fields. Target variable (won) profiled with intra-match consistency check. No formal outlier flagging or pattern analysis. |
| **Dataset-level profiling** | Partial | Row counts established for all 4 tables. Temporal coverage established. Class balance profiled. Match structure by leaderboard analyzed. No duplicate detection, no completeness matrix, no correlation matrix. |
| **EDA layers** | Partial | **Univariate:** Done. **Bivariate:** Not started. **Multivariate:** Not started. |
| **Cleaning & validation** | Not started | No cleaning rules. Raw data immutability respected. No staging layer. |

### 2.4 Invariant Violations Observed

| # | File | Description |
|---|---|---|
| 6 | `01_02_04_univariate_census.md` | Sections D, E, F use template-form SQL (`{col}`, `<table>`) rather than literal instantiated queries. The specific queries run are in the .py notebook but not fully reproduced in the report artifact. |
| 6 | `STEP_STATUS.yaml` (01_02_04 marked complete) vs `research_log.md` (no entry) | Step marked complete without research log entry. |
| — | `ROADMAP.md` 01_02_03 step spec | Missing required `report:` field per step template. |

### 2.5 Distance-to-Phase-Completion Summary

**Verdict: Phase 01 partially complete.**

Remaining items in dependency order:

1. Produce a fully instantiated `.md` report for 01_02_04 (replace template SQL with literal queries or reference the .py notebook explicitly) to satisfy Invariant #6.
2. Add research log entry for 01_02_04.
3. Add `report:` field to 01_02_03 step spec or produce the `.md` artifact.
4. Re-execute 01_02_04 notebook to embed outputs in ipynb.
5. Define and execute bivariate EDA step(s) under 01_02.
6. Define and execute multivariate EDA step(s) under 01_02.
7. Define and execute 01_03 steps (formal profiling).
8. Define and execute 01_04 steps (cleaning registry, rules, validation).
9. Define and execute 01_05 steps (temporal/panel EDA).
10. Define and execute 01_06 steps (decision gates, go/no-go).

**Hard blockers:** None. Raw data acquired. All 4 DuckDB tables populated.

---

## 3. aoestats

### 3.1 Step Inventory Table

| Step ID | Step Name | Notebook? | Executed? | SQL present? | Magic-number clean? | Status |
|---|---|---|---|---|---|---|
| 01_01_01 | File Inventory | .py + .ipynb | Artifacts on disk; ipynb has 0 outputs | N/A (filesystem only) | N/A (full census) | Done |
| 01_01_02 | Schema Discovery | .py + .ipynb | Artifacts on disk; ipynb has 0 outputs | N/A (reads file metadata) | N/A (full census) | Done |
| 01_02_01 | DuckDB Pre-Ingestion | .py + .ipynb | Artifacts on disk; ipynb has 0 outputs | Yes | Yes | Done |
| 01_02_02 | DuckDB Ingestion | .py + .ipynb | Artifacts on disk; ipynb has 8/9 outputs | Yes | Yes | Done |
| 01_02_03 | Raw Schema DESCRIBE | .py + .ipynb | Artifacts on disk; ipynb has 4/5 outputs | Yes | Yes | Partial |
| 01_02_04 | Univariate Census & Target Variable EDA | .py + .ipynb | Artifacts on disk (1143-line .md, 51KB .json, 7 plot PNGs); ipynb has 0 outputs | Yes (76 SQL blocks in .md, all with inline queries) | Yes (1e9 ns conversion from 01_02_01 finding; 0.001 threshold from EDA Manual §3.3) | Partial |

**01_02_03 Partial justification:** Missing required `report:` field in ROADMAP spec. No `.md` report artifact produced.

**01_02_04 Partial justification:** (a) Research log has no entry for 01_02_04. (b) ipynb has zero execution outputs. (c) **Artifact naming mismatch:** ROADMAP specifies `01_02_04_univariate_census.json` and `01_02_04_univariate_census.md` but actual files are `01_02_04_univariate_eda.json` and `01_02_04_univariate_eda.md`. The gate `artifact_check` condition as written would fail.

### 3.2 Pipeline Section Coverage

| Pipeline Section | Name | Steps Defined | Done | Partial | Missing | Section Exit Met? |
|---|---|---|---|---|---|---|
| 01_01 | Data Acquisition & Source Inventory | 2 | 2 | 0 | 0 | **Partially met.** Inventory and schema done. No formal Datasheet/Data Card. |
| 01_02 | Exploratory Data Analysis (Tukey-style) | 4 | 2 | 2 | 0 | **Partially met.** Univariate layer done. Bivariate and multivariate not started. |
| 01_03 | Systematic Data Profiling | 0 | 0 | 0 | 0 | **Not met.** No steps defined. |
| 01_04 | Data Cleaning | 0 | 0 | 0 | 0 | **Not met.** No steps defined. |
| 01_05 | Temporal & Panel EDA | 0 | 0 | 0 | 0 | **Not met.** No steps defined. |
| 01_06 | Decision Gates | 0 | 0 | 0 | 0 | **Not met.** No steps defined. |

### 3.3 Manual-Level Gap Analysis

| Sub-arc | Status | Notes |
|---|---|---|
| **Source inventory (Datasheets/Data Cards)** | Partial | Weekly dump provenance documented in ROADMAP header. File inventory and schema discovery complete. No formal Datasheet or Data Card. |
| **Column-level profiling** | Partial | NULL census covers all 18 matches_raw and 14 players_raw columns. Cardinality, descriptive stats, zero counts for numeric fields. Target variable (winner) profiled. No formal outlier flagging or pattern analysis. |
| **Dataset-level profiling** | Partial | Row counts established. Temporal coverage (2022-2026) established. Class balance profiled. Join integrity assessed. No duplicate detection, no completeness matrix, no correlation matrix. |
| **EDA layers** | Partial | **Univariate:** Done. **Bivariate:** Not started. **Multivariate:** Not started. |
| **Cleaning & validation** | Not started | No cleaning rules. Raw data immutability respected. No staging layer. |

### 3.4 Invariant Violations Observed

| # | File | Description |
|---|---|---|
| 6 | `STEP_STATUS.yaml` (01_02_04 marked complete) vs `research_log.md` (no entry) | Step marked complete without research log entry. |
| — | `ROADMAP.md` 01_02_04 step spec | Gate `artifact_check` references `01_02_04_univariate_census.json`/`.md` but actual artifacts are named `01_02_04_univariate_eda.json`/`.md`. |
| — | `ROADMAP.md` 01_02_03 step spec | Missing required `report:` field per step template. |

### 3.5 Distance-to-Phase-Completion Summary

**Verdict: Phase 01 partially complete.**

Remaining items in dependency order:

1. Fix artifact naming: either rename files to match ROADMAP spec or update ROADMAP to match actual names.
2. Add research log entry for 01_02_04.
3. Add `report:` field to 01_02_03 step spec or produce the `.md` artifact.
4. Re-execute 01_02_04 notebook to embed outputs in ipynb.
5. Define and execute bivariate EDA step(s) under 01_02.
6. Define and execute multivariate EDA step(s) under 01_02.
7. Define and execute 01_03 steps (formal profiling).
8. Define and execute 01_04 steps (cleaning registry, rules, validation).
9. Define and execute 01_05 steps (temporal/panel EDA).
10. Define and execute 01_06 steps (decision gates, go/no-go).

**Hard blockers:** None. Raw data acquired. All 3 DuckDB tables populated.

---

## Cross-Dataset Summary

| Dataset | Verdict | Remaining Items |
|---|---|---|
| sc2egset | Phase 01 partially complete | 9 |
| aoe2companion | Phase 01 partially complete | 10 |
| aoestats | Phase 01 partially complete | 10 |

All three datasets are at the same structural position: Pipeline Sections 01_01 and 01_02 have defined steps, all marked complete (with caveats for 01_02_03 and 01_02_04). Pipeline Sections 01_03 through 01_06 have no steps defined.

---

## Appendix A: Common Issues Across All Datasets

These issues apply identically to all three datasets and are not repeated in per-dataset sections.

### A.1 ipynb Execution Outputs

The jupytext configuration (`sandbox/jupytext.toml`) pairs `.py:percent` with `.ipynb`. When `.py` files are synced to `.ipynb`, outputs are not preserved. This means most `.ipynb` files show zero outputs even when artifacts exist on disk. **Impact:** The ipynb files cannot serve as standalone audit trails. The artifacts (`.json`, `.md`, `.png`) are the actual evidence of execution.

**Assessment:** This is not an invariant violation but is a methodological weakness for thesis audit purposes. The executed code lives in `.py` files; the results live in artifact files; the `.ipynb` files connect neither.

### A.2 Pipeline Section Scope

Phase 01 has 6 Pipeline Sections per `docs/PHASES.md`. Only 2 of 6 have any defined steps. The remaining 4 (01_03 Systematic Data Profiling, 01_04 Data Cleaning, 01_05 Temporal & Panel EDA, 01_06 Decision Gates) have no ROADMAP entries. This is the dominant gap — the existing work covers acquisition and early EDA but none of the profiling, cleaning, temporal/panel, or decision-gate work required by the methodology manual.

### A.3 Research Log Completeness

All three datasets have research log entries for steps 01_01_01 through 01_02_03. None have an entry for 01_02_04 despite STEP_STATUS marking it complete. Per `docs/TAXONOMY.md`, every step must produce a research log entry on completion. This is a step-contract violation across all three datasets.

### A.4 Step Template Compliance

All three datasets' 01_02_03 step specs omit the `report:` output field, which is marked `required: true` in `docs/templates/step_template.yaml`. The step produces a `.json` artifact and schema YAML files but no `.md` report.
