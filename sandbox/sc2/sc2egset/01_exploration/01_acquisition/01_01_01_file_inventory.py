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
# **Invariants applied:** #6 (reproducibility), #7 (no magic numbers)
# **ROADMAP reference:** `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md` Step 01_01_01
# **Commit:** 0a77634
#
# This notebook walks the sc2egset raw directory and counts everything.
# It does NOT compare against any expected counts — it produces the counts
# for the first time. The raw directory has a two-level structure:
# `raw/TOURNAMENT_NAME/TOURNAMENT_NAME_data/*.SC2Replay.json`.
# The top level also contains metadata files (`.zip`, `.log`, `.json`, no-extension).
# Both levels are inventoried.

# %%
import json
import logging
import statistics
from pathlib import Path

from rts_predict.common.inventory import inventory_directory
from rts_predict.common.notebook_utils import get_reports_dir
from rts_predict.common.filename_patterns import summarize_filename_patterns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# %%
from rts_predict.sc2.config import REPLAYS_SOURCE_DIR

RAW_DIR: Path = REPLAYS_SOURCE_DIR
ARTIFACTS_DIR: Path = get_reports_dir("sc2", "sc2egset") / "artifacts" / "01_exploration" / "01_acquisition"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

logger.info("Source directory: %s", RAW_DIR)
logger.info("Artifacts directory: %s", ARTIFACTS_DIR)

# %%
# Level 1 inventory: RAW_DIR -> tournament directories (metadata files only)
# Each tournament dir contains: .zip, .log, .json metadata, and a _data/ subdir.
# inventory_directory goes one level deep, so it counts metadata files per tournament.
meta_result = inventory_directory(RAW_DIR)

logger.info("Tournament directories (level 1): %d", len(meta_result.subdirs))
logger.info("Metadata files across all tournaments: %d", meta_result.total_files)
logger.info("Files at root: %d", len(meta_result.files_at_root))

# %% [markdown]
# ### Level 1 inventory
#
# The level 1 scan of the raw directory reveals the tournament directory structure
# and metadata file counts. Each tournament directory contains auxiliary files
# (.zip archives, .log files, metadata .json) alongside a `_data/` subdirectory
# holding the actual replay files. This cell establishes the top-level counts
# before drilling into replay-level detail.

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

# %% [markdown]
# ### Level 2 inventory — replay files
#
# The level 2 scan enters each tournament's `_data/` subdirectory and counts
# replay files. The total replay file count and cumulative size establish the
# authoritative source counts for all downstream steps. Any tournament missing
# its `_data/` directory is flagged as a warning — these gaps must be acknowledged
# in the data cleaning phase.

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

# %% [markdown]
# ### Replay distribution across tournaments
#
# The summary statistics (min, max, median replays per tournament) characterise
# the size distribution of the corpus. Tournaments with zero replay files are
# flagged explicitly — these are not data errors but may indicate incomplete
# extraction or metadata-only directories.

# %%
# Whole-tree filename pattern summary across both inventory levels.
# Level 1 (meta_result): root files + tournament-level metadata files.
all_files = list(meta_result.files_at_root)
all_files.extend(f for sd in meta_result.subdirs for f in sd.files)
# Level 2: re-scan each _data/ subdir to collect replay FileEntry objects.
# (cell_06 built summary dicts but did not retain FileEntry objects.)
for sd in meta_result.subdirs:
    data_dir = RAW_DIR / sd.name / (sd.name + "_data")
    if not data_dir.exists():
        continue
    replay_inv = inventory_directory(data_dir)
    all_files.extend(replay_inv.files_at_root)
    all_files.extend(f for rsd in replay_inv.subdirs for f in rsd.files)

patterns = summarize_filename_patterns(all_files)

logger.info("Total files scanned for patterns: %d", len(all_files))
for pattern, count in patterns.items():
    logger.info("  %s: %d", pattern, count)

# %% [markdown]
# ### Filename pattern summary
#
# The whole-tree pattern summary groups every file in the sc2egset `raw/`
# tree by its abstract naming pattern — spanning both the tournament-level
# metadata files and the `_data/` subdirectory replay files. This reveals
# the full file taxonomy: replay JSONs (`{hash}.SC2Replay.json`), metadata
# archives, processing trackers, and any housekeeping files (`.gitkeep`).
# No files are excluded from this count.

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
    "filename_patterns": dict(patterns),
    "total_files_scanned": len(all_files),
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

lines.extend(["\n## Filename patterns\n"])
lines.append(f"Total files scanned: {len(all_files)}\n")
lines.append("| Pattern | Count |")
lines.append("|---|---|")
for pattern, count in patterns.items():
    lines.append(f"| `{pattern}` | {count} |")

if tournaments_missing_data_dir:
    lines.extend([
        "\n## Tournaments with no _data directory\n",
        *[f"- {t}" for t in tournaments_missing_data_dir],
    ])

md_path = ARTIFACTS_DIR / "01_01_01_file_inventory.md"
md_path.write_text("\n".join(lines) + "\n")
logger.info("Markdown artifact written: %s", md_path)

# %% [markdown]
# ### Artifact output
#
# Both the structured JSON artifact and the human-readable Markdown report have
# been written to the artifacts directory. These are the authoritative inventory
# records for all downstream steps. Per Invariant #6, the code that produced
# each number is traceable via the paired `.ipynb` notebook.

# %% [markdown]
# ## Conclusion
#
# ### Artifacts produced
# - `src/rts_predict/sc2/reports/sc2egset/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json` — structured inventory with per-tournament breakdown
# - `src/rts_predict/sc2/reports/sc2egset/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md` — human-readable inventory report
#
# ### Thesis mapping
# - Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)
#
# ### Follow-ups
# - Step 01_01_02 (if defined) or Step 01_02_01: profile the replay JSON schema and field completeness
# - Any tournaments flagged with missing `_data/` directories need acknowledgement in data cleaning (Section 01_04)
