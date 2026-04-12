# Research Log — SC2 / sc2egset

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

SC2 / sc2egset findings. Reverse chronological.

---

## 2026-04-12 — [Phase 01 / Step 01_01_01] File inventory of sc2egset raw directory

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** filesystem
**Artifacts produced:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md`

### What

Ran `inventory_directory()` on the sc2egset `raw/` directory to count all files
and subdirectories at two levels: the top-level directories (level 1)
and each directory's `_data/` subdirectory (level 2). Filename patterns were
summarised across both levels using `summarize_filename_patterns()`. Results
were written to a JSON artifact and a Markdown report in the artifacts directory.

### Why

Phase 01, Step 01_01_01 requires establishing the authoritative file counts and
directory structure of the raw data before any content-level work. Per Invariant
#9, all downstream steps must reference this artifact for source file counts.
Per Invariant #6, the code that produced every count is traceable via the paired
notebook (`01_01_01_file_inventory.ipynb`).

### How (reproducibility)

```python
from rts_predict.common.inventory import inventory_directory
from rts_predict.common.filename_patterns import summarize_filename_patterns

# Level 1: top-level directories
meta_result = inventory_directory(RAW_DIR)

# Level 2: each directory's _data/ subdir
for sd in meta_result.subdirs:
    data_dir = RAW_DIR / sd.name / (sd.name + "_data")
    replay_inv = inventory_directory(data_dir)

# Filename patterns across both levels
patterns = summarize_filename_patterns(all_files)
```

Full code: `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb`

### Findings

- Raw directory layout: `raw/TOURNAMENT/TOURNAMENT_data/*.SC2Replay.json` (two levels)
- 70 top-level directories under `raw/`
- 3 files at `raw/` root: `README.md`, `README.sc2egset.md`, `SC2EGSet_datasheet.pdf`
- 431 metadata files distributed across top-level directories (`.zip`, `.log`, `.json` patterns)
- Each top-level directory contains one `map_foreign_to_english_mapping.json` (70 total)
- 22,390 files with extension `.json` and pattern `{hash}.SC2Replay.json` inside `_data/` subdirectories
- Total size of `_data/` files: 214,060.62 MB (~209 GiB)
- Files per `_data/` subdirectory: min 30, max 1,296, median 260.5
- 0 top-level directories with a missing `_data/` subdirectory
- Filename-derived date range: directory names span `2016_*` through `2024_*`
- 8 `.DS_Store` files present in the tree
- Total files scanned across both levels: 22,821
- All `_data/` files carry the `.json` extension; no other extension observed in `_data/` subdirectories

### Decisions taken

- None — observation only.

### Decisions deferred

- Whether any of the 70 top-level directories should be excluded from analysis
  (e.g., due to size, date coverage, or file count): deferred to Step 01_04_xx
  (data cleaning / filtering decisions require content-level profiling first).
- The `.DS_Store` files (8) and root-level housekeeping files are noted but
  no action is needed until ingestion is designed (Phase 01 content steps).

### Thesis mapping

- Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet (StarCraft II): source
  file counts, directory layout, and date range derived from directory names.

### Open questions / follow-ups

- The `{hash}.SC2Replay.json` filename pattern does not embed dates; dates are
  encoded only in top-level directory names, not individual filenames. Whether
  individual files carry internal timestamps must be established at Step 01_01_02
  (content/schema profiling).
- The per-directory file count range (30 to 1,296) is wide; whether top-level directories with fewer files (e.g., those with < 50) represent complete acquisitions or partial extractions cannot be determined from filenames alone.
- The `processed_failed.log` files present in every top-level directory indicate
  a processing step was run during dataset creation; the contents of these logs
  are unknown at this step and may surface exclusion-worthy files at Step 01_01_02.

---
