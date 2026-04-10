# Plan: Notebook Template v2 Conformance — 01_01_01 File Inventory

**Category:** C (chore — conformance cleanup)
**Branch:** `chore/notebook-template-conformance-01_01_01`
**Scope:** Rewrite three `01_01_01_file_inventory.py` notebooks to match
`docs/templates/notebook_template.yaml` v2. No functional changes — analysis
logic is preserved verbatim. Only cell structure, frontmatter fields, and
markdown interpretation cells change.

---

## Context

### Files to modify

| # | Path | Game | Dataset |
|---|------|------|---------|
| 1 | `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.py` | sc2 | sc2egset |
| 2 | `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py` | aoe2 | aoe2companion |
| 3 | `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py` | aoe2 | aoestats |

Each has a paired `.ipynb` that must be re-synced after the `.py` rewrite.

### Template requirements (Phase 01, no DuckDB)

From `docs/templates/notebook_template.yaml`:

- `cell_01_frontmatter` — mandatory, must include all 7 bold fields + description paragraph
- `cell_02_imports` — ALL imports in one cell (including `from datetime import ...`)
- `cell_03_paths` — config import + RAW_DIR + ARTIFACTS_DIR + log both
- `cell_04_duckdb_setup` — NOT needed (Phase 01 filesystem-only)
- `cells_05_to_N` — analysis cells, each followed by a markdown interpretation cell
- `cell_leakage_verification` — NOT needed (Phase 01, no features)
- `cell_conclusion` — mandatory: Artifacts produced, Thesis mapping, Follow-ups
- `cell_cleanup` — NOT needed (no DuckDB)

### Invariants applied

For Phase 01 File Inventory: `#6 (reproducibility), #7 (no magic numbers)`

### Thesis mappings (from ROADMAPs)

- **sc2egset:** `Chapter 3 — Data & Methodology > 3.1 Data Sources > SC2EGSet`
- **aoe2companion:** `Chapter 3 — Data & Methodology > 3.1 Data Sources > aoe2companion`
- **aoestats:** `Chapter 3 — Data & Methodology > 3.1 Data Sources > aoestats`

---

## Execution Steps

### Step 0 — Branch setup

```bash
git checkout -b chore/notebook-template-conformance-01_01_01
```

Get the git short hash for the Commit field:

```bash
git rev-parse --short HEAD
```

Store this value as `{git_short_hash}` for use in all three notebooks.

---

### Step 1 — Rewrite sc2egset notebook

**File:** `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.py`

Rewrite the entire `.py` file with the following cell structure. Preserve the
jupytext YAML header exactly as-is (lines 1-15 of the current file). Then write
cells in this order:

#### cell_01_frontmatter (markdown)

```
# Step 01_01_01 — File Inventory: sc2egset

**Phase:** 01 — Data Exploration
**Pipeline Section:** 01_01 — Data Acquisition & Source Inventory
**Dataset:** sc2egset
**Question:** What files exist on disk, how many are there, and how are they organized?
**Invariants applied:** #6 (reproducibility), #7 (no magic numbers)
**ROADMAP reference:** `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md` Step 01_01_01
**Commit:** {git_short_hash}

This notebook walks the sc2egset raw directory and counts everything.
It does NOT compare against any expected counts — it produces the counts
for the first time. The raw directory has a two-level structure:
`raw/TOURNAMENT_NAME/TOURNAMENT_NAME_data/*.SC2Replay.json`.
The top level also contains metadata files (`.zip`, `.log`, `.json`, no-extension).
Both levels are inventoried.
```

**Changes vs current:** Added `**Invariants applied:**`, `**ROADMAP reference:**`,
`**Commit:**` fields. Moved the layout note from a separate paragraph into the
description paragraph.

#### cell_02_imports (code)

```python
import json
import logging
import statistics
from pathlib import Path

from rts_predict.common.inventory import inventory_directory
from rts_predict.common.notebook_utils import get_reports_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

**Changes vs current:** None — already conformant. (sc2egset has no mid-notebook
imports.)

#### cell_03_paths (code)

```python
from rts_predict.sc2.config import REPLAYS_SOURCE_DIR

RAW_DIR: Path = REPLAYS_SOURCE_DIR
ARTIFACTS_DIR: Path = get_reports_dir("sc2", "sc2egset") / "artifacts" / "01_01"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

logger.info("Source directory: %s", RAW_DIR)
logger.info("Artifacts directory: %s", ARTIFACTS_DIR)
```

**Changes vs current:** Changed `logger.info("Raw directory: ...")` to
`logger.info("Source directory: ...")` to match template wording.

#### cell_04 — Level 1 inventory (code)

Preserve the existing analysis code verbatim (lines 58-66 of current file):

```python
# Level 1 inventory: RAW_DIR -> tournament directories (metadata files only)
# Each tournament dir contains: .zip, .log, .json metadata, and a _data/ subdir.
# inventory_directory goes one level deep, so it counts metadata files per tournament.
meta_result = inventory_directory(RAW_DIR)

logger.info("Tournament directories (level 1): %d", len(meta_result.subdirs))
logger.info("Metadata files across all tournaments: %d", meta_result.total_files)
logger.info("Files at root: %d", len(meta_result.files_at_root))
```

#### cell_05 — Level 1 interpretation (markdown) **NEW**

```
### Level 1 inventory

The level 1 scan of the raw directory reveals the tournament directory structure
and metadata file counts. Each tournament directory contains auxiliary files
(.zip archives, .log files, metadata .json) alongside a `_data/` subdirectory
holding the actual replay files. This cell establishes the top-level counts
before drilling into replay-level detail.
```

#### cell_06 — Level 2 inventory (code)

Preserve the existing analysis code verbatim (lines 69-98 of current file):

```python
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
```

#### cell_07 — Level 2 interpretation (markdown) **NEW**

```
### Level 2 inventory — replay files

The level 2 scan enters each tournament's `_data/` subdirectory and counts
replay files. The total replay file count and cumulative size establish the
authoritative source counts for all downstream steps. Any tournament missing
its `_data/` directory is flagged as a warning — these gaps must be acknowledged
in the data cleaning phase.
```

#### cell_08 — Summary statistics (code)

Preserve the existing analysis code verbatim (lines 101-115 of current file):

```python
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
```

#### cell_09 — Summary statistics interpretation (markdown) **NEW**

```
### Replay distribution across tournaments

The summary statistics (min, max, median replays per tournament) characterise
the size distribution of the corpus. Tournaments with zero replay files are
flagged explicitly — these are not data errors but may indicate incomplete
extraction or metadata-only directories.
```

#### cell_10 — Write JSON artifact (code)

Preserve the existing analysis code verbatim (lines 118-134 of current file):

```python
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
```

#### cell_11 — Write Markdown artifact (code)

Preserve the existing analysis code verbatim (lines 137-175 of current file):

```python
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
```

**Note:** This cell is 39 lines — within the 50-line cap.

#### cell_12 — Artifact writing interpretation (markdown) **NEW**

```
### Artifact output

Both the structured JSON artifact and the human-readable Markdown report have
been written to the artifacts directory. These are the authoritative inventory
records for all downstream steps. Per Invariant #6, the code that produced
each number is traceable via the paired `.ipynb` notebook.
```

#### cell_conclusion (markdown) **REPLACES old Verification section**

```
## Conclusion

### Artifacts produced
- `src/rts_predict/sc2/reports/sc2egset/artifacts/01_01/01_01_01_file_inventory.json` — structured inventory with per-tournament breakdown
- `src/rts_predict/sc2/reports/sc2egset/artifacts/01_01/01_01_01_file_inventory.md` — human-readable inventory report

### Thesis mapping
- Chapter 3 — Data & Methodology > 3.1 Data Sources > SC2EGSet

### Follow-ups
- Step 01_01_02 (if defined) or Step 01_02_01: profile the replay JSON schema and field completeness
- Any tournaments flagged with missing `_data/` directories need acknowledgement in data cleaning (Section 01_04)
```

---

### Step 2 — Rewrite aoe2companion notebook

**File:** `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py`

Preserve the jupytext YAML header (lines 1-15). Then write cells:

#### cell_01_frontmatter (markdown)

```
# Step 01_01_01 — File Inventory: aoe2companion

**Phase:** 01 — Data Exploration
**Pipeline Section:** 01_01 — Data Acquisition & Source Inventory
**Dataset:** aoe2companion
**Question:** What files exist on disk, how many are there, and how are they organized?
**Invariants applied:** #6 (reproducibility), #7 (no magic numbers)
**ROADMAP reference:** `src/rts_predict/aoe2/reports/aoe2companion/ROADMAP.md` Step 01_01_01
**Commit:** {git_short_hash}

This notebook walks the aoe2companion raw directory and counts everything.
For daily-file subdirectories, it extracts dates from filenames and reports
date range and gaps. The raw directory contains four subdirectories (matches,
ratings, leaderboards, profiles), each holding daily Parquet snapshots.
```

**Changes vs current:** Added `**Invariants applied:**`, `**ROADMAP reference:**`,
`**Commit:**` fields. Expanded description paragraph with layout detail.

#### cell_02_imports (code)

```python
import json
import logging
import re
import statistics
from datetime import date, timedelta
from pathlib import Path

from rts_predict.common.inventory import inventory_directory
from rts_predict.common.notebook_utils import get_reports_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

**Changes vs current:** Moved `from datetime import date, timedelta` from
mid-notebook (old cell at line 77) into cell_02. All imports now in one cell.

#### cell_03_paths (code)

```python
from rts_predict.aoe2.config import AOE2COMPANION_RAW_DIR

RAW_DIR: Path = AOE2COMPANION_RAW_DIR
ARTIFACTS_DIR: Path = get_reports_dir("aoe2", "aoe2companion") / "artifacts" / "01_01"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

logger.info("Source directory: %s", RAW_DIR)
logger.info("Artifacts directory: %s", ARTIFACTS_DIR)
```

**Changes vs current:** Changed `"Raw directory"` to `"Source directory"`.

#### cell_04 — Top-level inventory (code)

Preserve verbatim (lines 52-58 of current file):

```python
result = inventory_directory(RAW_DIR)

logger.info("Total files: %d", result.total_files)
logger.info("Total size: %.2f MB", result.total_bytes / (1024 * 1024))
logger.info("Subdirectories: %d", len(result.subdirs))
logger.info("Files at root: %d", len(result.files_at_root))
```

#### cell_05 — Top-level interpretation (markdown) **NEW**

```
### Top-level inventory

The raw directory scan reveals the subdirectory structure and total file counts.
The aoe2companion dataset is organised into four subdirectories (matches, ratings,
leaderboards, profiles), each containing daily Parquet snapshots. The total file
count and size establish the baseline for downstream processing steps.
```

#### cell_06 — Per-subdirectory breakdown (code)

Preserve verbatim (lines 61-74 of current file):

```python
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
```

#### cell_07 — Per-subdirectory interpretation (markdown) **NEW**

```
### Per-subdirectory file counts

The breakdown shows file counts and sizes for each subdirectory. The variance
in file counts across subdirectories reflects the different granularity and
retention policies of each data category (matches vs ratings vs snapshots).
```

#### cell_08 — Date extraction and gap analysis (code)

Preserve verbatim (lines 79-116 of current file), **MINUS** the
`from datetime import date, timedelta` line (already moved to cell_02):

```python
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
```

**Note:** This cell is 38 lines — within the 50-line cap.

#### cell_09 — Date analysis interpretation (markdown) **NEW**

```
### Date range and gap analysis

Date extraction from filenames reveals the temporal coverage of each
subdirectory. Gaps between consecutive dates indicate missing daily snapshots.
These gaps are recorded in the artifact for acknowledgement during data cleaning
(Section 01_04). Subdirectories without date-patterned filenames (e.g., snapshot
tables) are noted separately.
```

#### cell_10 — Write JSON artifact (code)

Preserve verbatim (lines 118-133 of current file):

```python
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
```

#### cell_11 — Write Markdown artifact (code)

Preserve verbatim (lines 135-167 of current file):

```python
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
```

**Note:** This cell is 33 lines — within the 50-line cap.

#### cell_12 — Artifact writing interpretation (markdown) **NEW**

```
### Artifact output

Both the structured JSON artifact and the human-readable Markdown report have
been written to the artifacts directory. These are the authoritative inventory
records for all downstream steps. Per Invariant #6, the code that produced
each number is traceable via the paired `.ipynb` notebook.
```

#### cell_conclusion (markdown) **REPLACES old Verification section**

```
## Conclusion

### Artifacts produced
- `src/rts_predict/aoe2/reports/aoe2companion/artifacts/01_01/01_01_01_file_inventory.json` — structured inventory with per-subdirectory breakdown and date analysis
- `src/rts_predict/aoe2/reports/aoe2companion/artifacts/01_01/01_01_01_file_inventory.md` — human-readable inventory report

### Thesis mapping
- Chapter 3 — Data & Methodology > 3.1 Data Sources > aoe2companion

### Follow-ups
- Step 01_01_02 (if defined) or Step 01_02_01: profile the Parquet schema and field completeness for each subdirectory
- Date gaps identified in the inventory must be acknowledged during data cleaning (Section 01_04)
- Sparse rating regime (pre-2025-06-26) flagged in ROADMAP must be verified against the date range found here
```

---

### Step 3 — Rewrite aoestats notebook

**File:** `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py`

Preserve the jupytext YAML header (lines 1-15). Then write cells:

#### cell_01_frontmatter (markdown)

```
# Step 01_01_01 — File Inventory: aoestats

**Phase:** 01 — Data Exploration
**Pipeline Section:** 01_01 — Data Acquisition & Source Inventory
**Dataset:** aoestats
**Question:** What files exist on disk, how many are there, and how are they organized?
**Invariants applied:** #6 (reproducibility), #7 (no magic numbers)
**ROADMAP reference:** `src/rts_predict/aoe2/reports/aoestats/ROADMAP.md` Step 01_01_01
**Commit:** {git_short_hash}

This notebook walks the aoestats raw directory and counts everything.
For weekly-file subdirectories, it extracts date ranges from filenames
and checks whether paired directories (matches and players) have matching
file counts and date ranges. The raw directory contains paired weekly
Parquet files where each file covers a one-week date span.
```

**Changes vs current:** Added `**Invariants applied:**`, `**ROADMAP reference:**`,
`**Commit:**` fields. Expanded description paragraph.

#### cell_02_imports (code)

```python
import json
import logging
import re
import statistics
from datetime import date
from pathlib import Path

from rts_predict.common.inventory import inventory_directory
from rts_predict.common.notebook_utils import get_reports_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

**Changes vs current:** Moved `from datetime import date` from mid-notebook
(old cell at line 78) into cell_02.

#### cell_03_paths (code)

```python
from rts_predict.aoe2.config import AOESTATS_RAW_DIR

RAW_DIR: Path = AOESTATS_RAW_DIR
ARTIFACTS_DIR: Path = get_reports_dir("aoe2", "aoestats") / "artifacts" / "01_01"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

logger.info("Source directory: %s", RAW_DIR)
logger.info("Artifacts directory: %s", ARTIFACTS_DIR)
```

**Changes vs current:** Changed `"Raw directory"` to `"Source directory"`.

#### cell_04 — Top-level inventory (code)

Preserve verbatim (lines 53-59 of current file):

```python
result = inventory_directory(RAW_DIR)

logger.info("Total files: %d", result.total_files)
logger.info("Total size: %.2f MB", result.total_bytes / (1024 * 1024))
logger.info("Subdirectories: %d", len(result.subdirs))
logger.info("Files at root: %d", len(result.files_at_root))
```

#### cell_05 — Top-level interpretation (markdown) **NEW**

```
### Top-level inventory

The raw directory scan reveals the subdirectory structure and total file counts.
The aoestats dataset is organised into paired weekly Parquet files across
subdirectories (matches and players). The total file count and size establish
the baseline for downstream processing steps.
```

#### cell_06 — Per-subdirectory breakdown (code)

Preserve verbatim (lines 61-75 of current file):

```python
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
```

#### cell_07 — Per-subdirectory interpretation (markdown) **NEW**

```
### Per-subdirectory file counts

The breakdown shows file counts and sizes for each subdirectory. Since matches
and players directories are expected to be paired (one file per week per
directory), count discrepancies signal missing files that must be acknowledged
in data cleaning.
```

#### cell_08 — Weekly date extraction and gap analysis (code)

Preserve verbatim (lines 80-119 of current file), **MINUS** the
`from datetime import date` line (already moved to cell_02):

```python
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
        logger.info("Subdir %s: %s to %s (%d weeks, %d gaps)",
                     sd.name, starts[0], ends[-1], len(weeks), len(gaps))
```

**Note:** This cell is 38 lines — within the 50-line cap.

#### cell_09 — Date analysis interpretation (markdown) **NEW**

```
### Weekly date range and gap analysis

Date extraction from filenames reveals the temporal coverage of each subdirectory.
The aoestats files span weekly date ranges (start_date to end_date). Gaps between
consecutive weeks indicate missing weekly snapshots. The known missing file
(`2025-11-16_2025-11-22_players.parquet`, documented in ROADMAP) should appear
as a gap or count mismatch in the paired comparison below.
```

#### cell_10 — Paired directory comparison (code)

Preserve verbatim (lines 122-145 of current file):

```python
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
    logger.info("Pair %s: count_match=%s, date_range_match=%s",
                pair, info["count_match"], info["date_range_match"])
```

#### cell_11 — Paired comparison interpretation (markdown) **NEW**

```
### Paired directory comparison

The comparison discovers which subdirectories share date ranges and whether
their file counts match. A count mismatch between matches and players confirms
the known data gap (one missing players file). The date range match indicates
whether both directories cover the same temporal window despite the count
difference. This pairing constraint is critical for downstream joins.
```

#### cell_12 — Write JSON artifact (code)

Preserve verbatim (lines 147-163 of current file):

```python
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
}

json_path = ARTIFACTS_DIR / "01_01_01_file_inventory.json"
json_path.write_text(json.dumps(artifact, indent=2, default=str))
logger.info("JSON artifact written: %s", json_path)
```

#### cell_13 — Write Markdown artifact (code)

Preserve verbatim (lines 165-208 of current file):

```python
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

md_path = ARTIFACTS_DIR / "01_01_01_file_inventory.md"
md_path.write_text("\n".join(lines) + "\n")
logger.info("Markdown artifact written: %s", md_path)
```

**Note:** This cell is 44 lines — within the 50-line cap.

#### cell_14 — Artifact writing interpretation (markdown) **NEW**

```
### Artifact output

Both the structured JSON artifact and the human-readable Markdown report have
been written to the artifacts directory. These are the authoritative inventory
records for all downstream steps. Per Invariant #6, the code that produced
each number is traceable via the paired `.ipynb` notebook.
```

#### cell_conclusion (markdown) **REPLACES old Verification section**

```
## Conclusion

### Artifacts produced
- `src/rts_predict/aoe2/reports/aoestats/artifacts/01_01/01_01_01_file_inventory.json` — structured inventory with per-subdirectory breakdown, date analysis, and paired comparison
- `src/rts_predict/aoe2/reports/aoestats/artifacts/01_01/01_01_01_file_inventory.md` — human-readable inventory report

### Thesis mapping
- Chapter 3 — Data & Methodology > 3.1 Data Sources > aoestats

### Follow-ups
- Step 01_01_02 (if defined) or Step 01_02_01: profile the Parquet schema and field completeness for each subdirectory
- The known missing file (`2025-11-16_2025-11-22_players.parquet`) should be confirmed by the count mismatch discovered here
- Schema drift documented in ROADMAP must be verified during profiling (Section 01_03)
```

---

### Step 4 — Jupytext sync

After rewriting each `.py` file, run the jupytext sync command to regenerate
the paired `.ipynb`:

```bash
source .venv/bin/activate && poetry run jupytext --sync sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.py
```

```bash
source .venv/bin/activate && poetry run jupytext --sync sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py
```

```bash
source .venv/bin/activate && poetry run jupytext --sync sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py
```

The `.ipynb` files will lose their cell outputs (since the `.py` is the source
of truth for structure). This is acceptable — the notebooks must be re-executed
to repopulate outputs. Re-execution is out of scope for this chore.

---

### Step 5 — Verification

Run jupytext check on all three files:

```bash
source .venv/bin/activate && poetry run jupytext --check sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.py && poetry run jupytext --check sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py && poetry run jupytext --check sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py
```

Manually verify for each notebook:
1. All 7 frontmatter fields are present (Phase, Pipeline Section, Dataset,
   Question, Invariants applied, ROADMAP reference, Commit)
2. All imports are in cell_02 (no mid-notebook imports)
3. Every code analysis cell is followed by a markdown interpretation cell
   within 2 cells
4. Conclusion section has all 3 subsections (Artifacts produced, Thesis mapping,
   Follow-ups)
5. No cell exceeds 50 lines
6. No `def`, `class`, or lambda assignments in any cell

---

### Step 6 — Commit and PR prep

Stage all 6 files (3 `.py` + 3 `.ipynb`):

```bash
git add sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.py sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb
```

Commit message (write to `.github/tmp/commit.txt`):

```
chore(notebooks): conform 01_01_01 file inventory to template v2

Restructure all three file inventory notebooks (sc2egset, aoe2companion,
aoestats) to match docs/templates/notebook_template.yaml v2:

- Add missing frontmatter fields (Invariants applied, ROADMAP reference, Commit)
- Consolidate all imports into cell_02 (move datetime imports from mid-notebook)
- Add markdown interpretation cells after each analysis code cell
- Replace bare Verification section with structured Conclusion
  (Artifacts produced, Thesis mapping, Follow-ups)

No functional changes — analysis logic is preserved verbatim.
```

Follow the standard version bump and PR workflow per git-workflow rule.

---

## Gate condition

All three `.py` files pass `poetry run jupytext --check` and both `.py` +
`.ipynb` are staged. The frontmatter, import consolidation, interpretation
cells, and conclusion sections match the template v2 specification.

---

## Change summary

| Notebook | Cells before | Cells after | New markdown cells | Import moves |
|----------|-------------|-------------|-------------------|-------------|
| sc2egset | 8 (6 code + 2 md) | 13 (6 code + 7 md) | 5 (4 interpretation + 1 conclusion) | 0 |
| aoe2companion | 9 (7 code + 2 md) | 14 (6 code + 8 md) | 6 (4 interpretation + 1 conclusion) | `from datetime import date, timedelta` |
| aoestats | 10 (8 code + 2 md) | 16 (7 code + 9 md) | 7 (5 interpretation + 1 conclusion) | `from datetime import date` |

## Orchestration note

This chore modifies non-overlapping files (three distinct notebooks). Strategy A
(shared branch) is appropriate. A single executor can process all three
sequentially. Alternatively, three parallel executors can each take one notebook
on the shared branch since the files do not overlap.
