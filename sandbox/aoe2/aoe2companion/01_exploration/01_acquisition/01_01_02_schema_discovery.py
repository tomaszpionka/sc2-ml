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
import logging
from pathlib import Path

from rts_predict.common.parquet_utils import discover_parquet_schema, discover_parquet_schemas, discover_csv_schema
from rts_predict.common.notebook_utils import get_reports_dir
from rts_predict.games.aoe2.config import (
    AOE2COMPANION_RAW_DIR,
    AOE2COMPANION_RAW_MATCHES_DIR,
    AOE2COMPANION_RAW_LEADERBOARDS_DIR,
    AOE2COMPANION_RAW_PROFILES_DIR,
    AOE2COMPANION_RAW_RATINGS_DIR,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
logger.info("Subdirectories: %s", subdir_counts)

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

logger.info("matches Parquet files: %d", len(matches_parquet_files))
logger.info("ratings CSV files: %d", len(ratings_csv_files))
logger.info("leaderboard.parquet exists: %s", leaderboard_file.exists())
logger.info("profile.parquet exists: %s", profile_file.exists())

# %% [markdown]
# ## Cell 4 — Schema discovery
#
# Parquet: full census via `discover_parquet_schemas()` (metadata-only, sub-second).
# CSV: full census via `discover_csv_schema(sample_rows=50)` on each file.
# Singletons: `discover_parquet_schema()`.

# %%
logger.info("Running discover_parquet_schemas() on %d matches files...", len(matches_parquet_files))
matches_result = discover_parquet_schemas(matches_parquet_files)
logger.info(
    "matches: all_same=%s, files_checked=%d, variant_cols=%s",
    matches_result["all_files_same_schema"],
    matches_result["files_checked"],
    matches_result["variant_columns"],
)

# %%
logger.info("Running discover_csv_schema() on %d ratings files...", len(ratings_csv_files))
ratings_schemas = []
ratings_errors = 0
for fp in ratings_csv_files:
    try:
        ratings_schemas.append(discover_csv_schema(fp, sample_rows=50))
    except Exception as exc:
        ratings_errors += 1
        logger.warning("CSV error for %s: %s", fp, exc)

logger.info("ratings CSV files processed: %d (errors: %d)", len(ratings_schemas), ratings_errors)

# %%
# Check ratings schema consistency
if len(ratings_schemas) > 1:
    ref_cols = [(c["name"], c["inferred_type"]) for c in ratings_schemas[0]["columns"]]
    ratings_variant_cols: list[str] = []
    for s in ratings_schemas[1:]:
        s_cols = [(c["name"], c["inferred_type"]) for c in s["columns"]]
        if s_cols != ref_cols:
            s_names = {c["name"] for c in s["columns"]}
            ref_names = {c[0] for c in ref_cols}
            ratings_variant_cols.extend(s_names.symmetric_difference(ref_names))
    ratings_all_same = len(ratings_variant_cols) == 0
else:
    ratings_all_same = True
    ratings_variant_cols = []

logger.info("ratings consistency: all_same=%s, variant_cols=%s", ratings_all_same, ratings_variant_cols[:5])

# %%
leaderboard_schema = discover_parquet_schema(leaderboard_file) if leaderboard_file.exists() else {}
profile_schema = discover_parquet_schema(profile_file) if profile_file.exists() else {}
logger.info("leaderboard columns: %d", leaderboard_schema.get("total_columns", 0))
logger.info("profile columns: %d", profile_schema.get("total_columns", 0))

# %% [markdown]
# ## Cell 5 — Schema consistency check (summary)

# %%
matches_representative = matches_result["schemas"][0] if matches_result["schemas"] else {}
ratings_representative = ratings_schemas[0] if ratings_schemas else {}

logger.info("matches representative schema columns: %d", matches_representative.get("total_columns", 0))
logger.info("ratings representative schema columns: %d", ratings_representative.get("total_columns", 0))

# %% [markdown]
# ## Cell 6 — Write JSON artifact

# %%
def build_column_list(schema_dict: dict, col_type_key: str = "arrow_type") -> list[dict]:
    return [
        {
            "name": c["name"],
            "physical_type": c.get(col_type_key, c.get("inferred_type", "")),
            "nullable": c.get("nullable", False),
        }
        for c in schema_dict.get("columns", [])
    ]


artifact = {
    "step": "01_01_02",
    "dataset": "aoe2companion",
    "sampling": {
        "strategy": "census",
        "total_files_in_dataset": inventory["total_files"],
        "files_checked": (
            len(matches_parquet_files)
            + len(ratings_csv_files)
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
            "files_checked": len(ratings_schemas),
            "schema": {
                "columns": build_column_list(ratings_representative, col_type_key="inferred_type"),
                "total_columns": ratings_representative.get("total_columns", 0),
            },
            "consistency": {
                "all_files_same_schema": ratings_all_same,
                "variant_columns": sorted(set(ratings_variant_cols)),
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
def build_schema_table(columns: list[dict], type_key: str = "physical_type") -> list[str]:
    lines = [
        "| Column | Type | Nullable |",
        "|--------|------|----------|",
    ]
    for c in columns:
        lines.append(f"| `{c['name']}` | {c.get(type_key, '')} | {c.get('nullable', '')} |")
    return lines


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
    f"| CSV | `ratings/` | {len(ratings_csv_files)} | {len(ratings_schemas)} | header + 50 rows (pd.read_csv) |",
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
