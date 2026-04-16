---
reviewer: reviewer-adversarial
plan: planning/plan_aoestats_01_02_06.md
date: 2026-04-15
verdict: APPROVE WITH CONDITIONS
blocking_count: 2
warning_count: 6
---

# Adversarial Review — aoestats 01_02_06 Plan

## Lens Assessments

- **Temporal discipline:** SOUND — duration annotated POST-GAME, opening/age uptimes IN-GAME, match_rating_diff leakage resolved empirically. new_rating included in Spearman matrix with annotation.
- **Statistical methodology:** AT RISK — leakage scatter uses Pearson r (correct and labeled). Spearman heatmap uses pandas `.corr(method="spearman")` (correct). Opening win rate bar lacks confidence intervals (W5).
- **Cross-game comparability:** MAINTAINED — cross-dataset comparability checklist at plan lines 1656-1666.

## Key discovery from planner

`match_rating_diff` is in `players_raw` (NOT matches_raw), alongside `old_rating` and `new_rating`. The leakage scatter is a within-table query on players_raw — no JOIN needed. This simplifies the analysis significantly.

## BLOCKER B1 — read_only connection contradicts CREATE TEMP VIEW

**Location:** T02 connection setup vs Performance Notes.
**Finding:** T02 opens DuckDB with `read_only=True` (correct per Invariant #9). The Performance Notes section instructs adding `CREATE OR REPLACE TEMP VIEW match_winner` in T02. DuckDB does not allow CREATE statements on read-only connections — runtime error.
**Required fix:** Either (a) remove the temp view recommendation and accept repeated CTE computation, or (b) change to `read_only=False` with documented justification that temp views are ephemeral and don't violate I9, or (c) verify DuckDB allows temp views on read-only connections with temp_directory configured. Pick one approach unambiguously.

## BLOCKER B2 — JSON artifact key name inconsistency

**Location:** ROADMAP gate condition (line 195), T11 verification (line 1628), gate checklist (line 1696), actual T03 code (line 421).
**Finding:** ROADMAP gate and T11 verification reference flat key `match_rating_diff_leakage_status`. Gate checklist correctly references nested path `match_rating_diff_leakage.leakage_status`. Actual code writes nested: `bivariate_results["match_rating_diff_leakage"]["leakage_status"]`. The flat key does not exist in the written JSON.
**Required fix:** Harmonize ROADMAP gate condition and T11 verification to use `bivariate_results["match_rating_diff_leakage"]["leakage_status"]`.

## WARNING W1 — Leakage decision thresholds need I7 justification

**Location:** T03 decision logic.
**Finding:** Thresholds `pearson_r > 0.99`, `exact_match_pct > 99.0`, `slope within 0.05 of 1.0`, `pearson_r < 0.3` are reasonable but undocumented. I7 requires justification.
**Required fix:** Add inline comment: "0.99 = practical certainty for N > 100M; 0.3 = conventional weak-correlation boundary per Cohen 1988."

## WARNING W2 — Spearman matrix includes post-game columns without per-cell annotation

**Location:** T10 heatmap.
**Finding:** `new_rating` and `match_rating_diff` are included in the Spearman matrix with only a plot-level annotation "Mixed — includes post-game columns." Individual cells involving post-game columns are not visually distinguished.
**Recommended fix:** Add asterisk or different border to post-game column tick labels in the heatmap.

## WARNING W3 — Sentinel filter inconsistency for old_rating vs team ELO

**Location:** T03, T04, T07, T10 WHERE clauses.
**Finding:** Team ELO sentinel is −1.0 (confirmed in census `elo_negative_distinct_values`). But `old_rating > 0` and `new_rating > 0` treat zero as sentinel despite census showing `old_rating min_val=0.0` with no negative sentinel documented. Zero may be a legitimate starting rating for new players.
**Required fix:** Add I7 comment documenting the assumption that zero = unrated sentinel (not a legitimate rating), grounded in domain knowledge.

## WARNING W4 — Plot visual subsample size 20,000 lacks I7 justification

**Location:** Leakage scatter plot code.
**Finding:** `plot_sample_size = min(20000, len(df_scatter))` — 20,000 is not derived from census.
**Required fix:** Add comment: "20K points is a common scatter plot ceiling for matplotlib rasterized rendering (Cleveland 1993)."

## WARNING W5 — Opening win rate bar lacks confidence intervals

**Location:** T08 opening win rate plot.
**Finding:** N per opening ranges from hundreds to 4.2M. A 51.2% win rate is highly significant at N=4.2M but not at N=500. Plot shows N per bar (good) but no confidence intervals or significance markers.
**Recommended fix:** Add 95% CI bars: `ci = 1.96 * np.sqrt(wr * (1-wr) / n)`.

## WARNING W6 — match_winner CTE drops edge-case game_ids where winner=NULL

**Location:** T05, T06, T07 match_winner CTE.
**Finding:** Census shows 5,210 surplus false winner rows over true winner rows. Some game_ids may have no winner=true player, producing NULL winning_team which silently drops from downstream plots.
**Required fix:** Add assertion after match_winner query verifying no NULL winning_team rows, or log the count of dropped game_ids.

## Summary Table

| ID | Severity | Task | Finding |
|----|----------|------|---------|
| B1 | BLOCKER | T02 | read_only=True contradicts CREATE TEMP VIEW — runtime error |
| B2 | BLOCKER | T03/T11/gate | JSON key path flat vs nested inconsistency across gate/verification/code |
| W1 | WARNING | T03 | Leakage decision thresholds lack I7 documentation |
| W2 | WARNING | T10 | Spearman matrix includes post-game columns without per-cell annotation |
| W3 | WARNING | T03/T04/T07/T10 | old_rating > 0 sentinel assumption undocumented vs team ELO −1.0 sentinel |
| W4 | WARNING | T03 scatter | plot_sample_size=20000 not I7-justified |
| W5 | WARNING | T08 | Opening win rate bar lacks confidence intervals |
| W6 | WARNING | T05/T06/T07 | match_winner CTE silently drops NULL-winner game_ids |

## VERDICT: APPROVE WITH CONDITIONS

Fix B1 (resolve read_only vs TEMP VIEW) and B2 (harmonize JSON key path) before execution. W1–W6 are strongly recommended.
