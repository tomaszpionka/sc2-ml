---
# raw_data_readme v2 -- conforms to docs/templates/raw_data_readme_template.yaml

# -- Section A: Identity -------------------------------------------------------

game: aoe2
dataset: aoestats
raw_directory: src/rts_predict/aoe2/data/aoestats/raw/

# -- Section B: Provenance -----------------------------------------------------

source_name: "aoestats.io weekly DB dumps"
source_url: "https://aoestats.io"
source_type: cdn_download
data_creator: "aoestats.io (community statistics service)"
sampling_mechanism: >
  exhaustive -- all matches recorded by aoestats.io for the covered date range;
  selection criteria used by the source service are not publicly documented.
manifest_path: "src/rts_predict/aoe2/data/aoestats/api/db_dump_list.json"
citation: aoestats_io
license: "Unknown -- no license file in source; check with data_creator before redistribution"
acquisition_date: "2026-04-06"
acquisition_script: "src/rts_predict/aoe2/data/aoestats/acquisition.py"

# -- Section C: Content and Layout ---------------------------------------------

description: >
  Weekly database dumps from aoestats.io. Contains paired weekly match and player
  parquet files named by date range, plus a single overview JSON reference file.
  The number of non-zero weeks downloaded (2022-08-28 to 2026-02-07) and the
  count of excluded zero-match weeks are PENDING (awaiting corrected 01_01_01
  artifact). 16 zero-match weeks from the manifest were excluded during
  acquisition (derived from manifest comparison, not from 01_01_01 artifact).
file_format: "parquet, JSON"

# NOTE: All file_count and size_mb values below are PENDING.
# The 01_01_01 file inventory artifact currently counts .gitkeep placeholder files
# present in each subdirectory. A corrected artifact (with post-processing exclusion
# of .gitkeep files and root-level non-data files) is required before these
# numbers can be populated.
subdirectory_layout:
  - directory: "matches/"
    contents: "Weekly match parquet files named {start_date}_{end_date}_matches.parquet"
    file_pattern: "{start_date}_{end_date}_matches.parquet"
    file_count: "PENDING: awaiting corrected 01_01_01 artifact"
    size_mb: "PENDING: awaiting corrected 01_01_01 artifact"
  - directory: "players/"
    contents: "Weekly player parquet files named {start_date}_{end_date}_players.parquet"
    file_pattern: "{start_date}_{end_date}_players.parquet"
    file_count: "PENDING: awaiting corrected 01_01_01 artifact"
    size_mb: "PENDING: awaiting corrected 01_01_01 artifact"
  - directory: "overview/"
    contents: "Overview JSON reference file with lookup tables (civilizations, maps, game modes)"
    file_pattern: "overview.json"
    file_count: "PENDING: awaiting corrected 01_01_01 artifact"
    size_mb: "PENDING: awaiting corrected 01_01_01 artifact"

# total_files is PENDING: the 01_01_01 artifact currently counts .gitkeep files
# in each subdirectory. A corrected artifact with post-processing exclusion of
# .gitkeep files and root-level non-data files is required.
total_files: "PENDING: awaiting corrected 01_01_01 artifact"
# total_size_mb is PENDING: same artifact correction required as total_files.
total_size_mb: "PENDING: awaiting corrected 01_01_01 artifact"

# -- Section D: Temporal Coverage ----------------------------------------------

temporal_grain: weekly
# Dates from 01_01_01 artifact date_analysis.matches
date_range_start: "2022-08-28"
date_range_end: "2026-02-07"

# Gaps identified in 01_01_01 artifact date_analysis. Matches and players share
# the same first three gaps; players has one additional gap.
known_gaps:
  - gap_start: "2024-07-20"
    gap_end: "2024-09-01"
    reason: "43-day gap in weekly dumps; present in both matches and players (01_01_01 artifact)"
  - gap_start: "2024-09-28"
    gap_end: "2024-10-06"
    reason: "8-day gap in weekly dumps; present in both matches and players (01_01_01 artifact)"
  - gap_start: "2025-03-22"
    gap_end: "2025-03-30"
    reason: "8-day gap in weekly dumps; present in both matches and players (01_01_01 artifact)"
  - gap_start: "2025-11-15"
    gap_end: "2025-11-23"
    reason: "8-day gap in players dumps only; matches unaffected (01_01_01 artifact date_analysis.players)"

gap_analysis_status: complete
coverage_notes: >
  Per-directory file counts for matches/ and players/ are PENDING (awaiting
  corrected 01_01_01 artifact that excludes .gitkeep files). The paired
  comparison in 01_01_01 shows a count mismatch of 1 between matches and
  players weeks, reflected in the fourth gap entry above.
  16 zero-match weeks from the manifest were excluded during acquisition
  (see acquisition_filters below).

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

inventory_artifact: "src/rts_predict/aoe2/reports/aoestats/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"

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
**Acquisition script:** `src/rts_predict/aoe2/data/aoestats/acquisition.py`
**Manifest:** `src/rts_predict/aoe2/data/aoestats/api/db_dump_list.json`

> **Note on file counts and sizes:** All numeric values (file counts, sizes) are
> PENDING. The 01_01_01 file inventory artifact currently includes `.gitkeep`
> placeholder files in each subdirectory in its counts. A corrected artifact with
> post-processing exclusion of `.gitkeep` files and root-level non-data files is
> required before these numbers can be populated.

## Subdirectory Layout

| Directory | Contents | Pattern | File count | Size (MB) |
|-----------|----------|---------|-----------|-----------|
| `matches/` | Weekly match parquet files | `{start}_{end}_matches.parquet` | PENDING | PENDING |
| `players/` | Weekly player parquet files | `{start}_{end}_players.parquet` | PENDING | PENDING |
| `overview/` | Overview JSON reference | `overview.json` | PENDING | PENDING |

**Total files:** PENDING (awaiting corrected 01_01_01 artifact)
**Total size:** PENDING (awaiting corrected 01_01_01 artifact)

## Temporal Coverage

- **Grain:** weekly
- **Date range:** 2022-08-28 to 2026-02-07 (from 01_01_01 artifact)
- **Gap analysis status:** complete
- **Known gaps:**
  - 2024-07-20 to 2024-09-01 (43 days, both matches and players)
  - 2024-09-28 to 2024-10-06 (8 days, both matches and players)
  - 2025-03-22 to 2025-03-30 (8 days, both matches and players)
  - 2025-11-15 to 2025-11-23 (8 days, players only)

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
- players/ has one fewer file than matches/ (count PENDING corrected artifact)

## Inventory Artifact

`src/rts_predict/aoe2/reports/aoestats/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`
