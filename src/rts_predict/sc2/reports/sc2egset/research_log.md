# Research Log — SC2 / sc2egset

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

SC2 / sc2egset findings. Reverse chronological.

---

## 2026-04-09 — [Phase 01 / Step 01_01_01] File Inventory (sc2egset)

**Category:** A (science)
**Dataset:** sc2egset
**Artifacts produced:**
- `src/rts_predict/sc2/reports/sc2egset/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`
- `src/rts_predict/sc2/reports/sc2egset/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md`

### What
Ran `inventory_directory()` on the raw directory of the sc2egset dataset.
Produced per-subdirectory file counts, sizes, and extension distributions.

### Why
Step 01_01_01 is the first step of Phase 01 Data Exploration. Before any
DuckDB ingestion can be designed, we need an authoritative inventory of
what files exist. Per Scientific Invariant 6, these counts must be produced
by auditable code.

### How (reproducibility)
The notebook calls `inventory_directory(RAW_DIR)` from
`rts_predict.common.inventory` and writes the result to JSON and Markdown
artifacts. The notebook is the reproducibility record.

### Findings
- Two-level layout: `raw/TOURNAMENT/TOURNAMENT_data/*.SC2Replay.json`.
- 70 tournament directories, all with a `_data/` subdirectory (no missing data dirs).
- Total replay files: 22,390 `.SC2Replay.json` files across 70 `_data/` subdirectories.
- Total replay size: ~214.1 GB (224,458,832,476 bytes).
- Tournament coverage spans 2016 to 2024.
- Metadata files at the tournament level (zip/log/json/no-extension): 432 total
  across 70 tournament dirs + 4 files at raw root.
- Initial inventory (before the `_data/` fix) only scanned metadata files at
  tournament level; the notebook was corrected to scan `_data/` subdirectories
  and report actual replay counts.

### What this means
The sc2egset raw directory is non-empty and structurally sound. The two-level
layout (tournament-level metadata + `_data/` subdirs with replay JSONs) means
ingestion must recurse into `_data/` directories. The actual replay count is
22,390 files (~214.1 GB).

### Decisions taken
- sc2egset notebook was corrected after initial inventory to scan into `_data/`
  subdirectories for actual replay JSON counts, not just tournament-level metadata.

### Decisions deferred
- Ingestion strategy depends on what we find in schema discovery (01_01_02/03).

### Thesis mapping
- Chapter 4 — Data and Methodology > 4.1 Datasets

### Open questions / follow-ups
- The 4 files at raw root and the no-extension files within tournament dirs
  should be inspected in 01_01_02 schema discovery.
