---
category: A
branch: feat/census-pass3
date: 2026-04-15
planner_model: claude-opus-4-6
dataset: aoestats
phase: "01"
pipeline_section: "01_02 -- Exploratory Data Analysis"
invariants_touched: [3, 6, 7, 9]
critique_required: true
---

# Plan: aoestats Step 01_02_05 — Univariate Visualizations

## Scope

**Phase/Step:** 01 / 01_02_05
**Branch:** feat/census-pass3
**Action:** CREATE (all prior 01_02_05 artifacts deleted; STEP_STATUS reset to not_started)
**Predecessor:** 01_02_04 (Univariate Census — complete, artifacts on disk)

Create a visualization notebook that reads the 01_02_04 JSON census artifact and
DuckDB tables, produces 15 thesis-grade PNG plots, and writes a markdown artifact
with all SQL queries (Invariant #6). No new analytics — visualization of existing
01_02_04 findings only (Invariant #9).

## Problem Statement

Step 01_02_04 produced quantitative census results for matches_raw (30.7M rows)
and players_raw (107.6M rows). Those numbers exist as JSON and markdown. Step
01_02_05 translates them into visual form for validation, thesis communication,
and pattern recognition.

## Assumptions & Unknowns

- The census JSON at `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`
  is the single source of truth for all plotted values.
- DuckDB queries are needed for histogram bins (duration, ELO, old_rating,
  match_rating_diff, monthly volume).
- `match_rating_diff` leakage status is unresolved — annotation reflects this.
- Duration column in DuckDB is BIGINT nanoseconds — requires `duration / 1e9`
  for conversion to seconds.
- Census label for duration numeric stats is `"duration_sec"` (pre-converted in census).
- p95 clip value for duration: 4,714.1s = 78.6 min (from census key
  `numeric_stats_matches` where `label="duration_sec"`, `p95=4714.1`).

## Literature Context

Not applicable for a visualization step.

## Scientific Questions

**Q1 — Target balance:** Is the winner distribution exactly 50/50 with zero NULLs,
confirming the cleanest target of all three datasets?

**Q2 — Match size distribution:** Is 1v1 (60.56%) the dominant match type? How do
the odd player counts (1, 3, 5, 7) appear visually — are they negligible anomalies?
This question drives the modelling scope decision.

**Q3 — Map concentration:** Does the map distribution show the same power-law
concentration as aoe2companion? Arabia at 35% vs. aoe2companion's 20% — is aoestats
more concentrated?

**Q4 — Civilization pick rates:** How does the civ distribution across 50 civs
compare to aoe2companion's 68? Does Franks still dominate?

**Q5 — Leaderboard distribution:** Is random_map (58.5%) + team_random_map (37.5%)
= 96% of all matches?

**Q6 — Duration distribution:** How extreme is the right tail (max 64 days)?
Does the body (clipped at p95=79 min) show a unimodal right-skew? How does median
43.6 min compare to aoe2companion's 28 min?

**Q7 — ELO distributions (3-panel):** Do avg_elo, team_0_elo, and team_1_elo show
similar bell-shaped distributions? Is the sentinel -1 visible in team_0/1_elo?

**Q8 — old_rating (pre-game ELO):** What does the authoritative pre-game rating
look like? How does it compare to avg_elo?

**Q9 — match_rating_diff:** What is the shape of this leakage-unresolved column?
Does the extreme kurtosis (65.7) produce visible leptokurtic tails?

**Q10 — Age uptimes (in-game):** What do the feudal/castle/imperial age uptime
distributions look like for the 14% non-NULL subset? Are they unimodal?

**Q11 — Opening strategies (in-game):** Among the 14% non-NULL subset, what are
the opening frequencies? Does "unknown" (24%) indicate classification gaps?

**Q12 — IQR outlier summary:** How many outliers exist per numeric column? Does
duration dominate the outlier landscape?

**Q13 — NULL rate bar chart:** Which columns are fully populated (0% NULL) and
which have the 87% NULL block (age uptimes, opening)?

**Q14 — Temporal volume:** Does match volume increase or plateau over the 2022–2026
span? Are the three temporal gaps (43-day summer 2024 gap) visible?

## Part A — ROADMAP Patch

The following fields in ROADMAP.md Step 01_02_05 entry must be updated:

**`description`:** Replace with:
```
"15 visualization plots for the aoestats univariate census findings from 01_02_04. Reads the 01_02_04 JSON artifact and queries DuckDB for histogram bin data. All plots saved to artifacts/01_exploration/02_eda/plots/. Temporal annotations on in-game, post-game, and leakage-unresolved columns per Invariant #3."
```

**`method`:** Replace with:
```
"Read 01_02_04 JSON artifact. Query DuckDB for histogram bins (duration, ELO, old_rating, match_rating_diff, monthly volume). Produce 15 plots: winner 2-bar, num_players bar, map top-20 barh, civ top-20 barh, leaderboard bar, duration dual-panel, ELO 1x3 panel (sentinel excluded), old_rating histogram, match_rating_diff histogram (LEAKAGE UNRESOLVED annotated), age uptime 1x3 panel (IN-GAME annotated), opening non-NULL bar (IN-GAME annotated), IQR outlier summary, NULL rate bar (4-tier), schema change temporal boundary (IN-GAME annotated), monthly volume line chart."
```

**`outputs.plots`:** Replace with:
```yaml
plots:
  - "artifacts/01_exploration/02_eda/plots/01_02_05_winner_distribution.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_num_players_distribution.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_map_top20.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_civ_top20.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_leaderboard_distribution.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_duration_histogram.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_elo_distributions.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_old_rating_histogram.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_match_rating_diff_histogram.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_age_uptime_histograms.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_opening_nonnull.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_iqr_outlier_summary.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_null_rate_bar.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_schema_change_boundary.png"
  - "artifacts/01_exploration/02_eda/plots/01_02_05_monthly_match_count.png"
```

**`gate`:** Replace with:
```yaml
gate:
  artifact_check: "All 15 PNG files exist under plots/. 01_02_05_visualizations.md exists with SQL queries (Invariant #6) and plot index table including Temporal Annotation column."
  continue_predicate: "All 15 PNG files exist. Markdown artifact contains plot index table with Temporal Annotation column and all SQL queries. Notebook executes end-to-end without errors."
  halt_predicate: "Any PNG file is missing or notebook execution fails."
```

**Add `scientific_invariants_applied` block:**
```yaml
scientific_invariants_applied:
  - number: "3"
    how_upheld: "duration annotated POST-GAME. opening and age uptimes annotated IN-GAME. match_rating_diff annotated LEAKAGE STATUS UNRESOLVED. new_rating not plotted (post-game, excluded)."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "All bin widths, clip boundaries, color thresholds derived from census JSON at runtime. match_rating_diff clip at [-200, +200] is ~3.6sigma editorial choice (stddev=55.23)."
  - number: "9"
    how_upheld: "Visualization of 01_02_04 findings only. No new analytical computation."
```

## Part B — Notebook Task List

### T01 — ROADMAP Patch

**Objective:** Update the ROADMAP.md Step 01_02_05 entry with the final plot list,
gate condition, invariants, and thesis mapping.

**Instructions:**
1. Open `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`.
2. Replace the Step 01_02_05 YAML block fields as specified in Part A above.
3. INSERT `scientific_invariants_applied` block.

**Verification:**
- ROADMAP.md Step 01_02_05 lists 15 PNG outputs under `plots/` subdirectory.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`

### T02 — Notebook Setup

**Objective:** Create the notebook skeleton.

**Instructions:**
1. Create `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py`
   with jupytext percent-format header.
2. Markdown header cell: Step 01_02_05, dataset, phase, question, invariants, predecessor.
3. Imports: `json`, `pathlib.Path`, `duckdb`, `matplotlib`, `matplotlib.pyplot as plt`,
   `pandas as pd`, `from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging`,
   `from rts_predict.games.aoe2.config import AOESTATS_DB_FILE`.
4. `matplotlib.use("Agg")`, logger setup.
5. Connect to DuckDB read-only.
6. Load census JSON.
7. Assert required keys: `winner_distribution`, `num_players_distribution`,
   `categorical_matches`, `categorical_players`, `numeric_stats_matches`,
   `numeric_stats_players`, `skew_kurtosis_players`, `players_null_census`,
   `matches_null_census`, `temporal_range`, `outlier_counts_matches`,
   `elo_sentinel_counts`.
8. Set up paths: `artifacts_dir`, `plots_dir`, `sql_queries = {}`.

**Verification:**
- Notebook imports and runs through setup without error.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py`

### T03 — Winner Distribution 2-Bar (Q1, cross-dataset mandatory)

**Scientific question answered:** Q1 — Target balance.

**Input:** `census["winner_distribution"]` (list of dicts with keys `winner`, `cnt`, `pct`).

**Output:** `plots/01_02_05_winner_distribution.png`

**Plot design:**
- 2-bar chart (True=Win, False=Loss). Winner has zero NULLs so no NULL annotation needed.
- Colors: Win=steelblue, Loss=salmon.
- Bar annotations: count and percentage.
- Title: `f"Target Variable Distribution — winner (N={total_n:,})"` where `total_n = sum(r["cnt"] for r in census["winner_distribution"])`.
- Annotation text below bars: "Zero NULLs — cleanest target across all three datasets".

**Invariant notes:**
- I7: all values from census JSON.

### T04 — num_players Distribution (Q2)

**Scientific question answered:** Q2 — Match size distribution.

**Input:** `census["num_players_distribution"]` (list of dicts with keys `num_players`,
`row_count`, `distinct_match_count`, `pct`, `distinct_match_pct`).

**Output:** `plots/01_02_05_num_players_distribution.png`

**Plot design:**
- Vertical bar chart. X-axis: num_players. Y-axis: `distinct_match_count` (not `row_count` —
  this is a match-level distribution, not a player-row distribution).
- Bar annotations: distinct_match_count and distinct_match_pct.
- Odd player counts (1, 3, 5, 7) highlighted in red.
- Title: `f"Match Size Distribution (N={total_matches:,} distinct matches)"` where
  `total_matches = sum(r["distinct_match_count"] for r in census["num_players_distribution"])`.

**Invariant notes:**
- I7: use `distinct_match_count`, not `row_count`.

### T05 — Map Top-20 Barh (Q3, cross-dataset mandatory)

**Scientific question answered:** Q3 — Map concentration.

**Input:** `census["categorical_matches"]["map"]["top_values"]` (top-20 list).

**Output:** `plots/01_02_05_map_top20.png`

**Plot design:**
- Horizontal barh, top-20, sorted descending.
- Bar annotations: count and percentage.
- Title: `f"Map Distribution — Top 20 of {cardinality} (matches_raw)"` where cardinality
  from `census["categorical_matches"]["map"]["cardinality"]` (93).
- Subtitle: coverage percentage.

### T06 — Civilization Top-20 Barh (Q4)

**Scientific question answered:** Q4 — Civilization pick rates.

**Input:** `census["categorical_players"]["civ"]["top_values"]` (top-20 list).

**Output:** `plots/01_02_05_civ_top20.png`

**Plot design:**
- Horizontal barh, top-20, sorted descending.
- Bar annotations: count and percentage.
- Title: `f"Civilization Pick Rates — Top 20 of {cardinality} (players_raw)"` where
  cardinality from `census["categorical_players"]["civ"]["cardinality"]` (50).

### T07 — Leaderboard Distribution (Q5)

**Scientific question answered:** Q5 — Leaderboard distribution.

**Input:** `census["categorical_matches"]["leaderboard"]["top_values"]`.

**Output:** `plots/01_02_05_leaderboard_distribution.png`

**Plot design:**
- Vertical bar chart, all leaderboard types.
- Bar annotations: count and percentage.

### T08 — Duration Dual-Panel Histogram (Q6, cross-dataset mandatory)

**Scientific question answered:** Q6 — Duration distribution.

**Input:** DuckDB query on matches_raw. Census stats (label `"duration_sec"`):
mean=2,613.7s, median=2,619.7s, p95=4,714.1s, max=5,574,815.1s.

**Output:** `plots/01_02_05_duration_histogram.png`

**SQL (store in sql_queries["hist_duration_body"]):**
```sql
SELECT
    FLOOR((duration / 1e9) / 60) AS bin_min,
    COUNT(*) AS cnt
FROM matches_raw
WHERE duration > 0
  AND (duration / 1e9) <= 4714.1
GROUP BY bin_min
ORDER BY bin_min
```

**SQL (store in sql_queries["hist_duration_full_log"]):**
```sql
SELECT
    FLOOR(LOG10(GREATEST(duration / 1e9, 1))) AS log_bin,
    COUNT(*) AS cnt
FROM matches_raw
WHERE duration > 0
GROUP BY log_bin
ORDER BY log_bin
```

I7 justification: p95 clip value 4,714.1s = 78.6 min from census key
`numeric_stats_matches` where `label="duration_sec"`, `p95=4714.1`. Bin width 1 minute
for body panel (~79 bins). `duration / 1e9` converts BIGINT nanoseconds to seconds.

**Plot design:**
- 2-panel (1x2): left = body clipped at p95=79 min, right = full range log-y.
- Left panel title: `f"Match Duration — Body (clipped at p95={p95_min:.0f} min)"`.
- Subtitle on left panel: `f"p95 clip = {p95_min:.0f} min; cf. aoe2companion p95 = 63 min — both use p95 clipping"`.
- Vertical dashed line at median on left panel.

**Temporal classification annotation:**
```python
for ax_panel in [ax_body, ax_full]:
    ax_panel.annotate(
        "POST-GAME — not available at prediction time (Inv. #3)",
        xy=(0.02, 0.98), xycoords="axes fraction",
        ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
        bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
    )
```

**Invariant notes:**
- I3: POST-GAME annotation (duration known only after match ends).
- I7: p95=4,714.1s from census. `duration / 1e9` for nanosecond conversion.
- I6: both SQL queries in sql_queries dict.

### T09 — ELO Distributions 1x3 Panel (Q7, cross-dataset mandatory for avg_elo)

**Scientific question answered:** Q7 — ELO distributions.

**Input:** DuckDB queries on matches_raw. Census stats:
avg_elo: mean=1,087.6, median=1,055.0, std=309.5, n_zero=121.
team_0_elo: mean=1,082.7, median=1,051.5, n_zero=4,824, sentinel_neg=34.
team_1_elo: mean=1,092.5, median=1,058.0, n_zero=192, sentinel_neg=39.

**Output:** `plots/01_02_05_elo_distributions.png`

**SQL (store in sql_queries["hist_elo_3panel"]):**
```sql
-- avg_elo (exclude zero sentinels for consistency with team panels):
SELECT FLOOR(avg_elo / 25) * 25 AS bin, COUNT(*) AS cnt
FROM matches_raw WHERE avg_elo > 0
GROUP BY bin ORDER BY bin;

-- team_0_elo (exclude sentinel -1 and zero):
SELECT FLOOR(team_0_elo / 25) * 25 AS bin, COUNT(*) AS cnt
FROM matches_raw WHERE team_0_elo > 0
GROUP BY bin ORDER BY bin;

-- team_1_elo (exclude sentinel -1 and zero):
SELECT FLOOR(team_1_elo / 25) * 25 AS bin, COUNT(*) AS cnt
FROM matches_raw WHERE team_1_elo > 0
GROUP BY bin ORDER BY bin
```

I7 justification: bin width 25 = ~0.08 stddev (stddev=309.5 from census key
`numeric_stats_matches` where `label="avg_elo"`, `stddev_val=309.54`). Sentinel -1
excluded for team_0/1_elo per census `elo_sentinel_counts`. avg_elo excludes zero
(121 rows) for consistent treatment with team panels — documented with I7 comment:
`# I7: avg_elo excludes 121 zero-valued rows for consistency with team_0/1_elo sentinel exclusion (34+39 sentinel -1 rows). Asymmetry: avg_elo has no -1 sentinels, only zeros.`

**Plot design:**
- 1x3 subplot panel: avg_elo, team_0_elo, team_1_elo.
- Shared y-axis for visual comparability.
- Each subplot: histogram bars, vertical line at median.
- Subplot titles include `f"(N={n_nonnull:,}, excl. {n_excluded} sentinel/zero)"`.

### T10 — old_rating Histogram (Q8)

**Scientific question answered:** Q8 — Pre-game rating.

**Input:** DuckDB query on players_raw. Census stats (label `"old_rating"`):
mean=1,091.1, median=1,066.0, std=286.9, n_zero=5,937.

**Output:** `plots/01_02_05_old_rating_histogram.png`

**SQL (store in sql_queries["hist_old_rating"]):**
```sql
SELECT FLOOR(old_rating / 25) * 25 AS bin, COUNT(*) AS cnt
FROM players_raw WHERE old_rating > 0
GROUP BY bin ORDER BY bin
```

I7 justification: bin width 25 = ~0.09 stddev (stddev=286.9). Zero excluded (5,937 rows).

**Plot design:**
- Single-panel histogram.
- Title: `f"Pre-Game Rating (old_rating) — players_raw (N={n_valid:,}, excl. {n_zero} zero)"`.
- Vertical dashed line at median.

### T11 — match_rating_diff Histogram (Q9)

**Scientific question answered:** Q9 — Leakage-unresolved column shape.

**Input:** DuckDB query on players_raw. Census stats (label `"match_rating_diff"`):
mean=0.0, median=0.0, stddev=55.23, p05=-59.0, p95=59.0, min=-2,185, max=2,185,
kurtosis=65.68.

**Output:** `plots/01_02_05_match_rating_diff_histogram.png`

**SQL (store in sql_queries["hist_match_rating_diff"]):**
```sql
SELECT
    FLOOR(match_rating_diff / 5) * 5 AS bin,
    COUNT(*) AS cnt
FROM players_raw
WHERE match_rating_diff IS NOT NULL
  AND match_rating_diff BETWEEN -200 AND 200
GROUP BY bin ORDER BY bin
```

I7 justification: `# I7: editorial clip at ~3.6sigma (stddev=55.23 from census key skew_kurtosis_players where label='match_rating_diff'); shows leptokurtic tail without [-2185,+2185] extremes. Not p05/p95 derived.`
Bin width 5 = ~0.09 stddev; produces 80 bins for smooth visualization.

**Plot design:**
- Single-panel histogram.
- Title: `f"match_rating_diff — players_raw (N={n_clipped:,}, clipped to [-200, +200])"`.
- Subtitle: `f"stddev={stddev:.2f}, kurtosis={kurt:.2f} — leptokurtic; full range [-2185, +2185]"`.

**Temporal classification annotation:**
```python
ax.annotate(
    "LEAKAGE STATUS UNRESOLVED — do not use as feature until verified (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)
```

### T12 — Age Uptime 1x3 Panel (Q10)

**Scientific question answered:** Q10 — Age uptime distributions.

**Input:** DuckDB queries on players_raw. Census stats:
feudal: p05=535.1, p95=962.6, median=680.2, non-null=13.9M.
castle: p05=889.1, p95=1,752.1, median=1,262.9, non-null=13.0M.
imperial: p05=1,681.1, p95=2,933.0, median=2,208.6, non-null=9.2M.

**Output:** `plots/01_02_05_age_uptime_histograms.png`

**SQL (store in sql_queries["hist_age_uptimes"]):**
```sql
-- feudal_age_uptime:
SELECT FLOOR(feudal_age_uptime / 10) * 10 AS bin, COUNT(*) AS cnt
FROM players_raw WHERE feudal_age_uptime IS NOT NULL
GROUP BY bin ORDER BY bin;

-- castle_age_uptime:
SELECT FLOOR(castle_age_uptime / 20) * 20 AS bin, COUNT(*) AS cnt
FROM players_raw WHERE castle_age_uptime IS NOT NULL
GROUP BY bin ORDER BY bin;

-- imperial_age_uptime:
SELECT FLOOR(imperial_age_uptime / 30) * 30 AS bin, COUNT(*) AS cnt
FROM players_raw WHERE imperial_age_uptime IS NOT NULL
GROUP BY bin ORDER BY bin
```

I7 justification: bin widths chosen to produce ~43 bins each across p05-p95 range:
feudal 10s = (962.6-535.1)/10 = 43 bins; castle 20s = (1752.1-889.1)/20 = 43 bins;
imperial 30s = (2933.0-1681.1)/30 = 42 bins.

**Plot design:**
- 1x3 subplot panel: feudal, castle, imperial.
- Each subplot shows non-NULL subset only, with N in subtitle.

**Temporal classification annotation (on each subplot):**
```python
for ax_panel in [ax_feudal, ax_castle, ax_imperial]:
    ax_panel.annotate(
        "IN-GAME — not available at prediction time (Inv. #3)",
        xy=(0.02, 0.98), xycoords="axes fraction",
        ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
        bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
    )
```

### T13 — Opening Non-NULL Bar (Q11)

**Scientific question answered:** Q11 — Opening frequencies.

**Input:** `census["categorical_players"]["opening"]["top_values"]`.

**Output:** `plots/01_02_05_opening_nonnull.png`

**Plot design:**
- Horizontal barh of opening categories from census top values.
- Bar annotations: count and percentage (of non-NULL only).
- Subtitle: `f"Non-NULL subset only: {n_nonnull:,} of {total:,} rows ({pct:.1f}%)"`.

**Temporal classification annotation:**
```python
ax.annotate(
    "IN-GAME — not available at prediction time (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)
```

### T14 — IQR Outlier Summary (Q12)

**Scientific question answered:** Q12 — Outlier landscape.

**Input:** `census["outlier_counts_matches"]` (list of dicts with `label`, `outlier_total`, `outlier_pct`).

**Output:** `plots/01_02_05_iqr_outlier_summary.png`

**Plot design:**
- Horizontal barh, one bar per numeric column, showing outlier_pct.
- Bar annotations: outlier count and percentage.
- Title: "IQR Outlier Rates — matches_raw Numeric Columns".

### T15 — NULL Rate Bar Chart with 4-Tier Severity (Q13)

**Scientific question answered:** Q13 — NULL landscape.

**Input:** Merged from `census["matches_null_census"]["columns"]` and
`census["players_null_census"]["columns"]`.

**Output:** `plots/01_02_05_null_rate_bar.png`

**Plot design:**
- Horizontal barh, all columns from both tables, sorted by null_pct descending.
- 4-tier color scheme: green=0%, gold=>0%<5%, orange=5-50%, red=>=50%.
- Table prefix on labels (m: matches_raw, p: players_raw).
- Title: "NULL Rate by Column — matches_raw + players_raw".
- Legend showing 4 tiers.

### T16 — Schema Change Temporal Boundary (86%-NULL Columns)

**Scientific question answered:** Do the ~86%-NULL columns in players_raw (feudal_age_uptime,
castle_age_uptime, imperial_age_uptime, opening) transition from ~100% NULL to ~0% NULL at a
common temporal boundary (schema change event), or is the missingness distributed uniformly
across all weeks? If a step-function boundary exists, rows before it are systematically missing
these features — critical for data cleaning scope and Phase 02 feature engineering decisions.
All four columns are IN-GAME (age uptimes from replay parsing, opening from in-game strategy
classification) — annotated per Invariant #3.

**Input:** DuckDB query on players_raw. Census: feudal_age_uptime 87.08% NULL,
castle_age_uptime 87.93% NULL, imperial_age_uptime 91.49% NULL, opening 86.05% NULL.
All four are co-NULL in 92,616,290 / 107,627,584 rows (census: `players_raw_null_cooccurrence`).
Filename column format: `players/YYYY-MM-DD_YYYY-MM-DD_players.parquet` (week start date at
characters 9-18, 0% NULL).

**Output:** `plots/01_02_05_schema_change_boundary.png`

**SQL (store in `sql_queries["weekly_null_rate_high_null_cols"]`):**

I7: the column list is derived from census at runtime — the notebook filters
`census["players_null_census"]["columns"]` to entries with `null_pct > 80.0`.
The >80% threshold is an editorial filter for visually significant missingness,
documented with inline I7 comment (80% is a round number below the lowest observed
rate of 86.05%, chosen to include all four co-NULL columns from
`players_raw_null_cooccurrence`). The SQL below is built dynamically in Python.

**Python:**
```python
# --- T16: Schema Change Temporal Boundary ---
# I7: column list derived from census at runtime; >80% threshold editorial,
# documented: 80% < lowest observed rate (86.05%), includes all four co-NULL
# columns identified in players_raw_null_cooccurrence census section.
NULL_THRESHOLD = 80.0
high_null_cols = [
    c["column"]
    for c in census["players_null_census"]["columns"]
    if c["null_pct"] > NULL_THRESHOLD
]
print(f"High-NULL columns (>{NULL_THRESHOLD:.0f}%): {high_null_cols}")
assert len(high_null_cols) >= 4, (
    f"Expected ≥4 high-NULL columns, got {len(high_null_cols)}: {high_null_cols}"
)

# Build SQL dynamically from census-derived column list
null_rate_exprs = ",\n    ".join(
    f'ROUND(100.0 * (COUNT(*) - COUNT("{col}")) / COUNT(*), 2) AS {col}_null_pct'
    for col in high_null_cols
)
sql = f"""
SELECT
    CAST(SUBSTR(filename, 9, 10) AS DATE) AS week_start,
    COUNT(*) AS total_rows,
    {null_rate_exprs}
FROM players_raw
GROUP BY week_start
ORDER BY week_start
"""
sql_queries["weekly_null_rate_high_null_cols"] = sql

df_weekly_null = conn.execute(sql).fetchdf()
df_weekly_null["week_start"] = pd.to_datetime(df_weekly_null["week_start"])

fig, ax = plt.subplots(figsize=(14, 6))
for col in high_null_cols:
    ax.plot(
        df_weekly_null["week_start"],
        df_weekly_null[f"{col}_null_pct"],
        marker=".", markersize=3, linewidth=1.2, label=col,
    )

ax.set_xlabel("Week (from players_raw filename)")
ax.set_ylabel("NULL Rate (%)")
ax.set_ylim(0, 105)
ax.set_title(
    f"Weekly NULL Rate — High-NULL Columns (>{NULL_THRESHOLD:.0f}%) in players_raw"
)
ax.legend(loc="center right", fontsize=9)
ax.grid(axis="y", alpha=0.3)

# IN-GAME annotation: all four are in-game columns per Invariant #3
ax.annotate(
    "IN-GAME — not available at prediction time (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)

fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_schema_change_boundary.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_schema_change_boundary.png'}")
```

**Temporal annotation:** `ax.annotate("IN-GAME — not available at prediction time (Inv. #3)", ...)` — applied to all four columns in the legend/title since all four are in-game.

**Invariant notes:**
- I3: All four columns (age uptimes, opening) are IN-GAME. Annotation applied at upper-left.
- I6: SQL stored in `sql_queries["weekly_null_rate_high_null_cols"]` and written to markdown artifact.
- I7: column list derived from `census["players_null_census"]["columns"]` filtered by `null_pct > 80.0` at runtime. Threshold 80% documented inline. No hardcoded column names or date bounds. Week parsed from `filename` column at chars 9-18.
- I9: Visualizes 01_02_04 NULL census findings for four co-NULL columns. No new analytics.

### T17 — Monthly Match Volume Line Chart (Q14)

**Scientific question answered:** Q14 — Temporal volume trends.

**Input:** DuckDB query on matches_raw.

**Output:** `plots/01_02_05_monthly_match_count.png`

**SQL (store in sql_queries["monthly_match_counts"]):**
```sql
SELECT
    DATE_TRUNC('month', started_timestamp) AS month,
    COUNT(*) AS match_count
FROM matches_raw
WHERE started_timestamp IS NOT NULL
GROUP BY month
ORDER BY month
```

**Plot design:**
- Line chart with markers. X-axis: month. Y-axis: match count.
- Title: "Monthly Match Volume — matches_raw".
- Annotate the 43-day summer 2024 gap if visible.
- Soft assertion: `assert len(monthly_df) <= census["temporal_range"]["distinct_months"]`
  (soft `<=`, not strict `==`).

**Invariant notes:**
- I6: SQL in sql_queries dict.

### T18 — Markdown Artifact and Verification

**Objective:** Write markdown artifact, verify all plots, close connection.

**Instructions:**
1. Define `expected_plots` list with all 15 PNG filenames.
2. Assert all exist on disk.
3. Build markdown with:
   - Header.
   - Plot index table with columns: #, Title, Filename, Observation, Temporal Annotation.
     Temporal Annotation column: "POST-GAME (Inv. #3)" for duration, "IN-GAME (Inv. #3)"
     for age uptimes, opening, and schema_change_boundary, "LEAKAGE UNRESOLVED (Inv. #3)"
     for match_rating_diff, "N/A" for all others.
   - SQL Queries section: iterate sql_queries dict. Must enumerate ALL queries:
     `hist_duration_body`, `hist_duration_full_log`, `hist_elo_3panel`,
     `hist_old_rating`, `hist_match_rating_diff`, `hist_age_uptimes`,
     `weekly_null_rate_high_null_cols`, `monthly_match_counts`.
   - Data Sources section.
4. Write to `artifacts_dir / "01_02_05_visualizations.md"`.
5. Close DuckDB connection.

**Verification:**
- All 15 PNG files exist.
- Markdown artifact contains all 8 SQL query groups.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py` (continuation)
- `reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md` (generated)

### T19 — STEP_STATUS Update

**Objective:** Mark 01_02_05 as complete.

**Instructions:**
1. Update `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml`:
   set `01_02_05.status` to `complete` and `01_02_05.completed_at` to the execution date.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml`

## Cross-Dataset Comparability Checklist

| Mandatory Plot | Column | p95 Clip | Dataset-Specific Handling |
|---|---|---|---|
| (a) Target 2-bar | `winner` (BOOLEAN) | N/A | Zero NULLs — no NULL annotation needed |
| (b) Map top-20 barh | `map` (VARCHAR, 93 distinct) | N/A | Direct from census |
| (c) Duration dual-panel | `duration / 1e9` (BIGINT nanoseconds to seconds) | p95=4,714.1s=79 min | `duration / 1e9` for nanosecond conversion. Subtitle: "cf. aoe2companion p95=63 min — both use p95 clipping". POST-GAME annotated. |
| (d) Rating histogram | `avg_elo` (panel 1 of 3-panel ELO plot) | N/A | Zero-valued rows (121) excluded for consistency with team_0/1_elo sentinel exclusion. |

All four present: confirmed.

## NULL Severity Thresholds

T15 uses the standardized 4-tier scheme:
- green: 0% NULL
- gold: >0% and <5% NULL
- orange: 5-50% NULL
- red: >=50% NULL

## Gate Condition

- [ ] `plots/01_02_05_winner_distribution.png`
- [ ] `plots/01_02_05_num_players_distribution.png`
- [ ] `plots/01_02_05_map_top20.png`
- [ ] `plots/01_02_05_civ_top20.png`
- [ ] `plots/01_02_05_leaderboard_distribution.png`
- [ ] `plots/01_02_05_duration_histogram.png`
- [ ] `plots/01_02_05_elo_distributions.png`
- [ ] `plots/01_02_05_old_rating_histogram.png`
- [ ] `plots/01_02_05_match_rating_diff_histogram.png`
- [ ] `plots/01_02_05_age_uptime_histograms.png`
- [ ] `plots/01_02_05_opening_nonnull.png`
- [ ] `plots/01_02_05_iqr_outlier_summary.png`
- [ ] `plots/01_02_05_null_rate_bar.png`
- [ ] `plots/01_02_05_schema_change_boundary.png`
- [ ] `plots/01_02_05_monthly_match_count.png`
- [ ] `01_02_05_visualizations.md` with SQL queries and plot index table including Temporal Annotation column
- [ ] ROADMAP.md Step 01_02_05 patched
- [ ] STEP_STATUS.yaml `01_02_05` -> complete
- [ ] Notebook executes end-to-end without error

## File Manifest

| File | Action |
|------|--------|
| `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py` | Create |
| `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.ipynb` | Create (jupytext sync) |
| `reports/artifacts/01_exploration/02_eda/plots/01_02_05_*.png` (15 files) | Create |
| `reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` | Modify |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml` | Modify |

## Out of Scope

- New analytics beyond 01_02_04 findings (Invariant #9)
- Bivariate or multivariate analysis (future steps)
- Research log entry (written post-execution)
- Resolution of `match_rating_diff` leakage status (Phase 02 verification query)
- Cleaning or filtering decisions (Step 01_04)
- `new_rating` is post-game and is NOT plotted — this is intentional

## Open Questions

- Is `match_rating_diff` = `new_rating - old_rating` (post-game) or `player_elo - opponent_elo` (pre-game)?
  Verification query ready; must execute before Phase 02.
- Should modelling scope be restricted to 1v1 (60.56%) or include team games?

---

For Category A, adversarial critique is required before execution.
Dispatch reviewer-adversarial to produce `planning/plan_aoestats_01_02_05.critique.md`.
```

---
