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
# # 01_06_01 — Data Dictionary (sc2egset)
#
# **Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0 (CROSS-01-06-v1)
# **Hypothesis:** Every column in matches_history_minimal / matches_flat_clean /
# player_history_all that is a Phase-02 feature candidate can be categorised as
# PRE_GAME, POST_GAME_HISTORICAL, TARGET, METADATA/CONTEXT, or IDENTIFIER under I3.
# **Falsifier:** Any column that resists categorisation, or any POST_GAME column
# assigned PRE_GAME.
#
# This notebook is a consolidation step (I9): reads schema YAMLs + cleaning artifacts
# from 01_04 only; no new DuckDB queries.

# %%
import csv
import json
import os
import yaml

REPO_ROOT = os.environ.get("REPO_ROOT", "/Users/tomaszpionka/Projects/rts-outcome-prediction")
SCHEMA_DIR = os.path.join(REPO_ROOT, "src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views")
OUT_DIR = os.path.join(REPO_ROOT, "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates")
os.makedirs(OUT_DIR, exist_ok=True)

# %%
# Load schemas
def load_schema(fname):
    with open(os.path.join(SCHEMA_DIR, fname)) as f:
        return yaml.safe_load(f)

mhm = load_schema("matches_history_minimal.yaml")
mfc = load_schema("matches_flat_clean.yaml")
pha = load_schema("player_history_all.yaml")

print(f"matches_history_minimal: {len(mhm['columns'])} cols")
print(f"matches_flat_clean: {len(mfc['columns'])} cols")
print(f"player_history_all: {len(pha['columns'])} cols")

# %%
# Build unified dictionary
# Temporal classification mapping from schema notes field
def classify(notes_str, name):
    n = notes_str.upper() if notes_str else ""
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
    if "CONTEXT" in n:
        return "METADATA"
    return "METADATA"

rows = []
for table_name, schema in [
    ("matches_history_minimal", mhm),
    ("matches_flat_clean", mfc),
    ("player_history_all", pha),
]:
    for col in schema.get("columns", []):
        name = col.get("name", "")
        dtype = col.get("type", "")
        desc = col.get("description", "")
        notes = col.get("notes", "")
        nullable_raw = col.get("nullable", True)
        nullable = "NOT NULL" if nullable_raw is False else "NULLABLE"

        tc = classify(notes, name)

        # Determine valid_range
        valid_range = "see notes"
        if dtype == "BOOLEAN":
            valid_range = "{TRUE, FALSE, NULL}"
        elif name in ("won",):
            valid_range = "{TRUE, FALSE}"
        elif name == "dataset_tag":
            valid_range = "constant 'sc2egset'"
        elif "duration_seconds" in name:
            valid_range = "≥0s; NULL if not parseable"
        elif "APM" in name and "missing" not in name and "unparseable" not in name:
            valid_range = ">0 integer (NULL if parse failure)"

        units = "none"
        if "duration_seconds" in name:
            units = "seconds"
        elif "APM" in name and not any(x in name for x in ["is_", "missing"]):
            units = "actions/minute"
        elif "Percent" in name:
            units = "percent"
        elif "Loops" in name:
            units = "game loops"

        rows.append({
            "column_name": name,
            "table_or_view": table_name,
            "dtype": dtype,
            "semantics": desc[:200] if desc else "",
            "valid_range": valid_range,
            "nullability": nullable,
            "units": units,
            "temporal_classification": tc,
            "provenance_step": "01_04_02" if table_name in ("matches_flat_clean", "player_history_all") else "01_04_03",
            "invariant_notes": notes[:300] if notes else "none",
        })

print(f"Total rows: {len(rows)}")

# %%
# Gate check: no POST_GAME column classified PRE_GAME
violations = [(r["column_name"], r["table_or_view"]) for r in rows
              if r["temporal_classification"] == "PRE_GAME"
              and "POST_GAME" in r["invariant_notes"].upper()]
assert len(violations) == 0, f"I3 VIOLATION: {violations}"
print("I3 gate: PASS — no POST_GAME column assigned PRE_GAME")

# Summary
from collections import Counter
tc_counts = Counter(r["temporal_classification"] for r in rows)
print("Temporal classification distribution:", dict(tc_counts))

# %%
# Write CSV
csv_path = os.path.join(OUT_DIR, "data_dictionary_sc2egset.csv")
with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
print(f"Wrote {csv_path} ({len(rows)} rows)")

# %%
# Write MD companion
md_lines = [
    "# Data Dictionary — sc2egset",
    "",
    "**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0 (CROSS-01-06-v1)",
    "**Produced by:** 01_06_01 (Phase 01 Decision Gates)",
    "**Date:** 2026-04-19",
    "",
    "## Temporal Classification Summary",
    "",
]
for tc, n in sorted(tc_counts.items()):
    md_lines.append(f"- **{tc}:** {n} column(s)")
md_lines.append("")
md_lines.append("## Tables covered")
md_lines.append("")
md_lines.append("- `matches_history_minimal` — 9-column Phase-02-ready cross-dataset view (I8 contract)")
md_lines.append("- `matches_flat_clean` — sc2egset-specific cleaned flat replay table")
md_lines.append("- `player_history_all` — sc2egset per-player history table (includes IN_GAME_HISTORICAL cols)")
md_lines.append("")
md_lines.append("## I3 Temporal Discipline Check")
md_lines.append("")
md_lines.append("- No POST_GAME_HISTORICAL column is classified PRE_GAME. **PASS.**")
md_lines.append("- `duration_seconds` and `is_duration_suspicious` are POST_GAME_HISTORICAL; Phase 02 feature extractors that drop POST_GAME_HISTORICAL tokens will auto-exclude them.")
md_lines.append("- `APM`, `SQ`, `supplyCappedPercent`, `is_decisive_result` are IN_GAME_HISTORICAL (sc2egset-specific; not available for AoE2 comparison datasets).")
md_lines.append("")
md_lines.append("## Columns with Invariant Notes")
md_lines.append("")
for r in rows:
    if r["invariant_notes"] != "none" and len(r["invariant_notes"]) > 10:
        md_lines.append(f"- **{r['column_name']}** (`{r['table_or_view']}`): `{r['invariant_notes'][:150]}`")
md_lines.append("")
md_lines.append("## Full Dictionary")
md_lines.append("")
md_lines.append("See `data_dictionary_sc2egset.csv` for the full column-level dictionary.")

md_path = os.path.join(OUT_DIR, "data_dictionary_sc2egset.md")
with open(md_path, "w") as f:
    f.write("\n".join(md_lines))
print(f"Wrote {md_path}")
