# SC2 Match Prediction — Distilled Methodology Plan

> **Scope:** This document covers the StarCraft II portion of the thesis only, based on the SC2EGSet dataset. It is intended as an actionable specification for implementation. The AoE2 portion will follow separately; however, the feature taxonomy and evaluation protocol here are designed to be portable to AoE2 with minimal structural changes.

---

## 1. Research Questions

The SC2 experiments answer three explicit research questions:

**RQ1 — Pre-match ceiling:** How accurately can match outcome be predicted from pre-match information alone, and how much do engineered features improve over a pure Elo baseline?

**RQ2 — In-game crossover point:** At what point during a game does in-game state information outperform the best pre-match model?

**RQ3 — Tournament-aware adaptation:** Does incrementally updating player features within a tournament (sequential prediction) improve accuracy over a static temporal split?

Every experiment, model, and ablation should map back to one of these three questions.

---

## 2. Data & Pipeline Architecture

### 2.1 Source
SC2EGSet (Białecki et al., Nature Scientific Data 2023): ~17,930 professional esport replays, 55 tournament replaypacks, 2016–present.

### 2.2 Hardware Constraints
Target machine: MacBook Pro M4 Max, 36 GB RAM, Apple MPS for PyTorch acceleration. All pipeline stages and model training must run locally on this hardware.

**Key implication:** The raw SC2EGSet nested JSONs total ~200 GB. The pre-match DuckDB (existing, without in-game events) is ~200 MB. Neither the full 200 GB nor even a large fraction of it should ever be loaded into memory at once. The pipeline is designed around a one-time streaming extraction that produces a compact DuckDB database suitable for all downstream work.

### 2.3 Ingestion Paths

Two parallel ingestion paths feed into a single DuckDB database:

**Path A — Pre-match features (currently implemented):**
Extracts per-player metadata from replay JSON headers: player name, race, SQ, APM, MMR, league, start location, result. Augmented with map metadata and tournament context from file paths and `details.timeUTC`. Already stored in the existing DuckDB.

**Path B — In-game time-series (to be implemented):**
New ingestion path preserving `trackerEvents` and `gameEvents` from each replay. This is the main new engineering effort.

### 2.4 In-Game Data Pipeline (Path B) — Detailed Specification

The pipeline has three stages. **Stage 1 is the critical bottleneck** — it processes 200 GB of raw data into ~1–2 GB of structured DuckDB tables. Stages 2 and 3 operate entirely in-memory.

```
Stage 1: Extraction (one-time, offline)
    Raw JSON files (200 GB on disk, external/SSD)
    → Python script processes ONE replay file at a time
    → Extract trackerEvents (PlayerStats, UnitBorn/Died, Upgrades)
    → Extract gameEvents (Cmd, CameraUpdate, SelectionDelta, ControlGroupUpdate)
    → Compute per-timestep features (see Section 3.2)
    → INSERT rows into DuckDB table: in_game_features
    → Repeat for next file

Stage 2: Query & Split (per experiment run)
    DuckDB query joins in_game_features with pre-match metadata
    → Filter by temporal split (train/val/test)
    → Slice by game progress for early prediction experiments
    → Return as pandas DataFrame or numpy array

Stage 3: Tensor Materialization (once per training run)
    DataFrame → pivot to [batch, timesteps, features] shape
    → Convert to PyTorch tensors
    → Entire training set lives in RAM (~850 MB)
    → Train with MPS acceleration, batch size 64–128
```

#### Stage 1 Implementation Notes

**Processing model:** Stream raw JSONs one at a time. Never load more than one replay (~3 MB) into memory simultaneously. This makes 200 GB irrelevant from a RAM perspective.

**Parallelism:** Each replay is independent. Use Python multiprocessing with 8–10 workers on M4 Max. Expected total extraction time: a few hours for the full dataset.

**Event extraction logic per replay:**

1. Walk `trackerEvents` array. For events where `_event == "NNet.Replay.Tracker.SPlayerStatsEvent"`, extract the 39 economic fields and key on `(match_id, _gameloop, m_playerId)`.
2. For `UnitBorn`, `UnitDied`, `UnitInit`, `UnitDone` events, maintain a running unit count per type per player. At each PlayerStats snapshot gameloop, record the current army composition as additional columns.
3. For `UpgradeCompleteEvent`, record tech milestones as binary flags at the corresponding gameloop.
4. Walk `gameEvents` array. Bin `Cmd`, `CameraUpdate`, `SelectionDelta`, `ControlGroupUpdate` events into ~160-gameloop windows aligned with PlayerStats snapshots. Compute: action count (APM proxy), camera movement distance, unique screen regions visited, control group switch count.
5. Write one row per `(match_id, game_loop, player_id)` with all computed features.

**DuckDB target schema:**

```sql
CREATE TABLE in_game_features (
    match_id        VARCHAR NOT NULL,
    game_loop       INTEGER NOT NULL,
    player_id       TINYINT NOT NULL,  -- 1 or 2
    -- PlayerStats economic fields (from trackerEvents)
    minerals_current          FLOAT,
    vespene_current           FLOAT,
    minerals_collection_rate  FLOAT,
    vespene_collection_rate   FLOAT,
    workers_active_count      FLOAT,
    minerals_used_in_progress FLOAT,
    minerals_used_current_army FLOAT,
    minerals_killed_army      FLOAT,
    minerals_lost_army        FLOAT,
    -- ... (remaining ~30 PlayerStats fields)
    -- Derived features
    army_supply               FLOAT,
    army_value_minerals       FLOAT,
    army_value_gas             FLOAT,
    -- Army composition (unit counts per type, or top-N most common)
    -- Action features (binned from gameEvents)
    actions_per_window        FLOAT,
    camera_move_distance      FLOAT,
    screen_regions_visited    INTEGER,
    control_group_switches    INTEGER,
    -- Tech flags
    -- ...
    PRIMARY KEY (match_id, game_loop, player_id)
);
```

**Size estimate:** ~22K matches × ~97 timesteps × 2 players × ~80 feature columns × 4 bytes ≈ 1.4 GB raw. DuckDB with columnar compression: ~500 MB–1 GB on disk.

#### Why DuckDB (not raw Parquet or HDF5)

1. **Consistency:** Pre-match data already lives in DuckDB. One tool, one query language for the entire project.
2. **Analytical queries during development:** "Show me average army value differential at the 5-minute mark for PvZ" is a SQL query, not a pandas script.
3. **Joins:** Linking in-game features to pre-match metadata (Elo, matchup, outcome) is a trivial `JOIN` on `match_id`.
4. **Early prediction slicing:** The early prediction curve experiment requires filtering `WHERE game_loop <= X` for various thresholds — DuckDB handles this instantly.
5. **Split management:** Train/val/test split membership can be stored as a column or a separate table, queryable with standard SQL.
6. **No network dependency:** DuckDB is an embedded database (single file), no server to manage.

#### Stage 3 — Tensor Shape for Model Training

For a given data split and game-progress cutoff, the final tensor shape is:

```
X_ingame: [N_matches, T_max, 2 * F]    # padded/truncated to T_max timesteps
X_prematch: [N_matches, P]               # P pre-match features
y: [N_matches, 1]                        # binary outcome
```

Where `2 * F` means both players' features are concatenated per timestep (or differenced — both representations should be tested). `T_max` is set per experiment: for full-game evaluation T_max ≈ 97; for early prediction at 30%, T_max ≈ 29.

Matches shorter than T_max are padded with zeros and a binary mask tensor is provided for the model to ignore padded timesteps. Matches longer than T_max are truncated.

### 2.5 Combined Storage Summary

| Component | Size on disk | Size in RAM | Location |
|-----------|-------------|-------------|----------|
| Raw SC2EGSet JSONs | ~200 GB | Never loaded fully | External drive / SSD |
| Pre-match DuckDB (existing) | ~200 MB | Trivial | Project directory |
| In-game DuckDB (new, Path B) | ~500 MB–1 GB | Trivial for queries | Project directory |
| Materialized training tensors | N/A (in-memory only) | ~850 MB | RAM during training |
| PyTorch model + optimizer state | Negligible | ~50–200 MB | RAM during training |
| **Total RAM during training** | | **~1.5–2 GB** | Well within 36 GB |

---

## 3. Feature Engineering

### 3.1 Pre-match Features (Variant 1)

Features are organized in **groups** for ablation. Each group is added incrementally to measure marginal lift using a single reference model (LightGBM with defaults) before any model comparison begins.

| Group | Features | Status |
|-------|----------|--------|
| **A: Elo** | Dynamic K-factor Elo, Elo difference, expected win prob | Exists |
| **B: Historical aggregates** | Bayesian-smoothed winrates, cumulative APM/SQ means, stat variance (std dev of APM/SQ) | Partially exists |
| **C: Matchup & map** | Race matchup winrates, map × race interaction winrates, spawn distance | Partially exists |
| **D: Form & momentum** | Win/loss streak, recency-weighted stats (EMA over APM/SQ/winrate), activity level (matches in last 7/30 days), head-to-head record | New |
| **E: Context** | Patch features (from `data_build`), tournament stage, best-of-N series position | New |

**Critical constraint:** Every feature must be computed using only data strictly preceding the match being predicted. All cumulative statistics are computed via expanding-window aggregation on temporally sorted data.

### 3.2 In-game Features (Variant 2)

**Step 1 — PlayerStats alignment:**
Join both players' `PlayerStats` snapshots by `(match_id, game_loop)` → tensor `[T, 2×F]`, where T ≈ 97 timesteps (one per ~6.7s), F ≈ 39 economic fields per player.

**Step 2 — Derived features per timestep:**
- Resource differentials: minerals, vespene, army value, worker count
- Efficiency ratios: collection rate, spending efficiency
- Kill/death resource ratios
- Army composition: accumulated UnitBorn − UnitDied per unit type
- Unit diversity: Shannon entropy of army composition
- Tech tier flags: presence of key tech units as binary indicators

**Step 3 — Action features (from gameEvents, binned per ~160-loop window):**
- Real-time APM
- Camera movement distance / screen regions visited
- Control group switches

**Step 4 — Normalization:**
Per-feature z-score standardization using training set statistics only. Applied only to models that require it (neural networks). Tree-based models receive raw features.

### 3.3 Game-Agnostic Feature Taxonomy

To ensure the methodology ports to AoE2, features are organized under abstract categories:

| Category | SC2 Implementation | Future AoE2 Equivalent |
|----------|--------------------|------------------------|
| Player strength | Elo, MMR, historical winrate | Elo from aoe2.net, ladder rating |
| Faction/matchup | Race pair winrates (6 matchups) | Civilization pair winrates (~1000 matchups) |
| Economic trajectory | Mineral/gas collection rates, worker count | Wood/food/gold/stone rates, villager count |
| Military capacity | Army supply, army value, kill ratios | Population, military unit value, relics |
| Tech progression | Key tech buildings present | Age advancement timing (Dark→Imperial) |
| Action intensity | APM, camera moves | APM, command density |
| Context | Map, patch, tournament stage | Map type, patch, tournament stage |

---

## 4. Data Splitting & Leakage Controls

### 4.1 Primary Split: Temporal

```
[======= Train (80%) =======][=== Val (15%) ===][= Test (5%) =]
         ↑                          ↑                  ↑
    CV & training            HP selection         Final report
                                                  (used once)
```

Split by `match_time`. No shuffling. Train final models on Train+Val with best hyperparameters, evaluate on Test exactly once.

### 4.2 Temporal Cross-Validation (for model selection & HP tuning)

Expanding-window CV within the training portion:

```
Fold 1: Train [months 1–12]  → Val [months 13–15]
Fold 2: Train [months 1–15]  → Val [months 16–18]
Fold 3: Train [months 1–18]  → Val [months 19–21]
...
```

### 4.3 Leakage Prevention Rules

1. Both player perspectives of the same match always stay in the same split.
2. All games from the same best-of series stay in the same split (unless the experiment is explicitly sequential-within-series).
3. Historical aggregates (Elo, winrates, APM means) are computed using only prior matches — no look-ahead.
4. Normalization statistics are computed on training data only.
5. Map-race winrates, patch-specific stats, and all derived features follow the same temporal discipline.

### 4.4 Tournament-Aware Sequential Split (for RQ3)

For each tournament T in the evaluation set:

```
for each tournament T in evaluation set:
    sort T.matches by match_time → [m_1, ..., m_N]
    for k = 1 to N:
        features_k = update_features_incrementally(history ∪ {m_1, ..., m_{k-1}})
        ŷ_k = model.predict(features_k[m_k])
        record(ŷ_k, y_k)
        reveal m_k → update Elo, winrates, counts
```

The model is trained once on all pre-tournament history (not retrained per step). Only lightweight feature counters are updated incrementally. This mirrors realistic deployment: retrain rarely, update features live.

---

## 5. Models

### 5.1 Guiding Principle

Depth over breadth. Each model is included because it answers a specific question, not to fill a leaderboard. The thesis narrative flows from simple baselines → best pre-match model → temporal models → fusion.

### 5.2 Baselines (always reported, no tuning needed)

| Model | Purpose |
|-------|---------|
| **Majority class** | Sanity check (~50% if balanced after perspective duplication) |
| **Elo-only classifier** | `expected_win_prob > 0.5` — does any model beat a simple rating system? |
| **Logistic Regression on Elo diff** | Minimal statistical model — linear baseline |

### 5.3 Pre-match Models (RQ1)

| Model | Why this one | Scaling |
|-------|-------------|---------|
| **Logistic Regression** | Interpretable linear baseline; coefficient analysis | Yes (StandardScaler) |
| **LightGBM** | Fast, handles categoricals natively, strong defaults, primary workhorse for feature ablation | No |
| **XGBoost** | Industry standard gradient boosting; comparison with LightGBM to check robustness of results across implementations | No |

**Dropped from primary comparison:** Random Forest (strictly dominated by gradient boosting on tabular benchmarks — include only if a bagging-vs-boosting comparison is explicitly needed), HistGradientBoosting (redundant with LightGBM for thesis purposes).

**Optional / appendix-only:** FT-Transformer (interesting academic comparison of attention-based tabular DL vs. trees, but not core), stacking ensemble (diminishing returns, not a separate finding).

**GNN models (GATv2, Node2Vec, Temporal GNN):** Deprioritized. These are research-level efforts with high implementation cost and the player interaction graph from pre-match metadata alone is too sparse to justify the complexity. If time permits, a simple GATv2 on the player matchup graph can go in an appendix.

### 5.4 In-game Models (RQ2)

| Model | Architecture | What it tests |
|-------|-------------|---------------|
| **LSTM** | 2-layer bidirectional LSTM → attention pooling → MLP head | Primary temporal model. Does in-game time-series data beat pre-match features? Established workhorse for sequential esports prediction. |
| **TCN** | Dilated causal convolutions → global pooling → MLP head | Convolution vs. recurrence on game sequences. TCN is completely absent from esports prediction literature — this fills a genuine gap. |

**Why these two and not more:** LSTM is the best-evidenced architecture for esports sequential prediction. TCN is a principled non-recurrent alternative that has never been tested in this domain — the comparison is novel and clean. Adding a Transformer here is optional: it requires substantially more data to outperform LSTM/TCN on sequences of length ~97, and risks underperforming due to dataset size (~22K matches). If implemented, it goes in an appendix with appropriate caveats about sample size.

### 5.5 Fusion Model (combines RQ1 + RQ2)

| Model | Architecture | What it tests |
|-------|-------------|---------------|
| **Dual-stream** | Pre-match MLP stream + in-game LSTM/TCN stream → concatenation → MLP head | Are pre-match and in-game signals complementary, or does in-game subsume pre-match? |

This is the "best possible" model and provides an upper bound for the dataset.

### 5.6 Hyperparameter Tuning Protocol

1. Use temporal CV from Section 4.2 as the inner evaluation loop.
2. Tune only the top 2 pre-match models (likely LightGBM and XGBoost) and the 2 in-game models using **Optuna** (Bayesian optimization), 100–200 trials each.
3. Logistic Regression: tune only `C` and `penalty` — fast enough for grid search.
4. Neural models (LSTM, TCN): keep architectures small (≤2 layers, hidden dim ≤128) due to dataset size. Tune learning rate, dropout, weight decay. Use early stopping on validation loss.

---

## 6. Early Prediction Curve (Key Thesis Contribution)

This is the central experiment of the in-game analysis and the strongest thesis contribution.

### 6.1 Protocol

Evaluate each in-game model at multiple game progress checkpoints:

**Relative time:** 10%, 20%, 30%, 40%, 50%, 60%, 70%, 80%, 90%, 100% of total game length.

**Absolute time:** 2 min, 4 min, 6 min, 8 min, 10 min, 12 min, 15 min, 20 min.

Both are needed because 20% of a 9-minute game is very different from 20% of a 24-minute game.

### 6.2 What to Report

At each checkpoint, report: accuracy, AUC-ROC, Brier score. Plot all three as curves over game progress.

### 6.3 Interpretation Focus

- **0% (pre-match only):** baseline from Variant 1.
- **10–30%:** the critical range — when does in-game start outperforming pre-match?
- **50–70%:** where fight outcomes become visible, expect substantial lift.
- **90–100%:** near-certainty, reported as sanity check only, not a headline result.

The meaningful analysis lives in the 10–50% range. Late-game near-certainty is trivial and should be explicitly acknowledged as such.

---

## 7. Ablation Studies (Required, Not Optional)

### 7.1 Feature Group Ablations (Pre-match)

Using LightGBM with defaults as the fixed model:

1. Group A only (Elo)
2. A + B (+ historical aggregates)
3. A + B + C (+ matchup/map)
4. A + B + C + D (+ form/momentum)
5. A + B + C + D + E (+ context)

Report marginal lift at each step. Use permutation importance and SHAP to identify the most and least valuable individual features within the winning group combination.

### 7.2 Feature Group Ablations (In-game)

Using LSTM as the fixed model:

1. PlayerStats economic features only
2. + Resource differentials and ratios
3. + Army composition features
4. + Action features (APM, camera, control groups)

### 7.3 Signal Source Ablations

1. Pre-match features only (best pre-match model)
2. In-game features only (best in-game model)
3. Dual-stream fusion

This answers: *are the two information sources complementary or does in-game subsume pre-match?*

---

## 8. Interpretability & Error Analysis

### 8.1 SHAP Analysis

- **Global:** SHAP summary plots (beeswarm) for the best pre-match model to show overall feature importance and direction of effects.
- **Time-segmented:** For in-game models, compute SHAP at different game progress checkpoints. Show how feature importance shifts across game phases (e.g., economic features dominate early, army trade features dominate mid-game).
- **Per-matchup:** Compare SHAP profiles across the 6 race matchup types (TvZ, PvT, etc.) — do different features drive prediction in different matchups?

### 8.2 Error Analysis

Mandatory breakdown of model errors across these subgroups:

| Subgroup | Why it matters |
|----------|---------------|
| Mirror matchups (TvT, PvP, ZvZ) | Race advantage is absent — prediction relies purely on skill/form |
| Upsets (lower-Elo wins) | Are errors concentrated on upsets? |
| Short games (<8 min) | Rush/cheese — pre-match features may be more useful |
| Long games (>20 min) | Macro games — in-game features should dominate |
| Patch transitions | Games near patch boundaries — concept drift |
| Close Elo games (diff < 50) | Hardest to predict — where is the model's floor? |

### 8.3 What Not to Include

LIME is excluded from the primary analysis. SHAP provides theoretically stronger guarantees (consistency, local accuracy) and is sufficient for the thesis scope. Adding LIME would be redundant without adding insight, and recent empirical work (Boidot et al. 2023) shows SHAP explanations don't consistently outperform simpler approaches in esports contexts anyway. The goal is to use SHAP to understand the model, not to generate XAI artifacts for their own sake.

---

## 9. Evaluation Metrics

### 9.1 Primary Metrics (reported for every model)

| Metric | What it measures |
|--------|-----------------|
| **Accuracy** | Intuitive headline number |
| **AUC-ROC** | Threshold-invariant discrimination |
| **Brier score** | Calibration quality of predicted probabilities |
| **Log loss** | Penalizes confident wrong predictions heavily |

### 9.2 Calibration Curve

For the best model in each category (pre-match, in-game, fusion): plot predicted probability vs. observed win frequency in 10 bins. A well-calibrated 68% predictor is more valuable than an overconfident 70% one.

### 9.3 Confidence Intervals

Report 95% confidence intervals on all metrics. Use bootstrap resampling (1000 iterations) over test set predictions.

### 9.4 Statistical Comparison

- **McNemar's test** between pairs of models on the held-out test set (tests whether disagreements are symmetric). Use exact binomial version when disagreements < 25.
- **DeLong's test** on AUC-ROC differences.
- Report p-values. Do not claim model A outperforms model B based on 0.3% accuracy difference alone.

### 9.5 Per-matchup Breakdown

Report accuracy and AUC-ROC separately for each of the 6 matchup types (TvZ, TvP, TvT, PvZ, PvP, ZvZ). Also report for "veterans only" (players with ≥N prior matches in the dataset) to assess whether prediction quality depends on historical data availability.

### 9.6 Prediction Stability (for in-game models)

For a given match, the win probability trajectory over time should be smooth. Report the mean absolute change in predicted probability between consecutive timesteps. A model that swings wildly between 20% and 80% within 30 seconds is useless for live prediction regardless of final accuracy.

---

## 10. Patch / Concept Drift Experiment

One dedicated experiment on temporal robustness:

1. Train on older patches only.
2. Test on a held-out newer patch block.
3. Compare with the standard mixed-patch model.

This answers: *how quickly do models degrade when the game's balance changes?* Report accuracy drop as a function of patch distance. Even a negative result (no significant drift) is a finding worth reporting.

---

## 11. Threats to Validity

The thesis should explicitly acknowledge:

1. **Population bias:** Dataset covers professional esports only. Results do not transfer to ladder or amateur play.
2. **Hidden confounders:** Map pool, tournament format, player fatigue, and psychological factors are unobserved.
3. **Patch drift:** Balance patches change race winrates over time. Models trained on old patches may not generalize.
4. **Series dependence:** Games within a best-of series are not independent — players adapt strategies.
5. **Survivorship bias:** Famous players have more data; model may overfit to well-represented players.
6. **Full information:** SC2EGSet provides complete game state (both players' perspectives). Real-time prediction systems would only have access to one player's view (fog of war). Reported accuracies are upper bounds for real-world deployment.
7. **Dataset size:** ~22K matches is modest for deep learning. Architectures are kept small to mitigate overfitting, but results should be interpreted with this constraint in mind.

---

## 12. Implementation Priority

| Priority | Task | Effort | Maps to |
|----------|------|--------|---------|
| **P0** | Fix temporal CV, proper baselines (Elo-only, LR on Elo diff) | Low | RQ1 |
| **P0** | Feature group ablation (Groups A→E) with LightGBM | Low–Med | RQ1 |
| **P0** | Tune top 2 pre-match models (Optuna + temporal CV) | Med | RQ1 |
| **P1** | In-game data ingestion pipeline (Path B) | Med | RQ2 |
| **P1** | LSTM on PlayerStats time-series | Med | RQ2 |
| **P1** | TCN on PlayerStats time-series | Med | RQ2 |
| **P1** | Early prediction curve (relative + absolute) | Low–Med | RQ2 |
| **P2** | Dual-stream fusion model | Med–High | RQ1+RQ2 |
| **P2** | Tournament-aware sequential evaluation | Med | RQ3 |
| **P2** | SHAP analysis + error analysis | Med | Interpretability |
| **P3** | Patch drift experiment | Low | Robustness |
| **P3** | Prediction stability metrics | Low | Evaluation |
| **Appendix** | FT-Transformer on pre-match | Med | Academic interest |
| **Appendix** | Transformer on in-game series | High | Comparison |
| **Appendix** | Build order sequence model | Med | Novel but risky |

---

## 13. Expected Outputs

The SC2 portion of the thesis should produce:

1. **Feature importance ranking** showing which information matters most for pre-match prediction, with marginal lift per feature group.
2. **Model comparison table** with accuracy, AUC-ROC, Brier score, log loss, confidence intervals, and McNemar's p-values for all primary models.
3. **Early prediction curve** — the central figure — showing accuracy/AUC/Brier as a function of game progress for both relative and absolute time.
4. **Calibration curves** for the best model in each category.
5. **SHAP analysis** revealing which features drive prediction and how this changes over game time and across matchups.
6. **Error analysis** identifying where models fail (upsets, mirrors, patch transitions).
7. **Tournament sequential results** comparing static vs. adaptive feature updates.
8. **Patch drift analysis** quantifying temporal robustness.

Together, these answer not just "which model wins" but "what information becomes predictive, when, and why" — which is the thesis-quality question.
