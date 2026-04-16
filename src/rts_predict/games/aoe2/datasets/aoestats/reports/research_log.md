# Research Log — AoE2 / aoestats

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

AoE2 / aoestats findings. Reverse chronological.

---

## 2026-04-15 — [Phase 01 / Step 01_03_03] Table Utility Assessment

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** Empirical assessment of all 3 raw tables for prediction pipeline utility. Column overlap, join integrity, ELO redundancy, overviews_raw STRUCT content, replay_summary_raw fill rate. Assessment only — no cleaning or feature decisions (I9).

### 01_03_03 — Table Utility Assessment

**Artifacts produced:**
- `artifacts/01_exploration/03_profiling/01_03_03_table_utility.json` (14K)
- `artifacts/01_exploration/03_profiling/01_03_03_table_utility.md` (7K)

**T01 — Column overlap:**
- Shared columns (2): `filename`, `game_id`
- matches_raw exclusive (16): `avg_elo`, `duration`, `game_speed`, `game_type`, `irl_duration`, `leaderboard`, `map`, `mirror`, `num_players`, `patch`, `raw_match_type`, `replay_enhanced`, `started_timestamp`, `starting_age`, `team_0_elo`, `team_1_elo`
- players_raw exclusive (12): `castle_age_uptime`, `civ`, `feudal_age_uptime`, `imperial_age_uptime`, `match_rating_diff`, `new_rating`, `old_rating`, `opening`, `profile_id`, `replay_summary_raw`, `team`, `winner`
- `winner` is exclusive to players_raw. `started_timestamp` is exclusive to matches_raw. Both tables confirmed.

**T02 — Join integrity:**
- Orphan matches (in matches_raw, no players): 212,890 — validated against 01_03_01 MATCHES_WITHOUT_PLAYERS.
- Orphan player game_ids (in players_raw, not in matches_raw): 0 — complete referential integrity in the player direction.
- matches_raw: 30,690,651 distinct game_ids / 30,690,651 rows = 100.0% unique (no duplicates per game_id).
- players_raw: 30,477,761 distinct game_ids, avg 3.5313 player rows per game_id.
- Multiplicity: 60.50% of game_ids have exactly 2 player rows (true 1v1). 16.50% have 4, 14.06% have 8, 8.94% have 6.

**T03 — ELO redundancy:**
- avg_elo = (team_0_elo + team_1_elo) / 2: 99.9955% exact within 0.001 tolerance. 1,386 rows deviate (max deviation: 1,640 -- likely data anomalies).
- avg_elo cross-derivation from players_raw.old_rating in 1v1 matches: 100.0% within 0.5 ELO. Mean absolute deviation = 0.0. avg_elo is **exactly** the mean of old_rating across the two players in every 1v1 match.
- Spearman rho (avg_elo vs player_avg_old_rating, n=100K RESERVOIR): **1.000000** (p=0.0). Perfect monotone agreement.
- team_0_elo vs player_avg: rho=0.996784; team_1_elo vs player_avg: rho=0.997060; team_0 vs team_1: rho=0.988389.
- **Temporal annotation (I3):** `old_rating` = pre-game rating, I3-safe. `new_rating` = post-game rating, LEAKING — must never be used as a feature.

**T04 — overviews_raw and replay_summary_raw:**
- overviews_raw: singleton (1 row), last_updated 2026-04-09. Contains 19 patches (release dates 2022-08-29 to 2025-12-02), 50 civs, 10 openings, 4 ELO groupings, 41 changelog entries, 3 tournament stages (`all`, `qualifiers`, `main_event`). Patch->release_date mapping is available here and not elsewhere in raw tables.
- replay_summary_raw: 86.05% empty (`'{}'`), 0% NULL, 13.95% non-empty (15,011,294 rows). Max content length: 7,484 chars. No rows are fully NULL.

**T05 — Verdicts:**
- **matches_raw**: ESSENTIAL — sole source of `started_timestamp` (temporal anchor, I3 critical), map, leaderboard, patch, duration, mirror. ELO columns are derivable from players_raw but the reverse is not true for the temporal anchor.
- **players_raw**: ESSENTIAL — sole source of `winner` (prediction target) and player-level features (`old_rating`, `civ`, `opening`, age uptimes).
- **overviews_raw**: SUPPLEMENTARY REFERENCE — singleton lookup. Provides 19-entry patch->release_date mapping useful for temporal version stratification.
- **replay_summary_raw**: PARTIAL UTILITY — 13.95% fill rate with max 7,484-char content. Content structure warrants further investigation in a dedicated step if replay features are considered.

**Decisions taken:**
- None. Verdicts documented for downstream steps. No cleaning or feature engineering decisions.

**Decisions deferred:**
- Whether to parse replay_summary_raw content (13.95% fill rate) -- deferred to Phase 02 feature decision gate.
- Whether to use overviews_raw.patches for patch-date enrichment of matches_raw -- deferred to Phase 02.

**Thesis mapping:** Chapter 4 §4.1.2 — AoE2 dataset split architecture, join structure, ELO redundancy finding.

### SQL queries (I6)

All SQL queries are embedded verbatim in `01_03_03_table_utility.json > sql_queries`.

### Cross-dataset summary (01_03_03 across all three datasets)

| Dataset | Table | Verdict | Key finding |
|---------|-------|---------|-------------|
| **aoe2companion** | matches_raw | ESSENTIAL | `rating` is PRE-GAME (99.8% match with ratings_raw), sole source for rm_1v1 ratings |
| | ratings_raw | CONDITIONALLY USABLE | No rm_1v1 coverage (leaderboard_id=6 absent). Useful for other leaderboards only |
| | leaderboards_raw | NOT USABLE | Singleton snapshot, 1 entry per player per leaderboard. I3 violation risk |
| | profiles_raw | NOT USABLE | No temporal dimension. Adds steamId/clan (99.9% non-null) but not usable for temporal features |
| **aoestats** | matches_raw | ESSENTIAL | Temporal anchor (`started_timestamp`), match context (map, leaderboard, patch) |
| | players_raw | ESSENTIAL | Target (`winner`), `old_rating` (pre-game), `civ`. ELO perfectly derivable (Spearman rho=1.0 with avg_elo in 1v1) |
| | overviews_raw | SUPPLEMENTARY | Singleton lookup. Patch release dates are the only unique data |
| **sc2egset** | replay_players_raw | ESSENTIAL | Target (`result`), player features (MMR, race, selectedRace) |
| | replays_meta_raw | ESSENTIAL | Match metadata, 31 struct fields. Join via replay_id (regexp_extract) |
| | map_aliases_raw | CONDITIONAL | All 188 map names already English — translation not required |
| | event views (3) | IN_GAME_ONLY | Deferred to optional Phase 02 in-game comparison |

---

## 2026-04-16 — [Phase 01 / Step 01_03_02] True 1v1 Match Identification

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** Cross-reference matches_raw.num_players against actual player row counts from players_raw. Compare true 1v1 (structural: exactly 2 player rows) against ranked 1v1 (label: leaderboard='random_map'). Profiling only — no cleaning decisions (I9).

### 01_03_02 — True 1v1 Match Identification

**Artifacts produced:**
- `artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json` (12K)
- `artifacts/01_exploration/03_profiling/01_03_02_match_type_breakdown.png` (67K)
- `artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md` (8.5K)

**Q1 — Active player definition:** Every row in players_raw is an active player. The schema has no observer/spectator marker columns (no `slot`, `is_observer`, `status`, or `type`). winner is never NULL (0 nulls), civ is never NULL, team has values {0, 1} only (team_distinct=2). This is a schema-level fact, not an assumption.

**Q2 — num_players vs actual player count:** LEFT JOIN of matches_raw with player counts from players_raw reveals the breakdown of mismatches. The 212,890 orphaned matches (matches_raw rows with zero player rows, from 01_03_01 linkage check) are validated — orphaned count cross-checked against profile_01_03_01 within tolerance ≤1. Cross-validation of player_count=2 against census `players_per_match` PASSED within 1% delta.

**Q3 — True 1v1 count:** 18,438,769 matches have exactly 2 player rows. This is 60.08% of all 30,690,651 matches. The player-count method is the structural definition used going forward.

**Q4 — True 1v1 vs Ranked 1v1 comparison:**
- True 1v1 (Set A, structural): 18,438,769
- Ranked 1v1 (Set B, leaderboard='random_map'): 17,959,543
- Overlap (A AND B): 17,815,944 — Jaccard index: 0.9588
- True-only (A NOT B): 622,825 (genuine 1v1 with non-random_map leaderboard, e.g. unranked/co-op)
- Ranked-only (B NOT A): 143,599 (leaderboard='random_map' with != 2 player rows — orphaned or corrupt)
- Overlap as % of true 1v1: 96.62%
- Overlap as % of ranked 1v1: 99.20%

**Recommended 1v1 definition for downstream use:** The player-count method (actual_player_count = 2) is the structural definition. The leaderboard='random_map' filter is a near-equivalent proxy (99.2% coverage of ranked matches are structurally 1v1) but misses 622,825 genuine 1v1 matches from other leaderboards. The final decision on which set to use belongs to 01_04 (Data Cleaning).

**Duplicate impact:** B1 diagnostic confirms the 489 duplicate player rows (from 01_03_01) have negligible impact on 1v1 classification. The `recovered_by_dedup` count (raw_count != 2 AND distinct_profiles = 2) is documented in the JSON artifact.

**NULL profile_id distribution:** 1,185 NULL profile_id rows analyzed by leaderboard and player count. Distribution documented in JSON artifact.

**Set arithmetic consistency:** overlap + true_only + ranked_only + neither = 30,690,651 = total_matches (verified).

**SQL queries:** All 11 queries embedded verbatim in JSON and markdown artifacts (I6). Key queries: active_player_diagnostic, num_players_vs_actual, player_counts_distribution, true_1v1_count, duplicate_impact, true_1v1_by_leaderboard, true_1v1_by_num_players, set_comparison, ranked_not_true_1v1, true_not_ranked, null_profile_by_type.

---

## 2026-04-16 — [Phase 01 / Step 01_03_01] Systematic Data Profiling

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** Comprehensive column-level and dataset-level profiling for matches_raw (18 cols) and players_raw (14 cols). Profiling only — no cleaning decisions, no feature engineering (I9).

### 01_03_01 — Systematic Data Profiling

**Artifacts produced:**
- `artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json` (27,260 bytes)
- `artifacts/01_exploration/03_profiling/01_03_01_completeness_heatmap.png`
- `artifacts/01_exploration/03_profiling/01_03_01_qq_matches.png`
- `artifacts/01_exploration/03_profiling/01_03_01_qq_players.png`
- `artifacts/01_exploration/03_profiling/01_03_01_ecdf_key_columns.png`
- `artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md`

**I3 classification:** All 32 columns (18 matches_raw + 14 players_raw) annotated with temporal class. Classes: CONTEXT, IDENTIFIER, PRE-GAME, POST-GAME, IN-GAME, TARGET. `avg_elo` classified PRE-GAME by convention; formal leakage test deferred to 01_04.

**Critical findings:**
- Dead fields (100% NULL): none
- Constant columns (cardinality=1): `game_type` ("random_map"), `game_speed` ("normal") — flagged for 01_04 drop
- Near-constant columns (cardinality ≤ 5 AND uniqueness_ratio < 0.001): `leaderboard`, `starting_age`, `replay_enhanced`, `mirror`, `team`, `winner`. Cardinality cap of 5 (NEAR_CONSTANT_CARDINALITY_CAP) prevents false-positive flagging of civ (50), map (93), opening (10), patch (19), num_players (8).

**ELO sentinel handling:** `team_0_elo` and `team_1_elo` stats reported both with and without sentinel value −1 (34 and 39 rows respectively). Sentinel-excluded stats use CTE pre-filter pattern (not PERCENTILE_CONT WITHIN GROUP FILTER, which has uncertain DuckDB support for ordered-set aggregates).

**Completeness pattern:** IN-GAME columns are 87–91% NULL: `feudal_age_uptime` (~87% NULL), `castle_age_uptime` (~89% NULL), `imperial_age_uptime` (~91% NULL), `opening` (~67% NULL). All other columns are <1% NULL.

**Distribution findings (QQ plots):** duration, avg_elo, team_0/1_elo show strong non-normality (heavy right tails, leptokurtic). old_rating and new_rating are approximately normal at this scale. match_rating_diff is near-normal with moderate tails. Age uptime columns show distinct bounded non-normal distributions (effective N ~6,500 per panel after dropna; documented in subplot titles per W2 fix).

**ECDF findings:** team_0/1_elo and old_rating show similar bell-shaped cumulative distributions centered near 1000–1200 ELO. match_rating_diff ECDF is near-symmetric around zero with fat tails.

**Duplicate detection:** players_raw uses census-aligned COALESCE string-concatenation key (`CAST(game_id AS VARCHAR) || '_' || COALESCE(CAST(profile_id AS VARCHAR), '__NULL__')`). Result: 489 duplicate rows, matching 01_02_04 census.

**Linkage integrity:** players_without_match = 0, matches_without_players = 212,890.

**Winner class balance:** near-equal split (confirmed from class_balance sub-dict in profile JSON).

**SQL queries:** All embedded verbatim in markdown artifact (I6). Key queries: matches_numeric_profile, elo_no_sentinel (CTE pre-filter), duplicate_players (COALESCE key), match_linkage, qq_matches_sample, qq_players_sample, ecdf_sample.

---

## 2026-04-15 — [Phase 01 / Step 01_02_06] Statistical Tests (pass-3 addition)

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** Mann-Whitney U tests with rank-biserial r added to bivariate EDA

### 01_02_06 — Statistical Tests (pass-3 addition, 2026-04-15)

Added Mann-Whitney U tests for old_rating and match_rating_diff (both PRE-GAME).
Sample: RESERVOIR(5M) per query; SE(r) = 0.00045.
- old_rating by winner: r_rb = -0.0159 (small effect; pre-game rating alone is weak signal)
- match_rating_diff by winner: r_rb = -0.2041 (medium effect; confirmed PRE-GAME from T03 scatter, not leakage)
Cross-game note: matches sc2egset Mann-Whitney U reporting (I8 compliance).

---

## 2026-04-15 — [Phase 01 / Step 01_02_07] Multivariate EDA

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** multivariate -- cross-table Spearman heatmap, PCA scree, PCA biplot
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.json`
- `reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_07_spearman_heatmap_all.png`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_07_pca_scree.png`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_07_pca_biplot.png`

### What

Produced 3 thesis-grade multivariate analyses on a 20,000-row RESERVOIR sample from a
cross-table JOIN of players_raw (107.6M rows) and matches_raw (30.7M rows). Sample size
justified by JOIN cost; SE(rho) ~0.007 at N=20K (Invariant #7). All SQL embedded verbatim
(Invariant #6). POST-GAME and IN-GAME columns annotated on heatmap axis labels (Invariant #3).
No cleaning decisions, no feature engineering, no model fitting (Invariant #9).

Spearman correlation computed via pandas `.corr(method='spearman')` (pairwise deletion),
not scipy matrix form (which uses listwise deletion and would have reduced the effective
sample from ~20K to ~1.7K rows due to 87%-NULL age uptime columns). Minimum pairwise N
asserted >= 1,000 rows.

### Spearman Heatmap Findings

The cluster ordering groups features by correlation magnitude. Three clusters emerge:

1. **ELO cluster** (rho > 0.98): avg_elo, team_0_elo, team_1_elo are near-perfectly
   correlated with each other (rho 0.9826--0.9958). old_rating and new_rating also join
   this cluster (old_rating x avg_elo rho=0.983; new_rating x avg_elo rho=0.981). This
   confirms massive ELO feature redundancy.

2. **match_rating_diff** is near-orthogonal to the ELO cluster (rho near zero with all
   ELO features). PC2 analysis confirms it is an independent dimension of variation.

3. **duration_sec** and **age uptime columns** (feudal/castle/imperial) form a separate
   cluster with weak correlations to ELO features, consistent with their POST-GAME /
   IN-GAME temporal class and high NULL rate (~87-91%).

4. Cross-table correlations between match-level ELO columns (avg_elo, team_0/1_elo) and
   player-level ELO columns (old_rating, new_rating) are high because all three match-level
   columns are repeated for every player in the JOIN. The authoritative within-table
   correlations remain those from 01_02_06.

### PCA Findings (Pre-Game Features Only)

Features: old_rating, match_rating_diff, avg_elo, team_0_elo, team_1_elo (N=20,000).

- **PC1: 79.21% variance.** Loadings nearly equal for old_rating (0.499), avg_elo (0.502),
  team_0_elo (0.500), team_1_elo (0.499); match_rating_diff loading near zero (0.022).
  PC1 captures the shared ELO axis -- this is a rating level factor, not a latent feature.
- **PC2: 20.11% variance (cumulative 99.33%).** Dominated by match_rating_diff (loading
  0.996). PC2 is effectively the match_rating_diff dimension alone.
- **PC3-5: <0.4% each.** Essentially numerical noise after the ELO and match_rating_diff
  axes are captured.
- **Two components explain 99.3% of variance.** The five pre-game features are nearly
  two-dimensional. ELO redundancy (avg_elo, team_0_elo, team_1_elo, old_rating) means
  keeping all four adds marginal information. Retention decision deferred to Phase 02.

### PCA Biplot Findings

- Scatter of 20K rows coloured by winner shows no visible cluster separation in PC1/PC2 space.
  Winner does not cleanly separate along the ELO axis or the match_rating_diff axis.
- All four ELO features point in nearly identical directions (PC1 direction), confirming
  near-perfect redundancy. match_rating_diff points perpendicular (PC2 direction).
- This is consistent with the bivariate finding that ELO features have weak but non-zero
  predictive value; the lack of winner separation in PCA space suggests the signal is
  distributed and not concentrated in a simple projection.

### Decisions / Column Classification Confirmed

All column classifications are documented and ready for thesis draft; `old_rating` is classified as PRE-GAME by schema inference (pre-match rating), not by bivariate temporal test:

| Column | Temporal Class | PCA | Notes |
|--------|---------------|-----|-------|
| old_rating | PRE-GAME | Yes | ELO cluster, high redundancy with avg_elo |
| match_rating_diff | PRE-GAME | Yes | Confirmed PRE-GAME in 01_02_06; PC2 |
| avg_elo | PRE-GAME | Yes | ELO cluster -- effectively = mean(team_0_elo, team_1_elo) |
| team_0_elo | PRE-GAME | Yes | ELO cluster |
| team_1_elo | PRE-GAME | Yes | ELO cluster |
| new_rating | POST-GAME | No | Excluded from PCA and from pre-game prediction |
| duration_sec | POST-GAME | No | Excluded from PCA and from pre-game prediction |
| feudal_age_uptime | IN-GAME, 87% NULL | No | Excluded from PCA |
| castle_age_uptime | IN-GAME, 88% NULL | No | Excluded from PCA |
| imperial_age_uptime | IN-GAME, 91% NULL | No | Excluded from PCA |

Pipeline section 01_02 (Exploratory Data Analysis) is now complete for aoestats.
Phase 02 (Feature Engineering) may proceed.

---

## 2026-04-15 — [Phase 01 / Step 01_02_06] Bivariate EDA

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** bivariate — pairwise relationships between features and match outcome
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.json`
- `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_06_*.png` (8 files)

### What

Produced 8 thesis-grade PNG plots examining pairwise relationships between features
and `winner` in players_raw (107.6M rows) and matches_raw (30.7M rows). Key analyses:
leakage scatter for `match_rating_diff` (Phase 02 blocker), `old_rating` by winner
violin, ELO panel, duration violin, opening win rate bar chart, age uptime violin,
Spearman correlation matrix, and multi-panel numeric features. All thresholds derived
from 01_02_04 census at runtime (Invariant #7). ELO sentinel (-1) excluded. POST-GAME
column tick labels marked with asterisk in Spearman heatmap. Age uptime and opening
analyses restricted to ~14% non-NULL subset (schema change boundary). DuckDB
connections read_only=True; no DDL.

### Plots produced

| Plot | Subject |
|------|---------|
| `01_02_06_match_rating_diff_leakage_scatter` | match_rating_diff vs (new_rating−old_rating) scatter (leakage test) |
| `01_02_06_old_rating_by_winner` | old_rating violin by winner (pre-game ELO predictor) |
| `01_02_06_elo_by_winner` | team_0_elo and team_1_elo panel by winner |
| `01_02_06_duration_by_winner` | Duration violin by winner (POST-GAME descriptor) |
| `01_02_06_numeric_by_winner` | Multi-panel numeric features by winner |
| `01_02_06_opening_winrate` | Opening win rate bar chart (Wilson score CI) |
| `01_02_06_age_uptime_by_winner` | Age uptime violin by winner (non-NULL subset only) |
| `01_02_06_spearman_correlation` | Spearman correlation matrix (scipy.stats.spearmanr on 20K sample) |

### Key findings

- **match_rating_diff — PRE-GAME SAFE (Phase 02 blocker RESOLVED):** Pearson r = 0.053
  between `match_rating_diff` and `new_rating − old_rating`; only 0.66% of rows have
  `|match_rating_diff − (new_rating − old_rating)| < 0.01`. Definitively refutes H1
  (that match_rating_diff = post-game rating change). The column encodes something
  other than the post-game rating delta — most likely a pre-game opponent rating
  difference or handicap value. **Safe to include in Phase 02 feature sets.**
- **old_rating × winner:** Pre-game ELO shows measurable distributional separation by
  winner. Winners have marginally higher old_rating, consistent with a predictive
  pre-game signal.
- **Opening win rate:** Some opening types show noticeably higher win rates than others.
  Wilson score CIs show which differences are reliable vs. noise (large-n openings only).
- **Age uptime columns (87% NULL):** Bivariate analysis on non-NULL subset confirms
  expected relationship; must note the selectivity bias in thesis (non-NULL = post-schema-change games only).

### Decisions

- `match_rating_diff` → PRE-GAME SAFE; include in Phase 02 feature engineering candidates
- `old_rating` → confirmed pre-game ELO predictor; include
- `new_rating` → post-game; exclude from all feature sets
- Post-game columns (`new_rating`, `match_result`) → excluded from feature sets

### Open questions

- What exactly does `match_rating_diff` encode? Opponent rating gap, handicap, or something else?
  Semantic clarity needed before thesis feature description.
- Do opening types (87% NULL) have enough non-NULL coverage to train on? Depends on Phase 02 target window selection.

---

## 2026-04-15 — [Phase 01 / Step 01_02_05] Univariate Visualizations

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** visualization
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_05_*.png` (15 files)

### What

Produced 15 thesis-grade PNG plots visualizing the 01_02_04 census findings for
matches_raw (30.7M rows) and players_raw (107.6M rows). Temporal annotations applied
to all in-game and post-game columns (Invariant #3). All SQL queries embedded in
the markdown artifact (Invariant #6). All thresholds derived from census (Invariant #7).

### Plots produced

| Plot | Subject |
|------|---------|
| `winner_distribution` | Target balance — winner True/False per match; balanced binary label |
| `num_players_distribution` | Match size distribution (1v1 dominant); using `distinct_match_count` not `row_count` |
| `map_top20` | Top-20 maps by match count |
| `civ_top20` | Top-20 civilizations by player-row count |
| `leaderboard_distribution` | Match counts per leaderboard tier |
| `duration_histogram` | Dual-panel body (0–78.6 min, p95-clipped) + full log-scale; duration in BIGINT nanoseconds converted via `/ 1e9` |
| `elo_distributions` | ELO 3-panel (team_0, team_1, avg); sentinel values (−1.0) excluded from team panels, not from avg_elo |
| `old_rating_histogram` | Pre-match rating distribution from players_raw |
| `match_rating_diff_histogram` | match_rating_diff body clipped at ±200 (~3.6σ, editorial); LEAKAGE UNRESOLVED annotation applied |
| `age_uptime_histograms` | Feudal / Castle / Imperial age-up times; all three IN-GAME annotated; ~87% NULL confirmed visually |
| `opening_nonnull` | opening strategy frequency among the ~14% of non-NULL rows; IN-GAME annotated |
| `iqr_outlier_summary` | IQR-fence outlier counts per numeric column |
| `null_rate_bar` | 4-tier NULL severity across all matches_raw + players_raw columns |
| `schema_change_boundary` | Weekly NULL rate for 86%-NULL columns in players_raw over time; IN-GAME annotated; column list derived from census `null_pct > 80%` at runtime |
| `monthly_match_count` | Monthly match volume 2022-08–2026-02 |

### Decisions taken

- Duration clip: p95 = 4,714.1s = 78.6 min (from census `numeric_stats_matches` label `"duration_sec"`). Above p95, log-panel tail shows extreme outliers. Cross-dataset note in subtitle vs aoe2companion (63.15 min).
- `match_rating_diff` clip: ±200 is an editorial choice (~3.6σ from stddev=55.23) to show leptokurtic shape without [-2185, +2185] range extremes; NOT derived from p05/p95 (which are ±59). I7 comment documents this.
- `avg_elo` histogram: no sentinel exclusion applied (sentinel impact negligible at 30.7M rows). Documented as asymmetric treatment vs team_0/1_elo in the markdown artifact.
- `schema_change_boundary`: column list derived at runtime from `census["players_null_census"]["columns"]` filtered by `null_pct > 80.0`. Filename-based temporal join (chars 9-18 of `players/YYYY-MM-DD_...` format) — no cross-table JOIN required.

### Decisions deferred

- `match_rating_diff` leakage resolution (post-game vs. pre-game) deferred to 01_02_06 Bivariate EDA (scatter vs `new_rating − old_rating`). Current I3 annotation: LEAKAGE STATUS UNRESOLVED.
- Schema change exact breakpoint date deferred — `schema_change_boundary` plot visually identifies the boundary but formal threshold analysis deferred to Phase 01_04 Data Cleaning.
- `avg_elo` sentinel asymmetry treatment deferred to Phase 01_04.

### Thesis mapping

- Chapter 4, §4.1.3 — AoE2 aoestats feature landscape, target balance, NULL structure
- Chapter 4, §4.1.4 — in-game column annotations (age uptimes, opening strategy)

### Open questions / follow-ups

- `match_rating_diff` leakage: the 01_02_06 bivariate scatter (`match_rating_diff` vs `new_rating − old_rating`) will resolve this. Feature engineering for Phase 02 blocked on this result.
- Schema change boundary: visual inspection of `schema_change_boundary` plot will reveal the exact week when age uptime / opening columns transitioned from ~0% to ~100% populated.

---

## 2026-04-15 — [Phase 01 / Step 01_02_04] Univariate Census & Target Variable EDA

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** query
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md`
- `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`

### What

Full univariate census of matches_raw (30,690,651 rows, 18 cols) and players_raw (107,627,584 rows, 14 cols). Covers NULL landscape, cardinality, categorical frequency distributions, numeric descriptive statistics with skewness/kurtosis, ELO sentinel analysis, join integrity, duplicate detection, and preliminary temporal-leakage field classification per Invariant #3. All SQL embedded in .md artifact (Invariant #6). Note: overviews_raw (1 row, 9 cols) was documented in 01_02_01/01_02_03 and is not a per-match profiling target.

### Tables profiled

| Table | Rows | Columns |
|-------|------|---------|
| `matches_raw` | 30,690,651 | 18 |
| `players_raw` | 107,627,584 | 14 |

### NULL landscape

**matches_raw:** Near-zero nulls. Only `raw_match_type` has any nulls (12,504 rows, 0.04%). All other 17 columns fully populated.

**players_raw — four columns with extreme null rates (co-occurring on ~86% of rows):**
- `feudal_age_uptime`: 87.08% NULL (93.7M rows)
- `castle_age_uptime`: 87.93% NULL (94.6M rows)
- `imperial_age_uptime`: 91.49% NULL (98.5M rows)
- `opening`: 86.05% NULL (92.6M rows)

Co-occurrence confirmed: exactly 92,616,290 rows have all four NULL simultaneously — this is the pre-schema-change population (earlier weekly files lacking these columns), not individual missing values. Imputation is not meaningful for these columns.

### Target variable (`winner`)

Zero nulls across all 107.6M rows. Near-perfect 50/50 balance: 53,811,187 true (50.00%) vs 53,816,397 false (50.00%). No class imbalance mitigation required.

### Match size distribution

- 1v1 (num_players=2): 60.56% of rows — primary modelling scope
- 4-player: 16.48%; 8-player: 14.04%; 6-player: 8.92%
- Odd player counts (1, 3, 5, 7): 1,067 rows — data quality anomalies, filter in cleaning

### ELO / rating analysis

- `avg_elo` in matches_raw: mean 1,087.6, median 1,055.0, std 309.5. 121 rows with avg_elo=0 (unrated matches; not sentinel -1). Sentinel -1 affects < 0.001% of team_0/team_1_elo rows.
- `old_rating` in players_raw: mean 1,091.1, median 1,066.0, std 286.9 — **the authoritative pre-game rating column.** 5,937 zero-valued rows.
- `new_rating`: mean 1,090.8 — post-game column (must never be used as a feature, Invariant #3).
- `match_rating_diff`: mean 0.0, symmetric, but extreme kurtosis (65.7); range [-2,185, +2,185]. Leakage status unresolved: could be (new_rating - old_rating) = post-game, or (player_elo - opponent_elo) = pre-game. Verification query documented but not yet executed.
- Usable ELO fraction: effectively 100%. Sentinel -1 affects < 0.001% of matches.

### Categorical distributions

**matches_raw:**
- `map`: 93 distinct values. Top: arabia 34.94%, arena 19.02%, nomad 6.94%, black_forest 6.42%
- `leaderboard`: random_map 58.52%, team_random_map 37.53%
- `game_type`: constant "random_map" (100%) — dead column
- `game_speed`: constant "normal" (100%) — dead column
- `starting_age`: 99.99%+ "dark" (19 non-"dark" rows) — dead column
- `patch`: 19 distinct values; largest patch_125283 at 17.83%
- `mirror` (same-civ matchup): 2.32%

**players_raw:**
- `civ`: 50 distinct civilizations. Top: franks 5.59%, mongols 5.24%, persians 4.29%, britons 4.03%
- `opening` (non-null only, 15M rows): fast_castle 27.98%, unknown 23.91%, scouts 14.10%, archers 13.15%
- `team`: perfectly balanced at 50/50

### Temporal leakage audit (Invariant #3)

**Post-game (must exclude):** `duration`, `irl_duration`, `new_rating`

**In-game (unavailable at prediction time):** `opening`, `feudal_age_uptime`, `castle_age_uptime`, `imperial_age_uptime`, `replay_summary_raw`

**Deferred — leakage unknown:** `match_rating_diff` — requires empirical verification before Phase 02 feature engineering

**Safe pre-game features:** `map`, `started_timestamp`, `num_players`, `avg_elo`, `team_0_elo`, `team_1_elo`, `leaderboard`, `patch`, `raw_match_type`, `starting_age` (matches_raw); `team`, `civ`, `old_rating` (players_raw)

> **[Retroactive correction 2026-04-16]:** `mirror` removed from safe pre-game list. Reclassified POST-GAME in 01_03_01 -- same-civ determination requires both players' civ selections, which are finalized only at match start.

### Duration distribution

Mean 2,613.7s (~43.6 min), median 2,619.7s. Extreme right skew (skewness 1,032.6) from outliers up to 5,574,815s (~64 days). 2.33% IQR outliers above 5,496s. IRL duration mean 1,537.5s (~25.6 min).

### Data quality flags

- **Orphans:** 0 player rows without a match; **212,890 match rows without any players** (0.69%) — corresponds to the 1-week file gap identified in 01_01_01
- **Duplicates:** matches_raw has 0 on game_id (30,690,651 distinct). players_raw has 489 duplicate (game_id, profile_id) pairs — negligible
- **profile_id** range: min 18, max 24,853,897 — below 2^53, no precision loss from DOUBLE promotion

### Decisions taken

- `new_rating` classified post-game and flagged for exclusion
- `game_type`, `game_speed`, `starting_age` classified as dead constant columns — will be dropped
- `opening` and age uptimes classified as in-game features (available for only ~14% of player rows)
- `match_rating_diff` leakage test deferred to a targeted verification query before Phase 02

### Decisions deferred

- `match_rating_diff` verification: `SELECT COUNT(*) FROM players_raw WHERE ABS(match_rating_diff - (new_rating - old_rating)) < 0.01` — must execute before Phase 02
- ELO=0 interpretation (0 = valid unrated or sentinel?) — low priority given 4,824 occurrences
- Imputation strategy for `opening`/age uptimes (86-91% NULL) — likely not imputable; schema change pattern
- Handling of 212,890 orphan matches without player data
- Whether to restrict modelling scope to 1v1 (60.56%) vs including team games

### Thesis mapping

- Chapter 4, section 4.1.2 — AoE2 dataset: target distribution, ELO landscape, field classification
- Chapter 4, section 4.2 — Pre-processing: post-game column exclusion, dead column identification
- Chapter 5, section 5.1 — Feature catalogue: pre-game candidates enumerated

### Open questions / follow-ups

- Is `match_rating_diff` the pre-match ELO gap (high-value pre-game feature) or the post-match rating change (leakage)? This is the critical open question. Verification query is ready.
- Should 1v1 only or all team sizes be included in the modelling scope?
- Can overviews_raw civs/openings/patches reference arrays decode numeric IDs or enrich civ metadata?
- The 86% null rate on opening/age uptimes — exclude entirely, or use for the 14% subset?

---

## 2026-04-14 — [Phase 01 / Step 01_02_03] Raw schema DESCRIBE

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** query
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_03_raw_schema_describe.json`
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/matches_raw.yaml`
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/players_raw.yaml`
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/overviews_raw.yaml`

### What

Captured the exact DuckDB column names and types for all three aoestats `*_raw` tables by connecting read-only to the persistent DuckDB and running `DESCRIBE` on each table.

### Why

Establish the source-of-truth bronze-layer schema for downstream steps. The `data/db/schemas/raw/*.yaml` files are consumed by feature engineering and documentation steps. Invariant #6 — DESCRIBE SQL embedded in artifact.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_03_raw_schema_describe.py`

Read-only connection to `data/db/db.duckdb`. `DESCRIBE <table>` for each of the three `*_raw` tables.

### Findings

| Table | Columns | Notable types |
|-------|---------|---------------|
| matches_raw | 18 | `started_timestamp` TIMESTAMP WITH TIME ZONE; `duration`/`irl_duration` BIGINT (nanoseconds); `raw_match_type` DOUBLE |
| players_raw | 14 | `winner` BOOLEAN (prediction target); `profile_id` DOUBLE; age uptimes DOUBLE; `opening` VARCHAR |
| overviews_raw | 9 | `civs`/`openings`/`patches`/`groupings`/`changelog` are STRUCT arrays; `tournament_stages` VARCHAR[] |

Key observations:
- `winner` (BOOLEAN, nullable) in `players_raw` confirmed as prediction target
- `profile_id` remains DOUBLE (promoted from int64/double variant source) — precision-loss risk flagged in 01_02_01 still open
- `duration`/`irl_duration` are BIGINT nanoseconds (Arrow `duration[ns]` promoted) — requires `/1e9` conversion for seconds in downstream queries
- `overviews_raw` has deeply nested STRUCT columns — reference metadata only, not a feature source
- All three schema YAMLs populated in `data/db/schemas/raw/`

### Decisions taken

- Schema YAMLs populated from this DESCRIBE output — source-of-truth for all downstream steps
- No schema modifications — read-only step

### Decisions deferred

- `profile_id` DOUBLE→BIGINT cast precision check — deferred to Step 01_04 (data cleaning)
- Column descriptions (`TODO: fill`) in `*.yaml` — deferred to 01_03

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset: bronze-layer schema catalog

### Open questions / follow-ups

- Does `profile_id` DOUBLE cause precision loss for any actual ID values in this dataset? (deferred to 01_04)

---

## 2026-04-14 — [Phase 01 / Step 01_02_02] DuckDB Ingestion

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** ingestion
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.md`

### What

Re-executed full ingestion of all three aoestats raw sources into the persistent DuckDB (`data/db/db.duckdb`). Supersedes the initial ingestion performed within 01_02_01 by applying Invariant I10-compliant relative filenames and renaming tables from `raw_*` prefix to `*_raw` suffix convention.

### Why

Invariant I10 required `filename` column to store paths relative to `raw_dir`. Table naming aligned with `*_raw` suffix convention used by sc2egset and aoe2companion. All ingestion SQL lives in `src/rts_predict/games/aoe2/datasets/aoestats/ingestion.py`.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_02_duckdb_ingestion.py`

### Findings

Row counts:
- `matches_raw`: 30,690,651 rows
- `players_raw`: 107,627,584 rows
- `overviews_raw`: 1 row

Row counts match the 01_02_01 initial ingestion, confirming data integrity.

Ingestion strategy:
- `matches_raw` / `players_raw`: `read_parquet` with `union_by_name=true`, `filename=true`, loaded in file-level batches (default 10 files per batch) — `CREATE TABLE ... AS SELECT` for the first batch, `INSERT INTO ... BY NAME SELECT` for subsequent batches. Batching avoids OOM on the full 171-file / 107.6M-row `players_raw` set.
- `overviews_raw`: `read_json_auto` on singleton `overview.json`, `filename=true`
- Invariant I10 (relative filenames): enforced inline via `SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)` in every CTAS and INSERT query. Post-load `UPDATE SET filename = substr(...)` was removed because it caused OOM on the 107.6M-row `players_raw` table. Only `overviews_raw` (1 row) uses post-load UPDATE.

### Decisions taken

- Tables named with `*_raw` suffix convention — consistent with sc2egset and aoe2companion
- File-level batched loading (CREATE + INSERT BY NAME) for `matches_raw` and `players_raw` to avoid OOM; default `batch_size=10` files per batch
- Invariant I10 via inline `SELECT * REPLACE` — no post-load UPDATE on large tables

### Artifact note

The `.json` artifact (`01_02_02_duckdb_ingestion.json`) is a minimal stub containing only row counts — no SQL, schema, NULL rates, or I10 verification. Both artifacts should be regenerated from a fresh notebook run. The discrepancy is tracked here.

### Decisions deferred

- None for this step

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset: bronze-layer ingestion

### Open questions / follow-ups

- None specific to this step — all open questions from 01_02_01 remain active

---

> **2026-04-14 amendment:** The original 01_02_01 heading says "DuckDB pre-ingestion investigation" but the artifact (`01_02_01_duckdb_pre_ingestion.json`) has `"type": "full_ingestion"` and contains `tables_created`, DDL, DESCRIBE output, and NULL counts — it performed full ingestion, not just investigation. The body accurately states "Ingested all three raw data sources" but the heading and step scope label are misleading. The canonical ingestion is step 01_02_02, which re-executed with Invariant I10-compliant relative filenames and renamed tables (`raw_matches` → `matches_raw`, `raw_players` → `players_raw`, `raw_overviews` → `overviews_raw`). Findings in the 01_02_01 entry (variant columns, NULL counts, duration types, missing week) remain valid.

## 2026-04-13 — [Phase 01 / Step 01_02_01] DuckDB pre-ingestion investigation

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** query
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json`

### What

Ingested all three raw data sources into DuckDB (`matches_raw`, `players_raw`,
`overviews_raw`) and validated types, null rates, and variant column behaviour
against 01_01_02 schema discovery findings.

### Why

Materialise the bronze layer. This dataset has known variant columns
(type changes across weekly Parquet files) requiring `union_by_name=true`.
Invariant #7 (type fidelity) — verify DuckDB's automatic type promotion.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py`

### Findings

- `matches_raw`: 30.7M rows, 18 columns. Two variant columns: `started_timestamp` (mixed us/ns precision across files, promoted to TIMESTAMP WITH TIME ZONE), `raw_match_type` (mixed int64/double, promoted to DOUBLE)
- `players_raw`: 107.6M rows, 14 columns. Five variant columns: `feudal_age_uptime`, `castle_age_uptime`, `imperial_age_uptime` (double in 82/81/81 files, null-typed in 89/90/90 files — promoted to DOUBLE with NULL fill); `profile_id` (int64 in 135 files, double in 36 files — promoted to DOUBLE); `opening` (string in 82 files, null-typed in 89 — promoted to VARCHAR)
- `overviews_raw`: 1 row, 9 columns. Contains STRUCT arrays for civs, openings, patches, groupings, changelog
- `duration` and `irl_duration` mapped from Arrow duration[ns] to BIGINT nanoseconds (not INTERVAL as might be expected)
- `profile_id` as DOUBLE: precision loss risk for IDs > 2^53, but only 1,185 NULLs out of 107.6M rows
- Missing week: `2025-11-16_2025-11-22` has matches but no player-level data (1 week gap out of 172)

### Decisions taken

- Raw layer uses `SELECT *` with `union_by_name=true, filename=true` — let DuckDB handle type promotion at bronze layer
- `profile_id` DOUBLE type flagged but not altered — precision check deferred to cleaning step
- Duration stored as BIGINT nanoseconds — will need division by 1e9 for seconds in queries

### Decisions deferred

- `profile_id` DOUBLE→BIGINT cast: need to verify no precision loss for actual ID values in the dataset
- Whether the 89 null-typed `opening` files represent a schema change or genuinely absent data
- Whether `feudal_age_uptime` NULLs (87% of rows) indicate games not reaching Feudal Age or missing data

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset description, variant column handling
- Chapter 4, §4.2.1 — Ingestion validation, DuckDB type promotion behaviour

### Open questions / follow-ups

- Is `profile_id` precision loss actually occurring for any real IDs in this dataset?
- What caused the schema break in player files around week 89/172 (~mid-2024)?
- Are the age uptime NULLs meaningful (game ended before that age) or data quality issues?

---

## 2026-04-13 — [Phase 01 / Step 01_01_02] Schema discovery

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** content
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.md`

### What

Full census of all 344 Parquet files plus the singleton overview JSON.
Catalogued column names, physical types, nullability, and critically —
variant columns where physical type changes across weekly files.

### Why

Map the exact schema per file, identifying type inconsistencies that will
affect DuckDB ingestion. Invariant #6 requires knowing field types.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_02_schema_discovery.py`

### Findings

- Matches: 17 columns, 2 variant columns (`started_timestamp` mixed us/ns precision, `raw_match_type` mixed int64/double)
- Players: 13 columns, 5 variant columns (`feudal_age_uptime`, `castle_age_uptime`, `imperial_age_uptime` appear as double or null-typed; `profile_id` appears as int64 or double; `opening` appears as string or null-typed)
- Overview: singleton JSON with nested STRUCT arrays (civs, openings, patches, groupings, changelog)
- `duration` and `irl_duration` are Arrow duration[ns] type (not timestamp)

### Decisions taken

- Full census used (344 files is manageable)
- Variant columns documented with exact file counts per type — critical input for ingestion

### Decisions deferred

- How to handle variant columns at ingestion — deferred to 01_02_01

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset schema, variant column documentation

### Open questions / follow-ups

- Why do player files switch from having `opening`/age uptimes to not having them mid-dataset?
- Is the `profile_id` int64→double transition a data source version change?

---

## 2026-04-13 — [Phase 01 / Step 01_01_01] File inventory

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** filesystem
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`

### What

Catalogued the aoestats raw data directory: 3 subdirectories (matches, players,
overview), file counts, sizes, extensions, and temporal coverage via filename
date range parsing.

### Why

Establish the data landscape. Invariant #9 — filesystem-level inventory before
content inspection.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py`

### Findings

- 349 total files across 3 subdirectories, 3.7 GB total
- Matches: 172 weekly Parquet files (611 MB), 2022-08-28 to 2026-02-07
- Players: 171 weekly Parquet files (3.2 GB), aligned with matches minus 1 week
- Overview: 1 singleton JSON (22 KB)
- 3 temporal gaps identified: 43-day gap at 2024-07-20→2024-09-01, plus two 8-day gaps
- File count mismatch: 172 match weeks vs 171 player weeks (1 week has matches but no players)

### Decisions taken

- Weekly granularity confirmed — files named by date range (e.g., `2022-08-28_2022-09-03`)
- Temporal gaps documented for downstream awareness

### Decisions deferred

- Internal file structure deferred to 01_01_02

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset description, temporal coverage, data gaps

### Open questions / follow-ups

- Is the 43-day gap (July–September 2024) a data collection outage or intentional?
