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
# # Step 01_01_02 — Schema Discovery: aoestats
#
# **Phase:** 01 — Data Exploration
# **Pipeline Section:** 01_01 — Data Acquisition & Source Inventory
# **Dataset:** aoestats
# **Question:** What columns exist in each file type, what are their data types, is the schema consistent across the temporal range, and do matches and players share structurally overlapping columns?
# **Invariants applied:** #6 (reproducibility), #7 (no magic numbers), #9 (pipeline discipline)
# **ROADMAP reference:** `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` Step 01_01_02
#
# Full census: `discover_parquet_schemas()` on all matches and players Parquet files.
# `discover_json_schema()` on `overview.json`. Cross-column-name comparison.
# No DuckDB type proposals.

# %% [markdown]
# ## Cell 1 — Imports, config, paths

# %%
import json
from pathlib import Path

from rts_predict.common.json_utils import discover_json_schema
from rts_predict.common.parquet_utils import discover_parquet_schemas
from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.aoe2.config import (
    AOESTATS_RAW_DIR,
    AOESTATS_RAW_MATCHES_DIR,
    AOESTATS_RAW_PLAYERS_DIR,
    AOESTATS_RAW_OVERVIEW_DIR,
)

logger = setup_notebook_logging()

ARTIFACTS_DIR: Path = (
    get_reports_dir("aoe2", "aoestats")
    / "artifacts"
    / "01_exploration"
    / "01_acquisition"
)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
PRIOR_ARTIFACT: Path = ARTIFACTS_DIR / "01_01_01_file_inventory.json"

logger.info("ARTIFACTS_DIR: %s", ARTIFACTS_DIR)

# %% [markdown]
# ## Cell 2 — Load 01_01_01 artifact to get file lists

# %%
with PRIOR_ARTIFACT.open() as fh:
    inventory = json.load(fh)

subdir_info = {sd["name"]: sd for sd in inventory["subdirs"]}
print(f"Subdirectories from inventory: {list(subdir_info.keys())}")

# %% [markdown]
# ## Cell 3 — File selection (full census for all file types)

# %%
matches_files = sorted(
    f for f in AOESTATS_RAW_MATCHES_DIR.iterdir()
    if f.suffix == ".parquet"
)
players_files = sorted(
    f for f in AOESTATS_RAW_PLAYERS_DIR.iterdir()
    if f.suffix == ".parquet"
)
overview_file = AOESTATS_RAW_OVERVIEW_DIR / "overview.json"

print(f"matches Parquet files: {len(matches_files)}")
print(f"players Parquet files: {len(players_files)}")
print(f"overview.json exists: {overview_file.exists()}")

# %% [markdown]
# ## Cell 4 — Schema discovery
#
# Parquet: `discover_parquet_schemas()` on all matches and players files.
# JSON: `discover_json_schema()` on `overview.json`.

# %%
print(f"Running discover_parquet_schemas() on {len(matches_files)} matches files...")
matches_result = discover_parquet_schemas(matches_files)
print(
    f"matches: all_same={matches_result['all_files_same_schema']}, "
    f"files_checked={matches_result['files_checked']}, "
    f"variant_cols={matches_result['variant_columns']}"
)

# %%
print(f"Running discover_parquet_schemas() on {len(players_files)} players files...")
players_result = discover_parquet_schemas(players_files)
print(
    f"players: all_same={players_result['all_files_same_schema']}, "
    f"files_checked={players_result['files_checked']}, "
    f"variant_cols={players_result['variant_columns']}"
)

# %%
print("Running discover_json_schema() on overview.json...")
overview_profiles = discover_json_schema([overview_file], max_sample_values=3) if overview_file.exists() else []
print(f"overview.json root keys: {len(overview_profiles)}")

# %% [markdown]
# ## Cell 5 — Schema consistency check + cross-column name comparison

# %%
matches_representative = matches_result["schemas"][0] if matches_result["schemas"] else {}
players_representative = players_result["schemas"][0] if players_result["schemas"] else {}

matches_col_names = {c["name"] for c in matches_representative.get("columns", [])}
players_col_names = {c["name"] for c in players_representative.get("columns", [])}

shared_col_names = sorted(matches_col_names & players_col_names)
matches_only_names = sorted(matches_col_names - players_col_names)
players_only_names = sorted(players_col_names - matches_col_names)

print(f"matches columns: {len(matches_col_names)}")
print(f"players columns: {len(players_col_names)}")
print(f"shared column names: {len(shared_col_names)}")
print(f"matches-only column names: {len(matches_only_names)}")
print(f"players-only column names: {len(players_only_names)}")
print(f"shared names: {shared_col_names}")

# %% [markdown]
# ## Cell 6 — Write JSON artifact

# %%
overview_columns_out = [
    {
        "name": kp.key,
        "physical_type": sorted(kp.observed_types)[0] if len(kp.observed_types) == 1 else sorted(kp.observed_types),
        "nullable": kp.nullable,
        "frequency": kp.frequency,
        "total_samples": kp.total_samples,
        "sample_values": kp.sample_values,
    }
    for kp in overview_profiles
]

artifact = {
    "step": "01_01_02",
    "dataset": "aoestats",
    "sampling": {
        "strategy": "census",
        "total_files_in_dataset": inventory["total_files"],
        "files_checked": len(matches_files) + len(players_files) + (1 if overview_file.exists() else 0),
        "method": (
            "Full census for all Parquet files (metadata-only read via pyarrow.parquet.read_schema). "
            "Full census for overview.json (1 file, discover_json_schema)."
        ),
    },
    "file_types": [
        {
            "type": "parquet",
            "subdirectory": "matches",
            "files_in_subdirectory": len(matches_files),
            "files_checked": matches_result["files_checked"],
            "schema": {
                "columns": [
                    {
                        "name": c["name"],
                        "physical_type": c["arrow_type"],
                        "nullable": c["nullable"],
                    }
                    for c in matches_representative.get("columns", [])
                ],
                "total_columns": matches_representative.get("total_columns", 0),
            },
            "consistency": {
                "all_files_same_schema": matches_result["all_files_same_schema"],
                "variant_columns": matches_result["variant_columns"],
            },
        },
        {
            "type": "parquet",
            "subdirectory": "players",
            "files_in_subdirectory": len(players_files),
            "files_checked": players_result["files_checked"],
            "schema": {
                "columns": [
                    {
                        "name": c["name"],
                        "physical_type": c["arrow_type"],
                        "nullable": c["nullable"],
                    }
                    for c in players_representative.get("columns", [])
                ],
                "total_columns": players_representative.get("total_columns", 0),
            },
            "consistency": {
                "all_files_same_schema": players_result["all_files_same_schema"],
                "variant_columns": players_result["variant_columns"],
            },
        },
        {
            "type": "json",
            "subdirectory": "overview",
            "files_in_subdirectory": 1,
            "files_checked": 1 if overview_file.exists() else 0,
            "schema": {
                "columns": overview_columns_out,
                "total_columns": len(overview_columns_out),
                "nesting_depth": 1,
            },
            "consistency": {
                "all_files_same_schema": True,
                "variant_columns": [],
            },
        },
    ],
    "cross_comparison": {
        "matches_vs_players_column_name_overlap": {
            "shared_column_names": shared_col_names,
            "shared_count": len(shared_col_names),
            "matches_only_count": len(matches_only_names),
            "players_only_count": len(players_only_names),
            "matches_only_column_names": matches_only_names,
            "players_only_column_names": players_only_names,
            "method": "raw string comparison of column names only — no semantic interpretation",
        }
    },
}

out_json = ARTIFACTS_DIR / "01_01_02_schema_discovery.json"
with out_json.open("w") as fh:
    json.dump(artifact, fh, indent=2)
logger.info("Wrote JSON artifact: %s", out_json)

# %% [markdown]
# ## Cell 7 — Write Markdown artifact

# %%
md_lines = [
    "# Step 01_01_02 — Schema Discovery: aoestats",
    "",
    "**Phase:** 01 — Data Exploration  ",
    "**Pipeline Section:** 01_01 — Data Acquisition & Source Inventory  ",
    "**Dataset:** aoestats  ",
    "**Invariants applied:** #6, #7, #9  ",
    "",
    "## Sampling methodology",
    "",
    "Full census for all file types.",
    "",
    "| File type | Subdirectory | Files in dataset | Files checked | Method |",
    "|-----------|-------------|-----------------|--------------|--------|",
    f"| Parquet | `matches/` | {len(matches_files)} | {matches_result['files_checked']} | metadata-only (pyarrow.parquet.read_schema) |",
    f"| Parquet | `players/` | {len(players_files)} | {players_result['files_checked']} | metadata-only (pyarrow.parquet.read_schema) |",
    f"| JSON | `overview/` | 1 | {1 if overview_file.exists() else 0} | discover_json_schema (root keys) |",
    "",
    "## matches/ schema (Parquet)",
    "",
    f"**Total columns:** {matches_representative.get('total_columns', 0)}  ",
    f"**Schema consistency:** {matches_result['all_files_same_schema']}  ",
    "",
    "| Column | Arrow type | Nullable |",
    "|--------|-----------|----------|",
]

for c in matches_representative.get("columns", []):
    md_lines.append(f"| `{c['name']}` | {c['arrow_type']} | {c['nullable']} |")

md_lines += [
    "",
    "## players/ schema (Parquet)",
    "",
    f"**Total columns:** {players_representative.get('total_columns', 0)}  ",
    f"**Schema consistency:** {players_result['all_files_same_schema']}  ",
    "",
    "| Column | Arrow type | Nullable |",
    "|--------|-----------|----------|",
]

for c in players_representative.get("columns", []):
    md_lines.append(f"| `{c['name']}` | {c['arrow_type']} | {c['nullable']} |")

md_lines += [
    "",
    "## overview/ schema (JSON)",
    "",
    f"**Total root keys:** {len(overview_profiles)}  ",
    "",
    "| Key | Observed types | Nullable | Frequency / Total |",
    "|-----|----------------|----------|-------------------|",
]

for kp in overview_profiles:
    type_str = ", ".join(sorted(kp.observed_types))
    md_lines.append(f"| `{kp.key}` | {type_str} | {kp.nullable} | {kp.frequency} / {kp.total_samples} |")

md_lines += [
    "",
    "## Cross-comparison: matches vs players column names",
    "",
    f"Comparison is raw string matching of column names only — no semantic interpretation.",
    "",
    f"| Metric | Count |",
    f"|--------|-------|",
    f"| Shared column names | {len(shared_col_names)} |",
    f"| matches-only column names | {len(matches_only_names)} |",
    f"| players-only column names | {len(players_only_names)} |",
    "",
    "**Shared column names:**",
    "",
]
for name in shared_col_names:
    md_lines.append(f"- `{name}`")

md_lines += [
    "",
    "**matches-only column names:**",
    "",
]
for name in matches_only_names:
    md_lines.append(f"- `{name}`")

md_lines += [
    "",
    "**players-only column names:**",
    "",
]
for name in players_only_names:
    md_lines.append(f"- `{name}`")

md_lines += [
    "",
    "## Notes",
    "",
    "- No DuckDB type proposals in this step (deferred to ingestion design).",
    "- Step scope: `content` (file headers/schemas).",
]

out_md = ARTIFACTS_DIR / "01_01_02_schema_discovery.md"
out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
logger.info("Wrote Markdown artifact: %s", out_md)
