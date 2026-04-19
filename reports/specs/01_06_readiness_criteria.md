---
spec_id: CROSS-01-06-v1
spec_version: "1.0"
created: 2026-04-19
status: LOCKED
datasets_bound: [sc2egset, aoe2companion, aoestats]
invariants_touched: [I1, I2, I3, I5, I6, I7, I8, I9]
plan_ref: planning/current_plan.md (Phase 01 Decision Gates, 01_06 bundled PR)
---

# Spec v1.0 — 01_06 Decision Gates: Readiness Criteria

This document is a **locked spec**. Parameters declared here are binding for all
01_06 notebooks across the three datasets (sc2egset, aoestats, aoe2companion).
Mid-execution amendments are **forbidden** per §4. If an executor finds a defect
in §1/§2/§3, they halt and report to parent; parent opens a follow-up PR to amend
the spec. This contrasts with the `01_05_preregistration.md` practice.

---

## §1 Four-Deliverable Schema

Manual 01 §6.1 requires four deliverables per dataset before Phase 02 may proceed.
Column sets for each artifact are enumerated below; no "etc." is permitted.

### §1.1 Data Dictionary

**Files:** `data_dictionary_<dataset>.csv` and `data_dictionary_<dataset>.md`

**CSV columns** (all mandatory; no columns may be omitted for any row):

| Column | Type | Description |
|--------|------|-------------|
| `column_name` | string | Exact column name as it appears in the DuckDB view/table |
| `table_or_view` | string | Source table or view name (e.g., `matches_1v1_clean`, `player_history_all`, `matches_history_minimal`) |
| `dtype` | string | DuckDB data type (e.g., `BIGINT`, `VARCHAR`, `BOOLEAN`, `DOUBLE`, `TIMESTAMP`) |
| `semantics` | string | Human-readable description of what the column represents |
| `valid_range` | string | Valid domain of values (e.g., `[0,1]`, `positive`, `NULL if unrated`, `enum: {Win,Loss,Undecided}`) |
| `nullability` | string | One of: `NOT NULL`, `NULLABLE`, `NULLABLE_MEANINGFUL` (NULL carries information per I3) |
| `units` | string | Units if applicable (e.g., `seconds`, `Elo points`, `none`) |
| `temporal_classification` | string | One of: `PRE_GAME`, `POST_GAME_HISTORICAL`, `TARGET`, `METADATA`, `IDENTIFIER` per Invariant I3 |
| `provenance_step` | string | Step number that established this column (e.g., `01_04_02`, `01_04_00`) |
| `invariant_notes` | string | Any I1–I10 constraint applying to this column; `none` if no constraint |

**MD companion:** human-readable grouping by table + narrative on temporal
classification, with a summary count of PRE_GAME / POST_GAME_HISTORICAL / TARGET
columns. Must note all columns with `invariant_notes != none`.

### §1.2 Data Quality Report

**File:** `data_quality_report_<dataset>.md`

**Required sections:**

1. **CONSORT-style flow** — ASCII or text table tracing row counts at each stage
   (raw → scope filter → structural filter → cleaning rules → final clean count).
   Each stage shows `n_rows_in`, `n_rows_excluded`, `reason`.
2. **Cleaning rule registry** — table with columns: `rule_id`, `condition`,
   `action`, `justification`, `impact` (rows affected, % of prior stage).
   Every rule must trace back to a `*_cleaning.yaml` or `01_04_01` registry entry.
3. **Route-decision table** — one row per column with NULL/missing rate ≥ 1%,
   showing: column, NULL%, mechanism (MCAR/MAR/MNAR), route (DROP/NULLIF/INDICATOR/RETAIN),
   decision source (rule_id or manual §4 threshold).
   Thresholds: <5% → RETAIN_AS_IS; 5–40% → NULLIF or INDICATOR per I3; ≥40% → DROP
   (with exceptions documented if primary feature retained despite ≥40%).
4. **Post-cleaning summary** — row counts in all major views/tables after cleaning;
   column count deltas (added/dropped/modified); brief validation assertions (e.g.,
   no negative ratings, no NULL match_id).

### §1.3 Risk Register

**Files:** `risk_register_<dataset>.csv` and `risk_register_<dataset>.md`

**CSV columns** (all mandatory):

| Column | Type | Description |
|--------|------|-------------|
| `risk_id` | string | Unique identifier (e.g., `R01`, `R02`) |
| `category` | string | Risk category (e.g., `TEMPORAL_LEAKAGE`, `IDENTITY`, `SURVIVORSHIP`, `SLOT_ASYMMETRY`, `SCHEMA_DIVERGENCE`, `POPULATION_SCOPE`, `ICC_SIGNAL`, `BACKLOG_ITEM`) |
| `description` | string | 1–3 sentence description of the risk |
| `evidence_artifact` | string | Relative path to the artifact establishing this risk |
| `severity` | string | One of: `BLOCKER`, `HIGH`, `MEDIUM`, `LOW`, `RESOLVED` |
| `phase02_implication` | string | How this risk constrains or affects Phase 02 feature engineering |
| `thesis_defence_reference` | string | Chapter/section anchor for the thesis defence (e.g., `§4.1.1`, `§4.4.5`, `N/A`) |
| `mitigation_status` | string | One of: `OPEN`, `OPEN (BACKLOG <item>)`, `RESOLVED`, `ACCEPTED (documented in thesis)` |

**Completeness gate:** every row in the dataset's INVARIANTS.md §5 with status
`PARTIAL` or `VIOLATED` must have a corresponding `risk_id` in this register.
Every BACKLOG item that affects this dataset must have a `BLOCKER` or `HIGH` row
with `mitigation_status = OPEN (BACKLOG <item>)`.

**MD companion:** human-readable narrative with severity grouping.

### §1.4 Modeling Readiness Decision

**File:** `modeling_readiness_<dataset>.md`

**Required sections:**

1. **Verdict** — verbatim from the §2 taxonomy (one of four tiers).
2. **Flip-predicate** — the exact condition under which the verdict would transition
   to a less-restricted state. Mandatory for all non-READY_FULL verdicts; `N/A`
   for READY_FULL.
3. **BLOCKER list** — all risk_ids with severity=BLOCKER; empty list if none.
4. **HIGH/MEDIUM residuals** — all risk_ids with severity HIGH or MEDIUM, each
   with its Chapter 4 defence anchor. Required for READY_WITH_DECLARED_RESIDUALS.
5. **Phase 02 go/no-go** — explicit statement of whether Phase 02 planning may
   commence, and if yes, whether at full scope or narrower scope (with scope
   restriction named).
6. **Role assignment summary** — cross-reference to the cross-dataset rollup memo
   (`reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md`)
   with the dataset's PRIMARY/SUPPLEMENTARY labels per dimension.

---

## §2 Verdict Taxonomy

Four tiers, applied from most to least permissive. Executor selects the tier
whose conditions are satisfied based on the dataset's actual risk register from
01_06_03. The anticipated verdicts in the plan are predictions; executor may
override per §4 binding.

### READY_FULL

**Conditions:** (a) zero BLOCKER rows in risk register; AND (b) zero HIGH or MEDIUM
severity rows in risk register (all risks are LOW or RESOLVED).

**Phase 02 action:** proceed unconditionally at full scope.

**Flip-predicate:** N/A (no further restrictions).

### READY_WITH_DECLARED_RESIDUALS

**Conditions:** (a) zero BLOCKER rows in risk register; AND (b) one or more HIGH or
MEDIUM rows in risk register, each documented with a Chapter 4 thesis-defence anchor.

**Phase 02 action:** proceed unconditionally; residuals are addressed in the thesis
text rather than fixed pre-Phase-02.

**Flip-predicate:** N/A (residuals are declared, not pending removal).

**Note:** "Declared residuals" means the dataset is methodologically ready for
Phase 02 but carries known limitations the thesis author accepts and defends.
This tier recognises that a dataset with known-but-documented limitations is more
scientifically honest than READY_FULL when significant residuals exist.

### READY_CONDITIONAL

**Conditions:** has one or more BLOCKER rows in risk register, but each BLOCKER has
a registered mitigation path (a BACKLOG item with a `feat/` branch planned).

**Phase 02 action:** may proceed on a narrower scope explicitly named in the verdict
memo (e.g., aggregate features only; per-slot features deferred). The narrower scope
must be stated as a concrete Phase 02 feature-set restriction.

**Flip-predicate:** each BLOCKER must name the exact condition under which it transitions
to RESOLVED (e.g., "BACKLOG F1 `canonical_slot` resolved AND INVARIANTS.md §5 I5 row
transitions PARTIAL → HOLDS"). If multiple BLOCKERs exist, all must resolve for the
flip.

### NOT_READY

**Conditions:** has one or more BLOCKER rows with no registered mitigation path (the
BLOCKER cannot be addressed by a planned BACKLOG item; it requires data re-acquisition
or fundamental re-design).

**Phase 02 action:** return to the specified Pipeline Section with a specific
remediation instruction.

**Flip-predicate:** address the unresolvable BLOCKER per the remediation instruction.

---

## §3 Role-Assignment Criteria

Six dimensions (D1–D5 + D6 as asymmetry flag). A dataset can be PRIMARY on one
dimension and SUPPLEMENTARY on another. For each dimension, the spec names the
comparable metric, decision rule, and falsifier.

### D1 — Sample-scale (ML training volume)

**Metric:** total Phase-02-ready rows in `matches_history_minimal` (or equivalent
cleaned 1v1 view), from the data quality report (§1.2) CONSORT final-stage row count.

**Decision:** PRIMARY if dataset's cleaned row count ≥ 10× the second-largest
dataset's cleaned row count. SUPPLEMENTARY otherwise.

**Comparability predicate:** comparable across all three datasets (all derive from
the same `matches_history_minimal` 9-column contract per spec `CROSS-01-05-v1 §1`).

**Falsifier:** if another dataset exceeds 10× the current PRIMARY within Phase 02
data refreshes, role flips.

### D2 — Skill-signal (observed-scale ICC)

**Metric:** observed-scale ICC point estimate with bootstrap CI on the pre-game
reference window (from each dataset's 01_05_05 ICC artifact).

**Decision requires two filters passed in conjunction:**

- **Filter F1 (quantitative):** ICC point estimate ≥ 0.01.
  *Justification:* 0.01 is the conventional ICC ignorable-variance floor
  (Koo & Li 2016 JCM §3.1; Cicchetti 1994); below this, between-player variance
  is indistinguishable from rounding error in typical skill-estimation studies.
  Threshold cited, not invented.

- **Filter F2 (qualitative):** the verdict field in the **dataset's INVARIANTS.md
  §5 row** for the ICC-relevant invariant does NOT read `FALSIFIED`.
  INVARIANTS.md §5 uses the uniform token set `{HOLDS, PARTIAL, FALSIFIED, DEVIATES}`.
  The per-dataset ICC JSON artifacts use inconsistent field schemas (`verdict` vs
  `falsifier_verdict` vs prose `verdict` value) and are **not** the canonical F2
  source; they are cited as evidence only. F2 reads from INVARIANTS.md §5 exclusively.
  `HOLDS` and `PARTIAL` pass F2; `FALSIFIED` and `DEVIATES` fail F2.

PRIMARY requires passing BOTH F1 AND F2 AND being the largest point-estimate ICC
among all F2-passing candidates. SUPPLEMENTARY otherwise (any dataset failing F1
or F2 is SUPPLEMENTARY on D2 regardless of absolute ICC value).

**Comparability predicate:** comparable across datasets that share pre-game reference
windows of overlapping duration (per `CROSS-01-05-v1 §2` 2022-Q3 through 2024-Q4
anchor). Not comparable to a dataset whose reference window is structurally non-overlapping.

**Falsifier:** if a SUPPLEMENTARY dataset's ICC rises above the current PRIMARY's
point estimate at equal or narrower CI width AND its INVARIANTS.md §5 row transitions
out of `FALSIFIED`, role flips to that dataset.

### D3 — Temporal coverage (months continuous, density floor)

**Metric:** count of distinct calendar months with ≥ 100 cleaned rows in
`matches_history_minimal`, computed via:

```sql
SELECT COUNT(DISTINCT DATE_TRUNC('month', started_at))
FROM matches_history_minimal
WHERE DATE_TRUNC('month', started_at) IN (
  SELECT DATE_TRUNC('month', started_at) AS month
  FROM matches_history_minimal
  GROUP BY 1
  HAVING COUNT(*) >= 100
)
```

**Density floor N = 100 rows/month justification:** derived from binomial SE bound
— at N=100 observations per month, the standard error of any within-month proportion
estimate is ≤ 5% (SE = √(p(1-p)/N) ≤ √(0.25/100) = 0.05 at p=0.5). 100 is the
project-set minimum for within-month rate stability at SE ≤ 5%. Threshold is derived,
not invented.

**Decision:** PRIMARY if density-filtered month-count ≥ 2× the median across all
three candidates (measured at the same density floor). SUPPLEMENTARY otherwise.

**Comparability predicate:** comparable across datasets only when the same density
floor (N=100) is applied uniformly. Tournament-sparse months (sc2egset) are excluded
when they fall below the floor.

**Falsifier:** if another dataset later exceeds the PRIMARY's density-filtered
month-count (e.g., after data refresh), role flips.

### D4a — Identity rename-stability (Branch per I2 extended procedure)

**Metric:** Branch assignment per `.claude/scientific-invariants.md` I2 extended
procedure (Branches i–v).

**Decision:**
- PRIMARY if Branch (i) — API-namespace ID, provider-level rename-stable.
- SUPPLEMENTARY if Branch (ii/iii) — scoped or handle-based with documented
  migration risk.
- SUPPLEMENTARY if Branch (v) — structurally-forced (rates unmeasurable).

**Comparability predicate:** comparable across all three datasets (all follow I2
extended procedure documented in INVARIANTS.md §2 per dataset).

**Falsifier:** if a SUPPLEMENTARY dataset's API namespace changes to Branch (i)
(e.g., aoestats acquires a stable global profile namespace), role flips.

### D4b — Identity within-scope rigor (rates < 15%)

**Metric:** measured `migration_rate` and `cross_scope_collision_rate` for the
chosen identity key within the declared scope (per INVARIANTS.md §2).

**Decision:**
- PRIMARY if BOTH rates < 15% AND documented with SQL (per I2 extended Step 2).
- SUPPLEMENTARY if Branch (v) structurally-forced (rates unmeasurable within dataset).
- SUPPLEMENTARY if either rate ≥ 15%.

The 15% threshold is sourced from INVARIANTS.md §2 per-dataset tolerance values
(not invented here; the sc2egset 30.6% within-region collision rate and aoe2companion
2.57%/3.55% rates both derive from INVARIANTS.md §2 with SQL citations).

**Comparability predicate:** comparable only across datasets where both rates can be
measured (excludes Branch (v) structurally-forced datasets).

**Falsifier:** if a currently SUPPLEMENTARY dataset reduces its rates below 15% via
a schema amendment or data re-acquisition, role flips.

### D5 — Patch resolution (patch metadata)

**Metric:** presence and usability of a `patch_id` or equivalent patch-binding column
in the cleaned views.

**Decision:**
- PRIMARY if a patch identifier is present AND usable for cohort slicing in Phase 02.
- SUPPLEMENTARY if no patch metadata is available or if patch data is present but
  has insufficient coverage (< 50% rows with non-NULL patch_id).

**Comparability predicate:** D5 is NOT cross-dataset comparable (each dataset either
has patch metadata or does not). The PRIMARY label on D5 is a within-dataset finding,
not a comparative ranking.

**Falsifier:** if a SUPPLEMENTARY dataset adds patch metadata in a later Phase, role flips.

### D6 — Controlled-asymmetry flag (I8 controlled variable, NOT a role dimension)

**Definition:** presence of game-internal event-timeline data (SC2 replays carry
parseable event sequences; neither AoE2 corpus does). This is an **asymmetry flag**
documenting the thesis's Invariant #8 controlled variable.

**This dimension DOES NOT COUNT toward PRIMARY-role weight in any cross-dataset
comparison.** D6 is listed in the T08 §2 matrix for I8 transparency only. The
cross-dataset role tally for Phase 02 kickoff uses only D1–D5 (with D4 split into
D4a and D4b, contributing 2 sub-dimensions).

**Why listed:** per reviewer-adversarial Pass 2 resolution, D6 is included in the
matrix to document the thesis's controlled experimental variable (AoE2 datasets
lack in-game state; sc2egset has it). This asymmetry is not a flaw but a design
feature that enables the cross-game comparison stated in Invariant #8.

---

## §4 Binding

- This spec is cited by SHA in each 01_06 notebook's docstring per Invariant I6.
- **Mid-execution amendments are forbidden.** If an executor finds a defect in
  §1/§2/§3 during T05–T08, they halt and report to parent; parent opens a
  follow-up PR to amend the spec, NOT this PR.
- Anticipated verdicts in the execution plan are predictions; executor verifies
  against actual 01_01–01_05 artifacts and may revise the verdict per §2 taxonomy.
- The four-tier taxonomy in §2 is binding; a fifth tier may not be improvised
  during execution.
- The role-assignment criteria in §3 are binding; a seventh dimension may not be
  added during execution.

---

## §5 Amendment Log

| Version | Date | Change | Author |
|---------|------|--------|--------|
| v1.0 | 2026-04-19 | Initial version. Locked per §4. Four-deliverable schema (§1), four-tier taxonomy (§2), six-dimension role criteria (§3). D4 split into D4a/D4b; D6 demoted to asymmetry flag. | planning/current_plan.md (Phase 01 Decision Gates) |
