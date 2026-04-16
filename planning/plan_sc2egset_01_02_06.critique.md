---
reviewer: reviewer-adversarial
plan: planning/plan_sc2egset_01_02_06.md
date: 2026-04-15
verdict: APPROVE WITH CONDITIONS
blocking_count: 1
warning_count: 6
---

# Adversarial Review — sc2egset 01_02_06 Plan

## Lens Assessments

- **Temporal discipline:** SOUND — all in-game columns (APM, SQ, supplyCappedPercent) carry mandatory red-bbox annotation on every plot. `result` used exclusively as grouping variable. `elapsed_game_loops` absence from bivariate analysis is acceptable (in replays_meta_raw, not replay_players_raw) but should be noted in Out of Scope.
- **Statistical methodology:** AT RISK — 4 Mann-Whitney U + 2 chi-square tests with no effect sizes (W1) and no multiple comparison correction rationale (W2). Spearman matrix corrupted by 83.65% MMR=0 sentinel rows (B1).
- **Cross-game comparability:** MAINTAINED — comparability checklist present at plan lines 1258-1271.

## JSON Key Path Verification (all confirmed correct)

| Plan reference | Actual key | Correct? |
|---|---|---|
| `census["result_distribution"]` | Present, dicts with `result`, `cnt`, `pct` | YES |
| `census["zero_counts"]["replay_players_raw"]["MMR_zero"]` | Present, value=37489 | YES |
| `census["zero_counts"]["replay_players_raw"]["SQ_sentinel"]` | Present, value=2 | YES |
| `census["mmr_zero_interpretation"]` | Present | YES |
| `census["isInClan_distribution"]` | Present, False=33210, True=11607 | YES |
| `census["field_classification"]` | APM/SQ/supplyCappedPercent confirmed as `in_game` | YES |

Result values in census: `'Win'`, `'Loss'`, `'Undecided'`, `'Tie'` — matches plan filter.
Column name: `MMR` (not `mmr`) confirmed from schema YAML.

## BLOCKER B1 — Spearman matrix includes 83.65% MMR=0 sentinel rows

**Location:** T11 SQL query `spearman_data`.
**Finding:** Query filters SQ sentinels (`AND SQ > {INT32_MIN}`) but does NOT filter MMR=0. With 37,489/44,817 rows having MMR=0, the Spearman correlation between MMR and every other variable is dominated by a massive point mass at zero. This will show MMR as near-uncorrelated with result — directly contradicting T03's violin which (correctly) filters to MMR > 0 and shows a clear Win/Loss difference.
**Examiner question:** "Your violin shows MMR differs by result, but your Spearman heatmap shows MMR-result rho ≈ 0. Which is wrong?"
**Required fix:** Either (a) exclude MMR=0 rows from Spearman matrix (consistent with T03), or (b) compute two matrices (all rows / MMR>0 only) and present both, or (c) add a prominent annotation that MMR correlation is deflated by the zero-sentinel population.

## WARNING W1 — No effect sizes for Mann-Whitney U tests

**Location:** T03, T05, T06, T07.
**Finding:** Reports U statistic and p-value only. With N=44,791 (Win/Loss), virtually any non-zero difference produces p < 0.05. Rank-biserial r = 1 - 2U/(n1*n2) is trivially derivable from the existing U statistic.
**Required fix:** Add `r_rb = 1 - 2 * U_stat / (n_win * n_loss)` to each test result dict and annotate on plot.

## WARNING W2 — No multiple comparison correction or exploratory rationale

**Location:** Plan-wide (6 tests total).
**Finding:** Six hypothesis tests with no mention of Bonferroni/Holm/BH correction, and no statement that these are exploratory Tukey-style tests (not confirmatory).
**Required fix:** Add one sentence in T02 setup or T12 markdown: "All statistical tests are exploratory per Tukey-style EDA framing; p-values are descriptive, not confirmatory."

## WARNING W3 — Q4 says `selectedRace` but implementation uses `race`

**Location:** Q4 definition vs T04 code.
**Finding:** Q4 titled "Does selectedRace affect win rate?" but SQL filters `race IN ('Prot', 'Zerg', 'Terr')` — the post-random-resolution column.
**Required fix:** Rename Q4 to "Does race (post-random-resolution) affect win rate?" or split Q4/Q10.

## WARNING W4 — Chi-square expected-cell-count assumption cited but not verified in code

**Location:** T04, T09.
**Finding:** Plan cites Agresti (2002): expected counts > 5. `chi2_contingency` returns expected frequencies but they are never checked or logged.
**Required fix:** Add `assert np.all(expected > 5), f"Chi-square assumption violated: min expected = {expected.min():.2f}"`.

## WARNING W5 — INT32_MIN should use `np.iinfo(np.int32).min` not literal

**Location:** T02 line: `INT32_MIN = -2_147_483_648`.
**Finding:** Minor I7 hygiene issue — a mistyped digit silently produces wrong filter.
**Required fix:** `INT32_MIN = int(np.iinfo(np.int32).min)`.

## WARNING W6 — Multi-panel violin T10 inconsistent MMR treatment

**Location:** T10 vs T03 vs T11.
**Finding:** T03 correctly excludes MMR=0. T10 includes all MMR rows (labeled "MMR (all, incl. zeros)"). T11 also includes MMR=0 (B1 above). Two plots with zero-contaminated MMR plus one clean view creates a confusing picture for the thesis.
**Recommended fix:** Align T10 MMR panel to use MMR>0 only (consistent with T03).

## Summary Table

| ID | Severity | Task | Finding |
|----|----------|------|---------|
| B1 | BLOCKER | T11 | Spearman matrix includes 83.65% MMR=0 sentinel — corrupts correlation values |
| W1 | WARNING | T03/T05/T06/T07 | No effect sizes for Mann-Whitney U tests |
| W2 | WARNING | Plan-wide | No multiple comparison correction or exploratory rationale stated |
| W3 | WARNING | Q4/T04 | Q4 says `selectedRace` but code uses `race` |
| W4 | WARNING | T04/T09 | Chi-square expected-count assumption not verified in code |
| W5 | WARNING | T02 | INT32_MIN as literal instead of `np.iinfo(np.int32).min` |
| W6 | WARNING | T10 | MMR treatment inconsistent with T03 in multi-panel violin |

## VERDICT: APPROVE WITH CONDITIONS

Single blocker (B1) must be resolved. It is a one-line SQL fix (add `AND MMR > 0` or compute two matrices). W1 through W6 are strongly recommended before execution.
