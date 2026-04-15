---
reviewer: reviewer-adversarial
model: claude-opus-4-6
date: 2026-04-15
plan: planning/plan_sc2egset_01_02_07.md
verdict: PROCEED (3 warnings to address before or during execution)
---

# Adversarial Review — plan_sc2egset_01_02_07.md

## Lens Assessments

- **Temporal discipline:** SOUND — Only pre-game features (MMR, selectedRace, highestLeague) used in Part B. Part A Spearman heatmap includes in-game features but annotates them with I3 classification and does not feed them into any predictive pipeline.
- **Statistical methodology:** SOUND — Spearman is appropriate for non-normal distributions documented in census. Hierarchical clustering for axis reordering is standard (Sokal & Michener 1958 UPGMA). No confirmatory claims; step is explicitly Tukey-style EDA.
- **Feature engineering:** N/A — Visualization only (I9).
- **Thesis defensibility:** ADEQUATE — PCA-skip justification is well-reasoned and documented with Jolliffe 2002 citation. MIN_LEAGUE_ROWS threshold and .df() convention issue weaken defensibility slightly.
- **Cross-game comparability:** N/A — SC2-only EDA step.

---

## Blockers

None.

---

## Warnings

### W-01 — `.df()` vs `.fetchdf()` convention inconsistency

**Location:** T03 cells — `conn.execute(sql_queries["spearman_all"]).df()`

**Issue:** The established convention in recent notebooks (01_02_05, 01_02_06) is `.fetchdf()`. Both methods produce identical results (verified against duckdb). Using `.df()` is a gratuitous convention break.

**Fix:** Change all `.df()` calls to `.fetchdf()` to match the convention in 01_02_05 and 01_02_06.

---

### W-02 — `MIN_LEAGUE_ROWS = 50` lacks a data-derived I7 justification

**Location:** T04, cell where `MIN_LEAGUE_ROWS = 50` is defined

**Issue:** The plan claims I7 justification ("minimum 50 rows for meaningful histogram density") but does not provide the derivation. This is a label, not a derivation, and contradicts I7's spirit.

**Fix:** Strengthen the comment with the actual derivation:
```python
# I7: histogram with bins=30 requires adequate density per bin.
# 50 rows / 30 bins ≈ 1.67 observations/bin — minimum for visual interpretability.
# Derivation: Cleveland (1993) recommends ~2 observations per bin minimum.
# 50 is conservative; census shows Unknown (32,338) and Master (6,458) far exceed this.
MIN_LEAGUE_ROWS = 50
```

---

### W-03 — No guard for zero surviving leagues

**Location:** T04, after `leagues_to_plot` is derived

**Issue:** If all leagues fall below `MIN_LEAGUE_ROWS` after the triple filter (MMR>0 AND standard races AND Win/Loss), `plt.subplots(0, 3)` will fail or produce degenerate output. The gate condition (`st_size > 0`) would pass for an empty figure, masking the failure.

**Fix:** Add an assertion before `plt.subplots`:
```python
assert n_leagues > 0, (
    f"No leagues with >= {MIN_LEAGUE_ROWS} rows after filtering "
    f"(MMR>0, standard races). Check census data."
)
```

In practice this is unlikely to trigger (census: Unknown=32,338, Master=6,458, Grandmaster=4,745 all far exceed threshold), but the plan should be robust by construction.

---

## Passed Checks

1. **Census key correctness:** All four key paths verified against actual census JSON:
   - `census["null_census"]["replay_players_raw"]["total_rows"]` ✓
   - `census["zero_counts"]["replay_players_raw"]["MMR_zero"]` ✓
   - `census["zero_counts"]["replay_players_raw"]["SQ_sentinel"]` ✓
   - `census["result_distribution"]` (list of dicts with "result" and "cnt" keys) ✓

2. **`compute_spearman_matrix` unpacking:** With scipy 1.17.1, `stats.spearmanr(matrix)` returns a `SignificanceResult` that supports tuple unpacking. `rho, _ = stats.spearmanr(...)` correctly assigns the (4,4) correlation matrix to `rho`. The `len(columns) == 2` scalar guard is correct. ✓

3. **`dendrogram["leaves"]` key:** Verified against scipy 1.17.1 — `dendrogram(..., no_plot=True)` returns a dict with key `"leaves"` (list of integer leaf indices). Correct; `"ivl"` contains string labels, not indices. ✓

4. **I3 compliance on faceted plot:** SQL selects only `MMR`, `selectedRace`, `highestLeague`, `result`. All are pre-game features. No in-game features (APM, SQ, supplyCappedPercent) used. ✓

5. **selectedRace filter:** `IN ('Prot', 'Zerg', 'Terr')` correctly matches the three major values (15,948 + 15,123 + 12,623 = 43,694 rows). Empty-string (1,110), Rand (10), and BW variants (3 total) correctly excluded. SQL comment documents exclusions. ✓

6. **DB_FILE import:** `from rts_predict.games.sc2.config import DB_FILE` resolves correctly to `src/rts_predict/games/sc2/config.py`. ✓

7. **I3 annotations on Spearman heatmap:** `COLUMN_CLASSIFICATION` dict correctly marks APM, SQ, supplyCappedPercent as "IN-GAME (Inv. #3)" and MMR as "PRE-GAME". `annotated_label()` function applies these to axis tick labels. ✓

8. **`result IN ('Win', 'Loss')` filter:** Consistent with 01_02_06; correctly excludes Undecided (24) and Tie (2) per census `result_distribution`. ✓

9. **PCA-skip justification:** Scientifically correct — p=1 PCA is trivially degenerate (Jolliffe 2002). Option 2 (in-game features in PCA) correctly rejected because APM-SQ correlation (~0.40 rho) would dominate PCs, obscuring pre-game structure. ✓

10. **No DDL, no DuckDB writes:** `read_only=True` throughout. No TEMP VIEWs, no INSERT/CREATE. ✓
