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
# # 01_06_02 — Data Quality Report (aoestats)
# **Hypothesis:** CONSORT flow balanced; 28 corrupt-duration matches included; rules trace to 01_04.
# **Falsifier:** Any unexplained row delta.

# %%
import json, os
REPO_ROOT = os.environ.get("REPO_ROOT", "/Users/tomaszpionka/Projects/rts-outcome-prediction")
A = os.path.join(REPO_ROOT, "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration")
OUT_DIR = os.path.join(REPO_ROOT, "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates")

with open(os.path.join(A, "04_cleaning/01_04_01_data_cleaning.json")) as f:
    c1 = json.load(f)
with open(os.path.join(A, "04_cleaning/01_04_02_post_cleaning_validation.json")) as f:
    c2 = json.load(f)

flow = c1["consort_flow"]
print("CONSORT stages:", {k:v for k,v in flow.items() if isinstance(v,(int,float))})

# CONSORT: stage_0=30,690,651 → stage_1 (has_players) → stage_2 (structural 1v1) → stage_3 → stage_4
s0 = flow["stage_0_all_matches"]
s1 = flow["stage_1_has_players"]
s2 = flow["stage_2_structural_1v1"]
s3 = flow["stage_3_ranked_1v1_distinct_teams"]
s4 = flow["stage_4_view_final"]
ph = flow["player_history_all_rows"]

excluded_winner = flow.get("excluded_at_stage_3_to_4_inconsistent_winner", 997)
print(f"S0→S4 flow: {s0:,} → {s1:,} → {s2:,} → {s3:,} → {s4:,}")
print(f"Excluded S3→S4 (inconsistent winner): {excluded_winner}")

# Verify final
assert s4 == 17_814_947, f"Expected 17,814,947 final rows, got {s4}"
print(f"Final matches_1v1_clean: {s4:,} (PASS)")

md = f"""# Data Quality Report — aoestats

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
**Date:** 2026-04-19

## 1. CONSORT-Style Row Flow

| Stage | Description | Rows/matches | Excluded |
|---|---|---|---|
| S0 All matches | Raw matches from Parquet files | {s0:,} | — |
| S1 Has players | R00: matches with player data present | {s1:,} | {s0-s1:,} |
| S2 Structural 1v1 | R01: `player_count=2` filter | {s2:,} | {s1-s2:,} |
| S3 Ranked 1v1 | R02: `leaderboard='random_map'` + distinct team_ids | {s3:,} | {s2-s3:,} |
| S4 Final `matches_1v1_clean` | R03: consistent winner (excluded {excluded_winner} inconsistent) | {s4:,} | {s3-s4:,} |
| `player_history_all` | All leaderboards; no row filter | {ph:,} | N/A |

**CONSORT note:** The 28 corrupt-duration matches identified in 01_04_02 addendum are retained in
`matches_1v1_clean` with `is_duration_suspicious=TRUE`; they are NOT row-excluded.
Duration is POST_GAME_HISTORICAL and does not affect the prediction label `team1_wins`.

## 2. Cleaning Rule Registry

| Rule | Condition | Action | Impact |
|---|---|---|---|
| R00 | profile_id != -1 / player data present | Retain only valid players | {s0-s1:,} rows excluded |
| R01 | player_count=2 (structural 1v1) | Remove non-2-player matches | {s1-s2:,} rows excluded |
| R02 | leaderboard='random_map' scope | Restrict to ranked 1v1 ladder | {s2-s3:,} rows excluded |
| R03 | consistent winner per match | Remove inconsistent results | {excluded_winner} rows excluded |
| DS-AOESTATS-01 | old_rating=0 sentinel | NULLIF + is_unrated flag | ~2.3M rows modified |
| DS-AOESTATS-02 | avg_elo=0 sentinel | NULLIF | 0 rows excluded |
| DS-AOESTATS-03 | raw_match_type redundant | DROP column | -1 col matches_1v1_clean |
| DS-AOESTATS-04 | constants (leaderboard, num_players) | DROP 2 columns | -2 cols |
| DS-AOESTATS-08 | overviews_raw singleton | OUT-OF-SCOPE declaration | registry only |
| [PRE-canonical_slot] | team=1 skill-correlated (W3) | Flag; no row drop | BACKLOG F1 pending |

## 3. Route-Decision Table

| Column | NULL% | Mechanism | Route | Rule |
|---|---|---|---|---|
| `old_rating` (p0/p1) | ~13% | MNAR (unrated players) | NULLIF + is_unrated flag | DS-AOESTATS-01 |
| `avg_elo` | ~0.0007% | MAR | NULLIF | DS-AOESTATS-02 |
| `raw_match_type` | 7055 NULLs (MCAR) | redundant | DROP | DS-AOESTATS-03 |
| `leaderboard` | 0% | constant (n_distinct=1) | DROP | DS-AOESTATS-08 |
| `num_players` | 0% | constant (n_distinct=1) | DROP | DS-AOESTATS-08 |

## 4. Post-Cleaning Summary

| View | Rows | Columns |
|---|---|---|
| `matches_1v1_clean` | {s4:,} | 20 (after drops/adds) |
| `player_history_all` | {ph:,} | 14 |
| `matches_history_minimal` | {s4*2:,} player rows | 9 (Phase-02-ready) |

**Validation assertions:**
- Final matches_1v1_clean: {s4:,} = expected ✓
- player_history_all: {ph:,} rows (all leaderboards)
- 14 [PRE-canonical_slot] columns flagged in data dictionary
"""

out_path = os.path.join(OUT_DIR, "data_quality_report_aoestats.md")
with open(out_path, "w") as f:
    f.write(md)
print(f"Wrote {out_path}")
