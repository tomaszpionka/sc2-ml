# Research Log — AoE2 / aoe2companion

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

AoE2 / aoe2companion findings. Reverse chronological.

---

## 2026-04-16 — [Phase 01 / Step 01_03_01] Systematic Data Profiling

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** profiling (read-only — no DuckDB writes, no new tables)
**Artifacts produced:**
- `reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json`
- `reports/artifacts/01_exploration/03_profiling/01_03_01_completeness_heatmap.png`
- `reports/artifacts/01_exploration/03_profiling/01_03_01_qq_plot.png`
- `reports/artifacts/01_exploration/03_profiling/01_03_01_ecdf_key_columns.png`
- `reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md`

### What

Systematic profiling of matches_raw (277,099,059 rows, 55 columns) per Manual Section 3. Consolidates and extends 01_02 census findings into a structured, machine-readable profile. All SQL queries written verbatim to artifacts (Invariant #6).

### Column-level profiling

55 columns profiled with: null count/pct, approximate cardinality, uniqueness ratio, zero count for numeric columns, descriptive stats (mean, std, percentiles from census), exact skewness/kurtosis for all 10 numeric columns (9 from census + derived duration_min) via DuckDB native SKEWNESS()/KURTOSIS() aggregation over the full table (no sampling, no listwise deletion), IQR outlier counts via consolidated single-scan query, and top-5 values for 21 categorical columns.

All columns carry I3 temporal classification (Invariant #3). Rating classified as AMBIGUOUS per 01_02_06 finding. Resolution deferred to 01_04. **[Note]:** Rating ambiguity resolution is assigned to 01_04 (Data Cleaning), not Phase 02 -- the temporal join with ratings_raw is a data investigation prerequisite, not a feature engineering decision.

### Dataset-level profiling

- **Primary key integrity (matchId, profileId):** Duplicates confirmed. 3,589,428 duplicate (matchId, profileId) groups containing 12,401,433 total rows (4.47% of 277M). Deduplication required in 01_04.
- **Class balance (won):** False=132,150,323 (47.69%), True=131,963,175 (47.62%), NULL=12,985,561 (4.69%). Balanced binary classification target.
- **Memory footprint:** Computed via DuckDB `pragma_database_size()`.

### Duplicate metric reconciliation

Two steps measured the same duplication phenomenon with different counting methods:
- **01_02_04 census:** 8,812,005 excess rows = total_rows (277,099,059) minus distinct (matchId, profileId) pairs (268,287,054). Counts only the surplus beyond the first occurrence.
- **01_03_01 profile:** 12,401,433 rows in 3,589,428 groups with count > 1. Counts all rows in any group that has duplicates, including the first occurrence.
Both metrics are correct; the 01_03_01 count is strictly larger because it includes the "keeper" row in each group. The actionable number for 01_04 deduplication is 8,812,005 rows to remove (retaining one row per group).

### Critical findings

- **Dead fields (0):** None.
- **Constant columns (0):** None.
- **Near-constant columns (50):** speedFactor (IQR=0), population (IQR=0), treatyLength (IQR=0) confirmed; many categorical game-setting columns flagged. Inform Phase 02 feature exclusion decisions.

### Distribution analysis

QQ plots (5 columns) and ECDFs (3 columns) from BERNOULLI 0.02% sample (~55,414 rows). Skewness/kurtosis exact over full 277M rows:
- rating: skew=0.4654, excess kurtosis=0.3047 (slightly right-skewed, near-symmetric)
- duration_min: right-skewed (long-tail matches)

### Rating stratification

| Scope | N Rows | Rating NULL % | Rating Mean |
|-------|--------|---------------|-------------|
| full_table | 277,099,059 | 42.46% | 1120.23 |
| 1v1_ranked (rm_1v1 + qp_rm_1v1) | 61,071,799 | 26.21% | 1091.65 |

Rating NULL rate notably lower in 1v1 ranked matches. Remaining 26.21% NULL in 1v1 requires 01_04 join with ratings_raw for resolution.

---

## 2026-04-15 — [Phase 01 / Step 01_02_06] Statistical Tests (pass-3 addition)

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** Mann-Whitney U tests with rank-biserial r added to bivariate EDA

### 01_02_06 — Statistical Tests (pass-3 addition, 2026-04-15)

Added Mann-Whitney U tests for ratingDiff (POST-GAME leakage diagnostic) and rating (AMBIGUOUS).
- ratingDiff by won: r_rb = -1.0 (near -1.0 confirms POST-GAME leakage — winners have ratingDiff > 0, losers < 0, perfectly separated)
- rating by won: r_rb = -0.0086 (near 0 supports AMBIGUOUS classification — negligible discriminative power)
Cross-game note: PRE-GAME effect sizes now comparable to sc2egset MMR (r=-0.09).

---

## 2026-04-15 — [Phase 01 / Step 01_02_07] Multivariate EDA

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** multivariate — feature cluster structure and effective dimensionality of the pre-game numeric space
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_07_spearman_heatmap_all.png`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_07_pca_biplot.png` (degenerate fallback)

### What

Produced 2 thesis-grade PNG plots examining the multivariate structure of numeric
features in matches_raw (277M rows; sampled to ~100K via BERNOULLI for Spearman).
Analysis A: Spearman cluster-ordered correlation heatmap for all 7 numeric columns
with I3 classification labels on axes (POST-GAME, AMBIGUOUS, PRE-GAME).
Hierarchical clustering on 1-|rho| distance matrix (UPGMA). Analysis B: PCA
degeneracy determination from census IQR statistics (I7 -- no magic numbers).

### Plots produced

| Plot | Subject |
|------|---------|
| `01_02_07_spearman_heatmap_all` | Spearman heatmap, all 7 numeric columns, cluster-ordered, I3-labelled axes |
| `01_02_07_pca_biplot` | Degenerate PCA fallback -- text summary (0 viable pre-game features) |

### Key findings

- **Spearman heatmap:** ratingDiff and rating show strong positive correlation
  (rho approximately +0.5–0.7), consistent with rating encoding a mix of pre-game
  and post-game information. duration_min is largely independent of the pre-game
  features. speedFactor, treatyLength, and population show near-zero correlation
  with all other features and with each other, consistent with their near-constant
  distributions in 1v1 ranked play.
- **NaN handling in Spearman matrix:** Near-constant columns (speedFactor, treatyLength,
  population, internalLeaderboardId) produced NaN entries in the scipy spearmanr
  output due to zero rank variance in the filtered sample. NaNs filled with 0
  (uncorrelated) for clustering distance computation; p-values set to 1.0 (not
  significant). This is documented in the notebook output and is expected behavior.
- **PCA DEGENERATE -- confirmed:** All 3 PCA candidates fail the IQR==0 near-constant
  filter (population p25==p75==200.0; speedFactor p25==p75==1.70; treatyLength
  p25==p75==0.0). internalLeaderboardId excluded by design (nominal categorical).
  Result: 0 viable pre-game numeric features survive. PCA is meaningless.
- **Pre-game feature poverty -- confirmed:** aoe2companion matches_raw has effectively
  zero numeric pre-game features usable for machine learning without engineering.
  This is the central finding of the 01_02 EDA stack for this dataset.

### Decisions

- `speedFactor`, `treatyLength`, `population` → near-constant in 1v1 ranked; exclude
  from Phase 02 raw numeric feature set (IQR==0 confirmed from census)
- `internalLeaderboardId` → retained in heatmap (rank-correlation meaningful); excluded
  from PCA (nominal categorical with arbitrary integer codes)
- PCA branch → degenerate path; Phase 02 must engineer features from temporal history

### I3 classification applied

| Column | Classification | Applied |
|--------|----------------|---------|
| rating | AMBIGUOUS | Deferred to 01_04 (row-level verification with ratings_raw) |
| ratingDiff | POST-GAME | Excluded from all pre-game feature sets |
| duration_min | POST-GAME | EDA characterization only; not prediction feature |
| population | PRE-GAME | Near-constant; excluded from PCA |
| speedFactor | PRE-GAME | Near-constant; excluded from PCA |
| treatyLength | PRE-GAME | Near-constant; excluded from PCA |
| internalLeaderboardId | PRE-GAME | Nominal categorical; in heatmap, excluded from PCA |

### Open questions

- Does the ratingDiff/rating cluster in the Spearman heatmap confirm that rating
  is partially post-game? Requires 01_04 row-level join with ratings_raw.
- Can engineered features (rolling win rates, Elo trajectories, civ matchup stats)
  recover sufficient pre-game signal for Phase 02 modelling?

---

## 2026-04-15 — [Phase 01 / Step 01_02_06] Bivariate EDA

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** bivariate — pairwise relationships between features and match outcome
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_06_*.png` (8 files)

### What

Produced 8 thesis-grade PNG plots examining pairwise relationships between numeric
features and `won` (True/False) in matches_raw (277M rows; sampled to 100K via
BERNOULLI for Spearman). Ran conditional histograms and violin/box plots for all
primary numeric features, a Spearman correlation matrix (scipy.stats.spearmanr on
sample), and leaderboard-faceted ratingDiff distributions. All thresholds derived
from 01_02_04 census at runtime (Invariant #7). POST-GAME annotations applied to
`ratingDiff` and `duration` (Invariant #3).

### Plots produced

| Plot | Subject |
|------|---------|
| `01_02_06_ratingdiff_by_won` | ratingDiff conditional histogram (POST-GAME annotated) |
| `01_02_06_rating_by_won` | rating overlapping histogram by outcome (sentinel -1 excluded) |
| `01_02_06_rating_vs_ratingdiff` | rating vs ratingDiff scatter (BERNOULLI sample) |
| `01_02_06_duration_by_won` | Duration histogram by outcome (POST-GAME annotated, p95-clipped) |
| `01_02_06_numeric_by_won` | Multi-panel box-and-whisker: rating, ratingDiff, duration_min |
| `01_02_06_spearman_correlation` | Spearman correlation heatmap (6 numeric features, sampled) |
| `01_02_06_ratingdiff_by_leaderboard` | ratingDiff std by leaderboard bar chart |
| `01_02_06_ratingdiff_by_won_by_leaderboard` | Mean ratingDiff by outcome, faceted by leaderboard |

### Key findings

- **ratingDiff (Q1 — I3 resolution) — POST-GAME CONFIRMED:** won=True mean ratingDiff
  = +16.6, won=False mean = −17.6. Perfect sign separation. ratingDiff encodes the
  match outcome directly in its sign (positive = won, negative = lost). **Must be
  excluded from all pre-game feature sets.** This is a hard constraint for Phase 02.
- **rating (Q2 — temporal ambiguity) — INCONCLUSIVE:** Mean rating difference = +7.0
  Elo (won=True: 1095, won=False: 1088). This is ~2% of the rating stddev (~344).
  Falls between the decision thresholds of 5 (likely pre-game) and 50 (likely
  post-game). Cannot resolve with bivariate analysis alone.
- **rating temporal status — deferred to 01_04:** Row-level verification required:
  check `rating = pre_rating + ratingDiff` via temporal join with ratings_raw. If
  true, `rating` is post-game and must be excluded alongside `ratingDiff`.
- **ratingDiff × leaderboard:** The ratingDiff magnitude varies substantially across
  leaderboards (higher-ELO leaderboards have larger absolute ratingDiff per match).
  Leaderboard ID may be a useful pre-game feature.

### Decisions

- `ratingDiff` → excluded from all pre-game feature sets (confirmed leakage, I3)
- `rating` → ambiguous; 01_04 row-level verification required before use
- `duration` → post-game descriptor; usable for EDA characterization but not prediction

### Open questions

- Is `rating` = pre_game_rating + ratingDiff (post-game)? Requires 01_04 join with ratings_raw.
- Does leaderboard_id (pre-game) have independent predictive power beyond rating?

---

## 2026-04-15 — [Phase 01 / Step 01_02_05] Univariate Census Visualizations

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** visualization
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_05_*.png` (17 files)

### What

Produced 17 thesis-grade PNG plots visualizing the 01_02_04 census findings.
All DuckDB queries embedded verbatim in the markdown artifact (Invariant #6).
All post-game and ambiguous columns annotated on plots (Invariant #3).
All clip thresholds and bin widths derived from census artifact at runtime (Invariant #7).

### Plots produced

| Plot | Subject |
|------|---------|
| `won_distribution` | Target balance — 47.69% false / 47.62% true / 4.69% NULL, visually near-perfectly balanced |
| `won_consistency` | Per-leaderboard win consistency — intra-match both_true (6.2%) and both_false (4.7%) flagged |
| `leaderboard_distribution` | 6 leaderboard tiers; rm_1v1 dominant (26.8M), qp_rm_1v1 secondary |
| `civ_top20` | Top-20 civilizations by pick rate; Franks 5.68% leads |
| `map_top20` | Top-20 maps; Arabia 19.53%, Arena 16.80%, Black Forest 12.42% |
| `rating_histogram` | Rating distribution; ambiguous temporal status flagged in subtitle |
| `ratingdiff_histogram` | ratingDiff distribution — symmetric around 0, range [−174, +319]; POST-GAME annotation |
| `duration_histogram` | Dual-panel body (0–63.15 min, p95-clipped) + full log-scale; clip derived from census p95 |
| `null_rate_bar` | 4-tier NULL severity (green/gold/orange/red) across all 55 matches_raw columns |
| `null_cooccurrence` | 2×2 annotated table: Cluster A (426,472 rows) vs Cluster B (431,288 rows), 428,321 overlap |
| `leaderboards_numeric_boxplots` | wins/losses/streak/drops box by leaderboard tier |
| `profiles_null_rate` | profiles_raw column completeness; 7 fully dead (100% NULL) deprecated API fields |
| `leaderboards_leaderboard_bar` | leaderboards_raw entry counts per tier |
| `boolean_stacked_bar` | Cluster A boolean settings distribution (trueFalseNull stacked) |
| `ratings_raw_rating_histogram` | ratings_raw rating distribution — safe for temporal join use |
| `monthly_volume` | Monthly match volume 2020-08–2026-04; shows stable growth with no major gaps |
| `rating_null_timeline` | Monthly NULL rate for `rating` and `ratingDiff` — tests schema-change hypothesis (42.46% overall) |

### Decisions taken

- Duration clip: p95 = 3,789s = 63.15 min (derived from census `match_duration_stats[0]["p95_secs"]`). Differs from aoestats (p95 = 78.6 min) — both use p95-derived clipping; subtitle documents cross-dataset difference.
- NULL co-occurrence: rendered as annotated 2×2 matplotlib table (not imshow) — 4-cell values span 6 orders of magnitude, making any linear colormap uninformative.
- `rating` histogram: no I3 annotation applied; subtitle flags the ambiguity pending 01_04 row-level co-occurrence check.
- `ratingDiff` histogram: POST-GAME annotation applied (range [-174, +319] is outcome-derived).

### Decisions deferred

- Bivariate analysis of `ratingDiff × won` and `rating × won` deferred to Step 01_02_06 (Bivariate EDA).
- `rating` temporal classification (ambiguous_pre_or_post) resolution deferred to 01_04.
- `won` inconsistency (both_true / both_false rows) cleaning strategy deferred to Phase 01_04 (Data Cleaning).

### Thesis mapping

- Chapter 4, §4.1.3 — AoE2 feature landscape, target balance, NULL structure visualized
- Chapter 4, §4.1.4 — temporal leakage annotation for ratingDiff

### Open questions / follow-ups

- Does `rating_null_timeline` show a step-function (schema change) or gradual missingness? Visual inspection of the artifact determines whether pre-change rows need special handling.
- Cross-dataset: aoestats duration body at p95 = 78.6 min vs aoe2companion at 63.15 min — difference noted in plot subtitle for thesis comparability.

---

## 2026-04-15 — [Phase 01 / Step 01_02_04] Univariate Census & Target Variable EDA

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** query
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md`
- `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`

### What

Full univariate profiling of all four raw tables (NULL census, cardinality, numeric descriptive statistics, skewness/kurtosis, categorical frequency distributions, boolean census, temporal ranges, duplicate detection, NULL co-occurrence analysis), plus target variable analysis and preliminary temporal field classification per Invariant #3. All SQL embedded in the .md artifact (Invariant #6).

### Tables profiled

| Table | Rows | Columns |
|-------|------|---------|
| `matches_raw` | 277,099,059 | 55 |
| `ratings_raw` | 58,317,433 | 8 |
| `leaderboards_raw` | 2,381,227 | 19 |
| `profiles_raw` | 3,609,686 | 14 |

### NULL landscape

**matches_raw — high-NULL columns (>5%):**
- `server`: 97.99% NULL — populated for only ~2% of matches; near-dead for feature use
- `modDataset`: 99.72% NULL — scenario-specific, effectively dead
- `scenario`: 98.27% NULL — custom scenario matches only
- `password`: 82.90% NULL — password-protected lobby indicator
- `antiquityMode`: 68.66% NULL — recently added setting, absent from older matches
- `hideCivs`: 49.30% NULL — similarly phased in over time
- `rating` and `ratingDiff`: both 42.46% NULL — identical null rate confirms co-occurrence; NULLs = unranked matches
- `country`: 12.60% NULL; `regicideMode`: 7.39% NULL
- `team`: 4.90% NULL; `won` (target): 4.69% NULL (12,985,561 rows)

**NULL co-occurrence clusters:**
- Cluster A (8 boolean game-setting columns: allowCheats, lockSpeed, lockTeams, recordGame, sharedExploration, teamPositions, teamTogether, turboMode): 426,472 rows all eight NULL simultaneously — API schema change
- Cluster B (fullTechTree, population): 431,288 rows jointly NULL; cross-cluster overlap 428,321 rows — single underlying cause

**profiles_raw — 7 completely dead columns (100% NULL):** sharedHistory, twitchChannel, youtubeChannel, youtubeChannelName, discordId, discordName, discordInvitation — deprecated API fields, exclude from all feature engineering.

**leaderboards_raw — block NULL at 25.61%:** rank, wins, losses, streak, drops, active, rankLevel all co-NULL (unranked entries lack these fields).

**ratings_raw:** Zero NULLs except `rating_diff` (1.85% NULL, 1,078,873 rows).

### Target variable (`won`)

Near-perfectly balanced: 47.69% false (132.15M), 47.62% true (131.96M), 4.69% NULL (12.99M). All ranked queues show exact 50/50 balance. NULLs concentrated in `unranked` (15.74% NULL) and `unknown` (17.21% NULL) leaderboards.

Intra-match consistency check (2-row matches): 88.6% have proper complementary outcomes. However, 6.2% have `both_true` and 4.7% have `both_false` — internally inconsistent; flagged for Phase 02 investigation.

Primary prediction scope: rm_1v1 (26.8M matches) + qp_rm_1v1 (3.7M matches) = 30.5M 1v1 matches.

### Cardinality highlights

- `civ`: 68 distinct — full AoE2:DE roster. Top: Franks 5.68%, Mongols 4.45%, Britons 4.26%
- `map`: 261 distinct — Arabia 19.53%, Arena 16.80%, Black Forest 12.42% (top 3 = 49%)
- `name`: ~2.47M distinct player names

**Near-constant / dead fields:** `season` constant -1 across ratings_raw and leaderboards_raw; `rankLevel` constant 1; `treatyLength` 96.56% zero; `status` only 2 values (player/ai).

### Temporal leakage audit (Invariant #3)

**Confirmed post_game:** `ratingDiff` (range [-174, 319], direct leakage); `finished`; `won` (target).

**Critical ambiguity — `matches_raw.rating`:** Classified `ambiguous_pre_or_post`. Identical 42.46% NULL rate for `rating` and `ratingDiff` suggests simultaneous population. If `rating` is post-match snapshot, it encodes the outcome via `rating = pre_rating + ratingDiff`. Row-level co-occurrence check required in 01_04 — this is the single most important open question for aoe2companion feature engineering.

**ratings_raw:** Time-series ratings safe only with strict temporal join (`rating.date < match.started`).

**leaderboards_raw cumulative stats** (wins, losses, games, streak, drops): Singleton snapshots, not a time series — usable only as static context features, not dynamic features.

### Sentinel and anomaly values

- `matches_raw.rating`: min -1 (sentinel), max 5,001
- `ratings_raw.games`: max 1,775,260,795 — obvious data error; p95 is 4,736
- `matches_raw.population`: min 0, max 9,999 — sentinels at extremes; median 200
- `matches_raw.team`: max 255 — sentinel given median 2, p95 5
- **8,812,005 duplicate (matchId, profileId) pairs** (3.18%) — deduplication required in Phase 02

### Histogram findings

- **Match duration:** median 1,678s (28 min), mean 1,815s, p05 145s, p95 3,789s, max 3.28M s (38 days — bugged). Right-skewed.
- **matches_raw.rating** (non-NULL): mean 1,120, median 1,093, std 290 — bell-shaped around Elo anchor.
- **leaderboards_raw.games**: mean 174, median 45, skewness 8.51 — heavy right tail of active players.

### Decisions taken

- 7 dead columns in profiles_raw identified for exclusion
- 10 constant/dead fields catalogued across all tables
- `matches_raw.rating` flagged as ambiguous; resolution deferred to 01_04
- 4,398,727 internally inconsistent 2-row matches flagged for investigation

### Decisions deferred

- Row-level `rating`/`ratingDiff` co-occurrence check — 01_04 (verify: does `rating - ratingDiff` = prior rating in time series?)
- Deduplication of 8.8M duplicate (matchId, profileId) pairs
- Root cause of internally inconsistent won values (both_true, both_false)
- `ratings_raw.games` max outlier capping/exclusion strategy

### Thesis mapping

- Chapter 4, section 4.1.2 — AoE2 univariate profiles, NULL landscape, target balance, temporal classification
- Chapter 4, section 4.2.2 — Data quality: duplicates, sentinels, inconsistent outcomes

### Open questions / follow-ups

- Is `matches_raw.rating` pre-match or post-match Elo? Answering this gates the entire aoe2companion feature set.
- Root cause of 4.4M internally inconsistent 2-row matches?
- The 428K NULL co-occurrence cluster — early data before API fields existed?

---

## 2026-04-14 — [Phase 01 / Step 01_02_03] Raw schema DESCRIBE

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** query
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_03_raw_schema_describe.json`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/matches_raw.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/ratings_raw.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/leaderboards_raw.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/profiles_raw.yaml`

### What

Captured the exact DuckDB column names and types for all four aoe2companion raw sources. Since step 01_02_02 had not yet been executed, no persistent DuckDB exists; the notebook uses in-memory DuckDB and reads source files directly with `LIMIT 0` to obtain schema without loading row data. Same read parameters as planned for 01_02_02 ingestion (`binary_as_string=true`, `union_by_name=true`, `filename=true` for Parquet; explicit `dtypes=` for CSV).

### Why

Establish the source-of-truth bronze-layer schema before full ingestion runs. The `data/db/schemas/raw/*.yaml` files are consumed by all downstream steps (feature engineering, cleaning, documentation). Invariant #6 — all DESCRIBE SQL embedded in artifact.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_03_raw_schema_describe.py`

- matches: `read_parquet(glob, binary_as_string=true, union_by_name=true, filename=true) LIMIT 0`
- ratings: `read_csv(glob, dtypes={profile_id: BIGINT, games: BIGINT, rating: BIGINT, date: TIMESTAMP, leaderboard_id: BIGINT, rating_diff: BIGINT, season: BIGINT}, union_by_name=true, filename=true) LIMIT 0`
- leaderboards, profiles: `read_parquet(singleton, binary_as_string=true, filename=true) LIMIT 0`

### Findings

| Source | Columns | Notable types |
|--------|---------|---------------|
| matches | 55 | `won` BOOLEAN (prediction target); `matchId`/`profileId` INTEGER; `started`/`finished` TIMESTAMP; `speedFactor` FLOAT |
| ratings | 8 | `profile_id` BIGINT; `date` TIMESTAMP; all numerics BIGINT |
| leaderboards | 19 | `profileId` INTEGER; `lastMatchTime`/`updatedAt` TIMESTAMP |
| profiles | 14 | `profileId` INTEGER; all string columns VARCHAR |

Key observations:
- `won` (BOOLEAN, nullable) confirmed as prediction target column
- Naming inconsistency cross-confirmed: `profileId` (camelCase, INTEGER) in matches and leaderboards vs `profile_id` (snake_case, BIGINT) in ratings — noted for Phase 02 join design
- `speedFactor` is FLOAT (only non-integer numeric in matches)
- All four schema YAMLs populated in `data/db/schemas/raw/`

### Decisions taken

- Schema YAMLs populated from this DESCRIBE output — source-of-truth for all downstream steps
- No ingestion or schema changes at this step — read-only

### Decisions deferred

- Column descriptions (`TODO: fill`) in `*.yaml` files — deferred to systematic profiling (01_03)

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset: bronze-layer schema catalog

### Open questions / follow-ups

- None — schema fully captured

---

## 2026-04-14 — [Phase 01 / Step 01_02_02] DuckDB ingestion

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** ingest
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.md`

### What

Materialised four `*_raw` DuckDB tables from the full aoe2companion corpus (2,073 daily match Parquets, 2,072 daily rating CSVs, 1 leaderboard Parquet, 1 profile Parquet) into the persistent database at `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/db.duckdb`.

### Why

Enable SQL-based EDA for subsequent profiling (01_03) and cleaning (01_04). Invariants #6 (reproducibility), #9 (step scope), #10 (relative filenames) upheld.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_02_duckdb_ingestion.py`
Module: `src/rts_predict/games/aoe2/datasets/aoe2companion/ingestion.py`

### Findings

**Table row counts:**
| Table | Rows |
|-------|------|
| `matches_raw` | 277,099,059 |
| `ratings_raw` | 58,317,433 |
| `leaderboards_raw` | 2,381,227 |
| `profiles_raw` | 3,609,686 |

**Dtype strategy for `ratings_raw`:** Explicit `dtypes=` map (BIGINT/TIMESTAMP) required — `read_csv_auto` infers all 7 columns as VARCHAR at scale (2,072 files). Strategy established in Step 01_02_01.

**NULL rates (key fields):**
- `matches_raw.won`: 12,985,561 NULLs / 277,099,059 rows (4.69%) — root cause established in 01_02_01 won=NULL investigation
- `matches_raw.matchId`: 0 NULLs
- `matches_raw.filename`: 0 NULLs
- `ratings_raw.profile_id`: 0 NULLs
- `ratings_raw.filename`: 0 NULLs

**Invariant I10 (relative filenames):** All four tables pass — filenames stored relative to `raw_dir`. Enforced inline via `SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)` in every CTAS. No post-load UPDATE (would OOM on 277M-row `matches_raw`).

**Parquet binary columns:** All Parquet reads use `binary_as_string=true` for the unannotated BYTE_ARRAY columns in matches/leaderboards/profiles. Established in 01_02_01.

### Decisions taken

- All tables use `*_raw` suffix convention (bronze layer)
- Inline `SELECT * REPLACE` for I10 relativization — never post-load UPDATE
- Explicit dtype map for ratings CSV ingestion — never `read_csv_auto` at scale
- `binary_as_string=true` for all Parquet sources

### Decisions deferred

- Handling of 12.99M NULL `won` values — deferred to Step 01_04 (data cleaning)

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset: four-table ingestion, dtype strategy, I10 compliance

### Artifact note

The `.json` artifact `sql` key records pre-fix SQL (`SELECT * FROM read_parquet(...)` without `REPLACE`). The actual ingestion code uses `SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)`. The DuckDB on disk is correct; the artifact should be regenerated from a fresh notebook run to reflect the inline I10 pattern.

### Open questions / follow-ups

- Full NULL profiles for all 55 `matches_raw` columns — deferred to 01_03 (systematic profiling)

---

## 2026-04-14 — [Phase 01 / Step 01_02_01] won=NULL root-cause investigation

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** query (amendment to 01_02_01)
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json` (extended with `won_null_root_cause` key)

### What

Diagnosed why 12,985,561 rows (4.69%) have `won=NULL` in the full matches
corpus. Added section 8 (Q1–Q4) to the 01_02_01 pre-ingestion notebook to
distinguish between two hypotheses: H1 (Parquet schema heterogeneity causing
DuckDB type promotion to inject NULLs) and H2 (genuine NULL values in source
files).

### Why

The `won` column is the prediction target for this thesis. Before any cleaning
decisions can be made in later steps, the root cause of NULLs must be
understood. Invariant #6 (reproducibility) — all diagnostic queries embedded
in the artifact.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py`

Q1: `parquet_schema()` metadata-only scan — counts distinct `won` Parquet types
across all 2,073 files without loading row data.

Q2: Per-type-group value census without `union_by_name` — reads each type group
independently to observe native values and genuine NULLs.

Q3: Type promotion NULL injection test — compares per-file NULL counts before
and after `union_by_name=true` on a mixed-type sample (runs only if Q1 finds
multiple types).

Q4: Per-file NULL distribution — identifies which files contribute NULLs and
their date range under `union_by_name=true`.

### Findings

**H1 REJECTED.** `parquet_schema()` scan across all 2,073 match files found a
single `won` Parquet type: `BOOLEAN`. There is no schema heterogeneity. DuckDB
type promotion under `union_by_name=true` is not the cause of NULLs.

**H2 SUPPORTED.** 12,985,561 genuine NULL `won` values exist in the source
files. Every single file (2,073 of 2,073) contributes NULLs — the date range
of affected files is 2020-08-01 to 2026-04-04, i.e., the entire corpus
history. There is no temporal step-change or isolated bad period: NULLs are
a structural property of the dataset from day one.

Additional context from the existing artifact:
- `avg_rows_per_match = 3.71` — the dataset contains substantial team-game
  data beyond 1v1 (expected avg would be 2.0 for pure 1v1). This means
  `won=NULL` cannot be attributed to a single-player record issue.
- NULL rate: 4.69% of 277,099,059 total rows = 12,985,561 NULL `won` values.
- The aoe2companion API simply does not record a winner for some matches — the
  root cause is upstream (API-level recording gap), not a data engineering
  artefact.

### Decisions taken

- H1 definitively rejected: no INT64-to-BOOLEAN cast recovery needed.
- H2 confirmed: NULLs are genuine and uniformly distributed across the entire
  dataset history — not concentrated in a time window that could be excluded.
- Investigation scope limited to diagnosis only — no cleaning decisions made
  at this step.

### Decisions deferred

- Handling strategy for NULL `won` rows (row-level drop, match-level drop,
  or leaderboard-filtered subset) deferred to Step 01_04 (data cleaning).
- Impact on thesis scope: whether to restrict analysis to the 95.31% of rows
  with recorded winners, or characterise the NULL population separately.
- Whether `avg_rows_per_match = 3.71` implies a leaderboard filter is needed
  to isolate 1v1 matches before the prediction task is scoped.

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 data quality: won column NULL analysis
- Chapter 4, §4.2.1 — Ingestion validation methodology

### Open questions / follow-ups

- What leaderboard value(s) correspond to ranked 1v1 in aoe2companion? Does
  filtering to that leaderboard reduce the NULL rate?
- Is `avg_rows_per_match = 3.71` driven by FFA/team-game leaderboards only,
  or does it affect the ranked 1v1 population too?

---

## 2026-04-13 — [Phase 01 / Step 01_02_01] DuckDB pre-ingestion investigation

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** query
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json`

### What

Pre-ingestion investigation using in-memory DuckDB and direct Parquet/CSV
queries to characterise the four aoe2companion data sources before committing
to a DuckDB ingestion design. Binary column inspection, smoke test, full-corpus
NULL rate census, and match_id uniqueness check. No DuckDB tables were created
at this step — that is step 01_02_02.

### Why

Determine ingestion strategy before materialising 277M rows. Invariants #7
(type fidelity) and #9 (step scope) — pre-ingestion characterisation is a
distinct step from ingest. The binary column issue (unannotated BYTE_ARRAY)
and the CSV type inference pitfall at scale must be resolved before 01_02_02.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py`

### Findings

**Binary column inspection** (metadata read on `match-2020-08-01.parquet` sample):
- matches: 22 of 54 columns are BYTE_ARRAY with no logical type annotation
  (no UTF-8 annotation) — strings stored without Parquet STRING annotation
- leaderboards: 4 of 18 columns BYTE_ARRAY unannotated
- profiles: 11 of 13 columns BYTE_ARRAY unannotated
- All require `binary_as_string=true` at ingestion to resolve to VARCHAR

**Smoke test** (sampled subset of files):
- matches sample: 491,099 rows × 55 columns
- ratings sample: 266,508 rows × 8 columns

**Full-corpus NULL rates** (direct Parquet queries on all 2,073 match files):
- Total rows: 277,099,059; `matchId` and `profileId` 100% populated
- `won` column: 12,985,561 NULLs (4.69%) — see 2026-04-14 won-NULL root-cause entry

**Match_id uniqueness** (full corpus):
- 74,788,989 distinct `matchId` values; avg 3.71 rows per match
- avg > 2.0 indicates substantial team-game data beyond 1v1

**CSV ratings at scale:**
- `read_csv_auto` infers all 7 columns as VARCHAR when scanning all 2,072 files
  simultaneously — explicit `types=` required for correct BIGINT/TIMESTAMP types
- Missing file: `rating-2025-07-11.csv` — 2,073 match files vs 2,072 rating files

### Decisions taken

- All Parquet reads require `binary_as_string=true`
- CSV ratings require explicit column type map — never `read_csv_auto` at scale
- Raw layer uses `SELECT *` with `filename=true`; no explicit DDL at this step
- Full row counts for ratings/leaderboards/profiles deferred to 01_02_02

### Decisions deferred

- Handling of 12.99M NULL `won` values — see 2026-04-14 root-cause entry;
  cleaning decision deferred to Step 01_04
- Whether missing `rating-2025-07-11.csv` is recoverable or a permanent gap
- `profileId` vs `profile_id` naming inconsistency across tables — deferred
  to Phase 02 join design

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset: binary column handling, CSV type pitfall
- Chapter 4, §4.2.1 — Ingestion validation methodology

### Open questions / follow-ups

- Full row counts for ratings_raw, leaderboards_raw, profiles_raw — confirmed
  in 01_02_02 artifact
- Does restricting to ranked 1v1 leaderboard reduce the won=NULL rate and
  bring avg_rows_per_match close to 2.0? — investigate in 01_03 or 01_04

---

## 2026-04-13 — [Phase 01 / Step 01_01_02] Schema discovery

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** content
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json`

### What

Full census of all 4,147 data files: Parquet metadata-only reads for matches,
leaderboards, and profiles; CSV header + 50-row samples for ratings.
Catalogued column names, physical types, and nullability.

### Why

Map the exact schema of each source before ingestion. Invariant #6 requires
knowing field names and types for reproducibility.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_02_schema_discovery.py`

### Findings

- Matches: 54 columns per Parquet file, consistent schema across all 2,073 daily files. 22 columns have unannotated BYTE_ARRAY physical type (no logical type annotation — Parquet files were written without UTF8 annotation)
- Ratings: 7 CSV columns (`profile_id`, `games`, `rating`, `date`, `leaderboard_id`, `rating_diff`, `season`), consistent across 2,072 files
- Leaderboards: 18 columns (singleton Parquet), 4 unannotated BYTE_ARRAY columns
- Profiles: 13 columns (singleton Parquet), 11 unannotated BYTE_ARRAY columns
- Schema is consistent within each file type — no variant columns detected

### Decisions taken

- Full census (not sampling) used because file counts are manageable (<4,200 files)
- BYTE_ARRAY without annotation flagged for `binary_as_string=true` at ingestion

### Decisions deferred

- Ingestion strategy deferred to 01_02_01

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset schema description

### Open questions / follow-ups

- Why do Parquet files lack UTF8 annotation on string columns? (upstream data source issue)

---

## 2026-04-13 — [Phase 01 / Step 01_01_01] File inventory

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** filesystem
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`

### What

Catalogued the aoe2companion raw data directory: 4 subdirectories (matches,
ratings, leaderboards, profiles), file counts, sizes, extensions, and
temporal coverage via filename date parsing.

### Why

Establish the data landscape. Invariant #9 — filesystem-level inventory before
content inspection.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py`

### Findings

- 4,153 total files across 4 subdirectories, 9.2 GB total
- Matches: 2,073 daily Parquet files (6.6 GB), 2020-08-01 to 2026-04-04, no date gaps
- Ratings: 2,072 daily CSV files (2.5 GB), 2020-08-01 to 2026-04-04, no date gaps
- Leaderboards: 1 singleton Parquet (83 MB)
- Profiles: 1 singleton Parquet (162 MB)
- 1 file count gap: matches has 2,073 files, ratings has 2,072 (missing 2025-07-11)

### Decisions taken

- Temporal coverage spans ~5.7 years — sufficient for longitudinal analysis
- File count mismatch between matches and ratings noted for investigation

### Decisions deferred

- Internal file structure deferred to 01_01_02

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset description, temporal coverage, data volume

### Open questions / follow-ups

- None — straightforward inventory step
