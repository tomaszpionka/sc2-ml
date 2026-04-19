# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     notebook_metadata_filter: kernelspec,jupytext
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
# ---

# %% [markdown]
# # 01_06_02 — Data Quality Report (aoe2companion)
#
# **Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
# **Hypothesis:** CONSORT flow balanced; 2.25% country NULL retained (MissingIndicator route, MAR);
#   358 duration clock-skew rows documented but retained; cleaning rules trace to 01_04.
# **Falsifier:** Any unexplained row delta; country NULL not documented.

# %%
import json, os

REPO_ROOT = os.environ.get("REPO_ROOT", "/Users/tomaszpionka/Projects/rts-outcome-prediction")
A = os.path.join(REPO_ROOT, "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning")
OUT_DIR = os.path.join(REPO_ROOT, "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates")

with open(os.path.join(A, "01_04_01_data_cleaning.json")) as f:
    c1 = json.load(f)
with open(os.path.join(A, "01_04_02_post_cleaning_validation.json")) as f:
    c2 = json.load(f)
with open(os.path.join(A, "01_04_03_minimal_history_view.json")) as f:
    c3 = json.load(f)
with open(os.path.join(A, "01_04_04_identity_resolution.json")) as f:
    c4 = json.load(f)

cf = c1["consort_flow"]
s0_rows = cf["S0_raw"]["n_rows"]
s0_matches = cf["S0_raw"]["n_matches"]
s1_rows = cf["S1_scope_restricted"]["n_rows"]
s1_matches = cf["S1_scope_restricted"]["n_matches"]
s2_rows = cf["S2_deduplicated"]["n_rows"]
s2_matches = cf["S2_deduplicated"]["n_matches"]
s3_rows = cf["S3_valid_complementary"]["n_rows"]
s3_matches = cf["S3_valid_complementary"]["n_matches"]

excl_01 = cf["excluded_S0_to_S1"]["n_rows"]
excl_12 = cf["excluded_S1_to_S2"]["n_rows"]
excl_23 = cf["excluded_S2_to_S3"]["n_rows"]

mhm_rows = c3["row_counts"]["total_rows"]
mhm_matches = c3["row_counts"]["distinct_match_ids"]
dur_non_positive = c3["duration_stats"]["non_positive_count"]
dur_outliers = c3["duration_stats"]["outlier_count_gt_86400"]

pha_rows = c2["consort_flow_matches"]["player_history_all"]["rows_after_01_04_02"]

id_total = c4["name_history_profile"]["total_profiles"]
rename_pct = c4["name_history_profile"]["pct_any_rename"]
collision_pct = c4["name_collision_profile"]["pct_collision"]

print(f"S0→S3: {s0_matches:,} → {s1_matches:,} → {s2_matches:,} → {s3_matches:,} matches")
print(f"MHM rows: {mhm_rows:,} ({mhm_matches:,} distinct matches)")
print(f"Duration non-positive: {dur_non_positive}, outliers >86400s: {dur_outliers}")
print(f"Identity: rename_pct={rename_pct}%, collision_pct={collision_pct}%")
assert s3_matches == 30_531_196, f"Expected 30,531,196 final matches, got {s3_matches}"
assert c2["all_assertions_pass"] is True
print("All assertions PASS")

# %%
md = f"""# Data Quality Report — aoe2companion

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
**Date:** 2026-04-19

## 1. CONSORT-Style Row Flow

| Stage | Description | Rows | Matches | Excluded Rows |
|---|---|---|---|---|
| S0 All rows | Raw `matches_raw` (all leaderboards) | {s0_rows:,} | {s0_matches:,} | — |
| S1 Scope-restricted | R01: `internalLeaderboardId IN (6, 18)` | {s1_rows:,} | {s1_matches:,} | {excl_01:,} |
| S2 Deduplicated | R02: dedup by (matchId, profileId); profileId=-1 excluded | {s2_rows:,} | {s2_matches:,} | {excl_12:,} |
| S3 Final `matches_1v1_clean` | R03: 2-row matches with complementary `won` | {s3_rows:,} | {s3_matches:,} | {excl_23:,} |
| `matches_history_minimal` | Canonical long-skeleton view (Phase-02-ready) | {mhm_rows:,} | {mhm_matches:,} | N/A |
| `player_history_all` | All leaderboards; no row filter | {pha_rows:,} | N/A | N/A |

**Key note:** 01_04_02 is a column-only cleaning step; row counts do not change between
S3 and the final validated views. All {s3_matches:,} matches are retained.

**Duration note:** {dur_non_positive} clock-skew rows (finished < started, i.e. `duration_seconds < 0`)
and {dur_outliers} outlier rows (duration > 86400s) are retained in `matches_1v1_clean` with
`is_duration_suspicious = TRUE` / `is_duration_negative = TRUE` flags respectively.
Duration is POST_GAME_HISTORICAL and does not affect the prediction label `won` (I3).

## 2. Cleaning Rule Registry

| Rule | Condition | Action | Impact |
|---|---|---|---|
| R01 | `internalLeaderboardId IN (6, 18)` (rm/ew scope) | Retain 1v1 ranked ladder only | {excl_01:,} rows excluded |
| R02 | Dedup (matchId, profileId) + profileId=-1 | Remove duplicates and invalid players | {excl_12:,} rows excluded |
| R03 | 2-row matches with complementary `won` | Remove non-complementary results | {excl_23:,} rows excluded |
| DS-AOEC-01 | server/scenario/modDataset/password: NULL >40% (MNAR/MAR) | DROP 4 columns | -4 cols matches_1v1_clean |
| DS-AOEC-02 | antiquityMode: NULL ~60% (schema-evolution) | DROP column | -1 col matches_1v1_clean |
| DS-AOEC-03b | mod/status: n_distinct=1 constants | DROP 2 columns | -2 cols matches_1v1_clean |
| DS-AOEC-04 | country: 2.25% NULL (MAR primary) | RETAIN + MissingIndicator flag | 0 rows excluded; flag added |
| DS-AOEC-05 | rating=0 for lb=6 (sentinel) | NULLIF + is_unrated_proxy flag | sentinel converted |
| DS-AOEC-06 | ratings_raw empty for lb=6 | OUT-OF-SCOPE (scope-boundary note) | registry only |
| duration | clock-skew (negative) / >86400s outliers | RETAIN with flags (REPORT-ONLY) | {dur_non_positive} + {dur_outliers} flagged |

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
| Total distinct profileIds (rm+ew scope) | {id_total:,} |
| Stable profiles (1 name ever) | {100-rename_pct:.2f}% |
| Any rename | {rename_pct:.2f}% |
| Name collision rate (same name, multiple profileIds) | {collision_pct:.2f}% |
| Identity branch | Branch (i) — API-namespace, rename-stable |
| Cross-dataset verdict | VERDICT A (0.9960 agreement with aoestats namespace bridge) |

Identity-rate reconciliation (2026-04-19): 2.57% rename / 3.55% collision — both below the
15% within-scope rigor threshold. `profileId` is the primary key for Phase 02 player features.

## 5. Post-Cleaning Summary

| View | Rows | Matches | Columns |
|---|---|---|---|
| `matches_1v1_clean` | {s3_rows:,} | {s3_matches:,} | 48 (after column drops/adds) |
| `player_history_all` | {pha_rows:,} | — | 19 |
| `matches_history_minimal` | {mhm_rows:,} | {mhm_matches:,} | 9 (Phase-02-ready) |

**Validation:** All 01_04_02 assertions passed (all_assertions_pass=True).
"""

out_path = os.path.join(OUT_DIR, "data_quality_report_aoe2companion.md")
with open(out_path, "w") as f:
    f.write(md)
print(f"Wrote {out_path}")
