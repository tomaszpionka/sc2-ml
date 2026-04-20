---
category: F
branch: docs/thesis-pass2-tg5b-circular-spec-thorrez-proxy
date: 2026-04-20
planner_model: claude-opus-4-7
---

# Plan: TG5-PR-5b — §4.1.3 reference-window defence + §2.2.3 Thorrez proxy insertion (F5.4 + F4.5)

**Category:** F (Thesis — science-lite; two prose insertions with literature anchors, no new empirical claims)
**Branch:** `docs/thesis-pass2-tg5b-circular-spec-thorrez-proxy`
**Base:** `master` (at `d640711a`, post-PR #192 handoff-status doc merge)
**Audit source:** `thesis/reviews_and_others/pass2_dispatch.md` §Task Group 5 F5.4 (line 163) + §Task Group 4 F4.5 (line 124) + Appendix B A15 (lines 410–414); scope inheritance documented in `thesis/reviews_and_others/pass2_status.md` §PR-5b (lines 25–34). The prior PR-5a plan at this same path has been overwritten by this file; see §Scope / §Binding discipline for the full PR-5b scope declaration.

## Problem Statement

Pass-2 audit flagged two defects that require literature-anchored prose insertions:

1. **F5.4 — §4.1.3 "Ramy okna referencyjnego" circular spec-reference.** The reference-window-asymmetry defence paragraph (at `thesis/chapters/04_data_and_methodology.md:207`) defends aoestats 9-week single-patch window vs. sc2egset / aoe2companion 4-month window by citing internal pre-registration `reports/specs/01_05_preregistration.md` §7 + §11 W3 ARTEFACT_EDGE. The spec was authored by the same team that authored the thesis, so the citation is circular — the spec cannot serve as external authority for the methodology defence. An examiner would ask "why is patch-regime homogeneity prioritized over window-length comparability?" and receive an answer that reduces to "because we wrote a rule that says so." The defence survives only if re-anchored to independent literature.
2. **F4.5 — §2.2.3 Aligulac calibration proxy insertion.** PR-5a (F5.3) reframed the §2.2.3 Aligulac-80% claim as calibration-not-accuracy and planted a [REVIEW] flag noting that the academic-proxy comparator (Thorrez 2024 Glicko-2 80.13% on SC2 data) would be inserted in PR-5b. The flag currently carries the explicit deferral text at `thesis/chapters/02_theoretical_background.md:39`. This PR realizes the insertion: the comparator sentence cites `Thorrez2024` (bib entry already present at `thesis/references.bib:144`) to provide the independent academic calibration-proxy anchor that the Aligulac FAQ claim lacks.

Both defects are literature-anchor insertions against sources already present in `thesis/references.bib`. No new bib entries, no new empirical claims, no methodology changes beyond reframing how existing claims are justified.

## Literature Context

### F5.4 defence anchors (all already in `thesis/references.bib`)

- **[Nakagawa2017]** (bib line 923, DOI 10.1098/rsif.2017.0213) — ICC estimation under GLMM; §2.2 establishes that ICC estimators depend on the variance-decomposition structure within the reference distribution. Cluster-level within-window non-stationarity biases variance-component estimates; the paper is already cited in §4.4.5 (chapter line 383) as the authority for latent-scale ICC under logit link.
- **[Gelman2007]** (bib line 973, ISBN 9780521686891) — Chapters 11–12 establish ICC identifiability conditions for one-way random-effects ANOVA with clustered data; the text treats within-cluster stationarity of the outcome distribution as the primary prerequisite for consistent variance-component estimation. Already cited in §4.4.5 line 387 as the authority for 744-cluster identifiability.
- **[Ukoumunne2003]** (bib line 948, DOI 10.1002/sim.1643) — Cluster-bootstrap CI for ICC; Section 2 establishes that the non-parametric bootstrap CI is consistent only under the assumption of exchangeable clusters within the reference distribution. Patch-regime change inside the reference window violates exchangeability because balance-patch shifts the game-state distribution, which changes the within-player win/loss variance structure. Already cited in §4.4.5 line 385 as the CI method for aoestats + aoe2companion.
- **[WuCrespiWong2012]** — ICC estimator for binary outcomes under one-way random-effects ANOVA; supplies the specific estimator form applicable to the per-player win/loss target used in §4.4.5 and grounds the precision-axis argument (CI width) that complements the point-estimate-bias argument from the preceding three anchors. Already cited in §4.4.5 line 385 as the authority for the ANOVA-type ICC on binary outcomes.

Collectively these four sources supply the methodological argument: *patch-regime homogeneity is a prerequisite for consistent ICC point-estimation and CI construction under the one-way random-effects framework used in §4.4.5. Window-length comparability is orthogonal — it governs precision (CI width) rather than point-estimate consistency.* The spec §7 rule operationalizes this methodological constraint; the rule is not itself the authority.

### F4.5 proxy anchor (already in `thesis/references.bib`)

- **[Thorrez2024]** (bib line 144, HuggingFace URL `https://huggingface.co/datasets/EsportsBench/EsportsBench`) — EsportsBench benchmark of paired-comparison rating systems across 20 esports titles including SC2 with Aligulac-sourced data. Table 2 of the preprint reports Glicko-2 accuracy of 0.8013 on SC2 data (411,030 train matches, ~22,343 test matches). This is the closest academic calibration-independence proxy to the Aligulac FAQ's self-reported calibration claim. Already framed as such in §2.5.5 (line 183 existing [REVIEW] flag; audit cites §2.5.4 — on current chapter structure the relevant locus is §2.5.5 per PR-TG5a closure), §3.2.4 (line 77 existing [REVIEW] flag), and §3.5 Luka 3 (line 189). PR-5b propagates the same framing from flag-level to prose-level at §2.2.3, completing the F5.3 / F4.5 consistency pair.

No literature search is required — all anchors are already in the bib and already cited in neighbouring chapter sections. The exact 80.13% figure is flagged for Pass-2 PDF verification in all four locations with consistent hedging.

## Assumptions & Unknowns

- **Assumed:** The three F5.4 literature anchors (Nakagawa 2017, Gelman 2007, Ukoumunne 2003) support the claim that patch-regime homogeneity dominates window-length comparability for ICC estimation under the estimator used in §4.4.5. This is consistent with how they are already cited in §4.4.5 (chapter lines 383–387). If Pass-2 manual verification of the three papers uncovers a contrary claim, the defence is revised; for this PR the anchoring is taken as sound.
- **Assumed:** The Thorrez2024 Glicko-2 80.13% figure is accurate per Table 2 of the preprint. This figure is currently flagged for Pass-2 verification in three other chapter locations (§2.5.5 line 183, §3.2.4 line 77, §3.5 line 189); PR-5b inserts with the same hedge convention, so PR-5b does not introduce new verification burden — it distributes the existing burden consistently.
- **Unknown:** Whether a peer-reviewed secondary source exists that would strengthen the F5.4 defence with a specific statement about "patch-regime non-stationarity biases ICC" in a game-data context. Pass-2 manual literature review may surface such a source; if so, it can be added in a post-Pass-2 refinement without revising the PR-5b text.
- **Unknown:** Exact bib-to-chapter-line anchoring for the 80.13% figure. The value is not in the bib `note` field of `Thorrez2024` (bib line 148 notes "Evaluated 11 rating systems across 20 esports titles…" without the figure); the figure lives only in the preprint Table 2. PR-5b inserts with the same [REVIEW: verify Table 2] hedge used in the neighbouring locations.

## Gate Condition

Per-task gates documented inline at T01–T06 below. Aggregate:

- `git diff --stat` touches exactly 5 files: `thesis/chapters/02_theoretical_background.md` (F4.5 insertion), `thesis/chapters/04_data_and_methodology.md` (F5.4 rewrite), `thesis/WRITING_STATUS.md`, `thesis/chapters/REVIEW_QUEUE.md`, plus `pyproject.toml` + `CHANGELOG.md` for the version bump (7 files total including release files).
- No changes to `thesis/references.bib` (all anchors exist).
- No changes to `src/`, `reports/`, `sandbox/`, or `.claude/`.
- The existing [REVIEW: F5.3 Pass-2 audit — …] flag at chapter line 39 is reworded to document completion of the F4.5 proxy insertion and to mark the 80.13% figure for Pass-2 Table-2 verification (consistent with the other three locations).
- The existing [REVIEW: Pass-2 — patch-anchored vs. comparable-length framing …] flag at chapter line 207 is reworded to record the F5.4 literature anchoring and to acknowledge the sensitivity-axis caveat.
- Post-edit: planning-drift pre-commit hook passes (all 8 Cat F sections present in this plan); ruff/mypy N/A (no .py changes).

## Open Questions

1. **Pass-2:** Manual verification of Thorrez 2024 Table 2 exact value (0.8013 vs. rounded ~80%). Closes the [REVIEW] flag simultaneously in all four affected sections once resolved.
2. **Pass-2:** Whether a higher-signal literature anchor exists for the "patch-regime homogeneity dominates window-length comparability" claim than the three sources used here. Nakagawa 2017 / Gelman 2007 / Ukoumunne 2003 are used in §4.4.5 for different (but related) methodological questions; a source more directly about sampling-window non-stationarity in ICC estimation would be ideal.
3. **Post-Pass-2:** §3.2 → §3.1.3 swap (F5.6 follow-up) remains deferred per prior plan; PR-5b does not interact with those flags.

## Scope

### What this PR covers

1. **F5.4 — §4.1.3 "Ramy okna referencyjnego" literature anchoring.** Rewrite the defence paragraph at `thesis/chapters/04_data_and_methodology.md:207` to lead with the methodological argument, reframed on two orthogonal axes: (a) point-estimate consistency — patch-regime homogeneity is a primary prerequisite for unbiased ICC point estimation, and (b) precision (CI width) — co-first-order but *bounded, not optimized* by the single-patch constraint (the precision penalty of a shorter window is consciously accepted in exchange for bias-consistency). The external, non-tuning anchor for patch 66692 specifically is data availability: patch 66692 is the sole patch fully covering the pre-registration reference window [2022-08-29, 2022-10-27] (123,367 matches within window / 241,981 across the full patch cycle 2022-08-29 → 2022-12-08 per `reports/specs/01_05_preregistration.md:580–582`); the 9-week window width corresponds to the number of weekly crawler files ingested within the spec §7 window, not to the patch calendar cycle. Window-length asymmetry is thus not a "second-order" concern on a unified hierarchy; it is orthogonal to point-estimate bias while remaining co-first-order for precision, and is addressed by a distinct design mechanism (single-patch window sizing with the precision trade-off acknowledged explicitly and CI widths reported per-corpus in §4.4.5). Cite [Nakagawa2017, Gelman2007, Ukoumunne2003, WuCrespiWong2012]. Retain the spec §7 + §11 reference as the operationalization anchor, not as the authority.
2. **F4.5 — §2.2.3 Thorrez academic-proxy insertion.** Insert a comparator sentence immediately after the existing Aligulac calibration sentence at `thesis/chapters/02_theoretical_background.md:39` citing [Thorrez2024] Glicko-2 80.13% on SC2 Aligulac data as the closest academic calibration-proxy benchmark. Preserve the calibration-vs-accuracy distinction from PR-5a (F5.3). Reword the existing [REVIEW] flag from "insertion deferred to PR-5b" to "F4.5 proxy inserted; Pass-2 verifies 80.13% exact value per Thorrez 2024 Table 2".
3. **REVIEW_QUEUE + WRITING_STATUS updates** documenting both edits per `.claude/rules/thesis-writing.md` end-of-draft checklist.

### What this PR does NOT cover

- **No new bib entries.** All literature anchors (Nakagawa2017, Gelman2007, Ukoumunne2003, Thorrez2024) exist.
- **No §4.4.5 rewrite.** §4.4.5 already cites all three F5.4 anchors; PR-5b does not touch §4.4.5 prose.
- **No §2.5.5 / §3.2.4 / §3.5 rewording.** The Thorrez-proxy framing in those three locations was established in PR-TG3 + PR-TG5a and is not re-litigated here.
- **No F5.6 Demšar §3.2 → §3.1.3 swap.** Remains deferred to post-Pass-2 once readable PDF confirms location.
- **No TG6 items** (PR-6a for F6.1–F6.3 science-lite, PR-6b for F6.4–F6.12 chore) — separate PRs.
- **No data/feature/model work.** Category F science-lite; `.claude/scientific-invariants.md` §Invariants #1, #3, #4, #5 are N/A; #6, #7, #8, #9, #10 are N/A; #2 applies only to the sense that all cited sources already have DOI/URL anchors.

### Binding discipline

- **Science-lite PR** with tight discipline: two prose insertions (one rewrite, one addition), both anchored to literature already in the bib. No new claims; all reframings apply existing audit findings to the chapter prose.
- **Polish academic register** throughout. Use the existing §4.4.5 vocabulary ("observed-scale ICC", "one-way random-effects ANOVA", "cluster-bootstrap CI") where applicable to keep terminology consistent across chapter 4 sections. Use the existing §2.5.5 vocabulary ("Glicko-2", "paired-comparison rating systems", "referencyjny zbiór benchmarków") for consistency across chapter 2 sections.
- **ISO dates** (yyyy-mm-dd) in any new prose. No localized Polish-idiomatic date forms (per `feedback_iso_date_format.md`).
- **No [UNVERIFIED] flags added** — the 80.13% hedge uses [REVIEW] consistent with existing pattern. [UNVERIFIED:] is reserved for numbers that cannot be traced; 80.13% traces to Thorrez 2024 Table 2.
- **3-round adversarial cap symmetric** (per `feedback_adversarial_cap_execution.md`): `/critic` max 3 iterations + `reviewer-adversarial` Mode A once + Mode C once. If Mode A or Mode C returns REVISE, max 1 revision cycle per mode before landing (symmetric to the /critic 3-iter cap).
- **Post-merge planning purge**: this plan overwrites the prior PR-5a plan; after PR-5b merges, the next TG (PR-6a) plan will overwrite this one in turn.

## Execution Steps

### T01 — F5.4 §4.1.3 literature-anchored rewrite

**File:** `thesis/chapters/04_data_and_methodology.md` (paragraph at line 207, inside §4.1.3 "Asymetria korpusów — ramy porównawcze").

**Action:** Rewrite the "Ramy okna referencyjnego" paragraph as follows. Preserve the opening factual statement about the two window lengths. Restructure so that the methodological argument (patch-regime homogeneity → within-cluster stationarity → consistent ICC estimation) precedes the operationalization citation (spec §7 + §11). Add citations to [Nakagawa2017, Gelman2007, Ukoumunne2003] explaining why patch homogeneity dominates window-length symmetry for this estimator. Explicitly acknowledge the sensitivity axis (different windows would produce different CI widths, not biased point estimates). Replace the existing [REVIEW] flag with a reworded version noting that F5.4 is now anchored in literature and that Pass-2 may add a more direct non-stationarity-in-ICC source if surfaced.

**Proposed new paragraph structure (writer-thesis may refine within this scope):**

> **Ramy okna referencyjnego.** Trzy korpusy używają dwóch długości okien referencyjnych: sc2egset oraz aoe2companion — czteromiesięcznego okna 2022-08-29 → 2022-12-31, aoestats — dziewięciotygodniowego okna single-patch 2022-08-29 → 2022-10-27 obejmującego wyłącznie okres patcha 66692. Wartość dziewięciu tygodni odpowiada liczbie cotygodniowych plików dostarczonych przez crawler aoestats w obrębie okna pre-rejestracyjnego i jest pochodną liczby plików ingerowanych, nie kalendarzowego cyklu życia patcha — pełny cykl patcha 66692 obejmuje 2022-08-29 → 2022-12-08 (~14 tygodni); specyficzna szerokość okna jest zatem sądem eksperckim popartym kryterium single-patch, nie niezależnym faktem empirycznym. Zewnętrznym ograniczeniem niezależnym od decyzji projektowej jest natomiast sam wybór kotwicy patchowej: patch 66692 jest jedynym patchem w pełni pokrywającym pre-rejestracyjne okno obserwacji [2022-08-29, 2022-10-27] (123 367 meczów wewnątrz okna na 241 981 meczów w całym cyklu życia patcha; `reports/specs/01_05_preregistration.md:580–582`), co czyni dobór kotwicy ograniczeniem dostępności danych, nie parametrem strojenia modelu. Asymetria wynika z metodologicznego priorytetu jednorodności rozkładu odniesienia, lecz formułowanego na dwóch ortogonalnych osiach — nie jako pojedyncza hierarchia. Po pierwsze, oś spójności punktowej estymaty: estymatory ICC typu ANOVA dla binarnych outcome'ów [WuCrespiWong2012] oraz ich przedziały ufności obliczane cluster-bootstrapem [Ukoumunne2003] są spójne wyłącznie przy stacjonarności wewnątrzklastrowej w obrębie okna referencyjnego; zmiana reżimu patchowego w środku okna narusza tę stacjonarność, ponieważ patch balansujący modyfikuje rozkład stanów gry, a w konsekwencji strukturę wariancji międzymeczowej per-gracz [Nakagawa2017, §2.2]. Identyfikowalność punktowej estymaty ICC wymaga stabilnej struktury klastrowej w obrębie zbioru odniesienia [Gelman2007, §11–12], a nie zadanej minimalnej długości okna — w tym sensie długość okna jest dla biasu punktowego co najwyżej drugorzędna. Po drugie, oś precyzji: szerokość CI dla ICC zależy od efektywnej liczby klastrów oraz rozkładu wariancji wewnątrzklastrowej, i zmienia się między oknami różnej długości przy zachowanej patch-homogeniczności; precyzja jest współrzędnie pierwszorzędną osią interpretacji ICC i jest *ograniczona, nie optymalizowana* przez konstrukcję single-patch — kara precyzji krótszego okna jest świadomie akceptowana w zamian za spójność biasu punktowego (jednorodność patchową), a szerokości CI są raportowane per-korpus w §4.4.5. Rozciągnięcie okna aoestats przez granicę patcha do pełnych czterech miesięcy wprowadziłoby non-stationarity patchową, której estymator nie kompensuje; konstrukcja single-patch jest zatem pierwszorzędową decyzją metodologiczną dla biasu punktowego i akceptowanym trade-offem dla precyzji, nie post-hoc korekcją. Pre-rejestracja §7 oraz §11 W3 ARTEFACT_EDGE (`reports/specs/01_05_preregistration.md`) operacjonalizuje tę decyzję jako zablokowany projektowo wybór; metodologiczny argument pozostaje aktualny niezależnie od spec-local operacjonalizacji. Szerokości CI w Tabeli 4.7 (§4.4.5) nie są ściśle porównywalne międzykorpusowo, ponieważ zależą zarówno od długości okna, jak i od liczby klastrów (152 / 744 / 5 000 dla sc2egset / aoestats / aoe2companion) — „kara precyzji" krótszego okna aoestats jest w tym sensie jakościowym zobowiązaniem projektowym, a nie ilościowo zademonstrowanym trade-offem na poziomie obecnych danych, ponieważ efekt długości okna jest w Tabeli 4.7 splątany z efektem liczby klastrów. [REVIEW: Pass-2 — F5.4 audit anchoring; brak bezpośredniego peer-reviewed źródła dla twierdzenia o biasie non-stationarity-patchowej na estymator ICC dla binarnych outcome'ów; cztery kotwice [Nakagawa2017, Gelman2007, Ukoumunne2003, WuCrespiWong2012] są użyte **analogicznie** z §4.4.5 (linie 383–387), gdzie te same prace ugruntowują wybór estymatora (WuCrespiWong2012), metodę CI (Ukoumunne2003), identyfikowalność punktową (Gelman2007) oraz skalę linka (Nakagawa2017) — każde w innym, ale pokrewnym kontekście metodologicznym. Pass-2 weryfikuje istnienie bezpośredniego źródła.]

**Gate:**
- Four new citations added inline: `[Nakagawa2017, §2.2]`, `[Gelman2007, §11–12]`, `[Ukoumunne2003]`, `[WuCrespiWong2012]`. The fourth citation is authorized by inclusion in §Literature Context as a fourth anchor; it grounds the precision-axis (CI width) portion of the orthogonal-axes reframe.
- Spec reference (`reports/specs/01_05_preregistration.md` §7 + §11 W3 ARTEFACT_EDGE) retained but reframed as operationalization, not authority; the 9-week window width is explicitly attributed to the crawler-file count (expert judgment anchored by single-patch criterion), the 14-week patch-66692 calendar cycle is cited as a distinct fact, and the external non-tuning anchor is patch-uniqueness (patch 66692 is the sole patch covering the reference window).
- The existing [REVIEW] flag on chapter line 207 is replaced with the new [REVIEW: F5.4 audit anchoring …] flag (single flag; flag count on §4.1.3 stays at 1, same as pre-PR — verified by Grep of `\[REVIEW` within §4.1.3 span lines 163–208 returning exactly one hit at line 207).
- Word-count delta: current paragraph ~834 characters → proposed paragraph ~3,600 characters (net delta ~+2,770 characters). The expansion is intentional and within editorial scope: it accommodates (a) the orthogonal-axes reframe with four literature anchors [Nakagawa2017, Gelman2007, Ukoumunne2003, WuCrespiWong2012], (b) the honest attribution of the 9-week value to the crawler-file count (not the patch calendar cycle) plus the 14-week patch-66692 cycle fact cited to `reports/specs/01_05_preregistration.md:580–582`, (c) the external patch-uniqueness justification (patch 66692 is the only patch fully covering the reference window; 123,367 matches within window, 241,981 across the full patch cycle), and (d) the explicit precision-is-bounded-not-optimized trade-off clause resolving R21. Writer-thesis may trim within ±200 chars while preserving all four lettered load-bearing claims.

### T02 — F4.5 §2.2.3 Thorrez proxy insertion

**File:** `thesis/chapters/02_theoretical_background.md` (paragraph at line 39, inside §2.2.3 "Scena zawodowa").

**Action:** Insert one comparator sentence immediately after the existing Aligulac calibration sentence (the one ending with "…której obecnie brak."). Reword the trailing [REVIEW] flag to document F4.5 completion and retain the Pass-2 verification hedge for the 80.13% figure.

**Proposed insertion (single sentence; writer-thesis may refine within this scope):**

> W akademickim benchmarku EsportsBench [Thorrez2024] system Glicko-2 — z rodziny paired-comparison rating systems, z której wywodzi się także bespoke algorytm Aligulac (szerzej omówiony w §2.5.4) — osiąga trafność 80,13% na 411 030 meczach SC2 pochodzących z Aligulac (ang. *train subset*), co stanowi niezależną akademicką miarę rzędu wielkości dla rankingowej predykcji w tej populacji; miara ta nie potwierdza ani nie falsyfikuje twierdzenia Aligulac FAQ o ~80% kalibracji probabilistycznej (rozróżnienie kalibracja vs. trafność klasyfikacyjna pozostaje zachowane zgodnie z framingiem ustanowionym w PR-5a, F5.3).

**Proposed replacement [REVIEW] flag (replaces the existing F5.3/deferral flag at line 39):**

> [REVIEW: F4.5 Pass-2 audit — insercja akademickiego proxy Thorrez2024 Glicko-2 80,13% na danych SC2 z Aligulac zgodnie z framingiem §2.5.5 oraz §3.2.4 (gdzie ta sama wartość jest już cytowana z analogicznym hedge'em); Pass 2 weryfikuje dokładną wartość z Tabeli 2 preprintu Thorrez 2024 oraz — istotniejsze — sprawdza, czy tabela zawiera wiersz dla algorytmu Aligulac (EsportsBench ocenia 11 systemów rankingowych); jeśli tak, preferowanym akademickim proxy jest Aligulac-on-Aligulac, a nie Glicko-2-on-Aligulac. Zamknięcie flagi w czterech loci (§2.2.3, §2.5.5, §3.2.4, §3.5) jednocześnie wymaga potwierdzenia zarówno dokładnej wartości, jak i odpowiedniego wyboru wiersza benchmarku. Wartości "~80%" (miara kalibracji Aligulac FAQ — etykieta binu kalibracyjnego) oraz "80,13%" (trafność klasyfikacyjna Glicko-2 w Thorrez 2024) mierzą dwie różne wielkości; sąsiedztwo liczbowe jest zbiegiem okoliczności, nie walidacją — rozróżnienie kalibracja vs. trafność klasyfikacyjna per FAQ Aligulac pozostaje zachowane.]

**Gate:**
- One new inline citation: `[Thorrez2024]`.
- The proxy sentence is ≤ 2 sentences (insertion is bounded). Does not exceed the chore-violation complaint raised in PR-5a iter 1.
- The [REVIEW] flag is reworded but not removed. Flag count on §2.2.3 stays at 1 (one reworded flag), same as post-PR-5a.
- The calibration-vs-accuracy distinction established in PR-5a is preserved verbatim in the new proxy sentence.

### T03 — REVIEW_QUEUE.md update

**File:** `thesis/chapters/REVIEW_QUEUE.md`.

**Action:** Append a 2026-04-20 note to both the §2.2 and §4.1.3 rows documenting PR-5b edits, consistent with the PR-TG5a/PR-TG4/PR-TG3 convention (each row carries bolded dated entries for each pass of revision). No structural changes; only the notes columns are touched.

**Gate:**
- Both rows (§2.2 and §4.1.3) carry a new `**2026-04-20 (PR-TG5b):**` bolded note.
- Flag counts updated if writer-thesis net-changes any flag; net change is zero if the [REVIEW] flags are reworded in place as planned.
- No other rows touched.

### T04 — WRITING_STATUS.md update

**File:** `thesis/WRITING_STATUS.md`.

**Action:** Append a 2026-04-20 note to both the §2.2 and §4.1.3 rows (same bolded-dated-entry convention as REVIEW_QUEUE).

**Gate:**
- Both rows carry a new `**2026-04-20 (PR-TG5b):**` entry.
- No status transitions (both rows were already DRAFTED and remain DRAFTED).

### T05 — CHAPTER_4_DEFEND_IN_THESIS.md cross-reference (optional, within scope)

**File:** `planning/CHAPTER_4_DEFEND_IN_THESIS.md`.

**Action:** If the file tracks Residual #1 (§4.1.3 reference-window defence) as OPEN, update to reflect PR-5b closure: Residual #1 now anchored to [Nakagawa2017, Gelman2007, Ukoumunne2003]; close if applicable. If the residual tracker does not have this format or the file is not touched by recent PRs, skip without updating.

**Gate:**
- If updated: one bolded dated entry matching T03/T04 convention.
- If skipped: writer-thesis notes the skip in the Chat Handoff Summary.

### T06 — Version bump + CHANGELOG

**Files:** `pyproject.toml`, `CHANGELOG.md`.

**Action:**
- Bump `version = "3.34.0"` to `version = "3.35.0"` in `pyproject.toml`.
- Move existing `[Unreleased]` entries (if any non-empty) to a new `[3.35.0] — 2026-04-20 (PR #<TBD>: docs/thesis-pass2-tg5b-circular-spec-thorrez-proxy)` heading.
- Add new `[Unreleased]` block with empty `### Added / Changed / Fixed / Removed` headers.
- Populate `[3.35.0]` with a Changed-section entry: "docs(thesis): Pass-2 PR-5b — F5.4 §4.1.3 reference-window defence anchored to [Nakagawa2017, Gelman2007, Ukoumunne2003]; F4.5 §2.2.3 Thorrez2024 Glicko-2 80.13% academic-proxy insertion; REVIEW_QUEUE + WRITING_STATUS entries; no bib changes."

**Gate:**
- `pyproject.toml` version line is exactly `version = "3.35.0"`.
- CHANGELOG `[Unreleased]` block is empty (has the four headers but no bullets).
- CHANGELOG `[3.35.0]` block has at least one entry under `### Changed`.

## File Manifest

Exactly these files are modified:

| File | Nature of change | Lines affected |
|---|---|---|
| `thesis/chapters/04_data_and_methodology.md` | F5.4 §4.1.3 paragraph rewrite | line 207 (one paragraph) |
| `thesis/chapters/02_theoretical_background.md` | F4.5 §2.2.3 proxy sentence insertion + flag rewording | line 39 (one paragraph) |
| `thesis/chapters/REVIEW_QUEUE.md` | Two bolded dated notes | §2.2 row + §4.1.3 row |
| `thesis/WRITING_STATUS.md` | Two bolded dated notes | §2.2 row + §4.1.3 row |
| `planning/CHAPTER_4_DEFEND_IN_THESIS.md` | Residual #1 closure cross-reference (optional) | one bolded dated note |
| `pyproject.toml` | Version bump 3.34.0 → 3.35.0 | single line |
| `CHANGELOG.md` | [Unreleased] → [3.35.0] release entry | two block swaps |
| `planning/current_plan.md` | This file (overwrites prior PR-5a plan) | whole file |

No other files are modified. The `.github/tmp/commit.txt` and `.github/tmp/pr.txt` artifacts are created during commit/PR stages and deleted at cleanup per `feedback_pr_body_cleanup.md`.

## Dispatch sequence

1. **This plan written** (you are reading it). Planning-drift hook validates all 8 Cat F sections present.
2. **`/critic planning/current_plan.md`** — max 3 iterations. Parent orchestrates 4 critics → merger → user-subset (for autonomous flow, parent applies RECOMMENDED subset each iteration) → writer-thesis for plan revision if needed. Stop when merger returns CLEAN or iteration 3 exhausted.
3. **Iteration-3 residual-BLOCKER branch.** If iteration 3 completes with residual BLOCKERs, halt and return choice to user (land-as-is with BLOCKERs flagged in PR body vs open a follow-up PR per `/critic.md` cleanup step 3) **before** proceeding to Mode A. Do not proceed to Mode A with unresolved BLOCKERs without explicit user authorization; this resolves the §Binding discipline / §Dispatch sequence incompatibility flagged by logical-L08.
4. **`reviewer-adversarial` Mode A** — one run; writes `planning/current_plan.critique.md`. If verdict is REVISE: apply minor revisions and re-run Mode A once (symmetric 1-revision cap); if REDESIGN: halt and return to planner (escalate to user per `feedback_adversarial_cap_execution.md`). If PROCEED: continue.
5. **`writer-thesis`** — dispatched against `planning/current_plan.md` with instruction to execute T01–T06. Writer emits Chat Handoff Summary per `.claude/rules/thesis-writing.md`. No commit yet.
6. **`reviewer-adversarial` Mode C** — one run; post-draft stress test; emits verdict in chat. If REVISE: apply once; if REDESIGN: halt. If PROCEED: continue.
7. **Pre-commit validation** — planning-drift, ruff (N/A no .py), mypy (N/A no .py). Only planning-drift will fire; it must pass.
8. **Commit** — `git commit -F .github/tmp/commit.txt` (heredocs break in zsh per `feedback_git_commit_format.md`).
9. **PR** — `gh pr create --body-file .github/tmp/pr.txt` (PR body to file per `feedback_pr_body_file.md`).
10. **Merge** — `gh pr merge --merge --delete-branch` (confirm with user before destructive operations if unclear — but this is the standard per-PR closing per repo convention).
11. **Cleanup** — `rm .github/tmp/pr.txt .github/tmp/commit.txt` per `feedback_pr_body_cleanup.md`.
12. **Halt** after merge — report to user; do NOT continue autonomously to PR-6a without explicit authorization.

## Risk mitigation

- **Risk: writer-thesis softens the F5.4 methodological argument into yet another "spec says so" restatement.** Mitigation: T01 gate specifies that the new paragraph must lead with the methodological argument (stacjonarność wewnątrzklastrowa → estymator spójność), cite the three literature anchors inline with chapter/§ specificity, and demote the spec reference to "operacjonalizacja" framing. Mode A and Mode C both catch this defect if it slips through /critic.
- **Risk: the 80.13% figure is off (e.g., 0.7983 or 0.8124) and the PR ships a wrong number.** Mitigation: the [REVIEW: Pass-2 verify Table 2] flag is preserved. Pass-2 PDF verification closes the flag simultaneously in all four locations (§2.2.3, §2.5.5, §3.2.4, §3.5). The rounding claim in the [REVIEW] flag is conservative — "~80%" is consistent with any value in [79.5%, 80.5%], which captures any plausible correction.
- **Risk: the F4.5 insertion at §2.2.3 inadvertently duplicates §2.5.5 / §3.2.4 prose.** Mitigation: the T02 proposed sentence is scoped narrowly to "closest academic proxy for Aligulac calibration" — it references Thorrez by bib key, states the 80.13% figure with 411k context, and explicitly distinguishes calibration (Aligulac FAQ) from classification accuracy (Thorrez Glicko-2). §2.5.5 line 177 already frames Thorrez as the reference-zbiór benchmark; §3.2.4 line 77 frames it as the rating-baseline context. §2.2.3's framing is narrower (local calibration-proxy anchor inside the Aligulac-discussion paragraph) and does not duplicate either neighbour.
- **Risk: planning-drift hook fails because the plan is missing a Cat F section.** Mitigation: this plan file explicitly has all 8 required sections (Problem Statement, Literature Context, Assumptions & Unknowns, Gate Condition, Open Questions, Scope, Execution Steps, File Manifest) as ## headings at the top level. Verified pre-commit by the author.
- **Risk: the 3-iteration /critic cap is exhausted with remaining BLOCKERs.** Mitigation: land as-is with residual BLOCKERs flagged in PR body, OR open a follow-up PR for the remaining items (per /critic.md cleanup step 3). User decides between the two.

## Non-negotiable invariants during execution

- **I2 (reproducibility):** All four literature anchors (Nakagawa2017, Gelman2007, Ukoumunne2003, Thorrez2024) have DOI, ISBN, or URL in the bib. No "personal communication."
- **I7 (no magic numbers):** The 80.13% figure traces to Thorrez 2024 Table 2 (flagged for Pass-2 verification, consistent with three other loci). The `2022-08-29 → 2022-10-27` and `2022-08-29 → 2022-12-31` dates trace to `reports/specs/01_05_preregistration.md` §7 (already cited). The patch identifier `66692` traces to the same spec.
- **I8 (raw-data immutability):** No changes to `reports/`, `src/`, `data/`.
- **Honesty clause:** If Mode A or Mode C returns REDESIGN, halt and escalate. Do not silently paper over methodological defects to ship the PR.
- **No thesis prose without a source:** Every new claim in T01 and T02 has an inline literature citation. No [NEEDS CITATION] flags planted; no un-cited claims.

## Post-merge

- Update `thesis/reviews_and_others/pass2_status.md` to reflect PR-5b merge (version 3.35.0; F5.4 + F4.5 closed; PR-6a next).
- Halt and ask user before starting PR-6a.
