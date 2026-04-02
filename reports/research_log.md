# Research Log

Thesis: "A comparative analysis of methods for predicting game results in real-time strategy games, based on the examples of StarCraft II and Age of Empires II."

Reverse chronological entries. Each entry documents the reasoning and learning behind code changes — intended as source material for thesis writing.

---

## 2026-04-02 — Repository restructured into proper Python package

**Objective:** Reorganize flat 13-module codebase into a proper `src/sc2ml/` package layout to support maintainability, testability, and future AoE2 integration.

**Approach:** Adopted PyPA-recommended src layout with four subpackages (`data/`, `features/`, `models/`, `gnn/`). Renamed modules to avoid namespace redundancy. Updated all imports, fixed test infrastructure (removed `sys.path` hacks, created proper `conftest.py`), configured Poetry for package mode with CLI entry point. Archived legacy execution reports to `reports/archive/`.

**Issues encountered:**
- `conftest.py` is auto-loaded by pytest but not directly importable — required moving shared test utilities to `tests/helpers.py` instead.
- Pre-existing LightGBM segfault on Apple M4 Max during `test_model_reproducibility` (known MPS issue, unrelated to refactoring).
- Ruff identified pre-existing F821 errors from string type annotations — fixed with proper `TYPE_CHECKING` imports.

**Resolution/Outcome:** All 28 non-MPS tests pass. Ruff clean (1 pre-existing E501 in `test_mps.py`). Package installs correctly via `poetry install`. CLI entry point registered. Legacy reports preserved in `reports/archive/`.

**Thesis notes:** The src layout establishes the foundation for shared abstractions when AoE2 integration begins. The package structure makes it clear which components are game-specific (data ingestion, graph construction) vs. reusable (model evaluation, feature engineering patterns).

---

## 2026-04-02 — Project infrastructure setup for Claude Code collaboration

**Objective:** Establish structured development workflow with rich guidelines, git conventions, and documentation trail for thesis work.

**Approach:** Augmented CLAUDE.md with comprehensive sections covering permissions, coding standards, ML experiment protocol, and documentation requirements. Created CHANGELOG.md and this research log.

**Issues encountered:** None — greenfield setup.

**Resolution/Outcome:** Three-tier documentation system in place: CHANGELOG (code versioning), research log (thesis narrative), execution reports (raw pipeline output).

**Thesis notes:** This infrastructure supports the reproducibility and methodology documentation requirements of the thesis. The structured experiment protocol (hypothesis-first, temporal splits, baseline comparisons) will provide a clear audit trail for Chapter 3 (Methodology).

---

## 2026-03-30 — Baseline SC2 pipeline results on Apple M4 Max (summary of prior work)

**Objective:** Establish working end-to-end prediction pipeline for StarCraft II match outcomes using both classical ML and Graph Neural Networks.

**Approach:** Built 5-stage pipeline: data ingestion from SC2Replay JSON files into DuckDB, SQL-based feature views, custom ELO system with dynamic K-factor, Bayesian-smoothed feature engineering (45+ features), and three model training paths (classical ML, Node2Vec embeddings, GATv2 GNN).

**Issues encountered:**
- Apple M4 Max MPS backend causes silent failures and segfaults with sparse tensor operations in PyTorch Geometric. Workaround: force CPU for GNN training, set `PYTORCH_ENABLE_MPS_FALLBACK=1`.
- Data leakage risk from using current-match statistics (APM, SQ, supply_capped_pct) as features. Resolution: feature engineering uses only pre-match historical aggregates.
- `matches_flat` view produces 2 rows per match (both player perspectives) — intentional augmentation but requires careful handling in ELO computation (deduplicate via `processed_matches` set).

**Resolution/Outcome:** Classical ML models achieve ~63-65% accuracy (Gradient Boosting best). Top features: historical win rate, experience differential, SQ differential. GNN pipeline functional with GATv2 edge classification. See `reports/archive/09_run.md` for detailed metrics.

**Thesis notes:** The ~63-65% accuracy on temporal splits provides a solid baseline for comparative analysis. The feature importance ranking (win rate > experience > mechanical skill) aligns with domain knowledge about RTS skill factors. MPS compatibility issues should be documented in the thesis as a practical consideration for reproducibility on Apple Silicon.
