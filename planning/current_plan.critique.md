# Plan Critique — reviewer-adversarial Mode A (TG5-PR-5a)

**Target:** `planning/current_plan.md` (TG5-PR-5a — internal-consistency chore)
**Branch:** `docs/thesis-pass2-tg5a-internal-consistency-chore` (base: master @ `fee3d324`)
**Date:** 2026-04-20

## Verdict

**REQUIRE_SUBSTANTIAL_REVISION** — 2 BLOCKERs, 4 WARNs, 4 NOTEs.

Two BLOCKERs (F5.6 Demšar §3.1.3 unverified at both §2.6.3 and §4.4.4) plus four WARNs that collectively undermine the PR's stated "internal consistency" thesis. The plan as written would replace one set of inconsistencies with another and land an unverified primary-source citation in the methodology chapter.

## BLOCKERs

### B1 — F5.6 Edit 2a over-commits to an unverified section attribution
- **Location:** plan Edit 2a (line 179); target `02_theoretical_background.md` line 211
- **Issue:** Plan rewrites prose to assert `$N \geq 10$ — również omawianego w §3.1.3`. But (a) the chapter itself flags this location as unverified via WebFetch/WebSearch; (b) the audit H3 assertion is a one-line claim with no primary-source quote; (c) this reviewer's independent WebFetch of JMLR Demšar 2006 PDF/HTML did not confirm §3.1.3 location either. The Edit 2b flag hedges AFTER the prose has already committed the citation — reads as retrospective cover.
- **Fix:** Rewrite Edit 2a so prose either (i) carries both thresholds with dual `[REVIEW:]` flag and contingent phrasing ("prawdopodobnie w §3.1.3, weryfikowany w Pass 2"), OR (ii) drops the specific subsection number and cites `[Demsar2006]` bare for the cross-dataset threshold.

### B2 — F5.6 Edit 1 (§4.4.4 lines 373+375+377) repeats the over-commitment at a load-bearing chapter
- **Location:** plan T05 Edit 1; target `04_data_and_methodology.md` lines 375, 377
- **Issue:** §4.4.4 hosts the statistical protocol. Landing §3.1.3 as a confirmed citation without PDF verification means the methodology chapter carries an unverified primary-source claim. The Pass-2 audit exists to eliminate exactly this class of error; landing F5.6 on audit H3 alone turns this PR into an instance of the failure mode.
- **Fix:** Stage Edit 1 as `[REVIEW: F5.6 — §3.1.3 per audit H3, unverified in PDF; Pass-2 confirmation required]` rather than a confirmed citation swap; do NOT claim F5.6 "resolved" in WRITING_STATUS.

## WARNs

### W1 — F5.2 THESIS_STRUCTURE footer over-claims "Tabela 4.4b, §4.1.3"
- **Location:** plan T02 Edit; target `thesis/THESIS_STRUCTURE.md` line 67
- **Issue:** §1.2 prose forward-references §1.4 (not §4.1.3 or Tabela 4.4b). New footer names a specific table §1.2 never cites — mirrors the defect F5.2 is meant to fix (old under-claimed; new over-claims).
- **Fix:** Soften to "Literature review (primary). Chapter 1 framing occasionally alludes to empirical findings presented in Chapter 4 (§4.1.3–§4.1.4 on cross-corpus data asymmetry); those findings are not anticipated here." Drop specific Tabela anchor.

### W2 — F5.3 asymmetric hedging (§2.2.3 vs §2.5.5) with no scheduled close
- **Location:** plan T03; §1.3 "asymmetric framing intentional" acknowledgement
- **Issue:** §2.5.5 names Thorrez2024 as academic proxy; §2.2.3 hedges without naming it. "Deferred to PR-5b" — but PR-5b in the dispatch DAG is scoped to F5.4 (§4.1.3 circular justification), NOT F4.5 Aligulac. There is no subsequent PR that will inject the Thorrez comparator at §2.2.3 → this PR lands a **permanent** inconsistency dressed as temporary.
- **Fix:** Either (a) include §2.2.3 Thorrez comparator inline with `[REVIEW:]` flag (reclassifies edit as science-lite — moves to PR-5b), OR (b) update §1.2 of this plan to explicitly add F4.5 to PR-5b's scope.

### W3 — F5.1 "2 [REVIEW]" count re-embeds drift risk
- **Location:** plan T01 Edit 2 (line 74); format `2 [REVIEW]`
- **Issue:** Audit H1 counts 3 concerns (GarciaMendez2025 / Shin1993+Forrest2005 / Mangat2024). Plan records `2 [REVIEW]` because line-13 tag physically bundles the second+third. Different counting convention than the audit used to flag the drift — a future audit using audit-convention will re-flag "2 but should be 3". Recreates the drift at different granularity.
- **Fix:** Use `2 physical [REVIEW] tags covering 3 audit-named concerns` in the Flag count cell; mirror wording in Pass-2 status and WRITING_STATUS.

### W4 — F5.5 placement rationale misnames §3.4's organizing principle
- **Location:** plan T04 Edit; target `03_related_work.md` §3.4.3
- **Issue:** Sentence grounds placement in "wspólny gatunek RTS z grą StarCraft II omawianą w §3.4.1". But §3.4 is titled "Predykcja wyników w Age of Empires II"; §3.4.1 is CetinTas2023 on AoE2 — NOT about SC2. The clause misstates what §3.4 contains.
- **Fix:** Rewrite around game identity (AoE2), not genre (RTS). Example: `§3.4 obejmuje literaturę predykcji w Age of Empires II; Elbert2025EC dotyczy AoE2 w formacie drużynowym i mieści się w tym podrozdziale na podstawie gry, a nie liczby graczy — §3.3 obejmuje literaturę predykcji spoza AoE2.`

## NOTEs

### N1 — Cat F frontmatter lacks `source_artifacts` + `invariants_touched`
Low-risk for chore PR; flagged against `writing_protocol.md:82`.

### N2 — T05 Edit 2a + Edit 2b self-contradicting sequentially on line 211
Edit 2a commits the §3.1.3 claim in prose; Edit 2b appends a hedge flag acknowledging the location is unverified. Reader sees committed-then-hedged — either collapse to one hedged prose edit, or accept the tension.

### N3 — T03 gate is weak (stem grep)
`grep -c "kalibracja" … ≥ baseline+1` satisfied by any "kalibracja" mention. Stronger gate: `grep "80%" … | grep "kalibrac"` returns ≥ 1 (confirms co-location of the 80% token with the calibration framing).

### N4 — Pre-flight check tautological
"confirm no staged or unstaged modifications … apart from this plan file" is self-satisfying. Use `git status --porcelain | grep -v '^ M planning/current_plan.md$' | wc -l` = 0.

## Examiner's anticipated questions

1. Where in Demšar 2006 does the N ≥ 10 data-sets threshold actually appear? (plan provides no primary-source read)
2. If Aligulac's 80% is calibration, why does §2.2.3 not name the Thorrez 80.13% proxy when §2.5.5 does?
3. Why is Elbert2025EC placed in AoE2 section under "RTS genre" rationale when §3.4.1 is AoE2 (CetinTas), not SC2?
4. Why does REVIEW_QUEUE Flag count use one convention and Pass-2 status another?
5. What is §1.2's actual feed from Phase 01? (footer commits to "Tabela 4.4b" not present in §1.2)

## Weakest link

**F5.6 / T05.** This PR would commit two unverified primary-source citations (§2.6.3 line 211 and §4.4.4 lines 375+377) on the strength of an audit assertion the same plan acknowledges is unverified. The chore-scope discipline "no new claims" is violated de facto by Edit 2a.

## Recommended revisions before execution

(A) **Halt T05 Demšar swap** — either retrieve readable PDF of Demšar 2006 and verify §3.1.3, OR restructure T05 to leave §3.2 citations in place with `[REVIEW: audit H3 claims §3.1.3; unverified; Pass 2]` flags only. Do not commit the swap to master without verification.

(B) **Revise T02 footer** — drop specific "Tabela 4.4b, §4.1.3" anchor.

(C) **Resolve F5.3 scope** — either inline §2.2.3 Thorrez comparator (reclassify as science-lite) OR amend PR-5b scope to explicitly include F4.5.

(D) **Revise T04 sentence** — name AoE2 as §3.4's organizing principle, not RTS genre.

(E) **Resolve T01 Flag-count convention** — use "2 physical / 3 audit-named" phrasing.

(F) **Strengthen T03 gate** — add `grep "80%" | grep "kalibrac"` ≥ 1 co-location check.

## Sources consulted (for methodology verification)

- Demšar 2006 — JMLR landing: https://jmlr.org/papers/v7/demsar06a.html
- Demšar 2006 — JMLR PDF direct: https://www.jmlr.org/papers/volume7/demsar06a/demsar06a.pdf (PDF content not extractable via WebFetch in this environment)
- García & Herrera 2008 — JMLR Extension: https://www.jmlr.org/papers/volume9/garcia08a/garcia08a.pdf (relevant as alternative anchor for H3 hypothesis)

## Summary table

| # | Severity | Risk | What breaks if ignored |
|---|---|---|---|
| B1 | BLOCKER | Demšar §3.1.3 for N≥10 not verified against PDF | Examiner retrieves PDF, finds threshold elsewhere, cites as factual error |
| B2 | BLOCKER | §4.4.4 citation swap replicates B1 at load-bearing locus | Methodology chapter citation fails primary-source check |
| W1 | WARN | THESIS_STRUCTURE footer over-claims "Tabela 4.4b, §4.1.3" | Structural footer claims more than §1.2 prose supports |
| W2 | WARN | Aligulac 80% reframing asymmetric between §2.2.3 and §2.5.5 with no scheduled close | Permanent inconsistency dressed as temporary |
| W3 | WARN | `2 [REVIEW]` count uses different convention than audit H1 | Re-creates drift at different granularity |
| W4 | WARN | F5.5 placement rationale misnames §3.4's organizing principle | Prose rationale contradicts actual §3.4 structure |
| N1 | NOTE | Frontmatter lacks Cat F required fields | Low-risk protocol non-compliance |
| N2 | NOTE | Edit 2a and Edit 2b sequentially self-contradict | Reader confusion |
| N3 | NOTE | T03 gate is weak (stem grep) | Could false-pass on a botched edit |
| N4 | NOTE | Pre-flight check tautological | Minor |
