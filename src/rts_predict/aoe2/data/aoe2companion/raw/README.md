---
# raw_data_readme v2 -- conforms to docs/templates/raw_data_readme_template.yaml

# -- Section A: Identity -------------------------------------------------------

game: aoe2
dataset: aoe2companion
raw_directory: src/rts_predict/aoe2/data/aoe2companion/raw/

# -- Section B: Provenance -----------------------------------------------------

source_name: "aoe2companion CDN dump"
source_url: "https://dump.cdn.aoe2companion.com/"
source_type: cdn_download
data_creator: "aoe2companion (community-run API service)"
sampling_mechanism: >
  exhaustive -- all matches recorded by the aoe2companion service for the
  covered date range; limited to players who use the aoe2companion application.
manifest_path: "src/rts_predict/aoe2/data/aoe2companion/api/api_dump_list.json"
citation: aoe2companion_cdn
license: "Unknown -- no license file in source; check with data_creator before redistribution"
acquisition_date: "2026-04-06"
acquisition_script: "src/rts_predict/aoe2/data/aoe2companion/acquisition.py"

# -- Section C: Content and Layout ---------------------------------------------

description: >
  CDN dump from the aoe2companion service. Contains daily match parquet files,
  leaderboard and profile snapshots, and daily rating CSV files. Mixed
  granularity: match-level and player-level records in separate subdirectories.
  Coverage spans 2020-08-01 to 2026-04-04.
file_format: "parquet, CSV"

# File counts and sizes populated from 01_01_01 artifact (step F.1).
# Dotfiles excluded: .gitkeep x4 (one per subdir), .DS_Store x1 at root.
subdirectory_layout:
  - directory: "matches/"
    contents: "Daily match parquet files"
    file_pattern: "match-{date}.parquet"
    file_count: 2073
    size_mb: 6621.52
  - directory: "leaderboards/"
    contents: "Leaderboard snapshot parquet file"
    file_pattern: "leaderboard.parquet"
    file_count: 1
    size_mb: 83.32
  - directory: "profiles/"
    contents: "Player profile snapshot parquet file"
    file_pattern: "profile.parquet"
    file_count: 1
    size_mb: 161.84
  - directory: "ratings/"
    contents: "Daily rating CSV files"
    file_pattern: "rating-{date}.csv"
    file_count: 2072
    size_mb: 2519.59

total_files: 4149  # excludes 5 dotfiles (.gitkeep x4, .DS_Store x1)
total_size_mb: 9387.8

# -- Section D: Temporal Coverage ----------------------------------------------

temporal_grain: daily
# Dates from 01_01_01 artifact date_analysis.matches
date_range_start: "2020-08-01"
date_range_end: "2026-04-04"

known_gaps:
  - gap_start: "2025-07-10"
    gap_end: "2025-07-12"
    reason: "Missing ratings file for 2025-07-11 (identified in 01_01_01 artifact date_analysis.ratings; matches file for that date is present)"

gap_analysis_status: complete
coverage_notes: >
  Files before 2025-06-27 are sparse (header-only); files from 2025-06-27
  onward are substantive. This boundary was identified during Phase 01 profiling.
  The one-day ratings gap (2025-07-11) affects ratings only; matches data has
  no gaps across the full date range.

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

inventory_artifact: "src/rts_predict/aoe2/reports/aoe2companion/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"

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
**Acquisition script:** `src/rts_predict/aoe2/data/aoe2companion/acquisition.py`
**Manifest:** `src/rts_predict/aoe2/data/aoe2companion/api/api_dump_list.json`

> **File counts and sizes:** Populated from 01_01_01 artifact. Dotfiles excluded
> (.gitkeep x4, .DS_Store x1). Counts reflect data files only.

## Subdirectory Layout

| Directory | Contents | Pattern | File count | Size (MB) |
|-----------|----------|---------|-----------|-----------|
| `matches/` | Daily match parquet files | `match-{date}.parquet` | 2073 | 6,621.5 |
| `leaderboards/` | Leaderboard snapshot | `leaderboard.parquet` | 1 | 83.3 |
| `profiles/` | Player profile snapshot | `profile.parquet` | 1 | 161.8 |
| `ratings/` | Daily rating CSV files | `rating-{date}.csv` | 2072 | 2,519.6 |

**Total files:** 4,149 (excludes 5 dotfiles: .gitkeep x4, .DS_Store x1)
**Total size:** 9,387.8 MB (9.2 GB)

## Temporal Coverage

- **Grain:** daily
- **Date range:** 2020-08-01 to 2026-04-04 (from 01_01_01 artifact)
- **Gap analysis status:** complete
- **Known gaps:** One missing ratings file for 2025-07-11 (matches unaffected)
- **Note:** Files before 2025-06-27 are sparse (header-only); substantive data starts 2025-06-27

## Excluded Formats

CSV equivalents of matches, leaderboards, and profiles exist in the manifest
but were not downloaded. Parquet was chosen for size and query performance.
Rating CSVs have no parquet equivalent and are downloaded.

## Known Limitations

- Coverage limited to aoe2companion service users; non-users are absent
- May under-represent casual or non-English-speaking communities

## Inventory Artifact

`src/rts_predict/aoe2/reports/aoe2companion/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`
