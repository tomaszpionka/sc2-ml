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
# # 01_06_02 — Data Quality Report (sc2egset)
#
# **Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
# **Hypothesis:** CONSORT flow accounts for every dropped row with a named cleaning rule.
# **Falsifier:** Any unexplained row delta; any rule not traceable to 01_04 artifacts.

# %%
import json
import os

REPO_ROOT = os.environ.get("REPO_ROOT", "/Users/tomaszpionka/Projects/rts-outcome-prediction")
ARTIFACTS_BASE = os.path.join(REPO_ROOT, "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration")
OUT_DIR = os.path.join(REPO_ROOT, "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates")

# Load 01_04_01 cleaning plan
with open(os.path.join(ARTIFACTS_BASE, "04_cleaning", "01_04_01_data_cleaning.json")) as f:
    clean01 = json.load(f)
with open(os.path.join(ARTIFACTS_BASE, "04_cleaning", "01_04_02_post_cleaning_validation.json")) as f:
    clean02 = json.load(f)

consort = clean01["consort_flow"]
registry = clean01.get("cleaning_registry", []) + clean02.get("cleaning_registry", [])
print(f"Cleaning rules total: {len(registry)}")
print(f"CONSORT stages: {list(consort.keys())}")

# %%
# CONSORT flow verification
raw_rows = consort["raw_player_rows"]          # 44817
r01_excluded = consort["r01_excluded_rows"]    # 85
r03_excluded = consort["r03_excluded_rows"]    # 314
clean_rows = consort["clean_rows"]             # 44418

# matches_flat_clean is match-grain (2 player rows per replay)
# player_history_all is also 2 rows per match
raw_replays = consort["raw_replays"]           # 22390
clean_replays = consort["clean_replays"]       # 22209

expected_clean = raw_rows - r01_excluded - r03_excluded
assert expected_clean == clean_rows, f"CONSORT imbalance: {raw_rows} - {r01_excluded} - {r03_excluded} != {clean_rows}"
print(f"CONSORT balanced: {raw_rows} - {r01_excluded} (R01) - {r03_excluded} (R03) = {clean_rows}")
print(f"Match level: {raw_replays} raw → {clean_replays} clean (dropped: {raw_replays - clean_replays})")

# %%
# Generate the data quality report MD
md = f"""# Data Quality Report — sc2egset

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0 (CROSS-01-06-v1)
**Produced by:** 01_06_02 (Phase 01 Decision Gates)
**Date:** 2026-04-19
**Source artifacts:** 01_04_01_data_cleaning.json, 01_04_02_post_cleaning_validation.json

---

## 1. CONSORT-Style Row Flow

| Stage | Description | Rows (player-grain) | Replays | Excluded |
|---|---|---|---|---|
| S0 Raw | All `.SC2Replay.json` files ingested | {raw_rows:,} | {raw_replays:,} | — |
| S1 After R01 | Non-2-player replays removed (R01: `player_count != 2`) | {raw_rows - r01_excluded:,} | {raw_replays - consort['r01_excluded_replays']:,} | {r01_excluded} rows / {consort['r01_excluded_replays']} replays |
| S2 After R03 | Mixed-result replays removed (R03: Undecided/Tie excluded) | {clean_rows:,} | {clean_replays:,} | {r03_excluded} rows / {consort['r03_excluded_replays']} replays |
| Final `matches_flat_clean` | After column-only cleaning (01_04_02) | {clean_rows:,} | {clean_replays:,} | column changes only |

**`player_history_all`:** {raw_rows:,} rows (includes Undecided/Tie matches; not row-filtered).

**CONSORT balance check:** {raw_rows:,} - {r01_excluded} - {r03_excluded} = {clean_rows:,} ✓

---

## 2. Cleaning Rule Registry

All rules traceable to `01_04_01_data_cleaning.json` and `01_04_02_post_cleaning_validation.json`.

| Rule ID | Condition | Action | Impact |
|---|---|---|---|
| R01 | player_count != 2 | Remove replay | {consort['r01_excluded_replays']} replays / {r01_excluded} rows |
| R03 | result NOT IN ('Win','Loss') | Remove replay (Undecided/Tie) | {consort['r03_excluded_replays']} replays / {r03_excluded} rows |
"""

for rule in registry[:12]:
    md += f"| {rule.get('rule_id','?')} | {rule.get('condition','?')[:60]} | {rule.get('action','?')[:60]} | {str(rule.get('impact','?'))[:80]} |\n"

md += f"""
---

## 3. Route-Decision Table (NULL/Missing ≥1%)

| Column | NULL% | Mechanism | Route | Rule |
|---|---|---|---|---|
| `mmr` | 83.95% | MNAR (professional not rated) | DROP + add `is_mmr_missing` flag | DS-SC2-01 (01_04_02) |
| `highestLeague` | 72.04% | MAR | DROP (non-primary feature) | DS-SC2-02 (01_04_02) |
| `clanTag` | 73.93% | MAR | DROP (`isInClan` retained) | DS-SC2-03 (01_04_02) |
| `APM` (= 0 sentinel) | 2.53% | MNAR (parse failure) | NULLIF + `is_apm_unparseable` flag | DS-SC2-10 (01_04_02) |
| `gd_mapSizeX/Y` | variable | parse artifacts | NULL-correct + drop from matches_flat_clean | DS-SC2-06 |
| `handicap` | near-constant | 2/44k anomalies | DROP | DS-SC2-09 |

---

## 4. Post-Cleaning Summary

| View | Rows | Replays | Columns |
|---|---|---|---|
| `matches_flat_clean` | {clean_rows:,} | {clean_replays:,} | 30 (after drops/adds from 01_04_02) |
| `player_history_all` | {raw_rows:,} | {raw_replays:,} | 37 (includes IN_GAME_HISTORICAL cols) |
| `matches_history_minimal` | {clean_rows:,} | {clean_replays:,} | 9 (Phase-02-ready cross-dataset view) |

**Validation assertions (from 01_04_02_post_cleaning_validation.json):**
- Column-only cleaning step for 01_04_02: row counts unchanged from S2.
- R01 and R03 row drops verified against raw replay counts.
- All 12 constant `go_*` columns dropped (DS-SC2-08).
- APM sentinel → NULL applied to 1,132 rows in player_history_all.
"""

out_path = os.path.join(OUT_DIR, "data_quality_report_sc2egset.md")
with open(out_path, "w") as f:
    f.write(md)
print(f"Wrote {out_path}")
print("CONSORT gate: PASS")
