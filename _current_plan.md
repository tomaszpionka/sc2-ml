# Plan: Raw Data README Template (v2 — revised after adversarial review)

**Category:** C — Chore
**Branch:** `chore/raw-data-readme-template`
**Date:** 2025-04-10

---

## Motivation (unchanged from v1)

Three `raw/README.md` files exist across the project, each ad-hoc. The template
standardizes the schema for three audiences: ML pipeline, thesis (Chapter 3),
and reproducibility auditors.

## Relationship to Scientific Invariants (unchanged)

- **Invariant #6 (Reproducibility):** Source URLs, acquisition methods, verification.
- **Invariant #7 (No magic numbers):** Acquisition filters must state rule, justification, exact count.
- **Invariant #8 (Cross-game comparability):** Game-agnostic schema; SC2 and AoE2 use same fields.

---

## Changes from v1, Organized by Finding

### BLOCKER 1: Example values contradict Phase 01 artifacts

**Problem:** v1 uses sc2egset-specific numbers as ground truth but they're wrong.
01_01_01 will be rerun (separate PR), so no concrete numbers are reliable now.

**Fix:** Template body uses only angle-bracket `<PLACEHOLDER>` tokens (pure schema).
A separate **Section Z — Examples Appendix** provides two illustrative snippets
(SC2-shaped and AoE2-shaped), each prefixed with:
`# ILLUSTRATIVE ONLY — values are placeholders, not ground truth. Populate from 01_01_01 artifacts.`

### BLOCKER 2: inventory_artifact is required: false

**Problem:** The field that cross-validates Section C totals is optional, making
Invariant #6 structural-in-name-only.

**Fix:** Change to `required: true`. Inline comment documents the bootstrapping
case: *"If Phase 01 profiling has not yet been completed, set value to
`PENDING: 01_01_01 not yet run` — must be updated to a real path before the
raw README is considered complete."*

### BLOCKER 3: impact field uses approximate "~800 replay files"

**Problem:** Tilde violates Invariant #7. The `impact` field mixes count and
description in one string.

**Fix:** Replace single `impact` string with structured sub-fields per filter entry:

```yaml
- rule: "<FILTER_DESCRIPTION>"
  justification: "<JUSTIFICATION>"
  excluded_count: <INTEGER>              # required: true, exact integer
  excluded_count_source: "<DERIVATION>"  # required: true
  notes: "<OPTIONAL_CONTEXT>"            # required: false
```

### WARNING 4: Checksum logic internally inconsistent

**Problem:** "partial" + verified: true but no coverage scope, date, or script.

**Fix:** Expand Section F from 3 fields to 6:

| Field | Required | Type |
|-------|----------|------|
| `checksum_status` | yes | enum: `full`, `partial`, `none` |
| `checksum_source` | conditional (if status != none) | string |
| `checksum_coverage_pct` | conditional (if status == partial) | integer 0–100 |
| `unchecksummed_pattern` | no | string (glob or description) |
| `checksum_verified` | conditional (if status != none) | boolean |
| `verification_date` | conditional (if verified == true) | ISO 8601 date |

Renamed `checksums_available` → `checksum_status` for clarity.

### WARNING 5: known_gaps required: false creates ambiguity

**Problem:** Absent gaps indistinguishable from "not investigated."

**Fix:** Make `known_gaps` `required: true` (empty list `[]` = none found).
Add companion field:

```yaml
gap_analysis_status:
  value: "<complete | partial | not_started>"
  required: true
  # "complete" = all subdirectories checked via 01_01_01
  # "partial" = some checked
  # "not_started" = gaps not yet investigated
```

### WARNING 6: Gebru et al. coverage gap (~7 of 57 questions)

**Judgment:** Full 57-question coverage impractical for 3-dataset thesis.
Add the thesis-relevant subset:

**Added to Section B (Provenance):**

| Field | Required | Rationale |
|-------|----------|-----------|
| `source_version` | no | Version tag, commit SHA, or DOI of specific release |
| `source_doi` | no | DOI if one exists |
| `data_creator` | yes | Who created the original data (distinct from redistributor) |
| `sampling_mechanism` | yes | How records were selected (exhaustive, convenience, stratified, etc.) |

**New Section H — Known Limitations:**

| Field | Required | Rationale |
|-------|----------|-----------|
| `known_biases` | yes | Selection, survivorship, geographic biases. `"None known"` if none. |
| `representativeness_notes` | no | Who/what is over- or under-represented |

**Explicitly deferred** (documented in "Not Covered" comment block): ethical
review, preprocessing-at-source, reuse conditions, update frequency, collector
vs creator distinction beyond `data_creator`.

### WARNING 7: immutable: true is unverifiable

**Decision:** Template is a documentation schema, not enforcement. But it can
document the mechanism. Change bare boolean to structured block:

```yaml
immutability:
  status: true                         # required: true, always true
  enforcement_mechanism: "<MECHANISM>" # required: true
  # Allowed: "none_documented", "read_only_permissions",
  #          "git_lfs_tracked", "directory_hash_verified"
```

Honest answer for current datasets is `none_documented` — convention, not enforced.

### WARNING 8: No AoE2 example despite game-agnosticism claim

**Fix:** Section Z includes both:
1. **SC2-shaped** — tournament-per-directory, hash-named replay JSONs
2. **AoE2-shaped** — date-stamped parquets, paired directories (matches + players),
   mixed granularity, CSV where no parquet alternative exists

Both clearly marked as illustrative.

---

## Revised Template Sections

| Section | Name | Key changes from v1 |
|---------|------|---------------------|
| A | Identity | All `<PLACEHOLDER>` tokens |
| B | Provenance | +`source_version`, +`source_doi`, +`data_creator`, +`sampling_mechanism` |
| C | Content and Layout | All `<PLACEHOLDER>` tokens; no dataset-specific numbers |
| D | Temporal Coverage | `known_gaps` required: true; +`gap_analysis_status` |
| E | Acquisition Filtering | `impact` → `excluded_count` (int) + `excluded_count_source` + `notes` |
| F | Verification | 3 → 6 fields; `checksums_available` → `checksum_status`; conditional requirements |
| G | Immutability and Artifact Link | `immutable` → `immutability` block with `enforcement_mechanism`; `inventory_artifact` required: true |
| H | Known Limitations (NEW) | `known_biases` (required), `representativeness_notes` (optional) |
| Z | Examples Appendix (NEW) | SC2-shaped + AoE2-shaped illustrative snippets with non-authoritative warning |
| -- | Not Covered (comment block) | Deferred Gebru questions with rationale |

---

## Implementation Steps

### Step 1 — Rewrite the template file

**File:** `docs/templates/raw_data_readme_template.yaml`

Replace the entire file with:
- Header comment block referencing PHASES.md, scientific-invariants.md, 01_DATA_EXPLORATION_MANUAL.md
- Usage instructions (same pattern as step_template.yaml)
- Sections A–H using `<PLACEHOLDER>` tokens for all `value:` fields
- Section Z examples appendix with SC2-shaped and AoE2-shaped snippets
- "Not Covered" comment block listing deferred Gebru questions

**Style:** Follow `step_template.yaml` conventions:
- `field: { value: "<PLACEHOLDER>", required: true/false }`
- Inline `#` comments explaining each field
- Invariant references where applicable

### Step 2 — Verification

```bash
source .venv/bin/activate && python3 -c "import yaml; yaml.safe_load(open('docs/templates/raw_data_readme_template.yaml')); print('YAML OK')"
```

---

## Gate Conditions

- [ ] File is non-empty and parses as valid YAML
- [ ] All fields from sections A–H present with `<PLACEHOLDER>` tokens and `required` flags
- [ ] No dataset-specific numbers in template body (only in Section Z, clearly marked)
- [ ] `inventory_artifact` is `required: true` with PENDING sentinel documented
- [ ] `known_gaps` is `required: true` with `gap_analysis_status` companion
- [ ] Acquisition filters use `excluded_count` (int) + `excluded_count_source`, not free-text `impact`
- [ ] Section F has `checksum_status`, `checksum_coverage_pct`, `verification_date`
- [ ] Section G has `immutability.enforcement_mechanism`
- [ ] Section H has `known_biases` (required)
- [ ] Section Z has SC2-shaped and AoE2-shaped examples with non-authoritative warning
- [ ] Inline comments reference invariants #6, #7, #8 where applicable
- [ ] Header references authoritative sources
- [ ] No other files modified

---

## Adversarial Findings Disposition

| # | Type | Finding | Disposition |
|---|------|---------|------------|
| 1 | BLOCKER | Example values contradict artifacts | FIXED: `<PLACEHOLDER>` tokens; examples in Section Z |
| 2 | BLOCKER | inventory_artifact optional | FIXED: required: true with PENDING sentinel |
| 3 | BLOCKER | impact field approximation | FIXED: `excluded_count` (int) + `excluded_count_source` |
| 4 | WARNING | Checksum logic inconsistent | FIXED: 6 fields with conditional requirements |
| 5 | WARNING | known_gaps ambiguity | FIXED: required: true + `gap_analysis_status` |
| 6 | WARNING | Gebru coverage gap | PARTIAL: +6 thesis-relevant fields; remainder deferred with docs |
| 7 | WARNING | immutable unverifiable | PARTIAL: `enforcement_mechanism` field; infrastructure deferred |
| 8 | WARNING | No AoE2 example | FIXED: Section Z AoE2-shaped snippet |

---

## Not in Scope

- Updating existing `raw/README.md` files to conform (separate chore PR)
- Rerunning 01_01_01 to fix stale numbers (separate PR, user-confirmed)
- Validation script for template coverage (future)
- Directory hash / manifest infrastructure for immutability enforcement
- Full 57-question Gebru datasheet (thesis-relevant subset selected; deferred documented)
