---
plan_ref: planning/current_plan.md
spec_ref: reports/specs/01_05_preregistration.md @ master 94e74d69
reviewer: reviewer-adversarial
date: 2026-04-19
round: 1
---

# Critique: Chapter 4 DEFEND-IN-THESIS residuals — canonical_slot flag (PR-3)

## Summary

Simplest PR in the three-PR sequence (NEW §4.4.6 + §4.1.2.1 footnote +
BACKLOG F1 bullet). All load-bearing empirical claims verified: 80,3%
/ +11,9 at `reports/research_log.md:107`; 52,27% sentence at
`thesis/chapters/04_data_and_methodology.md:93`; §4.4.5 ends cleanly;
invariant #5 IS "symmetric player treatment" (PR-2 M1 not repeated);
`grep '[PRE-canonical_slot]'` returns 0 in aoestats CSV (honest-match
valid); spec §1 line 71 definition present. **0 BLOCKERs**, **2 MAJORs**,
**3 MINORs**. Verdict: **REVISE — non-blocking**.

## Blockers

None.

## Majors

### M1 — `faction` is NOT aggregate in aoestats schema; T01 (b) conflates post-Phase-02 aggregate with raw-schema per-slot

Plan T01 (b) lists `faction`, `opponent_faction`, `won` as "aggregate
UNION-ALL-symmetric" exempt from flag. Verified against
`src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_1v1_clean.yaml:66–70, 95–99`:
view stores civilization choice as two per-slot columns `p0_civ` +
`p1_civ` — both slot-conditioned. aoestats `matches_1v1_clean` does
NOT materialize a slot-agnostic `faction` column.

DEFEND-doc phrasing is sustainable only when "faction aggregate" is
read as "post-Phase-02 UNION-ALL aggregate", not "raw-schema aggregate".

**Fix.** §4.4.6 (b) must disambiguate: "W schemacie `matches_1v1_clean`
civilizacja jest zakodowana per-slot (`p0_civ`, `p1_civ`); agregacja
`faction` powstaje w Phase 02 po UNION-ALL per-gracz."

### M2 — §4.4.6 char budget 1 800 – 2 500 unrealistic given PR-2 §4.4.5 delivered 5 020 chars (+67% over 3 000 budget)

PR-1 overage 59%, PR-2 overage 67%. Three-paragraph methodology
subsections consistently exceed targets 50–70%. §4.4.6 at 50–70%
overrun → actual 2 700 – 4 250 chars.

**Fix.** Widen to 1 800 – 3 500 chars. If exceeded by writer-thesis,
flag in Chat Handoff Summary; no budget amendment unless >4 000.

## Minors

### m1 — Second §4.4.6 flag is self-verifying

Flag `[REVIEW: Pass-2 — BACKLOG F1 ... sprawdzić spójność ze stanem
F1 na master po merge PR-3]` — PR-3 IS the merge; flag trivially
resolves by Pass-2 time. Same issue as PR-2 m_r2_5.

**Fix.** Either drop, or re-scope to: `[REVIEW: Pass-2 — §4.4.6 (c)
closure narrative assumes F1 unexecuted; verify F1 state advanced
beyond Predecessors bullet by Pass-2 time]`.

### m2 — T04 Q3 DEFEND doc closing paragraph is optional scope creep

Closing paragraph on DEFEND doc is planning-artifact housekeeping,
not thesis writing. 6 × `[x]` evidence is self-explanatory.

**Fix.** Skip in T04; if desired, follow-up chore.

### m3 — Redundant file-path anchoring for invariant #5

Plan prescribes "niezmiennik #5 symmetric player treatment per
`.claude/scientific-invariants.md` #5". Defensive over-anchoring
after PR-2 M1. Chapter 4 uses short form `niezmiennik I5` at
`04_data_and_methodology.md:93, 138, 181, 211`.

**Fix.** Keep short form "niezmiennik I5 (symmetric player
treatment)" — PR-2 M1 failure was miscontent not missing file anchor.

## Passes (verified)

- **W3 ARTEFACT_EDGE numerics:** 80,3% / +11,9 verified at
  `reports/research_log.md:107`. PASS.
- **`[PRE-canonical_slot]` artifact state:** `grep` returns 0 in
  aoestats CSV — honest-match framing accurate. PASS.
- **Invariant #5 content:** verified at `scientific-invariants.md:158–163`
  = "symmetric player treatment". PASS — not repeating PR-2 M1.
- **§4.1.2.1 footnote anchor:** 52,27% sentence at
  `04_data_and_methodology.md:93` — in §4.1.2.1 (within §4.1.2 "Korpusy
  Age of Empires II"). Natural for appended footnote clause. PASS.
- **BACKLOG F1 Predecessors format:** F1 has a Predecessors field
  (line 17) that accepts bullet-list; PR-3 addition is a clean add. PASS.
- **§4.4.5 ends cleanly at line ~387; §4.4.6 as sibling `###`
  structurally correct. PASS.
- **Spec §1 line 71 `[PRE-canonical_slot]` definition:** present and
  cited correctly. PASS.

## Invariant compliance

| # | Status | Note |
|---|--------|------|
| I1–I4 | N/A | No splitting/identity/temporal/modeling |
| I5 | RESPECTED | Cited correctly; not repeating PR-2 M1 |
| I6 | RESPECTED | Commit `ab23ab1d` + spec line anchors |
| I7 | RESPECTED | All numbers traceable |
| I8 | RESPECTED | Flag scoped to aoestats; cross-game unaffected |
| I9 | RESPECTED | Derives from Phase 01 + Phase 06 artifacts only |

## Weakest link

§4.4.6 (b) per-slot vs aggregate disambiguation (M1). Without it,
examiner asks "show me the `faction` column in `matches_1v1_clean`"
and the answer is "`p0_civ` and `p1_civ`" — which contradicts the
plan's "aggregate" framing. One sentence fix.

## Verdict

**REVISE — non-blocking.** M1 + M2 handleable by writer-thesis at
draft time. m1–m3 are stylistic. No round-2 critique required if
M1+M2 addressed before execution.


---

## Round 2 — execution-side

**Reviewer:** reviewer-adversarial
**Date:** 2026-04-19
**Base ref:** master 94e74d69
**Branch:** docs/thesis-ch4-canonical-slot-flag

### Summary

Writer-thesis delivered all three tasks. §4.4.6 (5 026 chars) overshoots
the M2-widened 3 500-char ceiling by 43.6%, crosses 4 000 soft-stop by
25.6%, but the overage is concentrated in the M1-driven "Zakres flagi"
paragraph (2 104 chars) — load-bearing, not inflation. All M1/M2/m1/m3
plan-side fixes verified implemented. 3 net new `[REVIEW]` flags match
gate. All empirical anchors independently verified. **0 BLOCKERs,
0 MAJORs, 3 MINORs.** Verdict: **PASS — cleared for T04 wrap-up.**

### Blockers

None.

### Majors

None.

### Minors

#### m_r2_1 — Off-by-one in aoestats CSV row count (137 vs actual 136)

§4.4.6 (c) cites "137 wierszy". CSV has 136 data rows. Inherited
miscount from BACKLOG F6 line 93 and REVIEW_QUEUE §4.1.4 Notes.
Qualitative claim ("0 hits") unaffected. Fix via Pass-2 or F6 execution
sweep (3 sites at once).

#### m_r2_2 — "Spec §14 v1.0.1" pointer redirection

§4.4.6 (c) cites amendment log §14 v1.0.1 where substantive content is
in §9/§11. Defensible pointer convention but indirect. Pass-2 revise
to "spec §9 + §11 (v1.0.1 amendment, patrz §14)".

#### m_r2_3 — Footnote clause 300 chars vs 100-200 target

§4.1.2.1 footnote at 300 chars (+50% over target). Load-bearing
(2 cross-refs + flag). Matches plan M2 overage-acceptance logic.

### Passes (verified)

- **M1 regression check:** §4.4.6 (b) explicitly distinguishes raw
  `matches_1v1_clean` per-slot (`p0_civ` + `p1_civ`) from post-Phase-02
  UNION-ALL aggregate (`faction`, `opponent_faction`, `won`). Four
  M1-critical claims all present. PASS.
- **Schema anchors:** `matches_1v1_clean.yaml:66-70, 95-99` confirms
  `p0_civ` VARCHAR + `p1_civ` VARCHAR per-slot. PASS.
- **M2 char budget transparency:** §4.4.6 = 5 026 chars; writer-thesis
  reported ~5 000. Overshoot concentrated in M1-disambiguation
  paragraph (2 104 chars). No padding. Load-bearing. PASS.
- **M3 invariant I5 short form:** §4.4.6 (b) cites "niezmiennikiem I5
  (symmetric player treatment)". No file-path anchor. Consistent with
  chapter pattern. PASS.
- **Flag count gate (3):** 2 in §4.4.6 + 1 in §4.1.2.1 footnote. PASS.
- **Re-scoped flag 2 wording:** "F1 state advanced beyond Predecessors
  bullet" — not self-verifying; PR-2 m_r2_5 issue not repeated. PASS.
- **§4.1.2.1 footnote placement:** At `04_data_and_methodology.md:93`
  — specific "team=1 wygrywa 52,27%" sentence. Cross-refs to §4.4.6 +
  BACKLOG F1 both present. PASS.
- **BACKLOG F1 Predecessors bullet:** Added without disturbing other
  fields; F6 intact. PASS.
- **REVIEW_QUEUE + WRITING_STATUS updates:** New §4.4.6 Pending row;
  §4.1.2 Notes extended 6→7 flag count; WRITING_STATUS §4.4.6 DRAFTED
  row added; Last updated 2026-04-19. PASS.
- **Cross-reference integrity:** BACKLOG F1, F6, §4.4.5, spec §1
  line 71, spec §11, commit `ab23ab1d` — all verified (§14 pointer
  flagged as m_r2_2). PASS.
- **Honest-match principle:** §4.4.6 (c) states 0/137 grep result;
  frames flag as "konwencja metodologiczna na poziomie spec §1 linia
  71, nie metadana artefaktu"; cross-refs F6. Four-component honest-
  match present. PASS (with m_r2_1 off-by-one note).
- **Examiner defense simulation:** All 4 preempted — `faction` column
  location; missing tag explanation; invariant I5 content correct;
  canonical_slot never-derived path. PASS.
- **Numerical accuracy:** 80,3% / +11,9 verified `research_log.md:107`;
  52,27% anchor at `04_data_and_methodology.md:93`; -0,72 p.p. at
  `research_log.md:105-106`; 1,5 p.p. floor `research_log.md:105`.
  PASS.
- **I5 content citation (PR-2 M1 regression check):** "niezmiennikiem
  I5 (symmetric player treatment)" — correct content, NOT conflated
  with matchmaking-equalization. PASS — PR-2 M1 failure not repeated.

### Invariant compliance

| # | Status | Note |
|---|--------|------|
| I1–I4 | N/A | No split/identity/temporal/modeling |
| I5 | RESPECTED | Short-form citation, correct content |
| I6 | RESPECTED | All anchors inline (commit, research_log, yaml, spec) |
| I7 | RESPECTED | Numbers traceable |
| I8 | RESPECTED | Flag scope aoestats-only; cross-game aggregates unaffected |
| I9 | RESPECTED | Derives from completed Phase 01 artifacts |

### Lens assessments

- **Temporal discipline:** N/A.
- **Statistical methodology:** SOUND.
- **Feature engineering:** SOUND — per-slot/aggregate scope correctly
  drawn.
- **Thesis defensibility:** STRONG — all 4 examiner questions
  preempted.
- **Cross-game comparability:** MAINTAINED.

### Weakest link

"w pełni tłumaczy" ("fully explains") wording in §4.4.6 (a) — verbatim
from research_log but strong rhetoric. CMH -0.72 p.p. pre-loaded
defense in same paragraph. Pass-2 could soften to "znacząco tłumaczy".
Not a round-2 gate.

### Verdict

**PASS — cleared for T04 wrap-up.** All plan-side M1/M2/m1/m3 fixes
implemented. Examiner defense preempts all questions. Writer-thesis
can proceed to version bump 3.25.0 → 3.26.0, CHANGELOG entry, DEFEND
checkbox #5 → `[x]` (completing 6-of-6 residuals across PR-1/#175,
PR-2/#176, PR-3).
