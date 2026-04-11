# Category C Plan: Template Hierarchy Restructuring

**Category:** C (chore)
**Branch:** `chore/template-hierarchy`
**Date:** 2026-04-11

---

## Scope

Fill four empty template YAMLs, create three new status template YAMLs, enhance
three existing status files per dataset, and update cross-cutting references.
Total: 5 new files, 4 populated-from-empty files, 10 modified files.

## Prerequisite observation

The project has a well-defined three-level hierarchy (Phase > Pipeline Section >
Step) documented in `docs/TAXONOMY.md` and `docs/PHASES.md`. The template system
currently has complete schemas only at the leaf level (`step_template.yaml`,
`research_log_entry_template.yaml`). The Phase and Pipeline Section levels have
empty placeholders. Status tracking files exist but lack the upward linking
fields needed to derive Pipeline Section and Phase status from Step status.

The derivation direction is: Steps are authoritative, Pipeline Section status is
derived from Steps, Phase status is derived from Pipeline Sections. This matches
the existing STEP_STATUS.yaml comment: "Phase is complete when ALL its steps are
complete."

---

## Execution steps

### Step 1: Create `docs/templates/phase_template.yaml`

**Purpose:** Template for how a Phase appears in a dataset ROADMAP.md. This is
not a status file template — it is the ROADMAP authoring template (the Phase
block that a ROADMAP author copies when adding a new Phase to a dataset ROADMAP).

**Fields (using `value:` + `required:` pattern):**

```yaml
# -- Identity --
phase_number:
  value: "<NN>"           # Two-digit zero-padded
  required: true

name:
  value: "<phase name from docs/PHASES.md>"
  required: true

# -- Source --
source_manual:
  value: "<docs/ml_experiment_lifecycle/NN_MANUAL_NAME.md>"
  required: true

canonical_reference:
  value: "docs/PHASES.md"
  required: true
  # This is always docs/PHASES.md. Included to make the derivation explicit.

# -- Dataset context --
dataset:
  value: "<sc2egset | aoe2companion | aoestats>"
  required: true

# -- Pipeline Sections --
pipeline_sections:
  value:
    - number: "<NN_NN>"
      name: "<pipeline section name from docs/PHASES.md>"
  required: true
  # The list must match docs/PHASES.md exactly. ROADMAPs do not invent,
  # rename, or omit Pipeline Sections.

# -- Gate --
gate:
  exit_criteria:
    value: "<what must hold for this Phase to be considered complete>"
    required: true
  is_gate_marker:
    value: false
    required: true
    # true only for Phase 07

# -- Status derivation rule --
status_derivation:
  description: >
    Phase status is derived from Pipeline Section statuses (which are
    themselves derived from Step statuses):
      complete    -- all Pipeline Sections are complete
      in_progress -- any Pipeline Section is in_progress or complete
      not_started -- no Pipeline Section has started
  required: false
  # Informational. Not a field to be filled in -- it documents the rule.
```

**Comment header:** Follows the pattern from step_template.yaml. References
TAXONOMY.md, PHASES.md, scientific-invariants.md.

**Special case for Phase 07:** The template includes `is_gate_marker` field. When
true, `pipeline_sections` is empty and `gate/exit_criteria` describes the gate
condition from PHASES.md.

---

### Step 2: Create `docs/templates/pipeline_section_template.yaml`

**Purpose:** Template for how a Pipeline Section appears within a Phase in a
dataset ROADMAP. This defines the Pipeline Section block structure that ROADMAP
authors use.

**Fields:**

```yaml
# -- Identity --
section_number:
  value: "<NN_NN>"        # Phase_Section, zero-padded
  required: true

name:
  value: "<pipeline section name from docs/PHASES.md>"
  required: true

# -- Hierarchy context --
phase:
  value: "<NN -- phase name>"
  required: true

manual_section:
  value: "<manual_filename.md, section or part number>"
  required: true

canonical_reference:
  value: "docs/PHASES.md"
  required: true

# -- Dataset context --
dataset:
  value: "<sc2egset | aoe2companion | aoestats>"
  required: true

# -- Steps --
steps:
  value:
    - step_number: "<NN_NN_NN>"
      name: "<step name>"
  required: true
  # Steps are defined in full using docs/templates/step_template.yaml.
  # This field is a summary index; full Step definitions are fenced
  # YAML blocks in the ROADMAP.

# -- Gate --
gate:
  exit_criteria:
    value: "<what must hold for this Pipeline Section to be complete>"
    required: true

# -- Status derivation rule --
status_derivation:
  description: >
    Pipeline Section status is derived from Step statuses:
      complete    -- all Steps are complete
      in_progress -- any Step is in_progress or complete
      not_started -- no Step has started
  required: false
```

---

### Step 3: Create `docs/templates/dataset_roadmap_template.yaml`

**Purpose:** Template for the overall structure of a dataset-level ROADMAP.md
file. Documents what sections a ROADMAP must contain and in what order.

**Fields (structural — describes document layout):**

```yaml
header:
  game:
    value: "<game identifier>"
    required: true
  dataset:
    value: "<dataset identifier>"
    required: true
  role:
    value: "<PRIMARY | SUPPLEMENTARY VALIDATION | omit if sole dataset>"
    required: false
    # Only for games with multiple datasets.
  canonical_references:
    value:
      canonical_phase_list: "docs/PHASES.md"
      methodology_manuals: "docs/INDEX.md"
      step_schema: "docs/templates/step_template.yaml"
    required: true

usage_section:
  heading: "## How to use this document"
  description: >
    Prose block explaining that this ROADMAP decomposes Phases into
    Pipeline Sections and Steps. Must state that the canonical Phase and
    Pipeline Section definitions live in docs/PHASES.md, and that this
    ROADMAP does not invent them. Must describe the XX_YY_ZZ numbering.
  required: true

source_data_section:
  heading: "## Source data"
  description: >
    Dataset provenance: citation, row counts, known issues, temporal
    coverage, warnings about snapshot tables or schema drift.
    Pre-Phase-01 values are marked with a provenance caveat.
  required: true

phase_sections:
  description: >
    One ## section per Phase (01 through 07).
  active_phase_structure:
    heading: "## Phase NN -- Phase Name"
    pipeline_section_list: "Bullet list: `NN_NN` -- Pipeline Section Name"
    step_definitions: "Fenced YAML blocks per docs/templates/step_template.yaml"
  placeholder_phase_structure:
    heading: "## Phase NN -- Phase Name (placeholder)"
    body: "Pipeline Sections: see `docs/PHASES.md`. Steps to be defined when Phase NN-1 gate is met."
  gate_marker_structure:
    heading: "## Phase 07 -- Thesis Writing Wrap-up (gate marker)"
    body: "Per `docs/PHASES.md`, Phase 07 is a gate marker with no Pipeline Sections."
  required: true
```

---

### Step 4: Create `docs/templates/research_log_template.yaml`

**Purpose:** Template for the overall structure of `reports/research_log.md`
(the container, not individual entries). The entry template already exists as
`research_log_entry_template.yaml`.

**Fields:**

```yaml
document:
  path: "reports/research_log.md"
  description: >
    Unified chronological narrative of all research decisions and
    findings, tagged by dataset. Newest entries first.
  required: true

header:
  thesis_title:
    value: "<full thesis title>"
    required: true
  ordering: "Reverse chronological (newest first)"
  required: true

entry_template:
  path: "docs/templates/research_log_entry_template.yaml"
  markdown_rendering: "reports/RESEARCH_LOG_TEMPLATE.md"
  # reports/RESEARCH_LOG_TEMPLATE.md already exists on disk as a human-readable
  # rendering of the entry template. It is not modified by this PR — the YAML
  # template is the authoritative schema; the .md rendering is a convenience.
  required: true

hierarchy_linking:
  description: >
    Each entry's title includes a Phase/Step reference
    (e.g., "[Phase 01 / Step 01_01_01]") that links it to the
    Phase > Pipeline Section > Step hierarchy. Non-Phase entries
    use [CROSS] or [CHORE] tags. The Pipeline Section is
    implicit in the Step number (first two components).
  required: true

dataset_tags:
  allowed: ["sc2egset", "aoe2companion", "aoestats", "CROSS"]
  description: >
    Every entry must specify its dataset scope. CROSS is used for
    entries that span multiple datasets or are game-agnostic.
  required: true

cross_references:
  to_roadmaps: >
    Entry artifacts must match paths declared in the ROADMAP step
    definition's outputs field.
  to_step_status: >
    Completion of a research log entry is a prerequisite for marking
    a Step as complete in STEP_STATUS.yaml.
  required: true
```

---

### Step 5: Enhance STEP_STATUS.yaml across all 3 datasets

**What changes:** Add `pipeline_section` field to each step entry (upward link
from Step to Pipeline Section). Add `game` field to header for consistency with
PHASE_STATUS.yaml.

**sc2egset** `src/rts_predict/sc2/reports/sc2egset/STEP_STATUS.yaml`:
```yaml
game: sc2
dataset: sc2egset

steps:
  "01_01_01":
    name: "File Inventory"
    pipeline_section: "01_01"
    status: complete
    completed_at: "2026-04-09"
```

**aoe2companion** — same change: add `game: aoe2`, add `pipeline_section: "01_01"`.

**aoestats** — same change: add `game: aoe2`, add `pipeline_section: "01_01"`.

**Update derivation rule comments** in all 3 STEP_STATUS.yaml files. The existing
comments say "PHASE_STATUS.yaml is derived from this file" (a direct Step ->
Phase rule). Replace with the three-tier chain:

```yaml
# PIPELINE_SECTION_STATUS.yaml is derived from this file:
#   Pipeline section is complete    when ALL its steps are complete.
#   Pipeline section is in_progress when ANY step is in_progress or complete.
#   Pipeline section is not_started when NO step has started.
#
# Derivation chain:
#   this file -> PIPELINE_SECTION_STATUS.yaml -> PHASE_STATUS.yaml
```

This ensures all three status files describe the same derivation chain
consistently.

---

### Step 6: Populate PIPELINE_SECTION_STATUS.yaml across all 3 datasets

**What:** sc2egset already has an empty file. aoe2companion and aoestats need
the file created.

**Structure (shared across datasets, differing in game/dataset and trailing
comment — see aoestats note below):**

```yaml
# Pipeline Section status for <dataset>.
# Derived from STEP_STATUS.yaml.
# If this file disagrees with STEP_STATUS.yaml, this file is wrong.
#
# PHASE_STATUS.yaml is derived from this file:
#   Phase is complete    when ALL its pipeline sections are complete.
#   Phase is in_progress when ANY pipeline section is in_progress or complete.
#   Phase is not_started when NO pipeline section has started.
#
# This file is derived from STEP_STATUS.yaml:
#   Pipeline section is complete    when ALL its steps are complete.
#   Pipeline section is in_progress when ANY step is in_progress or complete.
#   Pipeline section is not_started when NO step has started.

game: <sc2|aoe2>
dataset: <dataset>

pipeline_sections:
  "01_01":
    name: "Data Acquisition & Source Inventory"
    phase: "01"
    status: in_progress
  "01_02":
    name: "Exploratory Data Analysis (Tukey-style)"
    phase: "01"
    status: not_started
  "01_03":
    name: "Systematic Data Profiling"
    phase: "01"
    status: not_started
  "01_04":
    name: "Data Cleaning"
    phase: "01"
    status: not_started
  "01_05":
    name: "Temporal & Panel EDA"
    phase: "01"
    status: not_started
  "01_06":
    name: "Decision Gates"
    phase: "01"
    status: not_started
  # Pipeline sections for later Phases added when those Phases become active.
  # Phase 07 has no pipeline sections.
  #
  # NOTE: Only Phase 01 pipeline sections are listed here. PHASE_STATUS.yaml
  # lists all 7 phases (including not_started ones). This asymmetry is
  # intentional — pipeline sections are added incrementally as Phases activate,
  # not pre-populated.
```

**Dataset-specific trailing comment:**
- **sc2egset, aoe2companion:** `# Pipeline sections for Phases 02-06 added when those Phases become active.`
- **aoestats:** `# Pipeline sections for Phases 02-05 added when those Phases become active. Phase 06 is out of scope (SUPPLEMENTARY VALIDATION role — see ROADMAP).`

**Note:** 01_01 is `in_progress` because step 01_01_01 is complete but the
Pipeline Section's full step list is not yet determined to be complete.

---

### Step 7: Update PHASE_STATUS.yaml for derivation chain clarity (all 3 datasets)

**What changes:** Add a comment referencing the derivation chain. No structural
changes to the fields.

Add after existing derivation comment:
```yaml
# Derivation chain:
#   STEP_STATUS.yaml -> PIPELINE_SECTION_STATUS.yaml -> this file
# Phase status is derived from pipeline section statuses.
# See PIPELINE_SECTION_STATUS.yaml for the intermediate derivation.
```

No field additions needed — the existing `phases:` map with `name` and `status`
per phase is sufficient.

---

### Step 8: Create status template YAMLs in `docs/templates/`

Three new files defining the schema for status tracking files.

**8a. `docs/templates/phase_status_template.yaml`** — schema for
PHASE_STATUS.yaml files. Fields: file_path, game, dataset, dataset_roadmap,
derived_from, phases (entry_schema with phase_number, name, status + derivation
rule).

**8b. `docs/templates/pipeline_section_status_template.yaml`** — schema for
PIPELINE_SECTION_STATUS.yaml files. Fields: file_path, game, dataset,
derived_from, feeds, pipeline_sections (entry_schema with section_number, name,
phase, status + derivation rule).

**8c. `docs/templates/step_status_template.yaml`** — schema for
STEP_STATUS.yaml files. Fields: file_path, game, dataset, feeds, steps
(entry_schema with step_number, name, pipeline_section, status, completed_at
when complete).

---

### Step 9: Update ARCHITECTURE.md references

**Game package contract table additions** (STEP_STATUS.yaml is also currently
absent from the table — a pre-existing gap that this PR fixes):
```
| `reports/<dataset>/STEP_STATUS.yaml` | Machine-readable step progress (dataset-scoped) | Per dataset |
| `reports/<dataset>/PIPELINE_SECTION_STATUS.yaml` | Machine-readable pipeline section progress (dataset-scoped) | Per dataset |
```
Note: PHASE_STATUS.yaml is already in the table. The executor adds the two rows
above adjacent to it. Net result: all three status files are listed.

**Source-of-Truth Hierarchy update:** Current tier 7 is PHASE_STATUS.yaml with
prose "Strictly derived from tiers (5) and (6). Never authoritative; never
diverges." This prose must be rewritten to describe the three-tier derivation
chain. New tier 7:

- 7a. STEP_STATUS.yaml — derived from dataset ROADMAPs (tier 6)
- 7b. PIPELINE_SECTION_STATUS.yaml — derived from STEP_STATUS.yaml (tier 7a)
- 7c. PHASE_STATUS.yaml — derived from PIPELINE_SECTION_STATUS.yaml (tier 7b)

All three remain at precedence level 7 — they are all derived status files.
Rewrite the existing tier 7 description to: "Machine-readable status files.
STEP_STATUS is derived from the dataset ROADMAP (tier 6). PIPELINE_SECTION_STATUS
is derived from STEP_STATUS. PHASE_STATUS is derived from PIPELINE_SECTION_STATUS.
None are authoritative; if any disagrees with its upstream source, it is wrong and
gets regenerated."

**Progress tracking section:** Expand the paragraph that currently only mentions
PHASE_STATUS.yaml to describe the full derivation chain.

---

### Step 10: Update CLAUDE.md

Add PIPELINE_SECTION_STATUS.yaml to Key File Locations:
```
- Pipeline section status: `src/rts_predict/<game>/reports/<dataset>/PIPELINE_SECTION_STATUS.yaml`
```

---

### Step 11: Update CHANGELOG.md

Add under `[Unreleased]`:

```
### Added
- `docs/templates/phase_template.yaml` — ROADMAP authoring template for Phase blocks
- `docs/templates/pipeline_section_template.yaml` — ROADMAP authoring template for Pipeline Section blocks
- `docs/templates/dataset_roadmap_template.yaml` — ROADMAP document structure template
- `docs/templates/research_log_template.yaml` — research log document structure template
- `docs/templates/phase_status_template.yaml` — schema for PHASE_STATUS.yaml files
- `docs/templates/pipeline_section_status_template.yaml` — schema for PIPELINE_SECTION_STATUS.yaml files
- `docs/templates/step_status_template.yaml` — schema for STEP_STATUS.yaml files
- PIPELINE_SECTION_STATUS.yaml for all 3 datasets (sc2egset, aoe2companion, aoestats)

### Changed
- STEP_STATUS.yaml: added `game` and `pipeline_section` fields (all 3 datasets)
- PHASE_STATUS.yaml: added derivation chain comments (all 3 datasets)
- ARCHITECTURE.md: documented full status tracking hierarchy
- CLAUDE.md: added PIPELINE_SECTION_STATUS.yaml to Key File Locations
```

---

## Design decisions

1. **ROADMAP templates vs status templates are separate.** `phase_template.yaml`
   defines how a Phase appears in a ROADMAP (authoring guide).
   `phase_status_template.yaml` defines how a Phase appears in PHASE_STATUS.yaml
   (runtime status). These are different concerns at different source-of-truth
   tiers.

2. **Only Phase 01 Pipeline Sections are populated in
   PIPELINE_SECTION_STATUS.yaml.** Phases 02-06 pipeline sections are not yet
   added because those Phases are `not_started`. Adding them would create a large
   file with 44 sections all reading `not_started`. Pipeline sections are added
   when their Phase becomes active, matching how Steps are added to
   STEP_STATUS.yaml incrementally.

3. **The `value:` + `required:` pattern is used in field-level templates** for
   consistency with existing `step_template.yaml`. Document-structure templates
   (`dataset_roadmap_template.yaml`, `research_log_template.yaml`) use the
   pattern where applicable but use `heading:` + `description:` for prose-level
   layout constraints where `value:` would be semantically misleading.

4. **No changes to TAXONOMY.md.** The terminology is already complete. The
   templates implement the taxonomy; they do not extend it.

5. **PIPELINE_SECTION_STATUS.yaml for aoe2 datasets are created** (not just
   populated from empty) because unlike sc2egset which has an empty file, the
   aoe2 datasets have no file at all.

---

## File manifest

**New files (5)** — do not exist on disk:
1. `docs/templates/phase_status_template.yaml`
2. `docs/templates/pipeline_section_status_template.yaml`
3. `docs/templates/step_status_template.yaml`
4. `src/rts_predict/aoe2/reports/aoe2companion/PIPELINE_SECTION_STATUS.yaml`
5. `src/rts_predict/aoe2/reports/aoestats/PIPELINE_SECTION_STATUS.yaml`

**Populated from empty (4)** — exist on disk as 0-byte tracked files:
6. `docs/templates/phase_template.yaml`
7. `docs/templates/pipeline_section_template.yaml`
8. `docs/templates/dataset_roadmap_template.yaml`
9. `docs/templates/research_log_template.yaml`

**Modified files (10):**
10. `src/rts_predict/sc2/reports/sc2egset/STEP_STATUS.yaml`
11. `src/rts_predict/aoe2/reports/aoe2companion/STEP_STATUS.yaml`
12. `src/rts_predict/aoe2/reports/aoestats/STEP_STATUS.yaml`
13. `src/rts_predict/sc2/reports/sc2egset/PIPELINE_SECTION_STATUS.yaml` (populated from empty)
14. `src/rts_predict/sc2/reports/sc2egset/PHASE_STATUS.yaml`
15. `src/rts_predict/aoe2/reports/aoe2companion/PHASE_STATUS.yaml`
16. `src/rts_predict/aoe2/reports/aoestats/PHASE_STATUS.yaml`
17. `ARCHITECTURE.md`
18. `CLAUDE.md`
19. `CHANGELOG.md`

---

## Gate condition

All 19 files listed in the manifest exist on disk with non-empty content. The
derivation chain is consistent: every step in STEP_STATUS.yaml has a
`pipeline_section` field, every pipeline section in PIPELINE_SECTION_STATUS.yaml
has a `phase` field, and the derived statuses are consistent (01_01 is
`in_progress` because 01_01_01 is `complete`, Phase 01 is `in_progress` because
01_01 is `in_progress`).

---

## Adversarial Review

**Reviewer:** reviewer-adversarial agent
**Date:** 2026-04-11
**Verdict:** REVISE BEFORE EXECUTION → **all issues resolved in-plan (see below)**

### Issues found

**#1 — CRITICAL: Contradictory derivation rule in STEP_STATUS.yaml**

The plan (Step 5) says "Existing derivation rule comments are preserved
unchanged." The existing comments in all three STEP_STATUS.yaml files state:

> PHASE_STATUS.yaml is derived from this file:
> Phase is complete when ALL its steps are complete.

This is a direct Step -> Phase derivation. The new system introduces an
intermediate layer: Step -> PIPELINE_SECTION_STATUS -> PHASE_STATUS. After this
chore, STEP_STATUS.yaml will contain comments claiming it directly feeds
PHASE_STATUS.yaml, while PHASE_STATUS.yaml (Step 7) will contain a new comment
saying "STEP_STATUS.yaml -> PIPELINE_SECTION_STATUS.yaml -> this file."

These two derivation descriptions are mutually contradictory on the same disk.
The STEP_STATUS.yaml comments **must** be updated to say STEP_STATUS feeds
PIPELINE_SECTION_STATUS (not PHASE_STATUS directly). Agents read these comments
at session start to understand the derivation chain.

**#2 — MODERATE: File manifest misclassification**

The manifest lists items 1-4 as "New files" but `phase_template.yaml`,
`pipeline_section_template.yaml`, `dataset_roadmap_template.yaml`,
`research_log_template.yaml` already exist on disk as 0-byte files (empty but
tracked). Items 12-13 are listed as "Modified files" but
`PIPELINE_SECTION_STATUS.yaml` for aoe2companion and aoestats does not exist on
disk — these are file creations, not modifications. Design Decision #5 correctly
acknowledges this but the manifest contradicts it.

Proposed fix: reclassify. Actual split is roughly 5 new + 4 populated-from-empty
+ 8 modified + 2 created-from-nothing.

**#3 — MODERATE: aoestats Phase 06 asymmetry unaddressed**

The aoestats ROADMAP declares "It does not run Phase 06." But the plan's Step 6
uses an identical comment for all three datasets: "Pipeline sections for Phases
02-06 added when those Phases become active." For aoestats, Phase 06 will never
become active. The comment should say "Phases 02-05" for aoestats. Otherwise,
when Phase 06 work begins for sc2egset and aoe2companion, an executor reading
aoestats's PIPELINE_SECTION_STATUS.yaml may incorrectly add Phase 06 sections
there too.

**#4 — MODERATE: ARCHITECTURE.md Source-of-Truth Hierarchy prose inconsistency**

ARCHITECTURE.md tier 7 currently reads: "Strictly derived from tiers (5) and
(6). Never authoritative; never diverges." This means PHASE_STATUS is derived
from ROADMAPs. Under the new system, PHASE_STATUS is derived from
PIPELINE_SECTION_STATUS, which is derived from STEP_STATUS, which is derived
from ROADMAPs. The plan does not update the "Strictly derived from tiers (5) and
(6)" language — it only adds sub-tiers. The existing prose will contradict the
new derivation chain unless also rewritten.

**#5 — MODERATE: STEP_STATUS.yaml missing from ARCHITECTURE.md game package contract**

The plan proposes adding STEP_STATUS.yaml and PIPELINE_SECTION_STATUS.yaml rows
to the game package contract table. But STEP_STATUS.yaml is already absent from
the table (only PHASE_STATUS.yaml is listed). The plan should list three rows to
add, not two.

**#6 — MINOR: `value:` + `required:` pattern stretched for document-structure templates**

`dataset_roadmap_template.yaml` (Step 3) uses the pattern for structural sections
(like `usage_section`, `source_data_section`) that are prose-level layout
descriptions, not fields with concrete placeholder values. The heading is not a
"value" — it is a constraint. Design smell, not a blocker.

**#7 — MINOR: `research_log_template.yaml` references non-existent file**

Step 4 introduces a `markdown_rendering` field pointing to
`reports/RESEARCH_LOG_TEMPLATE.md`. This file already exists on disk at that
path, but it is not mentioned elsewhere in the plan and does not appear in the
file manifest. If it needs updating for consistency, the plan should say so. If
it is left as-is, the template should note that.

**#8 — NOTE: Asymmetry between PHASE_STATUS and PIPELINE_SECTION_STATUS population**

PHASE_STATUS.yaml lists all 7 phases including `not_started` ones.
PIPELINE_SECTION_STATUS.yaml only lists active Phase 01 sections. This asymmetry
is justified (Design Decision #2) but should be explicitly documented in the
status file comments so future executors know it is intentional, not an omission.

### Summary

- 1 critical issue (contradictory derivation comments — must fix in plan)
- 5 moderate issues (manifest accuracy, aoestats asymmetry, ARCHITECTURE.md prose, missing table row, document-level)
- 2 minor issues (template pattern semantics, cross-reference)
- All moderate/minor issues resolvable with plan edits before execution begins

### Resolutions applied

All 8 issues have been resolved by editing the plan above:

- **#1 CRITICAL** — Step 5 now specifies updating STEP_STATUS.yaml derivation
  comments to the three-tier chain (Step -> PIPELINE_SECTION_STATUS -> PHASE_STATUS)
- **#2 MODERATE** — File manifest reclassified: 5 new + 4 populated-from-empty + 10 modified
- **#3 MODERATE** — Step 6 now specifies dataset-specific trailing comments
  (Phases 02-06 for sc2egset/aoe2companion, Phases 02-05 for aoestats)
- **#4 MODERATE** — Step 9 now includes full prose rewrite for ARCHITECTURE.md tier 7
- **#5 MODERATE** — Step 9 now notes STEP_STATUS.yaml was already absent from the
  game package contract table; both rows are additions
- **#6 MINOR** — Design Decision #3 updated to distinguish field-level vs
  document-structure template patterns
- **#7 MINOR** — Step 4 research_log_template.yaml now includes a comment
  clarifying that RESEARCH_LOG_TEMPLATE.md exists and is not modified by this PR
- **#8 NOTE** — Step 6 PIPELINE_SECTION_STATUS.yaml structure now includes an
  explicit comment documenting the asymmetry with PHASE_STATUS.yaml as intentional
