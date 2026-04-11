# Template Enforcement Audit

Audited: 2026-04-11
Templates dir: `docs/templates/` (14 files)

---

## Enforcement Gap Summary

**The template regime is documentation-only.** All 14 templates are referenced in prose
(CLAUDE.md, AGENT_MANUAL.md, ml-protocol.md, etc.), and real instances largely conform —
but only because humans remember to follow them. The **only active programmatic check** is
`scripts/hooks/check_phases_drift.py`, which validates PHASES.md consistency. Nothing else.

---

## Templates by Enforcement State

### Enforced (human discipline only, but at least referenced strongly)

| Template | Referenced in | Real instances conform? |
|---|---|---|
| `spec_template.md` | planning/specs/README.md, AGENT_MANUAL.md | Yes (6/6 specs) |
| `notebook_template.yaml` | sandbox/README.md | Yes (3 notebooks) — Tier 2/3 planned but not built |
| `raw_data_readme_template.yaml` | (scientific-invariants.md chain) | Yes — files include explicit conformance statements |
| `research_log_entry_template.yaml` | ml-protocol.md, step_template | Yes |

### Referenced but zero programmatic enforcement

| Template | Gaps |
|---|---|
| `dag_template.yaml` | No schema check; real DAG.yaml missing `base_ref` field |
| `step_status_template.yaml` | No field validation, no `completed_at` ↔ `status=complete` check |
| `pipeline_section_status_template.yaml` | No field or derivation-chain validation |
| `phase_status_template.yaml` | No field validation; derivation rule (phase complete iff all sections complete) never verified |
| `step_template.yaml` | Steps embedded as YAML in ROADMAP.md; no schema parse, no cross-ref check against PHASES.md |
| `phase_template.yaml` | Same — embedded, unvalidated |
| `pipeline_section_template.yaml` | Same |
| `dataset_roadmap_template.yaml` | Required sections not validated |
| `research_log_template.yaml` | Reverse-chrono order, tag whitelist — not enforced |

### Orphaned

| Template | Status |
|---|---|
| `dag_status_template.yaml` | Correctly documented as optional/ephemeral; no instances exist |

---

## Per-Template Detail

### `dag_template.yaml`

**Defines:** DAG YAML structure — `dag_id`, `category`, `branch`, `phase_ref`,
`pipeline_section_ref`, `step_refs`, `default_isolation`, `jobs`, `final_review`,
`failure_policy`.

**Real instances:** `planning/dags/DAG.yaml` — mostly conforms; missing `base_ref` field.

**Referenced in:** planning/dags/README.md (line 15), docs/agents/AGENT_MANUAL.md (line 522).

**Enforcement gaps:**
- No pre-commit hook validates DAG.yaml against schema
- No CI check for required fields, field types, or task_group ordering
- Real DAG.yaml lacks `base_ref` (template marks it required)
- No check that `spec_file` paths in jobs resolve to actual files on disk

---

### `dag_status_template.yaml`

**Defines:** DAG execution state tracker — `dag_id`, `branch`, `status`, `jobs`,
`final_review_passed`.

**Real instances:** None — marked optional/ephemeral in planning/dags/README.md.

**Enforcement gaps:** None expected; intentional design. Minor inconsistency: template
implies an active orchestrator tracking state, but no orchestrator is present.

---

### `dataset_roadmap_template.yaml`

**Defines:** Document structure constraints for ROADMAP.md files. Required sections:
`header` (game, dataset, canonical_references), `usage_section`, `source_data_section`,
`phase_sections`.

**Real instances:**
- `docs/research/ROADMAP.md`
- `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md`
- `src/rts_predict/aoe2/reports/aoe2companion/ROADMAP.md`
- `src/rts_predict/aoe2/reports/aoestats/ROADMAP.md`

**Enforcement gaps:**
- No pre-commit hook validates required sections or ordering
- No check that phase numbering matches docs/PHASES.md
- No check that embedded step definitions conform to `step_template.yaml`

---

### `notebook_template.yaml`

**Defines:** Sandbox notebook cell structure (jupytext `.py:percent`). Cells
`cell_01_frontmatter` through `cell_cleanup`. Hard rules: no inline defs, max 50 lines
per cell, read-only DuckDB, logging mandatory.

**Real instances:**
- `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.py`
- `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py`
- `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py`

**Referenced in:** sandbox/README.md (line 70).

**Enforcement gaps:**
- Tier 2 (pre-commit AST cell validation) and Tier 3 (CI notebook lint) are planned but not implemented
- Jupytext sync hook exists (`.pre-commit-config.yaml`) but does not validate cell structure
- Max 50 lines per cell is documented but not enforced; `sandbox/notebook_config.toml` exists but is not actively validated
- No check that all `{placeholders}` are substituted
- Temporal leakage verification cell (required for Phase 02+) not enforced

---

### `phase_status_template.yaml`

**Defines:** `PHASE_STATUS.yaml` schema — `game`, `dataset`, `dataset_roadmap`,
`phases[]` with `phase_number`, `name`, `status`. Includes derivation rules.

**Real instances:**
- `src/rts_predict/sc2/reports/sc2egset/PHASE_STATUS.yaml` — conforms
- `src/rts_predict/aoe2/reports/aoe2companion/PHASE_STATUS.yaml` — conforms
- `src/rts_predict/aoe2/reports/aoestats/PHASE_STATUS.yaml` — conforms

**Referenced in:** CLAUDE.md (line 9 — must read before Category A or F work).

**Enforcement gaps:**
- No pre-commit hook validates schema or required fields
- No check that phase numbers match docs/PHASES.md
- Status values (`not_started | in_progress | complete`) not validated against whitelist
- Derivation rule (phase complete iff all pipeline sections complete) never verified programmatically

---

### `phase_template.yaml`

**Defines:** Phase block structure for ROADMAP authoring — `phase_number`, `name`,
`source_manual`, `canonical_reference`, `dataset`, `pipeline_sections`, `gate`,
`status_derivation`.

**Real instances:** Inline as fenced YAML blocks in all ROADMAP.md files.

**Enforcement gaps:**
- No schema parse of embedded YAML blocks
- No check that `phase_number` is 01–07
- No validation that `pipeline_sections` list matches docs/PHASES.md
- Placeholder vs. active phase distinction documented but not validated

---

### `pipeline_section_status_template.yaml`

**Defines:** `PIPELINE_SECTION_STATUS.yaml` schema — `game`, `dataset`,
`pipeline_sections[]` with `section_number`, `name`, `phase`, `status`.

**Real instances:**
- `src/rts_predict/sc2/reports/sc2egset/PIPELINE_SECTION_STATUS.yaml` — conforms
- `src/rts_predict/aoe2/reports/aoe2companion/PIPELINE_SECTION_STATUS.yaml` — conforms
- `src/rts_predict/aoe2/reports/aoestats/PIPELINE_SECTION_STATUS.yaml` — conforms

**Enforcement gaps:**
- No pre-commit hook validates schema
- `section_number` format (`NN_NN`) not validated
- Derivation rule (complete iff all steps complete) never verified
- No check that only active-phase sections are listed

---

### `pipeline_section_template.yaml`

**Defines:** Pipeline section block for ROADMAP authoring — `section_number`, `name`,
`phase`, `manual_section`, `canonical_reference`, `dataset`, `steps`, `gate`,
`status_derivation`.

**Real instances:** Inline as fenced YAML blocks in ROADMAP.md files.

**Enforcement gaps:**
- No schema parse of embedded YAML blocks
- `section_number` format not validated
- No check that section names match canonical definitions in docs/PHASES.md
- Template rule "ROADMAPs do not invent sections" (line 46) not enforced

---

### `raw_data_readme_template.yaml`

**Defines:** Raw data README schema — 8 mandatory sections (Identity A, Provenance B,
Content & Layout C, Temporal Coverage D, Acquisition Filtering E, Verification F,
Immutability G, Known Limitations H). Complex conditional field logic for Section Z.

**Real instances:**
- `src/rts_predict/sc2/data/sc2egset/raw/README.md` — conforms; explicit conformance statement present
- `src/rts_predict/aoe2/data/aoe2companion/raw/README.md` — conforms; explicit conformance statement present
- `src/rts_predict/aoe2/data/aoestats/raw/README.md` — conforms

**Enforcement gaps:**
- No pre-commit hook validates required fields or enum values
  (`source_type: api | cdn_download | web_scrape | database_export | manual`)
- Invariant #7 ("tilde estimates are not acceptable" in `excluded_count`) documented but not
  validated — could silently accept `~N` values
- Invariant #6 (checksums required) documented but `checksum_status` / `verification_date`
  consistency not verified
- Conditional field logic (e.g., `checksum_coverage_pct` required only when
  `checksum_status == partial`) not enforced
- No check that `inventory_artifact` path resolves to an actual file on disk

---

### `research_log_entry_template.yaml`

**Defines:** Research log entry schema — `entry_title` (date format), `category` (A|C|F),
`dataset`, `artifacts_produced`, and body sections: What, Why, How (reproducibility),
Findings, Decisions taken/deferred, Acknowledged trade-offs, Thesis mapping, Open questions.

**Real instances:** `reports/research_log.md` — two entries present, both conform.

**Referenced in:** `.claude/ml-protocol.md` (line 53), `step_template.yaml` (line 159).

**Enforcement gaps:**
- No pre-commit hook validates entry structure
- `category` whitelist (A | C | F) not enforced
- Conditional sections (How/Findings required for Category A only) not validated
- `artifacts_produced` paths not checked for existence on disk
- `thesis_mapping` references not checked against `thesis/THESIS_STRUCTURE.md`

---

### `research_log_template.yaml`

**Defines:** Container structure for `reports/research_log.md` — header, reverse
chronological ordering, entry template reference, hierarchy linking rules, allowed
`dataset_tags` (sc2egset, aoe2companion, aoestats, CROSS).

**Real instances:** `reports/research_log.md` — conforms (reverse chrono, correct tags).

**Enforcement gaps:**
- No pre-commit hook validates document structure
- Reverse-chronological ordering not enforced
- `dataset_tags` whitelist not validated
- Cross-reference rule ("entry artifacts must match paths in ROADMAP step `outputs` field") not enforced
- No check that research log entry completion is a prerequisite for marking a step complete

---

### `spec_template.md`

**Defines:** Spec file schema — YAML frontmatter: `task_id`, `task_name`, `agent`,
`dag_ref`, `group_id`, `file_scope`, `read_scope`, `category`. Markdown sections:
Objective, Instructions, Verification, Context.

**Real instances:** `planning/specs/spec_01_*.md` through `spec_06_*.md` — all 6 conform.

**Referenced in:** planning/specs/README.md (line 35), docs/agents/AGENT_MANUAL.md (line 524).

**Enforcement gaps:**
- No pre-commit hook validates frontmatter keys
- `task_id` not checked against DAG.yaml task references
- `category` (A–F) not validated against whitelist
- `dag_ref` not checked to resolve to a real file
- Spec numbering (always starts at 01) documented in CLAUDE.md but not enforced

---

### `step_status_template.yaml`

**Defines:** `STEP_STATUS.yaml` schema — `game`, `dataset`, `feeds` (path),
`steps[]` with `step_number`, `name`, `pipeline_section`, `status`, `completed_at`.

**Real instances:**
- `src/rts_predict/sc2/reports/sc2egset/STEP_STATUS.yaml` — conforms
- `src/rts_predict/aoe2/reports/aoe2companion/STEP_STATUS.yaml` — conforms
- `src/rts_predict/aoe2/reports/aoestats/STEP_STATUS.yaml` — conforms

**Enforcement gaps:**
- No pre-commit hook validates schema
- `step_number` format (`NN_NN_NN`) not validated
- `completed_at` presence not checked against `status == complete`
- Step definitions not cross-checked against ROADMAP entries
- Derivation uplink to `PIPELINE_SECTION_STATUS` never verified

---

### `step_template.yaml`

**Defines:** Step definition schema for ROADMAP authoring — Identity, Hierarchy context,
Scientific purpose, Predecessors, Inputs & outputs (duckdb_tables, schema_yamls,
data_artifacts, report), Reproducibility, Gate (artifact_check, continue/halt_predicate),
Traceability (thesis_mapping, research_log_entry).

**Real instances:** Inline as fenced YAML blocks in ROADMAP.md files.

**Enforcement gaps:**
- No schema parse of embedded YAML blocks
- `step_number` format (`NN_NN_NN`) not validated
- `scientific_invariants_applied` references not checked against `.claude/scientific-invariants.md`
- Notebook path convention (`sandbox/<game>/<dataset>/NN_.../NN_NN_NN_<name>.py`) not enforced
- Predecessor `step_numbers` not checked to exist in ROADMAP or be complete in STEP_STATUS
- Artifact paths not validated against naming convention
- `thesis_mapping` paths not checked against `thesis/THESIS_STRUCTURE.md`
- Gate conditions (continue/halt_predicate) are free-text prose — no schema enforcement

---

## The Core Problem

Three structural issues explain why templates aren't enforced:

1. **Templates are YAML/Markdown docs, not machine-readable schemas.** None are JSON Schema,
   Pydantic models, or `jsonschema`-compatible. A pre-commit hook can't just point at them.

2. **Status files embed derivation logic in prose comments** (`status_derivation:` blocks),
   but nothing runs that logic. The chain `step → pipeline_section → phase` can silently go
   stale.

3. **ROADMAP step/phase blocks are fenced YAML inside Markdown.** Extracting and validating
   them requires a custom parser — harder than validating standalone YAML files.

---

## Practical Path to Enforcement (prioritized)

### Tier 1 — Low effort, high value (standalone YAML files)

Add a pre-commit hook (~50 lines Python each) that validates the standalone status files:
`STEP_STATUS.yaml`, `PIPELINE_SECTION_STATUS.yaml`, `PHASE_STATUS.yaml`. Check:
- Required fields populated
- Enum values valid (`not_started | in_progress | complete`)
- `completed_at` present iff `status == complete`
- Derivation chain holds (recompute expected status from children, diff against actual)

### Tier 2 — Medium effort

- `DAG.yaml`: validate that every `spec_file` reference exists on disk (catches broken
  materialization immediately)
- `spec_*.md`: validate YAML frontmatter has required keys; `dag_ref` resolves to real file
- `raw_data_readme`: validate Section Z fields against allowed enums already defined in
  template; reject tilde estimates in `excluded_count`

### Tier 3 — High effort, highest value

- ROADMAP embedded YAML: parser that extracts fenced `yaml` blocks and validates them against
  step/phase/pipeline-section schemas; cross-checks against docs/PHASES.md
- Notebook cell structure: implement the Tier 2 cell validator already described in
  `notebook_template.yaml` lines 14–17

### Highest-risk gap to close first

The derivation chain is the most dangerous silent failure mode: a stale `PHASE_STATUS.yaml`
could cause Category A work to begin a phase that is not actually complete. A single script
that reads all `STEP_STATUS.yaml` files, recomputes expected `PIPELINE_SECTION_STATUS` and
`PHASE_STATUS` from scratch, and diffs against actual files would catch this with ~80 lines
of Python.

---                                                                                                                                                                                                         
### Quick Win Available Now
The derivation chain is the highest risk because a stale PHASE_STATUS.yaml would cause
Category A work to start a phase that isn't actually complete. A single script that:
1. Reads all three STEP_STATUS.yaml files                                                                                                                                                                               
2. Recomputes expected PIPELINE_SECTION_STATUS and PHASE_STATUS from scratch
3. Diffs against actual files                                                                                                                                                                                           