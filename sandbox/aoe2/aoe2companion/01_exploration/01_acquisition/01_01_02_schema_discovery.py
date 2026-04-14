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
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Step 01_01_02 — Schema Discovery: aoe2companion
#
# **Phase:** 01 — Data Exploration
# **Pipeline Section:** 01_01 — Data Acquisition & Source Inventory
# **Dataset:** aoe2companion
# **Question:** What columns exist in each file type, what are their data types, and is the schema consistent across the temporal range?
# **Invariants applied:** #6 (reproducibility), #7 (no magic numbers), #9 (pipeline discipline)
# **ROADMAP reference:** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` Step 01_01_02
#
# Full census: `discover_parquet_schemas()` on all matches Parquet files,
# `discover_csv_schema()` on all ratings CSV files, singletons for leaderboard
# and profile. No DuckDB type proposals.

# %% [markdown]
# ## Cell 1 — Imports, config, paths

# %%
import json
from pathlib import Path

from rts_predict.common.json_utils import build_column_list, build_schema_table
from rts_predict.common.parquet_utils import discover_parquet_schema, discover_parquet_schemas, discover_csv_schema, discover_csv_schemas
from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.aoe2.config import (
    AOE2COMPANION_RAW_DIR,
    AOE2COMPANION_RAW_MATCHES_DIR,
    AOE2COMPANION_RAW_LEADERBOARDS_DIR,
    AOE2COMPANION_RAW_PROFILES_DIR,
    AOE2COMPANION_RAW_RATINGS_DIR,
)

logger = setup_notebook_logging()

ARTIFACTS_DIR: Path = (
    get_reports_dir("aoe2", "aoe2companion")
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

subdir_counts = {sd["name"]: sd["file_count"] for sd in inventory["subdirs"]}
print(f"Subdirectories: {subdir_counts}")

# %% [markdown]
# ## Cell 3 — File selection (full census for all file types)

# %%
matches_parquet_files = sorted(
    f for f in AOE2COMPANION_RAW_MATCHES_DIR.iterdir()
    if f.suffix == ".parquet"
)
ratings_csv_files = sorted(
    f for f in AOE2COMPANION_RAW_RATINGS_DIR.iterdir()
    if f.suffix == ".csv"
)
leaderboard_file = AOE2COMPANION_RAW_LEADERBOARDS_DIR / "leaderboard.parquet"
profile_file = AOE2COMPANION_RAW_PROFILES_DIR / "profile.parquet"

print(f"matches Parquet files: {len(matches_parquet_files)}")
print(f"ratings CSV files: {len(ratings_csv_files)}")
print(f"leaderboard.parquet exists: {leaderboard_file.exists()}")
print(f"profile.parquet exists: {profile_file.exists()}")

# %% [markdown]
# ## Cell 4 — Schema discovery
#
# Parquet: full census via `discover_parquet_schemas()` (metadata-only, sub-second).
# CSV: full census via `discover_csv_schema(sample_rows=50)` on each file.
# Singletons: `discover_parquet_schema()`.

# %%
print(f"Running discover_parquet_schemas() on {len(matches_parquet_files)} matches files...")
matches_result = discover_parquet_schemas(matches_parquet_files)
print(
    f"matches: all_same={matches_result['all_files_same_schema']}, "
    f"files_checked={matches_result['files_checked']}, "
    f"variant_cols={matches_result['variant_columns']}"
)

# %%
print(f"Running discover_csv_schemas() on {len(ratings_csv_files)} ratings files...")
ratings_result = discover_csv_schemas(ratings_csv_files, sample_rows=50)
ratings_schemas = ratings_result["schemas"]
ratings_all_same = ratings_result["all_files_same_schema"]
ratings_variant_cols: list[str] = ratings_result["variant_columns"]

print(
    f"ratings CSV files processed: {ratings_result['files_checked']}, "
    f"all_same={ratings_all_same}, "
    f"variant_cols={ratings_variant_cols[:5]}"
)

# %%
leaderboard_schema = discover_parquet_schema(leaderboard_file) if leaderboard_file.exists() else {}
profile_schema = discover_parquet_schema(profile_file) if profile_file.exists() else {}
print(f"leaderboard columns: {leaderboard_schema.get('total_columns', 0)}")
print(f"profile columns: {profile_schema.get('total_columns', 0)}")

# %% [markdown]
# ## Cell 5 — Schema consistency check (summary)

# %%
matches_representative = matches_result["schemas"][0] if matches_result["schemas"] else {}
ratings_representative = ratings_schemas[0] if ratings_schemas else {}

print(f"matches representative schema columns: {matches_representative.get('total_columns', 0)}")
print(f"ratings representative schema columns: {ratings_representative.get('total_columns', 0)}")

# %% [markdown]
# ## Cell 6 — Write JSON artifact

# %%
artifact = {
    "step": "01_01_02",
    "dataset": "aoe2companion",
    "sampling": {
        "strategy": "census",
        "total_files_in_dataset": inventory["total_files"],
        "files_checked": (
            len(matches_parquet_files)
            + ratings_result["files_checked"]
            + (1 if leaderboard_file.exists() else 0)
            + (1 if profile_file.exists() else 0)
        ),
        "method": (
            "Full census for all file types: Parquet metadata-only read "
            "(pyarrow.parquet.read_schema); CSV header + 50 rows per file."
        ),
    },
    "file_types": [
        {
            "type": "parquet",
            "subdirectory": "matches",
            "files_in_subdirectory": len(matches_parquet_files),
            "files_checked": matches_result["files_checked"],
            "schema": {
                "columns": build_column_list(matches_representative),
                "total_columns": matches_representative.get("total_columns", 0),
            },
            "consistency": {
                "all_files_same_schema": matches_result["all_files_same_schema"],
                "variant_columns": matches_result["variant_columns"],
            },
        },
        {
            "type": "csv",
            "subdirectory": "ratings",
            "files_in_subdirectory": len(ratings_csv_files),
            "files_checked": ratings_result["files_checked"],
            "schema": {
                "columns": build_column_list(ratings_representative, col_type_key="inferred_type"),
                "total_columns": ratings_representative.get("total_columns", 0),
            },
            "consistency": {
                "all_files_same_schema": ratings_all_same,
                "variant_columns": ratings_variant_cols,
            },
        },
        {
            "type": "parquet",
            "subdirectory": "leaderboards",
            "files_in_subdirectory": 1,
            "files_checked": 1 if leaderboard_file.exists() else 0,
            "schema": {
                "columns": build_column_list(leaderboard_schema),
                "total_columns": leaderboard_schema.get("total_columns", 0),
            },
            "consistency": {
                "all_files_same_schema": True,
                "variant_columns": [],
            },
        },
        {
            "type": "parquet",
            "subdirectory": "profiles",
            "files_in_subdirectory": 1,
            "files_checked": 1 if profile_file.exists() else 0,
            "schema": {
                "columns": build_column_list(profile_schema),
                "total_columns": profile_schema.get("total_columns", 0),
            },
            "consistency": {
                "all_files_same_schema": True,
                "variant_columns": [],
            },
        },
    ],
}

out_json = ARTIFACTS_DIR / "01_01_02_schema_discovery.json"
with out_json.open("w") as fh:
    json.dump(artifact, fh, indent=2)
logger.info("Wrote JSON artifact: %s", out_json)

# %% [markdown]
# ## Cell 7 — Write Markdown artifact

# %%
md_lines = [
    "# Step 01_01_02 — Schema Discovery: aoe2companion",
    "",
    "**Phase:** 01 — Data Exploration  ",
    "**Pipeline Section:** 01_01 — Data Acquisition & Source Inventory  ",
    "**Dataset:** aoe2companion  ",
    "**Invariants applied:** #6, #7, #9  ",
    "",
    "## Sampling methodology",
    "",
    "Full census for all file types.",
    "",
    "| File type | Subdirectory | Files in dataset | Files checked | Method |",
    "|-----------|-------------|-----------------|--------------|--------|",
    f"| Parquet | `matches/` | {len(matches_parquet_files)} | {matches_result['files_checked']} | metadata-only (pyarrow.parquet.read_schema) |",
    f"| CSV | `ratings/` | {len(ratings_csv_files)} | {ratings_result['files_checked']} | header + 50 rows (discover_csv_schemas) |",
    f"| Parquet | `leaderboards/` | 1 | {1 if leaderboard_file.exists() else 0} | metadata-only |",
    f"| Parquet | `profiles/` | 1 | {1 if profile_file.exists() else 0} | metadata-only |",
    "",
]

md_lines += [
    "## matches/ schema (Parquet)",
    "",
    f"**Total columns:** {matches_representative.get('total_columns', 0)}  ",
    f"**Schema consistency:** {matches_result['all_files_same_schema']}  ",
    "",
]
md_lines += build_schema_table(build_column_list(matches_representative))
md_lines.append("")

md_lines += [
    "## ratings/ schema (CSV)",
    "",
    f"**Total columns:** {ratings_representative.get('total_columns', 0)}  ",
    f"**Schema consistency:** {ratings_all_same}  ",
    "",
]
md_lines += build_schema_table(build_column_list(ratings_representative, col_type_key="inferred_type"))
md_lines.append("")

md_lines += [
    "## leaderboards/ schema (Parquet singleton)",
    "",
    f"**Total columns:** {leaderboard_schema.get('total_columns', 0)}  ",
    "",
]
if leaderboard_schema:
    md_lines += build_schema_table(build_column_list(leaderboard_schema))
md_lines.append("")

md_lines += [
    "## profiles/ schema (Parquet singleton)",
    "",
    f"**Total columns:** {profile_schema.get('total_columns', 0)}  ",
    "",
]
if profile_schema:
    md_lines += build_schema_table(build_column_list(profile_schema))
md_lines.append("")

md_lines += [
    "## Notes",
    "",
    "- No DuckDB type proposals in this step (deferred to ingestion design).",
    "- Step scope: `content` (file headers/schemas).",
]

out_md = ARTIFACTS_DIR / "01_01_02_schema_discovery.md"
out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
logger.info("Wrote Markdown artifact: %s", out_md)
