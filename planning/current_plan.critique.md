# Adversarial Review — Plan (Mode A) — WP-7

**Plan:** `planning/current_plan.md` — sc2egset cross-region fragmentation Phase 01 annotation
**Branch:** `feat/sc2egset-cross-region-annotation`
**Base:** master `6ea71edf` (post PR #203; version 3.42.0)
**Category:** A (Phase 01 cleaning-rule extension)
**Date:** 2026-04-21
**Reviewer:** reviewer-adversarial, Mode A (pre-execution)

## Lens summary

| Lens | Verdict |
|------|---------|
| Temporal discipline (I3) | SOUND — static set-membership flag, no per-row temporal filter |
| Statistical methodology | N/A — annotation-only |
| Feature engineering (I7) | AT RISK — ±5 drift tolerance unjustified |
| Thesis defensibility | AT RISK — blanket flag conservatism not argued |
| Cross-game comparability | MAINTAINED |

## BLOCKER / WARNING / NOTE findings

### BLOCKER-1 — Column-count arithmetic is wrong (51 → 52 assumed; actual 37 → 38; spec says 36)

Plan treats `player_history_all` as 51 cols → 52 post-amendment. **Actual state:**
- Yaml lists 37 columns (confirmable via DESCRIBE).
- Spec 02_00 §2.1 line 90 says `Column count | 36` (LOCKED at v2) — already stale vs yaml.
- `sandbox/.../01_04_02_data_cleaning_execution.py:364` notes "Net: 51 - 16 + 2 = 37 columns" — 51 was a pre-cleaning intermediate, 37 is post-cleaning actual.

Plan's 51/52 arithmetic cascades into T04 yaml schema_version (`'52-col ...'`), T05 INVARIANTS sentence, T06 spec §2.1 cell, T09 CHANGELOG. All silent drift if executed as-written.

**Fix:** T01 verifies actual current yaml column count (37) AND spec §2.1 current-state value (36 per LOCKED v2 — document the pre-existing drift). Template all downstream amendment strings off T01's verified counts. Target: yaml 37 → 38; spec §2.1 from 36 (or correctly 37 pending the pre-existing drift reconciliation) → 38. The spec-vs-yaml pre-existing drift (36 vs 37) is documented in the §7 amendment log as a corrected-during-amendment item.

### BLOCKER-2 — VIEW DDL wrap pattern uses non-existent `pha` alias

Plan T02 says "wrap existing SELECT source in subquery aliased `pha`" + `(pha.toon_id IN (...))`. **Actual DDL** at `sandbox/.../01_04_02_data_cleaning_execution.py:440`: `... FROM matches_flat mf WHERE mf.replay_id IS NOT NULL;`. The source is `matches_flat mf`, NOT `player_history_all` re-projected. `cross_region_toons` CTE derives from `replay_players_raw`; the VIEW body projects from `matches_flat` (which does expose `toon_id` per yaml line 22).

Three ambiguous interpretations of plan T02 (rename `mf` → `pha`? wrap subquery? change source?) each with different effects.

**Fix:** T02 must specify: preserve `FROM matches_flat mf WHERE mf.replay_id IS NOT NULL`; add projected column `(mf.toon_id IN (SELECT toon_id FROM cross_region_toons)) AS is_cross_region_fragmented` inside the existing SELECT; prepend `WITH cross_region_toons AS (...)` CTE. No source rename, no outer subquery alias.

### WARNING-3 — ±5 drift tolerance is I7 magic number

T01 step 3: "If drift > ±5, halt and supersede." WP-3/WP-4 precedents use zero-tolerance halt-on-any-drift. Plan §Assumptions contradicts T01 step 3 ("no ±tolerance"). ±5 has no empirical basis.

**Fix:** Remove "> ±5"; halt on any drift (matches WP-3/WP-4 + §Assumptions). Align T01 + §Assumptions + §Open questions Q4 to one policy.

### WARNING-4 — Plan self-contradicts on drift handling

§Assumptions says "no ±tolerance"; T01 says "> ±5"; §Open questions Q4 says "> ±5". Three instances, two conflicting policies.

**Fix:** Pick one (zero-tolerance per WP-3/WP-4), apply consistently.

### WARNING-5 — INVARIANTS §2 three-sentence coherence not addressed

§2 "Tolerance and accepted bias" paragraph currently has: (a) original accepted-bias sentence; (b) WP-3 PR #200 impact sentence; (c) planned WP-7 sentence. Three appended sentences → long monolithic prose.

**Fix (suggested, not blocking):** Consider extracting WP-3 + WP-7 findings as a sub-heading "§2 Mitigation status" or bullet form. At minimum, explicit sentence breaks.

### WARNING-6 — Blanket flag conservatism not argued vs handle-length breakdown

Plan T02 computes `flagged_toons_length_lt_5 / 5_to_7 / 8_plus` but flag definition ignores length. Blanket flag treats "Zerg" (length 4, handle-collision artifact) identically to "Serral" (length 6, genuine cross-region player). Phase 02 sensitivity analysis gets diluted.

**Fix:** T03 §3 + T05 INVARIANTS §2 sentence explicitly argue blanket-flag conservatism: "false-positive rate bounded by length-<5 count; Phase 02 may subset to length ≥ 8 via additional join for strict analysis." One sentence; cites plan's own length breakdown.

### WARNING-7 — Spec §5.1 does not exist for sc2egset PH; correct is §5.4

Plan T06 step 4 says "§5.1 sc2egset `player_history_all` classification table". Spec 02_00 actual: §5.1 is `matches_history_minimal — sc2egset`; `player_history_all — sc2egset` is at §5.4 (line 379-399).

**Fix:** T06 step 4 + §Scope line 33 must reference §5.4, not §5.1.

### NOTE-8 — ROADMAP.md has zero "51/52/36 cols/columns/-col" references

Grep returns zero. T07 premise of "update current-state 51 → 52 references" has no targets. T07 reduces to: add new 01_04_05 step entry only.

### NOTE-9 — Rare-handle subsample n=96 consistency confirmed (INVARIANTS.md §2 / WP-3 §6).

### NOTE-10 — MMR correlation appropriately scoped out (WP-3 §5 carries it; WP-7 is operationalization).

### NOTE-11 — No plan-code discipline respected in T05 template. OK.

### NOTE-12 — Correlated subquery at n=44,817 × 2,495 is trivial for DuckDB hash-semi-join. Non-issue.

### NOTE-13 — Column-ordering append-at-end matches canonical_slot + WP-6 precedent. OK.

## Verdict

**REVISE BEFORE EXECUTION.** 2 BLOCKERs (column arithmetic; VIEW source alias) + 5 WARNINGs (drift tolerance, self-contradiction, prose coherence, blanket-flag argument, spec section mis-reference). Post-revision, plan is APPROVE-ready within 1-cap.

## If REVISE: required revisions (enumerated)

1. **BLOCKER-1:** T01 verifies current yaml column count (37) AND spec §2.1 LOCKED value (36 — pre-existing drift). Template all downstream strings off T01-verified counts: yaml 37 → 38; spec §2.1 corrected to 38 (acknowledge pre-existing 36→37 drift in §7 amendment log). Remove hardcoded "51"/"52" from plan.
2. **BLOCKER-2:** T02 "Amended DDL" pattern: preserve `FROM matches_flat mf WHERE mf.replay_id IS NOT NULL`; prepend `WITH cross_region_toons AS (...)` CTE; add one projected column `(mf.toon_id IN (SELECT toon_id FROM cross_region_toons)) AS is_cross_region_fragmented` inside existing SELECT. No rename; no wrap.
3. **WARNING-3 + WARNING-4:** Remove "> ±5" everywhere; halt on any drift per WP-3/WP-4 precedent. Align §Assumptions / T01 step 3 / §Open-questions Q4.
4. **WARNING-6:** T03 §3 + T05 INVARIANTS §2 sentence argue blanket-flag conservatism explicitly; cite length breakdown as context.
5. **WARNING-7:** T06 step 4 and §Scope reference §5.4 (not §5.1). §5.1 is MHM.
6. **NOTE-8 housekeeping:** T07 reduces to adding new 01_04_05 step entry; no current-state count references to update.
