# Phase 02 Readiness Hardening — T16 Decision Record

**Task:** T16 (thesis/audit-methodology-lineage-cleanup)
**Branch:** `thesis/audit-methodology-lineage-cleanup`
**Date:** 2026-04-27
**Executor model:** claude-sonnet-4-6

---

## Spec version baseline after T15

| Spec | Version after T15 | Status |
|------|------------------|--------|
| `reports/specs/02_00_feature_input_contract.md` | `CROSS-02-00-v3.0.1` | LOCKED |
| `reports/specs/02_01_leakage_audit_protocol.md` | `CROSS-02-01-v1.0.1` | LOCKED |

Both specs were amended by T15 (patch level). The amendment logs record these
changes. No further amendments were made in T16 (see sub-step decisions below).

---

## T16 sub-step decision table

| Sub-step | Classification | Files changed | Action taken |
|----------|---------------|---------------|--------------|
| **14A.1** Data-dictionary temporal-classification audit | **doc_patch (executed)** | ROADMAP, generator .py, artifact .csv+.md, research_log, STEP_STATUS | Temporal-classification contradiction repaired (see §14A.1) |
| **14A.2** CROSS-02-01 leakage-audit protocol hardening | **already_satisfied** | none | T15 v1.0.1 patch covers stale-artifact gate; no §2/§5 changes needed |
| **14A.3** CROSS-02-00 feature-input contract cold-start hardening | **already_satisfied** | none | T15 v3.0.1 patch covers UTC discipline and telemetry scope; no empirical cold-start pseudocount available; v3→v4 deferred |
| **14A.4** DuckDB UTC requirement | **already_satisfied** | none | CROSS-02-00 §3.3 UTC note present and sufficient; not duplicated |
| **14A.5** SC2 cross-region fragmentation (RISK-20) | **defer_with_gate** | none (register already updated by T10) | Empirical FAIL verdict documented; retention percentage deferred to Phase 02 |
| **14A.6** SC2 tracker_events semantic validation | **defer_with_gate** | none | Hard gate recorded below; overclaiming prevented |

---

## 14A.1 — Data-dictionary temporal-classification audit

### Contradiction found

`data_dictionary_aoe2companion.csv` contained two same-class temporal-classification
contradictions:

| Column | Table | Artifact classification | Correct classification | Authority |
|--------|-------|------------------------|----------------------|-----------|
| `rating` | `player_history_all` | `TARGET` | `PRE_GAME` | YAML notes; CROSS-02-00 §5.6 |
| `started` | `player_history_all` | `TARGET` | `METADATA` (CONTEXT) | YAML notes; CROSS-02-00 §5.6 |

**Root cause:** The generator `classify()` function used `"TARGET" in n` (substring
match). The I3-guard note for both columns reads "started < target_match.started" —
the word "target" appearing as part of "target_match" triggered a false-positive
TARGET classification. This is a generator keyword-priority bug, not an error in the
YAML schema or the CROSS-02-00 spec. Both the YAML and CROSS-02-00 §5.6 correctly
classify `rating` as PRE_GAME and `started` as CONTEXT (METADATA).

### Repair lineage

1. **ROADMAP updated first (G2):** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`
   Step 01_06_01 — description amended to note whole-word-boundary requirement;
   `gate.continue_predicate` extended with "No PRE_GAME column (per YAML notes or
   CROSS-02-00 §5.6) is classified as TARGET in the CSV."

2. **Generator fixed:** `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.py`
   — `classify()` updated to use `re.search(r'\bTARGET\b', n)` (whole-word boundary)
   instead of `"TARGET" in n` (substring). No other temporal class labels were at similar
   false-positive risk.

3. **Notebook synced and executed:** Jupytext sync followed by nbconvert execution
   (600s timeout). Execution was clean.

4. **Artifact counts after regeneration:**
   - PRE_GAME: 38 → 39 (`rating`/`player_history_all` reclassified)
   - METADATA: 16 → 17 (`started`/`player_history_all` reclassified)
   - TARGET: 5 → 3 (only the three `won` columns remain — the correct outcome)

5. **Notebook regeneration manifest updated:** Row for `01_06_01_data_dictionary.py`
   updated to `confirmed_intact` with cause `T16 14A.1 finding`.

6. **Research log updated:** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md`
   — section "2026-04-27 — [Phase 01 / Step 01_06_01] Data Dictionary temporal-classification repair" added.

7. **STEP_STATUS updated:** Step `01_06_01` — YAML comment appended (status remains `complete`).

### Data quality report (BLOCKER-1 sub-check 6)

The generated `data_quality_report_aoe2companion.md` was already repaired by T07/T08
(commit `9581b053`). The manifest records it as `confirmed_intact`. No further repair
needed. No manual patch was applied.

### Scope acceptance note

T16 14A.1 discovered a real generated-data-dictionary classification bug
(`classify()` substring matching "TARGET" inside the I3-guard phrase
"target_match.started"). Although the immediate T16 dispatch prompt
listed a narrower allowlist, the user accepted the broader plan-authorized
repair path because the generated data dictionary was explicitly within
T16 sub-step 14A.1 scope under the plan's generated-artifact discipline.
The repair was performed through the canonical lineage chain:
ROADMAP → notebook → artifact → research_log → STEP_STATUS → manifest.
No raw data, thesis chapter prose, specs, schemas, or unrelated artifacts
were modified.

---

## 14A.2 — CROSS-02-01 leakage-audit protocol hardening

**Decision: no further change needed.**

T15 produced CROSS-02-01-v1.0.1 (patch) with the following amendments:

- §4: stale-artifact discipline note — if a feature-generating notebook or SQL view changes
  after an audit artifact is produced, the artifact must be re-generated; the manifest is the
  authoritative stale/current authority; generated artifacts must not be manually patched.
  (Addresses T15 Concern 7.)
- §8: sibling spec reference updated from CROSS-02-00-v1 to CROSS-02-00-v3.0.1.

The T16 plan required a v1→v2 major bump only if T16 introduced NEW §2 audit dimension
or §5 gate condition changes. No such changes are required by the remaining T16 scope.
The v1 enforcement mechanism is documented in §5 as "convention-based — no CI check,
pre-commit hook, or gate script." This is the correct v1 characterisation. The future
v2 amendment target (CI/pre-commit tooling enforcement) is already documented in §7.

**T16 14A.2 verdict:** CROSS-02-01-v1.0.1 covers the stale-artifact gate and the
pattern-conformance enforcement mechanism. No v1→v2 bump warranted at this T16 execution.
Version remains `CROSS-02-01-v1.0.1` (LOCKED).

---

## 14A.3 — CROSS-02-00 feature-input contract cold-start hardening

**Decision: no further change needed.**

T15 produced CROSS-02-00-v3.0.1 (patch) with the following amendments:

- §3.3: UTC session discipline note — requires `SET TimeZone = 'UTC'` in Phase 02 notebooks
  comparing TIMESTAMPTZ vs TIMESTAMP columns.
- §5.4: SC2 in-game telemetry scope decision — IN_GAME_HISTORICAL columns (APM, SQ,
  supplyCappedPercent, header_elapsedGameLoops) are RETAINED IN SCOPE pending T16 14A.6.

The T16 plan required a v3→v4 major bump only if source-specific cold-start protocol
additions affected §2 column-grain commitments, the §4 encoding rule, or §5 gate
conditions. Per Invariant I7, pseudocount `m` must NOT be bound without empirical
derivation. No empirical cold-start data from Phase 02 is available at this T16
execution point. No §2/§4/§5 changes are required.

**T16 14A.3 verdict:** CROSS-02-00-v3.0.1 is sufficient. No v3→v4 bump warranted.
Version remains `CROSS-02-00-v3.0.1` (LOCKED).

---

## 14A.4 — DuckDB UTC requirement

**Decision: already satisfied — no action.**

CROSS-02-00 §3.3 contains the UTC session discipline note added by T15 v3.0.1:

> "Any DuckDB session that compares `TIMESTAMPTZ` values (e.g., in a rolling-window
> `WHERE ph.started_timestamp < target.started_at`) MUST operate with a UTC session
> timezone to avoid implicit offset injection. Phase 02 implementations MUST add the
> assertion below at the start of every notebook or script that issues cross-column
> timestamp comparisons involving `started_timestamp`:
> `con.execute("SET TimeZone = 'UTC'")`"

The note is present, correctly scoped to aoestats `started_timestamp` (TIMESTAMPTZ),
and correctly flags the risk of implicit offset injection. Naked-TIMESTAMP assumptions
per dataset are documented via the per-dataset anchor column table in §3.2. No
duplication is needed.

---

## 14A.5 — SC2 cross-region fragmentation (RISK-20)

**Decision: defer_with_gate — empirical values documented; retention percentage
deferred to Phase 02.**

### Empirical values from `cross_region_history_impact_sc2egset.md`

The WP-3 / 01_05_10 artifact (`cross_region_history_impact_sc2egset.md`) provides the
following empirical values at window=30 (primary):

| Metric | Value | Threshold | Pass? |
|--------|-------|-----------|-------|
| median_rolling30_undercount | 16.0 games | ≤ 1 game | FAIL |
| p95_rolling30_undercount | 29.0 games | ≤ 5 games | FAIL |
| Spearman ρ bootstrap CI upper | 0.2913 | < 0.2 | FAIL |

**VERDICT: FAIL** (all three thresholds violated; W=5 only passes but is not the
primary analysis window).

### What is NOT quantified

The `is_cross_region_fragmented` sample-retention percentage (the fraction of matches
retained under `WHERE NOT is_cross_region_fragmented`) is NOT quantified in any
existing Phase 01 artifact. Per Invariant I7 (no magic numbers without empirical
derivation), this percentage must not be hard-coded in thesis prose or specs until
Phase 02 measures it.

### RISK-20 status

RISK-20 in `methodology_risk_register.md` already records this as DEFERRED. The
empirical FAIL verdict and the above values are the best available Phase 01 anchor.
The risk register wording recommendation ("do NOT hard-code a retention percentage
until Phase 02 quantifies it") is correct and binding.

### Gate for T16 and downstream

- Thesis prose in §4.2.2 MUST NOT claim a specific sample-retention percentage from
  strict `WHERE NOT is_cross_region_fragmented` filtering.
- The FAIL verdict at window=30 (median undercount 16.0 games, p95 29.0 games) IS
  citable empirical evidence that strict filtering or sensitivity stratification is
  needed; this finding MAY be cited in thesis §4.2.2 prose.
- Phase 02 analysis will determine the concrete retention figure and the preferred
  handling strategy (strict exclusion, dual feature paths, or sensitivity indicator).
- This gate is linked from RISK-20 in `methodology_risk_register.md`.

---

## 14A.6 — SC2 tracker_events semantic validation

**Decision: GATED — validation did NOT execute. Hard gate recorded below.**

### Why validation did not execute

1. **Documentation unavailable as plaintext:** The SC2EGSet datasheet is a PDF at
   `src/rts_predict/games/sc2/datasets/sc2egset/data/raw/SC2EGSet_datasheet.pdf`.
   No `SC2EGSet Replay Data.txt` exists on disk. The plan specifies reading the
   datasheet to avoid unsafe PlayerStats assumptions before running the validation.

2. **PlayerStats field semantics are ambiguous:** The plan explicitly warns: "Do not
   assume final-tick `PlayerStats` minerals/vespene are cumulative totals unless
   source/schema proves it." Without resolved documentation, running the validation
   would risk embedding unsafe assumptions into a new STEP artifact.

3. **Magnitude of required work:** Creating Step 01_03_05 (new ROADMAP entry, new
   notebook pair, new artifact pair, research_log, STEP_STATUS) from scratch in a single
   session, under ambiguous semantics, carries high risk of producing unreliable results.
   The plan's own caution says: "If semantics are ambiguous, produce constrained verdict
   rather than forcing validation."

4. **Spec scope:** CROSS-02-00 §5.4 (T15 record) already states that IN_GAME_HISTORICAL
   columns are "RETAINED IN SCOPE pending T16 sub-step 14A.6 semantic validation" and that
   "Thesis methodology MUST frame SC2 in-game telemetry features as 'available and
   classified but not yet validated for Phase 02 feature generation' until T16 completes."
   This framing is already the correct conservative position.

### Hard gate (binding on T17, T18, T19, T11, and all Phase 02 work)

> **GATE-14A6:** Thesis methodology MUST NOT claim that SC2 `tracker_events`-derived
> in-game features have been semantically validated. Until Step 01_03_05 executes
> end-to-end and produces accepted `.md` + `.json` artifacts, the permitted thesis
> framing is: "SC2 in-game telemetry features (`tracker_events`: APM, SQ,
> supplyCappedPercent, header_elapsedGameLoops in `player_history_all`) are available
> and classified as IN_GAME_HISTORICAL. Their use as rolling-window history features
> (filtered strictly `< T`) is retained in Phase 02 scope pending semantic validation
> (Step 01_03_05, not yet executed)."

This gate links to RISK-21 in `methodology_risk_register.md`.

### Gate text for T18 / T19 mechanical checks

T18 (final consistency pass) and T19 (review gates) must verify that no Chapter 4 prose
in §4.4 (in-game feature section, if drafted) asserts "validated" status for
tracker_events fields beyond what the above permitted framing allows.

### What T17 should do

T17 (REVIEW_QUEUE and WRITING_STATUS synchronization) must:
- Record GATE-14A6 as a pending item in REVIEW_QUEUE.md.
- Ensure WRITING_STATUS.md reflects that Chapter 4 §4.4 cannot be FINAL until
  Step 01_03_05 executes.

---

## Spec versions — before and after T16

| Spec | Before T16 | After T16 | Amendment? |
|------|-----------|-----------|------------|
| `CROSS-02-00-v3.0.1` | v3.0.1 LOCKED | v3.0.1 LOCKED | No — already_satisfied |
| `CROSS-02-01-v1.0.1` | v1.0.1 LOCKED | v1.0.1 LOCKED | No — already_satisfied |

No spec amendments were introduced in T16. Both specs remain at the T15 baseline.

---

## Files changed by T16

| File | Action | Sub-step |
|------|--------|----------|
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` | Modified — Step 01_06_01 description and gate updated | 14A.1 |
| `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.py` | Modified — `classify()` whole-word boundary fix | 14A.1 |
| `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.ipynb` | Modified — jupytext sync + nbconvert execution | 14A.1 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoe2companion.csv` | Modified — regenerated; PRE_GAME 38→39, METADATA 16→17, TARGET 5→3 | 14A.1 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoe2companion.md` | Modified — regenerated (count summary updated) | 14A.1 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` | Modified — 2026-04-27 Step 01_06_01 repair entry added | 14A.1 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml` | Modified — YAML comment appended to Step 01_06_01 block | 14A.1 |
| `thesis/pass2_evidence/notebook_regeneration_manifest.md` | Modified — 01_06_01 row updated; detail record added | 14A.1 |
| `thesis/pass2_evidence/phase02_readiness_hardening.md` | Created (this file) | all sub-steps |

---

## SC2 tracker_events validation status

**NOT executed.** Hard gate (GATE-14A6) recorded above. Thesis methodology must not
claim validated tracker_events-derived features. RISK-21 in `methodology_risk_register.md`
remains OPEN (conditional on T15 decision to retain in-game telemetry scope).

---

## Remaining risks (pointers to methodology_risk_register.md)

| Risk ID | Sub-step relevance | Status after T16 |
|---------|--------------------|-----------------|
| RISK-20 | 14A.5 (cross-region fragmentation) | DEFERRED — empirical retention % awaits Phase 02 |
| RISK-21 | 14A.6 (tracker_events semantics) | OPEN — GATE-14A6 prevents overclaiming; Step 01_03_05 not yet executed |

All other RISK entries (RISK-01 through RISK-19, RISK-22 through RISK-26) are outside
T16 scope and status is unchanged from T10 register.

---

## Next owner task

**T17** is ready to begin.

T17 prerequisites met:
- `phase02_readiness_hardening.md` (this file) exists.
- No generated artifact was manually edited.
- All methodology-affecting spec changes (none in T16) would have required T10's
  consolidated adversarial gate; none were introduced.
- Data dictionary temporal-classification contradiction repaired and lineage closed.
- AoE2 ranked/ladder terminology governance is per T05 (not overridden by T16).
- GATE-14A6 is recorded and must be carried into T17 REVIEW_QUEUE update.

T17 must:
1. Update `thesis/chapters/REVIEW_QUEUE.md`: add GATE-14A6 as a pending item; record
   that Chapter 4 §4.4 is blocked on Step 01_03_05 execution.
2. Update `thesis/WRITING_STATUS.md`: reflect that Chapter 4 §4.4 cannot reach FINAL
   status until tracker_events validation executes.
3. Update `thesis/pass2_evidence/cleanup_flag_ledger.md` to match final chapter state
   post-T11/T12/T13/T14.
