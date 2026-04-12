---
# raw_data_readme v2 -- conforms to docs/templates/raw_data_readme_template.yaml

# -- Section A: Identity -------------------------------------------------------

game: aoe2
dataset: aoe2companion
raw_directory: src/rts_predict/games/aoe2/datasets/aoe2companion/data/raw/

# -- Section B: Provenance -----------------------------------------------------

source_name: "aoe2companion CDN dump"
source_url: "https://www.aoe2companion.com/more/api"
source_type: cdn_download
data_creator: "aoe2companion (community-run API service)"
sampling_mechanism: >
  exhaustive -- all matches recorded by the aoe2companion service for the
  covered date range; limited to players who use the aoe2companion application.
manifest_path: "src/rts_predict/games/aoe2/datasets/aoe2companion/data/api/api_dump_list.json"
citation: aoe2companion_cdn
license: "Unknown -- no license file in source; check with data_creator before redistribution"
acquisition_date: "2026-04-06"
acquisition_script: "src/rts_predict/games/aoe2/datasets/aoe2companion/data/acquisition.py"

# -- Section C: Content and Layout ---------------------------------------------

description: # to be repopulated from 01_01_01 artifacts
file_format: "parquet, CSV"

# File counts and sizes to be repopulated from 01_01_01 artifacts after rerun.
# Dotfiles excluded: .gitkeep x4 (one per subdir), .DS_Store x1 at root.
subdirectory_layout:
  - directory: "matches/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "match-{date}.parquet"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "leaderboards/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "leaderboard.parquet"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "profiles/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "profile.parquet"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "ratings/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "rating-{date}.csv"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts

total_files: # to be repopulated from 01_01_01 artifacts
total_size_mb: # to be repopulated from 01_01_01 artifacts

# -- Section D: Temporal Coverage ----------------------------------------------

temporal_grain: # to be populated from 01_01_01 artifact date_analysis
# Dates from 01_01_01 artifact date_analysis.matches
date_range_start: # to be repopulated from 01_01_01 artifacts
date_range_end: # to be repopulated from 01_01_01 artifacts

known_gaps: # to be repopulated from 01_01_01 artifacts

gap_analysis_status: not_started
# coverage_notes: stripped -- forward references to Phase 01 profiling steps not yet complete

# -- Section E: Acquisition Filtering ------------------------------------------

# acquisition_filters: no filtering was performed; all manifest entries downloaded.

excluded_formats:
  - format: "CSV equivalents of matches, leaderboards, profiles"
    reason: >
      Parquet format was chosen for size and query performance. CSV equivalents
      exist in the manifest but were not downloaded as they offer no additional
      information content. Rating CSVs have no parquet equivalent and are
      therefore downloaded.

# -- Section F: Verification ---------------------------------------------------

checksum_status: none
# The aoe2companion CDN manifest does not provide file checksums.
# checksum_source and checksum_verified omitted -- checksum_status is none.

# -- Section G: Immutability and Artifact Link ---------------------------------

immutability:
  status: true
  enforcement_mechanism: none_documented

inventory_artifact: "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"

# -- Section H: Known Limitations ----------------------------------------------

known_biases: >
  Coverage is limited to games recorded by players who use the aoe2companion
  service. Players who do not link their accounts or use the service are absent.
  This may under-represent casual or non-English-speaking player communities.

representativeness_notes: >
  The dataset captures only players who opt in to the aoe2companion service.
  Player segments without the application (particularly console players and
  players from regions with lower service awareness) are absent.
---

# aoe2companion -- Raw Data

CDN dump from the aoe2companion service. Files downloaded on 2026-04-06 from
[https://dump.cdn.aoe2companion.com/](https://dump.cdn.aoe2companion.com/).
This directory holds the raw data layer and must never be modified.

**License:** Unknown -- no license file in source
**Acquisition date:** 2026-04-06
**Acquisition script:** `src/rts_predict/games/aoe2/datasets/aoe2companion/data/acquisition.py`
**Manifest:** `src/rts_predict/games/aoe2/datasets/aoe2companion/data/api/api_dump_list.json`

> **File counts and sizes:** To be repopulated from 01_01_01 artifacts after rerun. Dotfiles excluded
> (.gitkeep x4, .DS_Store x1). Counts reflect data files only.

## Subdirectory Layout

| Directory | Contents | Pattern | File count | Size (MB) |
|-----------|----------|---------|-----------|-----------|
| `matches/` | to be repopulated from 01_01_01 artifacts | `match-{date}.parquet` | — | — |
| `leaderboards/` | to be repopulated from 01_01_01 artifacts | `leaderboard.parquet` | — | — |
| `profiles/` | to be repopulated from 01_01_01 artifacts | `profile.parquet` | — | — |
| `ratings/` | to be repopulated from 01_01_01 artifacts | `rating-{date}.csv` | — | — |

**Total files:** to be repopulated from 01_01_01 artifacts
**Total size:** to be repopulated from 01_01_01 artifacts

## Temporal Coverage

- **Grain:** to be populated from 01_01_01 artifact date_analysis
- **Date range:** to be repopulated from 01_01_01 artifacts
- **Gap analysis status:** not_started
- **Known gaps:** to be repopulated from 01_01_01 artifacts

## Excluded Formats

CSV equivalents of matches, leaderboards, and profiles exist in the manifest
but were not downloaded. Parquet was chosen for size and query performance.
Rating CSVs have no parquet equivalent and are downloaded.

## Known Limitations

- Coverage limited to aoe2companion service users; non-users are absent
- May under-represent casual or non-English-speaking communities

## Inventory Artifact

`src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`
