# SC2 Game Roadmap — Phases 3–10

**Scope:** Game-level pipeline from games table construction through model
evaluation. Operates on unified analytical views, not raw dataset artifacts.

**Dataset roadmap (Phases 0–2):** `sc2egset/ROADMAP.md`

---

## Phase 3 — Games table construction and temporal structure

**Context:** The `matches_flat` view in `processing.py` already pairs players within the same game. However, it produces **two rows per game** (one per perspective — p1 vs p2, then p2 vs p1). This phase constructs the canonical `games` table (one row per unique match), establishes correct temporal ordering per player, and validates that the data supports the sliding-window prediction framing.

**Critical design decision — symmetric player ordering:** In the `games` table, players are assigned to slots `player_a` and `player_b` using lexicographic ordering of canonical nicknames (LEAST/GREATEST). This is an arbitrary but consistent convention. At prediction time, the model receives features for a **focal player** and an **opponent** — the same feature computation pipeline runs for both perspectives. Neither player slot is privileged (Scientific Invariant #8).

**Inputs:** `raw` table, `player_appearances`, `canonical_players`, `map_translation`.

### Steps

**3.1 — Run `create_ml_views` to build `flat_players` and `matches_flat`**

Run `create_ml_views(con)`. Then immediately validate the output:
- Count rows in `flat_players` (should be exactly 2× the number of valid 1v1 replays)
- Count rows in `matches_flat` — determine exact multiplicity and document it
- Count distinct `match_id` values in `matches_flat`
- Check for any `match_id` with unexpected row count — these are data anomalies

Document the actual multiplicity explicitly so there is no ambiguity when building features.

**3.2 — Build the canonical `games` table**

Create a DuckDB table `games` with **one row per unique replay**, collapsing the two-perspective structure:

```sql
CREATE TABLE games AS
SELECT
    match_id,
    replay_id,         -- MD5 hash
    tournament_dir,
    match_time,
    game_loops,
    -- Both time representations, clearly labelled
    ROUND(game_loops / 22.4 / 60.0, 2) AS duration_real_minutes,
    ROUND(game_loops / 16.0 / 60.0, 2) AS duration_game_minutes,
    map_name,
    map_size_x,
    map_size_y,
    data_build,
    game_version,
    -- Player A is always the lexicographically smaller name (consistent ordering)
    LEAST(p1_name, p2_name) AS player_a_name,
    GREATEST(p1_name, p2_name) AS player_b_name,
    -- Race assignment follows the same ordering
    CASE WHEN p1_name < p2_name THEN p1_race ELSE p2_race END AS player_a_race,
    CASE WHEN p1_name < p2_name THEN p2_race ELSE p1_race END AS player_b_race,
    -- Winner
    CASE
        WHEN p1_result = 'Win' AND p1_name < p2_name THEN p1_name
        WHEN p1_result = 'Win' AND p1_name > p2_name THEN p2_name
        ELSE -- p1 lost
            CASE WHEN p1_name < p2_name THEN p2_name ELSE p1_name END
    END AS winner_name
FROM matches_flat
WHERE p1_name < p2_name  -- deduplicate: take only one perspective
```

Join to `canonical_players` to add `player_a_canonical_id`, `player_b_canonical_id`, and `winner_canonical_id`.

**Do NOT add an `is_valid` flag here.** Duration thresholds are determined in Phase 6 based on empirical evidence from Phase 1. Premature filtering violates the data-driven analysis principle.

**3.3 — Tournament timeline**

For each `tournament_dir` in `games`:
- First and last `match_time`
- Duration in days
- Number of unique players
- Number of games
- Year extracted from first match time

Sort chronologically. Verify that the tournament directory name years align with the actual timestamps (e.g. `2016_IEM_10_Taipei` should have matches in early 2016).

Output: `reports/03_tournament_timeline.csv`

**3.4 — Per-player career sequence**

For each canonical player, using `games` joined to `canonical_players`:
- Sort all their games by `match_time`
- Assign `career_game_seq` (1 = first ever recorded game)
- Compute `days_since_prev_game` (null for first game)
- Flag gaps > 180 days (possible retirement or injury break)

Store as DuckDB table `player_career_sequence`.

**3.5 — Within-tournament game sequence per player**

For each (player, tournament) pair:
- Sort games within that tournament by `match_time`
- Assign `within_tournament_seq` (1 = first game in that tournament for that player)
- Compute `minutes_since_prev_game_in_tournament` (null for first game)
- Flag any within-tournament gap < 1 minute (timestamp collision risk)
- Flag any within-tournament gap > 24 hours (multi-day event — legitimate)

Store in `player_career_sequence` as additional columns.

Output: `reports/03_timestamp_collision_report.csv` — list any sub-1-minute within-player gaps

**3.6 — Sliding-window feasibility analysis**

This is the most important step in this phase. For each canonical player, enumerate all valid `(history_window, target_game)` pairs where:
- Target game = game N in the player's career sequence
- History window = games 1 through N-1 (all prior games)

For each player, count:
- Total number of games (potential prediction targets)
- Number of targets where prior career games < 3 (cold-start: very little history)
- Number of targets where prior career games >= 3 (usable)
- Number of targets where the player also has ≥ 1 prior game **within the same tournament** (within-tournament conditioning available)
- Number of targets where the player has **only pre-tournament history** (no within-tournament context)

Aggregate across all players. This tells you: how many total training examples exist, how many are cold-start, and how often within-tournament context is available.

Output: `reports/03_sliding_window_feasibility.csv` (per player)
Output: `reports/03_sliding_window_summary.md` (aggregate stats — total examples, cold-start fraction, within-tournament context availability)

**3.7 — Head-to-head history analysis**

For each canonical player pair (A, B) where A < B alphabetically:
- Total games played against each other
- Chronological order of those games
- Earliest and latest match date

This establishes whether head-to-head history is a viable feature (requires at least some pairs playing each other multiple times).

Output: `reports/03_head_to_head_coverage.csv`

### Artifacts

- DuckDB table: `games`
- DuckDB table: `player_career_sequence`
- `reports/03_tournament_timeline.csv`
- `reports/03_timestamp_collision_report.csv`
- `reports/03_sliding_window_feasibility.csv`
- `reports/03_sliding_window_summary.md`
- `reports/03_head_to_head_coverage.csv`

### Gate

`games` table exists with exactly one row per replay and `player_a_canonical_id`, `player_b_canonical_id`, `winner_canonical_id` populated. The sliding-window feasibility report exists and you can state: (a) total prediction examples available, (b) cold-start proportion, (c) how often within-tournament context is available.

**Thesis mapping:** §4.2, §4.4.1 — Temporal structure and prediction framing

---

## Phase 4 — In-game statistics extraction and profiling

**Context:** The `player_stats` view in `ingestion.py` already extracts the 39 `PlayerStats` economic fields from `tracker_events_raw`. But it has not been profiled — we do not yet know which fields carry signal, whether sampling is regular, or what the distributions look like. This phase also extracts unit and upgrade events. Nothing here is feature engineering — this is raw value profiling.

**Inputs:** `tracker_events_raw` table, `games` table, `player_appearances`.

### Steps

**4.1 — Validate the `player_stats` view**

The `player_stats` view filters `tracker_events_raw` to `event_type = 'PlayerStats'` and extracts 39 typed columns.

Validate:
- Total rows in `player_stats`
- Distinct `match_id` values — should match `games` count
- Rows per match per player — should be approximately `game_loops / 160` per player (one snapshot every ~160 loops ≈ 7.14 real-time seconds at Faster speed)
- Distribution of row counts per match (min, median, max, p5, p95)
- Null rate per column — any of the 39 fields that are systematically null are dead

Output: `reports/04_player_stats_validation.md`

**4.2 — Sampling regularity check**

For 200 randomly sampled games, check that `PlayerStats` events are sampled at regular `~160 loop` intervals:
- For each game and player, sort events by `game_loop` and compute `diff(game_loop)`
- Distribution of diffs — should cluster tightly at 160
- Flag any game where mean diff deviates > 20% from 160 (irregular sampling)
- Flag any game with gaps > 500 loops (missed snapshots)

Note: 160 loops ÷ 22.4 loops/s = 7.14 real-time seconds per snapshot.

Output: `reports/04_sampling_regularity.csv`

**4.3 — Null and zero inflation per field**

For all 39 `player_stats` fields across the full corpus, compute:
- Fraction of rows that are null
- Fraction of rows that are exactly 0
- Mean, std, p5, p25, p75, p95 for non-null non-zero values

Fields where > 95% of values are 0 across all games are dead features. Document them explicitly.

Output: `reports/04_field_inflation.csv`

**4.4 — Winner vs. loser separability analysis**

This is the key statistical analysis for feature selection.

Join `player_stats` to `games` to label each player's snapshots as winner or loser.

Select canonical timepoints using the real-time conversion table from the
Reference section above. The timepoints should reflect meaningful game stages:

| Timepoint name | Real-time | Game loops | Rationale |
|---|---|---|---|
| `early_game` | ~3 min | ~4,032 | Post-opening, pre-expansion |
| `mid_game_1` | ~7 min | ~9,408 | First significant economic divergence |
| `mid_game_2` | ~12 min | ~16,128 | Mid-game army composition set |
| `late_game` | ~20 min | ~26,880 | Late-game macro differences |
| `final` | last snapshot | varies | End-of-game state |

For each timepoint: find the closest `PlayerStats` snapshot (nearest `game_loop`).

For each surviving (non-dead) field, compute:
- Mean for winners, mean for losers
- Cohen's d = (mean_winner - mean_loser) / pooled_std
- Two-sided t-test p-value (Bonferroni-corrected for number of fields tested)

Sort by Cohen's d descending. Fields with |Cohen's d| < 0.1 at all timepoints are weak and should be deprioritised.

Output: `reports/04_winner_loser_separability.csv`
Output: `reports/04_separability_heatmap.png` — heatmap: fields × timepoints, colour = Cohen's d

**4.5 — Extract and profile `UnitBorn` and `UnitDied` events**

From `tracker_events_raw`, filter to `event_type IN ('UnitBorn', 'UnitDied')`.

For each event, extract from `event_data` JSON:
- `unit_type_name`
- `control_player_id`
- `killer_player_id` (for UnitDied only)
- `game_loop`
- x, y coordinates

Build a table `unit_events` in DuckDB.

Then build a unit type taxonomy CSV `data/unit_type_taxonomy.csv`:
- List all distinct `unit_type_name` values across a sample of 500 games
- Classify each as: `worker`, `army_ground`, `army_air`, `building`, `neutral_destructible`, `other`
- Note which race produces each unit type (source: Liquipedia unit pages)

This taxonomy is used in Phase 7 feature engineering.

Output: DuckDB table `unit_events`
Output: `data/unit_type_taxonomy.csv`
Output: `reports/04_unit_type_profile.csv` — counts of each unit type born/died across the sample

**4.6 — Extract and profile `Upgrade` events**

From `tracker_events_raw`, filter to `event_type = 'Upgrade'`. Extract `upgrade_type_name`, `player_id`, `game_loop` from `event_data`.

Build DuckDB table `upgrade_events`. Then compute:
- Top 50 most frequent upgrades overall
- Median `game_loop` timing for each upgrade (converted to real-time minutes)
- Per-race breakdown: which upgrades are exclusively Terran/Protoss/Zerg?

Output: DuckDB table `upgrade_events`
Output: `reports/04_upgrade_timings.csv`

**4.7 — Build order fingerprinting (exploratory)**

For each game and player, extract the first 10 non-worker, non-neutral `UnitBorn` events (ordered by `game_loop`) as the build order prefix.

Compute:
- 20 most common build order prefixes per matchup (ZvT, ZvP, TvP, ZvZ, TvT, PvP)
- This is not a feature yet — it establishes build order diversity and whether it's feasible to use build orders as features

Output: `reports/04_build_order_analysis.md`

### Artifacts

- `reports/04_player_stats_validation.md`
- `reports/04_sampling_regularity.csv`
- `reports/04_field_inflation.csv`
- `reports/04_winner_loser_separability.csv`
- `reports/04_separability_heatmap.png`
- DuckDB table: `unit_events`
- `data/unit_type_taxonomy.csv`
- `reports/04_unit_type_profile.csv`
- DuckDB table: `upgrade_events`
- `reports/04_upgrade_timings.csv`
- `reports/04_build_order_analysis.md`

### Gate

You have a ranked list of which of the 39 PlayerStats fields show the strongest winner/loser separation at which timepoints. You have a unit type taxonomy. You know which fields are dead (all zeros). These findings directly determine which features to engineer in Phase 7.

**Thesis mapping:** §4.3.2 — SC2-specific in-game features

---

## Phase 5 — Map, meta-game, and matchup analysis

**Context:** Win/loss prediction in SC2 is heavily confounded by race matchup (ZvT, TvP, etc.), map pool, and game version (balance patches). This phase quantifies those confounds so they can be handled correctly in the model — either as control features or by stratifying the evaluation.

**Inputs:** `games` table, `player_appearances`, `map_translation`.

### Steps

**5.1 — Map pool by year**

For each calendar year, list the distinct `map_name` values that appear in `games` and their game counts. SC2 map pools rotate each competitive season.

Output: `reports/05_map_pool_by_year.csv`

**5.2 — Win rate by map and matchup**

For each (map_name, player_a_race, player_b_race) combination where we use canonical matchup ordering (alphabetically smaller race first, e.g. PvT not TvP):
- Total games
- Win rate for the first-listed race
- 95% Wilson confidence interval

Filter to combinations with ≥ 20 games. Flag combinations where win rate is outside [0.40, 0.60].

Output: `reports/05_map_matchup_winrates.csv`

**5.3 — Overall matchup balance by patch era**

Group replays into broad patch eras using the `game_version` landscape from Phase 1. For each (matchup, era) pair:
- Game count
- Win rate for race A
- 95% Wilson confidence interval

This tells you whether patch version is a necessary control variable in the model.

Output: `reports/05_matchup_balance_by_era.csv`

**5.4 — Map size vs. game duration correlation**

Compute `map_area = map_size_x * map_size_y` for each game. Scatter plot and Pearson correlation between map_area and `duration_real_minutes`.

Output: `reports/05_map_size_duration_correlation.png`

**5.5 — Race representation by tournament type**

Some tournaments (WCS Korea, GSL) skew toward Korean pros and thus Terran/Zerg. Others (WCS Global) have more diverse representation. Compute race proportion per tournament.

Output: `reports/05_race_representation_by_tournament.csv`

**5.6 — Decision document: required control features**

Write a short decision document answering:
1. Is map identity a necessary model feature? (Yes/No + evidence from 5.2)
2. Is patch era a necessary model feature? (Yes/No + evidence from 5.3)
3. Is race matchup encoded in the model or evaluated stratified? (Decision + rationale)

Output: `reports/05_control_feature_decisions.md`

### Artifacts

- `reports/05_map_pool_by_year.csv`
- `reports/05_map_matchup_winrates.csv`
- `reports/05_matchup_balance_by_era.csv`
- `reports/05_map_size_duration_correlation.png`
- `reports/05_race_representation_by_tournament.csv`
- `reports/05_control_feature_decisions.md`

### Gate

`reports/05_control_feature_decisions.md` exists and contains explicit yes/no decisions with supporting evidence. These decisions are locked in before feature engineering begins.

**Thesis mapping:** §4.1.1 context (meta-game confounds), §4.3.1 (control features)

---

## Phase 6 — Data cleaning and valid game corpus

**Context:** Based on all findings from Phases 1–5, this phase applies explicit, documented cleaning rules to produce the clean game corpus. Every exclusion is logged with its reason. No data is deleted — all exclusions are implemented as filters (a `games_clean` view). This is a thesis-auditable step.

**Critical principle:** Every threshold must be justified by either (a) empirical evidence from earlier phases, or (b) a cited precedent from the literature. No magic numbers.

**Inputs:** All tables and reports from Phases 1–5.

### Steps

**6.1 — Write the cleaning rules document**

Before touching any data, write `reports/06_cleaning_rules.md`. Each rule must reference which Phase finding motivates it:

| Rule ID | Condition | Action | Motivation |
|---------|-----------|--------|------------|
| R1 | `duration_real_minutes < T_min` (threshold T_min derived from Phase 1.3 distribution) | exclude | Phase 1.3: short-game tail analysis. T_min should be chosen based on the observed distribution, annotated game-play landmarks, and precedent (Wu et al. 2017 used 7 min; Białecki et al. 2023 used 9 min). Document the exact choice and its justification. |
| R2 | No rows in `tracker_events_raw` for this `replay_id` | exclude | Phase 1.1: no event data, cannot compute in-game features |
| R3 | Player count per game ≠ 2 (after observer/caster exclusion) | exclude | Not a valid 1v1 game |
| R4 | Either player's `result` not in {Win, Loss} | exclude | No ground truth label |
| R5 | Race is not in {Terr, Prot, Zerg} (e.g. BW exhibition, Random) | exclude | Non-standard race |
| R6 | Tournament `event_coverage_pct < 20%` (from Phase 1.2) | flag whole tournament | Insufficient data quality |
| R7 | Player appears only with ambiguous identity (unresolved from Phase 2.4) | flag game | Degraded player identity confidence |

Add any additional rules discovered during exploration.

**6.2 — Apply rules and create `games_clean` view**

Create a DuckDB view (not a copy) `games_clean` that filters `games` using all rules. Add an `exclusion_reason` column to the base `games` table explaining why each excluded game was removed.

**6.3 — Cleaning impact report**

For each rule, report:
- Games excluded by this rule (and this rule alone — not already excluded by a higher-priority rule)
- Tournaments affected
- Players who lose the most games due to each rule

Output: `reports/06_cleaning_impact.md`

**6.4 — Final clean corpus statistics**

On `games_clean`:
- Total games
- Total unique players
- Total tournaments
- Date range
- Games per year
- Overall win rate (sanity check: should be exactly 0.500, since every game has one winner and one loser)
- Matchup distribution (ZvT, ZvP, TvP, ZvZ, TvT, PvP counts and percentages)

Output: `reports/06_clean_corpus_summary.md`

### Artifacts

- `reports/06_cleaning_rules.md`
- DuckDB view: `games_clean`
- `reports/06_cleaning_impact.md`
- `reports/06_clean_corpus_summary.md`

### Gate

`games_clean` view exists. Overall win rate is exactly 0.500. Cleaning impact is documented. Every exclusion has a documented rule ID with a traceable justification (Phase finding or literature reference).

**Thesis mapping:** §4.2.3 — Preprocessing and quality filtering

---

## Phase 7 — Feature engineering

**Context:** With the data exploration complete and the clean corpus established, feature engineering can begin. Features fall into two groups:

- **Group A — Pre-game features:** Available before the match starts — player history, opponent history, head-to-head, derived skill rating, map, matchup. These are the **common feature set** that can also be computed for AoE2 (using civilisation instead of race, Elo instead of derived Glicko, etc.). This is the primary model.
- **Group B — In-game snapshot features:** From `PlayerStats` at canonical timepoints. SC2-only (AoE2 has no equivalent). Secondary experiment.

Do not mix groups A and B in the same model without understanding the temporal position they represent.

**Symmetric player treatment (Scientific Invariant #8):** Every feature must be computed identically for both players. The model input for a given game is structured as (focal_player_features, opponent_features, context_features), where the same function produces features for both perspectives.

**Inputs:** `games_clean`, `player_career_sequence`, `player_stats` view, `unit_events`, `upgrade_events`, `canonical_players`, all reports from Phases 1–5.

### Steps

**7.1 — Define the feature groups formally**

Write `reports/07_feature_specification.md` before writing any feature code:

**Group A — Pre-game features (predict before the game begins)**

Per-player features (computed for both focal and opponent):
- Derived skill rating: Elo or Glicko-2, computed from the player's match history
  strictly before the target game (Scientific Invariant #3). Starting rating, K-factor
  or RD parameters should be documented and tuned.
  [Reference: Glickman 2001; EsportsBench shows Glicko-2 at 80.13% for SC2]
- Games played in last 30 days, last 90 days, last 365 days
- Overall career win rate (all prior games)
- Win rate in last 10 / 20 / 50 games (rolling window)
- Win rate vs. the specific opponent's race (all prior games vs. that race)
- Win rate on this specific map (historical)
- Head-to-head record against this specific opponent (all prior games)
- Within-tournament momentum: win/loss record in current tournament so far (games 1..M)
- Career summary: total career games, career span in days
- APM: mean APM from last 10 games (available from 2017+; imputed for 2016)

Context features (per-game, not per-player):
- Race matchup encoding (one-hot for the 6 matchup types)
- Map features: map_name (one-hot or hashed), map_size_x, map_size_y
- Patch era encoding (from Phase 5 decision)
- Rating differential: focal_rating - opponent_rating

**Group B — In-game snapshot features (SC2 only)**
- From `player_stats` at the canonical timepoints from Phase 4.4:
  all surviving non-dead fields with |Cohen's d| > 0.2
- Differential features: focal_player_stat - opponent_stat at each timepoint
- Note: both players' stats are computed from the same game state —
  neither perspective is privileged

**7.2 — Implement derived skill ratings**

Before computing other features, implement an Elo or Glicko-2 rating system
that processes the full `games_clean` corpus chronologically:

- For each game in chronological order, update both players' ratings
- The rating **before** the game is the feature value (strict temporal discipline)
- Store the full rating history as a table: `player_rating_history`
  (columns: player_canonical_id, game_id, rating_before, rating_after, ...)
- Validate: the implied prediction accuracy from ratings alone (P(higher-rated wins))
  should approximate the ~80% reported by EsportsBench for Glicko-2 on SC2

Output: DuckDB table `player_rating_history`
Output: `reports/07_rating_system_validation.md`

**7.3 — Implement Group A feature computation**

All Group A features must be computed with **strict temporal discipline**: for any target game at time T, only information from games where `match_time < T` may be used (Scientific Invariant #3).

Implement as a Python function `compute_pre_game_features(games_clean, player_career_sequence, player_rating_history, target_game_id, focal_player_id)` that returns a feature vector for a given target game and focal player. Then vectorise over all games in `games_clean`, computing features for **both** players in each game (two rows per game — one per perspective).

Key implementation constraint: use `player_career_sequence` with `career_game_seq < target_seq` filters — never a naïve `.shift()` on a DataFrame that could leak future information.

Output: `data/features_group_a.parquet` — two rows per game (one per player perspective)

**7.4 — Implement Group B feature computation (SC2-only experiment)**

For the in-game model variant, compute PlayerStats features at each canonical timepoint per game.

Apply the surviving fields list from Phase 4 (|Cohen's d| > 0.2). Compute differential columns (focal_player_stat - opponent_stat).

Output: `data/features_group_b.parquet`

**7.5 — Feature validation**

For the Group A features:
- Null rate per feature column — document and handle (impute with career-prior mean, or use 0 for cold-start players with no prior games)
- Distribution checks: any features with extreme skew should be documented; consider log-transform or clipping if needed
- **Temporal leakage check:** for a random sample of 20 target games, manually verify that no feature value for that game depends on any event at or after `match_time` of the target game. Print the feature values alongside the data that produced them.
- **Symmetry check:** verify that for a sample of games, swapping focal and opponent player produces the expected mirror of feature values (e.g., focal_win_rate for player A = opponent_win_rate when player B is focal)

Output: `reports/07_feature_validation.md`

**7.6 — Build the prediction target table**

Create the final ML-ready table combining features and labels:

| column | description |
|--------|-------------|
| `game_id` | the game being predicted |
| `focal_player_id` | the canonical player we are predicting for |
| `opponent_player_id` | the opponent |
| `focal_player_name` | for human readability |
| `opponent_player_name` | for human readability |
| `within_tournament_context_games` | prior games by focal player in this tournament |
| `career_prior_games` | total prior career games for focal player |
| [all Group A feature columns] | prefixed `focal_` and `opp_` for per-player features |
| `label` | 1 if focal player won, 0 if lost |
| `split` | train / val / test (assigned in Phase 8) |

**Note on class balance:** Since each game produces two rows (one per perspective), the overall label distribution is exactly 50/50 by construction. This is intentional and correct.

Output: `data/ml_dataset.parquet`

### Artifacts

- `reports/07_feature_specification.md`
- DuckDB table: `player_rating_history`
- `reports/07_rating_system_validation.md`
- `data/features_group_a.parquet`
- `data/features_group_b.parquet` (if implemented)
- `reports/07_feature_validation.md`
- `data/ml_dataset.parquet`

### Gate

`ml_dataset.parquet` exists. Temporal leakage check passed for sampled games. Symmetry check passed. Null rates documented and handled. Rating system validated. `reports/07_feature_specification.md` explicitly distinguishes Group A (pre-game) from Group B (in-game) features.

**Thesis mapping:** §4.3 — Feature engineering

---

## Phase 8 — Train/val/test split construction

**Context:** This is where the correct splitting strategy from the thesis design is implemented. The naïve global temporal split in `processing.py` is replaced with a per-player temporal split (Scientific Invariant #1).

**Inputs:** `data/ml_dataset.parquet`, `games_clean`, `player_career_sequence`.

### Steps

**8.1 — Implement the correct split strategy**

The split logic is:

- **Test set:** For each canonical player, their last tournament appearance. All games in that tournament where the player is the focal player go to test.
- **Validation set:** For each canonical player, their second-to-last tournament appearance (same logic).
- **Training set:** All remaining games.

Implementation notes:
- A game can appear in both player A's training and player B's test set (if they played at different points in their respective careers). This is correct behaviour — the split is per-player, not per-game (Scientific Invariant #1).
- Players with fewer than 3 tournament appearances cannot have separate train/val/test — flag them as cold-start and exclude from validation/test, keep in training only.

**8.2 — Validate the split**

For the new split:
- No player's test target is temporally before their training data
- No player's validation target is temporally before their training data
- Class balance (win rate) in train, val, test — should each be ~0.500 (guaranteed by symmetric two-row design)
- Distribution of `within_tournament_context_games` in test: how often does the model have 0, 1, 2, 3+ prior games in the target tournament?
- Size of each split: number of examples

Output: `reports/08_split_validation.md`

**8.3 — Baseline win rate by split**

For each split, compute win rate by matchup (ZvT, TvP, etc.). If any matchup in test has win rate significantly different from 0.5, it is a potential confound.

Output: `reports/08_split_matchup_balance.csv`

**8.4 — Compare to the naïve global split**

For reference, document what the old `create_temporal_split` would have produced vs. the new per-player split. Include: split sizes, matchup balance, cold-start proportion, within-tournament context availability.

This comparison goes into the thesis methodology section as justification for the new approach.

Output: `reports/08_split_comparison.md`

### Artifacts

- `data/ml_dataset.parquet` (updated with correct `split` column)
- `reports/08_split_validation.md`
- `reports/08_split_matchup_balance.csv`
- `reports/08_split_comparison.md`

### Gate

Split is validated. No temporal leakage. Class balance ~0.500 in each split. The split comparison document exists.

**Thesis mapping:** §4.4.1 — Train/validation/test split strategy

---

## Phase 9 — Baseline models and sanity checks

**Context:** Before training any serious model, establish baselines that any real model must beat. Also run sanity checks to confirm the dataset and features are not trivially broken.

**Inputs:** `data/ml_dataset.parquet` with correct split.

### Steps

**9.1 — Implement and evaluate baselines**

- **Random baseline:** Predicts win probability = 0.5 always. Accuracy = 50%.
- **Race-matchup baseline:** Predicts the historically more winning race for each matchup. Uses only training set matchup win rates.
- **Elo/Glicko-2 rating baseline:** Predicts the higher-rated player wins.
  This is the primary strength-of-schedule baseline.
  [Reference: EsportsBench reports 80.13% for Glicko-2 on Aligulac SC2 data]
- **Recent form baseline:** Predicts the player with the higher win rate in their last 10 career games wins.
- **Head-to-head baseline:** Predicts based on prior head-to-head record. Falls back to recent form if no prior H2H exists.

Evaluate each baseline on the test set: accuracy, log-loss, ROC-AUC, per-matchup accuracy, calibration (Brier score).

Output: `reports/09_baseline_results.md`

**9.2 — Sanity check: permutation test**

Shuffle the `label` column randomly (keeping all features intact). Train a logistic regression on shuffled labels. Confirm it achieves ~50% accuracy. This verifies the training pipeline is not broken.

**9.3 — Sanity check: perfect feature leakage test**

Create a "cheat" feature: the actual in-game outcome stat from the final `PlayerStats` snapshot (e.g. `mineralsCurrent` differential at game end). Train a model on this. It should achieve near-100% accuracy. This verifies that the pipeline can distinguish signal from noise and that the join between features and labels is correct.

Output: `reports/09_sanity_checks.md`

### Artifacts

- `reports/09_baseline_results.md`
- `reports/09_sanity_checks.md`

### Gate

At least one baseline beats random (otherwise the features contain no signal). The Glicko-2 baseline should be in the 75–82% range (consistent with EsportsBench). Permutation test achieves ~50%. Leakage test achieves near-100%. All sanity checks documented.

**Thesis mapping:** §5.1.1 — SC2 baselines and sanity validation

---

## Phase 10 — Model training and evaluation

**Context:** With clean features, a correct split, and validated baselines, train the primary models. Start simple and add complexity only if justified by validation performance.

**Inputs:** `data/ml_dataset.parquet`, baseline results from Phase 9.

### Steps

**10.1 — Logistic Regression (interpretable baseline)**

Train with Group A features, evaluate on val set. Record: accuracy, log-loss, ROC-AUC, per-matchup accuracy, calibration curve. Inspect top feature weights — do they make domain sense? (e.g., rating differential should be the strongest predictor)

**10.2 — Random Forest**

Train with Group A features, tune on val set. Record same metrics plus feature importances. This tests whether non-linear interactions improve over LR.

**10.3 — Gradient Boosted Trees (LightGBM or XGBoost)**

Train with Group A features, tune on val set (learning rate, depth, regularisation). Evaluate on test set only after hyperparameter selection is finalised. Record same metrics plus feature importances via SHAP.

**10.4 — Feature ablation study**

Train best-performing model with each feature group removed in turn:
- Without derived skill ratings (Elo/Glicko)
- Without within-tournament context features
- Without head-to-head history
- Without career-level stats (win rate, activity)
- Without control features (map, matchup)

Report accuracy drop for each ablation. This answers which feature groups matter most.

Output: `reports/10_ablation_results.md`

**10.5 — Per-matchup evaluation**

For the best model, evaluate separately on ZvT, ZvP, TvP, ZvZ, TvT, PvP subsets of the test set. Are some matchups harder to predict than others?

**10.6 — Cold-start analysis**

Stratify test set by `career_prior_games` (0–5, 6–20, 21–50, 51+). How does model accuracy vary with career history length? This directly addresses the cold-start problem (Research Question RQ4).

**10.7 — In-game prediction experiment (Group B features, SC2 only)**

Using Group B features (PlayerStats at canonical timepoints), train LightGBM at each timepoint. Plot accuracy as a function of real-time game elapsed. Compare to the pre-game model. This produces the "accuracy over time" curve common in the esports prediction literature.

[Reference: Hodge et al. 2021 showed 85% at 5 min for Dota 2; SC2 literature shows accuracy increasing monotonically with game time]

**10.8 — Optional: GNN experiment**

If time permits, implement the GNN model from the existing `sc2/gnn` code. Compare to the tabular models. The key thesis question is: does modelling the player interaction graph add anything beyond the tabular features?

Output: `reports/10_model_results.md`
Output: `reports/10_ablation_results.md`
Output: `reports/10_per_matchup_results.csv`
Output: `reports/10_cold_start_analysis.csv`
Output: `reports/10_ingame_accuracy_curve.png` (if 10.7 done)

### Artifacts

- `reports/10_model_results.md`
- `reports/10_ablation_results.md`
- `reports/10_per_matchup_results.csv`
- `reports/10_cold_start_analysis.csv`
- `reports/10_ingame_accuracy_curve.png`

### Gate

Best model accuracy > best baseline accuracy (otherwise the ML is not adding value). Ablation results document which features drive performance. Results are ready for the thesis Chapter 5.

**Thesis mapping:** §5.1.2–5.1.4 — SC2 experimental results

---

## Appendix — Artifact index

Game-level reports (Phases 3+) land in `reports/`. Dataset-level reports (Phases 0–2) land in `sc2egset/`. All data files land in `data/`.

```
reports/
  03_tournament_timeline.csv
  03_timestamp_collision_report.csv
  03_sliding_window_feasibility.csv
  03_sliding_window_summary.md
  03_head_to_head_coverage.csv
  04_player_stats_validation.md
  04_sampling_regularity.csv
  04_field_inflation.csv
  04_winner_loser_separability.csv
  04_separability_heatmap.png
  04_unit_type_profile.csv
  04_upgrade_timings.csv
  04_build_order_analysis.md
  05_map_pool_by_year.csv
  05_map_matchup_winrates.csv
  05_matchup_balance_by_era.csv
  05_map_size_duration_correlation.png
  05_race_representation_by_tournament.csv
  05_control_feature_decisions.md
  06_cleaning_rules.md
  06_cleaning_impact.md
  06_clean_corpus_summary.md
  07_feature_specification.md
  07_rating_system_validation.md
  07_feature_validation.md
  08_split_validation.md
  08_split_matchup_balance.csv
  08_split_comparison.md
  09_baseline_results.md
  09_sanity_checks.md
  10_model_results.md
  10_ablation_results.md
  10_per_matchup_results.csv
  10_cold_start_analysis.csv
  10_ingame_accuracy_curve.png

data/
  unit_type_taxonomy.csv
  features_group_a.parquet
  features_group_b.parquet
  ml_dataset.parquet
```

---

## Appendix — Key references

| Short cite | Full reference | Used for |
|---|---|---|
| Białecki et al. 2023 | Białecki, A. et al. SC2EGSet: SC2 Esport Replay and Game-state Dataset. *Scientific Data* 10(1), 600. | Dataset |
| Vinyals et al. 2017 | Vinyals, O. et al. StarCraft II: A New Challenge for RL. *arXiv:1708.04782*. | Game loop timing, SC2LE |
| Wu et al. 2017 | Wu, H. et al. MSC: A Dataset for Macro-Management in SC2. *arXiv:1710.03131*. | Duration threshold (7 min), GRU baseline |
| Baek & Kim 2022 | Baek, J. & Kim, J. 3D-CNNs for SC2 prediction. *PLOS ONE*. | 90% accuracy benchmark |
| Khan et al. 2021 | Khan, A. et al. Transformers on SC2 MSC. *IEEE ICMLA*. | Transformer baseline |
| Glickman 2001 | Glickman, M. The Glicko-2 System. | Rating system |
| Thorrez 2024 | Thorrez, L. EsportsBench. | Glicko-2 at 80.13% for SC2 |
| Demšar 2006 | Demšar, J. Statistical Comparisons of Classifiers. *JMLR* 7. | Cross-game statistical comparison |
| Hodge et al. 2021 | Hodge, V. et al. Dota 2 Win Prediction. *IEEE Trans. Games*. | In-game accuracy curve precedent |
| Liquipedia | Game Speed article, Cheese strategies | Game loop conversion, short game landmarks |
| s2client-proto | Blizzard/s2client-proto protocol.md | 22.4 loops/s at Faster speed |
