# Research Log

Thesis: "A comparative analysis of methods for predicting game results in real-time strategy games, based on the examples of StarCraft II and Age of Empires II."

Reverse chronological entries. Each entry documents the reasoning and learning behind code changes — intended as source material for thesis writing.

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

**Resolution/Outcome:** Classical ML models achieve ~63-65% accuracy (Gradient Boosting best). Top features: historical win rate, experience differential, SQ differential. GNN pipeline functional with GATv2 edge classification. See `reports/09_run_mac.md` for detailed metrics.

**Thesis notes:** The ~63-65% accuracy on temporal splits provides a solid baseline for comparative analysis. The feature importance ranking (win rate > experience > mechanical skill) aligns with domain knowledge about RTS skill factors. MPS compatibility issues should be documented in the thesis as a practical consideration for reproducibility on Apple Silicon.
