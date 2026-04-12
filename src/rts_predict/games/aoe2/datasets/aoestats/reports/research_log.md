# Research Log — AoE2 / aoestats

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

AoE2 / aoestats findings. Reverse chronological.

---

## 2026-04-12 — [Phase 01 / Step 01_01_01] File inventory of aoestats raw directory

**Category:** A (science)
**Dataset:** aoestats
**Step scope:** filesystem
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md`

### What

Executed the notebook `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb` with a fresh kernel via `jupyter nbconvert --execute --inplace`. The notebook called `inventory_directory()` on the aoestats raw directory, extracted filename-derived date ranges using a regex on the `{date}_{date}_<type>.parquet` pattern, identified gaps between consecutive week filenames, and produced a paired-directory comparison. Both JSON and Markdown artifacts were written to the artifacts directory.

### Why

Step 01_01_01 is the baseline filesystem inventory — it establishes what files exist on disk and how they are organised before any content-level reading. Required by Manual 01_DATA_EXPLORATION as the first action of Phase 01. Per Invariant #9, conclusions at this step must derive from the filesystem level only (filenames, sizes, counts).

### How (reproducibility)

```python
# inventory_directory() — filesystem-only glob + stat walk
result = inventory_directory(RAW_DIR)

# Filename date extraction
WEEK_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})")

# Gap detection between consecutive week filenames
for i in range(1, len(weeks)):
    prev_end = weeks[i - 1][1]
    curr_start = weeks[i][0]
    delta = (curr_start - prev_end).days
    if delta > 1:
        gaps.append({"prev_end": str(prev_end), "next_start": str(curr_start), "gap_days": delta})

# Paired comparison
paired_report["matches vs players"] = {
    "count_match": a["week_count"] == b["week_count"],
    "matches_weeks": a["week_count"],
    "players_weeks": b["week_count"],
    "date_range_match": (a["earliest_start"] == b["earliest_start"] and a["latest_end"] == b["latest_end"]),
}

# Whole-tree filename pattern summary
patterns = summarize_filename_patterns(all_files)
```

### Findings

- Total files in `raw/`: 349
- Total size: 3,773.61 MB (3,956,920,062 bytes)
- Subdirectories: 3 (`matches/`, `players/`, `overview/`)
- Files at root level: 2 (`README.md`, `_download_manifest.json`)
- `matches/`: 173 files (172 `.parquet` + 1 `.gitkeep`), 610.55 MB
- `players/`: 172 files (171 `.parquet` + 1 `.gitkeep`), 3,162.86 MB
- `overview/`: 2 files (1 `overview.json` + 1 `.gitkeep`), 0.02 MB
- Filename pattern `{date}_{date}_matches.parquet`: 172 files
- Filename pattern `{date}_{date}_players.parquet`: 171 files
- `matches/` date range (from filenames): 2022-08-28 to 2026-02-07, 172 weeks, 3 gaps:
  - 2024-07-20 -> 2024-09-01 (43 days)
  - 2024-09-28 -> 2024-10-06 (8 days)
  - 2025-03-22 -> 2025-03-30 (8 days)
- `players/` date range (from filenames): 2022-08-28 to 2026-02-07, 171 weeks, 4 gaps:
  - 2024-07-20 -> 2024-09-01 (43 days)
  - 2024-09-28 -> 2024-10-06 (8 days)
  - 2025-03-22 -> 2025-03-30 (8 days)
  - 2025-11-15 -> 2025-11-23 (8 days)
- Paired comparison (`matches/` vs `players/`): count_match=False (172 vs 171), date_range_match=True

### What this means

The `players/` directory has one fewer file than `matches/`, with the extra gap at 2025-11-15 -> 2025-11-23 — this corresponds to the absent file `2025-11-16_2025-11-22_players.parquet`. Both directories share the same temporal endpoints (2022-08-28 to 2026-02-07). All three gaps shared between directories (the 43-day gap in mid-2024 and two 8-day gaps) indicate missing 7-day-interval filename blocks in both `matches/` and `players/`. These will need to be accounted for in downstream processing.

### Decisions taken

- None — observation only.

### Decisions deferred

- Whether missing week-blocks (the 43-day and 8-day gaps) are acceptable or require investigation: deferred to Step 01_01_02 or later content-level steps that establish whether the gaps are data collection absences or data provider gaps.
- Whether the count mismatch (172 vs 171) affects downstream joins: deferred to the join step (Phase 01, later steps).

### Thesis mapping

- Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data (aoestats dataset description)

### Open questions / follow-ups

- Confirm whether the three shared gaps (43-day gap and two 8-day gaps) represent data provider absences or collection failures — requires content-level inspection (Step 01_01_02).
- The `overview/` subdirectory contains one `overview.json` file — its content and role relative to the `{date}_{date}_*.parquet` files is unknown at the filesystem level and must be established in Step 01_01_02.
- The `.gitkeep` placeholder in each subdirectory is housekeeping and not a data file — confirmed by filename extension and zero content.

---
