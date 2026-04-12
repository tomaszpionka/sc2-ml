---
# raw_data_readme v2 -- conforms to docs/templates/raw_data_readme_template.yaml

# -- Section A: Identity -------------------------------------------------------

game: sc2
dataset: sc2egset
raw_directory: src/rts_predict/games/sc2/datasets/sc2egset/data/raw/

# -- Section B: Provenance -----------------------------------------------------

source_name: "SC2EGSet -- StarCraft II Esport Replay and Game-state Dataset"
source_url: "https://zenodo.org/records/17829625"
source_type: cdn_download
source_version: "v2.1.0 (Published 2025-12-05)"
source_doi: "10.1038/s41597-023-02510-7"
data_creator: "Bialecki, A. et al."
sampling_mechanism: >
  tournament_only -- replays from publicly released esports tournaments only;
  ladder and amateur games excluded.
citation: Bialecki2023
license: CC-BY-4.0
acquisition_date: "2025-12-05"
# acquisition_date note: manual download from Zenodo; date is publication date of v2.1.0

# acquisition_script omitted -- data was downloaded manually without a script

# -- Section C: Content and Layout ---------------------------------------------

description: # to be repopulated from 01_01_01 artifacts
file_format: "JSON (SC2Replay export)"

# File counts and sizes to be repopulated from 01_01_01 artifacts after rerun.
# Dotfiles excluded (9 x .DS_Store). Counts reflect replay JSON files only;
# metadata files (map_foreign_to_english_mapping.json per tournament) are
# counted separately in total_files but sizes are not measured.
subdirectory_layout:
  - directory: "2016_IEM_10_Taipei/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2016_IEM_11_Shanghai/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2016_WCS_Winter/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2017_HomeStory_Cup_XV/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2017_HomeStory_Cup_XVI/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2017_IEM_Shanghai/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2017_IEM_XI_World_Championship_Katowice/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2017_WCS_Austin/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2017_WCS_Global_Finals/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2017_WCS_Jonkoping/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2017_WCS_Montreal/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2017_WESG_Barcelona/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2017_WESG_Haikou/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2018_Cheeseadelphia_8/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2018_HomeStory_Cup_XVII/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2018_HomeStory_Cup_XVIII/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2018_IEM_Katowice/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2018_IEM_PyeongChang/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2018_WCS_Austin/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2018_WCS_Global_Finals/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2018_WCS_Leipzig/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2018_WCS_Montreal/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2018_WCS_Valencia/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2018_WESG_Grand_Finals/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2019_Assembly_Summer/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2019_HomeStory_Cup_XIX/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2019_HomeStory_Cup_XX/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2019_IEM_Katowice/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2019_WCS_Fall/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2019_WCS_Grand_Finals/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2019_WCS_Spring/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2019_WCS_Summer/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2019_WCS_Winter/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2020_05_Dreamhack_Last_Chance/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2020_ASUS_ROG_Online/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2020_Dreamhack_SC2_Masters_Fall/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2020_Dreamhack_SC2_Masters_Summer/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2020_IEM_Katowice/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2020_StayAtHome_Story_Cup_1/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2020_StayAtHome_Story_Cup_2/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2020_TSL5/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2020_TSL6/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2021_ASUS_ROG_Fall/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2021_Cheeseadelphia_Winter_Championship/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2021_Dreamhack_SC2_Masters_Fall/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2021_Dreamhack_SC2_Masters_Summer/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2021_Dreamhack_SC2_Masters_Winter/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2021_IEM_Katowice/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2021_StayAtHome_Story_Cup_3/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2021_StayAtHome_Story_Cup_4/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2021_TSL7/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2021_TSL8/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2022_03_DH_SC2_Masters_Atlanta/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2022_Dreamhack_SC2_Masters_Last_Chance2021/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2022_Dreamhack_SC2_Masters_Valencia/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2022_HomeStory_Cup_XXI/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2022_HomeStory_Cup_XXII/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2022_IEM_Katowice/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2022_TSL9/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2023_01_IEM_Katowice/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2023_04_ESL_SC2_Masters_Summer_Finals/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2023_05_Gamers8/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2023_07_ESL_SC2_Masters_Winter_Finals/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2023_HomeStory_Cup_XXIV/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2024_01_IEM_Katowice/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2024_03_ESL_SC2_Masters_Spring_Finals/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2024_05_EWC/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2024_HomeStory_Cup_XXV/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2024_HomeStory_Cup_XXVI/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts
  - directory: "2024_StaraZagora_BellumGensElite/"
    contents: # to be repopulated from 01_01_01 artifacts
    file_pattern: "<sha256_hash>.SC2Replay.json"
    file_count: # to be repopulated from 01_01_01 artifacts
    size_mb: # to be repopulated from 01_01_01 artifacts

total_files: # to be repopulated from 01_01_01 artifacts
total_size_mb: # to be repopulated from 01_01_01 artifacts

# -- Section D: Temporal Coverage ----------------------------------------------

temporal_grain: # to be populated from 01_01_01 artifact date_analysis
# date_range_start: # to be repopulated from 01_01_01 artifacts
# date_range_end: # to be repopulated from 01_01_01 artifacts
date_range_start: # to be repopulated from 01_01_01 artifacts
date_range_end: # to be repopulated from 01_01_01 artifacts
known_gaps: []
gap_analysis_status: partial
# coverage_notes: stripped -- forward references to steps not yet complete

# -- Section E: Acquisition Filtering ------------------------------------------

# acquisition_filters: no filtering was performed; all files from Zenodo v2.1.0 downloaded.

excluded_formats:
  - format: ".SC2Replay (binary)"
    reason: >
      Binary replay files require a running StarCraft II client to parse.
      The JSON export format was chosen because it is human-readable and
      parseable without game client dependencies. SC2EGSet distributes
      JSON exports, not binary replays.

# -- Section F: Verification ---------------------------------------------------

checksum_status: none
# No file-level checksums were verified for replay JSON files.
# The map_foreign_to_english_mapping.json files were checked for
# cross-tournament consistency during Phase 01 profiling (01_01_01 notebook),
# but this is a content-consistency check, not a file-integrity checksum.

# checksum_source and checksum_verified omitted -- checksum_status is none.

# -- Section G: Immutability and Artifact Link ---------------------------------

immutability:
  status: true
  enforcement_mechanism: none_documented

inventory_artifact: "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"

notes: >
  Acquired by manual download from Zenodo record 17829625 (v2.1.0, published
  2025-12-05). Numeric fields will be repopulated from 01_01_01 artifact after
  rerun. Dotfiles to be excluded (9 x .DS_Store). Per-tournament sizes cover
  replay JSON files only; metadata file sizes not measured separately.

# -- Section H: Known Limitations ----------------------------------------------

known_biases: >
  Tournament-only coverage introduces survivorship bias: only games from
  professional players who competed in events with publicly released replays
  are represented. Ladder games and amateur play are absent entirely.

representativeness_notes: >
  Top-tier professional players are over-represented relative to the broader
  StarCraft II player population. Korean players dominate pre-2022 coverage due
  to tournament geography. Coverage broadens geographically from 2022 onward
  following globalization of the esports scene.
---

# SC2EGSet -- Raw Replays

SC2EGSet v2.1.0 contains StarCraft II tournament replay files exported as JSON.
This directory holds the raw data layer and must never be modified.

**Source:** [https://zenodo.org/records/17829625](https://zenodo.org/records/17829625)
**DOI:** 10.1038/s41597-023-02510-7 (Bialecki et al., 2023)
**License:** CC-BY-4.0
**Acquisition date:** 2025-12-05 (manual download; date is Zenodo v2.1.0 publication date)

> **File counts and sizes:** To be repopulated from 01_01_01 artifacts after rerun. Dotfiles
> excluded (9 x .DS_Store). Per-tournament sizes cover replay JSON files only;
> metadata file (map_foreign_to_english_mapping.json) sizes not measured separately.

## Layout

Two-level structure:

Each of the 70 tournament subdirectories contains:
- Per-replay JSON files named 
- A  metadata file

| Metric | Value |
|--------|-------|
| Tournament directories | to be repopulated from 01_01_01 artifacts |
| Total replay files | to be repopulated from 01_01_01 artifacts |
| Total metadata files | to be repopulated from 01_01_01 artifacts |
| **Total files** | to be repopulated from 01_01_01 artifacts |
| Total size | to be repopulated from 01_01_01 artifacts |

## Temporal Coverage

- **Grain:** to be populated from 01_01_01 artifact date_analysis
- **Date range:** to be repopulated from 01_01_01 artifacts
- **Gap analysis status:** not_started

## Verification

No file-level checksums were verified. The 
files were checked for cross-tournament consistency during Phase 01 profiling,
but this is a content-consistency check, not a file-integrity checksum.

## Known Limitations

- Tournament-only survivorship bias; ladder and amateur games absent
- Professional players over-represented relative to the general player population
- Korean players dominate pre-2022 coverage due to tournament geography

## Inventory Artifact


