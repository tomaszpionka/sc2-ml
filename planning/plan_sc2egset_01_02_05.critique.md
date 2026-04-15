---
reviewer: reviewer-adversarial
plan: planning/plan_sc2egset_01_02_05.md
date: 2026-04-15
verdict: APPROVE WITH CONDITIONS
blocking_count: 2
warning_count: 5
---

# Adversarial Review — sc2egset 01_02_05 Plan

## Lens Assessments

- **Temporal discipline:** SOUND — Visualization-only step. In-game annotations are correctly specified. Annotation wording inconsistency between ROADMAP promise and T09 implementation is a documentation gap, not a leakage risk.
- **Thesis defensibility:** ADEQUATE — Plan addresses all audit BLOCKERs. The data-derived p95 clip replaces the unjustified 40-min threshold. The map chart fills the cross-dataset gap.
- **Cross-game comparability:** MAINTAINED — Plan explicitly verifies all four mandatory plot types across all three datasets.

## Examiner's Questions

1. "The existing markdown artifact says '7 Undecided' but the JSON shows 24. How did this error survive the first two passes?" The plan implicitly fixes this via T14 but doesn't flag it as an error correction — an executor not reading T14 carefully could propagate the old error.
2. "Why does elapsed_game_loops get a different annotation text than APM, SQ, and supplyCappedPercent?" The plan does not justify the variant wording, and the ROADMAP promises identical text for all four.
3. "The top-20 map counts sum to 10,000 out of 22,390 replays — 44.7% coverage. Is this correct or a truncation artifact?" Answer: correct; the JSON `categorical_profiles["map_name"]` contains exactly 20 entries (pre-truncated top-20), and the sum of their counts is the actual replay count on those maps.

---

## Path / Existing State Check (Cross-Cutting CC-1)

**[CONFIRMED SAFE]** All existing tasks (T01, T03–T05, T10–T13) already write to `plots_dir` (confirmed at notebook lines 113, 159, 196, 256, 296, 344, 376, 430, 485, 522, 559, 591). The concern about unchanged tasks writing to a wrong path is not valid — the existing notebook already uses `plots_dir = artifacts_dir / "plots"`.

---

## T02 — Result Distribution Bar Chart (REVISED)

**[WARNING] T02-1 — Extraction code not specified:** The plan says derive `n_undecided` and `n_tie` "dynamically from the JSON data" but shows no code. The JSON structure is a list of dicts with keys `result`, `cnt`, `pct`. The plan's prose mentions "Undecided (24) and Tie (2)" — this creates a copy-paste hazard where an executor hardcodes these values, violating Invariant #7.

Required addition to plan:
```python
df = pd.DataFrame(census["result_distribution"])
n_undecided = int(df.loc[df["result"] == "Undecided", "cnt"].values[0])
n_tie = int(df.loc[df["result"] == "Tie", "cnt"].values[0])
```

**[NOTE] T02-2:** Total N for the title is not specified. The existing title uses the table name. The revision should add N to the title for thesis comparability: `f"Result Distribution (N={total_n:,})"` where `total_n = df["cnt"].sum()`.

**[NOTE] T02-3:** The existing markdown artifact (line 13) says "7 Undecided" — this is a factual error (correct value is 24). The plan (T14, line 484) implicitly corrects this. The plan should explicitly flag this as "correcting a factual error in the existing artifact."

---

## T06 — APM Histogram (REVISED — temporal annotation)

**[WARNING] T06-1 — Ambiguous placement choice:** The plan offers two annotation placements and says "the executor may choose either." For four in-game plots (T06, T07, T08, T09) that must be visually consistent in the thesis, the placement must be mandated as a single style. An executor choosing different placements for different plots will produce visually inconsistent figures.

**Required fix:** Mandate a single placement for all four in-game annotation tasks. Recommended: upper-left inside plot area with red background box:
```python
ax.annotate(
    "IN-GAME — not available\nat prediction time (Inv. #3)",
    xy=(0.02, 0.98), xycoords="axes fraction",
    ha="left", va="top", fontsize=8, fontstyle="italic", color="darkred",
    bbox=dict(boxstyle="round,pad=0.3", fc="#ffe0e0", ec="red", alpha=0.9),
)
```
Apply the same pattern to T07, T08 (and T09 with the variant wording — see T09-5 below).

**[CONFIRMED SAFE]:** The existing APM cell (notebook line 274) uses `fig, ax = plt.subplots(...)`. `ax.annotate(...)` will work.

---

## T07 — SQ Split View (REVISED — temporal annotation)

**[WARNING] T07-1 — fig.text() at y=0.01 will clip:** The existing SQ plot (line 316) uses `plt.tight_layout()` at line 343. After `tight_layout()`, the figure bottom margin is typically at y~0.08–0.12. `fig.text(0.5, 0.01, ...)` will be clipped or overlap the x-axis label.

**Required fix:** The plan specifies `subplots_adjust` only for T09. Add the same bottom adjustment for T07 if `fig.text()` is used, or apply the per-subplot `ax.annotate` pattern from T06 (which avoids the issue entirely). Since T06-1 above mandates a single annotation style, use the `ax.annotate` pattern on both subplots individually.

**[CONFIRMED SAFE]:** The existing notebook (line 316) defines `fig, (ax_a, ax_b) = ...`. Both axes are accessible.

---

## T08 — supplyCappedPercent Histogram (REVISED — temporal annotation)

**[CONFIRMED SAFE]:** The existing T08 cell (notebook line 363) uses `fig, ax = plt.subplots(...)`. `ax.annotate(...)` works. Column name `supplyCappedPercent` confirmed in JSON null_census (line 49). No issues.

---

## T09 — Duration Histogram (REVISED — clip + annotation)

**[CONFIRMED SAFE] T09-1:** `census["duration_stats"]["p95"]` = 30,270.1 game loops confirmed in JSON (line 2156). Derivation: 30,270.1 / 22.4 = 1,351.3s = 22.5 min. Correct.

**[CONFIRMED SAFE] T09-2:** `CLIP_SECONDS = 2400` and `LOOPS_PER_SECOND = 22.4` both confirmed in the existing notebook (lines 398 and 390). Replacement is correctly specified.

**[WARNING] T09-3 — Subplot titles not fully specified:** The plan specifies updating subplot (b) title to `f"Game Duration (clipped at p95 = {clip_minutes:.0f} min)"`. The existing suptitle (notebook line 428) says "Game Duration from elapsed_game_loops (replays_meta_raw)". The plan does not say whether to keep or update the suptitle. For consistency with T07/T08's temporal annotations, the suptitle or a figure-level annotation should carry the "IN-GAME" designation. Specify explicitly.

**[WARNING] T09-4 — `subplots_adjust` bottom value unspecified:** Line 381 says "Adjust `fig.subplots_adjust(bottom=...)` if needed." The two-line annotation text at fontsize=9 requires approximately y=0.08 of figure height. "If needed" forces the executor to iterate. Specify `bottom=0.12` or equivalent concrete value.

**[BLOCKER] T09-5 — ROADMAP annotation promise vs plan implementation mismatch:**

The ROADMAP `scientific_invariants_applied` section (Part A, line 151) states:
> "All four in-game columns (APM, SQ, supplyCappedPercent, elapsed_game_loops) carry a visible annotation: **'IN-GAME — not available at prediction time (Inv. #3)'**."

But T09 (line 376) specifies:
> `"IN-GAME (game-level descriptor) — duration known only after match ends (Inv. #3)"`

These are different texts. The ROADMAP will contain a factual misrepresentation of what the plan implements.

**Required fix:** Either:
- **(a)** Change T09 annotation text to the standard: `"IN-GAME — not available at prediction time (Inv. #3)"`; OR
- **(b)** Update the ROADMAP `how_upheld` to acknowledge the variant: `"elapsed_game_loops uses variant text noting game-level timing context."`

Option (a) is cleaner and ensures all four plots use identical annotation text.

---

## T14 — Markdown Artifact Update

**[WARNING] T14-1:** The existing artifact has a markdown table at lines 11–24. T14 says to add "Relationship to 01_02_04 Plots" section "after the plot index table." This should be specified as "between the plot index table and the SQL Queries section."

**[WARNING] T14-2:** The existing verification cell in the notebook (line 599–614) checks for exactly 12 expected plot filenames. After T16 adds `01_02_05_map_top20.png`, this list must be updated to 13 entries. The plan does not mention this cell. An executor following the plan will have a notebook that passes its own internal verification check against 12 files while the gate requires 13.

**Required addition to T14 instructions:** "Update the `expected_plots` list at notebook line 599 from 12 to 13 entries by adding `'01_02_05_map_top20.png'`."

---

## T15 — ROADMAP Update

**[BLOCKER] T15-1 — Contradictory STEP_STATUS instruction:**

Line 519: "Do NOT modify STEP_STATUS.yaml — the step status remains `complete` with the existing date."

Line 520: "After execution, STEP_STATUS `completed_at` should be updated to the new date."

The gate condition (line 562) says "STEP_STATUS.yaml `01_02_05.completed_at` updated to execution date" — which requires the update.

These two sentences within the same bullet point directly contradict each other. An executor following line 519 will fail the gate check at line 562.

**Required fix:** Remove the "Do NOT modify STEP_STATUS.yaml" sentence. Retain only: "Update STEP_STATUS.yaml `01_02_05.completed_at` to the execution date."

**[NOTE] T15-2:** `supplements_not_supersedes` is a non-standard ROADMAP field not in the step template. No parser will reject it, but it violates the template's "do not add new fields" rule. Acceptable for this use case, but the template should be updated in a follow-up chore.

---

## T16 — Map Top-20 (NEW)

**[BLOCKER] T16-1 — Code block contains dead code with hardcoded magic number:**

Lines 419–423 of the plan:
```python
total_in_top20 = sum(r["cnt"] for r in census["categorical_profiles"]["map_name"])
total_replays = census["duration_stats"]["min_val"]  # wrong, use below
# Actually, derive total replays from the known count:
total_replays = 22390  # But don't hardcode -- use:
total_replays = census["null_census"]["replays_meta_raw_filename"]["total_rows"]
```

This block has THREE assignments to `total_replays`, including a hardcoded 22390 explicitly forbidden by the plan's own text, and a line labeled `# wrong`. An executor copy-pasting this verbatim will produce a notebook with dead code containing a magic number, violating Invariant #7 and producing unprofessional artifact content an examiner could read.

**Required fix:** Replace the entire block with a single clean derivation:
```python
total_replays = census["null_census"]["replays_meta_raw_filename"]["total_rows"]
total_in_top20 = sum(r["cnt"] for r in census["categorical_profiles"]["map_name"])
pct_top20 = 100.0 * total_in_top20 / total_replays
```

**[WARNING] T16-2 — map_name field name not specified for DataFrame:** `pd.DataFrame(census["categorical_profiles"]["map_name"])` produces a DataFrame with columns `map_name` and `cnt`. The plan does not specify these column names for the barh plot. An executor using a wrong column name (e.g., `name` or `map`) will get a KeyError. Specify explicitly: y-axis from `map_data["map_name"]`, x-axis from `map_data["cnt"]`.

**[NOTE] T16-3:** Coverage percentage: `categorical_profiles["map_name"]` contains exactly 20 entries summing to 10,000 replays out of 22,390 total = 44.7% coverage. This is correct and defensible.

**[NOTE] T16-4:** Plan references `cardinality_data` key (line 429) which does not exist in the JSON. The correct key is `cardinality` (a list of dicts). This is documentation prose only — it does not affect runtime code since 188 is used only in the title string, derived from the same `cardinality` lookup. A minor documentation error.

---

## Summary Table

| ID | Severity | Task | Finding |
|----|----------|------|---------|
| T09-5 | **BLOCKER** | T09/ROADMAP | ROADMAP promises standard annotation text for all 4 columns; T09 uses variant text — ROADMAP will be inaccurate |
| T15-1 | **BLOCKER** | T15 | Contradictory STEP_STATUS instruction (line 519 says don't modify; line 520 says update; gate requires update) |
| T16-1 | **BLOCKER** | T16 | Code block has 3 `total_replays` assignments including hardcoded 22390; violates I7 |
| T02-1 | WARNING | T02 | Extraction code for `n_undecided`/`n_tie` unspecified; copy-paste hardcoding risk |
| T06-1 | WARNING | T06 | Ambiguous annotation placement (two options offered); all four in-game plots must use identical placement |
| T07-1 | WARNING | T07 | `fig.text()` at y=0.01 will clip after tight_layout; use `ax.annotate` per-subplot instead |
| T09-3 | WARNING | T09 | Suptitle update not specified; existing suptitle may not carry IN-GAME designation |
| T09-4 | WARNING | T09 | `subplots_adjust` bottom value unspecified ("if needed" forces executor to iterate) |
| T14-2 | WARNING | T14 | `expected_plots` verification cell (line 599) must be updated from 12 to 13 entries; plan does not mention it |
| T16-2 | WARNING | T16 | DataFrame column names `map_name`/`cnt` not specified for barh plot |

---

## VERDICT: APPROVE WITH CONDITIONS

**Blocking conditions (must resolve before execution):**

1. **T16-1** — Replace the three-line `total_replays` block with a single clean derivation. Remove all dead code, hardcoded values, and `# wrong` comments.

2. **T15-1** — Remove "Do NOT modify STEP_STATUS.yaml" sentence. Retain only the instruction to update `completed_at`.

3. **T09-5** — Harmonize T09 annotation text with the standard used in T06/T07/T08: `"IN-GAME — not available at prediction time (Inv. #3)"`. Update ROADMAP `how_upheld` if variant text is retained.

**Strongly recommended before gate sign-off:**

4. T06-1: Mandate a single annotation placement style for all four in-game plots.
5. T14-2: Add explicit instruction to update `expected_plots` list at notebook line 599 from 12 to 13 entries.
6. T02-1: Add explicit extraction code for `n_undecided` and `n_tie`.
7. T07-1: Replace `fig.text()` with `ax.annotate` on each subplot, consistent with T06 style.
