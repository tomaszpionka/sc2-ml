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
# # Step 01_01_01 — File Inventory: aoe2companion
#
# **Phase:** 01 — Data Exploration
# **Pipeline Section:** 01_01 — Data Acquisition & Source Inventory
# **Dataset:** aoe2companion
# **Question:** What files exist on disk, how many are there, and how are they organized?
#
# This notebook walks the aoe2companion raw directory and counts everything.
# For daily-file subdirectories, it extracts dates from filenames and reports
# date range and gaps.

# %%
import json
import logging
import re
import statistics
from pathlib import Path

from rts_predict.common.inventory import inventory_directory
from rts_predict.common.notebook_utils import get_reports_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# %%
from rts_predict.aoe2.config import AOE2COMPANION_RAW_DIR

RAW_DIR: Path = AOE2COMPANION_RAW_DIR
ARTIFACTS_DIR: Path = get_reports_dir("aoe2", "aoe2companion") / "artifacts" / "01_01"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

logger.info("Raw directory: %s", RAW_DIR)
logger.info("Artifacts directory: %s", ARTIFACTS_DIR)

# %%
result = inventory_directory(RAW_DIR)

logger.info("Total files: %d", result.total_files)
logger.info("Total size: %.2f MB", result.total_bytes / (1024 * 1024))
logger.info("Subdirectories: %d", len(result.subdirs))
logger.info("Files at root: %d", len(result.files_at_root))

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
    logger.info("Files per subdir — min: %d, max: %d, median: %.1f",
                min(file_counts), max(file_counts), statistics.median(file_counts))

# %%
from datetime import date, timedelta

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
        logger.info("Subdir %s: %s to %s (%d files, %d gaps)",
                     sd.name, dates_found[0], dates_found[-1],
                     len(dates_found), len(gaps))
    else:
        logger.info("Subdir %s: no dates extracted from filenames", sd.name)

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

md_path = ARTIFACTS_DIR / "01_01_01_file_inventory.md"
md_path.write_text("\n".join(lines) + "\n")
logger.info("Markdown artifact written: %s", md_path)

# %% [markdown]
# ## Verification
#
# The artifacts have been written. The counts above ARE the authoritative
# inventory — they are not compared against any prior documentation.
