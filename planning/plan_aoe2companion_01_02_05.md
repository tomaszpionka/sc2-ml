---
category: A
branch: feat/census-pass3
date: 2026-04-15
planner_model: claude-opus-4-6
dataset: aoe2companion
phase: "01"
pipeline_section: "01_02 -- Exploratory Data Analysis"
invariants_touched: [3, 6, 7, 9]
critique_required: true
---

# Plan: aoe2companion Step 01_02_05 — Univariate Census Visualizations

## Scope

**Phase/Step:** 01 / 01_02_05
**Branch:** feat/census-pass3
**Action:** CREATE (all prior 01_02_05 artifacts deleted; STEP_STATUS reset to not_started)
**Predecessor:** 01_02_04 (Univariate Census — complete, artifacts on disk)

Create a visualization notebook that reads the 01_02_04 JSON census artifact and
DuckDB tables, produces 17 thesis-grade PNG plots, and writes a markdown artifact
with all SQL queries (Invariant #6). No new analytics — visualization of existing
01_02_04 findings only (Invariant #9).

## Problem Statement

Step 01_02_04 produced quantitative census results (NULL rates, distributions,
skewness, cardinality, temporal ranges, target balance) for all four aoe2companion
raw tables. Those numbers exist only as JSON and markdown text. Step 01_02_05
translates them into visual form for three purposes: (1) validate that visual
distributions match statistical summaries, (2) produce thesis-ready figures for
Chapter 4, and (3) reveal patterns (bimodality, cliff shapes, co-occurrence
structure) invisible in summary statistics alone.

## Assumptions & Unknowns

- The census JSON at `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`
  is the single source of truth for all plotted values.
- DuckDB queries are needed only where the census JSON does not contain bin-level
  data (histograms for rating, ratingDiff, duration, temporal volume).
- `matches_raw.rating` temporal status remains ambiguous — the rating histogram
  carries no leakage annotation, but a subtitle note flags the ambiguity.
- Duration p95 clip value: 3,789s = 63.15 min (from census key
  `match_duration_stats[0]["p95_secs"]`). This differs from aoestats, which clips
  at p95=4,714s = 78.6 min. Both use p95-derived clipping; the difference reflects
  genuinely different game-length distributions. Subtitle annotation documents this.

## Literature Context

Not applicable for a visualization step. Threshold derivations reference the
01_02_04 census artifact, not external literature.

## Scientific Questions

These questions drive the notebook structure and plot selection. Each maps to one
or more tasks.

**Q1 — Target balance:** Is the win/loss split near 50/50 for aoe2companion, and how
does the 4.69% NULL rate compare visually to the win/loss counts? (Comparable to
sc2egset's near-perfect balance and aoestats's zero-NULL target.)

**Q2 — Intra-match consistency:** What fraction of 2-row matches have internally
consistent (complementary) outcomes, and how do the anomalous categories (both_true,
both_false, mixed_null) compare in magnitude?

**Q3 — Map concentration:** Does the map distribution show power-law concentration
(a few maps dominating) or a flat distribution? How does the top-3 coverage (49%)
compare to aoestats (60.9% for top-3)?

**Q4 — Leaderboard distribution:** What is the relative volume across leaderboard
types? Does the rm_1v1 + qp_rm_1v1 subset (30.5M matches, the primary prediction
scope) dominate?

**Q5 — Civilization pick rates:** Are civilization pick rates uniform or concentrated?
Does the top civ (Franks 5.68%) stand out, and how does the distribution compare to
aoestats (Franks 5.59%)?

**Q6 — Rating distribution shape:** Is the Elo distribution unimodal and bell-shaped
around the anchor, or does it show bimodality (two player populations)?
Note: `matches_raw.rating` has ambiguous temporal status — subtitle must flag this.

**Q7 — ratingDiff leakage visualization:** What does the post-game ratingDiff
distribution look like? The plot must carry a POST-GAME annotation since ratingDiff
is confirmed post-game (Invariant #3).

**Q8 — Duration distribution:** How extreme is the right tail (max 38 days)?
Does the body (clipped at p95=63 min) show a unimodal right-skew or bimodality?
How does p95=63 min compare to aoestats p95=79 min?

**Q9 — NULL landscape:** Which columns are data-rich (0% NULL) and which are
effectively dead (>50% NULL)? Does the 4-tier severity coloring reveal clusters?

**Q10 — NULL co-occurrence:** Do the 428K jointly-NULL rows in Cluster A (8 boolean
settings) and Cluster B (fullTechTree, population) represent a single historical
schema change event?

**Q11 — Leaderboards_raw numeric boxplots:** How do wins, losses, games, streak,
drops distribute across the leaderboard snapshot? Do they confirm the heavy
right-tail (skewness 8.51 for games)?

**Q12 — Profiles_raw NULL rates:** Which of the 14 profile columns are populated
vs. the 7 dead columns (100% NULL)?

**Q13 — Leaderboards_raw leaderboard type distribution:** What is the relative
volume across leaderboard types in the snapshot table?

**Q14 — Boolean settings:** What fraction of matches have each boolean setting
enabled? Do the 8 Cluster A columns show identical non-NULL rates (confirming
co-occurrence)?

**Q15 — Temporal volume:** Does match volume increase steadily over 2020–2026, or
are there plateaus, dips, or inflection points?

**Q16 — Cross-dataset comparison:** Can the four mandatory cross-dataset plots
(target bar, map top-20, duration histogram, rating histogram) be placed side-by-side
with aoestats and sc2egset equivalents?

## Part A — ROADMAP Patch

The following fields in ROADMAP.md Step 01_02_05 entry must be updated:

**`description`:** Replace with:
```
"17 visualization plots for the aoe2companion univariate census findings from 01_02_04. Reads the 01_02_04 JSON artifact and queries DuckDB for histogram bin data. All plots saved to artifacts/01_exploration/02_eda/plots/. Temporal annotations on post-game columns per Invariant #3."
```

**`method`:** Replace with:
```
"Read 01_02_04 JSON artifact. Query DuckDB for histogram bins (rating, ratingDiff, duration, monthly volume). Produce 17 plots: won 2-bar, won consistency stacked, leaderboard bar, civ top-20, map top-20 barh, rating histogram, ratingDiff histogram (POST-GAME annotated), duration dual-panel histogram, NULL rate bar (4-tier), NULL co-occurrence annotated 2x2 table, leaderboards_raw numeric boxplots, profiles_raw NULL rate bar, leaderboards_raw leaderboard bar, boolean stacked bar, monthly volume line chart, ratings_raw rating histogram, rating/ratingDiff NULL rate timeline. Markdown artifact with SQL queries and plot index table."
```

**`outputs.plots`:** Replace with the full list of 17 PNG files:
```yaml
plots:
  - "artifacts/01_exploration/02_eda/plots/01_02_05_won_distribution.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_won_consistency.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_leaderboard_distribution.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_civ_top20.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_map_top20.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_rating_histogram.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_ratingdiff_histogram.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_duration_histogram.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_null_rate_bar.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_null_cooccurrence.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_leaderboards_numeric_boxplots.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_profiles_null_rate.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_leaderboards_leaderboard_bar.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_boolean_stacked_bar.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_monthly_volume.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_ratings_raw_rating_histogram.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_rating_null_timeline.png"
```

**`gate.artifact_check`:** Replace with:
```
"All 17 PNG files exist under plots/. 01_02_05_visualizations.md exists with SQL queries (Invariant #6) and plot index table including Temporal Annotation column."
```

**Add `scientific_invariants_applied` block:**
```yaml
scientific_invariants_applied:
  - number: "3"
    how_upheld: "ratingDiff histogram carries POST-GAME annotation. matches_raw.rating subtitle notes ambiguous temporal status."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "All bin widths, clip boundaries, color thresholds, and annotation values derived from census JSON at runtime. No hardcoded numbers."
  - number: "9"
    how_upheld: "Visualization of 01_02_04 findings only. No new analytical computation."
```

## Part B — Notebook Task List

### T01 — ROADMAP Patch

**Objective:** Update the ROADMAP.md Step 01_02_05 entry with the final plot list,
gate condition, invariants, and thesis mapping.

**Instructions:**
1. Open `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`.
2. Replace the Step 01_02_05 YAML block fields as specified in Part A above.
3. This is an INSERT for `scientific_invariants_applied` (the current ROADMAP entry
   lacks this block).

**Verification:**
- ROADMAP.md Step 01_02_05 lists 17 PNG outputs under `plots/` subdirectory.
- `scientific_invariants_applied` block present with I3, I6, I7, I9.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`

### T02 — Notebook Setup

**Objective:** Create the notebook skeleton with imports, DuckDB connection,
census JSON load, path setup, and sql_queries dict.

**Instructions:**
1. Create `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py`
   with jupytext percent-format header.
2. Markdown header cell: Step 01_02_05, dataset, phase, question, invariants, predecessor, step scope.
3. Imports: `json`, `pathlib.Path`, `duckdb`, `matplotlib`, `matplotlib.pyplot as plt`,
   `pandas as pd`, `from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging`,
   `from rts_predict.games.aoe2.config import AOE2COMPANION_DB_FILE`.
4. `matplotlib.use("Agg")`, logger setup.
5. Connect to DuckDB read-only: `con = duckdb.connect(str(AOE2COMPANION_DB_FILE), read_only=True)`.
6. Load census JSON: `census_json_path = get_reports_dir("aoe2", "aoe2companion") / "artifacts" / "01_exploration" / "02_eda" / "01_02_04_univariate_census.json"`.
7. Assert required keys present: `won_distribution`, `won_consistency_2row`, `categorical_profiles`, `matches_raw_null_census`, `match_duration_stats`, `boolean_census`, `cross_cluster_overlap`, `matches_raw_total_rows`.
8. Set up paths: `artifacts_dir`, `plots_dir = artifacts_dir / "plots"`, `plots_dir.mkdir(parents=True, exist_ok=True)`.
9. Initialize: `sql_queries = {}`.

**Verification:**
- Notebook imports and runs through setup without error.
- Census JSON loads and key assertion passes.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py`

### T03 — Won Distribution 2-Bar (Q1)

**Scientific question answered:** Q1 — Target balance.

**Input:** `census["won_distribution"]` (list of dicts with keys `won`, `cnt`, `pct`).

**Output:** `plots/01_02_05_won_distribution.png`

**Plot design:**
- 2-bar chart (Win and Loss only). Filter with: `[r for r in census["won_distribution"] if r["won"] is not None]`
  (identity check — JSON null becomes Python None).
- Colors: Win=steelblue, Loss=salmon.
- Bar annotations: count and percentage.
- Title: `f"Target Variable Distribution — won (N={total_n:,})"` where `total_n = sum(r["cnt"] for r in census["won_distribution"])`.
- Text annotation below chart: `f"Excluded: {null_cnt:,} NULL ({null_pct:.2f}%)"` where null values extracted with `[r for r in census["won_distribution"] if r["won"] is None][0]`.
- Y-axis comma formatter.

**Temporal classification annotation:** None (target variable, not a feature).

**Invariant notes:**
- I7: all values from census JSON at runtime. No hardcoded counts.

### T04 — Won Consistency Stacked Bar (Q2)

**Scientific question answered:** Q2 — Intra-match consistency.

**Input:** `census["won_consistency_2row"]` (list of dicts with keys `outcome_pattern`, `match_count`, `pct`).

**Output:** `plots/01_02_05_won_consistency.png`

**Plot design:**
- Horizontal stacked bar chart showing proportions of `complementary`, `both_true`, `both_false`, `mixed_null` categories.
- Colors: complementary=green, both_true=red, both_false=orange, mixed_null=gray.
- Annotated with counts and percentages.
- Title: "Intra-Match Won Consistency (2-Row Matches)".

**Invariant notes:**
- I7: values from census JSON.

### T05 — Leaderboard Distribution Bar (Q4)

**Scientific question answered:** Q4 — Leaderboard volume.

**Input:** `census["categorical_profiles"]["leaderboard"]` (top-k list).

**Output:** `plots/01_02_05_leaderboard_distribution.png`

**Plot design:**
- Vertical bar chart, all leaderboard types, sorted by count descending.
- Bar annotations: count and percentage.
- Highlight rm_1v1 and qp_rm_1v1 bars with a distinct color (accent) and bracket annotation showing combined count.
- Title: `f"Leaderboard Distribution — matches_raw (N={census['matches_raw_total_rows']:,})"`.

**Invariant notes:**
- I7: total_rows from `census["matches_raw_total_rows"]`.

### T06 — Civilization Top-20 Barh (Q5)

**Scientific question answered:** Q5 — Civilization pick rates.

**Input:** `census["categorical_profiles"]["civ"]` (top-20 list with keys `civ`, `cnt`, `pct`).

**Output:** `plots/01_02_05_civ_top20.png`

**Plot design:**
- Horizontal barh, top-20, sorted descending (highest at top).
- Bar annotations: count and percentage.
- Title: `f"Civilization Pick Rates — Top 20 of {cardinality} (matches_raw)"` where cardinality from census null_census `civ` entry `approx_cardinality`.
- Subtitle: coverage percentage of top-20.

**Invariant notes:**
- I7: cardinality from census.

### T07 — Map Top-20 Barh (Q3, cross-dataset mandatory)

**Scientific question answered:** Q3 — Map concentration.

**Input:** `census["categorical_profiles"]["map"]` (top-20 list with keys `map`, `cnt`, `pct`).

**Output:** `plots/01_02_05_map_top20.png`

**Plot design:**
- Horizontal barh, top-20, sorted descending (highest at top).
- Bar annotations: count and percentage.
- Title: `f"Map Distribution — Top 20 of {cardinality} (matches_raw)"` where cardinality from census null_census `map` entry `approx_cardinality` (261).
- Subtitle: `f"Top-20 coverage: {top20_pct:.1f}% of {census['matches_raw_total_rows']:,} rows"`.

**Invariant notes:**
- I7: cardinality 261 from census, not hardcoded.

### T08 — Rating Histogram (Q6, cross-dataset mandatory)

**Scientific question answered:** Q6 — Rating distribution shape.

**Input:** DuckDB query on matches_raw. Census stats: mean=1,120, median=1,093, std=290, p05=687, p95=1,598, sentinel min=-1.

**Output:** `plots/01_02_05_rating_histogram.png`

**SQL (store in sql_queries["hist_rating"]):**
```sql
SELECT
    FLOOR(rating / 25) * 25 AS bin,
    COUNT(*) AS cnt
FROM matches_raw
WHERE rating IS NOT NULL AND rating > 0
GROUP BY bin
ORDER BY bin
```
I7 justification: bin width 25 chosen as ~0.09 stddev (stddev=290 from census key
`matches_raw_numeric_stats` where `column_name="rating"`, `stddev_val=290.01`);
provides ~64 bins across p05-p95 range for smooth histogram with 159M non-NULL rows.
Sentinel -1 excluded with `rating > 0`.

**Plot design:**
- Single-panel histogram. X-axis: Elo rating. Y-axis: count.
- Title: `f"Elo Rating Distribution — matches_raw (N={n_nonnull:,}, sentinel -1 excluded)"`.
- Subtitle: `f"mean={mean:.0f}, median={median:.0f}, std={std:.0f} | AMBIGUOUS TEMPORAL STATUS — see Phase 02"`.
- Vertical dashed lines at mean and median.

**Temporal classification annotation:** None (ambiguous — not annotated as leakage, but subtitle flags the ambiguity).

**Invariant notes:**
- I7: bin width 25, sentinel exclusion, and all stats from census.
- I6: SQL stored in sql_queries dict.

### T09 — ratingDiff Histogram with POST-GAME Annotation (Q7)

**Scientific question answered:** Q7 — ratingDiff leakage visualization.

**Input:** DuckDB query on matches_raw. Census stats: mean=-0.19, median=0, std=17.66, p05=-20, p95=20, min=-174, max=319.

**Output:** `plots/01_02_05_ratingdiff_histogram.png`

**SQL (store in sql_queries["hist_ratingdiff"]):**
```sql
SELECT
    ratingDiff AS val,
    COUNT(*) AS cnt
FROM matches_raw
WHERE ratingDiff IS NOT NULL
GROUP BY ratingDiff
ORDER BY ratingDiff
```
I7 justification: ratingDiff has integer values in range [-174, +319]; plotting all
distinct values (no binning needed) since the range is narrow enough for direct
value-count bars.

**Plot design:**
- Single-panel bar/step chart. X-axis: ratingDiff value. Y-axis: count.
- Title: `f"Rating Difference Distribution — matches_raw (N={n_nonnull:,})"`.
- Subtitle: `f"mean={mean:.2f}, median={median:.0f}, std={std:.2f}, skew={skew:.4f}"`.

**Temporal classification annotation:**
```python
ax.annotate(
    "POST-GAME — not available at prediction time (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)
```

**Invariant notes:**
- I3: POST-GAME annotation confirms ratingDiff is temporal leakage.
- I6: SQL in sql_queries dict.

### T10 — Duration Dual-Panel Histogram (Q8, cross-dataset mandatory)

**Scientific question answered:** Q8 — Duration distribution extremes.

**Input:** DuckDB query on matches_raw. Census stats: median=1,678s, p95=3,789s,
max=3,279,303s. Non-positive duration count: 2,941 rows.

**Output:** `plots/01_02_05_duration_histogram.png`

**SQL (store in sql_queries["hist_duration_body"]):**
```sql
SELECT
    FLOOR(EXTRACT(EPOCH FROM (finished - started)) / 60) AS bin_min,
    COUNT(*) AS cnt
FROM matches_raw
WHERE finished > started
  AND EXTRACT(EPOCH FROM (finished - started)) <= 3789
GROUP BY bin_min
ORDER BY bin_min
```

**SQL (store in sql_queries["hist_duration_full_log"]):**
```sql
SELECT
    FLOOR(LOG10(GREATEST(EXTRACT(EPOCH FROM (finished - started)), 1))) AS log_bin,
    COUNT(*) AS cnt
FROM matches_raw
WHERE finished > started
GROUP BY log_bin
ORDER BY log_bin
```

I7 justification: p95 clip value 3,789s from census key
`match_duration_stats[0]["p95_secs"]`. Bin width 1 minute for body panel (~63 bins).
Non-positive durations excluded with `finished > started` (2,941 rows per census key
`duration_excluded_rows[0]["non_positive_duration_count"]`).

**Plot design:**
- 2-panel (1x2): left = body clipped at p95=63 min, right = full range log-y.
- Left panel title: `f"Match Duration — Body (clipped at p95={p95_min:.0f} min)"`.
- Right panel title: "Match Duration — Full Range (log scale)".
- Suptitle: `f"Match Duration — matches_raw (N={n_valid:,}, excl. {n_excluded:,} non-positive)"`.
- Subtitle annotation on left panel: `f"p95 clip = {p95_min:.0f} min; cf. aoestats p95 = 79 min — both use p95 clipping"`.
- Vertical dashed line at median on left panel.

**Temporal classification annotation:** None (duration is derived from `finished - started`;
`finished` is post-game but duration itself is a match-level descriptor that is
known post-game but is not a direct leakage vector for win/loss prediction in the
same way ratingDiff is. It will be formally classified in Phase 02.)

**Invariant notes:**
- I7: clip at p95=3,789s from census. Bin width 1 min. Exclusion count 2,941 from census.
- I6: both SQL queries in sql_queries dict.

### T11 — NULL Rate Bar Chart with 4-Tier Severity (Q9)

**Scientific question answered:** Q9 — NULL landscape.

**Input:** `census["matches_raw_null_census"]` (list of dicts with `column_name`, `null_pct`).

**Output:** `plots/01_02_05_null_rate_bar.png`

**Plot design:**
- Horizontal barh, all 55 columns sorted by null_pct descending.
- 4-tier color scheme:
  - green: 0% NULL
  - gold: >0% and <5% NULL
  - orange: 5-50% NULL
  - red: >=50% NULL
- Bar annotations: null_pct value.
- Title: `f"NULL Rate by Column — matches_raw ({len(null_data)} columns)"`.
- Legend showing the 4 tiers.

**Invariant notes:**
- I7: thresholds (0%, 5%, 50%) are the standardized 4-tier scheme used across all
  three datasets for cross-dataset comparability.

### T12 — NULL Co-occurrence Annotated Table (Q10)

**Scientific question answered:** Q10 — NULL co-occurrence structure.

**Input:** `census["cross_cluster_overlap"]` (dict with keys `both_clusters_null`,
`cluster_a_only_null`, `cluster_b_only_null`). Total rows from `census["matches_raw_total_rows"]`.

**Output:** `plots/01_02_05_null_cooccurrence.png`

**Plot design:**
- Annotated 2x2 table (NOT a raw-count heatmap — the 6-orders-of-magnitude range
  makes linear colormaps uninformative). Use `matplotlib` table or `ax.text()` to
  render a formatted 2x2 grid.
- Rows: allowCheats NULL (proxy for Cluster A) / NOT NULL
- Columns: fullTechTree NULL (proxy for Cluster B) / NOT NULL
- Cells show: count and percentage of total rows.
- Derive `total_rows = census["matches_raw_total_rows"]` (277,099,059).
- Derive non-cluster counts:
  `neither_null = total_rows - both - a_only - b_only`.
- Title: "NULL Co-occurrence: allowCheats (proxy Cluster A) vs fullTechTree (proxy Cluster B)".
- Footnote: "Cluster A proxy: allowCheats IS NULL captures 428,338 rows; exact
  all-8-NULL count is 426,472 (1,866-row gap). Cluster B proxy: fullTechTree IS NULL."

**Invariant notes:**
- I7: all counts from census JSON. total_rows from `census["matches_raw_total_rows"]`.

### T13 — Leaderboards_raw Numeric Boxplots (Q11)

**Scientific question answered:** Q11 — Leaderboard snapshot distributions.

**Input:** DuckDB query on leaderboards_raw.

**Output:** `plots/01_02_05_leaderboards_numeric_boxplots.png`

**SQL (store in sql_queries["leaderboards_boxplots"]):**
```sql
SELECT wins, losses, games, streak, drops
FROM leaderboards_raw
WHERE rank IS NOT NULL
```

**Plot design:**
- 1x5 subplot panel, one boxplot per column. Log-y scale for games (skewness 8.51).
- Title: "Leaderboards_raw Numeric Distributions (ranked entries only)".
- WHERE clause excludes 25.61% unranked entries (co-NULL block).

**Invariant notes:**
- I7: skewness 8.51 from census; unranked exclusion rate 25.61% from census.
- I6: SQL in sql_queries dict.

### T14 — Profiles_raw NULL Rate Bar (Q12)

**Scientific question answered:** Q12 — Profile column data availability.

**Input:** Census JSON profiles_raw null census data (from full JSON scan; key path
depends on census structure — look for profiles_raw null counts).

**Output:** `plots/01_02_05_profiles_null_rate.png`

**Plot design:**
- Horizontal barh, all 14 columns, sorted by null_pct descending.
- Same 4-tier color scheme as T11.
- Highlight the 7 dead columns (100% NULL) with explicit label annotation.
- Title: "NULL Rate by Column — profiles_raw (14 columns)".

**Invariant notes:**
- I7: 4-tier thresholds consistent with T11.

### T15 — Leaderboards_raw Leaderboard Type Bar (Q13)

**Scientific question answered:** Q13 — Leaderboard type distribution.

**Input:** Census JSON leaderboards_raw categorical profile for `leaderboard` column.

**Output:** `plots/01_02_05_leaderboards_leaderboard_bar.png`

**Plot design:**
- Vertical bar chart, all leaderboard types, sorted descending.
- Bar annotations: count and percentage.
- Title: "Leaderboard Type Distribution — leaderboards_raw".

### T16 — Boolean Settings Stacked Bar (Q14)

**Scientific question answered:** Q14 — Boolean settings distribution.

**Input:** `census["boolean_census"]` (list of dicts with `column_name`, `true_count`,
`false_count`, `null_count`).

**Output:** `plots/01_02_05_boolean_stacked_bar.png`

**Plot design:**
- Horizontal stacked barh, one row per boolean column.
- Three segments: True (blue), False (orange), NULL (gray).
- Annotations: percentage for each segment.
- Title: "Boolean Column Distribution — matches_raw".

### T17 — Ratings_raw Rating Histogram (supplementary Q6)

**Scientific question answered:** Q6 supplementary — Compare ratings_raw.rating
distribution to matches_raw.rating.

**Input:** DuckDB query on ratings_raw. Census stats: mean=1,120, median=1,093, std=267.

**Output:** `plots/01_02_05_ratings_raw_rating_histogram.png`

**SQL (store in sql_queries["hist_ratings_raw_rating"]):**
```sql
SELECT
    FLOOR(rating / 25) * 25 AS bin,
    COUNT(*) AS cnt
FROM ratings_raw
WHERE rating IS NOT NULL
GROUP BY bin
ORDER BY bin
```

**Plot design:**
- Single-panel histogram. Bin width 25 (same as T08 for comparability).
- Title: `f"Rating Distribution — ratings_raw (N={n_nonnull:,})"`.
- Subtitle: `f"mean={mean:.0f}, median={median:.0f}, std={std:.0f}"`.

**Invariant notes:**
- I7: bin width 25 matches T08. Stats from census.
- I6: SQL in sql_queries dict.

### T18 — Monthly Volume Line Chart (Q15)

**Scientific question answered:** Q15 — Temporal volume trends.

**Input:** DuckDB query on matches_raw.

**Output:** `plots/01_02_05_monthly_volume.png`

**SQL (store in sql_queries["monthly_volume"]):**
```sql
SELECT
    DATE_TRUNC('month', started) AS month,
    COUNT(*) AS match_count
FROM matches_raw
WHERE started IS NOT NULL
GROUP BY month
ORDER BY month
```

**Plot design:**
- Line chart with markers. X-axis: month. Y-axis: match count.
- Title: `f"Monthly Match Volume — matches_raw"`.
- Y-axis comma formatter.
- Soft assertion: `len(monthly_df) <= census["temporal_range_matches"][0]["distinct_match_dates"]` (approximate check).

**Invariant notes:**
- I6: SQL in sql_queries dict.

### T19 — Rating & ratingDiff NULL Rate Timeline

**Scientific question answered:** Is the 42.46% co-NULL rate for `rating` and `ratingDiff`
in matches_raw explained by a discrete schema change at a temporal boundary
(step-function NULL rate over time), or is missingness gradual? Determines whether
pre-change rows can ever carry rating features in Phase 02 feature engineering.

**Input:** DuckDB query on matches_raw. Census facts:
- `rating` NULL rate: 42.46% (117,656,260 / 277,099,059) from `matches_raw_null_census`
- `ratingDiff` NULL rate: 42.46% (117,656,260 / 277,099,059) — identical count confirms row-level co-occurrence
- Temporal column: `started` (TIMESTAMP, 0% NULL, range 2020-07-31 to 2026-04-04)
- Total rows: 277,099,059 from `census["matches_raw_total_rows"]`

**Output:** `plots/01_02_05_rating_null_timeline.png`

**SQL (store in `sql_queries["rating_null_timeline"]`):**
```sql
SELECT
    DATE_TRUNC('month', started) AS month,
    COUNT(*) AS total_rows,
    ROUND(100.0 * SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2)
        AS rating_null_pct,
    ROUND(100.0 * SUM(CASE WHEN "ratingDiff" IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2)
        AS ratingdiff_null_pct
FROM matches_raw
WHERE started IS NOT NULL
GROUP BY month
ORDER BY month
```
I7: no hardcoded date bounds — query groups all rows by `started` month.
Column names `rating` and `ratingDiff` identified as co-NULL in census
`matches_raw_null_census`. Total row count from `census["matches_raw_total_rows"]`.

**Python:**
```python
# --- T19: Rating & ratingDiff NULL Rate Timeline ---
# I7: overall NULL rates derived from census at runtime
rating_null_pct = next(
    c["null_pct"]
    for c in census["matches_raw_null_census"]["columns"]
    if c["column"] == "rating"
)
ratingdiff_null_pct = next(
    c["null_pct"]
    for c in census["matches_raw_null_census"]["columns"]
    if c["column"] == "ratingDiff"
)

sql_queries["rating_null_timeline"] = """
SELECT
    DATE_TRUNC('month', started) AS month,
    COUNT(*) AS total_rows,
    ROUND(100.0 * SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2)
        AS rating_null_pct,
    ROUND(100.0 * SUM(CASE WHEN "ratingDiff" IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2)
        AS ratingdiff_null_pct
FROM matches_raw
WHERE started IS NOT NULL
GROUP BY month
ORDER BY month
"""

df_null_timeline = conn.execute(sql_queries["rating_null_timeline"]).fetchdf()
df_null_timeline["month"] = pd.to_datetime(df_null_timeline["month"])

fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(
    df_null_timeline["month"],
    df_null_timeline["rating_null_pct"],
    color="steelblue", linewidth=1.5, label="rating NULL %",
)
ax.plot(
    df_null_timeline["month"],
    df_null_timeline["ratingdiff_null_pct"],
    color="darkorange", linewidth=1.5, linestyle="--", label="ratingDiff NULL %",
)

ax.set_xlabel("Month")
ax.set_ylabel("NULL Rate (%)")
ax.set_ylim(0, 105)
ax.set_title(
    f"Monthly NULL Rate — rating & ratingDiff\n"
    f"(matches_raw, N={census['matches_raw_total_rows']:,})"
)
ax.legend(loc="upper right", fontsize=9)
ax.grid(axis="y", alpha=0.3)
fig.autofmt_xdate()

# I7: detect schema-change breakpoint algorithmically — no hardcoded date
months_high = df_null_timeline[df_null_timeline["rating_null_pct"] > 90]["month"]
months_low = df_null_timeline[df_null_timeline["rating_null_pct"] < 10]["month"]
if len(months_high) > 0 and len(months_low) > 0:
    breakpoint_month = months_low.min()
    ax.axvline(breakpoint_month, color="red", linestyle=":", linewidth=1.2,
               label=f"Schema change ~{breakpoint_month.strftime('%Y-%m')}")
    ax.legend(loc="upper right", fontsize=9)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_rating_null_timeline.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_rating_null_timeline.png'}")
```

**Temporal annotation:** None. NULL rate is a data-quality diagnostic, not an in-game feature.

**Invariant notes:**
- I7: no hardcoded date bounds; overall NULL rates derived from `census["matches_raw_null_census"]`; total rows from `census["matches_raw_total_rows"]`; breakpoint detected algorithmically.
- I6: SQL stored in `sql_queries["rating_null_timeline"]` and written to markdown artifact.
- I9: Visualizes 01_02_04 NULL census finding (42.46% co-NULL rate) decomposed into monthly temporal bins. No new analytics.

### T20 — Markdown Artifact and Verification

**Objective:** Write the markdown artifact with plot index table, SQL queries, and
verification cell. Close DuckDB connection.

**Instructions:**
1. Define `expected_plots` list with all 17 PNG filenames.
2. Assert all exist on disk.
3. Build markdown string with:
   - Header (step, dataset, phase, predecessor, invariants).
   - Plot index table with columns: #, Title, Filename, Observation, Temporal Annotation.
     The Temporal Annotation column must say "POST-GAME (Inv. #3)" for ratingDiff,
     "AMBIGUOUS — see Phase 02" for rating, and "N/A" for all others.
   - SQL Queries section: iterate over `sql_queries` dict and write each query verbatim
     in a fenced code block. This must enumerate ALL queries including:
     `hist_rating`, `hist_ratingdiff`, `hist_duration_body`, `hist_duration_full_log`,
     `leaderboards_boxplots`, `hist_ratings_raw_rating`, `monthly_volume`.
   - Data Sources section.
4. Write to `artifacts_dir / "01_02_05_visualizations.md"`.
5. Close DuckDB connection.
6. Print summary line.

**Verification:**
- All 17 PNG files exist.
- Markdown artifact exists and contains all 7 SQL queries.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py` (continuation)
- `reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md` (generated)

### T21 — STEP_STATUS Update

**Objective:** Mark 01_02_05 as complete.

**Instructions:**
1. Update `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`:
   set `01_02_05.status` to `complete` and `01_02_05.completed_at` to the execution date.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`

## Cross-Dataset Comparability Checklist

| Mandatory Plot | Column | p95 Clip | Dataset-Specific Handling |
|---|---|---|---|
| (a) Target 2-bar | `won` (BOOLEAN) | N/A | NULL (4.69%) annotated as text below chart, not as a third bar |
| (b) Map top-20 barh | `map` (VARCHAR, 261 distinct) | N/A | Direct from census categorical_profiles |
| (c) Duration dual-panel | `finished - started` (derived seconds) | p95=3,789s=63 min | Subtitle notes "cf. aoestats p95=79 min — both use p95 clipping" |
| (d) Rating histogram | `rating` (INTEGER, sentinel -1) | N/A | Sentinel -1 excluded. Subtitle notes AMBIGUOUS temporal status. |

All four present: confirmed.

## NULL Severity Thresholds

T11 and T14 both use the standardized 4-tier scheme:
- green: 0% NULL
- gold: >0% and <5% NULL
- orange: 5-50% NULL
- red: >=50% NULL

## Gate Condition

- [ ] `plots/01_02_05_won_distribution.png`
- [ ] `plots/01_02_05_won_consistency.png`
- [ ] `plots/01_02_05_leaderboard_distribution.png`
- [ ] `plots/01_02_05_civ_top20.png`
- [ ] `plots/01_02_05_map_top20.png`
- [ ] `plots/01_02_05_rating_histogram.png`
- [ ] `plots/01_02_05_ratingdiff_histogram.png`
- [ ] `plots/01_02_05_duration_histogram.png`
- [ ] `plots/01_02_05_null_rate_bar.png`
- [ ] `plots/01_02_05_null_cooccurrence.png`
- [ ] `plots/01_02_05_leaderboards_numeric_boxplots.png`
- [ ] `plots/01_02_05_profiles_null_rate.png`
- [ ] `plots/01_02_05_leaderboards_leaderboard_bar.png`
- [ ] `plots/01_02_05_boolean_stacked_bar.png`
- [ ] `plots/01_02_05_monthly_volume.png`
- [ ] `plots/01_02_05_ratings_raw_rating_histogram.png`
- [ ] `plots/01_02_05_rating_null_timeline.png`
- [ ] `01_02_05_visualizations.md` with SQL queries and plot index table including Temporal Annotation column
- [ ] ROADMAP.md Step 01_02_05 patched
- [ ] STEP_STATUS.yaml `01_02_05` -> complete
- [ ] Notebook executes end-to-end without error

## File Manifest

| File | Action |
|------|--------|
| `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.py` | Create |
| `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_05_visualizations.ipynb` | Create (jupytext sync) |
| `reports/artifacts/01_exploration/02_eda/plots/01_02_05_*.png` (17 files) | Create |
| `reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` | Modify |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml` | Modify |

All paths relative to `src/rts_predict/games/aoe2/datasets/aoe2companion/` except sandbox and ROADMAP.

## Out of Scope

- New analytics beyond 01_02_04 findings (Invariant #9)
- Bivariate or multivariate analysis (future steps)
- Research log entry (written post-execution by the parent session)
- Resolution of `matches_raw.rating` temporal ambiguity (Phase 02)
- Cleaning or filtering decisions (Step 01_04)
- Color palette harmonization across datasets beyond the 4 mandatory cross-dataset plots

## Open Questions

- Should the rating histogram be split into ranked vs. unranked subpopulations?
  (deferred to 01_03 or Phase 02)
- The 4.69% NULL won rate — is it concentrated in specific leaderboards?
  (already answered in 01_02_04 census: yes, unranked/unknown leaderboards)

---

For Category A, adversarial critique is required before execution.
Dispatch reviewer-adversarial to produce `planning/plan_aoe2companion_01_02_05.critique.md`.
```

---
