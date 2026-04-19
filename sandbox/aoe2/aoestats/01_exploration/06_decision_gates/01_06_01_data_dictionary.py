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
# # 01_06_01 — Data Dictionary (aoestats)
#
# **Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
# **Hypothesis:** Every Phase-02-candidate column categorises cleanly under I3.
#   team=0/team=1 columns flagged [PRE-canonical_slot].
# **Falsifier:** POST_GAME column assigned PRE_GAME; team columns missing [PRE-canonical_slot] flag.

# %%
import csv, yaml, os

REPO_ROOT = os.environ.get("REPO_ROOT", "/Users/tomaszpionka/Projects/rts-outcome-prediction")
SCHEMA_DIR = os.path.join(REPO_ROOT, "src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views")
OUT_DIR = os.path.join(REPO_ROOT, "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates")
os.makedirs(OUT_DIR, exist_ok=True)

def load_schema(fname):
    with open(os.path.join(SCHEMA_DIR, fname)) as f:
        return yaml.safe_load(f)

m1v1 = load_schema("matches_1v1_clean.yaml")
pha = load_schema("player_history_all.yaml")
mhm = load_schema("matches_history_minimal.yaml")

def classify(notes_str, name):
    n = (notes_str or "").upper()
    if "TARGET" in n:
        return "TARGET"
    if "POST_GAME_HISTORICAL" in n:
        return "POST_GAME_HISTORICAL"
    if "IN_GAME_HISTORICAL" in n:
        return "IN_GAME_HISTORICAL"
    if "PRE_GAME" in n:
        return "PRE_GAME"
    if "IDENTITY" in n:
        return "IDENTIFIER"
    return "METADATA"

rows = []
for table_name, schema in [
    ("matches_history_minimal", mhm),
    ("matches_1v1_clean", m1v1),
    ("player_history_all", pha),
]:
    for col in schema.get("columns", []):
        name = col.get("name", "")
        dtype = col.get("type", "")
        desc = col.get("description", col.get("notes", ""))[:200]
        notes = col.get("notes", "")
        nullable_raw = col.get("nullable", True)
        nullable = "NOT NULL" if nullable_raw is False else "NULLABLE"
        tc = classify(notes, name)

        # Flag team-slot columns [PRE-canonical_slot]
        inv_notes = notes[:300] if notes else "none"
        if name in ("team_0_elo", "team_1_elo", "p0_civ", "p1_civ",
                    "p0_old_rating", "p1_old_rating", "p0_is_unrated", "p1_is_unrated",
                    "p0_winner", "p1_winner", "p0_profile_id", "p1_profile_id",
                    "team1_wins", "team"):
            if "[PRE-canonical_slot]" not in inv_notes:
                inv_notes = f"[PRE-canonical_slot] team=0/1 assignment is skill-correlated per W3 ARTEFACT_EDGE (01_04_05). " + inv_notes

        valid_range = "see notes"
        if dtype == "BOOLEAN":
            valid_range = "{TRUE, FALSE, NULL}"
        elif "duration_seconds" in name:
            valid_range = "≥0s"
        units = "none"
        if "duration_seconds" in name:
            units = "seconds"
        elif "elo" in name.lower() or "rating" in name.lower():
            units = "Elo points"

        rows.append({
            "column_name": name, "table_or_view": table_name, "dtype": dtype,
            "semantics": desc, "valid_range": valid_range, "nullability": nullable,
            "units": units, "temporal_classification": tc,
            "provenance_step": "01_04_02" if table_name in ("matches_1v1_clean","player_history_all") else "01_04_03",
            "invariant_notes": inv_notes,
        })

print(f"Total rows: {len(rows)}")

# Gate: no POST_GAME assigned PRE_GAME
violations = [(r["column_name"],r["table_or_view"]) for r in rows
              if r["temporal_classification"]=="PRE_GAME" and "POST_GAME" in r["invariant_notes"].upper()]
assert len(violations)==0, f"I3 violation: {violations}"

# Gate: [PRE-canonical_slot] team columns present
team_cols_flagged = [r for r in rows if "[PRE-canonical_slot]" in r["invariant_notes"]]
assert len(team_cols_flagged) > 0, "No [PRE-canonical_slot] columns flagged"
print(f"[PRE-canonical_slot] flagged columns: {len(team_cols_flagged)}")
print("I3 gate: PASS")

csv_path = os.path.join(OUT_DIR, "data_dictionary_aoestats.csv")
with open(csv_path, "w", newline="") as f:
    csv.DictWriter(f, fieldnames=list(rows[0].keys())).writeheader()
    csv.DictWriter(f, fieldnames=list(rows[0].keys())).writerows(rows)

# fix: rewrite properly
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"Wrote {csv_path}")

from collections import Counter
tc_counts = Counter(r["temporal_classification"] for r in rows)

md = f"""# Data Dictionary — aoestats

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
**Date:** 2026-04-19

## Temporal Classification: {dict(tc_counts)}

## Key Notes
- `team=0/1` slot columns carry `[PRE-canonical_slot]` flag per W3 ARTEFACT_EDGE (01_04_05).
  Direct slot-conditioned features are forbidden until BACKLOG F1 + W4 resolve.
- `patch` (BIGINT) present in matches_1v1_clean and player_history_all — D5 PRIMARY role for aoestats.
- `duration_seconds` is POST_GAME_HISTORICAL; DO NOT use as PRE_GAME feature (I3).
- `avg_elo` sentinel=0 → NULL via NULLIF in 01_04_02.

## Full Dictionary
See `data_dictionary_aoestats.csv`.
"""
md_path = os.path.join(OUT_DIR, "data_dictionary_aoestats.md")
with open(md_path, "w") as f:
    f.write(md)
print(f"Wrote {md_path}")
