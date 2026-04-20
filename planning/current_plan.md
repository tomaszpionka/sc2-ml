---
category: F
branch: docs/thesis-pass2-tg6a-luka-prophylactic-strengthening
date: 2026-04-20
planner_model: claude-opus-4-7
---

# Plan: TG6-PR-6a — §3.5 Luka 1 / Luka 2 / Luka 4 prophylactic strengthening (F6.1 + F6.2 + F6.3)

**Category:** F (Thesis — science-lite; three prose additions to §3.5 + one verified bib entry)
**Branch:** `docs/thesis-pass2-tg6a-luka-prophylactic-strengthening`
**Base:** `master` (at `a5dae995`, post-PR #193 merge; version 3.35.0)
**Audit source:** `thesis/reviews_and_others/pass2_dispatch.md` Task Group 6 F6.1 (line 181) + F6.2 (line 183) + F6.3 (line 185); scope inheritance documented in `thesis/reviews_and_others/pass2_status.md` §PR-6a (lines 36–44).

## Problem Statement

Pass-2 audit Task Group 6 identified three prophylactic-strengthening opportunities in §3.5 (Luka badawcza i pozycjonowanie niniejszej pracy):

1. **F6.1 — Luka 1 can be strengthened.** The current Luka 1 prose establishes the gap abstractly ("no esports paper does multi-family classification benchmarking with probabilistic metrics") without naming the 2024–2026 evidence base. The audit proposed six seed references (Brookhouse & Buckley 2025; Caldeira et al. 2025; Alhumaid & Tur 2025; Minami et al. 2024; García-Méndez & de Arriba-Pérez 2025; Ferraz et al. 2025) that would concretely witness the gap. **WebSearch verification (2026-04-20) surfaced exactly ONE of the six seeds as retrievable peer-reviewed literature satisfying Luka 1's reference class (multi-family classifier benchmarking): Minami et al. 2024.** The other four (Brookhouse & Buckley; Caldeira; Alhumaid & Tur; Ferraz) could not be located via multiple targeted WebSearch formulations. GarciaMendez2025 already exists in `thesis/references.bib:275` but is a single-paradigm streaming-ML pipeline and does NOT satisfy Luka 1's multi-family-classifier-benchmark reference class — it is therefore NOT added as a Luka 1 witness despite surfacing in the audit seed list. Per `.claude/rules/thesis-writing.md` Literature Search Protocol (§6 WebSearch failure handling) and the Pass-2 critical gotcha #1 ("do not trust audit primary-source claims as verified"), un-verifiable seed names MUST NOT be cited as existing references — the fix is to plant `[NEEDS CITATION]` flags enumerating the unverified seed authors for Pass-2 manual verification, rather than to invent bib entries.
2. **F6.2 — Luka 2 needs a SHAP/econometric-residualization disambiguation.** The current Luka 2 prose treats Elbert et al. 2025 as "uses eAPM, Solo Elo, miary znajomości funkcjonalnej (mapa, cywilizacja jako wymiary znajomości, nie bezpośrednie predyktory) — architektura cech zaprojektowana pod identyfikację efektu drużynowego, nie pod optymalizację predykcji 1v1." This understates a precise methodological distinction: Elbert's feature-attribution strategy is econometric linear-fixed-effects residualization, not a marginal-attribution method like SHAP. The F6.2 amendment should add one sentence explicitly naming this distinction so that an examiner cannot argue "Elbert does SHAP-equivalent analysis." No new bib entries are required.
3. **F6.3 — Luka 4 needs a short restatement that no related-work paper stratifies by player match-history length.** The current Luka 4 prose establishes the gap ("no esports prediction paper stratifies accuracy by player history length"). The audit originally proposed a terminology-acknowledgement footnote anchored to GarciaMendez2025's "cold start" term-of-art. Per R13 (merged-critic iteration 2), GarciaMendez2025 is decoupled from PR-6a's substantive argumentation: (a) it does NOT satisfy Luka 1's multi-family-classifier-benchmark reference class (see F6.1 above), and (b) WebSearch 2026-04-20 did not confirm the literal string "cold start" in the paper abstract. Luka 4's amendment is therefore reframed as a pure Luka-4 restatement that does NOT depend on GarciaMendez2025's "cold start" terminology — a single short sentence noting that no paper cited in §3.2–§3.4 stratifies prediction accuracy by player match-history length, with a parenthetical clarification that different uses of the term "cold start" in adjacent literature (e.g., streaming-ML context) do not cover this gap. GarciaMendez2025 remains cited in §1.1 for its streaming-ML win-prediction framing; §3.5 Luka 4 references it only to note that the "cold start" terminology from streaming-ML is not synonymous with player-history length. No new bib entry is required.

Together, the three amendments strengthen §3.5's prophylactic framing against three specific examiner attack vectors without introducing new empirical claims or methodology. The PR's discipline is: **(a) verified-only literature additions** (Minami 2024, verified against `journals.sagepub.com`/`sciencedirect.com`); **(b) prose-level methodological disambiguations**; **(c) [NEEDS CITATION] flags for items that cannot currently be verified against published literature.**

## Literature Context

### F6.1 verified anchors (one new bib entry)

Of the six audit-seed names, **one** is retrievable as a real peer-reviewed publication that satisfies Luka 1's multi-family-classifier-benchmark reference class (the remaining four are unverifiable via WebSearch — see subsection below; GarciaMendez2025 is retrievable but a single-paradigm streaming-ML pipeline and is NOT added as a Luka 1 witness per R13):

- **[Minami2024]** (new bib entry — one new `@article`) — Minami, Sorato; Koyama, Haruki; Watanabe, Ken; Saijo, Naoki; Kashino, Makio 2024, "Prediction of esports competition outcomes using EEG data from expert players," *Computers in Human Behavior*, vol. 160, article 108351, DOI 10.1016/j.chb.2024.108351. NTT Corporation research. 20 experienced fighting-video-game players; LightGBM achieved 80% accuracy on pre-match EEG features across multiple ML algorithms (logistic regression, linear-SVM, rbf-SVM, k-NN, random forest, extra trees, XGBoost, LightGBM, CatBoost). Reports accuracy, macro-F1, MCC — **NOT** Brier score, log-loss, or reliability diagrams. This is the concrete 2024 witness of the Luka 1 gap: a multi-family classifier comparison that reports classification metrics but not probabilistic calibration. Key distinguishing feature for Luka 1: input modality is EEG (physiological), not pre-game metadata — which slightly narrows the direct Luka 1 relevance (F6.1 framing must acknowledge the modality distinction). **Coverage narrative:** "1 of 6 retrievable" under Luka 1's reference-class filter (Minami2024); 4 unverifiable via WebSearch; GarciaMendez2025 retrievable but filtered out as single-paradigm streaming-ML pipeline, referenced only in F6.3's terminology context.

### F6.1 unverified seed names ([NEEDS CITATION] flag)

The following four names from the audit seed list (pass2_dispatch.md:181) could not be located via WebSearch on 2026-04-20:

- **"Brookhouse & Buckley 2025"** — no publication matching this author pair surfaced in targeted searches (5 distinct query formulations). The closest surfaced reference is Buckley, Chen & Knowles 2015 "Rapid skill capture in a first-person shooter" (IEEE TCIAIG) — a 10-year-older paper with a different author list.
- **"Caldeira et al. 2025"** — no publication matching this author pair in esports-ML surfaced. Top results across 3 formulations returned GarciaMendez2025 (already in bib; different authors) or unrelated football/generic-sports work.
- **"Alhumaid & Tur 2025"** — no publication matching either author surfaced in esports-ML search; top results returned unrelated 2025 SHAP-Counter-Strike work by Jing, Awang et al. (a performance-analysis paper, not outcome prediction).
- **"Ferraz et al. 2025"** — no publication matching this author in esports-ML prediction with calibration focus surfaced; top results returned a Jalovaara 2024 Aalto master's thesis (grey literature) on LoL win probability.

Per `.claude/rules/thesis-writing.md` §Literature Search Protocol item 6: "If two widened queries both return nothing, plant `[NEEDS CITATION]` in the draft … Do NOT invent a citation." PR-6a plants a single consolidated `[NEEDS CITATION]` flag on the §3.5 Luka 1 paragraph listing the 4 unverified author names and the 5 queries attempted, for Pass-2 manual verification.

### F6.2 anchors (no new bib)

- **[Elbert2025EC]** (bib line 74) — AoE2 team-games outcome prediction. Per §3.4.3 framing already in chapter, uses pseudo-R² 0.0744 (S1.3) and 0.1004 (S2.4); econometric linear-fixed-effects specification. The F6.2 amendment names its feature-attribution strategy (linear fixed-effects residualization) and contrasts with SHAP's marginal-contribution / conditional-expectation approach. SHAP itself as a method is not newly cited — it is already the ablation-analysis reference in §4.4.

### F6.3 anchors (no new bib)

- **[GarciaMendez2025]** (bib line 275) — CS:GO streaming win prediction. Per R13, GarciaMendez2025 is decoupled from F6.3's substantive argumentation. The paper is cited in §1.1 for its streaming-ML win-prediction framing; §3.5 Luka 4 references it only within a brief terminology-example parenthetical noting that different uses of the term "cold start" in adjacent streaming-ML literature do not cover Luka 4's gap (player match-history length stratification). No substantive claim about GarciaMendez2025's internal terminology is load-bearing for F6.3 after R13 decoupling; the "cold start" term-of-art presupposition is retracted.

## Assumptions & Unknowns

- **Assumed:** Minami2024's multi-algorithm comparison (9+ algorithms) + single-best-accuracy reporting + EEG-feature modality is correctly characterized above based on WebSearch-surfaced abstract details. Pass-2 can read the PDF to confirm (a) exact algorithm set; (b) whether any calibration metric is reported; (c) whether the EEG-feature claim is correct. For PR-6a purposes, the paper is cited only for the "multi-family accuracy-only benchmark" claim; if Pass-2 PDF verification surfaces Brier or log-loss reporting, the F6.1 framing needs revision.
- **Assumed (hedged per R14):** Elbert2025EC's feature-attribution strategy is linear fixed-effects residualization, not SHAP-equivalent, based on our reading of its §3.4.3 framing and the paper's ACM EC '25 econometric architecture. This is consistent with the §3.4.3 framing already in chapter 3 ("architektura cech zaprojektowana pod identyfikację efektu drużynowego"). Pass-2 PDF read confirms; the T02 insertion prose is phrased conditionally so that a contrary Pass-2 finding does not commit a false declarative claim.
- **Unknown:** Whether the 4 unverifiable seed author names from pass2_dispatch.md:181 are (a) mis-spellings of real papers, (b) real papers not indexed by WebSearch, (c) confabulated by the audit, or (d) accepted-but-not-yet-published preprints. PR-6a plants `[NEEDS CITATION]` with the queries attempted; Pass-2 manual verification closes. **This is the most load-bearing assumption for the F6.1 scope limitation.**

## Gate Condition

Per-task gates at T01–T06 below. Aggregate:

- `git diff --stat` touches exactly: `thesis/chapters/03_related_work.md` (§3.5 Luka 1 + Luka 2 + Luka 4 edits), `thesis/references.bib` (one Minami2024 entry appended), `thesis/WRITING_STATUS.md`, `thesis/chapters/REVIEW_QUEUE.md`, `pyproject.toml` + `CHANGELOG.md` for version bump (6 files total).
- NO changes to `src/`, `reports/`, `sandbox/`, `.claude/`, or chapters other than §3.5.
- Exactly ONE new bib entry (`Minami2024`); NO invented citations for Brookhouse/Caldeira/Alhumaid/Ferraz.
- Exactly 2 flags added/modified in §3.5: one `[NEEDS CITATION]` on Luka 1 enumerating the 4 unverified seed names; one `[REVIEW: F6.2 Pass-2 Elbert2025EC PDF confirmation of linear-fixed-effects-residualization attribution]` on Luka 2. Per R13, Luka 4's F6.3 restatement carries no `[REVIEW]` flag (no presupposition to verify after decoupling).
- Planning-drift pre-commit hook passes (all 8 Cat F sections present in this plan).

## Open Questions

1. **Pass-2:** Manual verification of 4 unverified seed author names. Closes `[NEEDS CITATION]` flag or tightens F6.1 prose if any surfaces as real publications.
2. **Pass-2:** Read Minami2024 PDF to confirm (a) multi-algorithm framing, (b) absence of calibration metrics, (c) EEG-feature modality characterization.
3. **Pass-2:** Read Elbert2025EC PDF to confirm the feature-attribution strategy is linear fixed-effects residualization.
4. **Pass-2 (no longer load-bearing per R13):** GarciaMendez2025 PDF read is optional rather than required after F6.3's decoupling. The F6.3 amendment no longer presupposes a specific internal use of the term "cold start" by the paper; Pass-2 may read the PDF if useful for §1.1 citation context, but F6.3 does not depend on it.

## Scope

### What this PR covers

1. **F6.1 — §3.5 Luka 1 strengthening.** Add to the existing Luka 1 paragraph a concrete naming of the 2024–2026 multi-family-classifier-without-calibration literature: Minami et al. 2024 explicitly named (bib entry to be added) as the single verified Luka 1 witness, with a `[NEEDS CITATION]` flag enumerating the 4 unverifiable seed authors for Pass-2 closure. Per R13, GarciaMendez2025 is NOT added as a Luka 1 co-witness (single-paradigm streaming-ML pipeline does not satisfy multi-family-classifier-benchmark reference class).
2. **F6.2 — §3.5 Luka 2 strengthening.** Add to the existing Luka 2 paragraph one sentence — phrased conditionally per R14 — distinguishing Elbert2025EC's econometric linear-fixed-effects residualization from SHAP's marginal-attribution method. Per R15, SHAP is referenced as "metoda SHAP (omawiana w §4.4)" to provide a forward-reference anchor without adding a new bib entry. Plant `[REVIEW: F6.2 Pass-2 Elbert2025EC PDF confirmation of linear-fixed-effects-residualization attribution]` flag.
3. **F6.3 — §3.5 Luka 4 short restatement.** Per R13, reframe as a pure Luka-4 restatement: one short sentence noting that no paper cited in §3.2–§3.4 stratifies prediction accuracy by player match-history length, with a brief parenthetical clarification that different uses of the term "cold start" in adjacent literature (e.g., streaming-ML context) do not cover this gap. GarciaMendez2025 is referenced only as a terminology example, not as a substantive Luka 4 anchor. The `[REVIEW: F6.3 …]` flag is removed (no presupposition to verify after R13 decoupling).
4. **Bib addition:** One new entry `Minami2024` in `thesis/references.bib` with DOI, journal, volume, article number.
5. **REVIEW_QUEUE + WRITING_STATUS updates** documenting the three amendments per `.claude/rules/thesis-writing.md`.

### What this PR does NOT cover

- **NO invented bib entries** for Brookhouse, Caldeira, Alhumaid, Ferraz. These are Pass-2 follow-up items, not silent additions.
- **NO §3.5 Luka 3 touch.** Luka 3 was handled in PR-TG3 (PR #189) + PR-TG5a/PR-TG5b; not re-litigated here.
- **NO rewriting of existing Luka 1/2/4 paragraphs** — only insertions. Existing prose framing preserved.
- **NO F6.4–F6.12 chore items** — deferred to PR-6b (separate PR per audit ordering).
- **NO F5.6 Demšar §3.2 → §3.1.3 swap** — deferred to post-Pass-2 once readable PDF confirms location.
- **NO data/feature/model work.** Category F science-lite; `.claude/scientific-invariants.md` Invariants #1, #3, #4, #5, #6, #7 (except I7 trace for Minami 80% accuracy — anchored to WebSearch result URL), #8, #9, #10 are N/A.

### Binding discipline

- **Polish academic register** throughout. Use existing §3.5 vocabulary ("Luka 1", "Luka 2", "Luka 4", "*method-family benchmarking*", "stratyfikacja") for consistency.
- **ISO dates** (yyyy-mm-dd); no locale-Polish date forms.
- **Citation discipline (`I2` reproducibility invariant):** every new inline citation has DOI in the bib entry. Minami2024 has DOI 10.1016/j.chb.2024.108351.
- **[NEEDS CITATION] flag convention:** enumerate the 4 author names + note the 5 WebSearch queries attempted + Pass-2 manual verification as the closure mechanism. Per `.claude/rules/thesis-writing.md` Literature Search Protocol §6 WebSearch failure handling.
- **3-round adversarial caps asymmetric** (per `feedback_adversarial_cap_execution.md`): `/critic` max 3; Mode A one run + up to 1 revision cycle; Mode C one run + up to 1 revision cycle. Caps are not numerically equal; asymmetry reflects distinct review cost/benefit profiles.
- **Post-merge planning purge**: overwrites PR-5b plan; future PR-6b plan will overwrite this.

## Execution Steps

### T01 — F6.1 §3.5 Luka 1 strengthening

**File:** `thesis/chapters/03_related_work.md` (Luka 1 paragraph at line 185 ending with "dekompozycją Murphy'ego (per §2.6).").

**Action:** Append one new sentence + `[NEEDS CITATION]` flag inside the existing Luka 1 paragraph, immediately before its closing sentence "Niniejsza praca, zgodnie z RQ1 (§1.3), przeprowadza takie porównanie…". New content:

**Proposed insertion (Polish; writer-thesis may refine within scope):**

> Wzorzec ten — raportowanie trafności klasyfikacyjnej bez pełnej oceny probabilistycznej (Brier score, log-loss, diagramy rzetelności) — jest konsystentnie obserwowany także w sąsiadującej literaturze ML-esportowej 2024–2025, choć poza ścisłą klasą referencyjną RQ1 (klasyfikatory 1v1 RTS z cechami przedmeczowymi). Ilustracją takiego sąsiadującego — nie-bezpośrednio-w-klasie-referencyjnej — przypadku jest praca [Minami2024], porównująca dziewięć rodzin klasyfikatorów (m.in. regresję logistyczną, SVM, random forest, XGBoost, LightGBM, CatBoost) w predykcji wyniku walk w grze FVG z cech EEG przed-meczu, raportująca trafność (80% dla LightGBM jako najlepszego modelu), macro-F1 i MCC — lecz nie Brier score, log-loss ani diagramu rzetelności. Praca ta nie jest bezpośrednim świadkiem Luka 1 w ścisłym sensie (modalność cech = EEG, nie metadane pre-game; typ gry = FVG, nie RTS 1v1), lecz dokumentuje szerszy branżowy wzorzec raportowania bez pełnej oceny probabilistycznej — wzorzec, do którego literatura pokrywająca ściśle klasę referencyjną Luka 1 (omówiona w §3.2–§3.3) również się stosuje. [NEEDS CITATION: F6.1 Pass-2 audit — 4 dodatkowe kandydatury autorskie z dispatch seed list (`thesis/reviews_and_others/pass2_dispatch.md:181`) wyliczone są w `thesis/chapters/REVIEW_QUEUE.md` §3.5 (wpis 2026-04-20 wraz z 5 sformułowaniami zapytania WebSearch); WebSearch 2026-04-20 nie zidentyfikował tych publikacji; Pass 2 weryfikuje manualnie, czy istnieją.]

**Gate:**
- Exactly ONE new inline citation in Luka 1: `[Minami2024]` (new bib entry added to `thesis/references.bib`). Per R13, GarciaMendez2025 is NOT cited in Luka 1.
- One new `[NEEDS CITATION]` flag with explicit Pass-2 verification payload (the 4 author names + query-attempted note + Pass-2 mechanism).
- Closing Luka 1 sentence ("Niniejsza praca, zgodnie z RQ1 (§1.3), przeprowadza takie porównanie…") preserved unchanged.
- Word-count delta: approximately +700 characters in Polish (bounded expansion; reduced vs. pre-R13 draft).

### T02 — F6.2 §3.5 Luka 2 strengthening

**File:** `thesis/chapters/03_related_work.md` (Luka 2 paragraph at line 187).

**Action:** Insert one sentence after the existing "Elbert2025EC używa eAPM, Solo Elo i miary znajomości funkcjonalnej…" sentence, explicitly distinguishing Elbert's feature-attribution strategy from SHAP.

**Proposed insertion (Polish; writer-thesis may refine within scope):**

> Metoda atrybucji cech w Elbert i in. [Elbert2025EC] jest — zgodnie z naszym odczytaniem ich §3.4.3 framingu oraz architektury ekonometrycznej ACM EC '25 — linearną regresją z efektami stałymi (*linear fixed-effects residualization*), a nie warunkową atrybucją marginalną typu metoda SHAP (omawiana formalnie w §4.4) ani leave-one-category-out ablacją rodzin cech; **jeśli nasze odczytanie jest poprawne**, rozróżnienie to jest istotne, ponieważ SHAP i ablacja podają per-instance lub per-feature-group wkład niezależnie od liniowości modelu. [REVIEW: F6.2 Pass-2 audit — zweryfikować PDF Elbert2025EC (arXiv:2506.04475) pod kątem dokładnego opisu metody atrybucji; jeśli praca wykorzystuje dodatkowo SHAP lub equivalent, niniejsze rozróżnienie wymaga korekty.]

**Gate:**
- One new bib entry in this PR (Minami2024 in T04); Lundberg2017 is **NOT** added here (deferred; §4.4 will cite it when SHAP is introduced methodologically). Per R15, SHAP in this insertion is referenced as "metoda SHAP (omawiana formalnie w §4.4)" — a forward-reference parenthetical providing a within-thesis anchor without requiring a new bib entry.
- One inline citation `[Elbert2025EC]` reused from existing bib; no new inline citation for SHAP.
- Per R14, the attribution-method claim is phrased conditionally ("jest — zgodnie z naszym odczytaniem … — …") so that a contrary Pass-2 finding does not commit a false declarative claim.
- One new `[REVIEW]` flag for Pass-2 PDF verification.

### T03 — F6.3 §3.5 Luka 4 short restatement

**File:** `thesis/chapters/03_related_work.md` (Luka 4 paragraph at line 191).

**Action (per R13 middle-ground option):** Insert one short sentence into the existing Luka 4 paragraph, immediately before its closing "Niniejsza praca adresuje tę lukę…". The sentence restates Luka 4 at the §3.2–§3.4 scope and notes that adjacent uses of the term "cold start" in streaming-ML literature do not cover this gap. GarciaMendez2025 is referenced only as a terminology example, not as a substantive Luka 4 anchor. No `[REVIEW]` flag is planted (the R13 decoupling removes the cold-start term-of-art presupposition from the plan's load-bearing claims, so there is no specific PDF finding that would invalidate the sentence as written).

**Proposed insertion (Polish; writer-thesis may refine within scope):**

> Żadna z prac cytowanych w §3.2–§3.4 nie stratyfikuje trafności predykcji według długości historii meczowej gracza; różne użycia terminu "cold start" w adjacent literaturze (np. streaming-ML kontekst w [GarciaMendez2025], cytowanym w §1.1 z powodu ramowania streaming-ML win prediction) nie pokrywają tej luki w sensie RQ4.

**Gate (per R13):**
- Zero new bib entries (GarciaMendez2025 already at bib line 275; not used as a Luka 1 co-witness per R13).
- One new inline citation `[GarciaMendez2025]` (reused from existing bib) — appears in Luka 4 only as a terminology example.
- **No new `[REVIEW]` flag** (R13 decoupling removes the dependency on a GarciaMendez2025 PDF finding; the sentence as written is defensible regardless of the paper's internal "cold start" usage).
- Per R16, the narrowed "different reason" claim is folded into the sentence itself ("cytowanym w §1.1 z powodu ramowania streaming-ML win prediction"), eliminating a separate generic "for a different reason" framing.

### T04 — Minami2024 bib entry

**File:** `thesis/references.bib`.

**Action:** Add a new `@article{Minami2024, …}` entry. Placement guidance (writer-thesis judgment per structural convention of existing bib file): either (a) **preferred** — create a new dated block header `% === Additions for §3.5 (2026-04-20, Pass-2 PR-6a) ===` placed immediately before the new entry, or (b) place the entry under an existing thematic section if structurally tighter (e.g., `% === SC2 prediction ===` or `% === MOBA / other esports ===` if present). Do NOT simply append at EOF without a header — existing bib uses thematic section dividers (`%===`). Required fields:

- `author` — `{Minami, Sorato and Koyama, Haruki and Watanabe, Ken and Saijo, Naoki and Kashino, Makio}` (5 authors, verified via ScienceDirect 2026-04-20; NTT Corporation affiliation).
- `title` — Prediction of esports competition outcomes using EEG data from expert players
- `journal` — Computers in Human Behavior
- `volume` — 160
- `year` — 2024
- `doi` — 10.1016/j.chb.2024.108351
- `url` — https://www.sciencedirect.com/science/article/pii/S074756322400219X (ScienceDirect) or https://dl.acm.org/doi/10.1016/j.chb.2024.108351
- `note` — NTT Corporation research; 20 FVG players; LightGBM 80% accuracy; multi-algorithm comparison (9+ algorithms); accuracy/macro-F1/MCC reported, no Brier/log-loss.

**Gate:**
- Exactly one new `@article` entry added; `thesis/references.bib` grows from 99 entries to 100.
- DOI and URL fields present (satisfies I2 reproducibility).
- No other bib modifications.

### T05 — REVIEW_QUEUE.md and WRITING_STATUS.md updates

**Files:** `thesis/chapters/REVIEW_QUEUE.md`, `thesis/WRITING_STATUS.md`.

**Action:** Append a `**2026-04-20 (PR-TG6a):**` bolded note to the §3.5 row in both files, documenting (a) F6.1 Minami2024 addition reframed per Mode A as **adjacent-reference-class witness, not direct Luka 1 witness** (single new citation; modality+game-type explicitly acknowledged in prose) + [NEEDS CITATION] flag pointing to REVIEW_QUEUE for 4 unverified seed authors; (b) F6.2 Elbert2025EC/SHAP disambiguation sentence phrased conditionally per R14 with importance-claim also conditionalized ("jeśli nasze odczytanie jest poprawne, rozróżnienie to jest istotne") per Mode A, SHAP forward-reference "omawiana formalnie w §4.4" per R15 + `[REVIEW: F6.2 Pass-2 Elbert2025EC PDF confirmation of linear-fixed-effects-residualization attribution]` flag; (c) F6.3 Luka 4 short restatement per R13 (GarciaMendez2025 referenced only as terminology example, no [REVIEW] flag); (d) new flag count: Luka 1 gains 1 [NEEDS CITATION], Luka 2 gains 1 [REVIEW], Luka 4 gains 0 new flags — §3.5 row flag count +2 net.

**Additional T05 sub-action per Mode A fix for L4-iter3 (cross-PR dependency tracking):** Append a second bolded dated note to the **§4.4 Methodology row** of `thesis/WRITING_STATUS.md` and `thesis/chapters/REVIEW_QUEUE.md` (or add §4.4 row if not present): "**2026-04-20 (PR-TG6a cross-PR dep):** §3.5 Luka 2 (PR-TG6a insertion) references 'metoda SHAP (omawiana formalnie w §4.4)' — §4.4 drafting must cite `[Lundberg2017]` at first SHAP mention and add the bib entry; dependency is one-way and Pass-2/§4.4-PR closes it."

**Additional T05 sub-action per Mode A fix for Warning 3 (Luka 1 [NEEDS CITATION] hygiene):** In the same §3.5 row bolded dated note, enumerate the 4 unverified audit-seed author names explicitly: "Brookhouse & Buckley 2025; Caldeira et al. 2025; Alhumaid & Tur 2025; Ferraz et al. 2025. WebSearch 2026-04-20 queries attempted: (Q1) 'Brookhouse Buckley 2025 esports win prediction machine learning classifier'; (Q2) 'Caldeira 2025 esports match prediction machine learning multiple classifiers'; (Q3) 'Alhumaid Tur 2025 esports prediction classifiers machine learning'; (Q4) 'Ferraz 2025 esports match prediction calibration machine learning'; (Q5) 'Ferraz 2024 2025 esports win probability calibration single model'. No matches retrieved; chapter flag is a POINTER to this REVIEW_QUEUE entry, reducing reputational surface in thesis prose per `.claude/rules/thesis-writing.md` Literature Search Protocol §6."

### T06 — Version bump + CHANGELOG

**Files:** `pyproject.toml`, `CHANGELOG.md`.

**Action:**
- `pyproject.toml`: `version = "3.35.0"` → `version = "3.36.0"` (minor bump for docs per `.claude/rules/git-workflow.md` §Version).
- `CHANGELOG.md`: move `[Unreleased]` contents (if any non-empty) to a new `[3.36.0] — 2026-04-20 (PR #TBD: docs/thesis-pass2-tg6a-luka-prophylactic-strengthening)` heading. Add new empty `[Unreleased]` block with `### Added / ### Changed / ### Fixed / ### Removed` headers. Populate `[3.36.0]` `### Changed` with: "docs(thesis): Pass-2 PR-6a — F6.1 §3.5 Luka 1 strengthened with verified Minami2024 citation (single witness per reference-class filter) + [NEEDS CITATION] flag for 4 unverified seed authors (Brookhouse & Buckley; Caldeira; Alhumaid & Tur; Ferraz); F6.2 §3.5 Luka 2 Elbert2025EC/SHAP conditional disambiguation with §4.4 forward-reference; F6.3 §3.5 Luka 4 short restatement (GarciaMendez2025 referenced as terminology example only); one new bib entry (Minami2024)."

**Gate:**
- `pyproject.toml` version line = `version = "3.36.0"`.
- CHANGELOG `[Unreleased]` block empty; `[3.36.0]` has the Changed-section entry.

## File Manifest

Exactly these files modified:

| File | Nature of change | Scope |
|---|---|---|
| `thesis/chapters/03_related_work.md` | 3 prose insertions in §3.5 | Luka 1 (+1 sentence + [NEEDS CITATION] flag); Luka 2 (+1 conditional-hedge sentence with §4.4 forward-ref + [REVIEW] flag); Luka 4 (+1 short restatement sentence; no new flag per R13) |
| `thesis/references.bib` | 1 new entry | `@article{Minami2024, …}` |
| `thesis/WRITING_STATUS.md` | 1 bolded dated note | §3.5 row |
| `thesis/chapters/REVIEW_QUEUE.md` | 1 bolded dated note | §3.5 row |
| `pyproject.toml` | version 3.35.0 → 3.36.0 | single line |
| `CHANGELOG.md` | [Unreleased] → [3.36.0] release entry | two block swaps |
| `planning/current_plan.md` | This file (overwrites PR-5b plan) | whole file |

No other files modified. `.github/tmp/commit.txt` and `.github/tmp/pr.txt` created during commit/PR stages, deleted at cleanup per `feedback_pr_body_cleanup.md`.

## Dispatch sequence

1. This plan written. Planning-drift hook validates all 8 Cat F sections.
2. `/critic planning/current_plan.md` — max 3 iterations. Parent orchestrates 4 critics → merger → RECOMMENDED subset → writer-thesis for plan revision if needed.
3. If iteration 3 completes with residual BLOCKERs, halt and return choice to user (land-as-is vs follow-up PR) before proceeding to Mode A.
4. `reviewer-adversarial` Mode A — one run; writes `planning/current_plan.critique.md`. If REVISE: apply once (symmetric 1-revision cap per `feedback_adversarial_cap_execution.md`); if REDESIGN: halt and escalate.
5. `writer-thesis` — dispatched against this plan with T01–T06. Emits Chat Handoff Summary.
6. `reviewer-adversarial` Mode C — one run; post-draft stress test. If REVISE: apply once; if REDESIGN: halt.
7. Pre-commit validation — planning-drift + ruff (N/A no .py) + mypy (N/A no .py).
8. Commit via `git commit -F .github/tmp/commit.txt`.
9. PR via `gh pr create --body-file .github/tmp/pr.txt`.
10. Merge via `gh pr merge --merge --delete-branch`.
11. Cleanup: `rm .github/tmp/pr.txt .github/tmp/commit.txt`.
12. Halt after merge — ask user before continuing to PR-6b.

## Risk mitigation

- **Risk: writer-thesis invents citations for the 4 unverified seed authors.** Mitigation: T01 gate explicitly enumerates the [NEEDS CITATION] flag payload. The plan's §Literature Context names only Minami2024 as the verified addition; the other four author names appear only inside the [NEEDS CITATION] flag text, never as `@article` entries. Writer-thesis follows plan literally.
- **Risk: Minami2024 paper turns out to report calibration metrics (Brier/log-loss) upon Pass-2 PDF read.** Mitigation: the [REVIEW] flag on T01 insertion explicitly lists this as Pass-2 verification item. If Pass-2 discovers calibration metrics, the F6.1 framing "accuracy-only benchmark" is revised — but the citation itself stands as a 2024 multi-family-classifier benchmark, so Luka 1 framing remains defensible with a minor text adjustment.
- **Risk: SHAP is not cited anywhere in thesis bib, leaving the F6.2 Elbert-vs-SHAP distinction un-anchored.** Mitigation (chosen fallback): verified via grep on 2026-04-20 that `thesis/references.bib` contains NO `Lundberg2017` entry. PR-6a does NOT add Lundberg2017 in this iteration — the "one new bib entry" discipline (Minami2024 only) is preserved, and the F6.2 insertion refers to "metoda SHAP" descriptively without a bibkey. §4.4 will cite Lundberg2017 properly when SHAP is introduced methodologically. This keeps T02 prose scientifically precise while respecting the PR's single-bib-entry gate.
- **Risk: GarciaMendez2025's internal use of "cold start" may differ from what the plan (or a reader) assumes.** Mitigation (per R13 decoupling): F6.3 no longer presupposes any specific internal use of the term by GarciaMendez2025. The R13-reframed Luka 4 sentence states only that "different uses of the term 'cold start' in adjacent literature (e.g., streaming-ML context) do not cover this gap" — a defensible claim regardless of the paper's internal terminology. Pass-2 PDF read on GarciaMendez2025 is no longer load-bearing for F6.3.
- **Risk: the 4 unverified seed authors ARE real publications mis-indexed by WebSearch.** Mitigation: `[NEEDS CITATION]` flag documents the 5 WebSearch queries attempted; Pass-2 manual search (e.g., Google Scholar, arXiv advanced) may surface them. If verified, a follow-up docs PR adds them without re-opening PR-6a.

## Non-negotiable invariants during execution

- **I2 (reproducibility):** Minami2024 has DOI + ScienceDirect URL. All other citations reused from existing bib entries.
- **I7 (no magic numbers):** Minami2024's 80% accuracy claim traces to the paper's own Table / abstract (flagged for Pass-2 PDF confirmation, consistent hedge pattern).
- **I8 / I9 (raw data immutability):** no changes to `reports/`, `src/`, `data/`.
- **Honesty clause:** PR-6a does NOT invent Brookhouse/Caldeira/Alhumaid/Ferraz citations. If Pass-2 discovers they do not exist, F6.1 [NEEDS CITATION] flag can be DELETED rather than resolved. The audit's seed list is not itself a primary source.
- **No thesis prose without a source:** every new inline citation has a bib entry (Minami2024 new; Elbert2025EC, GarciaMendez2025 existing — GarciaMendez2025 appears in Luka 4 only as a terminology example per R13). SHAP is referenced as "metoda SHAP (omawiana formalnie w §4.4)" in the T02 insertion per R15 (no bibkey at §3.5; Lundberg2017 will be added by §4.4 when SHAP is introduced methodologically).

## Post-merge

- Update `thesis/reviews_and_others/pass2_status.md` to reflect PR-6a merge (version 3.36.0; F6.1 partially closed with 4 [NEEDS CITATION] residuals on Luka 1; F6.2 partially closed with 1 [REVIEW] residual on Luka 2; F6.3 closed in place per R13 decoupling — no residual flag on Luka 4; PR-6b next).
- Halt and ask user before starting PR-6b.
