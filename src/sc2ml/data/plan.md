# SC2 Match Prediction: Data Analysis & Model Recommendations

## Raw Data Summary

Each SC2Replay JSON (~3MB) contains:
- **Pre-match metadata** (`ToonPlayerDescMap`): player name, race, SQ, APM, MMR, league, start location, result
- **trackerEvents** (~500 events): `PlayerStats` snapshots every ~6.7s (39 economic fields), `UnitBorn/Died/Init/Done` (unit lifecycle with position + type), `Upgrade`
- **gameEvents** (~9000 events): `Cmd` (player commands), `CameraUpdate`, `SelectionDelta`, `ControlGroupUpdate`
- **Match metadata**: map name/size, game version, duration (game loops)

Current pipeline **strips all in-game events** during ingestion and uses only pre-match historical aggregates → ~64.5% accuracy baseline.

---

## Variant 1: Pre-Match Only

### What We Have
45 features: ELO (dynamic K-factor), Bayesian-smoothed winrates, cumulative APM/SQ means, race matchup rates, spawn distance. Models: LR, RF, GBM, XGB, LGBM, GATv2 GNN, Node2Vec.

### What's Missing
| Feature | Source | Why It Matters |
|---------|--------|---------------|
| Win/loss streak | Match history | Momentum effects |
| Recency-weighted stats | EMA over APM/SQ/winrate | Recent form > lifetime average |
| Head-to-head record | Player pair lookup | Stylistic matchup advantages |
| Activity level | Matches in last 7/30 days | Rust vs. active form |
| Stat variance | Std dev of APM/SQ | Consistency signal |
| Map × race interaction | Historical winrate of race on map | Maps favor specific races |
| Patch features | `data_build` | Balance patches shift race winrates |

### Additional Models to Try
- **FT-Transformer** — attention-based tabular DL; tests if learned interactions beat manual feature diffs
- **Stacking ensemble** — combines LR+RF+XGB+GNN via meta-learner; tests model complementarity
- **Temporal GNN** (TGN) — nodes evolve over time; captures skill trajectory, not just snapshot

### Expected Ceiling
~67-70%. Even chess ELO achieves only ~65-70% for pro matches. SC2 is real-time and stochastic — pre-match prediction has hard limits.

---

## Variant 2: With In-Game Data

### Data Processing Pipeline Needed

```
Raw JSON → Event Extraction → Time-Series Alignment → Feature Engineering → Normalization → Model Input
```

**Step 1 — Event extraction:** New ingestion path preserving trackerEvents/gameEvents (currently stripped). Store as Parquet or DuckDB tables.

**Step 2 — PlayerStats alignment:** Both players' snapshots joined by `(match_id, loop)` → tensor `[T, 2×F]`, T≈97, F≈39.

**Step 3 — Derived features per timestep:**
- Resource differentials (minerals, vespene, army value, workers)
- Collection rate / spending efficiency ratios
- Kill/death resource ratios
- Army composition from accumulated UnitBorn - UnitDied per type
- Unit diversity (Shannon entropy), tech unit presence flags

**Step 4 — Action features** (from gameEvents, binned per ~160-loop window):
- Real-time APM, camera movement distance, screen regions visited, control group switches

**Step 5 — Normalization:** Per-feature standardization (training set stats only).

**Storage:** ~680MB for full dataset as float32 tensors (fits M4 Max RAM).

### Models

| Model | Architecture | Thesis Question It Answers |
|-------|-------------|---------------------------|
| **LSTM/GRU** | 2-layer bidir LSTM → attention pool → MLP | Does temporal in-game data beat pre-match features? |
| **TCN** | Dilated causal convolutions → global pool → MLP | Convolution vs. recurrence for game sequences? |
| **Transformer** | Encoder with positional encoding on game loops | Can attention identify critical game moments? |
| **Build order model** | Unit sequences as tokens → LSTM/Transformer | Do strategic decisions predict independently of execution? |
| **Dual-stream** | Pre-match MLP + in-game LSTM/Transformer → fusion → MLP | Are pre-match and in-game signals complementary? |

### Early Prediction Curve (Key Thesis Contribution)

Evaluate at 10%, 20%, ..., 100% of game length:
- **0%** → pre-match baseline (~64.5%)
- **20-30%** → in-game should start outperforming pre-match
- **50-70%** → substantially higher (fight outcomes visible)
- **100%** → near certainty

Answers: *"When during a game does the outcome become predictable?"*

---

## Implementation Priority

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| **1** | Additional pre-match features (streaks, recency, map-race) | Low | Moderate |
| **1** | LSTM on PlayerStats time-series | Moderate | High |
| **1** | Early prediction curve | Low | High (thesis) |
| **2** | FT-Transformer on pre-match | Moderate | Academic |
| **2** | Transformer on in-game series | High | Interpretability |
| **2** | Dual-stream fusion | High | Strongest comparison |
| **3** | Build order sequence model | Moderate | Novel |
| **3** | Temporal GNN | Very High | Research-level |
| **3** | Stacking ensemble | Low-Moderate | Diminishing returns |

## Evaluation Protocol

All models: accuracy (full + veterans-only), AUC-ROC, Brier score, per-matchup breakdown, computational cost. Variant 2 models: early prediction curve. Temporal split only (no shuffling).

## Key Risks

1. **Late-game triviality** — last 10% of game ≈ seeing result → focus analysis on 20-50% range
2. **Overfitting** — 22K samples with deep models → small architectures, heavy regularization
3. **Pre-match ceiling** — may already be near it → report ELO-only calibration as reference
4. **Patch heterogeneity** — balance changes across data → per-patch analysis

---

## Classical ML Methodology: Critique & Corrected Approach

### Problems with Current Implementation

The current pipeline (`classical.py`, `tuning.py`) has several methodological issues that undermine the validity of comparisons:

**1. No proper model selection — just "try everything with arbitrary hyperparameters"**
All 5 models use hardcoded hyperparameters from `config.py` (RF: 200 trees, depth 8; XGB/LGBM: 200 estimators, depth 6; HGB: 200 iters, lr 0.05). These were not derived from any tuning process — they're default-ish values. Comparing models at arbitrary hyperparameters tells you nothing about which *algorithm* is better; it tells you which *specific configuration* happened to work, which is not a valid thesis finding.

**2. Tuning exists only for Random Forest, and uses standard k-fold CV**
`tuning.py` runs `RandomizedSearchCV` with 5-fold CV on RF only. Standard k-fold **violates temporal ordering** — folds mix future and past data, causing leakage. For time-ordered match data, this inflates CV scores and selects hyperparameters that overfit to temporal patterns. None of the other 4 models get any tuning at all.

**3. Single train/test split with no validation set**
The pipeline does a single 95/5 temporal split and reports test accuracy. There is no validation set for model selection or hyperparameter tuning. The test set is effectively used for both selection and evaluation, which biases reported results upward.

**4. Unnecessary preprocessing for tree-based models**
`StandardScaler` is applied to all models including RF, XGBoost, LightGBM, and HistGradientBoosting. Tree-based models are invariant to monotonic feature transformations — scaling does nothing except add computational overhead. Only Logistic Regression benefits from scaling.

**5. No statistical significance testing**
Accuracy differences of 0.1-0.5% between models are reported as meaningful, but with ~8,900 test samples, the confidence interval on accuracy is roughly ±1%. Without significance testing (e.g., McNemar's test or DeLong's test on AUC), we cannot claim one model outperforms another.

### Corrected Methodology

The proper order for classical ML experimentation is:

```
Step 1: Baseline & data understanding
    ↓
Step 2: Feature engineering (iterative)
    ↓
Step 3: Model selection via temporal CV
    ↓
Step 4: Hyperparameter optimization (top candidates only)
    ↓
Step 5: Final evaluation on held-out test set
    ↓
Step 6: Statistical comparison & reporting
```

#### Step 1: Establish a Proper Baseline

Before touching any model, establish reference points:

- **Naive baseline**: majority class accuracy (should be ~50% if data is balanced after perspective duplication)
- **ELO-only baseline**: `expected_win_prob > 0.5` as a classifier — this is the "does any model beat a simple rating system?" benchmark
- **Single-feature LR**: logistic regression on `elo_diff` alone — the minimal statistical model

These baselines frame the entire analysis. If XGBoost with 45 features only beats ELO-only by 1-2%, that's itself a thesis finding (feature engineering adds little beyond skill rating).

#### Step 2: Feature Engineering First, Then Model

Features matter more than model choice for tabular data (see Grinsztajn et al., 2022). The correct order:

1. Start with a **single robust model** (LightGBM with defaults is a good choice — fast, handles missing values, reasonable out-of-box performance)
2. Add feature groups incrementally, measuring lift with each group:
   - Group A: ELO features only
   - Group B: + historical aggregates (APM, SQ, winrate)
   - Group C: + race matchup features
   - Group D: + map/spatial features
   - Group E: + new features (streaks, recency, head-to-head)
3. Use **feature importance** and **permutation importance** to prune low-value features
4. Only after the feature set is stable, proceed to model comparison

This tells you *which information matters*, which is far more valuable for a thesis than *which algorithm is 0.3% better*.

#### Step 3: Temporal Cross-Validation for Model Selection

Replace standard k-fold with **TimeSeriesSplit** or a custom expanding-window CV:

```
Window 1: Train [month 1-12]  → Validate [month 13-15]
Window 2: Train [month 1-15]  → Validate [month 16-18]
Window 3: Train [month 1-18]  → Validate [month 19-21]
...
```

This respects temporal ordering and tests whether models generalize to future data. Use this for:
- Comparing algorithms (LR vs. RF vs. XGB vs. LGBM vs. HGB) with default hyperparameters
- The mean ± std CV score across folds determines which algorithms are worth tuning

**Only tune the top 2-3 algorithms** — tuning all 5 is wasted compute if 2 of them are clearly worse.

#### Step 4: Hyperparameter Optimization (Top Candidates Only)

For the 2-3 best algorithms from Step 3:

- Use **Optuna** (Bayesian optimization) instead of `RandomizedSearchCV` — it's more sample-efficient and handles the temporal CV constraint naturally
- Define search spaces per algorithm:
  - **LightGBM**: `num_leaves` (20-100), `learning_rate` (0.01-0.3), `min_child_samples` (5-50), `reg_alpha` (0-1), `reg_lambda` (0-1), `subsample` (0.6-1.0)
  - **XGBoost**: `max_depth` (3-10), `learning_rate` (0.01-0.3), `min_child_weight` (1-20), `gamma` (0-1), `subsample` (0.6-1.0), `colsample_bytree` (0.5-1.0)
  - **Logistic Regression** (if competitive): `C` (0.001-100), `penalty` (l1/l2/elasticnet)
- Use the **same temporal CV** from Step 3 as the inner loop
- Budget: 100-200 trials per algorithm (Optuna converges much faster than random search)

#### Step 5: Final Evaluation (Held-Out Test Set, Used Once)

Split the data into three temporal segments:

```
[=== Train (80%) ===][== Val (15%) ==][= Test (5%) =]
         ↑                    ↑                ↑
    CV & training     HP selection      Final report
```

- Train final models on Train+Val with best hyperparameters from Step 4
- Evaluate on Test **exactly once** — no iterating on test results
- Report: accuracy, AUC-ROC, Brier score, per-matchup breakdown, veterans-only

#### Step 6: Statistical Comparison

- **McNemar's test** between pairs of models (tests if disagreements are symmetric)
- **DeLong's test** on AUC-ROC differences
- **Calibration curves** — is a model's predicted probability of 70% actually correct 70% of the time?
- **Learning curves** — accuracy vs. training set size (is more data likely to help?)
- Report confidence intervals, not just point estimates

### Corrected Model Set

| Model | Scaling Needed | Why Include |
|-------|---------------|-------------|
| **Logistic Regression** | Yes (StandardScaler) | Linear baseline; interpretable coefficients |
| **LightGBM** | No | Fast, handles categoricals natively, strong default performance |
| **XGBoost** | No | Industry standard; comparison with LightGBM |
| **HistGradientBoosting** | No | Sklearn-native alternative; good with missing values |

**Drop Random Forest** from the primary comparison — it's strictly dominated by gradient boosting methods on tabular data in virtually all benchmarks. Keep it only if thesis requires a "bagging vs. boosting" comparison.

**Drop StandardScaler** from tree-based model pipelines — it adds nothing and muddies the methodology.

### What This Changes in Implementation

| File | Change |
|------|--------|
| `classical.py` | Remove StandardScaler from tree pipelines; add temporal CV; add McNemar's test; add calibration curves |
| `tuning.py` | Replace RandomizedSearchCV with Optuna; use temporal CV; extend to all top models |
| `config.py` | Remove hardcoded model hyperparameters (they'll come from tuning); add CV/split config |
| `engineering.py` | Add incremental feature group evaluation loop |
| `cli.py` | Restructure to run baseline → features → selection → tuning → evaluation sequentially |

---

## Appendix A: Map Translation Reference Data

The file `data/samples/raw/map_foreign_to_english_mapping.json` ships with the repository as sample/reference data. It contains **1,488 entries** mapping localized SC2 map names to **215 canonical English names**. SC2 replays record map names in the client's display language, so the same map appears under different keys depending on the server region.

| Language Group | Example (foreign → English) |
|----------------|---------------------------|
| English (identity) | `16-Bit LE` → `16-Bit LE` |
| Korean | `16비트 - 래더` → `16-Bit LE` |
| Chinese (Simplified + Traditional) | `16位-天梯版` → `16-Bit LE` |
| Russian | `16 бит РВ` → `16-Bit LE` |
| Spanish / French / German / Portuguese / Polish / Italian | `16 bits EC` → `16-Bit LE` |

**Pipeline usage.** `load_map_translations()` in `ingestion.py` scans all `*map_foreign_to_english_mapping.json` files under the replays source directory, merges them into a single DuckDB `map_translation` table. The `flat_players` view in `processing.py` LEFT JOINs this table:

```sql
COALESCE(mt.english_name, metadata->>'$.mapName') AS map_name
```

This ensures map-based features (map area, spawn distance, future map-race winrate features) are computed over canonical map identities regardless of the client language that recorded the replay. For planned features like map-race interaction winrates (Variant 1 "What's Missing"), consistent map identities are a prerequisite.

---

## Appendix B: Tournament-Aware Sequential Prediction Split

### B.1 Motivation

The current pipeline uses a single bulk temporal split (95/5 or 80/15/5 as proposed in the corrected methodology). This is appropriate for general chronological integrity but does not capture a key structural property of the data: **matches within a tournament happen in sequence, and later matches are conditioned on earlier results**.

Three properties of professional tournament data make bulk splitting insufficient:

1. **Bracket selection bias.** In elimination brackets, later-round opponents are winners of earlier rounds — they are systematically stronger (or at least hotter) than average. A model trained on the full historical distribution faces a non-stationary test distribution within a single tournament.

2. **Within-tournament information accumulation.** An analyst predicting match 9 of a tournament knows the outcomes of matches 1–8. Player form, confidence, fatigue, and strategic adaptation (e.g., a player's build order was scouted in game 5) are all tournament-local signals. The bulk split discards this sequential structure.

3. **Realistic evaluation protocol.** In practice, predictions are made one game at a time. Evaluating on a static block of future games conflates "can the model predict at all" with "can the model adapt to emerging information." The sequential split isolates the second question.

### B.2 Formal Definition

Let tournament T contain matches m_1, m_2, ..., m_N ordered by `match_time`. Let H denote all historical data prior to tournament T.

For each prediction target m_k (k = 1, ..., N):

| Component | Definition |
|-----------|-----------|
| **Historical training set** | H (all matches before tournament T begins) |
| **Tournament context** | {m_1, ..., m_{k-1}} — revealed results from current tournament |
| **Test instance** | m_k — single match to predict |
| **Feature state** | ELO ratings, winrates, and all cumulative features updated to include m_1, ..., m_{k-1} |

The model is evaluated on each m_k independently. After prediction, m_k's result is revealed and features are updated before predicting m_{k+1}.

**Pseudocode:**

```
for each tournament T in evaluation set:
    sort T.matches by match_time → [m_1, ..., m_N]
    for k = 1 to N:
        features_k = recompute_features(history ∪ {m_1, ..., m_{k-1}})
        ŷ_k = model.predict(features_k[m_k])
        record(ŷ_k, y_k)
        reveal m_k result → update ELO, winrates, counts
```

**Concrete example** (Bo5 semifinal bracket):

```
game  | p1      | p2      | p1_win | action
------+---------+---------+--------+------------------------------------------
  1   | Maru    | Serral  |   0    | known — update features
  2   | Reynor  | Clem    |   1    | known — update features
  3   | Stats   | Dark    |   1    | known — update features
  ...
  8   | Maru    | Reynor  |   1    | known — update features
  9   | Serral  | Stats   |  n/a   | PREDICT (games 10-11 not visible)
 10   | winner9 | Reynor  |  n/a   | PREDICT (game 9 result now revealed)
 11   | ...     | ...     |  n/a   | PREDICT (games 9-10 results now revealed)
```

### B.3 Evaluation Variants

| Variant | Training Data | Feature Updates | What It Tests |
|---------|--------------|----------------|---------------|
| **Within-tournament sequential** | Fixed historical H; model is not retrained | ELO + winrates updated after each revealed game | Can pre-trained model benefit from live feature updates? |
| **Cross-tournament sequential** | All tournaments before T; model retrained per-tournament | Full recomputation per step | Does training on more recent tournaments improve next-tournament prediction? |
| **Hybrid (recommended)** | Global model trained once on H | Lightweight feature updates only (ELO, game counts, winrates) | Practical deployment scenario — retrain rarely, update features live |

The **hybrid variant** is recommended as the primary evaluation protocol because it mirrors realistic deployment: the model is trained offline, but features are updated in real time as tournament results come in.

### B.4 Implementation Considerations

**Data requirements (already available):**
- `tournament_name`: extracted from file paths via `split_part(filename, '/', -3)` in `processing.py`
- `match_time`: parsed from `details.timeUTC` — provides intra-tournament ordering

**Feature recomputation cost per revealed game:**

| Operation | Cost | Approach |
|-----------|------|----------|
| ELO update | O(1) — two additions | Maintain live `elo_dict`, update after each reveal (mirrors existing `elo.py` pattern) |
| Bayesian winrate update | O(1) — increment numerator/denominator | Maintain per-player running sums |
| Historical mean APM/SQ | O(1) — running mean update | Maintain sum + count per player |
| Race-specific winrates | O(1) — increment by grouping key | Maintain per (player, race) and (player, vs_race) counters |
| Full `perform_feature_engineering` | O(N) — cumsum over full dataset | **Avoid.** Use incremental updates instead |

The current `engineering.py` uses Pandas `cumsum`/`cumcount` over the full dataframe, which recomputes everything from scratch. For the sequential split, an incremental update class should maintain dictionaries of running statistics — mirroring the structure already used in `elo.py`'s `elo_dict` and `games_played_dict`.

**Evaluation metric — accuracy curve across tournament progression:**

| Tournament Stage | Matches | Expected Behavior |
|-----------------|---------|------------------|
| Group stage / Round of 16 (early games) | Little tournament context | Model relies on historical features; accuracy ≈ bulk baseline |
| Quarterfinals (mid-tournament) | Some context accumulated | Feature updates begin to help; slight accuracy lift if model captures form |
| Semifinals + Finals (late games) | Strong selection bias toward top players | Harder to predict (top players are closer in skill); accuracy may drop |

Plotting accuracy as a function of tournament round number is a key thesis figure. It answers: *"Does within-tournament information improve prediction, or does bracket selection difficulty offset it?"*

**Sample size considerations:**
- Each tournament yields only ~8–16 test predictions (depending on format)
- Statistical power requires aggregating across many tournaments
- Report per-tournament accuracy distributions (box plots), not just the global mean
- Consider bootstrap confidence intervals over tournaments rather than over individual predictions

### B.5 Comparison with Existing Splits

| Property | Bulk Temporal Split (current) | Tournament-Aware Sequential |
|----------|------------------------------|---------------------------|
| Granularity | One cutoff date; all future matches are test | Per-match within each tournament |
| Feature freshness | Features frozen at cutoff | Features updated after each revealed result |
| Information available | Only pre-cutoff history | Pre-cutoff history + intra-tournament results |
| Evaluation realism | Offline batch evaluation | Online one-step-ahead evaluation |
| Statistical power | Large test set (~1K+ matches) | Small per-tournament (~8–16); needs aggregation |
| What it measures | Generalization to future time periods | Adaptation to within-event dynamics |
| Implementation cost | Trivial (single index split) | Moderate (incremental feature updates, per-tournament loop) |

**These are complementary, not competing protocols.** The bulk split answers "does the model generalize over time?" while the sequential split answers "does the model adapt within a tournament?" Both should be reported in the thesis.

### B.6 Thesis Value

1. **Methodological contribution.** Tournament-aware sequential evaluation is not standard in SC2 prediction literature. Most work uses random or simple temporal splits. Formalizing and implementing this protocol is a contribution independent of model performance.

2. **Practical relevance.** The sequential protocol directly models the use case of live tournament prediction / betting market analysis, making results interpretable to non-academic audiences.

3. **Diagnostic power.** The accuracy-vs-tournament-stage curve reveals whether the model captures within-tournament dynamics (player form, strategic adaptation, bracket progression) or merely relies on static historical ratings.

4. **Negative results are informative.** If sequential feature updates provide no lift over the bulk baseline, this indicates that within-tournament signals are either too noisy or too sparse to exploit — itself a finding worth reporting.
