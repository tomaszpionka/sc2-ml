# Plan Critique — reviewer-adversarial Mode A (TG3)

**Target:** `planning/current_plan.md` (272 lines)
**Date:** 2026-04-20

## Verdict: REQUIRE_MINOR_REVISION

1 BLOCKER (B-1) + 2 WARNINGs (W-1, W-2). Three narrow edits before execution.

## Findings

### BLOCKER B-1 — Constraint (c) anchor prose overclaims EsportsBench advertised metrics
T01 step 3(c) instructs: *"EsportsBench w ogłoszonym opisie obejmuje trafność rankingową i log-loss, lecz nie diagramy rzetelności ani dekompozycję Murphy'ego"*.

WebFetch of HuggingFace + GitHub README: neither advertises Brier, log-loss, accuracy, reliability, calibration, or Murphy. The "obejmuje trafność i log-loss" positive claim is an OVERCLAIM — replicates L-1 BLOCKER in a new shape.

**Fix:** rewrite to absence-from-README claim only: *"publicznie dostępna dokumentacja EsportsBench (HuggingFace dataset README v8.0 2025-12-31 oraz README repozytorium GitHub) nie wymienia diagramów rzetelności ani dekompozycji Murphy'ego wśród opisanych metryk benchmarku; integralność tych miar w protokole ewaluacyjnym EsportsBench pozostaje niezweryfikowana w ramach niniejszej pracy pending manualnej analizy preprintu"*.

Also extend Rollback degradation-mode with a third scenario (c): if preprint PDF Table 2 contains calibration metrics, constraint (c) must be rewritten to cross-game-benchmarking-as-standalone-operative.

### WARNING W-1 — §1.3 RQ1 surgical deletion narrows inductive base, mitigation silent
Post-deletion, RQ1 hypothesis cites Hodge2021 (Dota 2 only) + Tang2025 margin caveat. Plan Open Q 3 acknowledges narrowing but doesn't mitigate in execution. An examiner asking "why Dota-2-only base for SC2+AoE2 hypothesis?" has an opening.

**Fix:** plant `[REVIEW: RQ1 hipoteza inductive base narrowed to Dota 2 — Pass 2 ocenić, czy dodać cytat na cross-esport GBDT-dominance]` flag at `01_introduction.md:31` post-T02. OR add explicit narrowed-induction note to T03 WRITING_STATUS §1.3 entry.

### WARNING W-2 — Asymmetric rating-family enumeration: §3.2.4 vs §2.5.5:177
§3.2.4 T01 step 2: lists 5 families (Elo, Glicko, Glicko-2, TrueSkill, warianty BT).
§2.5.5:177 T02 step 4: lists 4 families (Elo, Glicko, Glicko-2, TrueSkill).

Both are true subsets of EsportsBench's 11 systems. Reviewer will notice asymmetry.

**Fix:** unify phrasing: *"rodziny paired-comparison rating systems, m.in. Elo, Glicko, Glicko-2, TrueSkill"* at both sites.

## Probes answered

- Four-constraint conjunction: holds at (a), (b), (d); fragility at (c) → B-1 fix required
- AoE2 absence: confirmed absent from v8.0
- §1.3 surgical deletion parses cleanly → but see W-1
- Degradation-mode fallback: covers v9.0+ scenarios; needs third scenario for preprint-PDF divergence (B-1 extension)
- File Manifest 7 files: confirmed
- No new bibkeys: confirmed
- Thorrez author typo deferral: consistent (no TG3 site references author name)

## Recommendation

REQUIRE_MINOR_REVISION — three edits (B-1 + W-1 + W-2), no redesign needed.

## Sources
- EsportsBench HuggingFace v8.0
- EsportsBench GitHub README
