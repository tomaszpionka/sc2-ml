---
# raw_data_readme v2 -- conforms to docs/templates/raw_data_readme_template.yaml

# -- Section A: Identity -------------------------------------------------------

game: aoe2
dataset: aoestats
raw_directory: src/rts_predict/games/aoe2/datasets/aoestats/data/raw/

# -- Section B: Provenance -----------------------------------------------------

source_name: "aoestats.io weekly DB dumps"
source_url: "https://aoestats.io"
source_type: cdn_download
data_creator: "aoestats.io (community statistics service)"
sampling_mechanism: >
  exhaustive -- all matches recorded by aoestats.io for the covered date range;
  selection criteria used by the source service are not publicly documented.
manifest_path: "src/rts_predict/games/aoe2/datasets/aoestats/data/api/db_dump_list.json"
citation: aoestats_io
license: "Unknown -- no license file in source; check with data_creator before redistribution"
acquisition_date: "2026-04-06"
acquisition_script: "src/rts_predict/games/aoe2/datasets/aoestats/data/acquisition.py"

# -- Section C: Content and Layout ---------------------------------------------

description: # to be repopulated from 01_01_01 artifacts
file_format: "parquet, JSON"

# File counts and sizes to be repopulated from 01_01_01 artifacts after rerun.
# Dotfiles excluded: .gitkeep x3 (one per subdir).
subdirectory_layout:
  - directory: "matches/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "{start_date}_{end_date}_matches.parquet"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "players/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "{start_date}_{end_date}_players.parquet"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "overview/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "overview.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts

total_files: # to be repopulated from 01_01_01 artifacts
total_size_mb: # to be repopulated from 01_01_01 artifacts

# -- Section D: Temporal Coverage ----------------------------------------------

temporal_grain: # to be populated from 01_01_01 artifact date_analysis
# Dates from 01_01_01 artifact date_analysis.matches
date_range_start: # to be repopulated from 01_01_01 artifacts
date_range_end: # to be repopulated from 01_01_01 artifacts

# Gaps from 01_01_01 artifact -- to be repopulated after rerun
known_gaps: # to be repopulated from 01_01_01 artifacts

gap_analysis_status: not_started
# coverage_notes: stripped -- forward references to Phase 01 profiling steps not yet complete

# -- Section E: Acquisition Filtering ------------------------------------------

acquisition_filters:
  - rule: "Manifest entries with num_matches == 0 are skipped during download"
    justification: >
      Weeks with zero matches contain no usable data. Downloading them would
      consume storage without adding information. The filter is implemented in
      acquisition.py (filter_download_targets function).
    excluded_count: 16
    excluded_count_source: >
      manifest comparison: 188 total manifest entries minus 172 downloaded
      match files = 16 zero-match weeks excluded.

# -- Section F: Verification ---------------------------------------------------

checksum_status: full
checksum_source: "db_dump_list.json manifest -- match_checksum and player_checksum fields (MD5)"
checksum_verified: true
# MD5 checksums are verified during download (acquisition.py download_file function
# raises ValueError on checksum mismatch) and checked for idempotent re-runs
# (acquisition.py is_already_downloaded function computes MD5 before skipping).
verification_date: "2026-04-06"

# -- Section G: Immutability and Artifact Link ---------------------------------

immutability:
  status: true
  enforcement_mechanism: none_documented

inventory_artifact: "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"

# -- Section H: Known Limitations ----------------------------------------------

known_biases: >
  The selection criteria used by aoestats.io to include matches in its database
  are not publicly documented. It is unknown whether all ranked or casual matches
  are captured, or whether filtering is applied at the source. This limits claims
  about population representativeness.

representativeness_notes: >
  Coverage is limited to matches recorded by the aoestats.io service. The
  service audience and any server-side filters applied before publication are
  not known, making it difficult to assess which parts of the AoE2 player
  population are under- or over-represented.
---

# aoestats -- Raw Data

Weekly database dumps from aoestats.io. Files downloaded on 2026-04-06 from
[https://aoestats.io](https://aoestats.io).
This directory holds the raw data layer and must never be modified.

**License:** Unknown -- no license file in source
**Acquisition date:** 2026-04-06
**Acquisition script:** `src/rts_predict/games/aoe2/datasets/aoestats/data/acquisition.py`
**Manifest:** `src/rts_predict/games/aoe2/datasets/aoestats/data/api/db_dump_list.json`

> **File counts and sizes:** To be repopulated from 01_01_01 artifacts after rerun. Dotfiles excluded
> (.gitkeep x3, one per subdir). Counts reflect data files only.

## Subdirectory Layout

| Directory | Contents | Pattern | File count | Size (MB) |
|-----------|----------|---------|-----------|-----------|
| `matches/` | to be repopulated from 01_01_01 artifacts | `{start}_{end}_matches.parquet` | — | — |
| `players/` | to be repopulated from 01_01_01 artifacts | `{start}_{end}_players.parquet` | — | — |
| `overview/` | to be repopulated from 01_01_01 artifacts | `overview.json` | — | — |

**Total files:** to be repopulated from 01_01_01 artifacts
**Total size:** to be repopulated from 01_01_01 artifacts

## Temporal Coverage

- **Grain:** to be populated from 01_01_01 artifact date_analysis
- **Date range:** to be repopulated from 01_01_01 artifacts
- **Gap analysis status:** not_started
- **Known gaps:** to be repopulated from 01_01_01 artifacts

## Acquisition Filtering

16 zero-match weeks from the manifest were excluded during download.
These correspond to manifest entries with `num_matches == 0`. The manifest
contained 188 total entries; 172 non-zero entries were downloaded.

## Verification

MD5 checksums are available in the manifest (`match_checksum` and
`player_checksum` fields) and were verified during download. The acquisition
script raises an error on checksum mismatch and checks MD5 for idempotent
re-downloads.

## Known Limitations

- Source selection criteria not documented; representativeness unknown
- players/ has one fewer file than matches/ (172 vs 171: one additional gap week in players)

## Inventory Artifact

`src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`
