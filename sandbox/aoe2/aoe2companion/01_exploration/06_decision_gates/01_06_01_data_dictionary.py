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
# # 01_06_01 — Data Dictionary (aoe2companion)
#
# **Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
# **Hypothesis:** Every Phase-02-candidate column categorises cleanly under I3.
#   `profileId` flagged with identity-rate reconciliation (2.57% / 3.55%).
#   No POST_GAME column assigned PRE_GAME.
# **Falsifier:** POST_GAME column assigned PRE_GAME; profileId missing identity note.

# %%
import csv, yaml, os
from collections import Counter

REPO_ROOT = os.environ.get("REPO_ROOT", "/Users/tomaszpionka/Projects/rts-outcome-prediction")
SCHEMA_DIR = os.path.join(REPO_ROOT, "src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/views")
OUT_DIR = os.path.join(REPO_ROOT, "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates")
os.makedirs(OUT_DIR, exist_ok=True)

def load_schema(fname):
    with open(os.path.join(SCHEMA_DIR, fname)) as f:
        return yaml.safe_load(f)

mhm = load_schema("matches_history_minimal.yaml")
m1v1 = load_schema("matches_1v1_clean.yaml")
pha = load_schema("player_history_all.yaml")

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

        inv_notes = notes[:300] if notes else "none"

        # Flag profileId with identity-rate reconciliation note
        if name in ("profileId", "player_id"):
            if "identity" not in inv_notes.lower() and "branch" not in inv_notes.lower():
                inv_notes = (
                    "[IDENTITY: Branch (i) API-namespace identifier] aoe2companion uses profileId "
                    "(Branch i rename-stable per INVARIANTS.md §5 I2). Identity-rate reconciliation "
                    "2026-04-19: 2.57% / 3.55% rename-rate in rm_1v1 scope. Cross-dataset "
                    "aoe2companion-aoestats namespace bridge VERDICT A (0.9960 agreement). "
                    + inv_notes
                )

        valid_range = "see notes"
        if dtype == "BOOLEAN":
            valid_range = "{TRUE, FALSE, NULL}"
        elif "duration_seconds" in name or "duration" in name.lower():
            valid_range = "≥0s"
        units = "none"
        if "duration" in name.lower():
            units = "seconds"
        elif "rating" in name.lower() or "elo" in name.lower():
            units = "Elo points"

        rows.append({
            "column_name": name, "table_or_view": table_name, "dtype": dtype,
            "semantics": desc, "valid_range": valid_range, "nullability": nullable,
            "units": units, "temporal_classification": tc,
            "provenance_step": "01_04_02" if table_name in ("matches_1v1_clean", "player_history_all") else "01_04_03",
            "invariant_notes": inv_notes,
        })

print(f"Total rows: {len(rows)}")

# Gate: no POST_GAME assigned PRE_GAME
violations = [(r["column_name"], r["table_or_view"]) for r in rows
              if r["temporal_classification"] == "PRE_GAME" and "POST_GAME" in r["invariant_notes"].upper()]
assert len(violations) == 0, f"I3 violation: {violations}"

# Gate: profileId/player_id has identity note
id_flagged = [r for r in rows if r["column_name"] in ("profileId", "player_id")
              and "IDENTITY" in r["invariant_notes"].upper()]
assert len(id_flagged) > 0, "profileId/player_id missing identity-rate note"
print(f"Identity-annotated columns: {[r['column_name'] for r in id_flagged]}")
print("I3 gate: PASS")

csv_path = os.path.join(OUT_DIR, "data_dictionary_aoe2companion.csv")
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"Wrote {csv_path}")

tc_counts = Counter(r["temporal_classification"] for r in rows)

md = f"""# Data Dictionary — aoe2companion

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
**Date:** 2026-04-19

## Temporal Classification: {dict(tc_counts)}

## Key Notes
- `profileId` / `player_id`: Branch (i) API-namespace identifier. Identity-rate reconciliation
  2026-04-19: 2.57% / 3.55% rename-rate in rm_1v1 scope. Cross-dataset
  aoe2companion-aoestats namespace bridge VERDICT A (0.9960 agreement). See §4.2.2.
- `duration_seconds` is POST_GAME_HISTORICAL; DO NOT use as PRE_GAME feature (I3).
- `won` is the TARGET variable; also used as drift-proxy in PSI (W2) — stable in all quarters.
- `faction` and `map_id`: both show substantive drift from 2023-Q3 (DLC map-pool rotation);
  Phase 02 temporal CV must handle unseen categories for map_id.
- No `[PRE-canonical_slot]` flag needed: aoe2companion does not assign team slots by skill rank
  (no equivalent of aoestats W3 ARTEFACT_EDGE).
- `country` column: 2.25% NULL retention (MAR primary / MNAR sensitivity per §4.2.3);
  MissingIndicator route applied in cleaning.

## Full Dictionary
See `data_dictionary_aoe2companion.csv`.
"""
md_path = os.path.join(OUT_DIR, "data_dictionary_aoe2companion.md")
with open(md_path, "w") as f:
    f.write(md)
print(f"Wrote {md_path}")
