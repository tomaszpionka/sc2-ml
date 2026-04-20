---
category: F
branch: docs/thesis-pass2-tg3-luka3-narrowing
date: 2026-04-20
planner_model: claude-opus-4-7
dataset: null
phase: null
pipeline_section: "Phase 01 — Data Exploration (thesis-writing adaptation)"
invariants_touched: []
source_artifacts:
  - thesis/chapters/01_introduction.md
  - thesis/chapters/02_theoretical_background.md
  - thesis/chapters/03_related_work.md
  - thesis/references.bib
  - thesis/WRITING_STATUS.md
  - thesis/chapters/REVIEW_QUEUE.md
  - thesis/reviews_and_others/related_work_rating_systems.md
  - .claude/author-style-brief-pl.md
  - .claude/scientific-invariants.md
  - .claude/rules/thesis-writing.md
critique_required: true
research_log_ref: "thesis/WRITING_STATUS.md (PR-TG3 notes)"
---

# Plan: Pass-2 TG3 — Luka 3 narrowing against Thorrez 2024 EsportsBench (§3.5 + §3.2.4 + §1.3/§2.5.5 coordination)

## Scope

This is a **revision** of previously-DRAFTED sections (§1.3, §2.5.5, §3.2.4, §3.5). No figures, tables, or bibkeys are created; `thesis/references.bib` is not touched (the `Thorrez2024` bibkey stays; only the surrounding prose is re-scoped).

This plan executes Task Group 3 of the Pass-2 dispatch. It narrows the Luka 3 novelty claim (§3.5) so it argues — rather than hedges — against the adversarial reading that Thorrez 2024 EsportsBench already covers the same contribution. The narrowing operates via a three-site edit: (Part 1) rewrite §3.5 Luka 3 to explicitly acknowledge EsportsBench, enumerate four operative disqualifying constraints (ML-classifier family / SC2+AoE2 / proper probabilistic evaluation with calibration diagnostics / 1v1), and anchor the narrowing against a verified fact (EsportsBench covers SC1/SC2/WC3 for the RTS genre but does **not** include AoE2); (Part 2) re-scope the §3.2.4 EsportsBench mention to match what the benchmark actually is (rating-systems benchmark, per-game fit); (Part 3) correct two Thorrez2024 miscitations in §1.3 RQ1 hypothesis and §2.5.5 hybrid-strategy claim that currently attribute ML-classifier findings to a pure-rating-system benchmark. The plan produces one PR (PR-3) and defers TG4–TG6 to sequential follow-up plans per the dispatch's halt-and-review protocol. No empirical artifacts are touched; work is prose-only across three chapter files and the two tracker files (WRITING_STATUS.md, REVIEW_QUEUE.md).

## Problem Statement

The three findings operate at the same adversarial surface — correct citation of what Thorrez 2024 EsportsBench does and does not benchmark — and must be resolved together to avoid introducing a new contradiction between a narrowed §3.5 and an unedited §1.3 / §2.5.5.

**Finding 1 — §3.5 Luka 3 over-hedge rather than argument.** `03_related_work.md:187` currently asserts: *"przedmiot niniejszej pracy stanowi, zgodnie z najlepszą dostępną wiedzą autorów, pierwszą znaną nam pracę porównującą rodzinę klasyfikatorów uczenia maszynowego w zadaniu benchmarkowania metod predykcji wyniku meczu między dwiema grami RTS z jawną oceną probabilistyczną w grach 1v1"*. The sentence hedges ("pierwsza znana nam") but does not argue against the nearest-adjacent published benchmark. An examiner familiar with Thorrez 2024 EsportsBench — which benchmarks 11 paired-comparison rating systems across 20 esports titles including SC1, SC2 and WC3 (three RTS titles) — could dispute the claim without the thesis providing an argued response. The author-style brief (`§Przejście z opisowego na argumentacyjne`) requires that each methodological decision carry at least one sentence answering *"dlaczego to, a nie oczywista alternatywa?"*; Luka 3 currently fails this bar because it does not say why EsportsBench does not fill the same space.

**Finding 2 — §3.2.4 EsportsBench characterization.** `03_related_work.md:77` introduces EsportsBench as *"jednym z nielicznych źródeł raportujących trafność czysto rankingową na korpusie SC2 (411 030 meczów z Aligulac), na poziomie około 80% dla najlepszych systemów rodziny Glicko"*. This description is accurate for the pre-match vs in-match dimension (Luka 1's direction). It must be supplemented — not replaced — with a sentence identifying three facts that Part 1 depends on: (a) EsportsBench benchmarks pure rating systems (Elo / Glicko / Glicko-2 / TrueSkill / Bradley-Terry variants), not ML-classifier families; (b) the evaluation protocol is per-game fit with chronological train/test split (most recent year as test), not cross-game transfer; (c) AoE2 is absent from EsportsBench's title list (20 titles, none of which is AoE2, verified against the HuggingFace dataset README version 8.0). The `[REVIEW: 80,13%]` flag is either resolved by substituting an explicit verification date or demoted to qualitative hedging; the plan carries the conservative option (qualitative hedge) and leaves the exact-number verification as Pass 2 work.

**Finding 3 — two §1.3 / §2.5.5 miscitations that would become externally visible once §3.5 is narrowed.** `01_introduction.md:31` (RQ1 hypothesis) currently couples `[Thorrez2024]` with the claim that gradient-boosted trees dominate other classical classifiers in esports prediction: *"hipoteza: … można oczekiwać, że gradientowo wzmacniane drzewa decyzyjne osiągną przewagę nad pozostałymi klasyfikatorami klasycznymi, zgodnie z wynikami Hodge i in. [Hodge2021] dla Dota 2 oraz powtarzalnym wzorcem obserwowanym w predykcji esportowej [Thorrez2024]"*. EsportsBench does not benchmark gradient-boosted trees vs classical classifiers; it benchmarks pure rating systems only. The load-bearing citation for "powtarzalny wzorzec" should be either Hodge2021 alone (where GBDT dominance is directly evidenced on Dota 2), Tang2025 (already cited at the same sentence, argues for 2–5 pp ML uplift over tuned rating baselines), or both. `[Thorrez2024]` does not support the claim. `02_theoretical_background.md:181` (§2.5.5) has the analogous miscitation: *"Hybrydowa strategia łącząca rankingi z gradientowo wzmacnianymi drzewami pozostaje obecnie najlepiej udokumentowaną kombinacją w literaturze predykcji esportowej, zarówno pod względem skuteczności, jak i interpretowalności [Hodge2021, Thorrez2024]"* — Thorrez2024 does not benchmark hybrid rating+GBDT pipelines. The correct citation is Hodge2021 alone. Both miscitations would become externally visible once Part 1 narrowed §3.5 makes it clear that EsportsBench benchmarks rating systems, not ML classifiers; TG3 resolves them pre-emptively in the same PR to avoid shipping a new contradiction.

**Target end-state.** After execution: (i) §3.5 Luka 3 argues against EsportsBench via four operative constraints (ML-classifier family / SC2+AoE2 specifically / proper probabilistic evaluation with calibration / 1v1) and anchors the narrowing on the verified EsportsBench title list (AoE2 absent, SC1+SC2+WC3 present as RTS titles); (ii) §3.2.4 EsportsBench mention is supplemented with a sentence identifying its scope (pure rating systems, per-game fit, AoE2 absence); (iii) §1.3 RQ1 hypothesis citation drops `Thorrez2024` from the GBDT-dominance claim (Hodge2021 + Tang2025 retained); (iv) §2.5.5 hybrid-strategy claim drops `Thorrez2024` (Hodge2021 retained; empirical support is on Dota 2 GBDT, not EsportsBench). The `REVIEW_QUEUE.md:22` Pass 2 question 2 on §1.3 (verify Thorrez2024 cross-system comparability) is resolved (answer: per-system fit only). The `REVIEW_QUEUE.md:40` §3.5 `[REVIEW: RQ3 novelty hedge]` question 1 is resolved (answer: adversarial reading against EsportsBench is neutralized by the four-constraint narrowing). No empirical artifacts are touched. No new bibkeys are introduced. No bibliography entries are modified (TG4 scope). The exact 80.13% SC2 Glicko figure remains qualitative ("~80% kalibracji do progu") pending Pass 2 manual PDF read (unchanged from current state).

## Assumptions & unknowns

### Pre-flight facts (verified 2026-04-20 via Read/Grep/WebSearch/WebFetch)

- §3.5 Luka 3 is at `03_related_work.md:187` (paragraph 4 of §3.5). Verified via Read of lines 179–189.
- §3.2.4 "Po pierwsze" paragraph with the EsportsBench mention is at `03_related_work.md:77`. Verified via Read.
- §1.3 RQ1 hypothesis with the `Thorrez2024` citation is at `01_introduction.md:31`. Verified via Read.
- §2.5.5 hybrid-strategy claim with `[Hodge2021, Thorrez2024]` is at `02_theoretical_background.md:181`. Verified via Read.
- Thorrez2024 bibkey exists at `references.bib:147–152` as `@misc{Thorrez2024, author = {Thorrez, Lucas}, ...}`. Note: author name is "Lucas Thorrez" in the bibkey; HuggingFace and cthorrez.github.io both identify the author as "Clayton Thorrez". This is a TG4 concern (bibliography fix) — NOT fixed in TG3 to preserve one-PR-per-task-group discipline; TG3 prose retains the existing `[Thorrez2024]` citation key without touching the bib entry.
- EsportsBench title list (20 titles) verified via HuggingFace dataset README (v8.0, 2025-12-31) and GitHub repo README: League of Legends, Counter-Strike, Rocket League, StarCraft I, StarCraft II, Smash Melee/Ultimate, Dota 2, Overwatch, Valorant, Warcraft III, Rainbow Six, Halo, Call of Duty, Tetris, Street Fighter, Tekken, King of Fighters, Guilty Gear, EA Sports FC.
- Age of Empires II is **absent** from EsportsBench (verified by grep of visible title list; no `aoe2.csv` or `age_of_empires*.csv` file exists in the HuggingFace repo).
- EsportsBench benchmark type: pure rating systems (Elo baseline; additional Glicko/Glicko-2/TrueSkill/BT variants), not ML classifiers. Verified via HuggingFace README *"The goal of the datasets is to provide a resource for comparison and development of rating systems used to predict the results of esports matches"* and via GitHub README *"The baseline is the Elo rating system"*.
- EsportsBench evaluation protocol: chronological train/test split with most-recent-year holdout; per-game fit; match-level prediction on a date-batched loop. Verified via HuggingFace README.
- SC2 row count in EsportsBench: 463,000 rows as of v8.0 (HuggingFace dataset viewer). Note: the existing thesis text cites "411 030 meczów z Aligulac" which is the v1.0 (2024-03-31) figure. The discrepancy (v1.0 → v8.0 growth) does not invalidate the thesis claim because the `[Thorrez2024]` citation refers to the 2024 preprint, which used the v1.0 data. Keep "411 030" as the version-consistent number.
- AoE2 absence from EsportsBench verified by absolute comparison: the thesis's AoE2 corpus size is 1,261,288 rows (Lin2024NCT) or ~620,000–2,400,000 rows (aoestats). If AoE2 had been in EsportsBench, the TMLR paper (Lin2024NCT) would almost certainly have cited it. The absence is structural.
- REVIEW_QUEUE.md:22 carries Pass 2 question 2 on §1.3 — *"RQ1 hypothesis on GBDT dominance in two-game cross comparison — verify Thorrez2024 EsportsBench reports cross-system comparability beyond per-system fit"*. Verified via Read. Answer is now known: EsportsBench reports per-system fit only; no cross-system transfer comparison.
- REVIEW_QUEUE.md:40 carries the §3.5 `[REVIEW:]` flag on the Luka 3 novelty hedge. Verified via Read.
- The author-style brief requires argumentation-in-place for methodological decisions (`§Przejście z opisowego na argumentacyjne`, `§Instrukcje operacyjne dla Claude Code` bullet "Argumentacja decyzyjna w miejscu decyzji"). TG3's narrowing substitutes argued disqualification for hedged silence.
- The "ISO YYYY-MM-DD dates; em-dash "—" for ranges" lesson from TG1/TG2 applies: any date-range reference (e.g., "EsportsBench v1.0 data up to 2024-03-31" or "v8.0 2025-12-31") uses the ISO format and the em-dash for ranges if used. Polish month names are forbidden in dates.

### Assumptions

- **Assumption (principle, unstated in dispatch):** the 3-part edit covers `§3.5 + §3.2.4 + (§1.3 RQ1 hypothesis coupled with §2.5.5 hybrid claim)`. Rationale: both §1.3 and §2.5.5 carry the same Thorrez2024 miscitation pattern (attributing ML-classifier dominance to a rating-systems benchmark), so fixing them in one pass preserves the "no new contradictions" principle from TG2. If the user's dispatch master intended §3.5-internal-only or a different Part 3 target, the plan narrows (see Open Q 1). Decision in Part 3 is to handle both §1.3 and §2.5.5 inside a single Task T02 to preserve atomic-edit commit discipline.
- **Assumption (EsportsBench v8.0 validity):** AoE2 remains absent in the most recent HuggingFace release (v8.0, 2025-12-31). Verified as of 2026-04-20. If the user's Pass-2 dispatch master references a different version or has an updated understanding, the plan should be re-run.
- **Unknown — deferred:** whether the `Thorrez2024` bibkey's author name ("Lucas") is a thesis-internal typo vs a published-by-pen-name. The author's web profile self-identifies as Clayton Thorrez. This is explicitly out-of-scope for TG3 (TG4 territory) and the plan does not modify the bib entry. Flagged for TG4 as a new finding.
- **Unknown — resolved by reviewer-adversarial Mode A:** whether the four-constraint narrowing (ML-classifier family / SC2+AoE2 / proper probabilistic evaluation / 1v1) is genuinely operative, or whether it re-commits the novelty claim at a lower abstraction that still overstates. Decision in plan: present the constraints as *jointly* required (logical conjunction); if any single constraint is relaxed, existing literature fills the gap. reviewer-adversarial Mode A validates the conjunction is tight.
- **Unknown — resolved by reviewer-adversarial Mode A:** whether the `[REVIEW: RQ3 novelty hedge]` flag should be removed (resolved) or replaced with a reduced-scope flag. Decision in plan: **replace** with a reduced-scope flag covering one residual uncertainty (whether EsportsBench has added AoE2 in any future release post-v8.0 that the thesis cannot anticipate). This matches TG2's pattern of resolving the load-bearing question while keeping a narrower flag for future-release monitoring.

## Literature context

- [Thorrez2024] — EsportsBench, preprint 2024. 20 esports datasets, paired-comparison rating system benchmark. Chronological train/test split. Per-game fit. No ML classifier benchmarking. SC2 present (463k rows as of v8.0; 411,030 rows as of v1.0 cited in the preprint); **AoE2 absent**. The HuggingFace README describes EsportsBench as benchmarking rating systems via accuracy and log-loss; full preprint metric set not verified in this plan round (binary PDF). Aligulac SC2 result ~80% predicted-win-probability calibration.
- [Hodge2021] — IEEE Transactions on Games. LightGBM on Dota 2 pre-match + in-match features, ~85% accuracy at 5-minute mark. Direct ML-classifier benchmark with peer-reviewed venue. This is the correct citation for the GBDT-dominance claim previously co-attributed to Thorrez2024.
- [Tang2025] — Typical ML uplift 2–5 pp over well-tuned rating baselines across chess/tennis/football/esports. Already co-cited with Thorrez2024 at §1.3 RQ1 hypothesis; stays.
- [Lin2024NCT] — Uses AoE2 (1,261,288 matches from aoestats.io) as one of four titles for intransitivity analysis, but not as a prediction benchmark. Already cited in §3.4.2 and §3.5; relevant here because it is the load-bearing "AoE2 has 1.2M matches" observation that anchors the "AoE2 corpus size would have been visible to EsportsBench authors" implicit argument (not cited in Part 1's prose; referenced only in the plan's rationale for the AoE2-absence-is-structural claim).
- [Bialecki2023], [Bialecki2022] — SC2EGSet + SC2 determinants. Pre-existing citations, not touched by TG3.
- [OPINION] — The combined argumentative approach (narrowing against EsportsBench via operative disqualifying constraints) is consistent with the scoping rigor that TG1 introduced for triptych framing and TG2 introduced for civilization count. No external citation is claimed for this methodological pattern itself.

## Pre-flight (branch-creation operation, not a numbered task)

Note on plan provenance: this plan body is authored in a planning session (Claude Code opusplan) and applied to the working tree by the human before the seed commit fires. The pre-flight commits encode that tree state onto the new branch; they are not self-generated by the plan.

Per git-workflow atomicity, the branch-creation purge is split into two commits before any content work begins:

- **Commit A** — `chore(planning): purge artifacts from merged PR #188 (TG2)` — deletes the TG2 `planning/current_plan.md` + `planning/current_plan.critique.md` that are inherited from master after the TG2 merge.
- **Commit B** — `chore(planning): seed TG3 plan (Luka 3 narrowing against Thorrez 2024 EsportsBench)` — writes this TG3 plan to `planning/current_plan.md`.
- **Commit C** — `chore(planning): seed TG3 plan critique (reviewer-adversarial Mode A)` — writes `planning/current_plan.critique.md` after Mode A runs.

These commits are not part of the Execution Steps DAG; they establish the planning state before T01 begins.

## Execution Steps

For shared tracker files (`WRITING_STATUS.md`, `REVIEW_QUEUE.md`), each task appends row notes only to rows it owns (per File Manifest attribution). Task sequencing T01 → T02 → T03 guarantees no concurrent tracker write. Writer-thesis must re-read the tracker file immediately before each edit.

### T01 — Rewrite §3.5 Luka 3 paragraph + update §3.2.4 EsportsBench characterization (Parts 1+2)

**Objective:** substitute the current §3.5 Luka 3 hedge-only novelty claim with a four-constraint argued narrowing against Thorrez 2024 EsportsBench, anchored on the verified fact that EsportsBench covers SC1/SC2/WC3 for the RTS genre but does not include AoE2. Simultaneously, supplement §3.2.4 "Po pierwsze" paragraph so its EsportsBench characterization supports the narrowing in §3.5 (rating-systems benchmark, per-game fit, AoE2 absence).

**Instructions:**
1. Read `thesis/chapters/03_related_work.md` lines 73–84 (§3.2.4 full subsection) and lines 179–192 (§3.5 full subsection) to confirm the exact current prose before rewriting.
2. **Part 2 first (§3.2.4 supplementation, `03_related_work.md:77`).** In the "Po pierwsze" paragraph, after the existing sentence *"EsportsBench [Thorrez2024], cytowany już w §2.5, jest jednym z nielicznych źródeł raportujących trafność czysto rankingową na korpusie SC2 (411 030 meczów z Aligulac), na poziomie około 80% dla najlepszych systemów rodziny Glicko."*, insert one supplementary sentence: *"Należy jednak doprecyzować zakres tego benchmarku: EsportsBench jest benchmarkiem rodziny paired-comparison rating systems (m.in. Elo, Glicko, Glicko-2, TrueSkill) oceniającym je w protokole per-gra z temporalnym podziałem ostatniego roku jako zbioru testowego, a nie benchmarkiem porównującym rodziny klasyfikatorów uczenia maszynowego; spośród 20 tytułów EsportsBench obejmuje StarCrafta I, StarCrafta II i Warcrafta III jako reprezentację RTS, ale nie obejmuje Age of Empires II."* Preserve the existing `[REVIEW: dokładna wartość 80,13%]` flag unchanged — it remains a valid Pass 2 verification item pending manual PDF read. The rest of the paragraph is untouched.
3. **Part 1 next (§3.5 Luka 3 rewrite, `03_related_work.md:187`).** Replace the current Luka 3 paragraph (from *"**Luka 3 — brak porównawczego benchmarku…"* through the trailing `[REVIEW:]` flag) with a rewritten paragraph containing five argumentative moves in this order: (a) restate Luka 3 title identically (*"Luka 3 — brak porównawczego benchmarku predykcji wyniku między dwoma grami RTS z jawną oceną probabilistyczną (RQ3)"*); (b) name EsportsBench explicitly as the nearest-adjacent published benchmark that could be read as filling the same space, citing `[Thorrez2024]` and cross-referencing §3.2.4; (c) enumerate in one flowing sentence the four operative constraints that must hold jointly for Luka 3 to remain an open gap — a rodzina klasyfikatorów ML (logistic regression / random forest / GBDT / MLP), nie rodzina pure-rating-systems (Elo/Glicko/TrueSkill); struktura porównawcza między dwoma tytułami RTS w ramach jednego projektu badawczego (cross-game benchmarking), a nie niezależne dopasowanie per-grę — EsportsBench wykonuje per-gra fit osobno dla każdego z 20 tytułów (w tym SC1, SC2 i WC3 dla gatunku RTS), lecz nie raportuje cross-game benchmarkingu; dodatkowo AoE2 nie występuje w zbiorze EsportsBench w żadnej wersji wydanej do 2025-12-31; diagnostyka kalibracyjna probabilistyczna (diagramy rzetelności i dekompozycja Murphy'ego) jako integralna część protokołu ewaluacji — publicznie dostępna dokumentacja EsportsBench (HuggingFace dataset README v8.0 2025-12-31 oraz README repozytorium GitHub) nie wymienia diagramów rzetelności ani dekompozycji Murphy'ego wśród opisanych metryk benchmarku; integralność tych miar w protokole ewaluacyjnym EsportsBench pozostaje niezweryfikowana w ramach niniejszej pracy pending manualnej analizy preprintu (Table 2); zakres 1v1 z identyczną strukturą zadania między grami; (d) re-retain the existing Lin2024NCT / Elbert2025EC / CetinTas2023 disqualifications from the current paragraph (each with its current argumentative function preserved); (e) close with a reduced-scope hedge that replaces the current "pierwsza znana nam" hedge: *"W przestrzeni wyznaczonej koniunkcją tych czterech ograniczeń przedmiot niniejszej pracy stanowi — zgodnie z najlepszą dostępną wiedzą autorów i po bezpośredniej weryfikacji składu tytułów EsportsBench w wersji v8.0 (2025-12-31) — konfigurację badawczą, w której literatura recenzowana nie jest obecna."* Plant one reduced-scope `[REVIEW:]` flag covering residual uncertainty: *"[REVIEW: narrowing przeciwko EsportsBench — zweryfikować w Pass 2, czy żadna wersja EsportsBench nowsza niż v8.0 2025-12-31 nie dodała Age of Empires II lub nie rozszerzyła protokołu o benchmark rodzin klasyfikatorów ML; obecne twierdzenie o lukcie jest argumentowane przez koniunkcję czterech ograniczeń, nie przez hedging pozbawiony argumentacji; dodatkowo: weryfikować Table 2 preprintu Thorrez 2024 pod kątem raportowania diagramów rzetelności, dekompozycji Murphy'ego lub Brier score — jeśli obecne, constraint (c) wymaga przepisania."* Remove the original `[REVIEW: RQ3 novelty hedge — weryfikacja po opublikowaniu Chapter 3 w Claude Chat Pass 2; sformułowanie "pierwsza znana nam"…]` flag as resolved.
4. Verify that the closing paragraph of §3.5 ("Zestawiając cztery luki…" at `03_related_work.md:191`) still parses correctly with the narrowed Luka 3: the paragraph references *"porównanie międzygrowe jako celowo utrzymana asymetria"* and does not directly cite EsportsBench or Thorrez2024, so no edit is required in §3.5 closing prose.
5. Run the writer-thesis Critical Review Checklist (Literature variant, `.claude/rules/thesis-writing.md` §Critical Review Checklist → Literature variant):
   - Citation accuracy: every claim about EsportsBench reflects its documented behaviour.
   - Claim-citation alignment: each Luka 3 disqualification (EsportsBench / Lin2024NCT / Elbert2025EC / CetinTas2023) is backed by the existing citation for that paper.
   - Coverage completeness: Luka 3 now references EsportsBench, which the pre-TG3 version did not.
   - Critical evaluation: argumentative (four-constraint conjunction), not descriptive.
   - Scope honesty: the residual hedge is reduced to future-release monitoring; no absolute-novelty claim.
   - Missing context flags: one reduced-scope `[REVIEW:]` flag planted per (c).
6. Verify all ISO YYYY-MM-DD date formatting and em-dash use in the rewritten prose. The dates "v8.0 (2025-12-31)" and "v1.0 (2024-03-31)" must use this exact format; no Polish month names; em-dash where range is implied.

**Verification:**
- `grep -nF "pierwszą znaną nam" thesis/chapters/03_related_work.md` returns zero hits (the hedge-only phrasing is removed from §3.5).
- `grep -nF "EsportsBench" thesis/chapters/03_related_work.md` returns hits at `:77` (existing mention), `:77+1` (new supplementary sentence inside the same paragraph, verify as one logical hit), and at the rewritten §3.5 Luka 3 paragraph (new).
- `grep -nF "Age of Empires II" thesis/chapters/03_related_work.md` returns at least one new hit inside §3.2.4 (the "nie obejmuje Age of Empires II" disqualification) and inside §3.5 Luka 3 (the "AoE2 nie występuje w zbiorze 20 tytułów EsportsBench" operative constraint).
- `grep -nE "StarCraft.{0,3}[Ii]\\b|Warcraft.{0,3}III" thesis/chapters/03_related_work.md` returns at least one new hit at §3.2.4 (the RTS-titles enumeration in the supplementary sentence).
- `grep -nF "2025-12-31" thesis/chapters/03_related_work.md` returns exactly one new hit (the EsportsBench v8.0 anchor date).
- Word-boundary search `grep -nE "\\bREVIEW: RQ3 novelty hedge\\b" thesis/chapters/03_related_work.md` returns zero hits (the old flag is gone).
- Word-boundary search `grep -nE "\\bREVIEW: narrowing przeciwko EsportsBench\\b" thesis/chapters/03_related_work.md` returns exactly one new hit.

**File scope:**
- `thesis/chapters/03_related_work.md`

**Read scope:**
- (none — Parts 1 and 2 edit a single file)

---

### T02 — Remove Thorrez2024 miscitations from §1.3 RQ1 hypothesis and §2.5.5 hybrid-strategy claim (Part 3)

**Objective:** correct two miscitations that couple `[Thorrez2024]` with ML-classifier claims. EsportsBench does not benchmark ML classifiers; the citation is load-bearing elsewhere but not at these two sites. The correction is surgical: remove `Thorrez2024` from the citation list at each site; retain the other citations (Hodge2021 at both; Tang2025 at §1.3; both these sources directly support the ML-classifier claims). This edit must ship in the same PR as T01 to avoid shipping a new contradiction between the (narrowed) §3.5 and the (unedited) §1.3 + §2.5.5.

**Instructions:**
1. Read `thesis/chapters/01_introduction.md` lines 29–33 (§1.3 RQ1 hypothesis) and `thesis/chapters/02_theoretical_background.md` lines 179–184 (§2.5.5 closing paragraph) to confirm the exact current prose.
2. **§1.3 RQ1 hypothesis (`01_introduction.md:31`).** Surgical deletion to avoid Tang2025 doubling (Open Q 3 resolution: the existing later-sentence Tang2025 caveat is load-bearing and reads well — preserve it; remove only the miscited Thorrez2024 phrase). Locate the exact phrase *"oraz powtarzalnym wzorcem obserwowanym w predykcji esportowej [Thorrez2024]"* and delete it together with its connective *" oraz "* (the leading " oraz " conjunction that previously linked Hodge2021 and Thorrez2024 — after deletion, the Hodge2021 clause stands alone). The preceding Hodge2021 citation remains. The subsequent text *"; należy jednak zaznaczyć, że — jak wykazali Tang, Wang i Jin [Tang2025] — typowy przyrost trafności klasyfikatora ML nad dobrze nastrojoną linią bazową rankingową wynosi jedynie 2–5 punktów procentowych, co czyni rzetelne dobranie linii bazowej rangą metodologicznie krytyczną."* is preserved verbatim. Result: the sentence reads *"zgodnie z wynikami Hodge i in. [Hodge2021] dla Dota 2; należy jednak zaznaczyć, że — jak wykazali Tang, Wang i Jin [Tang2025] — typowy przyrost…"* — one Hodge2021 citation, one Tang2025 citation, zero Thorrez2024 citations. This is the minimal-substance edit: the Thorrez2024 miscitation is excised; no new content is introduced; Tang2025's argumentative function (margin caveat) is unchanged.
3. **§2.5.5 hybrid-strategy claim (`02_theoretical_background.md:181`).** Locate the exact phrase *"Hybrydowa strategia łącząca rankingi z gradientowo wzmacnianymi drzewami pozostaje obecnie najlepiej udokumentowaną kombinacją w literaturze predykcji esportowej, zarówno pod względem skuteczności, jak i interpretowalności [Hodge2021, Thorrez2024]"*. Replace the citation bracket `[Hodge2021, Thorrez2024]` with `[Hodge2021]` only. The claim stands on the Hodge2021 Dota 2 evidence; EsportsBench does not benchmark hybrid rating+GBDT pipelines.
4. **Tighten §2.5.5 line 177 EsportsBench mention** (per iter-1 logical critique L-5). The current prose at `02_theoretical_background.md:177` reads *"EsportsBench [Thorrez2024] — referencyjny zbiór benchmarków obejmujący ponad 20 tytułów esportowych, w tym StarCraft II z 411 030 meczami pochodzącymi z Aligulac — potwierdza, że rankingi rodziny Elo, Glicko i TrueSkill są standardowo używane jako linie bazowe lub jako cechy wejściowe w bardziej zaawansowanych pipeline'ach uczenia maszynowego"*. The "cechy wejściowe w ML pipelines" sub-claim is not what EsportsBench demonstrates (EsportsBench benchmarks pure rating systems, not hybrid pipelines). Surgical tightening: replace the sub-clause "potwierdza, że rankingi rodziny Elo, Glicko i TrueSkill są standardowo używane jako linie bazowe lub jako cechy wejściowe w bardziej zaawansowanych pipeline'ach uczenia maszynowego" with "benchmarkuje rankingi paired-comparison rating systems (m.in. Elo, Glicko, Glicko-2, TrueSkill) na danych esportowych". This keeps the Thorrez2024 citation load-bearing correctly (EsportsBench-as-rating-systems-benchmark is verified) and removes the overclaim about downstream ML-pipeline use. The "linie bazowe lub cechy wejściowe w ML pipelines" framing can be reintroduced in a separate future edit with a correctly-supporting citation (e.g., Hodge2021 for GBDT+rating-features).
5. **Avoid collateral damage at §1.3 RQ4 and §3.5 paragraphs.** Verify that §1.3 RQ2/RQ3/RQ4 hypotheses and the §3.5 Luka 1/Luka 2/Luka 4 blocks do not cite Thorrez2024. Grep: `grep -nF "Thorrez2024" thesis/chapters/01_introduction.md thesis/chapters/02_theoretical_background.md thesis/chapters/03_related_work.md` should return the pre-edit baseline hits minus exactly two (the §1.3 RQ1 and §2.5.5 hybrid-strategy sites).
6. Run the writer-thesis Critical Review Checklist (Literature variant) on the two rewritten sites:
   - Citation accuracy: Hodge2021 directly evidences GBDT dominance on Dota 2 (peer-reviewed, IEEE Transactions on Games). Tang2025 directly evidences the 2–5 pp margin.
   - Claim-citation alignment: every claim now cites a source that literally supports it.
   - Scope honesty: margin-hedging preserved.

**Verification:**
- `grep -cF "Thorrez2024" thesis/chapters/01_introduction.md` decreases by exactly 1 (the §1.3 RQ1 hypothesis hit removed).
- `grep -cF "Thorrez2024" thesis/chapters/02_theoretical_background.md` decreases by exactly 1 (the §2.5.5 hybrid-strategy hit removed at line 181).
- `grep -nF "Hodge2021" thesis/chapters/02_theoretical_background.md:181` still returns a hit.
- `grep -nF "Thorrez2024" thesis/chapters/02_theoretical_background.md:177` still returns a hit (citation retained with tightened claim per T02 step 4).
- `grep -nF "Tang2025" thesis/chapters/01_introduction.md` returns at least two hits (one in the rewritten RQ1 sentence; one in the existing later-sentence citation).
- No doubled Tang2025 citation within the same sentence: `grep -nE "\\[Tang2025\\][^\\[]{0,200}\\[Tang2025\\]" thesis/chapters/01_introduction.md` returns zero multiline hits. (If multiline is needed: re-verify visually — macOS BSD grep does not support `-P`.)

**File scope:**
- `thesis/chapters/01_introduction.md`
- `thesis/chapters/02_theoretical_background.md`

**Read scope:**
- `thesis/chapters/03_related_work.md` (for T01 consistency check at line 77 and 187 — reviewer validates §3.5 narrowing references EsportsBench scope correctly, which requires reading T01's output)

---

### T03 — Update WRITING_STATUS.md and REVIEW_QUEUE.md tracker entries

**Objective:** record the TG3 revisions in the two trackers so the Pass 2 workflow state reflects the resolved flags.

**Instructions:**
1. **WRITING_STATUS.md.** Append PR-TG3 notes to the four affected sections in the same format as the TG1/TG2 entries:
   - §1.3 Research questions: append *"**2026-04-20 (PR-TG3): §1.3 RQ1 hypothesis citation corrected — `[Thorrez2024]` removed from the GBDT-dominance claim per Pass-2 TG3 dispatch (EsportsBench benchmarks rating systems, not ML classifiers); `[Hodge2021, Tang2025]` retained as the directly-supporting citations. REVIEW_QUEUE.md:22 Pass 2 question 2 resolved. Uwaga o zakresie hipotezy: usunięcie `[Thorrez2024]` zawęża bazę indukcyjną hipotezy RQ1 do pojedynczego wyniku Dota 2 (Hodge2021) wraz z caveatem marginesu (Tang2025); szersze twierdzenie o 'powtarzalnym wzorcu w predykcji esportowej' zostało usunięte jako nieposieżone przez właściwe źródło. Rozszerzenie bazy indukcyjnej o poprawnie cytowane cross-esport GBDT-dominance (np. Yang2017Dota dla Dota 2 fazy przedmeczowej lub analogicznych źródeł z MOBA/FPS) pozostaje otwartą kwestią Pass 2 — bez wpływu na poprawność korekty miscytatu w TG3."*
   - §2.5 Player skill rating systems: append *"**2026-04-20 (PR-TG3): §2.5.5 hybrid-strategy claim citation corrected — `Thorrez2024` removed from `[Hodge2021, Thorrez2024]` at line 181 per Pass-2 TG3 dispatch (EsportsBench does not benchmark hybrid rating+GBDT pipelines); `[Hodge2021]` retained. EsportsBench mention at line 177 left unchanged (citation carries correct load there)."*
   - §3.2 StarCraft prediction literature: append *"**2026-04-20 (PR-TG3): §3.2.4 "Po pierwsze" paragraph supplemented with one sentence specifying EsportsBench as a rating-systems benchmark (not ML-classifier benchmark) with per-game fit protocol and the AoE2-absence finding (v8.0 2025-12-31 verified). Existing `[REVIEW: dokładna wartość 80,13%]` flag retained as a Pass 2 verification item."*
   - §3.5 Research gap: append *"**2026-04-20 (PR-TG3): §3.5 Luka 3 rewritten to narrow the novelty claim via a four-constraint argued disqualification against Thorrez 2024 EsportsBench per Pass-2 TG3 dispatch (ML-classifier family / SC2+AoE2 / proper probabilistic evaluation with calibration / 1v1). The "pierwsza znana nam" hedge is replaced by an argued "w przestrzeni wyznaczonej koniunkcją tych czterech ograniczeń…" framing anchored on the verified EsportsBench v8.0 title list (AoE2 absent). Original `[REVIEW: RQ3 novelty hedge]` flag resolved; reduced-scope `[REVIEW: narrowing przeciwko EsportsBench — weryfikować przyszłe wersje]` flag planted."*
2. **REVIEW_QUEUE.md.** Two entries updated:
   - Row for §1.3 at line 22: append *"**RESOLVED 2026-04-20 (PR-TG3): question (2) closed — EsportsBench reports per-system fit only, not cross-system comparability; `Thorrez2024` citation removed from RQ1 hypothesis and replaced with Hodge2021 + Tang2025 (directly-supporting peer-reviewed sources). Question (1) — RQ4 cold-start strata — remains Pending pending Phase 03 empirical match-count distribution.**"*
   - Row for §3.5 at line 40: append *"**RESOLVED 2026-04-20 (PR-TG3): novelty hedge reformulated as an argued four-constraint narrowing against Thorrez 2024 EsportsBench. ML-classifier vs rating-systems family distinction, SC2+AoE2 specificity (AoE2 absence from EsportsBench v8.0 2025-12-31 verified), proper probabilistic evaluation with calibration diagnostics, and 1v1 scope — conjunction required. `[REVIEW: RQ3 novelty hedge]` flag resolved; reduced-scope `[REVIEW: narrowing przeciwko EsportsBench — weryfikować czy przyszłe wersje dodają AoE2 lub rozszerzają protokół o ML-classifier benchmarking]` flag planted. Key artifacts column unchanged. Remaining Pass 2 questions: (2) confirm Luka 4 cold-start gap is not addressed by any 2025-2026 esports paper not captured by planning sweep; (3) verify forward-ref to §4.4 is stable with current experimental protocol design.**"*
3. Verify ISO date format and em-dash usage in the new notes.

**Verification:**
- `grep -cF "PR-TG3" thesis/WRITING_STATUS.md` returns exactly 4 (one per affected section).
- `grep -cF "2026-04-20 (PR-TG3)" thesis/chapters/REVIEW_QUEUE.md` returns exactly 2 (the §1.3 row update and the §3.5 row update).

**File scope:**
- `thesis/WRITING_STATUS.md`
- `thesis/chapters/REVIEW_QUEUE.md`

**Read scope:**
- `thesis/chapters/01_introduction.md`
- `thesis/chapters/02_theoretical_background.md`
- `thesis/chapters/03_related_work.md`

## File Manifest

| File | Action |
|------|--------|
| `planning/current_plan.md` | Rewrite (TG3 plan) |
| `planning/current_plan.critique.md` | Rewrite (reviewer-adversarial Mode A critique) |
| `thesis/chapters/03_related_work.md` | Update (§3.2.4 supplementation + §3.5 Luka 3 rewrite) |
| `thesis/chapters/01_introduction.md` | Update (§1.3 RQ1 citation correction) |
| `thesis/chapters/02_theoretical_background.md` | Update (§2.5.5 hybrid-strategy citation correction) |
| `thesis/WRITING_STATUS.md` | Update (four PR-TG3 notes) |
| `thesis/chapters/REVIEW_QUEUE.md` | Update (§1.3 and §3.5 row resolutions) |

## Gate Condition

- `grep -nF "pierwszą znaną nam" thesis/chapters/03_related_work.md` returns zero hits.
- `grep -nF "AoE2 nie występuje" thesis/chapters/03_related_work.md` or equivalent narrowed-claim anchor returns at least one hit inside §3.5.
- `grep -nF "EsportsBench" thesis/chapters/03_related_work.md` returns two or more hits (one in §3.2.4 existing+supplemented; one in §3.5 rewritten Luka 3).
- `grep -cF "Thorrez2024" thesis/chapters/01_introduction.md` = 0 (pre-edit count was 1; T02 removes the §1.3 RQ1 citation).
- `grep -cF "Thorrez2024" thesis/chapters/02_theoretical_background.md` = 3 (pre-edit count was 4; T02 removes §2.5.5:181 citation; §2.5.5:177 citation RETAINED with tightened claim per L-5).
- `grep -cF "Thorrez2024" thesis/chapters/03_related_work.md` = 3 (pre-edit count was 2; T01 adds §3.5 Luka 3 citation; §3.2.4:77 and §3.0:9 preserved).
- `grep -nF "Hodge2021" thesis/chapters/02_theoretical_background.md:181` still returns a hit.
- `grep -cF "PR-TG3" thesis/WRITING_STATUS.md` equals 4.
- `grep -cF "2026-04-20 (PR-TG3)" thesis/chapters/REVIEW_QUEUE.md` equals 2.
- `grep -nF "REVIEW: RQ3 novelty hedge" thesis/chapters/03_related_work.md` returns zero hits.
- `grep -nF "REVIEW: narrowing przeciwko EsportsBench" thesis/chapters/03_related_work.md` returns exactly one hit.
- ISO YYYY-MM-DD format preserved in all new prose (spot-check via `grep -nE "2026-04-[0-9]{2}|2025-12-31|2024-03-31" thesis/chapters/01_introduction.md thesis/chapters/02_theoretical_background.md thesis/chapters/03_related_work.md thesis/WRITING_STATUS.md thesis/chapters/REVIEW_QUEUE.md`); no Polish month names (`grep -nE "stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|listopada|grudnia" <same-files>` returns zero hits in newly-written lines).
- Pre-commit hooks pass (ruff, mypy, markdown linting if enabled). No test coverage impact (prose-only).
- PR body generated from `.github/pull_request_template.md` skeleton; Summary bullets list the four sections touched and one-sentence per-site rationale; Test plan bullets list the grep-based verifications above.

## Rollback plan

If reviewer-adversarial Mode A flags a BLOCKER at T01 or T02 (e.g., the four-constraint conjunction is judged insufficiently tight, or a missing EsportsBench title invalidates the AoE2-absence argument), roll back the branch to `master` via `git reset --hard origin/master` (user-authorized destructive op; planner note: explicit user approval required). If only a WARNING or MINOR is raised, apply the surgical fix on the same branch and re-run the Gate Condition checks; do not ship PR-TG3 until the critique converges. If TG3 lands but TG4–TG6 later discover a new Thorrez2024 citation that should have been corrected here, TG4's scope expands to a catch-all "Thorrez2024 citation audit" step (one extra task). Rollback of a merged PR is performed by the user; planner does not propose destructive ops without explicit direction.

**Degradation-mode fallback for EsportsBench v9.0+ scenarios.** If Pass 2 verification (per the reduced-scope [REVIEW:] flag planted in T01) discovers that a post-v8.0 EsportsBench release adds Age of Empires II or introduces ML-classifier benchmarking: the Luka 3 narrowing degrades gracefully rather than collapses. Specific mode: (a) if AoE2 added but still per-game rating-systems fit — constraint (b) "cross-game benchmarking (SC2+AoE2)" survives because cross-game benchmarking remains unperformed; T01 prose update is minimal (swap "żadnej wersji wydanej do 2025-12-31" for "przez referencyjny benchmark paired-comparison rating systems"); (b) if ML-classifier benchmarking added AND AoE2 added AND cross-game protocol added — three of four constraints collapse; Luka 3 narrows to SC2-only scope and the AoE2-specific claim moves from §3.5 to §1.3 RQ3 operationalization only, treated as a Phase 03 empirical finding rather than a literature gap; (c) if Pass 2 manual preprint-PDF analysis reveals Table 2 of Thorrez 2024 contains calibration diagrams, Brier score, or Murphy decomposition — constraint (c) must be rewritten to promote cross-game-benchmarking as a standalone operative constraint (distinguished from per-game fit) and drop the calibration-diagnostics anchor; §3.5 narrowing then rests on three active constraints ((a) ML-classifier family / (b) paired-game cross-comparison / (d) 1v1 scope). This degradation-mode is not a TG3 action; it is a documented contingency for a future PR.

## Out of scope

- **TG4** — 11 bibliography findings including Thorrez2024 bibkey author-name correction (Lucas → Clayton) and the 11 other bibliography fixes. Separate PR.
- **TG5** — 6 internal-consistency fixes. Separate PR.
- **TG6** — 12 prophylactic/hygiene fixes. Separate PR.
- **Exact 80.13% SC2 Glicko figure verification.** The existing `[REVIEW: 80,13%]` flag at `03_related_work.md:77` remains. TG3 does not decode the EsportsBench PDF to resolve it (WebFetch failed on 2026-04-20 due to binary-encoded PDF; manual verification is Pass 2 work).
- **§4.4.4 and §4.4.5 and §4.4.6** — Untouched by TG3. The within-game protocol (§4.4.4) and ICC estimator (§4.4.5) and `[PRE-canonical_slot]` flag (§4.4.6) are all invariant to the Luka 3 narrowing; no forward-refs need adjustment.
- **`.claude/scientific-invariants.md`** — Not modified. Invariant #8 (cross-game comparability) remains advisory; TG3 prose does not reference invariant #8 directly.
- **Phase 01 artifact modification** — Invariant #9 forbids; nothing in TG3 requires it.
- **Bibkey additions** — None. All citations exist in `thesis/references.bib` (Thorrez2024, Hodge2021, Tang2025, Lin2024NCT, Elbert2025EC, CetinTas2023).
- **EsportsBench v9.0+ monitoring** — Left as a Pass 2 monitoring question via the reduced-scope `[REVIEW:]` flag planted in T01. TG3 freezes the narrowing against v8.0 (2025-12-31).
- **Any prose edit to §3.5 Luka 1, Luka 2, Luka 4, or closing paragraph** — Out of TG3 scope. Luka 1 and Luka 2 already cite EsportsBench correctly (the sibling claim about rating-systems reporting AUC/accuracy only is unaffected). Luka 4 and the closing paragraph do not cite Thorrez2024.
- **TrueSkill 2 AlphaStar / Halo 5 wording** — Untouched by TG3. The existing `[REVIEW:]` flag at §2.5.3 stays.

## Open questions

- **Open Q 1 (3-part edit interpretation).** The user's Pass-2 dispatch master describes TG3 as a "3-part edit" against §3.5. This plan interprets the three parts as §3.5 + §3.2.4 + (coupled §1.3 + §2.5.5, treated as "Part 3" because both carry the same miscitation pattern). Alternative interpretation: §3.5-internal only (three paragraphs within §3.5 rewritten in series). If the user prefers the §3.5-internal reading, Part 2 (§3.2.4 supplementation) moves to TG4 as a new finding and Part 3 (§1.3 + §2.5.5 miscitations) moves to TG5 as internal-consistency. Planner recommendation: proceed with the broader reading because leaving §1.3 and §2.5.5 unedited allows a new contradiction to ship between the narrowed §3.5 and the Thorrez2024-miscited upstream sites — violating the "no new contradictions" principle established by TG2. **Resolves by:** user confirmation before T01 begins.
- **Open Q 2 (Thorrez2024 author-name typo in `references.bib`).** The bibkey at `references.bib:147` credits "Lucas Thorrez"; the author's web profile and HuggingFace dataset ownership identify "Clayton Thorrez". This is a bibliographic error but TG3 does not touch the bib file per one-PR-per-task-group discipline. Planner recommendation: flag this as a new TG4 finding (added to the 11 bibliography findings list). **Resolves by:** TG4 plan (separate PR).
- **Open Q 3 (RQ1 hypothesis Tang2025 citation doubling) — RESOLVED via surgical deletion.** The plan does not integrate Tang2025 where Thorrez2024 previously stood. Instead, T02 step 2 surgically deletes only the miscited phrase *"oraz powtarzalnym wzorcem obserwowanym w predykcji esportowej [Thorrez2024]"* (together with its leading " oraz " connective). The preserved later-sentence Tang2025 caveat (*"— jak wykazali Tang, Wang i Jin [Tang2025] — typowy przyrost 2–5 pp"*) carries the margin-hedge function cleanly with ONE Tang2025 citation in the sentence. Result: post-T02 the RQ1 hypothesis sentence cites Hodge2021 once and Tang2025 once; no doubling; no new content introduced. **Resolves by:** T02 surgical deletion per the explicit instruction. Secondary note: the deletion does narrow the RQ1 hypothesis's inductive base to a single Dota 2 result (Hodge2021) plus a margin caveat (Tang2025). The previously-miscited "repeating pattern in esports prediction" broader claim is lost. This narrowing is intentional: the original citation did not support the broader claim. A correctly-cited cross-esport GBDT-dominance source could be added in a future Pass 2 edit if the narrowed inductive base proves insufficient during defense, but no such citation is added in TG3 (which is scope-limited to correcting miscitations, not introducing new positive evidence).
- **Open Q 4 (EsportsBench v8.0 stability assumption).** The TG3 narrowing anchors on EsportsBench v8.0 (2025-12-31). If a v9.0 release between 2025-12-31 and the thesis defense adds Age of Empires II or introduces ML-classifier benchmarking, the narrowing would need to move to a newer version. Planner recommendation: the reduced-scope `[REVIEW:]` flag planted in T01 explicitly directs Pass 2 to re-check version stability. **Resolves by:** Pass 2 monitoring / defense-prep verification.
- **Open Q 5 (four-constraint conjunction tightness).** Whether the four operative constraints (ML-classifier family / cross-game benchmarking SC2+AoE2 / calibration diagnostics and Murphy decomposition / 1v1) are genuinely operationally disjoint or whether a reviewer could collapse some pair into one (e.g., "calibration diagnostics + 1v1 = standard esports-pre-match evaluation"). Planner recommendation: the constraints are disjoint because (a) ML-classifier vs rating-systems is a fundamental method-family distinction EsportsBench-confirmed; (b) cross-game benchmarking (SC2+AoE2) is the two-game paired structure that Thorrez would have performed if AoE2 were included — the paired-game cross-comparison is the operative requirement, not just "two RTS games in the benchmark"; (c) calibration-diagnostics-and-Murphy-decomposition goes beyond EsportsBench's announced accuracy-and-log-loss metric set (EsportsBench README and HuggingFace documentation do not advertise reliability diagrams or Murphy decomposition); (d) 1v1 scope rules out Elbert2025EC-style team matches. Completeness argument: the four constraints are claimed jointly sufficient because (i) ML-classifier family captures the method-space distinction from rating systems; (ii) paired-game cross-comparison captures the two-game structure distinct from per-game fit; (iii) calibration diagnostics capture the probabilistic-evaluation depth distinct from accuracy-only reporting; (iv) 1v1 scope captures the task-structure alignment. An unmentioned paper that satisfies all four would by construction benchmark ML classifiers on SC2+AoE2 with calibration diagrams on 1v1 matches — a configuration that the planner's sweep of 2024–2026 esports-prediction literature did not find. No additional operative constraint (e.g., pre-match vs in-match feature family, temporal vs random CV) is required to distinguish this work because Luka 1 (pre-match vs in-match) and Luka 2 (calibration coverage) are handled as separate gaps in §3.5, each with its own literature disqualification. The four-constraint conjunction is necessary and locally sufficient for Luka 3; broader scope questions fall under Luka 1/2/4 rather than Luka 3. reviewer-adversarial Mode A validates the tightness before T01 proceeds. **Resolves by:** reviewer-adversarial Mode A.
- **Open Q 6 (whether the Thorrez2024 citation retention at §2.5.5 line 177 risks a consistency issue with Part 3) — RESOLVED via tightening.** The "cechy wejściowe w ML pipelines" sub-claim at `02_theoretical_background.md:177` was an overclaim: EsportsBench benchmarks pure rating systems, not hybrid pipelines. T02 step 4 surgically tightens the line 177 prose by replacing the overclaiming sub-clause with "benchmarkuje rankingi paired-comparison rating systems (m.in. Elo, Glicko, Glicko-2, TrueSkill) na danych esportowych". The Thorrez2024 citation is retained at line 177 with this corrected, tighter claim. No residual inconsistency with Part 3 (line 181 removal) remains: both sites now accurately reflect what EsportsBench benchmarks. **Resolves by:** T02 step 4 tightening edit (iter-1 critique L-5).

## Adversarial critique triggers

The parent session must, after planner returns this plan, dispatch reviewer-adversarial Mode A to produce `planning/current_plan.critique.md`. Triggers for Mode A to look at specifically:

- Four-constraint conjunction tightness (Open Q 5).
- Whether §3.5 Part 1's rewrite re-commits a novelty claim at a lower abstraction (parallel to TG1 triptych risk).
- Whether §2.5.5 line 177 retention of `Thorrez2024` is consistent with Part 3's line 181 removal (Open Q 6).
- Whether ISO YYYY-MM-DD dates and em-dash formatting are preserved in all new prose.
- Whether the rewritten §1.3 RQ1 hypothesis sentence has exactly one Tang2025 citation (Open Q 3).
- Whether the new reduced-scope `[REVIEW:]` flag tied to EsportsBench future-release monitoring is tight enough or should be deferred to a global "thesis-wide literature currency" concern.
- Whether "3-part edit" is correctly decomposed across §3.5 + §3.2.4 + (§1.3 + §2.5.5) versus the §3.5-internal-only alternative (Open Q 1).

> For Category A or F, adversarial critique is required before execution. Dispatch reviewer-adversarial to produce `planning/current_plan.critique.md`.

---

Sources:

- [EsportsBench dataset on Hugging Face](https://huggingface.co/datasets/EsportsBench/EsportsBench)
- [Clayton Thorrez personal page](https://cthorrez.github.io/)
- [EsportsBench GitHub repository](https://github.com/cthorrez/esports-bench)
- [EsportsBench preprint PDF (binary; manual read required for 80.13% verification)](https://cthorrez.github.io/papers/esportsbench/EsportsBench_preprint.pdf)
