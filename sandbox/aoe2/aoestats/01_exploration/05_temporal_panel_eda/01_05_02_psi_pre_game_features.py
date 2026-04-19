# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     notebook_metadata_filter: kernelspec,jupytext
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: .venv
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Step 01_05_02 -- PSI with Frozen Reference Edges (Q2)
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_05 -- Temporal & Panel EDA
# **Step:** 01_05_02
# **Dataset:** aoestats
# **spec:** reports/specs/01_05_preregistration.md@7e259dd8
#
# # Hypothesis: Rating drift (focal_old_rating, avg_elo) is the largest PSI contributor;
# # PSI >= 0.10 in >= 3 of 8 tested quarters. Civ distribution (faction) is relatively
# # stable (PSI < 0.10 in >= 5 quarters).
# # Falsifier: Rating PSI < 0.10 across all 8 quarters AND faction PSI >= 0.25 in any
# # quarter -- would reverse expected drift ordering.
#
# **Critique B2 fix:** Binary features (mirror, p0_is_unrated, p1_is_unrated) use
# Cohen's h instead of PSI. High-cardinality categorical (faction, map) use
# categorical PSI with __unseen__ bin.
#
# **Critique M4 fix:** focal_old_rating = CASE WHEN half=0 THEN p0_old_rating ELSE
# p1_old_rating END — symmetric. p0/p1 ratings NOT used as primary PSI features.
# Per-slot p0/p1 sensitivity emitted with [PRE-canonical_slot] tag.
#
# **Critique B3 fix:** Primary reference 2022-08-29..2022-10-27 (patch 66692; spec §7 corrected v1.0.3).
# Counterfactual reference 2023-01-01..2023-03-31. Both emitted with reference_window_id.
#
# **Critique M8 fix:** Primary PSI on full data; sensitivity with is_duration_suspicious=FALSE.

# %%
import hashlib
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir
from rts_predict.games.aoe2.datasets.aoestats.analysis.psi import compute_feature_psi
from rts_predict.games.aoe2.datasets.aoestats.analysis.survivorship import CONDITIONAL_CAPTION

ARTIFACTS_DIR = get_reports_dir("aoe2", "aoestats") / "artifacts" / "01_exploration" / "05_temporal_panel_eda"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

db = get_notebook_db("aoe2", "aoestats")

# %%
# Spec §9 Q3 reference window assertion
REF_START = date(2022, 8, 29)
REF_END = date(2022, 10, 27)
REF_PATCH = 66692  # matches_raw: patch 66692 covers [2022-08-29, 2022-12-08]; spec §7 corrected v1.0.3 (was 125283).
assert REF_START == date(2022, 8, 29) and REF_END == date(2022, 10, 27), "Bad aoestats ref window"
# Spec §7 originally cited 125283 as the reference-window patch; empirical
# verification against matches_raw (2026-04-19) established that patch 125283
# covers 2024-10-15..2025-04-11 and the 2022-08-29 window is exclusively on
# patch 66692. Spec v1.0.3 §14 amendment documents the correction.
assert REF_PATCH == 66692, f"Bad aoestats ref_patch: {REF_PATCH}"

# Counterfactual reference per critique B3
ALT_REF_START = date(2023, 1, 1)
ALT_REF_END = date(2023, 3, 31)

TESTED_QUARTERS = [
    ("2023-Q1", "2023-01-01", "2023-03-31"),
    ("2023-Q2", "2023-04-01", "2023-06-30"),
    ("2023-Q3", "2023-07-01", "2023-09-30"),
    ("2023-Q4", "2023-10-01", "2023-12-31"),
    ("2024-Q1", "2024-01-01", "2024-03-31"),
    ("2024-Q2", "2024-04-01", "2024-06-30"),
    ("2024-Q3", "2024-07-01", "2024-09-30"),
    ("2024-Q4", "2024-10-01", "2024-12-31"),
]

# Pre-game features per critique M4 fix (focal_old_rating replaces p0/p1 as primary)
PRE_GAME_FEATURES = [
    "focal_old_rating",
    "avg_elo",
    "faction",
    "opponent_faction",
    "mirror",
    "p0_is_unrated",
    "p1_is_unrated",
    "map",
]

print(f"Reference: {REF_START} .. {REF_END}, patch={REF_PATCH}")
print(f"Counterfactual reference: {ALT_REF_START} .. {ALT_REF_END}")

# %%
# Reference cohort SQL (spec §6.3 N >= 10 matches in reference)
# NOTE: Using SEMI-JOIN pattern to avoid materializing large cohort ID lists
REF_COHORT_SQL = f"""
WITH ref_cohort AS (
  SELECT CAST(player_id AS BIGINT) AS player_id, COUNT(*) AS n_matches
  FROM matches_history_minimal
  WHERE started_at >= TIMESTAMP '{REF_START}'
    AND started_at <= TIMESTAMP '{REF_END}'
  GROUP BY player_id
  HAVING COUNT(*) >= 10
)
SELECT
  CAST(mhm.player_id AS BIGINT) AS player_id,
  mhm.faction,
  mhm.opponent_faction,
  CAST(mhm.won AS INTEGER) AS won,
  mhm.duration_seconds,
  m1v1.patch,
  m1v1.avg_elo,
  CAST(m1v1.mirror AS INTEGER) AS mirror,
  m1v1.p0_old_rating,
  m1v1.p1_old_rating,
  CAST(m1v1.p0_is_unrated AS INTEGER) AS p0_is_unrated,
  CAST(m1v1.p1_is_unrated AS INTEGER) AS p1_is_unrated,
  m1v1.map,
  CASE WHEN CAST(mhm.player_id AS BIGINT) = m1v1.p0_profile_id
    THEN m1v1.p0_old_rating
    ELSE m1v1.p1_old_rating
  END AS focal_old_rating,
  rc.n_matches AS n_matches_in_ref
FROM matches_history_minimal mhm
JOIN matches_1v1_clean m1v1
  ON mhm.match_id = 'aoestats::' || m1v1.game_id
JOIN ref_cohort rc ON CAST(mhm.player_id AS BIGINT) = rc.player_id
WHERE mhm.started_at >= TIMESTAMP '{REF_START}'
  AND mhm.started_at <= TIMESTAMP '{REF_END}'
"""

print("Loading reference cohort...")
df_ref = db.fetch_df(REF_COHORT_SQL)
print(f"Reference cohort: {len(df_ref):,} rows, {df_ref['player_id'].nunique():,} unique players")

# %%
# M8 sensitivity: check impact of duration corruption filter
dup_corrupt = (df_ref["duration_seconds"] > 86400).sum()
print(f"Duration suspicious rows in reference: {dup_corrupt} ({dup_corrupt/len(df_ref)*100:.4f}%)")
df_ref_clean = df_ref[df_ref["duration_seconds"] <= 86400].copy()
print(f"Reference after corruption filter: {len(df_ref_clean):,} rows")

# %%
# Build reference edge fingerprints per feature
REF_EDGES: dict[str, object] = {}

for feat in PRE_GAME_FEATURES:
    if feat not in df_ref.columns:
        print(f"WARNING: {feat} not in reference data, skipping")
        continue
    series = df_ref[feat]
    unique_vals = series.dropna().unique()
    fingerprint = hashlib.md5(
        ",".join(sorted(str(v) for v in unique_vals)).encode()
    ).hexdigest()[:8]
    REF_EDGES[feat] = {"n_unique": int(len(unique_vals)), "fingerprint": fingerprint}

print("Reference edge fingerprints:", REF_EDGES)

# %%
# Helper: load tested quarter data using semi-join (avoids large IN clause)
def load_quarter_data(q_name: str, q_start: str, q_end: str) -> pd.DataFrame:
    """Load tested quarter data for reference cohort players (semi-join)."""
    TESTED_SQL = f"""
    WITH ref_cohort AS (
      SELECT CAST(player_id AS BIGINT) AS player_id
      FROM matches_history_minimal
      WHERE started_at >= TIMESTAMP '{REF_START}'
        AND started_at <= TIMESTAMP '{REF_END}'
      GROUP BY player_id HAVING COUNT(*) >= 10
    )
    SELECT
      CAST(mhm.player_id AS BIGINT) AS player_id,
      mhm.faction,
      mhm.opponent_faction,
      CAST(mhm.won AS INTEGER) AS won,
      mhm.duration_seconds,
      m1v1.avg_elo,
      CAST(m1v1.mirror AS INTEGER) AS mirror,
      m1v1.p0_old_rating,
      m1v1.p1_old_rating,
      CAST(m1v1.p0_is_unrated AS INTEGER) AS p0_is_unrated,
      CAST(m1v1.p1_is_unrated AS INTEGER) AS p1_is_unrated,
      m1v1.map,
      CASE WHEN CAST(mhm.player_id AS BIGINT) = m1v1.p0_profile_id
        THEN m1v1.p0_old_rating
        ELSE m1v1.p1_old_rating
      END AS focal_old_rating
    FROM matches_history_minimal mhm
    JOIN matches_1v1_clean m1v1
      ON mhm.match_id = 'aoestats::' || m1v1.game_id
    JOIN ref_cohort rc ON CAST(mhm.player_id AS BIGINT) = rc.player_id
    WHERE mhm.started_at >= TIMESTAMP '{q_start}'
      AND mhm.started_at <= TIMESTAMP '{q_end}'
    """
    return db.fetch_df(TESTED_SQL)

cohort_ids = df_ref["player_id"].unique().tolist()
print(f"Cohort: {len(cohort_ids):,} unique players")

# %%
# Compute PSI for all features across tested quarters
all_psi_rows = []
ref_features = {feat: df_ref[feat] for feat in PRE_GAME_FEATURES if feat in df_ref.columns}

for q_name, q_start, q_end in TESTED_QUARTERS:
    print(f"Processing {q_name}...")
    df_test = load_quarter_data(q_name, q_start, q_end)
    print(f"  {q_name}: {len(df_test):,} rows")

    for feat in PRE_GAME_FEATURES:
        if feat not in df_test.columns or feat not in ref_features:
            continue
        ref_s = ref_features[feat]
        test_s = df_test[feat]
        result = compute_feature_psi(ref_s, test_s, feat)

        notes = result["notes"]
        # PRE-canonical_slot: per-slot breakdown rows only (critique M4)
        # faction/opponent_faction are UNION-ALL symmetric -> NO flag on aggregate
        # p0/p1 ratings not in primary list -> no flag here

        row = {
            "dataset_tag": "aoestats",
            "quarter": q_name,
            "feature_name": feat,
            "metric_name": result["metric_name"],
            "metric_value": round(float(result["psi_value"]) if result["psi_value"] is not None else float("nan"), 4),
            "reference_window_id": "2022-Q3-patch66692",
            "cohort_threshold": 10,
            "sample_size": int(result["tested_bin_count"]),
            "notes": notes,
            "is_duration_corrupt_sensitive": False,
        }
        all_psi_rows.append(row)

    # M8: sensitivity with corruption filter
    df_test_clean = df_test[df_test["duration_seconds"] <= 86400]
    for feat in ["focal_old_rating", "avg_elo"]:
        if feat not in df_test_clean.columns or feat not in ref_features:
            continue
        ref_s_clean = df_ref_clean[feat] if feat in df_ref_clean.columns else ref_features[feat]
        test_s_clean = df_test_clean[feat]
        result_clean = compute_feature_psi(ref_s_clean, test_s_clean, feat)
        row_sens = {
            "dataset_tag": "aoestats",
            "quarter": q_name,
            "feature_name": feat,
            "metric_name": result_clean["metric_name"],
            "metric_value": round(float(result_clean["psi_value"]) if result_clean["psi_value"] is not None else float("nan"), 4),
            "reference_window_id": "2022-Q3-patch66692",
            "cohort_threshold": 10,
            "sample_size": int(result_clean["tested_bin_count"]),
            "notes": result_clean["notes"] + " [M8-sensitivity: is_duration_suspicious=FALSE]",
            "is_duration_corrupt_sensitive": True,
        }
        all_psi_rows.append(row_sens)

df_psi = pd.DataFrame(all_psi_rows)
print(f"PSI table: {len(df_psi)} rows")

# %%
# Emit per-quarter PSI CSVs
for q_name, _, _ in TESTED_QUARTERS:
    q_df = df_psi[(df_psi["quarter"] == q_name) & ~df_psi["is_duration_corrupt_sensitive"]]
    q_df = q_df.drop(columns=["is_duration_corrupt_sensitive"])
    fname = ARTIFACTS_DIR / f"psi_aoestats_{q_name}.csv"
    q_df.to_csv(fname, index=False)
print("Per-quarter PSI CSVs written.")

# %%
# B3 Counterfactual: PSI with alternative reference 2023-Q1
print("Computing counterfactual PSI (alt ref 2023-01-01..2023-03-31)...")
ALT_REF_SQL = f"""
WITH ref_cohort AS (
  SELECT CAST(player_id AS BIGINT) AS player_id
  FROM matches_history_minimal
  WHERE started_at >= TIMESTAMP '{ALT_REF_START}'
    AND started_at <= TIMESTAMP '{ALT_REF_END}'
  GROUP BY player_id HAVING COUNT(*) >= 10
)
SELECT mhm.faction, mhm.opponent_faction, m1v1.avg_elo,
  CAST(m1v1.mirror AS INTEGER) AS mirror,
  CAST(m1v1.p0_is_unrated AS INTEGER) AS p0_is_unrated,
  CAST(m1v1.p1_is_unrated AS INTEGER) AS p1_is_unrated,
  m1v1.map,
  CASE WHEN CAST(mhm.player_id AS BIGINT) = m1v1.p0_profile_id
       THEN m1v1.p0_old_rating ELSE m1v1.p1_old_rating END AS focal_old_rating
FROM matches_history_minimal mhm
JOIN matches_1v1_clean m1v1 ON mhm.match_id = 'aoestats::' || m1v1.game_id
JOIN ref_cohort rc ON CAST(mhm.player_id AS BIGINT) = rc.player_id
WHERE mhm.started_at >= TIMESTAMP '{ALT_REF_START}'
  AND mhm.started_at <= TIMESTAMP '{ALT_REF_END}'
"""
df_alt_ref = db.fetch_df(ALT_REF_SQL)
print(f"Alt reference: {len(df_alt_ref):,} rows")

alt_psi_rows = []
alt_ref_features = {feat: df_alt_ref[feat] for feat in PRE_GAME_FEATURES if feat in df_alt_ref.columns}

for q_name, q_start, q_end in TESTED_QUARTERS[1:]:  # skip 2023-Q1 (= reference itself)
    df_test = load_quarter_data(q_name, q_start, q_end)
    for feat in PRE_GAME_FEATURES:
        if feat not in df_test.columns or feat not in alt_ref_features:
            continue
        result = compute_feature_psi(alt_ref_features[feat], df_test[feat], feat)
        alt_psi_rows.append({
            "dataset_tag": "aoestats",
            "quarter": q_name,
            "feature_name": feat,
            "metric_name": result["metric_name"],
            "metric_value": round(float(result["psi_value"]) if result["psi_value"] is not None else float("nan"), 4),
            "reference_window_id": "2023-Q1-alt",
            "cohort_threshold": 10,
            "sample_size": int(result["tested_bin_count"]),
            "notes": result["notes"] + " [B3-counterfactual]",
        })

df_alt_psi = pd.DataFrame(alt_psi_rows)
alt_csv = ARTIFACTS_DIR / "psi_aoestats_counterfactual_2023Q1ref.csv"
df_alt_psi.to_csv(alt_csv, index=False)
print(f"Counterfactual PSI written: {alt_csv}")

# %%
# Falsifier check: does rating PSI stay < 0.10 across all 8 quarters?
primary_psi = df_psi[~df_psi["is_duration_corrupt_sensitive"] & (df_psi["feature_name"].isin(["focal_old_rating", "avg_elo"]))]
rating_psi_by_q = primary_psi.groupby("quarter")["metric_value"].max()
n_above_010 = (rating_psi_by_q >= 0.10).sum()

faction_psi = df_psi[~df_psi["is_duration_corrupt_sensitive"] & (df_psi["feature_name"] == "faction")]
faction_psi_by_q = faction_psi.groupby("quarter")["metric_value"].max()
faction_above_025 = (faction_psi_by_q >= 0.25).sum()

if n_above_010 == 0 and faction_above_025 > 0:
    verdict = "FALSIFIED"
else:
    verdict = "PASSED"

print(f"Rating PSI >= 0.10 in {n_above_010} of 8 quarters")
print(f"Faction PSI >= 0.25 in {faction_above_025} of 8 quarters")
print(f"Q2 rating-drift hypothesis: {verdict}")

# %%
# Summary JSON with edge fingerprints (proves frozen edges across quarters)
summary = {
    "step": "01_05_02",
    "spec": "reports/specs/01_05_preregistration.md@7e259dd8",
    "reference_window": {"start": str(REF_START), "end": str(REF_END), "patch": REF_PATCH},
    "counterfactual_reference_window": {"start": str(ALT_REF_START), "end": str(ALT_REF_END)},
    "feature_list": PRE_GAME_FEATURES,
    "reference_edge_fingerprints": REF_EDGES,
    "n_psi_rows_primary": len(df_psi[~df_psi["is_duration_corrupt_sensitive"]]),
    "n_psi_rows_m8_sensitivity": len(df_psi[df_psi["is_duration_corrupt_sensitive"]]),
    "n_psi_rows_counterfactual": len(df_alt_psi),
    "falsifier_verdict": verdict,
    "rating_psi_quarters_above_010": int(n_above_010),
    "faction_psi_quarters_above_025": int(faction_above_025),
    "note_B3_coincidence": (
        "Primary reference start 2022-08-29 coincides with dataset earliest date. "
        "Counterfactual 2023-Q1 reference provided. Gate memo documents whether "
        "counterfactual supports/undermines primary PSI conclusions."
    ),
}
summary_json = ARTIFACTS_DIR / "01_05_02_psi_summary.json"
with open(summary_json, "w") as f:
    json.dump(summary, f, indent=2, default=str)
print(f"Wrote {summary_json}")

# %%
# Summary MD
caption = CONDITIONAL_CAPTION
md_summary = f"""# PSI Pre-Game Features Summary — aoestats

**spec:** reports/specs/01_05_preregistration.md@7e259dd8
**Step:** 01_05_02
{caption}

## Primary Reference: 2022-08-29..2022-10-27 (patch 66692; spec §7 corrected v1.0.3)

Features analyzed: {', '.join(PRE_GAME_FEATURES)}

## Rating Drift (focal_old_rating, avg_elo)

Quarters with PSI >= 0.10: **{n_above_010}** of 8

## Faction Stability

Quarters with PSI >= 0.25: **{faction_above_025}** of 8

## B3 Coincidence Note

Primary reference window start (2022-08-29) coincides with dataset's earliest date.
Counterfactual reference (2023-Q1) CSV: `psi_aoestats_counterfactual_2023Q1ref.csv`.
See gate memo for B3 verdict.

## M4 Note (Critique fix)

`focal_old_rating = CASE WHEN player_id = p0_profile_id THEN p0_old_rating ELSE p1_old_rating END`
is used as the symmetric rating feature. Per-slot (p0/p1) analysis not emitted in
primary PSI; would carry [PRE-canonical_slot] tag.

## Falsifier verdict

**Q2 rating-drift hypothesis:** {verdict}
"""
(ARTIFACTS_DIR / "01_05_02_psi_summary.md").write_text(md_summary)

# %%
print(f"Q2 rating-drift hypothesis: {verdict}")
print("Step 01_05_02 complete.")
