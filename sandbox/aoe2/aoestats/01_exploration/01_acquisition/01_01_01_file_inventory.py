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
# # Step 01_01_01 — File Inventory: aoestats
#
# **Phase:** 01 — Data Exploration
# **Pipeline Section:** 01_01 — Data Acquisition & Source Inventory
# **Dataset:** aoestats
# **Question:** What files exist on disk, how many are there, and how are they organized?
# **Invariants applied:** #6 (reproducibility), #7 (no magic numbers)
# **ROADMAP reference:** `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` Step 01_01_01
# **Commit:** 0a77634
#
# This notebook walks the aoestats raw directory and counts everything.
# For weekly-file subdirectories, it extracts date ranges from filenames
# and checks whether paired directories (matches and players) have matching
# file counts and date ranges. The raw directory contains paired weekly
# Parquet files where each file covers a one-week date span.

# %%
import json
import re
import statistics
from datetime import date
from pathlib import Path

from rts_predict.common.inventory import inventory_directory
from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.common.filename_patterns import summarize_filename_patterns

logger = setup_notebook_logging()

# %%
from rts_predict.games.aoe2.config import AOESTATS_RAW_DIR

RAW_DIR: Path = AOESTATS_RAW_DIR
ARTIFACTS_DIR: Path = get_reports_dir("aoe2", "aoestats") / "artifacts" / "01_exploration" / "01_acquisition"
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
# The aoestats dataset is organised into paired weekly Parquet files across
# subdirectories (matches and players). The total file count and size establish
# the baseline for downstream processing steps.

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
# The breakdown shows file counts and sizes for each subdirectory. Since matches
# and players directories are expected to be paired (one file per week per
# directory), count discrepancies signal missing files that must be acknowledged
# in data cleaning.

# %%
# aoestats files are named like: 2024-01-01_2024-01-07_matches.parquet
# Extract start_date and end_date from each filename.
WEEK_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})")

date_analysis = {}
for sd in result.subdirs:
    weeks: list[tuple[date, date]] = []
    for f in sd.files:
        match = WEEK_PATTERN.search(f.path.stem)
        if match:
            try:
                start = date.fromisoformat(match.group(1))
                end = date.fromisoformat(match.group(2))
                weeks.append((start, end))
            except ValueError:
                pass
    if weeks:
        weeks.sort()
        starts = [w[0] for w in weeks]
        ends = [w[1] for w in weeks]
        # Check for gaps between consecutive weeks
        gaps = []
        for i in range(1, len(weeks)):
            prev_end = weeks[i - 1][1]
            curr_start = weeks[i][0]
            delta = (curr_start - prev_end).days
            if delta > 1:
                gaps.append({
                    "prev_end": str(prev_end),
                    "next_start": str(curr_start),
                    "gap_days": delta,
                })
        date_analysis[sd.name] = {
            "earliest_start": str(starts[0]),
            "latest_end": str(ends[-1]),
            "week_count": len(weeks),
            "gaps": gaps,
        }
        print(f"Subdir {sd.name}: {starts[0]} to {ends[-1]} ({len(weeks)} weeks, {len(gaps)} gaps)")

# %% [markdown]
# ### Weekly date range and gap analysis
#
# Date extraction from filenames reveals the temporal coverage of each subdirectory.
# The aoestats files span weekly date ranges (start_date to end_date). Gaps between
# consecutive weeks indicate missing weekly snapshots. The known missing file
# (`2025-11-16_2025-11-22_players.parquet`, documented in ROADMAP) should appear
# as a gap or count mismatch in the paired comparison below.

# %%
# Discover paired directories by checking which subdirs share date ranges.
# We do NOT assume matches/players pairing — we discover it.
paired_report = {}
subdir_names = [sd.name for sd in result.subdirs]
for name_a in subdir_names:
    for name_b in subdir_names:
        if name_a >= name_b:
            continue
        if name_a in date_analysis and name_b in date_analysis:
            a = date_analysis[name_a]
            b = date_analysis[name_b]
            paired_report[f"{name_a} vs {name_b}"] = {
                "count_match": a["week_count"] == b["week_count"],
                f"{name_a}_weeks": a["week_count"],
                f"{name_b}_weeks": b["week_count"],
                "date_range_match": (
                    a["earliest_start"] == b["earliest_start"]
                    and a["latest_end"] == b["latest_end"]
                ),
            }

for pair, info in paired_report.items():
    print(f"Pair {pair}: count_match={info['count_match']}, date_range_match={info['date_range_match']}")

# %% [markdown]
# ### Paired directory comparison
#
# The comparison discovers which subdirectories share date ranges and whether
# their file counts match. A count mismatch between matches and players confirms
# the known data gap (one missing players file). The date range match indicates
# whether both directories cover the same temporal window despite the count
# difference. This pairing constraint is critical for downstream joins.

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
# naming pattern. For aoestats, this should reveal the weekly date-range naming
# convention (`{date}_{date}_matches.parquet`, `{date}_{date}_players.parquet`)
# alongside any housekeeping files (`.gitkeep`, ingestion trackers, overview
# files). No files are excluded from this count.

# %%
artifact = {
    "step": "01_01_01",
    "dataset": "aoestats",
    "raw_dir": str(RAW_DIR),
    "total_files": result.total_files,
    "total_bytes": result.total_bytes,
    "num_subdirs": len(result.subdirs),
    "files_at_root": len(result.files_at_root),
    "subdirs": subdir_data,
    "date_analysis": date_analysis,
    "paired_comparison": paired_report,
    "filename_patterns": dict(patterns),
    "total_files_scanned": len(all_files),
}

json_path = ARTIFACTS_DIR / "01_01_01_file_inventory.json"
json_path.write_text(json.dumps(artifact, indent=2, default=str))
logger.info("JSON artifact written: %s", json_path)

# %%
lines = [
    "# Step 01_01_01 — File Inventory: aoestats\n",
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
        lines.append(f"- Date range: {info['earliest_start']} to {info['latest_end']}")
        lines.append(f"- Weeks found: {info['week_count']}")
        if info["gaps"]:
            lines.append(f"- Gaps found: {len(info['gaps'])}")
            for g in info["gaps"]:
                lines.append(
                    f"  - {g['prev_end']} -> {g['next_start']} ({g['gap_days']} days)"
                )
        else:
            lines.append("- No gaps found")
        lines.append("")

if paired_report:
    lines.extend(["\n## Paired directory comparison\n"])
    lines.append("| Pair | Count match | Date range match |")
    lines.append("|---|---|---|")
    for pair, info in sorted(paired_report.items()):
        lines.append(
            f"| {pair} | {info['count_match']} | {info['date_range_match']} |"
        )

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
# - `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json` — structured inventory with per-subdirectory breakdown, date analysis, and paired comparison
# - `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md` — human-readable inventory report
#
# ### Thesis mapping
# - Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data
#
# ### Follow-ups
# - Step 01_01_02 (if defined) or Step 01_02_01: profile the Parquet schema and field completeness for each subdirectory
# - The known missing file (`2025-11-16_2025-11-22_players.parquet`) should be confirmed by the count mismatch discovered here
# - Schema drift documented in ROADMAP must be verified during profiling (Section 01_03)
