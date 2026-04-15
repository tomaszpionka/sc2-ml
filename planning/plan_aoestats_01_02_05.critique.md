---
reviewer: reviewer-adversarial
plan: planning/plan_aoestats_01_02_05.md
date: 2026-04-15
verdict: REWORK REQUIRED
blocking_count: 2
warning_count: 6
---

# Adversarial Review — aoestats 01_02_05 Plan

## Lens Assessments

- **Temporal discipline:** AT RISK — The plan correctly identifies post-game/in-game columns and specifies annotations. However, the plan describes a CREATE workflow against artifacts that already exist on disk. An executor following "Create" instructions will overwrite 842 lines of working code.
- **Thesis defensibility:** AT RISK — The match_rating_diff I7 justification is wrong (claims p05/p95 derivation, but actual p05/p95 are ±59, not ±200).
- **Cross-game comparability:** MAINTAINED — Plan explicitly checks constraints #7a–#7d and harmonizes NULL thresholds.

## Examiner's Questions

1. "Why is your match_rating_diff histogram clipped to [-200, +200] when the census shows p05=-59 and p95=59?" The plan has no documented answer — the hardcoded [-200, +200] is approximately 3.6σ from the stddev, which is a defensible editorial choice, but the plan claims I7 derivation from p05/p95 which is false.
2. "Why does the avg_elo histogram not exclude sentinel/zero values, while team_0/1_elo histograms do?"

---

## BLOCKER 1 — Plan describes CREATE for artifacts that already exist

**[BLOCKER]** The notebook `sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_05_visualizations.py` already exists (842 lines, fully executed). The STEP_STATUS already shows 01_02_05 as `complete` (completed_at: 2026-04-14). All 14 PNG artifacts already exist under `plots/`. The markdown artifact `01_02_05_visualizations.md` also exists (130 lines).

The File Manifest (line 804) says "Action: Create" for the notebook, .ipynb, and .md. An executor following "Create" will write the notebook from scratch, overwriting 842 lines of working code with only the plan's pseudo-code. This risks destroying a working implementation.

**Required fix:** Reframe the plan as a MODIFICATION of existing artifacts:
- Change all File Manifest actions from "Create" to "Modify/Amend"
- Add a "Prior State" section at the top enumerating what already exists and confirming the current state
- Change T16 STEP_STATUS instruction from "change from not_started to complete" to "update completed_at to execution date; status remains complete"
- For each modified task (T07, T10, T11, T12), specify the exact line numbers and content to change in the existing 842-line notebook, not a from-scratch implementation
- For T16 (artifact writing), specify what changes to the existing 130-line markdown artifact (add temporal annotation column, not rewrite from scratch)

The temporal annotations are the only substantive changes needed. The plan's pseudo-code for tasks T03–T15 is correct as intent, but must be framed as targeted modifications.

---

## BLOCKER 2 — Invariant #7 violation on match_rating_diff clip

**[BLOCKER]** Plan T10 (line 478): SQL clips `match_rating_diff BETWEEN -200 AND 200`. The plan's I7 annotation says this derives from p05/p95. Census JSON (lines 1245–1249) shows: p05=-59.0, p95=59.0. The hardcoded [-200, +200] is NOT derived from p05/p95 (which are ±59), NOT from IQR fences (which are ±68 per census), and NOT from any documented census statistic.

The existing notebook (line 432) has a comment: "clip to [-200, +200] to show leptokurtic shape while covering main body; full range is [-2185, +2185]." This is a defensible editorial choice (~3.6σ from stddev=55.23), but the plan must not claim I7 compliance via "from p05/p95."

**Required fix:** Either:
- **(a)** Change the I7 comment to the actual derivation: `# I7: clip at approx. 3.6σ (stddev=55.23 from census); shows leptokurtic tail structure without the [-2185, +2185] range extremes. Chosen to cover ~99.97% of data. stddev from census["skew_kurtosis_players"] where label="match_rating_diff".`; OR
- **(b)** Change the clip to the actual p05/p95 of [-59, +59] and update the I7 comment accordingly.

Option (a) is the better visualization choice (shows more of the leptokurtic tails) and requires only a comment correction.

---

## T02 — Notebook Skeleton and Setup

**[WARNING] T02-1:** The import `from rts_predict.games.aoe2.config import AOESTATS_DB_FILE` — verify this symbol exists. The existing notebook uses `from rts_predict.games.aoe2.config import AOESTATS_DB_FILE` at line 14 (confirmed). No issue.

**[NOTE] T02-2:** The import `from rts_predict.common.notebook_utils import get_reports_dir` — confirmed at existing notebook line 15. `get_reports_dir("aoe2", "aoestats")` confirmed as valid call. No issue.

**[NOTE] T02-3:** `plots_dir.mkdir(parents=True, exist_ok=True)` is in the existing setup cell (line 23). The `plots/` subdirectory already exists with 14 PNGs. No issue.

---

## T03 — Winner Distribution

**[WARNING] T03-1:** The existing notebook at line 82 uses `colors = {True: "green", False: "red"}`. The plan (line 224) specifies "Colors: Win=steelblue, Loss=salmon." This is an out-of-scope color change: the plan's goal is to add temporal annotations, not change aesthetics. The plan should preserve the existing colors unless harmonization with aoe2companion/sc2egset is explicitly required (which the audit did not mandate for colors, only for bar count and annotation structure).

**[WARNING] T03-2:** `winner_distribution` structure confirmed in JSON (list of dicts with keys `winner`, `row_count`, `pct`). Plan's `pd.DataFrame(winner_data)` will produce a valid DataFrame. However, the plan should specify column name `winner` (boolean), not `result` or `won`, to avoid executor confusion across datasets.

---

## T04 — num_players Distribution

**[WARNING] T04-1:** The plan says "annotated with count and pct." The census `num_players_distribution` has keys `num_players`, `row_count`, `distinct_match_count`, `pct`, and `distinct_match_pct`. The plan does not specify which count. The existing notebook (line 118) uses `distinct_match_count` for the bar height, which is correct for a "match size distribution" (counts matches, not player-rows). The plan must specify `distinct_match_count`, not `row_count`, to avoid an ambiguous executor producing the wrong y-axis values.

---

## T07 — Duration Histogram

**[WARNING] T07-1:** SQL uses `duration / 1e9 / 60` for nanoseconds→minutes. Confirmed: `duration` column in `matches_raw` is BIGINT nanoseconds (per `matches_raw.yaml` line 43: `type: BIGINT` with `description: "Match duration in nanoseconds"`). SQL is correct.

**[WARNING] T07-2:** `census["numeric_stats_matches"]` where `label="duration_sec"` — the actual census label for duration is `"duration"` (from the census JSON line 287: `{"label": "duration", ...}`). The label is NOT `"duration_sec"`. An executor using `label="duration_sec"` will get `None` from the lookup and raise a KeyError or produce a silent None. The plan must use `label="duration"` and note that the unit is nanoseconds (requiring division by 1e9 for seconds before computing median/p95 in minutes).

---

## T08 — ELO Distributions

**[WARNING] T08-1:** The avg_elo histogram (plan line 386–389) has no sentinel exclusion (`GROUP BY bin ORDER BY bin` with no WHERE clause). Census shows `avg_elo` min_val=0.0 and n_zero=121. If avg_elo is computed from team_0/1_elo, matches with sentinel team values (-1.0) will have anomalous avg_elo. With team_0_elo having 34 sentinels and team_1_elo having 39, approximately 34–73 matches will produce corrupted avg_elo values. Given 30.7M rows, the visual impact is negligible, but the asymmetry (team_0/1 exclude sentinels; avg_elo does not) should be documented in an I7 comment or excluded consistently.

---

## T10 — match_rating_diff (see BLOCKER 2 above)

Also: `census["skew_kurtosis_players"]` — the actual label for match_rating_diff in the skew_kurtosis list is confirmed as `"match_rating_diff"` (JSON line 1379). No issue with label lookup.

---

## T11 — Age Uptimes

**[WARNING] T11-1:** Column names `feudal_age_uptime`, `castle_age_uptime`, `imperial_age_uptime` confirmed in `players_raw.yaml`. The I7 p05/p95 values (feudal: p05=535.1, p95=962.6; castle: p05=889.1, p95=1752.1; imperial: p05=1681.1, p95=2933.0) are confirmed in census JSON. Bin widths (10s/20s/30s) are correctly derived. No issue.

---

## T15 — Monthly Match Count

**[WARNING] T15-1:** The assertion `len(monthly_df) == census["temporal_range"]["distinct_months"]` (expected: 42) will fail if any calendar month within the range has zero matches. DuckDB GROUP BY does not produce zero-count rows. The existing notebook passes this assertion empirically (confirmed), but the plan should note this assumption explicitly. Recommend changing to a soft check: `assert len(monthly_df) <= census["temporal_range"]["distinct_months"]`.

---

## T-Number Mapping Warning

**[NOTE]:** The plan's T-numbers (T03–T15) do not match the existing notebook's internal section labels. Examples:
- Plan T10 (match_rating_diff) → notebook section "T09" (line 389)
- Plan T11 (age uptimes) → notebook section "T10" (line 477)
- Plan T12 (opening) → notebook section "T11" (line 569)

An executor applying modifications by T-number will need a mapping. The plan should include a cross-reference table or refer to notebook line numbers.

---

## Summary Table

| ID | Severity | Task | Finding |
|----|----------|------|---------|
| BLOCKER-1 | **BLOCKER** | All | Plan describes CREATE for artifacts that already exist; will overwrite working 842-line notebook |
| BLOCKER-2 | **BLOCKER** | T10 | I7 justification for [-200, +200] clip claims p05/p95 derivation; actual p05/p95 are ±59 |
| T03-1 | WARNING | T03 | Color change (green/red → steelblue/salmon) is out of scope for this revision |
| T04-1 | WARNING | T04 | Must use `distinct_match_count`, not `row_count` for match size bars |
| T07-2 | WARNING | T07 | Duration census label is `"duration"` (nanoseconds), not `"duration_sec"` |
| T08-1 | WARNING | T08 | avg_elo histogram lacks sentinel exclusion; asymmetric treatment vs team_0/1_elo |
| T11-1 | NOTE | T11 | I7 p05/p95 values and bin widths confirmed correct |
| T15-1 | WARNING | T15 | Assertion `len == distinct_months` will fail if any month has zero matches |

---

## VERDICT: REWORK REQUIRED

**Blocking conditions (must resolve before execution):**

1. **BLOCKER-1** — Reframe entire plan as MODIFICATION of existing artifacts. Add "Prior State" section. Change all File Manifest actions to Modify/Amend. Specify exact line numbers to change in the existing 842-line notebook.

2. **BLOCKER-2** — Correct the I7 annotation for match_rating_diff clip. Either document the actual derivation (~3.6σ from stddev=55.23) or change clip to actual p05/p95 of ±59.

**Additional fixes required before execution:**

3. T07-2: Change duration census label lookup from `"duration_sec"` to `"duration"`.

**Strongly recommended:**

4. T04-1: Specify `distinct_match_count` explicitly.
5. T15-1: Soften assertion to `<=`.
6. T-number mapping: add cross-reference table from plan T-numbers to notebook line numbers.
