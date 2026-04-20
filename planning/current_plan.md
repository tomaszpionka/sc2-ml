---
category: F
branch: docs/thesis-pass2-tg5a-internal-consistency-chore
date: 2026-04-20
planner_model: claude-opus-4-7
---

# Plan: TG5-PR-5a — Pass-2 internal-consistency chore (F5.1, F5.2, F5.3, F5.5, F5.6)

**Category:** F (Thesis)
**Branch:** `docs/thesis-pass2-tg5a-internal-consistency-chore`
**Base:** `master` (at `fee3d324`)
**Audit source:** `thesis/reviews_and_others/pass2_dispatch.md` §Task Group 5 (lines 153–175); Appendix A H1–H3 (lines 307–309); Appendix B A15 (lines 410–414) for F5.3 / F4.5 reframing; F4.5 audit text (line 124) providing the calibration-vs-accuracy distinction. Audit saved 2026-04-20 from transcript `36812a12` line 6 for durable recovery.

## Problem Statement

Pass-2 audit Task Group 5 identified 6 internal-consistency drifts across WRITING_STATUS, REVIEW_QUEUE, THESIS_STRUCTURE, and chapters 1–4. This PR (PR-5a chore subset) fixes 5 of them; F5.4 and F4.5 are deferred to PR-5b (science-lite). F5.6 is executed as flag-planting only (no §3.2 → §3.1.3 swap) pending readable Demšar 2006 PDF verification per Mode A BLOCKER resolution.

## Literature Context

The only new literature reference planted is a meta-reference to Demšar 2006 via the F5.6 `[REVIEW]` flags — no new bib entries, no new claims in prose. F5.3 calibration-vs-accuracy framing rests on the audit's primary-source reading of the Aligulac FAQ (audit Appendix B A15 line 411). The Thorrez2024 comparator is already in the bib (not added here) and referenced only inside existing/reworded [REVIEW] flags.

## Assumptions & Unknowns

- **Assumed:** The Demšar 2006 §3.1.3 location claim from audit H3 is the best available guidance until a readable PDF confirms it. Until verification, F5.6 flags rather than swaps.
- **Unknown:** Exact section location of the N ≥ 10 cross-dataset threshold in Demšar 2006 (JMLR PDF unreachable via WebFetch in this environment). Pass-2 resolves via manual PDF read.
- **Assumed:** The audit's counting of §1.1 "3 flags" (H1) refers to audit-named concerns, not physical [REVIEW:] tags. Plan records both counts explicitly to resolve the convention ambiguity.

## Gate Condition

Per-task gates are documented inline at each T0x step (see §2 Execution Steps). Aggregate: all 6 tasks pass their gates; `git diff --stat` touches exactly the 6 thesis/ files plus `pyproject.toml` + `CHANGELOG.md`; no src/ / reports/ / sandbox/ / references.bib changes.

## Open Questions

None load-bearing for PR-5a. Pass-2 targets:
1. Demšar 2006 §3.1.3 vs §3.2 location confirmation (F5.6 flag closure).
2. Whether the audit's H1 "3 flags" counting convention or physical-tag counting convention becomes the repo-wide norm for REVIEW_QUEUE.

## 0. Pre-flight

- Confirm branch is `docs/thesis-pass2-tg5a-internal-consistency-chore` not `master` (check: `git branch --show-current`).
- Confirm audit source file is present at `thesis/reviews_and_others/pass2_dispatch.md` (prior commit `195a33c8` on this branch).
- Confirm no staged or unstaged modifications in working tree apart from this plan file before starting T01.
- No purge step: the prior plan artifacts (`planning/current_plan.md` + `planning/current_plan.critique.md` from TG4) already purged in the master merge via the standard purge-chore cycle (the merge of PR #190 included the post-TG4 purge). This file overwrites any residual stub.

## Scope

(Canonical scope declaration for hook compliance — see §1.1/§1.2/§1.3 below for full detail.)

## 1. Scope, constraints, and discipline

### 1.1 What this PR covers

Five chore-tier findings from the Pass-2 audit Task Group 5:

1. **F5.1 — WRITING_STATUS + REVIEW_QUEUE §1.1 flag-count drift**
2. **F5.2 — THESIS_STRUCTURE.md Chapter 1 feed-attribution drift**
3. **F5.3 — §2.2.3 / §2.5.5 Aligulac 80% flag-presence inconsistency** (subsumes F4.5 reframing which was deferred from TG4)
4. **F5.5 — §3.3 / §3.4 Elbert 2025 placement decision, documented inline**
5. **F5.6 — §4.4.4 + §2.6.3 + §4.1.4 Demsar §3.2 / §3.1.3 location uncertainty flagged (swap deferred to Pass 2 after PDF verification)**

### 1.2 What this PR does NOT cover

- **F5.4** (§4.1.3 circular spec-reference) — moved to PR-5b (science-lite). **PR-5b scope also expanded to include F4.5 Aligulac Thorrez-proxy-insertion at §2.2.3** (the Thorrez comparator sentence originally attempted under F5.3 in this chore PR but removed per R6 iter-1 revision to stay within chore discipline). Both F5.4 and F4.5 require literature-level prose insertions; PR-5b is the natural vehicle.
- **TG6 items** — separate PRs (PR-6a, PR-6b).
- **F6.11** — already landed in TG4 (bib has `Stein, Nikolai` and `von Schenk, Alicia`; verified via grep on `thesis/references.bib`). Drop from future PR-6b.
- Any new literature search, bib additions, or methodology defence.
- Any Chapter 4 §4.4.4 *within-game* protocol rewrite — TG1 already reframed that as candidate-list framing; F5.6 is a pure citation-location fix, not a methodology edit.

### 1.3 Binding discipline

- Chore PR: all edits are citation-location fixes, flag-presence reconciliations, documentation-of-decision sentences, and metadata refreshes in status files. No new claims, no methodology changes, no bib additions.
- F5.3 reframing (Aligulac 80%) is **not** a new claim — it applies the F4.5 finding (misreading confirmed in audit Appendix B A15 line 411) by rewording existing sentences to distinguish "calibration ~80%" (Aligulac FAQ) from "classification accuracy" (Thorrez 2024 Glicko-2 at 80.13% as academic proxy). Both locations must land with consistent framing and consistent flag presence. Note: The audit summary uses "§2.5.4" for this finding, but the actual flag at chapter line 183 sits inside the `### 2.5.5` heading (confirmed via structural check); the correct section label is §2.5.5 throughout this plan. F5.3 reframing applies a prose-softening of the existing §2.2.3 claim (calibration-not-accuracy hedge) consistent with the existing §2.5.5 [REVIEW] flag; the full F4.5 Thorrez-comparator insertion at §2.2.3 is explicitly deferred to PR-5b per §1.2.
- F5.5 documentation decision is a single-sentence inline addition to §3.4 (or §3.3) explaining the placement logic; does not move Elbert between sections.
- F5.6 is executed as flag-planting only; the §3.2 → §3.1.3 swap is deferred to a post-Pass-2 PR once a readable Demšar 2006 PDF confirms the corrected location. All four citation loci (§4.4.4 lines 375+377, §4.1.4 line 213, §2.6.3 line 211) receive `[REVIEW:]` flags acknowledging the uncertainty; the existing `§3.2` text is left in place.
- Invariant discipline: no changes touching `.claude/scientific-invariants.md`, no changes to `reports/` or `sandbox/`, no changes to `src/`.

## Execution Steps

(Step list anchored at §2 Task breakdown below — T01 through T06 with per-task gates.)

## 2. Task breakdown

### T01 — F5.1: WRITING_STATUS.md + REVIEW_QUEUE.md §1.1 row refresh

**Files:**
- `thesis/WRITING_STATUS.md` (Chapter 1 table, §1.1 row)
- `thesis/chapters/REVIEW_QUEUE.md` (Pending table, §1.1 row — already exists at line 19 with `Flag count` cell = `0`)

**Empirical anchor:**
- §1.1 current in-prose `[REVIEW:]` flags (verified 2026-04-20 via grep on `thesis/chapters/01_introduction.md`):
  - Line 11: `[REVIEW: GarciaMendez2025 — zweryfikować pełną listę autorów, grę docelową i dokładną trafność]`
  - Line 13: `[REVIEW: Shin1993 i Forrest2005 dotyczą rynków sportów tradycyjnych ... Mangat i in. [Mangat2024] omawiają zakłady esportowe ...]`
- §1.1-adjacent bibliography-footer `[REVIEW:]` annotations (lines 81, 83) are part of the draft's chapter-local `## References` block, not in-prose flags; count them separately.
- REVIEW_QUEUE.md Pending table columns are: `Section | Chapter file | Drafted date | Flag count | Key artifacts | Pass 2 status`.
- WRITING_STATUS.md Chapter 1 table columns are: `Section | Status | Feeds from | Notes` — there is NO `Flag count` column in WRITING_STATUS.md.

**Edit 1 — WRITING_STATUS.md §1.1 row:**
- There is no `Flag count` column in WRITING_STATUS.md. Do NOT modify or reference a non-existent flag-count cell.
- Target: the **Notes** cell of the existing §1.1 row.
- Append to the current Notes value: `**2026-04-20 (PR-TG5a):** §1.1 has 2 physical [REVIEW:] tags covering 3 audit-named concerns (GarciaMendez2025 at line 11; Shin1993/Forrest2005/Mangat2024 bundled at line 13) plus 2 bibliography-footer flags (lines 81, 83 of the chapter file). Prior REVIEW_QUEUE Flag count "0" was drift from an earlier revision; updated per F5.1 of Pass-2 audit.`

**Edit 2 — REVIEW_QUEUE.md Pending table §1.1 row (UPDATE, not insert):**
- §1.1 row **already exists** at line 19 of `thesis/chapters/REVIEW_QUEUE.md` with `Flag count` = `0` and `Pass 2 status` = `Pending — Pass 2 blocking items resolved`. Do NOT insert a duplicate row.
- Update the existing §1.1 row:
  - Change `Flag count` cell from `0` to `2 physical [REVIEW] tags covering 3 audit-named concerns`. [R4 choice: option (b) — record `2 physical [REVIEW] tags covering 3 audit-named concerns` because line 13 bundles three audit-named concerns (GarciaMendez2025 / Shin1993+Forrest2005 / Mangat2024) in a single tag; the bibliography-footer annotations at lines 81, 83 are not in-prose flags and are not counted here. The plan comment below explains the bundle for future auditors.]
  - Append to `Pass 2 status` cell: `**2026-04-20 (PR-TG5a):** flag count corrected per F5.1 of Pass-2 audit — §1.1 has 2 physical in-prose [REVIEW:] lines (line 11: GarciaMendez2025; line 13: bundles three concerns — Shin1993+Forrest2005 generalisation scope + Mangat2024 psychological-gambling framing; audit F5.1 counts 3 named concerns across these 2 physical flags). Key verification items: (1) GarciaMendez2025 full author list + target game + accuracy from ScienceDirect full text; (2) Shin1993 + Forrest2005 generalisation scope; Mangat2024 psychological-gambling framing; (3) bibliography-footer entries at lines 81, 83 noted separately.`

**Gate:** after T01, `grep "§1.1" thesis/chapters/REVIEW_QUEUE.md` still returns ≥ 1 (row was already present); the §1.1 row's `Flag count` cell now reads `2 physical [REVIEW] tags covering 3 audit-named concerns` (no longer `0`). WRITING_STATUS.md §1.1 Notes cell carries a `(PR-TG5a)` annotation.

### T02 — F5.2: THESIS_STRUCTURE.md Chapter 1 feed attribution

**File:** `thesis/THESIS_STRUCTURE.md` (line 67, the Chapter 1 closing footer)

**Empirical anchor:**
- Line 67 current: `**Fed by:** Background reading, literature review. No roadmap phase directly.`
- §1.2's data-asymmetry framing (chapter file `01_introduction.md` line 21) references the AoE2 vs SC2 data asymmetry that is anchored on Phase 01 Tabela 4.4b (§4.1.3).
- §1.1 line 15 cites `Bialecki2023` (SC2EGSet corpus descriptor) which is a Phase 01 motivational reference.

**Edit:**
- Replace line 67 with:
  > `**Fed by:** Literature review (primary). Chapter 1 framing occasionally alludes to empirical findings presented in Chapter 4 (§4.1.3–§4.1.4 on cross-corpus data asymmetry) without pre-committing them; those findings are not anticipated here and remain the responsibility of Chapter 4.`

**Gate:** after T02, grep `"roadmap phase directly"` on `thesis/THESIS_STRUCTURE.md` returns 0 lines; grep `"cross-corpus data asymmetry"` on the same file returns ≥ 1 match.

### T03 — F5.3: §2.2.3 + §2.5.5 Aligulac 80% reframe (applies F4.5) + flag consistency

**Files:**
- `thesis/chapters/02_theoretical_background.md` line 39 (§2.2.3)
- `thesis/chapters/02_theoretical_background.md` line 183 (§2.5.5 [REVIEW] flag referencing §2.5.5 Aligulac methodology)

**Audit resolution for F4.5 (Appendix B A15, lines 410–414):**
- The Aligulac FAQ's 80% refers to **calibration** ("actual winrate close to predicted winrate up to about 80%"), not classification accuracy.
- No direct academic validation of Aligulac's bespoke algorithm exists.
- Thorrez 2024 (EsportsBench) Glicko-2 at 80.13% on Aligulac SC2 data is the closest academic proxy — but it evaluates Glicko-2, not Aligulac's specific algorithm.

**Edit 1 — §2.2.3 line 39 (chapter prose rewrite):**
- Current (ground truth from master, confirmed via grep): `Aligulac generuje predykcje wyników nadchodzących meczów wraz z miarami rzetelności, raportowanymi przez społeczność na poziomie około 80% prognozowanego prawdopodobieństwa [Aligulac]; ta wartość ma jednak charakter samodzielnej walidacji społecznościowej i — zgodnie z dyskusją w §2.5.4 — wymaga niezależnej walidacji akademickiej, której obecnie brak.`
- Note: the "Current:" excerpt reads `§2.5.4` (the section that discusses the Aligulac methodology) — this is correct; the flag added by this PR sits inside the `### 2.5.5` heading. The prose at line 39 legitimately points to §2.5.4 (methodology section); this plan updates it to reference `§2.5.5` as part of the rewrite below.
- Rewrite to distinguish calibration from accuracy, keeping the edit within chore scope (no new Thorrez2024 citation at §2.2.3 — that insertion is deferred to PR-5b):
  > Rewording target: change "80% prognozowanego prawdopodobieństwa" to "80% kalibracji" with a brief hedge distinguishing calibration from classification accuracy; update the forward-reference from `§2.5.4` to `§2.5.5`; plant a `[REVIEW:]` flag referencing the F5.3 inconsistency and explicitly noting that the Thorrez-proxy-insertion is deferred to PR-5b alongside F5.4. Do NOT add a new Thorrez2024 comparative sentence at §2.2.3 — that constitutes a new claim and violates §1.3 "no new claims" for this chore PR.

**Edit 2 — §2.5.5 line 183 [REVIEW] flag rewrite:**
- Current (second `[REVIEW:]` on line 183): `[REVIEW: kalibracja Aligulac do ~80% prognozowanego prawdopodobieństwa, raportowana w dokumentacji systemu [Aligulac], opiera się na samodzielnej analizie społeczności — warto zweryfikować, czy literatura akademicka (np. EsportsBench [Thorrez2024]) zawiera niezależną walidację porównawczą z innymi systemami, którą można by przytoczyć dla wzmocnienia argumentacji.]`
- Rewrite to align with §2.2.3 framing and close the "warto zweryfikować" question now resolved via F4.5:
  > `[REVIEW: kalibracja Aligulac do ~80% z FAQ [Aligulac] — miara skali probabilistycznej, nie trafności klasyfikacyjnej; referencyjnym akademickim proxy jest 80,13% Glicko-2 na danych SC2 z Thorrez2024 (ocena Glicko-2, nie specyficznego algorytmu Aligulac). Pass 2 weryfikuje aktualne brzmienie FAQ na aligulac.com/about oraz dokładną wartość Thorrez2024 z Tabeli 2 preprintu. Framing zsynchronizowany z §2.2.3 per F5.3 Pass-2 audit.]`

**Edit 3 — §2.5.4 body (lines 163–171) sanity check:**
- §2.5.4 prose does NOT currently contain a numeric 80% claim (verified 2026-04-20 via `grep "80" thesis/chapters/02_theoretical_background.md` which matches only line 39 in §2.2.3 and line 183 in §2.5.5). No §2.5.4 edit required. If executor discovers a previously-unseen 80% mention in §2.5.4 during T03 execution, apply the same reframing as Edit 1 and ensure flag consistency.

**Gate:** after T03:
- **Pre-edit baseline (verified via grep):** `grep -c "kalibracja" thesis/chapters/02_theoretical_background.md` = 3 (nominative-only); `grep -c "kalibrac" …` = 10 (stem, all declensions). Post-edit target: ≥ baseline + 1 for `kalibracja` count.
- `grep -c "kalibracja" thesis/chapters/02_theoretical_background.md` increases by ≥ 1 vs. pre-edit baseline (new §2.2.3 usage).
- `grep -c "Thorrez2024" thesis/chapters/02_theoretical_background.md` remains ≥ 1 (currently 3 occurrences in §2.5.5 pre-edit; gate checks presence, not exclusivity — no new §2.2.3 citation added in this chore PR).
- `grep "80%" thesis/chapters/02_theoretical_background.md | grep -vE "kalibrac|trafnośc[ią]"` returns 0 lines asserting 80% as a bare accuracy claim (stem `kalibrac` matches all Polish declensions including nominative `kalibracja`, genitive `kalibracji`, accusative `kalibrację`; and `trafności`/`trafnością`).
- `[REVIEW:]` flag framing: §2.2.3 flag references F5.3 inconsistency and defers Thorrez-proxy insertion to PR-5b; §2.5.5 flag cites Thorrez2024 as proxy. Asymmetric framing is intentional and documented (R6 deferral in §1.2) — the gate does NOT require both flags to cite Thorrez2024 directly.

### T04 — F5.5: Elbert 2025 §3.3 vs §3.4 placement decision documentation

**File:** `thesis/chapters/03_related_work.md` (single-sentence insertion at §3.4.3)

**Empirical anchor:**
- §3.3 heading (line 85): `## 3.3 Predykcja wyników w grach MOBA i pozostałych gatunkach esportowych`
- §3.3 subsections span MOBA (§3.3.1 Dota 2, §3.3.2 LoL), FPS (§3.3.3 Counter-Strike), tactical FPS (§3.3.4 Valorant). Scope is explicitly **non-RTS esports genres**.
- §3.4.3 (line 147): `### 3.4.3 Recenzowana praca z pogranicza ekonomii obliczeniowej: Elbert i in. (2025)`. Elbert2025EC is AoE2-team-games prediction. AoE2 is RTS.

**Decision:** Leave Elbert2025EC in §3.4 (correct by genre; §3.3 is non-RTS-only by scope). Document the decision in prose so a reviewer asking "why isn't Elbert also in §3.3?" has the answer inline.

**Edit:**
- Insert the following sentence adjacent to the first Elbert introduction in §3.4.3 (the executor may choose line 148 or line 149 as insertion point and may refine wording while preserving intent and argument):
  > `§3.4 obejmuje literaturę predykcji w Age of Empires II; Elbert i in. [Elbert2025EC] dotyczą AoE2 w formacie drużynowym i mieszczą się w tym podrozdziale na podstawie tytułu gry, nie zaś liczby graczy. §3.3 obejmuje literaturę predykcji spoza AoE2 (MOBA: Dota 2, League of Legends; FPS: Counter-Strike, Valorant).`
- Note: the placement rationale is now grounded in game identity (AoE2), not RTS genre, avoiding the misreference to §3.4.1 (which covers CetinTas2023 on AoE2, not SC2).

**Gate:** after T04:
- `grep -c "lokow" thesis/chapters/03_related_work.md` increases by ≥ 1 (stem matches both `lokowani w §3.4` from the R5 sentence and `lokowana w §3.4` — covers the inserted placement-decision phrasing regardless of grammatical gender).
- `grep -c "§3.3" thesis/chapters/03_related_work.md` increases by ≥ 1.

### T05 — F5.6: Demsar §3.2 / §3.1.3 location uncertainty — flag-planting (swap deferred to Pass 2)

**Files:**
- `thesis/chapters/04_data_and_methodology.md` lines 375 and 377 (§4.4.4 — PRIMARY locus per audit H3; line 375 contains inline `§3.2 Demšara`, line 377 contains bibkey `[Demsar2006, §3.2]` for N ≥ 10)
- `thesis/chapters/04_data_and_methodology.md` line 213 (§4.1.4 — co-locus; contains `[Demsar2006, §3.2]` for N ≥ 10)
- `thesis/chapters/02_theoretical_background.md` line 211 (§2.6.3 — contains "§3.2, adresującego inne zastosowanie")

**Empirical anchor (to verify during T05 execution):**
- `grep -En "Demsar2006.*§3\.2|Demsar2006, §3\.2" thesis/chapters/04_data_and_methodology.md` — expected matches at §4.4.4 line 377 (bibkey, PRIMARY) and §4.1.4 line 213 (co-locus). Line 373 already reads `[Demsar2006, §3.1.3]` (fixed in TG1) — DO NOT touch line 373.
- `grep -n "§3\.2 Demšara" thesis/chapters/04_data_and_methodology.md` — expected match at §4.4.4 line 375 (inline form, PRIMARY co-locus).
- `grep -n "§3\.2" thesis/chapters/02_theoretical_background.md` — expected ≥ 1 match at §2.6.3 line 211.
- Audit F5.6 and H3 (line 309 of `thesis/reviews_and_others/pass2_dispatch.md`): "§4.4.4 cites Demsar §3.2 corollary; actual reference for N ≥ 10 is §3.1.3." — §4.4.4 is the **primary** locus; §4.1.4 is a co-locus. The swap itself is unverified against a readable PDF; this task plants flags only — the §3.2 text is left in place at all four loci.

**Flag text (to append after each existing citation at all four loci):**
> `[REVIEW: F5.6 Pass-2 audit H3 claims $N \geq 10$ threshold is in Demšar 2006 §3.1.3, not §3.2; manual verification against readable PDF required — Pass 2 closes this flag.]`

**Edit 1 — flag-planting at `04_data_and_methodology.md` §4.4.4 lines 375 + 377 (PRIMARY locus):**
- Line 377: DO NOT replace bibkey `[Demsar2006, §3.2]`. Append the flag text immediately after the citation on the same line or as a sentence-end insertion.
- Line 375: DO NOT replace inline `§3.2 Demšara`. Append the flag text adjacent to the inline reference.
- Line 373 already reads `[Demsar2006, §3.1.3]` (fixed in TG1) — explicitly do NOT modify line 373.

**Edit 1b — flag-planting at `04_data_and_methodology.md` line 213 (§4.1.4, co-locus):**
- Current: `są inaplikowalne per [Demsar2006, §3.2] (wymóg $N \geq 10$ zbiorów danych dla aproksymacji asymptotycznej)`
- DO NOT replace `§3.2`. Append the flag text after the parenthetical on the same line.

**Edit 2a — flag-planting at `02_theoretical_background.md` line 211 (§2.6.3):**
- Current excerpt contains: `z §3.2, adresującego inne zastosowanie testu Friedmana`
- DO NOT modify the existing sentence or swap `§3.2` to `§3.1.3`. Append the flag text after the sentence (same line or immediately following).
- Preserve the "adresującego inne zastosowanie" and the N ≥ 5 vs N ≥ 10 structural contrast intact — the contrastive clause is load-bearing for the §2.6.4 cross-game N=2 defence.

**Gate:** after T05:
- `grep -c "Demsar2006, §3\.2" thesis/chapters/04_data_and_methodology.md` remains ≥ 3 (swap NOT performed; existing `§3.2` citations retained at lines 377 and 213, plus any other occurrences).
- `grep -c "audit H3" thesis/chapters/02_theoretical_background.md thesis/chapters/04_data_and_methodology.md` returns ≥ 4 (one flag per each of the four loci: §4.4.4 line 375, §4.4.4 line 377, §4.1.4 line 213, §2.6.3 line 211).
- `grep "adresującego inne zastosowanie" thesis/chapters/02_theoretical_background.md` returns ≥ 1 (contrastive clause preserved, not swapped away).
- `grep "§3\.1\.3" thesis/chapters/04_data_and_methodology.md | grep -v "^373:"` does NOT introduce new `§3.1.3` occurrences beyond line 373 (confirms the swap was not performed).

### T06 — WRITING_STATUS.md + REVIEW_QUEUE.md section-row annotations

**Files:**
- `thesis/WRITING_STATUS.md` (Chapter 2 §2.2 row, §2.5 row, §2.6 row; Chapter 3 §3.4 row; Chapter 4 §4.4.4 row and §4.1.4 row if that row also exists and was touched)
- `thesis/chapters/REVIEW_QUEUE.md` (matching section rows; §4.1.4 row already exists)

**Pre-flight (before editing):**
- Run `grep "§4.1.4" thesis/WRITING_STATUS.md` to verify the §4.1.4 row exists before modifying it.
- Run `grep "§4.4.4" thesis/WRITING_STATUS.md` to confirm the §4.4.4 row location (audit-named primary locus for F5.6).

**Edit pattern — append a short `**2026-04-20 (PR-TG5a):**` annotation on the Notes/Pass-2-status column for each affected row:**
- §2.2 row: F5.3 Edit 1 (§2.2.3 line 39 Aligulac 80% reframed to calibration-not-accuracy; new [REVIEW] flag planted; F4.5 reframing consolidated here per TG5-PR-5a).
- §2.5 row: F5.3 Edit 2 (§2.5.5 line 183 Aligulac [REVIEW] flag reworded to align with §2.2.3; F4.5 framing cross-referenced).
- §2.6 row: F5.6 Edit 2a (§2.6.3 line 211 — [REVIEW: audit H3] flag planted adjacent to existing §3.2 citation; swap deferred to post-Pass-2 PR).
- §3.4 row: F5.5 Edit (§3.4.3 cross-reference sentence added documenting Elbert2025EC placement logic by game identity, not RTS genre).
- §4.4.4 row (PRIMARY for F5.6): F5.6 Edit 1 (§4.4.4 lines 375 + 377 — [REVIEW: audit H3] flags planted; §3.2 text retained pending PDF verification of §3.1.3 location).
- §4.1.4 row (co-locus for F5.6): if the §4.1.4 row exists in WRITING_STATUS (verify via pre-flight grep above), append `**2026-04-20 (PR-TG5a):** F5.6 co-locus — line 213 [REVIEW: audit H3] flag planted; §3.2 citation retained pending PDF verification.`
- §1.1 row: F5.1 (flag count refresh) — **already handled in T01**; do not duplicate.

**Gate:** after T06, every WRITING_STATUS row for an edited section carries a `(PR-TG5a)` annotation; REVIEW_QUEUE Pending table mirrors the annotations where applicable.

## 3. Execution order and gates

1. **T01** — F5.1 WRITING_STATUS + REVIEW_QUEUE §1.1 (metadata only; no chapter edits).
2. **T02** — F5.2 THESIS_STRUCTURE.md line 67 (metadata only).
3. **T03** — F5.3 §2.2.3 + §2.5.5 Aligulac reframing (chapter prose — the largest delta of this PR).
4. **T04** — F5.5 §3.4.3 Elbert placement sentence (chapter prose).
5. **T05** — F5.6 §4.4.4 (primary) + §4.1.4 (co-locus) + §2.6.3 Demsar flag-planting (chapter prose; swap deferred to Pass 2).
6. **T06** — WRITING_STATUS + REVIEW_QUEUE section-row annotations for every chapter touched by T03–T05.
7. **Final gate**: all T0x gates pass; `git diff --stat` touches exactly the files listed in §5.

## 4. Rollback plan

- Each task is a pure prose edit; revert by `git checkout HEAD~1 -- <file>` at the file granularity. The entire PR can be reverted post-merge via `git revert <merge-sha>`.
- No database writes, no artifact regeneration, no phase-status changes, no `src/` or `tests/` touches, no dependency updates.

## File Manifest

(See §5 File manifest below for full table.)

## 5. File manifest

| File | Change type | Source finding |
|------|-------------|----------------|
| `thesis/WRITING_STATUS.md` | notes-column appends (§1.1, §2.2, §2.5, §2.6, §3.4, §4.4.4, §4.1.4 if exists) | F5.1, F5.3, F5.5, F5.6 |
| `thesis/chapters/REVIEW_QUEUE.md` | §1.1 row update (Flag count 0→2+2) + notes appends to §2.2 / §2.5 / §2.6 / §3.4 / §4.4.4 / §4.1.4 rows | F5.1, F5.3, F5.5, F5.6 |
| `thesis/THESIS_STRUCTURE.md` | line 67 rewrite | F5.2 |
| `thesis/chapters/02_theoretical_background.md` | prose edits + flag rewrites at lines 39, 183, 211 | F5.3, F5.6 |
| `thesis/chapters/03_related_work.md` | single-sentence insertion at §3.4.3 | F5.5 |
| `thesis/chapters/04_data_and_methodology.md` | [REVIEW] flag-planting at §4.4.4 lines 375+377 (primary) and §4.1.4 line 213 (co-locus); §3.2 text retained | F5.6 |

Total: 6 files. No changes to `thesis/chapters/01_introduction.md` prose; no changes to `thesis/references.bib`.

## 6. Open questions for planner / reviewer

None load-bearing for chore-scope. One contingent item for the executor to handle inline:
1. If T03 Edit 3 grep surfaces a 80% mention in §2.5.4 prose (not expected — pre-check returned none), apply the same Edit 1 framing.
Note: §4.4.4 is the **mandatory** primary locus for T05 Edit 1 (not contingent). The executor must plant the flag at §4.4.4 lines 375+377 regardless of what the grep returns; the §3.2 text must NOT be swapped.

## 7. Semver + changelog

- Version bump: `3.33.0 → 3.34.0` (minor, per docs-branch convention established in PR #187–#190).
- CHANGELOG.md entry under `[3.34.0] — 2026-04-20 (PR #N: docs/thesis-pass2-tg5a-internal-consistency-chore)` enumerating F5.1 / F5.2 / F5.3 / F5.5 / F5.6 and noting F5.4 deferred to PR-5b.

## 8. PR wrap-up checklist

- [ ] All T01–T06 gates pass.
- [ ] `pyproject.toml` version bumped to `3.34.0`.
- [ ] `CHANGELOG.md` entry added and `[Unreleased]` reset with empty headers.
- [ ] PR body drafted at `.github/tmp/pr.txt` via `Write` tool (not heredoc).
- [ ] Commit message via `.github/tmp/commit.txt`, then `git commit -F .github/tmp/commit.txt`.
- [ ] After PR creation: delete `.github/tmp/pr.txt` + `.github/tmp/commit.txt`.
