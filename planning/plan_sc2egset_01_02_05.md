---
category: A
branch: feat/census-pass3
date: 2026-04-15
planner_model: claude-opus-4-6
dataset: sc2egset
phase: "01"
pipeline_section: "01_02 -- Exploratory Data Analysis"
invariants_touched: [3, 6, 7, 9]
critique_required: true
---

# Plan: sc2egset Step 01_02_05 — Univariate EDA Visualizations

## Scope

**Phase/Step:** 01 / 01_02_05
**Branch:** feat/census-pass3
**Action:** CREATE (all prior 01_02_05 artifacts deleted; STEP_STATUS reset to not_started)
**Predecessor:** 01_02_04 (Univariate Census — complete, artifacts on disk)

Create a visualization notebook that reads the 01_02_04 JSON census artifact and
DuckDB tables, produces 14 thesis-grade PNG plots, and writes a markdown artifact
with all SQL queries (Invariant #6). No new analytics — visualization of existing
01_02_04 findings only (Invariant #9).

The existing notebook at `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`
(687 lines) serves as a format reference but its artifacts have been deleted. This plan
specifies a complete CREATE that may reuse structural patterns from the existing notebook
but must produce all artifacts fresh and incorporate all critique resolutions.

## Problem Statement

Step 01_02_04 produced census results for replay_players_raw (44,817 rows) and
struct_flat/replays_meta_raw (22,390 replays). The sc2egset dataset is unique
among the three datasets: zero NULLs, esports-focused (tournament replays),
and contains in-game metrics (APM, SQ, supplyCappedPercent) not available in AoE2
datasets. Step 01_02_05 visualizes these findings and annotates in-game columns
per Invariant #3.

## Assumptions & Unknowns

- Census JSON at `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`
  is the source of truth.
- DuckDB queries needed for: MMR histogram, APM histogram, SQ histogram,
  supplyCappedPercent histogram, duration histogram.
- MMR=0 sentinel: 83.65% of rows. Histogram uses split view (all vs. non-zero).
- SQ INT32_MIN sentinel: 2 rows. Excluded from main histogram.
- Duration measured in `elapsed_game_loops`; `LOOPS_PER_SECOND = 22.4` (SC2 "Faster"
  game speed constant).
- p95 clip for duration: 30,270.1 game loops = 1,351.3s = 22.5 min.

## Literature Context

Not applicable for a visualization step.

## Scientific Questions

**Q1 — Target balance:** Is the result distribution near-perfect 50/50 Win/Loss?
How many Undecided (24) and Tie (2) rows need exclusion? (Cross-dataset comparison:
all three datasets show ~50/50.)

**Q2 — Race/faction distribution:** Is the race balance Protoss/Zerg/Terran roughly
equal (36/35/29%)? What do the selectedRace anomalies (1,110 empty strings, 10 Rand)
look like?

**Q3 — MMR distribution:** What does the 84% zero-spike look like? Among the 16%
non-zero rows, is the distribution unimodal? Does the min=-36,400 negative value
appear as a visible outlier?

**Q4 — APM distribution (in-game):** Is APM near-symmetric as census suggests
(skewness=-0.20)? Do the 1,132 APM=0 rows form a visible spike?

**Q5 — SQ distribution (in-game):** Does the INT32_MIN sentinel appear as an
isolated spike far below the main mass? What does the sentinel-excluded distribution
look like?

**Q6 — supplyCappedPercent (in-game):** Is it right-skewed as census suggests
(skewness=2.25)? Is the median near 6%?

**Q7 — Duration distribution (in-game):** How does the body (clipped at p95=22.5 min)
compare to AoE2 durations? SC2 games are shorter — does the visual confirm this?

**Q8 — MMR zero-spike interpretation:** Does the MMR=0 rate correlate with
result (win/loss) or league? (Census confirms: uniform — "not reported" sentinel.)

**Q9 — Temporal coverage:** Does the 2016-2024 span show gaps? Is there a
mid-period peak and late-period decline?

**Q10 — Clan membership:** What fraction are in clans (26%)? Which clans dominate?

**Q11 — Map distribution:** What does the top-20 map concentration look like?
How does 188 distinct maps compare to AoE2's 261 (aoe2companion) and 93 (aoestats)?

**Q12 — highestLeague distribution:** With 72% Unknown, what does the league
distribution look like for the known subset?

## Part A — ROADMAP Patch

The ROADMAP entry for 01_02_05 is minimal (no outputs, gate, or invariants listed).
Replace the entire YAML block:

**Full replacement:**
```yaml
step_number: "01_02_05"
name: "Univariate EDA Visualizations"
description: "14 visualization plots for the sc2egset univariate census findings from 01_02_04. Reads the 01_02_04 JSON artifact and queries DuckDB for histogram bin data. All plots saved to artifacts/01_exploration/02_eda/plots/. Temporal annotations on in-game columns (APM, SQ, supplyCappedPercent, elapsed_game_loops) per Invariant #3."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Sections 2.1, 3.4"
dataset: "sc2egset"
question: "What do the distributions from 01_02_04 look like visually, and do the visual patterns confirm or challenge the statistical summaries?"
method: "Read 01_02_04 JSON artifact. Query DuckDB for histogram bins (MMR, APM, SQ, supplyCappedPercent, duration). Produce 14 plots: result 2-bar, categorical 3-panel (race/highestLeague/region), selectedRace bar, MMR split view, APM histogram (IN-GAME), SQ split view (IN-GAME), supplyCappedPercent histogram (IN-GAME), duration dual-panel (IN-GAME), MMR zero-spike cross-tab, temporal coverage line, isInClan bar, clanTag top-20, map top-20 barh, player repeat frequency. Markdown artifact with SQL queries."
predecessors: "01_02_04"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py"
inputs:
  duckdb_tables:
    - "replay_players_raw"
    - "replays_meta_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  external_references:
    - ".claude/scientific-invariants.md"
outputs:
  plots:
    - "artifacts/01_exploration/02_eda/plots/01_02_05_result_bar.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_categorical_bars.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_selectedrace_bar.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_mmr_split.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_apm_hist.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_sq_split.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_supplycapped_hist.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_duration_hist.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_mmr_zero_interpretation.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_temporal_coverage.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_isinclan_bar.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_clantag_top20.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_map_top20.png"
    - "artifacts/01_exploration/02_eda/plots/01_02_05_player_repeat_frequency.png"
  report: "artifacts/01_exploration/02_eda/01_02_05_visualizations.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "3"
    how_upheld: "All four in-game columns (APM, SQ, supplyCappedPercent, elapsed_game_loops) carry a visible annotation: 'IN-GAME — not available at prediction time (Inv. #3)'."
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "All bin widths, clip boundaries, sentinel thresholds derived from census JSON at runtime. No hardcoded numbers."
  - number: "9"
    how_upheld: "Visualization of 01_02_04 findings only. No new analytical computation."
gate:
  artifact_check: "All 14 PNG files and 01_02_05_visualizations.md exist and are non-empty."
  continue_predicate: "All 14 PNG files exist. Markdown artifact contains plot index table with Temporal Annotation column and all SQL queries. Notebook executes end-to-end without errors."
  halt_predicate: "Any PNG file is missing or notebook execution fails."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet"
research_log_entry: "Required on completion."
```

## Part B — Notebook Task List

### T01 — ROADMAP Patch

**Objective:** Replace the ROADMAP.md Step 01_02_05 entry with the full specification.

**Instructions:**
1. Open `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`.
2. Replace the entire Step 01_02_05 YAML block with the content from Part A.

**Verification:**
- ROADMAP.md Step 01_02_05 lists 14 PNG outputs under `plots/`.
- `scientific_invariants_applied` block present with I3, I6, I7, I9.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`

### T02 — Notebook Setup

**Objective:** Create the notebook skeleton (may reuse structure from existing 687-line notebook).

**Instructions:**
1. Create `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`
   with jupytext percent-format header.
2. Markdown header, imports, DuckDB connection, census JSON load (same pattern as existing).
3. Assert required keys: `result_distribution`, `categorical_profiles`, `monthly_counts`,
   `mmr_zero_interpretation`, `isInClan_distribution`, `clanTag_top20`.
4. Set up paths: `artifacts_dir`, `plots_dir`, `sql_queries = {}`.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py`

### T03 — Result Distribution 2-Bar (Q1, cross-dataset mandatory)

**Scientific question answered:** Q1 — Target balance.

**Input:** `census["result_distribution"]` (list of dicts with keys `result`, `cnt`, `pct`).

**Output:** `plots/01_02_05_result_bar.png`

**Plot design:**
- 2-bar chart (Win and Loss only).
- Extract non-target categories dynamically:
  ```python
  df = pd.DataFrame(census["result_distribution"])
  n_undecided = int(df.loc[df["result"] == "Undecided", "cnt"].values[0])
  n_tie = int(df.loc[df["result"] == "Tie", "cnt"].values[0])
  total_n = int(df["cnt"].sum())
  ```
- Colors: Win=steelblue, Loss=salmon.
- Bar annotations: count and percentage.
- Title: `f"Result Distribution (N={total_n:,})"`.
- Text annotation: `f"Excluded: Undecided ({n_undecided}), Tie ({n_tie}) — 13 replays total"`.
  (Note: "13 replays" is derived: (24+2)/2 = 13. But derive dynamically:
  `n_excluded_replays = (n_undecided + n_tie) // 2`.)

**Invariant notes:**
- I7: all values from census JSON. Undecided=24 and Tie=2 extracted at runtime, not hardcoded.

### T04 — Categorical Distributions 3-Panel (Q2, Q12)

**Scientific question answered:** Q2, Q12 — Race and league distributions.

**Input:** `census["categorical_profiles"]` for `race`, `highestLeague`, `region`.

**Output:** `plots/01_02_05_categorical_bars.png`

**Plot design:**
- 1x3 subplot panel: race, highestLeague, region.
- Each: vertical bar chart with annotations.

### T05 — selectedRace Bar (Q2 supplement)

**Scientific question answered:** Q2 — selectedRace anomalies.

**Input:** `census["categorical_profiles"]["selectedRace"]`.

**Output:** `plots/01_02_05_selectedrace_bar.png`

**Plot design:**
- Vertical bar chart. Empty-string bar highlighted in red.
- Title: "selectedRace Distribution".

### T06 — MMR Split View (Q3, cross-dataset mandatory for rating)

**Scientific question answered:** Q3 — MMR distribution.

**Input:** DuckDB query on replay_players_raw. Census: 83.65% zero,
non-zero range [-36,400, 7,464].

**Output:** `plots/01_02_05_mmr_split.png`

**SQL (store in sql_queries["hist_mmr"]):**
```sql
SELECT MMR FROM replay_players_raw WHERE MMR IS NOT NULL
```

**Plot design:**
- 2-panel: left = all MMR (showing zero spike), right = MMR > 0 only.
- Left: full histogram showing the dominant zero-spike.
- Right: histogram of non-zero MMR values only.
- Title: `f"MMR Distribution — replay_players_raw (N={total_n:,})"`.
- Left subtitle: `f"83.65% zero-valued (sentinel = not reported)"`.
- Sentinel exclusion count: `census["zero_counts"]["replay_players_raw"]["MMR_zero"]` = 37,489.

**Invariant notes:**
- I7: zero count from census. Sentinel interpretation from census `mmr_zero_interpretation`.
- I6: SQL in sql_queries dict.

### T07 — APM Histogram with IN-GAME Annotation (Q4)

**Scientific question answered:** Q4 — APM distribution.

**Input:** DuckDB query on replay_players_raw. Census: mean=355.6, median=349,
std=104.9, p05=219, p95=523.

**Output:** `plots/01_02_05_apm_hist.png`

**SQL (store in sql_queries["hist_apm"]):**
```sql
SELECT APM FROM replay_players_raw WHERE APM IS NOT NULL
```

I7 justification: bin width chosen by matplotlib auto-binning (Sturges or FD rule)
given the manageable row count (44,817). Or use 20 bins = (523-219)/20 = ~15 APM per bin.

**Plot design:**
- Single-panel histogram.
- Title includes N, mean, median.

**Temporal classification annotation:**
```python
ax.annotate(
    "IN-GAME — not available at prediction time (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)
```

### T08 — SQ Split View with IN-GAME Annotation (Q5)

**Scientific question answered:** Q5 — SQ distribution.

**Input:** DuckDB query on replay_players_raw. Census: SQ has 2 INT32_MIN sentinels.
Sentinel-excluded: range [-51, 187], median=123, mean=122.4, std=18.9.

**Output:** `plots/01_02_05_sq_split.png`

**SQL (store in sql_queries["hist_sq"]):**
```sql
SELECT SQ FROM replay_players_raw WHERE SQ IS NOT NULL
```

**Plot design:**
- 2-panel: left = all SQ (showing INT32_MIN sentinel spike), right = sentinel excluded
  (SQ > -2147483648).
- Sentinel threshold: `INT32_MIN = -2147483648` from census
  (`census["zero_counts"]["replay_players_raw"]["SQ_sentinel"]` = 2).

**Temporal classification annotation (on each subplot):**
```python
for ax_panel in [ax_all, ax_clean]:
    ax_panel.annotate(
        "IN-GAME — not available at prediction time (Inv. #3)",
        xy=(0.02, 0.98), xycoords="axes fraction",
        ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
        bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
    )
```

### T09 — supplyCappedPercent Histogram with IN-GAME Annotation (Q6)

**Scientific question answered:** Q6 — supplyCappedPercent.

**Input:** DuckDB query. Census: median=6, mean=7.24, std=4.71, skewness=2.25.

**Output:** `plots/01_02_05_supplycapped_hist.png`

**SQL (store in sql_queries["hist_supplycapped"]):**
```sql
SELECT supplyCappedPercent FROM replay_players_raw
WHERE supplyCappedPercent IS NOT NULL
```

**Plot design:**
- Single-panel histogram.

**Temporal classification annotation:**
```python
ax.annotate(
    "IN-GAME — not available at prediction time (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)
```

### T10 — Duration Dual-Panel Histogram with IN-GAME Annotation (Q7, cross-dataset mandatory)

**Scientific question answered:** Q7 — Game duration.

**Input:** DuckDB query on replays_meta_raw. Census: p95=30,270.1 game loops,
LOOPS_PER_SECOND=22.4 (SC2 "Faster" speed). p95 in seconds: 30270.1/22.4 = 1,351.3s = 22.5 min.
p95 in minutes: 22.5.

**Output:** `plots/01_02_05_duration_hist.png`

**SQL (store in sql_queries["hist_duration"]):**
```sql
SELECT header.elapsedGameLoops AS elapsed_game_loops
FROM replays_meta_raw
WHERE header.elapsedGameLoops IS NOT NULL
```

I7 justification: p95 = 30,270.1 game loops from census key `duration_stats["p95"]`.
Conversion: `LOOPS_PER_SECOND = 22.4` (SC2 "Faster" game speed, documented in SC2
engine specification). `CLIP_SECONDS = census["duration_stats"]["p95"] / LOOPS_PER_SECOND`.

**Plot design:**
- 2-panel (1x2): left = body clipped at p95=22.5 min, right = full range log-y.
- Left panel title: `f"Game Duration — Body (clipped at p95={clip_min:.0f} min)"`.
- Subtitle: `f"p95 clip = {clip_min:.0f} min; cf. aoe2companion 63 min, aoestats 79 min"`.
- Convert game loops to minutes for x-axis: `/ LOOPS_PER_SECOND / 60`.

**Temporal classification annotation (on each subplot):**
```python
for ax_panel in [ax_body, ax_full]:
    ax_panel.annotate(
        "IN-GAME — not available at prediction time (Inv. #3)",
        xy=(0.02, 0.98), xycoords="axes fraction",
        ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
        bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
    )
```

Note: identical annotation text to T07, T08, T09. No variant wording for duration.

### T11 — MMR Zero-Spike Cross-Tab (Q8)

**Scientific question answered:** Q8 — MMR=0 interpretation.

**Input:** `census["mmr_zero_interpretation"]`.

**Output:** `plots/01_02_05_mmr_zero_interpretation.png`

**Plot design:**
- Grouped bar chart or heatmap showing MMR=0 rate by result and by league.
- Confirms uniform distribution (no correlation with outcome).

### T12 — Temporal Coverage Line Chart (Q9)

**Scientific question answered:** Q9 — Temporal span and gaps.

**Input:** `census["monthly_counts"]` (pre-computed in JSON).

**Output:** `plots/01_02_05_temporal_coverage.png`

**Plot design:**
- Line chart with markers. X: month. Y: replay count.
- Title: "Monthly Replay Volume — sc2egset".

### T13 — isInClan Bar (Q10)

**Scientific question answered:** Q10 — Clan membership.

**Input:** `census["isInClan_distribution"]`.

**Output:** `plots/01_02_05_isinclan_bar.png`

### T14 — clanTag Top-20 Barh (Q10 supplement)

**Scientific question answered:** Q10 — Top clans.

**Input:** `census["clanTag_top20"]`.

**Output:** `plots/01_02_05_clantag_top20.png`

### T15 — Map Top-20 Barh (Q11, cross-dataset mandatory)

**Scientific question answered:** Q11 — Map concentration.

**Input:** `census["categorical_profiles"]["map_name"]` (top-20 list).

**Output:** `plots/01_02_05_map_top20.png`

**Plot design:**
- Horizontal barh, top-20, sorted descending.
- Bar annotations: count and percentage.
- Total replays derived from census: `total_replays = census["null_census"]["replays_meta_raw_filename"]["total_rows"]` (22,390).
  Single clean derivation. No dead code, no hardcoded 22390.
- `total_in_top20 = sum(r["cnt"] for r in census["categorical_profiles"]["map_name"])`.
- `pct_top20 = 100.0 * total_in_top20 / total_replays`.
- Title: `f"Map Distribution — Top 20 of {cardinality} (replays_meta_raw)"`.
  Cardinality from census cardinality data for map_name (188).
- Subtitle: `f"Top-20 coverage: {pct_top20:.1f}% of {total_replays:,} replays"`.
- DataFrame column names: `map_data["map_name"]` for y-axis, `map_data["cnt"]` for x-axis.

**Invariant notes:**
- I7: total_replays from census, not hardcoded. Cardinality 188 from census.

### T16 — Player Repeat Frequency (Games per toon_id)

**Scientific question answered:** How concentrated is the player pool in sc2egset?
With 2,495 unique players across 44,817 rows (~18 games/player average), is this a
small pool of recurring tournament regulars or a broad base with many one-time
appearances? A heavily right-skewed distribution signals that replay-based train/val
splits leak player-level information (same player in train and val), directly
informing the Phase 03 splitting strategy.

**Input:** DuckDB query on replay_players_raw. Census: toon_id cardinality = 2,495,
total_rows = 44,817, top player = 512 appearances. These values derived at runtime
from `census["cardinality"]` and `census["null_census"]["replay_players_raw_filename"]["total_rows"]`.

**Output:** `plots/01_02_05_player_repeat_frequency.png`

**SQL (store in `sql_queries["hist_player_repeat"]`):**
```sql
SELECT games_per_player, COUNT(*) AS player_count
FROM (
    SELECT toon_id, COUNT(*) AS games_per_player
    FROM replay_players_raw
    GROUP BY toon_id
)
GROUP BY games_per_player
ORDER BY games_per_player
```

**Python:**
```python
# --- T16: Player Repeat Frequency ---
# I7: n_unique_players and total_n derived from census at runtime
cardinality_entry = next(
    (c for c in census["cardinality"] if c["column"] == "toon_id" and "replay" in c.get("table", "")),
    next(c for c in census["cardinality"] if c["column"] == "toon_id")
)
n_unique_players = int(cardinality_entry["cardinality"])
total_n = int(census["null_census"]["replay_players_raw_filename"]["total_rows"])
mean_games = total_n / n_unique_players

sql_queries["hist_player_repeat"] = """
SELECT games_per_player, COUNT(*) AS player_count
FROM (
    SELECT toon_id, COUNT(*) AS games_per_player
    FROM replay_players_raw
    GROUP BY toon_id
)
GROUP BY games_per_player
ORDER BY games_per_player
"""

df_repeat = conn.execute(sql_queries["hist_player_repeat"]).fetchdf()

# Compute median from distribution
df_repeat["cum_players"] = df_repeat["player_count"].cumsum()
median_games = int(df_repeat.loc[df_repeat["cum_players"] >= n_unique_players / 2, "games_per_player"].iloc[0])

fig, ax = plt.subplots(figsize=(12, 5))
ax.bar(
    df_repeat["games_per_player"],
    df_repeat["player_count"],
    color="steelblue", alpha=0.8, width=0.8,
)
ax.set_yscale("log")
ax.set_xlabel("Games per player (toon_id)")
ax.set_ylabel("Number of players (log scale)")
ax.set_title(
    f"Player Repeat Frequency — replay_players_raw\n"
    f"N_players = {n_unique_players:,}  |  N_rows = {total_n:,}  |  "
    f"mean = {mean_games:.1f} games/player"
)
ax.axvline(mean_games, color="darkorange", linestyle="--", linewidth=1.2,
           label=f"mean = {mean_games:.1f}")
ax.axvline(median_games, color="red", linestyle=":", linewidth=1.2,
           label=f"median = {median_games}")
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3)

fig.tight_layout()
fig.savefig(plots_dir / "01_02_05_player_repeat_frequency.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {plots_dir / '01_02_05_player_repeat_frequency.png'}")
```

**Temporal annotation:** None. toon_id is a player identifier — structural dataset property,
not an in-game or post-game metric. No I3 annotation required.

**Invariant notes:**
- I7: n_unique_players and total_n derived from census artifact at runtime. mean_games
  computed as `total_n / n_unique_players`. median_games computed from query result
  cumulative sum. No hardcoded values.
- I6: SQL stored in `sql_queries["hist_player_repeat"]` and written to markdown artifact.
- I9: Visualizes census cardinality finding (2,495 distinct toon_ids, uniqueness_ratio 0.056).
  No new analytics — bins the per-player counts that follow from existing cardinality data.

### T17 — Markdown Artifact, Verification, and Connection Close

**Objective:** Write markdown artifact, verify all 14 plots, close connection.

**Instructions:**
1. Define `expected_plots` list with all 14 PNG filenames:
   ```
   "01_02_05_result_bar.png",
   "01_02_05_categorical_bars.png",
   "01_02_05_selectedrace_bar.png",
   "01_02_05_mmr_split.png",
   "01_02_05_apm_hist.png",
   "01_02_05_sq_split.png",
   "01_02_05_supplycapped_hist.png",
   "01_02_05_duration_hist.png",
   "01_02_05_mmr_zero_interpretation.png",
   "01_02_05_temporal_coverage.png",
   "01_02_05_isinclan_bar.png",
   "01_02_05_clantag_top20.png",
   "01_02_05_map_top20.png",
   "01_02_05_player_repeat_frequency.png",
   ```
   NOTE: 14 entries (not 13).
2. Assert all exist on disk.
3. Build markdown with:
   - Header.
   - Plot index table with columns: #, Title, Filename, Observation, Temporal Annotation.
     Temporal Annotation: "IN-GAME (Inv. #3)" for APM, SQ, supplyCappedPercent, duration;
     "N/A" for all others.
     Observation for result: correct Undecided count to 24 (not 7 as in prior artifact).
   - SQL Queries section: enumerate ALL queries from sql_queries dict:
     `hist_mmr`, `hist_apm`, `hist_sq`, `hist_supplycapped`, `hist_duration`, `hist_player_repeat`.
   - Data Sources section.
4. Write to `artifacts_dir / "01_02_05_visualizations.md"`.
5. Close DuckDB connection.

**Verification:**
- All 14 PNG files exist (verify count is 14, not 13).
- Markdown artifact contains all 6 SQL queries.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py` (continuation)
- `reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md` (generated)

### T18 — STEP_STATUS Update

**Objective:** Mark 01_02_05 as complete.

**Instructions:**
1. Update `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`:
   set `01_02_05.status` to `complete` and `01_02_05.completed_at` to the execution date.
   (Single instruction only — no contradictory "do NOT modify" text.)

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`

## Cross-Dataset Comparability Checklist

| Mandatory Plot | Column | p95 Clip | Dataset-Specific Handling |
|---|---|---|---|
| (a) Target 2-bar | `result` (VARCHAR: Win/Loss) | N/A | Undecided (24) and Tie (2) annotated as text, not plotted as bars |
| (b) Map top-20 barh | `map_name` (VARCHAR, 188 distinct) | N/A | From census categorical_profiles. total_replays from `census["null_census"]["replays_meta_raw_filename"]["total_rows"]`. |
| (c) Duration dual-panel | `elapsed_game_loops / 22.4 / 60` (game loops to minutes) | p95=30,270.1 loops=22.5 min | SC2 games much shorter than AoE2. Subtitle notes cross-dataset comparison. IN-GAME annotated. |
| (d) Rating/MMR histogram | `MMR` (INTEGER, 84% sentinel=0) | N/A | Split view: all (showing zero spike) + non-zero only. Sentinel=0 excluded in right panel. |

All four present: confirmed.

## Gate Condition

- [ ] `plots/01_02_05_result_bar.png`
- [ ] `plots/01_02_05_categorical_bars.png`
- [ ] `plots/01_02_05_selectedrace_bar.png`
- [ ] `plots/01_02_05_mmr_split.png`
- [ ] `plots/01_02_05_apm_hist.png`
- [ ] `plots/01_02_05_sq_split.png`
- [ ] `plots/01_02_05_supplycapped_hist.png`
- [ ] `plots/01_02_05_duration_hist.png`
- [ ] `plots/01_02_05_mmr_zero_interpretation.png`
- [ ] `plots/01_02_05_temporal_coverage.png`
- [ ] `plots/01_02_05_isinclan_bar.png`
- [ ] `plots/01_02_05_clantag_top20.png`
- [ ] `plots/01_02_05_map_top20.png`
- [ ] `plots/01_02_05_player_repeat_frequency.png`
- [ ] `01_02_05_visualizations.md` with SQL queries and plot index table including Temporal Annotation column
- [ ] ROADMAP.md Step 01_02_05 patched (full YAML block)
- [ ] STEP_STATUS.yaml `01_02_05` -> complete
- [ ] Notebook executes end-to-end without error

## File Manifest

| File | Action |
|------|--------|
| `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.py` | Create |
| `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_05_visualizations.ipynb` | Create (jupytext sync) |
| `reports/artifacts/01_exploration/02_eda/plots/01_02_05_*.png` (14 files) | Create |
| `reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | Modify |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` | Modify |

## Out of Scope

- New analytics beyond 01_02_04 findings (Invariant #9)
- Bivariate or multivariate analysis (future steps)
- Research log entry (written post-execution)
- Event table visualization (608M rows; deferred per EDA Manual)
- Cleaning of Undecided/Tie/BW-race entries (Step 01_04)

## Open Questions

- Optimal MMR handling for 84% missing: imputation vs. indicator vs. subsetting (Phase 02)
- Whether isInClan/clanTag carry win-rate signal (Phase 02)

---

For Category A, adversarial critique is required before execution.
Dispatch reviewer-adversarial to produce `planning/plan_sc2egset_01_02_05.critique.md`.
```

---

## Summary

Three plan files written:

| File | Dataset | Plot Count | All Critiques Resolved |
|------|---------|-----------|----------------------|
| `planning/plan_aoe2companion_01_02_05.md` | aoe2companion | 16 | Yes: NULL filter identity check, duration p95 clip with cross-dataset subtitle, NULL co-occurrence as 2x2 table not heatmap, explicit markdown SQL section enumeration, POST-GAME annotation on ratingDiff |
| `planning/plan_aoestats_01_02_05.md` | aoestats | 14 | Yes: CREATE framing (not MODIFY), match_rating_diff I7 as ~3.6sigma editorial (not p05/p95), duration label is `"duration_sec"` confirmed, `distinct_match_count` for T04, avg_elo sentinel exclusion documented, soft assertion for monthly counts, LEAKAGE UNRESOLVED annotation on match_rating_diff, IN-GAME on opening/age uptimes, POST-GAME on duration |
| `planning/plan_sc2egset_01_02_05.md` | sc2egset | 14 | Yes: STEP_STATUS single instruction only, total_replays single clean derivation from census, all four in-game plots use identical annotation text, expected_plots updated to 14 entries (adding map_top20.png and player_repeat_frequency.png), Undecided/Tie extraction code specified, single annotation placement mandated |

For Category A, adversarial critique is required before execution begins. Dispatch reviewer-adversarial to produce critique files for all three plans.
