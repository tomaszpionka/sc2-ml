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
# # Step 01_01_01 — File Inventory: sc2egset
#
# **Phase:** 01 — Data Exploration
# **Pipeline Section:** 01_01 — Data Acquisition & Source Inventory
# **Dataset:** sc2egset
# **Question:** What files exist on disk, how many are there, and how are they organized?
#
# This notebook walks the sc2egset raw directory and counts everything.
# It does NOT compare against any expected counts — it produces the counts
# for the first time.
#
# **Layout note:** The raw directory has a two-level structure:
# `raw/TOURNAMENT_NAME/TOURNAMENT_NAME_data/*.SC2Replay.json`
# The top level (`raw/TOURNAMENT/`) also contains metadata files
# (`.zip`, `.log`, `.json`, no-extension). Both levels are inventoried.

# %%
import json
import logging
import statistics
from pathlib import Path

from rts_predict.common.inventory import inventory_directory
from rts_predict.common.notebook_utils import get_reports_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# %%
# Paths — derived from project config, not hardcoded
from rts_predict.sc2.config import REPLAYS_SOURCE_DIR

RAW_DIR: Path = REPLAYS_SOURCE_DIR
ARTIFACTS_DIR: Path = get_reports_dir("sc2", "sc2egset") / "artifacts" / "01_01"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

logger.info("Raw directory: %s", RAW_DIR)
logger.info("Artifacts directory: %s", ARTIFACTS_DIR)

# %%
# Level 1 inventory: RAW_DIR -> tournament directories (metadata files only)
# Each tournament dir contains: .zip, .log, .json metadata, and a _data/ subdir.
# inventory_directory goes one level deep, so it counts metadata files per tournament.
meta_result = inventory_directory(RAW_DIR)

logger.info("Tournament directories (level 1): %d", len(meta_result.subdirs))
logger.info("Metadata files across all tournaments: %d", meta_result.total_files)
logger.info("Files at root: %d", len(meta_result.files_at_root))

# %%
# Level 2 inventory: for each tournament, scan its _data/ subdir for replay files.
# The _data/ subdir is named TOURNAMENT_NAME_data and contains *.SC2Replay.json files.
replay_subdir_data = []
total_replay_files = 0
total_replay_bytes = 0
tournaments_missing_data_dir = []

for sd in meta_result.subdirs:
    data_dir = RAW_DIR / sd.name / (sd.name + "_data")
    if not data_dir.exists():
        logger.warning("No _data dir for tournament: %s", sd.name)
        tournaments_missing_data_dir.append(sd.name)
        continue
    replay_inv = inventory_directory(data_dir)
    total_replay_files += replay_inv.total_files
    total_replay_bytes += replay_inv.total_bytes
    ext_dist = {}
    for f in replay_inv.files_at_root:
        ext_dist[f.extension] = ext_dist.get(f.extension, 0) + 1
    replay_subdir_data.append({
        "name": sd.name,
        "replay_file_count": replay_inv.total_files,
        "total_bytes": replay_inv.total_bytes,
        "total_mb": round(replay_inv.total_bytes / (1024 * 1024), 2),
        "extensions": ext_dist,
    })

logger.info("Total replay files (level 2): %d", total_replay_files)
logger.info("Total replay size: %.2f MB", total_replay_bytes / (1024 * 1024))
if tournaments_missing_data_dir:
    logger.warning("Tournaments with no _data dir: %s", tournaments_missing_data_dir)

# %%
# Summary statistics for replay file counts per tournament
replay_counts = [sd["replay_file_count"] for sd in replay_subdir_data]
if replay_counts:
    logger.info(
        "Replays per tournament — min: %d, max: %d, median: %.1f, total: %d",
        min(replay_counts),
        max(replay_counts),
        statistics.median(replay_counts),
        sum(replay_counts),
    )

# Flag tournaments with 0 replay files
for sd in replay_subdir_data:
    if sd["replay_file_count"] == 0:
        logger.warning("Tournament with 0 replay files: %s", sd["name"])

# %%
artifact = {
    "step": "01_01_01",
    "dataset": "sc2egset",
    "raw_dir": str(RAW_DIR),
    "layout": "two-level: raw/TOURNAMENT/TOURNAMENT_data/*.SC2Replay.json",
    "num_tournament_dirs": len(meta_result.subdirs),
    "files_at_root": len(meta_result.files_at_root),
    "metadata_files_total": meta_result.total_files,
    "total_replay_files": total_replay_files,
    "total_replay_bytes": total_replay_bytes,
    "tournaments_missing_data_dir": tournaments_missing_data_dir,
    "tournaments": replay_subdir_data,
}

json_path = ARTIFACTS_DIR / "01_01_01_file_inventory.json"
json_path.write_text(json.dumps(artifact, indent=2, default=str))
logger.info("JSON artifact written: %s", json_path)

# %%
lines = [
    "# Step 01_01_01 — File Inventory: sc2egset\n",
    f"**Raw directory:** `{RAW_DIR}`\n",
    f"**Layout:** `raw/TOURNAMENT/TOURNAMENT_data/*.SC2Replay.json`\n",
    f"**Tournament directories:** {len(meta_result.subdirs)}\n",
    f"**Total replay files:** {total_replay_files}\n",
    f"**Total replay size:** {total_replay_bytes / (1024**2):.2f} MB\n",
    f"**Metadata files (zip/log/json at tournament level):** {meta_result.total_files}\n",
    f"**Files at root level:** {len(meta_result.files_at_root)}\n",
]

if replay_counts:
    lines.extend([
        "\n## Summary statistics (replays per tournament)\n",
        f"- Min: {min(replay_counts)}",
        f"- Max: {max(replay_counts)}",
        f"- Median: {statistics.median(replay_counts):.1f}",
    ])

lines.extend([
    "\n## Per-tournament breakdown\n",
    "| Tournament | Replay Files | Size (MB) | Extensions |",
    "|---|---|---|---|",
])
for sd in replay_subdir_data:
    ext_str = ", ".join(f"{k}: {v}" for k, v in sorted(sd["extensions"].items()))
    lines.append(
        f"| {sd['name']} | {sd['replay_file_count']} | {sd['total_mb']} | {ext_str} |"
    )

if tournaments_missing_data_dir:
    lines.extend([
        "\n## Tournaments with no _data directory\n",
        *[f"- {t}" for t in tournaments_missing_data_dir],
    ])

md_path = ARTIFACTS_DIR / "01_01_01_file_inventory.md"
md_path.write_text("\n".join(lines) + "\n")
logger.info("Markdown artifact written: %s", md_path)

# %% [markdown]
# ## Verification
#
# The artifacts have been written. The counts above ARE the authoritative
# inventory — they are not compared against any prior documentation.
