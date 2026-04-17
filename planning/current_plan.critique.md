---
verdict: APPROVE
plan_reviewed: planning/current_plan.md
revision_reviewed: 4
reviewer_model: claude-opus-4-7[1m]
date: 2026-04-17
findings:
  - id: NOTE-6
    severity: NOTE
    title: "Defensive .fillna(-1) on _zero filter is redundant given explicit identity exclusion (cosmetic)"
    description: |
      In Deliverable 6.B, the _zero filter has BOTH:
        (df_ledger["n_distinct"].fillna(-1) != 1)
      AND
        (~df_ledger["column"].isin(identity_cols_for_view))
      Identity columns are the only source of n_distinct=None per W6 skip logic
      in _detect_constants. With the explicit isin exclusion already filtering
      them out, the .fillna(-1) is belt-and-suspenders. Not a defect — defensive
      coding is appropriate for a thesis-grade audit and survives if W6's
      identity_cols set ever drifts from the 6.B identity_cols_for_view binding.
      Documented for transparency only.

  - id: NOTE-7
    severity: NOTE
    title: "Stale meta-references to 'v2 plan' / 'v2 critique' in handoff section (cosmetic)"
    description: |
      The 'Adversarial-critique handoff (v2)' section still references 'v2 plan',
      'v2 critique', and 'After user approval, the parent session should:
      ... dispatch reviewer-adversarial with planning/current_plan.md and
      base_ref=master to produce planning/current_plan.critique.v2.md'. The plan
      is now v3-r2 with this round-4 critique. These are stale meta-comments,
      not methodology flaws. Recommend the executor (or a final cosmetic edit)
      strip or update this section before merge so the merged plan history is
      internally consistent. Non-blocking.

verified_correct:
  - "v3-r1 BLOCKER B5 (identity column n_distinct=None misclassification) — RESOLVED. Identity branch is FIRST in if/elif chain; subsequent branches use elif ensuring short-circuit. _zero filter uses .fillna(-1) on n_distinct comparison; explicitly excludes identity_cols_for_view (defense-in-depth — see NOTE-6). New 6.B identity-only assertion enforces mechanism=N/A and recommendation=RETAIN_AS_IS. Per-VIEW identity_cols_for_view bindings documented. Notebook cell descriptions (Deliverables 4.A/4.B/4.C) pass identity_cols={...} per dataset."
  - "v3-r1 BLOCKER B6 (CONVERT_SENTINEL_TO_NULL pre-empts surfaced DS questions) — RESOLVED via Option D (deferral). The _recommend() W3 branch carries an explicit B6 deferral note: '...if carries_semantic_content=True (consult ledger column), this recommendation is non-binding'. DS-AOESTATS-02, DS-AOESTATS-03, DS-SC2-09 (handicap), DS-SC2-10 (APM) all extended/added with B6 deferral notes. Recommendation logic UNCHANGED per the user's elected Option D."
  - "v3-r1 WARNING W8 (is_primary_feature missing from ledger) — RESOLVED. CSV column list (17 columns) includes is_primary_feature; JSON example shows is_primary_feature: true; _consolidate_ledger row dict surfaces is_primary; each branch of the if/elif/else chain initializes is_primary at the right value. Gate condition #4 updated."
  - "Empirical truth for new DS-SC2-09 / DS-SC2-10 verified against 01_02_04_univariate_census.json: zero_counts.replay_players_raw.handicap_zero=2 (2/44,817 = 0.00446% — plan cites '~0.0045% — 2 anomalous rows'); zero_counts.replay_players_raw.APM_zero=1132 (1132/44,817 = 2.527% — plan cites '~2.53%'). Both spec entries (handicap, APM) carry carries_semantic_content=True consistent with the DS B6 deferral notes."
  - "v2 BLOCKERs B1/B2/B3 — confirmed still resolved (no regressions)."
  - "v2 WARNINGs W1-W7 — confirmed still resolved."
  - "Locked decisions Q1 (keep both ledger forms), Q2 (no CROSS entry), Q3 (full coverage Option B) intact."
  - "Out-of-scope discipline preserved."
  - "Phase boundary respected: Phase 01 documents (Invariant I9); audit produces recommendations only; downstream 01_04_02+ executes."
  - "Edge cases scanned: identity-target intersection disjoint per design; constant identity column impossible by definition; identity column with non-zero NULLs caught by upstream zero-NULL assertions in 6.A; multi-line W3 justification text doesn't break 6.C string-matching; override priority interactions clean (target post-step requires n_total_missing > 0, identity branch has zero NULLs by construction)."

locked_decisions_check:
  Q1_keep_both: pass
  Q2_no_cross_entry: pass
  Q3_full_coverage: pass
---

# Adversarial Review Round 4 — 01_04_01 Missingness Audit consolidated plan v3-r2

## Verdict: APPROVE — ready for execution-launch

The v3-r2 surgical edits cleanly resolve all three round-3 findings (B5/B6/W8). Empirical claims for the two new DS entries (DS-SC2-09 handicap, DS-SC2-10 APM) verify against `01_02_04_univariate_census.json`. All v2-resolved findings remain resolved with no regressions. The locked user decisions (Q1/Q2/Q3) are intact. The plan can be dispatched to executor sessions without further plan changes.

The user's Option D resolution of B6 (deferral via DS entries + W3 docstring rather than gating `_recommend()` on `carries_semantic_content`) is defensible. The audit's "produce recommendations only" contract is preserved through explicit documentation: the W3 branch docstring marks the CONVERT_SENTINEL_TO_NULL recommendation as non-binding when `carries_semantic_content=True`, and the four affected DS entries (DS-AOESTATS-02, DS-AOESTATS-03, DS-SC2-09, DS-SC2-10) explicitly surface the retain-as-category alternative arm. A sharp examiner may still ask "why does your ledger recommend converting a signal you documented as semantic?" — the plan now has a documented answer in both code (W3 docstring) and the surfaced-decisions block. Defensible at examination provided the executor preserves the docstring and DS entries verbatim. The reviewer-deep post-execution check (NOTE-4 in plan) is well-positioned to verify the as-shipped ledger reflects this contract.

## Round-4 findings summary

| ID | Severity | Issue | Action |
|----|----------|-------|--------|
| NOTE-6 | NOTE | Defensive .fillna(-1) on _zero filter is redundant given explicit identity_cols_for_view exclusion | None required — belt-and-suspenders |
| NOTE-7 | NOTE | Stale 'v2 plan' / 'v2 critique' meta-references in handoff section | Optional cosmetic cleanup before merge |

No BLOCKER, no WARNING. APPROVE.

## Round-3 finding resolution

| Round-3 ID | Required v3-r2 fix | Status |
|------------|---------------------|--------|
| BLOCKER B5 | Identity branch FIRST + `.fillna(-1)` + identity exclusion | RESOLVED |
| BLOCKER B6 | Deferral via DS entries (Option D) | RESOLVED |
| WARNING W8 | is_primary_feature in CSV + JSON + row dict | RESOLVED |

## Empirical spot-check (DS-SC2-09 / DS-SC2-10)

| Spec entry | Plan claim | Census ground truth | Status |
|------------|-----------|---------------------|--------|
| handicap (DS-SC2-09) | sentinel=0, ~0.0045%, 2 anomalous rows | `zero_counts.replay_players_raw.handicap_zero=2`; 2/44,817 = 0.00446% | VERIFIED |
| APM (DS-SC2-10) | sentinel=0, ~2.53% | `zero_counts.replay_players_raw.APM_zero=1132`; 1132/44,817 = 2.527% | VERIFIED |

## Re-verification carry-overs (still pass from v3-r1)

- All 3 v2 BLOCKERs (B1/B2/B3): empirical truth retained — no phantom winner column; old_rating spec cites min_val=0/n_zero=5,937 only; antiquityMode/hideCivs grounded in 01_02_04 alone.
- All 7 v2 WARNINGs (W1-W7): retained.
- Locked decisions Q1/Q2/Q3 intact.
- Out-of-scope discipline preserved.
- Phase boundary respected (Invariant I9).
- Reproducibility / Invariant I6: SQL templates serialized in helpers + spec dict; per-column sentinel queries reconstructible from the template + the _missingness_spec dict.

## Executor dispatch checklist

The executor can be dispatched immediately. Suggested verification at execution time (not blocking):

1. After sc2egset audit cells, spot-check that `df_ledger_mfc` and `df_ledger_hist` each have rows for `replay_id` and `toon_id` with `mechanism="N/A"`, `recommendation="RETAIN_AS_IS"`, `n_distinct=null` — direct B5 fix verification.
2. Spot-check `df_ledger_hist[df_ledger_hist["column"].isin(["handicap", "APM"])]` shows `recommendation="CONVERT_SENTINEL_TO_NULL"` AND `carries_semantic_content=True` — this is the B6 deferral signature in actual data.
3. After CSV+JSON write, `len(df_ledger.columns) == 17` — direct W8 verification.
4. Reviewer-deep post-execution (NOTE-4 in plan) validates mechanism justifications across the produced ledgers before Phase 02 cites them.

## Reproducibility / Invariant #6

Empirical claims verified verbatim against `01_02_04_univariate_census.json` for both new DS entries. All v3-r1 verified-correct empirical claims retained: `old_rating min=0/n_zero=5937`, `avg_elo n_zero=121`, `team_0_elo n_zero=4824`, `team_1_elo n_zero=192`, `raw_match_type null_count=12504/null_pct=0.0407%`, aoe2companion `antiquityMode null_pct=68.66%`, `hideCivs null_pct=49.30%`. SQL templates remain serialized; per-column sentinel queries reconstructible. Reproducibility constraint met for the round-4 diff and all carry-overs.
