# 01_02 EDA Pipeline Section — Finalization Roadmap
# Working document. Not a formal artifact.
# date: 2026-04-15

## Context

All three ROADMAPs (aoe2companion, aoestats, sc2egset) define 01_02 as ending at
01_02_05 (univariate visualizations). Per Manual §2, 01_02 must cover all three
EDA layers: univariate → bivariate → multivariate. Layers 2 and 3 are absent from
every ROADMAP. This document tracks the plan to close that gap.

---

## Revised 01_02 Step Inventory (all three datasets)

| Step     | Name                          | Status (all datasets)           | Action                                  |
|----------|-------------------------------|---------------------------------|-----------------------------------------|
| 01_02_01 | DuckDB Pre-Ingestion          | complete ✓                      | —                                       |
| 01_02_02 | DuckDB Ingestion              | complete ✓                      | —                                       |
| 01_02_03 | Raw Schema DESCRIBE           | complete ✓                      | —                                       |
| 01_02_04 | Univariate Census             | complete ✓                      | —                                       |
| 01_02_05 | Univariate Visualizations     | not_started → plan update + run | Add 1 new plot per dataset (see below)  |
| 01_02_06 | Bivariate EDA                 | not in ROADMAP                  | Plan → adversarial review → execute     |
| 01_02_07 | Multivariate EDA              | not in ROADMAP                  | Plan → adversarial review → execute     |

---

## 01_02_05 — Plan Updates (per dataset)

### aoe2companion — add `01_02_05_rating_null_timeline.png`

**Scientific question:** Is the 86% NULL rate for `rating` and `ratingDiff` explained
by a discrete schema change at a temporal boundary, or is missingness gradual?

- SQL: monthly NULL rate for `rating` and `ratingDiff` in `matches_raw`
- Temporal column: derive month from match timestamp column
- Expected pattern: step function (low NULL before cutoff, high NULL after, or vice versa)
- I7: no magic numbers — derive min/max months from `temporal_range` in census artifact
- New plan total: 17 plots

### aoestats — add `01_02_05_schema_change_boundary.png`

**Scientific question:** Do the ~86%-NULL columns (openClose, fullTechTree, etc.)
share a common temporal activation boundary, suggesting a schema change?

- SQL: monthly NULL rate for all ~86%-NULL columns derived from filename-based date
  (STRFTIME on filename parsed date — no JOIN to other tables needed)
- I7: column list and NULL rates derived from census `null_census` section at runtime
- New plan total: 15 plots

### sc2egset — add `01_02_05_player_repeat_frequency.png`

**Scientific question:** How often do the same players appear across replays?
Is there a player-overlap data leakage risk for a train/val split by replay ID?

- SQL: SELECT games_per_player, COUNT(*) FROM
  (SELECT toon_id, COUNT(*) as games_per_player FROM replay_players_raw GROUP BY toon_id)
  GROUP BY games_per_player ORDER BY games_per_player
- Expected output: heavily right-skewed (most players appear 1–2 times;
  a few tournament regulars appear many times)
- I7: derive total unique players and total rows from census artifact at runtime
- New plan total: 14 plots

---

## 01_02_06 — Bivariate EDA (new step, all datasets)

One step per dataset. Core deliverables:

**All datasets:**
- Conditional violin/box plots: every numeric feature split by win/loss outcome
- Spearman correlation matrix for all numeric columns (heatmap, cluster-ordered)

**Dataset-specific key questions:**

| Dataset       | Priority bivariate question                                           |
|---------------|-----------------------------------------------------------------------|
| aoe2companion | ratingDiff × won — is it outcome-derived? (I3 decision-making)        |
|               | rating × won — does rating predict outcome as expected baseline?       |
| aoestats      | match_rating_diff × (new_rating − old_rating) scatter — leakage audit |
|               | old_rating × winner — pre-game predictor baseline                     |
| sc2egset      | MMR (non-zero) × result — does tournament MMR predict result?          |
|               | selectedRace × result — racial balance check                          |
|               | APM/SQ × result for in-game reference (I3-annotated, NOT features)    |

---

## 01_02_07 — Multivariate EDA (new step, all datasets)

One step per dataset. Core deliverables:

1. **Numeric correlation heatmap** — Spearman, cluster-ordered, all numeric columns.
   Labels include I3 classification (in-game/post-game annotations on axis tick labels).
2. **PCA scree + biplot** — pre-game numeric features only (no I3 columns).
   Variance concentration and feature clustering for Phase 02 planning.
   For large tables (aoestats 30M+ rows, aoe2companion): sample-based or DuckDB
   `TABLESAMPLE` — not full-table PCA.

---

## ROADMAP update required

Steps 01_02_06 and 01_02_07 must be added to all three dataset ROADMAPs before
planning begins. This is a Category C chore bundled with the 01_02_06 planning PR.

---

## Sequencing

1. ✅ (now) Update 01_02_05 plans with 3 additional univariate plots, one per dataset
2. □ Execute 01_02_05 for all three datasets (single executor session, parallel)
3. □ Plan 01_02_06 bivariate (planner-science, one agent per dataset or single multi-dataset plan)
   → adversarial review → execute
4. □ Plan 01_02_07 multivariate (same workflow)
5. □ 01_02 complete → begin 01_03 Systematic Data Profiling

---

## Notes

- match_rating_diff leakage scatter (aoestats) is BIVARIATE → belongs in 01_02_06, not 01_02_05
- Duration clip: aoe2companion p95=63.15 min, aoestats p95=78.6 min — both use p95-derived
  clipping; difference reflects genuine game-length distribution divergence
- All in-game column plots (APM, SQ, supplyCappedPercent, elapsed_game_loops for sc2egset)
  carry mandatory Inv. #3 annotation regardless of which step they appear in
