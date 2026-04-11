# Research Log

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

Reverse chronological entries.

> **Phase migration note (2026-04-09):** This log was reset as part of the
> Phase 01-07 migration. Prior entries were removed in v2.0.0 (archive
> cleanup); historical context is preserved in git history.
> All new entries use the Phase XX / Step XX_YY_ZZ format per docs/PHASES.md.

---

## 2026-04-11 — [CROSS] AoE2 Dataset Strategy Decision

**Category:** C (chore — decision record)

### What
Formalized the AoE2 dataset strategy: aoe2companion is PRIMARY,
aoestats is SUPPLEMENTARY VALIDATION.

### Why
Both datasets had identical ROADMAP structures implying equal treatment.
Without formalization, Phase 01 work proceeds on both at equal priority,
potentially wasting 50% of AoE2 effort.

### Decision
- aoe2companion (277M matches, daily, 2020–2026) runs full Phases 01–07.
- aoestats (30.7M matches, weekly, 2022–2026) runs full Phase 01, then
  lightweight Phase 02–05 replication for validation.
- Phase 06 uses aoe2companion exclusively.
- Contradictions between datasets are reported in thesis §6.5.

### Thesis mapping
- Chapter 4 — Data and Methodology > 4.1 Datasets

---

## 2026-04-09 — [Phase 01 / Step 01_01_01] File Inventory (all 3 datasets)

**Category:** A (science)
**Dataset:** sc2egset, aoe2companion, aoestats
**Artifacts produced:**
- `src/rts_predict/sc2/reports/sc2egset/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`
- `src/rts_predict/sc2/reports/sc2egset/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md`
- `src/rts_predict/aoe2/reports/aoe2companion/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`
- `src/rts_predict/aoe2/reports/aoe2companion/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md`
- `src/rts_predict/aoe2/reports/aoestats/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`
- `src/rts_predict/aoe2/reports/aoestats/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md`

### What
Ran `inventory_directory()` on the raw directory of each dataset. Produced
per-subdirectory file counts, sizes, and extension distributions. For
aoe2companion and aoestats, extracted dates from filenames and checked for
gaps. For aoestats, compared paired directories.

### Why
Step 01_01_01 is the first step of Phase 01 Data Exploration. Before any
DuckDB ingestion can be designed, we need an authoritative inventory of
what files exist. Per Scientific Invariant 6, these counts must be produced
by auditable code.

### How (reproducibility)
Each notebook calls `inventory_directory(RAW_DIR)` from
`rts_predict.common.inventory` and writes the result to JSON and Markdown
artifacts. The notebooks are the reproducibility record.

### Findings

**sc2egset:** Two-level layout: `raw/TOURNAMENT/TOURNAMENT_data/*.SC2Replay.json`.
70 tournament directories, all with a `_data/` subdirectory (no missing data dirs).
Total replay files: 22,390 `.SC2Replay.json` files across 70 `_data/`
subdirectories, total replay size: ~214.1 GB (224,458,832,476 bytes).
Metadata files at the tournament level (zip/log/json/no-extension): 432 total
across 70 tournament dirs + 4 files at raw root. Tournament coverage spans
2016 to 2024. Initial inventory (before this fix) only scanned the metadata
files at tournament level — this notebook was corrected to scan the `_data/`
subdirectories and report the actual replay counts.

**aoe2companion:** 4,154 total files across 4 subdirectories + 3 files at
root. Total size: 9,388.27 MB (~9.2 GB). Breakdown:
- `matches/`: 2,074 files (1 no-ext + 2,073 `.parquet`), 6,621.52 MB
- `ratings/`: 2,073 files (1 no-ext + 2,072 `.csv`), 2,519.59 MB
- `leaderboards/`: 2 files (1 no-ext + 1 `.parquet`), 83.32 MB (snapshot)
- `profiles/`: 2 files (1 no-ext + 1 `.parquet`), 161.84 MB (snapshot)
Date range for matches: 2020-08-01 to 2026-04-04, 2,073 daily files, no gaps.
Date range for ratings: 2020-08-01 to 2026-04-04, 2,072 daily files, 1 gap
(2025-07-10 to 2025-07-12, 2 days).

**aoestats:** 349 total files across 3 subdirectories + 2 files at root.
Total size: 3,773.43 MB (~3.7 GB). Breakdown:
- `matches/`: 173 files (1 no-ext + 172 `.parquet`), 610.55 MB
- `players/`: 172 files (1 no-ext + 171 `.parquet`), 3,162.86 MB
- `overview/`: 2 files (1 no-ext + 1 `.json`), 0.02 MB
Date range for both matches and players: 2022-08-28 to 2026-02-07.
matches: 172 weekly files, 3 gaps (43 days, 8 days, 8 days).
players: 171 weekly files (1 missing — documented download failure for
2025-11-16_2025-11-22), same 3 gaps plus an 8-day gap confirming the
missing file.
Paired comparison (matches vs players): count_match=False (172 vs 171),
date_range_match=True. The asymmetry is the known missing file.

### What this means
All three raw directories are non-empty and structurally sound. The sc2egset
layout is two-level: tournament-level metadata + `_data/` subdirs with replay
JSONs. The actual replay count is 22,390 files (~214.1 GB). The aoe2companion
matches directory is daily and complete (no gaps). The ratings directory has
one 2-day gap in July 2025. The aoestats asymmetry (172 match files vs 171
player files) is consistent with the documented download failure already noted
in the ROADMAP source data section — this is not a new finding.

### Decisions taken
- sc2egset notebook was corrected after initial inventory to scan into `_data/`
  subdirectories for actual replay JSON counts, not just tournament-level metadata.

### Decisions deferred
- Ingestion strategy depends on what we find in schema discovery (01_01_02/03).

### Thesis mapping
- Chapter 4 — Data and Methodology > 4.1 Datasets

### Open questions / follow-ups
- sc2egset: The 4 files at root and the no-extension files within tournament
  dirs should be inspected in 01_01_02 schema discovery.
- aoe2companion: The ratings 2-day gap (2025-07-10 to 2025-07-12) is minor
  but should be flagged in cleaning notes.
- aoestats: The 43-day gap in matches (2024-07-20 to 2024-09-01) is
  significant and should be documented in 01_01_02 analysis.

