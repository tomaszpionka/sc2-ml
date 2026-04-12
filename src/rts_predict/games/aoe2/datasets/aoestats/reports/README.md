# aoestats -- Dataset Reports Provenance

Permanent provenance record for the aoestats dataset. This file is
independent of the phase system and is not archived when phases are reset.

---

# -- Section A: Identity -------------------------------------------------------

game: aoe2
dataset: aoestats
reports_dir: src/rts_predict/games/aoe2/datasets/aoestats/reports/

# -- Section B: Acquisition provenance -----------------------------------------
# Source: acquisition script execution (pre-Phase 01)

acquisition:
  date: "2026-04-06"
  script: "poetry run aoe2 download aoestats --force"
  branch: "feat/aoe2-phase0-acquisition"
  source: "aoestats.io"
  source_url: "https://aoestats.io"
  method: cdn_download

# -- Section C: File inventory summary -----------------------------------------
# Source: Step 01_01_01 artifact
# Invariant #9: MUST NOT contain interpretive labels. Report file counts,
# sizes, extensions, and filename patterns only.

file_inventory:
  total_files:    # to be repopulated from 01_01_01 artifacts
  total_size_mb:  # to be repopulated from 01_01_01 artifacts
  subdirectories: # to be repopulated from 01_01_01 artifacts
  artifact_ref:   # to be repopulated from 01_01_01 artifacts

# -- Section D: Known issues ----------------------------------------------------
# Source: acquisition script logs or 01_01_01 artifact
# Report filesystem-level facts only.

known_issues:
  - "171 files in players/ vs 172 in matches/"

# -- Section E: Reconciliation --------------------------------------------------
# Source: acquisition script verification

reconciliation:
  strength: DEGRADED
  reason: "manifest lacks per-file row counts; limited to file-count match"

# -- Section F: Provenance rule -------------------------------------------------

provenance_rule: >
  Raw data is immutable. The weekly dump download will not be repeated.
