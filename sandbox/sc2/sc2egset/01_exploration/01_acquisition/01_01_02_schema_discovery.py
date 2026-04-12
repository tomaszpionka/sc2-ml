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
# # Step 01_01_02 — Schema Discovery: sc2egset
#
# **Phase:** 01 — Data Exploration
# **Pipeline Section:** 01_01 — Data Acquisition & Source Inventory
# **Dataset:** sc2egset
# **Question:** What is the internal structure of the SC2EGSet JSON files, and is this structure consistent across all 70 directories?
# **Invariants applied:** #6 (reproducibility), #7 (no magic numbers), #9 (pipeline discipline)
# **ROADMAP reference:** `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` Step 01_01_02
#
# Reads 1 file per directory (first alphabetically) for root schema via
# `discover_json_schema()` and 3 files per directory for full keypath
# enumeration via `get_json_keypaths()`. No DuckDB type proposals.

# %% [markdown]
# ## Cell 1 — Imports, config, paths

# %%
import json
import logging
from pathlib import Path

from rts_predict.common.json_utils import discover_json_schema, get_json_keypaths
from rts_predict.common.notebook_utils import get_reports_dir
from rts_predict.games.sc2.config import REPLAYS_SOURCE_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAW_DIR: Path = REPLAYS_SOURCE_DIR
ARTIFACTS_DIR: Path = (
    get_reports_dir("sc2", "sc2egset")
    / "artifacts"
    / "01_exploration"
    / "01_acquisition"
)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
PRIOR_ARTIFACT: Path = ARTIFACTS_DIR / "01_01_01_file_inventory.json"

logger.info("RAW_DIR: %s", RAW_DIR)
logger.info("ARTIFACTS_DIR: %s", ARTIFACTS_DIR)

# %% [markdown]
# ## Cell 2 — Load 01_01_01 artifact to get directory list

# %%
with PRIOR_ARTIFACT.open() as fh:
    inventory = json.load(fh)

top_level_dirs = [d["name"] for d in inventory["top_level_dirs"]]
logger.info("Loaded %d top-level directories from prior artifact", len(top_level_dirs))
logger.info("First 3 dirs: %s", top_level_dirs[:3])

# %% [markdown]
# ## Cell 3 — Sampling / file selection (deterministic)
#
# Root schema: 1 file per directory (first alphabetically) → 70 files total.
# Keypath enumeration: 3 files per directory (first 3 alphabetically) → up to 210 files total.

# %%
root_schema_files: list[Path] = []
keypath_files: list[Path] = []

for dir_name in sorted(top_level_dirs):
    data_dir = RAW_DIR / dir_name / (dir_name + "_data")
    if not data_dir.exists():
        logger.warning("Missing _data/ subdir for: %s", dir_name)
        continue
    json_files = sorted(f for f in data_dir.iterdir() if f.suffix == ".json")
    if not json_files:
        logger.warning("No JSON files in: %s", data_dir)
        continue
    root_schema_files.append(json_files[0])
    keypath_files.extend(json_files[:3])

logger.info("root_schema_files selected: %d", len(root_schema_files))
logger.info("keypath_files selected: %d", len(keypath_files))

# %% [markdown]
# ## Cell 4 — Schema discovery
#
# Root-level key catalog via `discover_json_schema()`.
# Full keypath enumeration via `get_json_keypaths()` on the keypath sample.

# %%
logger.info("Running discover_json_schema() on %d files...", len(root_schema_files))
key_profiles = discover_json_schema(root_schema_files, max_sample_values=3)
logger.info("Root-level keys discovered: %d", len(key_profiles))

# %%
logger.info("Running get_json_keypaths() on %d files...", len(keypath_files))
all_keypaths: set[str] = set()
keypath_parse_errors = 0
for fp in keypath_files:
    try:
        paths = get_json_keypaths(fp)
        all_keypaths.update(paths)
    except Exception as exc:
        keypath_parse_errors += 1
        logger.warning("Keypath parse error for %s: %s", fp, exc)

sorted_keypaths = sorted(all_keypaths)
logger.info("Unique keypaths discovered: %d (parse errors: %d)", len(sorted_keypaths), keypath_parse_errors)

# %% [markdown]
# ## Cell 5 — Schema consistency check
#
# Compare root-level key sets across all 70 directories.
# Directories are temporal strata (2016-2024), so variation would indicate
# era-dependent schema evolution.

# %%
per_dir_key_sets: dict[str, set[str]] = {}
for fp in root_schema_files:
    dir_name = fp.parent.parent.name
    try:
        with fp.open() as fh:
            obj = json.load(fh)
        per_dir_key_sets[dir_name] = set(obj.keys()) if isinstance(obj, dict) else set()
    except Exception as exc:
        logger.warning("Cannot read keys from %s: %s", fp, exc)

all_key_sets = list(per_dir_key_sets.values())
if all_key_sets:
    reference_keys = all_key_sets[0]
    variant_dirs = [
        d for d, ks in per_dir_key_sets.items() if ks != reference_keys
    ]
    all_files_same_schema = len(variant_dirs) == 0
else:
    all_files_same_schema = True
    variant_dirs = []

logger.info(
    "Schema consistency: all_same=%s, variant_dirs_count=%d",
    all_files_same_schema,
    len(variant_dirs),
)
if variant_dirs:
    logger.info("Variant directories: %s", variant_dirs[:10])

# %% [markdown]
# ## Cell 6 — Write JSON artifact

# %%
columns_out = []
for kp in key_profiles:
    col_entry = {
        "name": kp.key,
        "physical_type": sorted(kp.observed_types)[0] if len(kp.observed_types) == 1 else sorted(kp.observed_types),
        "nullable": kp.nullable,
        "frequency": kp.frequency,
        "total_samples": kp.total_samples,
        "sample_values": kp.sample_values,
    }
    columns_out.append(col_entry)

artifact = {
    "step": "01_01_02",
    "dataset": "sc2egset",
    "sampling": {
        "strategy": "systematic_temporal_stratified",
        "total_files_in_dataset": inventory["total_replay_files"],
        "files_checked_root_schema": len(root_schema_files),
        "files_checked_keypaths": len(keypath_files),
        "method": (
            "1 file per directory (first alphabetically) for root schema; "
            "3 files per directory (first 3 alphabetically) for keypath enumeration. "
            "All 70 directories represented."
        ),
    },
    "file_types": [
        {
            "type": "json",
            "subdirectory": "TOURNAMENT_data",
            "files_in_subdirectory": inventory["total_replay_files"],
            "files_checked": len(root_schema_files),
            "schema": {
                "columns": columns_out,
                "total_columns": len(columns_out),
                "nesting_depth": max(p.count(".") + 1 for p in sorted_keypaths) if sorted_keypaths else 0,
                "keypaths": sorted_keypaths,
            },
            "consistency": {
                "all_files_same_schema": all_files_same_schema,
                "variant_dirs": variant_dirs if not all_files_same_schema else [],
            },
        }
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
    "# Step 01_01_02 — Schema Discovery: sc2egset",
    "",
    "**Phase:** 01 — Data Exploration  ",
    "**Pipeline Section:** 01_01 — Data Acquisition & Source Inventory  ",
    "**Dataset:** sc2egset  ",
    "**Invariants applied:** #6, #7, #9  ",
    "",
    "## Sampling methodology",
    "",
    "| Parameter | Value |",
    "|-----------|-------|",
    f"| Strategy | systematic temporal stratification (1 file/dir for root schema, 3 files/dir for keypaths) |",
    f"| Directories | {inventory['num_top_level_dirs']} |",
    f"| Files selected (root schema) | {len(root_schema_files)} |",
    f"| Files selected (keypaths) | {len(keypath_files)} |",
    f"| Total files in dataset | {inventory['total_replay_files']} |",
    "",
    "File selection is deterministic: first N files alphabetically per `_data/` directory.",
    "",
    "## Root-level key catalog (JSON schema)",
    "",
    "| Key | Observed types | Nullable | Frequency / Total |",
    "|-----|----------------|----------|-------------------|",
]

for kp in key_profiles:
    type_str = ", ".join(sorted(kp.observed_types))
    md_lines.append(
        f"| `{kp.key}` | {type_str} | {kp.nullable} | {kp.frequency} / {kp.total_samples} |"
    )

md_lines += [
    "",
    "## Full keypath tree",
    "",
    f"Total unique keypaths: {len(sorted_keypaths)}",
    "",
    "```",
]
md_lines.extend(sorted_keypaths[:200])
if len(sorted_keypaths) > 200:
    md_lines.append(f"... ({len(sorted_keypaths) - 200} more keypaths truncated)")
md_lines.append("```")

md_lines += [
    "",
    "## Schema consistency",
    "",
    f"**All 70 directories share the same root-level schema:** {all_files_same_schema}",
    "",
]
if not all_files_same_schema:
    md_lines.append(f"**Variant directories ({len(variant_dirs)}):**")
    for vd in variant_dirs:
        md_lines.append(f"- {vd}")
    md_lines.append("")

md_lines += [
    "## Notes",
    "",
    "- No DuckDB type proposals in this step (deferred to ingestion design).",
    "- Sample values in the JSON artifact are for type-inference validation only.",
    "- Step scope: `content` (file headers/schemas/sample root keys).",
]

out_md = ARTIFACTS_DIR / "01_01_02_schema_discovery.md"
out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
logger.info("Wrote Markdown artifact: %s", out_md)
