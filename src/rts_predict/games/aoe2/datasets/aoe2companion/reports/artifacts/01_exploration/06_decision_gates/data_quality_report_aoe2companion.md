# Data Quality Report — aoe2companion

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
**Date:** 2026-04-19

## 1. CONSORT-Style Row Flow

| Stage | Description | Rows | Matches | Excluded Rows |
|---|---|---|---|---|
| S0 All rows | Raw `matches_raw` (all leaderboards) | 277,099,059 | 74,788,989 | — |
| S1 Scope-restricted | R01: `internalLeaderboardId IN (6, 18)` | 61,071,799 | 30,536,248 | 216,027,260 |
| S2 Deduplicated | R02: dedup by (matchId, profileId); profileId=-1 excluded | 61,071,794 | 30,536,248 | 5 |
| S3 Final `matches_1v1_clean` | R03: 2-row matches with complementary `won` | 61,062,392 | 30,531,196 | 9,402 |
| `matches_history_minimal` | Canonical long-skeleton view (Phase-02-ready) | 61,062,392 | 30,531,196 | N/A |
| `player_history_all` | All leaderboards; no row filter | 264,132,745 | N/A | N/A |

**Key note:** 01_04_02 is a column-only cleaning step; row counts do not change between
S3 and the final validated views. All 30,531,196 matches are retained.

**Duration note:** 358 clock-skew rows (finished < started, i.e. `duration_seconds < 0`)
and 142 outlier rows (duration > 86400s) are retained in `matches_1v1_clean` with
`is_duration_suspicious = TRUE` / `is_duration_negative = TRUE` flags respectively.
Duration is POST_GAME_HISTORICAL and does not affect the prediction label `won` (I3).

## 2. Cleaning Rule Registry

| Rule | Condition | Action | Impact |
|---|---|---|---|
| R01 | `internalLeaderboardId IN (6, 18)` (rm/ew scope) | Retain 1v1 ranked ladder only | 216,027,260 rows excluded |
| R02 | Dedup (matchId, profileId) + profileId=-1 | Remove duplicates and invalid players | 5 rows excluded |
| R03 | 2-row matches with complementary `won` | Remove non-complementary results | 9,402 rows excluded |
| DS-AOEC-01 | server/scenario/modDataset/password: NULL >40% (MNAR/MAR) | DROP 4 columns | -4 cols matches_1v1_clean |
| DS-AOEC-02 | antiquityMode: NULL ~60% (schema-evolution) | DROP column | -1 col matches_1v1_clean |
| DS-AOEC-03b | mod/status: n_distinct=1 constants | DROP 2 columns | -2 cols matches_1v1_clean |
| DS-AOEC-04 | country: 2.25% NULL (MAR primary) | RETAIN + MissingIndicator flag | 0 rows excluded; flag added |
| DS-AOEC-05 | rating=0 for lb=6 (sentinel) | NULLIF + is_unrated_proxy flag | sentinel converted |
| DS-AOEC-06 | ratings_raw empty for lb=6 | OUT-OF-SCOPE (scope-boundary note) | registry only |
| duration | clock-skew (negative) / >86400s outliers | RETAIN with flags (REPORT-ONLY) | 358 + 142 flagged |

## 3. Route-Decision Table

| Column | NULL% | Mechanism | Route | Rule |
|---|---|---|---|---|
| `country` | ~2.25% | MAR (primary) / MNAR (sensitivity) | RETAIN + MissingIndicator | DS-AOEC-04 |
| `server` | ~97.4% | MNAR | DROP | DS-AOEC-01 |
| `scenario` | 100% | MAR | DROP | DS-AOEC-01 |
| `modDataset` | 100% | MAR | DROP | DS-AOEC-01 |
| `password` | ~77.6% | MAR | DROP | DS-AOEC-01 |
| `antiquityMode` | ~60.1% | Schema-evolution (MAR) | DROP | DS-AOEC-02 |
| `mod` | 0% | Constant (FALSE) | DROP | DS-AOEC-03b |
| `status` | 0% | Constant ('player') | DROP | DS-AOEC-03b |
| `rating` | ~0% (sentinel) | Sentinel=0 for lb=6 | NULLIF + flag | DS-AOEC-05 |

## 4. Identity Quality Summary

| Metric | Value |
|---|---|
| Total distinct profileIds (rm+ew scope) | 683,790 |
| Stable profiles (1 name ever) | 97.43% |
| Any rename | 2.57% |
| Name collision rate (same name, multiple profileIds) | 3.55% |
| Identity branch | Branch (i) — API-namespace, rename-stable |
| Cross-dataset verdict | VERDICT A (0.9960 agreement with aoestats namespace bridge) |

Identity-rate reconciliation (2026-04-19): 2.57% rename / 3.55% collision — both below the
15% within-scope rigor threshold. `profileId` is the primary key for Phase 02 player features.

## 5. Post-Cleaning Summary

| View | Rows | Matches | Columns |
|---|---|---|---|
| `matches_1v1_clean` | 61,062,392 | 30,531,196 | 48 (after column drops/adds) |
| `player_history_all` | 264,132,745 | — | 19 |
| `matches_history_minimal` | 61,062,392 | 30,531,196 | 9 (Phase-02-ready) |

**Validation:** All 01_04_02 assertions passed (all_assertions_pass=True).
