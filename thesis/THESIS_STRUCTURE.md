# Thesis Structure

**Title:** "A comparative analysis of methods for predicting game results in real-time strategy games, based on the examples of StarCraft II and Age of Empires II."

**Degree:** Master of Science in Computer Science (Data Science specialisation)

**Estimated length:** 60–90 pages (excluding appendices)

---

## How to use this document

This file defines the thesis chapter structure, what each section should contain,
and which roadmap phases feed into each section. Claude Code should reference this
document to understand **where** each piece of analysis will appear in the final
thesis, ensuring that every phase artifact is produced with the right level of
detail and narrative framing for its target section.

Sections marked `[SC2]` are fed primarily by the SC2 roadmap phases (`src/rts_predict/sc2/reports/SC2_THESIS_ROADMAP.md`).
Sections marked `[AoE2]` will be fed by a future AoE2 roadmap (not yet written).
Sections marked `[CROSS]` synthesise findings from both games.

---

## Chapter 1 — Introduction (5–8 pp.)

### 1.1 Background and motivation
- Growth of esports as a domain for data science research
- Real-time strategy games as particularly rich prediction problems
  (imperfect information, asymmetric factions, complex decision trees)
- Practical applications: broadcasting, betting markets, coaching tools,
  AI agent evaluation

### 1.2 Problem statement
- Formal definition: given the pre-game context (player histories, matchup,
  map, tournament stage) for a 1v1 RTS match, predict the probability
  that a designated player wins
- Secondary problem: how does prediction accuracy change when in-game
  state snapshots are also available (SC2 only, due to AoE2 data limitations)?

### 1.3 Research questions
- **RQ1:** Which machine learning methods achieve the highest prediction accuracy
  for 1v1 match outcomes in StarCraft II and Age of Empires II?
- **RQ2:** Which categories of features (player skill history, matchup/faction
  balance, map context, in-game economy) contribute most to prediction accuracy?
- **RQ3:** To what extent do the best-performing methods and feature importance
  rankings generalise across the two games?
- **RQ4:** How does prediction accuracy change as a function of available
  player history (cold-start problem)?

### 1.4 Scope and limitations
- 1v1 matches only (no team games)
- Professional/ranked matches (not casual)
- SC2: full replay data with in-game state; AoE2: match metadata only
  (no in-game state reconstruction) — this asymmetry is acknowledged and
  handled by defining a common pre-game feature set
- Prediction is per-game, not per-tournament or per-series

### 1.5 Thesis outline
- Brief description of each subsequent chapter

**Fed by:** Background reading, literature review. No roadmap phase directly.

---

## Chapter 2 — Theoretical Background (15–20 pp.)

### 2.1 Real-time strategy games
- Definition and characteristics of the RTS genre
- Key mechanics: resource gathering, base building, unit production, combat,
  technology trees, fog of war
- Why RTS games are harder to predict than turn-based games
  (continuous decision-making, imperfect information, high action rate)

### 2.2 StarCraft II
- Game mechanics relevant to prediction: three asymmetric races (Terran,
  Protoss, Zerg), economy model (minerals/gas), supply system, build orders,
  map pool rotation, balance patches
- Competitive scene: WCS/ESL/DreamHack circuit, tournament formats (Bo3/Bo5),
  Aligulac rating system
- SC2 game engine timing: 16 game loops per game-second at Normal speed,
  22.4 game loops per real-time second at Faster (competitive) speed
  [cite: Blizzard s2client-proto; Vinyals et al. 2017; Liquipedia Game Speed]
- The replay file format: s2protocol, tracker events, game events

### 2.3 Age of Empires II
- Game mechanics: civilisation bonuses (45+ civilisations in Definitive Edition),
  age advancement (Dark → Feudal → Castle → Imperial), economy model (food/wood/
  gold/stone), map generation (random maps vs. fixed)
- Competitive scene: Red Bull Wololo, King of the Desert, ranked ladder on
  Steam/Xbox, Elo rating system
- Data availability: match metadata via aoestats.io API, recorded game parsing
  via mgz, absence of programmatic game-state reconstruction

### 2.4 Machine learning methods for binary classification
For each method, describe: mathematical formulation, assumptions, strengths,
weaknesses, hyperparameters, and interpretability.
- Logistic Regression
- Random Forests
- Gradient Boosted Decision Trees (XGBoost, LightGBM)
- Support Vector Machines (optional, if used)
- Neural networks: MLP, LSTM/GRU for sequential data, GNN for player graphs
  (brief introduction — details in methodology if used)

### 2.5 Player skill rating systems
- Elo (Elo 1978): logistic model, K-factor, expected score formula
- Glicko / Glicko-2 (Glickman 1999, 2001): rating deviation, volatility
- TrueSkill (Herbrich et al. 2006): Bayesian factor graphs
- Aligulac's race-matchup-specific Glicko variant for SC2
- How derived ratings serve as features in ML models

### 2.6 Evaluation metrics and statistical comparison
- Accuracy, log-loss, ROC-AUC, calibration (Brier score)
- Friedman test with Nemenyi post-hoc for comparing classifiers across
  multiple datasets [cite: Demšar 2006, JMLR]
- Critical difference diagrams

**Fed by:** Literature review. Some domain knowledge validated during
SC2 Phase 0–1 (game loop timing, APM/MMR findings).

---

## Chapter 3 — Related Work (8–12 pp.)

### 3.1 Outcome prediction in traditional sports
- Brief survey of Elo/Glicko in chess, football, tennis
- Transition to esports

### 3.2 StarCraft prediction literature
- Erickson & Buro (2014): logistic regression on BW replays
- Ravari et al. (2016): Random Forests, economic features dominant
- MSC dataset and GRU baselines (Wu et al. 2017)
- Baek & Kim (2022, PLOS ONE): 3D-ResNet, ~90% accuracy on TvP
- Khan et al. (2021): transformers outperform GRUs on MSC
- Lin et al. (2019): Neural Processes with uncertainty
- Tarassoli et al. (2024): fine-tuned Phi-2 for build order prediction
- EsportsBench (Thorrez 2024): Glicko-2 at 80.13% on Aligulac SC2 data

### 3.3 MOBA and other esports prediction
- Hodge et al. (2021): LightGBM on Dota 2, 85% at 5 min
- Yang et al.: 93.73% at 40 min in Dota 2
- Bahrololloomi et al. (2023): role-specific LoL prediction, 86%
- Common finding: accuracy increases monotonically with game time

### 3.4 Age of Empires II prediction
- Çetin Taş et al. (2023, IEEE): ML regression on AoE2 DE match results
- Community analyses (Xie, Voobly data; aoestats civilisation balance)
- Identification of research gap: no prior cross-game RTS comparison

### 3.5 Research gap and contribution
- No published work compares ML prediction methods across two different
  RTS games with different data availability
- This thesis fills that gap

**Fed by:** Literature search (already started in research report).

---

## Chapter 4 — Data and Methodology (20–25 pp.)

This is the largest chapter. It covers both games' data pipelines, feature
engineering, and the unified experimental protocol.

### 4.1 Datasets

#### 4.1.1 SC2EGSet (StarCraft II) `[SC2]`
- Citation: Białecki et al. (2023), Scientific Data, v2.1.0
  (Zenodo: https://zenodo.org/records/17829625)
- Corpus size, tournament count, date range, replay structure
- Data quality: parse coverage, missing events, duration distribution
- APM availability (2017+) and MMR unusability (systematic missingness)

**Fed by:** SC2 Phases 0–1 (audit, corpus inventory).

#### 4.1.2 AoE2 Match Data `[AoE2]`
- Source: aoestats.io API / Parquet dumps, match metadata structure
- Corpus size, date range, Elo distribution
- Data limitations: no in-game state, no replay-level game events
- Comparison with SC2 data richness — table of available fields

**Fed by:** AoE2 roadmap Phase 0 (future).

#### 4.1.3 Data asymmetry acknowledgement `[CROSS]`
- SC2: rich in-game time series (PlayerStats every ~7s) + pre-game metadata
- AoE2: pre-game metadata only (civilisation, map, Elo, match history)
- Consequence: the common comparison uses only pre-game features;
  SC2 in-game prediction is a bonus SC2-only experiment

### 4.2 Data preprocessing `[SC2]`

#### 4.2.1 Ingestion and validation
- Two-path pipeline (Path A: metadata, Path B: events)
- Canonical replay_id design and join validation

**Fed by:** SC2 Phase 0.

#### 4.2.2 Player identity resolution
- Toon fragmentation problem, nickname as canonical ID
- Multi-toon classification (server switch, rename, ambiguous)
- Player coverage: game count distribution, cold-start players

**Fed by:** SC2 Phase 2.

#### 4.2.3 Cleaning rules and valid corpus
- Each exclusion rule with its empirical motivation (table format)
- Data-driven duration threshold derivation (from Phase 1 distribution)
- Cleaning impact quantification

**Fed by:** SC2 Phase 6.

### 4.3 Feature engineering

#### 4.3.1 Common pre-game feature set (both games) `[CROSS]`
- Derived skill rating (Elo or Glicko-2, computed from match history)
- Rolling win rate (last N games, overall and vs. opponent faction)
- Activity features (games in last 30/90 days)
- Head-to-head record
- Within-tournament momentum (win/loss record in current event)
- Career summary statistics
- Faction/race matchup encoding
- Map encoding
- **Symmetric formulation:** features are computed identically for both
  player_a and player_b; model input is always
  (focal_player_features, opponent_features, context_features)

**Fed by:** SC2 Phase 7 (Group A), AoE2 feature engineering (future).

#### 4.3.2 SC2-specific in-game features (SC2 only) `[SC2]`
- PlayerStats economic fields at canonical timepoints
- Unit and upgrade event summaries
- Winner/loser separability analysis (Cohen's d ranking)

**Fed by:** SC2 Phases 4, 7 (Group B).

#### 4.3.3 AoE2-specific features `[AoE2]`
- Civilisation pick features, map type features
- Elo-derived features specific to AoE2 ladder structure

**Fed by:** AoE2 roadmap (future).

### 4.4 Experimental protocol

#### 4.4.1 Train/validation/test split strategy
- Per-player temporal split (last tournament = test, penultimate = val)
- Why per-game splits cause leakage in player-dependent prediction
- Comparison with naïve global temporal split

**Fed by:** SC2 Phase 8.

#### 4.4.2 Model configurations
- Logistic Regression: regularisation, feature scaling
- Random Forest: n_estimators, max_depth, min_samples_leaf
- LightGBM/XGBoost: learning rate, max_depth, num_leaves, regularisation
- Elo/Glicko-2 rating baseline: K-factor / RD tuning
- (If applicable) MLP, LSTM, GNN configurations

#### 4.4.3 Hyperparameter tuning protocol
- Validation-set-based selection, no test set peeking
- Grid or Bayesian search with cross-validation on training set

#### 4.4.4 Evaluation metrics
- Primary: accuracy, log-loss, ROC-AUC
- Secondary: calibration curve, per-matchup accuracy, cold-start stratification
- Cross-game comparison: Friedman test + critical difference diagram

**Fed by:** SC2 Phases 8–9, AoE2 equivalent phases (future).

---

## Chapter 5 — Experiments and Results (20–25 pp.)

### 5.1 StarCraft II results `[SC2]`

#### 5.1.1 Baselines
- Random (50%), race-matchup, recent form, head-to-head, Glicko-2 rating

#### 5.1.2 Pre-game prediction (Group A features)
- Model comparison table (LR, RF, LightGBM, etc.)
- Best model: accuracy, log-loss, AUC, calibration
- Feature importance (SHAP values or permutation importance)
- Feature ablation study

#### 5.1.3 In-game prediction (Group B features, SC2 only)
- Accuracy as a function of game time (snapshot at 1 min, 3 min, 5 min, etc.)
- Comparison with pre-game model
- Which in-game features add the most signal?

#### 5.1.4 Per-matchup and cold-start analysis
- ZvT, ZvP, TvP, mirrors
- Accuracy stratified by career history length

**Fed by:** SC2 Phases 9–10.

### 5.2 Age of Empires II results `[AoE2]`

#### 5.2.1 Baselines
- Random, civilisation-matchup, Elo-based

#### 5.2.2 Pre-game prediction
- Model comparison table (same methods as SC2)
- Feature importance
- Per-civilisation-matchup analysis

#### 5.2.3 Cold-start analysis
- Accuracy vs. match history length

**Fed by:** AoE2 roadmap phases (future).

### 5.3 Cross-game comparison `[CROSS]`

#### 5.3.1 Method ranking comparison
- Do the same methods rank in the same order for both games?
- Friedman test with Nemenyi post-hoc on matched method × game matrix
- Critical difference diagram

#### 5.3.2 Feature category importance comparison
- Which feature groups matter most in each game?
- Common patterns (e.g., skill rating features dominate both)
  vs. game-specific patterns (e.g., SC2 matchup features stronger
  due to rock-paper-scissors race asymmetry)

#### 5.3.3 Prediction difficulty comparison
- Overall accuracy ceiling in each game
- Cold-start curves overlaid
- Discussion of information asymmetry (SC2 has in-game data, AoE2 does not)

**Fed by:** Synthesis of SC2 Phases 9–10 and AoE2 equivalent phases.

---

## Chapter 6 — Discussion (8–12 pp.)

### 6.1 Interpretation of results
- Answers to RQ1–RQ4
- Why certain methods outperform others
- Why certain features matter more

### 6.2 Comparison with published literature
- How do our SC2 results compare to Baek & Kim (2022), MSC baselines,
  EsportsBench Glicko-2?
- How do AoE2 results compare to Çetin Taş et al. (2023)?

### 6.3 Generalisability assessment
- What transfers across games and what doesn't
- Implications for other RTS or esports titles

### 6.4 Practical implications
- Which approach should a broadcasting overlay use?
- Which approach should a coaching tool use?
- Minimum data requirements for useful prediction

### 6.5 Threats to validity
- Internal: data quality, identity resolution errors, timestamp precision
- External: professional-only data may not generalise to casual play
- Construct: win/loss is binary — doesn't capture game quality or closeness

**Fed by:** All previous chapters.

---

## Chapter 7 — Conclusions and Future Work (3–5 pp.)

### 7.1 Summary of contributions
- Cross-game RTS prediction comparison (novel)
- Feature importance analysis across two games
- Per-player temporal split methodology
- Open-source pipeline and reproducibility

### 7.2 Key findings
- Bullet summary of main results

### 7.3 Future work
- Transfer learning between games
- Sequence models (LSTM/Transformer) on SC2 time series
- AoE2 replay parsing for in-game features
- Extension to team games (AoE2 team games, SC2 Archon mode)
- Real-time prediction systems

**Fed by:** Reflection on all results.

---

## References

All citations use a consistent format (APA or IEEE, per university requirements).
Maintain a BibTeX file `references.bib` in the repository.

Key references to include (non-exhaustive):
- Białecki et al. (2023) — SC2EGSet, Scientific Data
- Vinyals et al. (2017) — SC2LE, arXiv:1708.04782
- Wu et al. (2017) — MSC dataset, arXiv:1710.03131
- Baek & Kim (2022) — 3D-ResNet SC2 prediction, PLOS ONE
- Khan et al. (2021) — Transformers on SC2, IEEE ICMLA
- Çetin Taş et al. (2023) — AoE2 DE ML prediction, IEEE
- Glickman (2001) — Glicko-2 rating system
- Herbrich et al. (2006) — TrueSkill, NeurIPS
- Demšar (2006) — Statistical comparisons of classifiers, JMLR
- Hodge et al. (2021) — Dota 2 prediction, IEEE Trans. Games

---

## Appendices

### Appendix A — Data acquisition and preprocessing infrastructure
- Pipeline architecture diagram
- DuckDB schema
- SC2 ingestion audit results (Phase 0 artifacts)
- AoE2 data collection methodology

### Appendix B — Complete feature lists
- Full feature specification tables (SC2 Group A, Group B, AoE2)
- Feature distributions and correlations

### Appendix C — Hyperparameter grids and tuning results
- Full grid search / Bayesian optimisation results

### Appendix D — Additional results tables
- Per-tournament results, per-year results, per-patch-era results
- Full SHAP summary plots

### Appendix E — Code repository
- Repository structure description
- How to reproduce all experiments
- Software versions and dependencies

---

## Phase-to-chapter mapping (quick reference)

| SC2 Roadmap Phase | Primary thesis section |
|---|---|
| Phase 0 — Ingestion audit | Appendix A |
| Phase 1 — Corpus inventory | §4.1.1 (SC2EGSet description) |
| Phase 2 — Player identity | §4.2.2 (Player identity resolution) |
| Phase 3 — Games table | §4.2, §4.4.1 (Temporal structure, split design) |
| Phase 4 — In-game profiling | §4.3.2 (SC2 in-game features) |
| Phase 5 — Map/meta-game | §4.3.1 (Control features), §5.1 context |
| Phase 6 — Cleaning | §4.2.3 (Cleaning rules) |
| Phase 7 — Feature engineering | §4.3 (Feature engineering) |
| Phase 8 — Split construction | §4.4.1 (Split strategy) |
| Phase 9 — Baselines | §5.1.1 (SC2 baselines) |
| Phase 10 — Models | §5.1.2–5.1.4 (SC2 results) |
