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
# # Step 01_01_01 — File Inventory: aoe2companion
#
# **Phase:** 01 — Data Exploration
# **Pipeline Section:** 01_01 — Data Acquisition & Source Inventory
# **Dataset:** aoe2companion
# **Question:** What files exist on disk, how many are there, and how are they organized?
# **Invariants applied:** #6 (reproducibility), #7 (no magic numbers)
# **ROADMAP reference:** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` Step 01_01_01
# **Commit:** 0a77634
#
# This notebook walks the aoe2companion raw directory and counts everything.
# For daily-file subdirectories, it extracts dates from filenames and reports
# date range and gaps. The raw directory contains four subdirectories (matches,
# ratings, leaderboards, profiles), each holding daily Parquet snapshots.

# %%
import json
import logging
import re
import statistics
from datetime import date
from pathlib import Path

from rts_predict.common.filename_patterns import summarize_filename_patterns
from rts_predict.common.inventory import inventory_directory
from rts_predict.common.notebook_utils import get_reports_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# %%
from rts_predict.games.aoe2.config import AOE2COMPANION_RAW_DIR

RAW_DIR: Path = AOE2COMPANION_RAW_DIR
ARTIFACTS_DIR: Path = get_reports_dir("aoe2", "aoe2companion") / "artifacts" / "01_exploration" / "01_acquisition"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

logger.info("Source directory: %s", RAW_DIR)
logger.info("Artifacts directory: %s", ARTIFACTS_DIR)

# %%
result = inventory_directory(RAW_DIR)

print(f"Total files: {result.total_files}")
print(f"Total size: {result.total_bytes / (1024 * 1024):.2f} MB")
print(f"Subdirectories: {len(result.subdirs)}")
print(f"Files at root: {len(result.files_at_root)}")

# %% [markdown]
# ### Top-level inventory
#
# The raw directory scan reveals the subdirectory structure and total file counts.
# The aoe2companion dataset is organised into four subdirectories (matches, ratings,
# leaderboards, profiles), each containing daily Parquet snapshots. The total file
# count and size establish the baseline for downstream processing steps.

# %%
subdir_data = []
for sd in result.subdirs:
    subdir_data.append({
        "name": sd.name,
        "file_count": sd.file_count,
        "total_bytes": sd.total_bytes,
        "total_mb": round(sd.total_bytes / (1024 * 1024), 2),
        "extensions": sd.extensions,
    })

file_counts = [sd.file_count for sd in result.subdirs]
if file_counts:
    print(f"Files per subdir — min: {min(file_counts)}, max: {max(file_counts)}, median: {statistics.median(file_counts):.1f}")

# %% [markdown]
# ### Per-subdirectory file counts
#
# The breakdown shows file counts and sizes for each subdirectory. The variance
# in file counts across subdirectories reflects the different granularity and
# retention policies of each data category (matches vs ratings vs snapshots).

# %%
# Try to extract dates from filenames in each subdirectory.
# We discover the date pattern — we do NOT assume a format.
# Common patterns: YYYY-MM-DD, YYYYMMDD embedded in filenames.
DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")

date_analysis = {}
for sd in result.subdirs:
    dates_found: list[date] = []
    for f in sd.files:
        match = DATE_PATTERN.search(f.path.stem)
        if match:
            try:
                dates_found.append(date.fromisoformat(match.group(1)))
            except ValueError:
                pass
    if dates_found:
        dates_found.sort()
        # Find gaps: consecutive dates with more than 1 day between them
        gaps = []
        for i in range(1, len(dates_found)):
            delta = (dates_found[i] - dates_found[i - 1]).days
            if delta > 1:
                gaps.append({
                    "after": str(dates_found[i - 1]),
                    "before": str(dates_found[i]),
                    "gap_days": delta,
                })
        date_analysis[sd.name] = {
            "earliest": str(dates_found[0]),
            "latest": str(dates_found[-1]),
            "count": len(dates_found),
            "gaps": gaps,
        }
        print(f"Subdir {sd.name}: {dates_found[0]} to {dates_found[-1]} ({len(dates_found)} files, {len(gaps)} gaps)")
    else:
        print(f"Subdir {sd.name}: no dates extracted from filenames")

# %% [markdown]
# ### Date range and gap analysis
#
# Date extraction from filenames reveals the temporal coverage of each
# subdirectory. Gaps between consecutive dates indicate missing daily snapshots.
# These gaps are recorded in the artifact for acknowledgement during data cleaning
# (Section 01_04). Subdirectories without date-patterned filenames (e.g., snapshot
# tables) are noted separately.

# %%
# Whole-tree filename pattern summary.
# Collect ALL FileEntry objects from the entire raw/ tree into one flat list.
all_files = result.files_at_root + [f for sd in result.subdirs for f in sd.files]
patterns = summarize_filename_patterns(all_files)

print(f"Total files scanned for patterns: {len(all_files)}")
for pattern, count in patterns.items():
    print(f"  {pattern}: {count}")

# %% [markdown]
# ### Filename pattern summary
#
# The whole-tree pattern summary groups every file in `raw/` by its abstract
# naming pattern — dates replaced with `{date}`, hex hashes with `{hash}`,
# numeric IDs with `{N}`. This reveals the naming conventions across all
# subdirectories without excluding any files. Housekeeping files (`.gitkeep`,
# ingestion trackers) appear alongside data files in the same table.

# %%
artifact = {
    "step": "01_01_01",
    "dataset": "aoe2companion",
    "raw_dir": str(RAW_DIR),
    "total_files": result.total_files,
    "total_bytes": result.total_bytes,
    "num_subdirs": len(result.subdirs),
    "files_at_root": len(result.files_at_root),
    "subdirs": subdir_data,
    "date_analysis": date_analysis,
    "filename_patterns": dict(patterns),
    "total_files_scanned": len(all_files),
}

json_path = ARTIFACTS_DIR / "01_01_01_file_inventory.json"
json_path.write_text(json.dumps(artifact, indent=2, default=str))
logger.info("JSON artifact written: %s", json_path)

# %%
lines = [
    "# Step 01_01_01 — File Inventory: aoe2companion\n",
    f"**Raw directory:** `{RAW_DIR}`\n",
    f"**Total files:** {result.total_files}\n",
    f"**Total size:** {result.total_bytes / (1024**2):.2f} MB\n",
    f"**Subdirectories:** {len(result.subdirs)}\n",
    f"**Files at root level:** {len(result.files_at_root)}\n",
    "\n## Per-subdirectory breakdown\n",
    "| Subdirectory | Files | Size (MB) | Extensions |",
    "|---|---|---|---|",
]
for sd in subdir_data:
    ext_str = ", ".join(f"{k}: {v}" for k, v in sorted(sd["extensions"].items()))
    lines.append(f"| {sd['name']} | {sd['file_count']} | {sd['total_mb']} | {ext_str} |")

if date_analysis:
    lines.extend(["\n## Date range analysis\n"])
    for name, info in sorted(date_analysis.items()):
        lines.append(f"### {name}\n")
        lines.append(f"- Date range: {info['earliest']} to {info['latest']}")
        lines.append(f"- Files with dates: {info['count']}")
        if info["gaps"]:
            lines.append(f"- Gaps found: {len(info['gaps'])}")
            for g in info["gaps"]:
                lines.append(f"  - {g['after']} -> {g['before']} ({g['gap_days']} days)")
        else:
            lines.append("- No gaps found")
        lines.append("")

lines.extend(["\n## Filename patterns\n"])
lines.append(f"Total files scanned: {len(all_files)}\n")
lines.append("| Pattern | Count |")
lines.append("|---|---|")
for pattern, count in patterns.items():
    lines.append(f"| `{pattern}` | {count} |")

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
# - `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json` — structured inventory with per-subdirectory breakdown and date analysis
# - `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md` — human-readable inventory report
#
# ### Thesis mapping
# - Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data
#
# ### Follow-ups
# - Step 01_01_02 (if defined) or Step 01_02_01: profile the Parquet schema and field completeness for each subdirectory
# - Date gaps identified in the inventory must be acknowledged during data cleaning (Section 01_04)
# - Sparse rating regime (pre-2025-06-26) flagged in ROADMAP must be verified against the date range found here
