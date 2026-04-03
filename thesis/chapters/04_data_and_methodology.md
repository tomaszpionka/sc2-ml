# Chapter 4 — Data and Methodology

## 4.1 Datasets

### 4.1.1 SC2EGSet (StarCraft II)

<!--
Citation: Białecki et al. 2023, Scientific Data, v2.1.0 (Zenodo: 17829625).
Corpus size, tournament count, date range, replay structure.
Data quality: parse coverage, duration distribution, APM/MMR findings.

DRAFTABLE — Phase 0 complete, full stats after Phase 1.
-->

### 4.1.2 AoE2 match data

<!--
aoestats.io, match metadata structure, Elo, limitations.
BLOCKED — AoE2 roadmap.
-->

### 4.1.3 Data asymmetry acknowledgement

<!--
SC2: in-game time series + pre-game metadata.
AoE2: pre-game metadata only.
Common comparison uses pre-game features only.
BLOCKED — both datasets needed.
-->

## 4.2 Data preprocessing

### 4.2.1 Ingestion and validation

<!--
Two-path pipeline, canonical replay_id, join validation.
DRAFTABLE — Phase 0 complete.
-->

### 4.2.2 Player identity resolution

<!--
Toon fragmentation, nickname as canonical ID, multi-toon classification.
Player coverage stats, cold-start players.
BLOCKED — Phase 2.
-->

### 4.2.3 Cleaning rules and valid corpus

<!--
Each exclusion rule with empirical motivation. Duration threshold derivation.
Cleaning impact quantification.
BLOCKED — Phase 6.
-->

## 4.3 Feature engineering

### 4.3.1 Common pre-game feature set (both games)

<!--
Elo/Glicko-2, rolling win rate, activity, H2H, tournament momentum, career stats.
Symmetric formulation: focal_player + opponent + context.
BLOCKED — Phase 7.
-->

### 4.3.2 SC2-specific in-game features

<!--
PlayerStats fields at canonical timepoints, separability analysis.
BLOCKED — Phase 4.
-->

### 4.3.3 AoE2-specific features

<!--
Civilisation pick, map type, Elo-derived.
BLOCKED — AoE2 roadmap.
-->

## 4.4 Experimental protocol

### 4.4.1 Train/validation/test split strategy

<!--
Per-player temporal split. Why per-game splits cause leakage.
Comparison with naïve global split.
BLOCKED — Phase 8.
-->

### 4.4.2 Model configurations

<!--
LR, RF, LightGBM/XGBoost, Elo/Glicko baseline. Neural nets if used.
BLOCKED — Phase 9–10.
-->

### 4.4.3 Hyperparameter tuning protocol

<!--
Validation-set-based, no test set peeking.
BLOCKED — Phase 10.
-->

### 4.4.4 Evaluation metrics

<!--
Accuracy, log-loss, ROC-AUC, calibration, per-matchup, cold-start strata.
Friedman + Nemenyi for cross-game comparison.
SKELETON — can draft from literature.
-->
