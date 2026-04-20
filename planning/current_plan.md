---
category: F
branch: docs/thesis-pass2-tg6b-bib-hygiene-minor-prose
date: 2026-04-20
planner_model: claude-opus-4-7
---

# Plan: TG6-PR-6b — §2.2.4 + §3.3.1 + §3.4.4 + bib hygiene (F6.4-F6.10 + F6.12; F6.11 already landed in TG4)

**Category:** F (Thesis — chore; bib hygiene + minor prose annotations with literature-verification hedges)
**Branch:** `docs/thesis-pass2-tg6b-bib-hygiene-minor-prose`
**Base:** `master` (at `48d557f6`, post-PR #194 merge; version 3.36.0)
**Audit source:** `thesis/reviews_and_others/pass2_dispatch.md` Task Group 6 items F6.4 (line 187) / F6.5 (line 189) / F6.6 (line 191) / F6.7 (line 193) / F6.8 (line 195) / F6.9 (line 197) / F6.10 (line 199) / F6.12 (line 203); scope inheritance at `thesis/reviews_and_others/pass2_status.md` §PR-6b (lines 46–60). F6.11 is already resolved in TG4 (PR #190) per pass2_status.md:57.

## Problem Statement

Pass-2 audit Task Group 6 second half (F6.4 through F6.12) packages nine chore-tier findings — bibliographic entry corrections plus minor prose annotations flagging primary-source verification — into a single chore PR. Seven items are substantive chore work; two are skip/defer:

1. **F6.4 — §2.2.4 Vinyals2017 replacement for 22.4 loops/sec citation** (currently Liquipedia_GameSpeed). Per pass2_dispatch.md:187, Vinyals et al. 2017 SC2LE is the peer-reviewed source. Vinyals2017 bib exists at line 16. **WebFetch 2026-04-20 could not verify the 22.4 claim in the SC2LE abstract or binary PDF download; [REVIEW] flag planted for Pass-2 PDF read** per the honesty discipline from PR-5b (F5.4 anchor reliance) + PR-5a (F5.6 Demšar).
2. **F6.5 — §2.2.4 add 2013-05-07 patch date for s2protocol 2.0.8**. Liquipedia confirms Patch 2.0.8 NA release **2013-05-07** (EU/KR release 2013-05-08, SEA 2013-05-06; the audit cites 7 May 2013 consistent with NA first-release). Add inline date in the existing §2.2.4 paragraph. **Citation:** reuse the existing `[BlizzardS2Protocol]` bibkey as the grey-literature anchor for this patch date — no new bib entry (keeps `NO new bib entries` gate intact, eliminates the non-existent `Liquipedia_SC2Patches` bibkey risk from earlier drafting).
3. **F6.6 — §2.5.5 + §3.2.4 EsportsBench dataset versioning footnote**. §3.5 Luka 3 (line 189) already notes "v8.0 (2025-12-31)"; §2.5.5 + §3.2.4 reference EsportsBench without any version. Add brief version-anchor parenthetical to both.
4. **F6.7 — §3.3.1 Yang 2017 Dota paragraph clarifications**. Treated asymmetrically per R5 / F6.1 symmetry: (a) "9:1 split is random, not temporal" qualitative disclaimer is added to thesis prose with a single [REVIEW] flag (audit pass2_dispatch.md A8 line 373–374 primary-source reading; Pass-2 PDF confirmation); (b) Yang's own LR on hero features alone = 60.07% vs the 58.69% currently cited (which audit says is Kinkade et al. reimplemented) is **deferred to REVIEW_QUEUE §3.3 row only**, not added to prose — mirroring the F6.1 precedent where unverifiable audit claims stayed out of the chapter. **WebSearch 2026-04-20 did NOT surface 60.07% in search results**, which grounds the REVIEW_QUEUE deferral.
5. **F6.8 — `thesis/references.bib:500` Silva2018LoL add pages 639–642 + ISSN**. **WebSearch 2026-04-20 VERIFIED** pages 639–642 via sbgames.org PDF URL. ISSN 2179-2259 per audit is standard SBGames Proceedings ISSN; not independently verified but low-risk bibliographic metadata.
6. **F6.9 — §3.4.4 Xie 2020 R²-vs-accuracy flag**. Current §3.4.4 (chapter line 161) states "trafność poniżej 2% niezależnie od konfiguracji cech — obserwacja sama w sobie interesująca, sugerująca silną nieliniowość" which the audit pass2_dispatch.md:197 + A12 line 395–398 identifies as likely an R² misreported as accuracy (XGBRegression + binary target + 2% value — impossible as accuracy, plausible as R²). Add one sentence flagging this terminological-error hypothesis per audit.
7. **F6.10 — `thesis/references.bib:95` Porcpine2020EloAoE URL correction + r=0.96 bin-aggregation caveat**. Current bib URL `https://porcpine1967.github.io/aoe2/elo.html` returns **HTTP 404** (WebFetch 2026-04-20). Correct URL is `https://porcpine1967.github.io/aoe2_comparisons/elo/` (audit) which WebFetch confirms is live and serves the analysis. Additionally, add to §3.4.4 (chapter line 163) that r=0.96 is on bin-level aggregated win-percentages, not raw binary matches — inflation vs raw binary signal.
8. **F6.11 — SKIP** (already resolved in TG4/PR #190: Elbert bib "Stein Nora→Nikolai" and "Schenk Amadeus→Alicia" corrections verified at bib line 74 area).
9. **F6.12 — SKIP** per audit ("only if no tooling regression"). Adopting `> [REVIEW: …]` blockquote convention for flags would require re-typesetting all existing flags; scope creep for a chore PR and risks regressing markdown tooling. Defer indefinitely as stylistic polish.

Together, PR-6b lands 7 substantive chore edits (F6.4–F6.10) spanning §2.2.4, §2.5.5, §3.2.4, §3.3.1, §3.4.4, and `thesis/references.bib`. No new bib entries; two existing bib entries are **edited** (Silva2018LoL pages+ISSN; Porcpine2020EloAoE URL+note). Everything else is prose annotation.

## Literature Context

### Verified-against-primary-source (WebSearch/WebFetch 2026-04-20)

- **[Silva2018LoL]** pages 639–642 — VERIFIED via `sbgames.org/sbgames2018/files/papers/ComputacaoShort/188226.pdf` (PDF path contains paper number 188226; page range 639–642 confirmed via Semantic Scholar + ResearchGate metadata).
- **[Porcpine2020EloAoE]** URL `porcpine1967.github.io/aoe2_comparisons/elo/` — VERIFIED live (WebFetch 2026-04-20 returned content describing the Elo analysis + linking to GitHub repo `github.com/porcpine1967/aoe2_comparisons`). Current bib URL `porcpine1967.github.io/aoe2/elo.html` returned HTTP 404.
- **Patch 2.0.8 NA release 2013-05-07** — VERIFIED via Liquipedia `liquipedia.net/starcraft2/Patch_2.0.8` (NA: May 7, 2013; EU/KR: May 8; SEA: May 6). The audit's "7 May 2013" matches NA release.

### Audit-claimed-but-not-independently-verified (flagged as [REVIEW])

- **Vinyals2017 SC2LE stating "22.4 (at 'fast speed') times per second"** — UNVERIFIED. Abstract page (arxiv.org/abs/1708.04782) does NOT mention the figure; full PDF (arxiv.org/pdf/1708.04782) returned as binary and not readable via WebFetch. Audit pass2_dispatch.md:187 and A16 line 415–417 assert SC2LE explicitly contains this value. PR-6b proceeds with citation substitution BUT plants [REVIEW: F6.4 Pass-2 verify] flag.
- **Yang2017 9:1 split is random not temporal; Yang's own LR hero-features-only = 60.07%** — UNVERIFIED. Audit pass2_dispatch.md:193 + A8 line 373–374 assert this as PDF-read finding. WebSearch surfaces 58.69/71.49/93.73% but NOT 60.07%. PR-6b treats the two audit claims asymmetrically: (a) the qualitative "random-not-temporal 9:1 split semantics" clarification is planted in prose with a single [REVIEW: F6.7 Pass-2 verify] flag — low-stakes, retractable as one sentence if Pass-2 contradicts; (b) the numeric reclassification (58,69% = Kinkade reimplementation vs Yang's own LR = 60,07%) is **deferred to REVIEW_QUEUE only**, mirroring the F6.1 precedent where unverifiable audit claims stayed out of thesis prose. This keeps prose defensibility symmetric with F6.1.

### Existing bib entries referenced (no edits, just citation reuse)

- **[Vinyals2017]** (bib line 16) — arXiv:1708.04782; used for F6.4 citation substitution.
- **[Thorrez2024]** (bib line 144) — EsportsBench; used for F6.6 version-footnote anchor.
- **[Yang2017Dota]** (bib line 477) — arXiv:1701.03162; cited in §3.3.1.
- **[Xie2020MediumAoE]** (bib line 85) — Medium grey literature; referenced in §3.4.4.

## Assumptions & Unknowns

- **Assumed:** The audit's pass2_dispatch.md Appendix-A/B-level claims (A8 Yang 60.07%; A16 SC2LE 22.4; A17 Patch 2.0.8 tracker events; A13 Porcpine bin-aggregation; A12 Xie R²-vs-accuracy) are accurate primary-source reads. The PR plants [REVIEW] flags on the TWO claims that WebSearch/WebFetch could not independently corroborate (F6.4 Vinyals 22.4; F6.7 Yang 60.07%). The other five (F6.5 patch date; F6.6 versioning; F6.8 Silva pages; F6.9 Xie R² hypothesis; F6.10 Porcpine URL + bin-aggregation) are either verified by this PR's independent verification (F6.5, F6.8, F6.10 URL) or are hypothesis-framing annotations that do not require primary-source proof (F6.9 is explicitly worded as a hypothesis).
- **Assumed:** ISSN 2179-2259 for SBGames Proceedings is the standard ISSN for the Brazilian Symposium on Computer Games and Digital Entertainment series. Audit provides this; not independently verified. Low-risk metadata field.
- **Assumed:** The `[REVIEW]` flag pattern from prior PRs (F5.4 literature anchoring + F5.6 Demšar section + F6.1 [NEEDS CITATION]) is the right hygiene precedent for the two unverified audit claims in this PR. Pattern: flag explicitly states what is unverified, names the Pass-2 closure mechanism (PDF read), and acknowledges the specific queries already attempted.
- **Unknown:** Whether F6.12 (`> [REVIEW:]` blockquote convention) would cause any tooling regression. Audit explicitly conditions F6.12 adoption on "no tooling regression" (pass2_dispatch.md:203). PR-6b **DEFERS F6.12** entirely — the repo's `grep [REVIEW` patterns used in prior PRs (e.g., PR-5b flag-count verification, PR-6a [NEEDS CITATION] vs [REVIEW:] distinction) assume non-blockquote inline form; introducing `> [REVIEW:]` risks breaking those grep patterns. Staying with existing inline convention is the conservative choice.

## Gate Condition

Per-task gates at T01–T09 below. Aggregate:

- **Git-diff-tracked files (7)** — `git diff --stat` touches exactly these and nothing else:
  1. `thesis/chapters/02_theoretical_background.md` — F6.4 §2.2.4 Vinyals substitution (existing line-49 [REVIEW] flag harvested and replaced — one flag total, not two); F6.5 §2.2.4 Patch 2.0.8 date parenthetical; F6.6-part-1 §2.5.5 EsportsBench versioning + [REVIEW].
  2. `thesis/chapters/03_related_work.md` — F6.6-part-2 §3.2.4 EsportsBench versioning + [REVIEW]; F6.7 §3.3.1 Yang (prose retains ONLY the qualitative random-not-temporal clarification with a single [REVIEW]; the 60.07% / Kinkade reclassification is deferred to REVIEW_QUEUE per F6.1 precedent); F6.9 §3.4.4 R²-vs-accuracy flag; F6.10-prose §3.4.4 bin-aggregation caveat.
  3. `thesis/references.bib` — F6.8 Silva2018LoL edit (pages + ISSN + bib-comment); F6.10 Porcpine2020EloAoE edit (URL + howpublished + note).
  4. `thesis/WRITING_STATUS.md` — dated notes on affected §-rows.
  5. `thesis/chapters/REVIEW_QUEUE.md` — dated notes on affected §-rows, incl. the F6.7 60.07%+Kinkade deferral entry.
  6. `pyproject.toml` — version 3.36.0 → 3.37.0.
  7. `CHANGELOG.md` — [Unreleased] → [3.37.0] entry.
- **Plan-meta file (1)** — `planning/current_plan.md` (this file; overwrites the PR-6a plan, tracked separately from the 7 git-diff-scope files).
- NO changes to `src/`, `reports/`, `sandbox/`, `.claude/`, chapters 1/4+.
- **ZERO new bib entries** (chore discipline); two existing entries edited: Silva2018LoL (add pages + ISSN + adjacent bib-comment); Porcpine2020EloAoE (fix URL + extend howpublished + note bin-aggregation caveat).
- Net new [REVIEW] flags (post-Mode-A revision): **5** total in prose — F6.5 Pass-2 defer of patch-notes date (standalone [REVIEW] in §2.2.4 paragraph per Mode A option (c)); F6.6 v7.0-vs-v8.0 release-status (×2, one at §2.5.5, one at §3.2.4, both with Mode-A-corrected v7.0 current / v8.0 planned wording); F6.7 Yang 9:1 random-not-temporal (qualitative only; 60.07%/Kinkade in REVIEW_QUEUE); F6.9 Xie R²-vs-accuracy. F6.4 Vinyals-added-as-secondary leaves the existing line-49 [REVIEW] flag intact (no new flag at that locus). ISSN 2179-2259 carries a `%` bib-comment hedge per F6.8 above the `@inproceedings{}` block (parser-safe placement per Mode A NOTE).
- Planning-drift pre-commit hook passes (all 8 Cat F sections present).

## Open Questions

1. **Pass-2:** Read Vinyals2017 SC2LE PDF section 3 or 4 (game engine description) to verify "22.4 times per second" is explicitly stated. Closes F6.4 [REVIEW] flag.
2. **Pass-2:** Read Yang2017Dota PDF to verify (a) 9:1 split is random not temporal — closes the in-prose F6.7 [REVIEW] flag; (b) LR on hero features alone = 60.07% and (c) whether 58.69% is Yang's own reimplementation of Kinkade et al. baseline — closes the REVIEW_QUEUE §3.3 deferral row (per R5 / F6.1 symmetry, the numeric reclassification is tracked in REVIEW_QUEUE only, not in prose, until Pass-2 PDF read confirms).
3. **Pass-2:** Confirm SBGames 2018 Proceedings ISSN is 2179-2259. Low priority; bib entry functional without ISSN.

## Scope

### What this PR covers

1. **F6.4 — §2.2.4 citation substitution** for 22.4 loops/sec: replace `[Liquipedia_GameSpeed]` with `[Vinyals2017]` at the specific 22.4-figure-citing location (chapter line 43, second sentence "co w przeliczeniu daje 22,4 game loops na sekundę rzeczywistą"). Keep Liquipedia citation only at the 5734/4096 fixed-point-constant location (same line, first half). Append [REVIEW: F6.4 Pass-2 verify Vinyals2017 PDF contains the 22.4 figure explicitly] inline.
2. **F6.5 — §2.2.4 patch date addition**: in the existing paragraph at chapter line 45 ("*Tracker events* (wprowadzone w protokole 2.0.8 [BlizzardS2Protocol])"), add the parenthetical "(Patch 2.0.8 wydany 2013-05-07 w regionie NA / 2013-05-08 EU/KR [BlizzardS2Protocol])" inline. Reuse the existing `[BlizzardS2Protocol]` bibkey as the grey-literature anchor for the patch date — no new bib entry required; no `Liquipedia_SC2Patches` bibkey is introduced.
3. **F6.6 — §2.5.5 + §3.2.4 EsportsBench versioning footnote**: add a version parenthetical to the first EsportsBench mention in §2.5.5 (chapter line 177) and §3.2.4 (chapter line 77), each accompanied by a `[REVIEW: F6.6 Pass-2 — reconcile v8.0 cutoff 2025-12-31 (current thesis wording per §3.5 Luka 3) vs audit-cited v1.0-v7.0 cutoff 2025-09-30 (pass2_dispatch.md:191); Pass 2 weryfikuje na HuggingFace release notes]` flag. Prose wording follows the existing §3.5 Luka 3 convention ("v8.0 (2025-12-31)") for internal consistency, but the [REVIEW] flag makes the audit-vs-§3.5 date-discrepancy (audit line 191 says "v1.0–v7.0 through cutoff 2025-09-30") explicit rather than silent. Exact per-locus wordings are specified in T02.
4. **F6.7 — §3.3.1 Yang paragraph clarification (prose) + REVIEW_QUEUE deferral (numeric)**: append to the existing paragraph at chapter line 91 exactly ONE qualitative sentence — "Protokół walidacji stosuje podział 9:1 dobierany losowo (nie temporalnie) [REVIEW: F6.7 Pass-2 verify arXiv:1701.03162 PDF — split semantics]". The numeric reclassification (58,69% = Kinkade reimplementation vs Yang's own LR = 60,07%) is moved to REVIEW_QUEUE §3.3 row ONLY (not into thesis prose), mirroring the F6.1 precedent where unverifiable audit claims were recorded in REVIEW_QUEUE rather than planted in the chapter. Rationale: WebSearch 2026-04-20 did NOT corroborate 60.07%; prose defensibility requires the numeric change to survive Pass-2 PDF read before landing.
5. **F6.8 — `thesis/references.bib:500` Silva2018LoL bib edit**: add two fields to the existing entry:
   ```
   pages = {639--642},
   issn  = {2179-2259},
   ```
   No other fields changed. Confirmed via WebSearch 2026-04-20.
6. **F6.9 — §3.4.4 Xie R²-vs-accuracy hypothesis flag**: append to the existing sentence at chapter line 161 (about "trafność poniżej 2%") one clarifying sentence: "Wartość poniżej 2% sugeruje, że opisywana wielkość to prawdopodobnie współczynnik determinacji R², nie trafność klasyfikacji — uzasadnienie: autor stosuje XGBRegression (model regresyjny), a wartość rzędu 2% jest niemożliwa jako trafność klasyfikacji binarnej (losowa baseline daje ≈50%), lecz jest plausibilnie małym R² dla zadania z bardzo wąskim rozkładem różnicy Elo [REVIEW: F6.9 Pass-2 verify Xie 2020 terminologii — oryginalny tekst Medium post]." Does NOT remove the existing sentence; adds the hypothesis annotation after.
7. **F6.10-bib — `thesis/references.bib:95` Porcpine2020EloAoE bib edit**:
   - Change `url` from `https://porcpine1967.github.io/aoe2/elo.html` to `https://porcpine1967.github.io/aoe2_comparisons/elo/` (verified live via WebFetch 2026-04-20; old URL returns 404).
   - Update `howpublished` from "GitHub Pages (community analysis)" to "GitHub Pages \\url{https://porcpine1967.github.io/aoe2_comparisons/} with code at \\url{https://github.com/porcpine1967/aoe2_comparisons}".
   - Extend `note` to document bin-aggregation inflation: "Community analysis; 908,940 matches from aoe2.net API; r=0.96 computed on bin-aggregated win-percentages per rating-difference bin — correlation is inflated relative to raw-binary win/loss signal. Tier 3 grey literature."
8. **F6.10-prose — §3.4.4 (chapter line 163)**: append to the existing paragraph one sentence: "Wartość r=0,96 jest korelacją liczoną na zagregowanych wskaźnikach wygranej w obrębie kubełków różnicy rankingowej, nie na surowym sygnale binarnym wygrana/przegrana — co znacząco zawyża korelację względem estymaty na surowych danych." No [REVIEW] flag (the audit Appendix B A13 is a methodological note, not a primary-source claim that requires PDF verification).
9. **F6.11 — SKIP** (verified resolved in TG4 PR #190).
10. **F6.12 — DEFER** (blockquote convention; conservative to avoid tooling regression).
11. **REVIEW_QUEUE + WRITING_STATUS updates** documenting all seven PR-6b edits.
12. **Version bump 3.36.0 → 3.37.0** + CHANGELOG.

### What this PR does NOT cover

- **NO rewriting of existing paragraphs** — all edits are inline annotation / parenthetical / single-sentence appends. Consistent with chore discipline.
- **NO new bib entries** (chore constraint).
- **NO F5.6 Demšar §3.2 → §3.1.3 swap** — still deferred to post-Pass-2 once readable PDF confirms.
- **NO F6.12 blockquote convention** (explicitly deferred per audit condition "only if no tooling regression" + repo's grep patterns depend on inline form).
- **NO methodology changes** — all edits are citation-location, metadata, or explanatory annotation.
- **NO data/feature/model work** — Cat F chore; invariants #1, #3–#10 are N/A (I2 applies: new/changed bib fields must not remove DOI/URL anchors; they only add metadata).

### Binding discipline

- **Polish academic register** throughout. Use existing §2.2.4 vocabulary ("protokół", "game loop", "patch") for consistency.
- **ISO dates** (yyyy-mm-dd); no locale-Polish dates. Exception: inline prose may say "7 maja 2013 r." for readability; pure-metadata fields use ISO.
- **Chore PR discipline** (per pass2_dispatch.md:145 category guidance): all edits are citation-location fixes, metadata refreshes, flag-presence reconciliations, or explanatory annotations. No new claims, no methodology changes, no bib additions.
- **[REVIEW] flag convention** per `.claude/rules/thesis-writing.md:69`: `[REVIEW: <specific concern> — Pass-2 <mechanism>]`. Flags name the verifiable claim + Pass-2 closure mechanism.
- **Asymmetric caps** (per `feedback_adversarial_cap_execution.md`): `/critic` max 3, Mode A one+1, Mode C one+1. Chore scope may warrant reduced critique per pass2_dispatch.md:145 ("chore scope → skip critique"), but given the two unverified audit claims (F6.4 + F6.7) that WebSearch could not corroborate, **PR-6b runs full /critic workflow** plus Mode A+C as precaution.
- **Post-merge planning purge**: overwrites PR-6a plan; PR-6b is the final scheduled Pass-2 PR (after merge, only post-Pass-2 F5.6 Demšar swap remains).

## Execution Steps

### T01 — F6.4 + F6.5 §2.2.4 edits

**File:** `thesis/chapters/02_theoretical_background.md` §2.2.4 (lines 43, 45).

**Action (F6.4) — Mode A WARNING 3 resolution (keep Liquipedia + add Vinyals as secondary anchor):** In the sentence at line 43, REPLACE "22,4 game loops na sekundę rzeczywistą [Liquipedia_GameSpeed]" with "22,4 game loops na sekundę rzeczywistą [Liquipedia_GameSpeed; potwierdzenie peer-reviewed w Vinyals2017]". Liquipedia remains PRIMARY (verified grey-literature) anchor; Vinyals2017 is added as secondary (peer-reviewed) anchor pending Pass-2 PDF confirmation. Preserve the FIRST `[Liquipedia_GameSpeed]` citation (the one after "domyślną liczbą 16 logicznych klatek na sekundę gry przy prędkości *Normal*"). This reverses the original swap per Mode A: audit-claim should not swap before verifying; existing chapter line-49 [REVIEW] flag remains its conservative branch ("jeśli nie, grey-literature zachowana").

**Preserve existing line-49 [REVIEW] flag:** chapter 02 already carries a `[REVIEW: ... zweryfikować, czy Vinyals2017 zawiera explicite te liczby; jeśli nie, podejście grey-literature wymaga ujednolicenia]` hedge at line 49. After Mode A reversal (Liquipedia + Vinyals secondary, not substitute), this existing flag is CORRECTLY POSITIONED — it hedges the peer-reviewed secondary anchor exactly as Mode A recommends. DO NOT harvest or modify line 49. Zero new flag added at the F6.4 locus.

No new flag inserted at §2.2.4 line 43 (existing line-49 [REVIEW] flag preserved, which already hedges the Vinyals2017 primary-source verification concern).

**Action (F6.5) — Mode A option (c) adopted:** KEEP the sentence at chapter line 45 ("*Tracker events* (wprowadzone w protokole 2.0.8 [BlizzardS2Protocol])") UNCHANGED. Do NOT insert the inline date parenthetical. Instead, append a standalone [REVIEW] flag to the §2.2.4 paragraph noting that the exact patch release date is deferred to Pass-2 for proper citation: `[REVIEW: F6.5 Pass-2 audit — Patch 2.0.8 release date (audit pass2_dispatch.md:189 cytuje 7 May 2013 NA; Liquipedia potwierdza 2013-05-07 NA / 2013-05-08 EU/KR / 2013-05-06 SEA) wymaga oddzielnego źródła patch-notes (BlizzardS2Protocol README pokrywa wersję protokołu 2.0.8, nie datę wydania patcha Pattern); Pass-2 dodaje date-specific citation lub nowy bib entry dla patch-notes.]`. This defers F6.5 closure to Pass-2 but preserves citation integrity (no citation-content mismatch planted in prose per Mode A BLOCKER 1).

**Gate:**
- Citation count on line 43: unchanged (2 citations: Liquipedia_GameSpeed at first position + Vinyals2017 at second position — Liquipedia at second position removed).
- Flag count at line 49 (F6.4 locus): **net 0** — the existing line-49 [REVIEW] flag is harvested and replaced by the new F6.4 [REVIEW] flag; exactly one flag total remains at that locus on this topic, not two.
- Line 45: no citation changes; date parenthetical added using the existing `[BlizzardS2Protocol]` bibkey (no `Liquipedia_SC2Patches`, no new bib entry).

### T02 — F6.6 §2.5.5 + §3.2.4 EsportsBench version footnote

**Files:** `thesis/chapters/02_theoretical_background.md` (§2.5.5 line 177); `thesis/chapters/03_related_work.md` (§3.2.4 line 77).

**Action (§2.5.5) — Mode A WebFetch 2026-04-20 resolution:** HuggingFace EsportsBench dataset page shows v1.0-v7.0 are RELEASED (v7.0 cutoff 2025-09-30); v8.0 is listed as a PLANNED future release (cutoff 2025-12-31). Thesis thus depends on v7.0 (the latest released at time of writing), not v8.0 (not yet released). Add parenthetical "(publicznie dostępna wersja HuggingFace v7.0, cutoff 2025-09-30; planowana wersja v8.0 ma cutoff 2025-12-31) [REVIEW: F6.6 Pass-2 — §3.5 Luka 3 obecnie wspomina 'v8.0 (2025-12-31)' — przy lądowaniu PR-6b jest to wersja planowana, nie wydana; Pass 2 aktualizuje §3.5 do v7.0/2025-09-30 lub do późniejszej wydanej wersji (do Pass 2 data cutoff HuggingFace może się zmienić)]". Do not touch the remainder of the sentence.

**Action (§3.2.4) — parallel to §2.5.5 Mode A fix:** After "EsportsBench [Thorrez2024], cytowany już w §2.5", add parenthetical "(publicznie dostępna wersja HuggingFace v7.0, cutoff 2025-09-30; v8.0 planowana z cutoff 2025-12-31) [REVIEW: F6.6 Pass-2 — §3.5 Luka 3 obecnie wspomina v8.0 (2025-12-31); przy lądowaniu PR-6b jest to wersja planowana, nie wydana; Pass 2 aktualizuje §3.5 wraz ze stanem HuggingFace w dacie Pass 2]". Harmonized with §2.5.5 parenthetical.

**Gate:**
- Net new flags: **+2 [REVIEW]** (one at §2.5.5, one at §3.2.4 — both flagging the v8.0/2025-12-31 vs v1.0-v7.0/2025-09-30 reconciliation gap; Pass-2 closure via HuggingFace release notes).
- Consistency with §3.5 Luka 3 wording (which says "v8.0 (2025-12-31)") preserved; the [REVIEW] flags make the unverified-date ambiguity explicit rather than silent.

### T03 — F6.7 §3.3.1 Yang paragraph clarifications

**File:** `thesis/chapters/03_related_work.md` §3.3.1 (line 91, Yang2017Dota paragraph).

**Action (prose — qualitative-only):** Append to the paragraph, after the last existing sentence ending with "argumentacja zgodna z konwencją wczesnych prac w domenie StarCraftowej [Erickson2014]", exactly **one** new sentence:

> Należy odnotować, że podział 9:1 stosowany w ocenie trafności w tej pracy jest dobierany losowo, a nie temporalnie [REVIEW: F6.7 Pass-2 verify arXiv:1701.03162 — semantyka podziału 9:1 (random vs temporal)].

**Action (REVIEW_QUEUE.md only — DEFERRED numeric reclassification):** The quantitative claim that "58,69% odpowiada reimplementacji modelu Kinkade i in. z samymi cechami bohatera, natomiast własny model regresji logistycznej Yanga i in. osiąga 60,07%" is an audit Appendix-B read (pass2_dispatch.md:193 + A8 line 373–374) that this PR's WebSearch could NOT independently corroborate. Per the F6.1 precedent (where four unverified author names were recorded in REVIEW_QUEUE only, NOT planted into thesis prose), this PR **does not add the 60.07%/Kinkade reclassification to thesis prose**. Instead, a REVIEW_QUEUE §3.3 row entry documents the deferred question for Pass-2 PDF verification: "F6.7 — Yang2017Dota (§3.3.1): audit asserts 58,69% is Kinkade-et-al. reimplementation while own LR on hero features = 60,07% (pass2_dispatch.md:193 + A8 line 373–374); WebSearch 2026-04-20 did not surface 60.07%; defer figure-reassignment until Pass-2 PDF read confirms. Existing 58,69/71,49/93,73 framing in §3.3.1 retained unchanged pending closure." This keeps prose defensibility symmetric with F6.1 — unverifiable numeric audit claims remain outside chapter prose until they survive primary-source review.

**Gate:**
- Net new flags in prose: **+1 [REVIEW]** (the random-not-temporal clarification only; the 60.07%/Kinkade claim is NOT in prose).
- Net new REVIEW_QUEUE entries: **+1** — §3.3 row entry documenting the deferred 60.07%/Kinkade reclassification question.
- No other sentences modified; existing "58,69% → 71,49% → 93,73%" framing preserved.
- If Pass-2 verification returns negative on the random-not-temporal claim, the single appended sentence + its flag can be removed cleanly. The REVIEW_QUEUE entry either closes (if Pass-2 confirms audit Appendix-B reading — follow-up PR plants the prose reclassification) or stays deferred (if Pass-2 cannot locate the 60.07% in the PDF).

### T04 — F6.8 bib edit for Silva2018LoL

**File:** `thesis/references.bib` lines 500–506 (`@inproceedings{Silva2018LoL, ...}`).

**Action:** Add two fields to the existing entry — `pages = {639--642},` and `issn = {2179-2259},` — plus one adjacent BibTeX-level comment line hedging the ISSN (per R10: ISSN is audit-provided and not independently verified; the comment preserves an audit-trail without planting an inline prose [REVIEW] flag). Suggested positions: `pages` after the `year = {2018}` line, then `issn` with the comment line immediately preceding it. Do NOT modify other fields.

**Proposed final entry state (Mode A NOTE: `%` bib-comment OUTSIDE the `@inproceedings{}` block for parser safety):**
```
% [REVIEW: F6.8 — ISSN 2179-2259 provided by audit; not independently verified; Pass-2 WebSearch SBGames Proceedings ISSN]
@inproceedings{Silva2018LoL,
  author    = {Silva, Antonio Luis Cardoso and Pappa, Gisele Lobo and Chaimowicz, Luiz},
  title     = {Continuous Outcome Prediction of {League of Legends} Competitive Matches Using Recurrent Neural Networks},
  booktitle = {Proc. 17th Brazilian Symposium on Computer Games and Digital Entertainment (SBGames)},
  year      = {2018},
  pages     = {639--642},
  issn      = {2179-2259}
}
```

**Gate:**
- No new bib entries; one entry edited with two metadata-only fields added plus a BibTeX comment line hedging the ISSN (R10 compliance).
- Existing `author`/`title`/`booktitle`/`year` preserved exactly.
- The BibTeX comment uses the `%` prefix (standard BibTeX line-comment syntax) so it does not appear in the rendered bibliography; it is an audit-trail anchor only.

### T05 — F6.9 §3.4.4 Xie R²-vs-accuracy hypothesis flag

**File:** `thesis/chapters/03_related_work.md` §3.4.4 (line 161, Xie2020MediumAoE paragraph).

**Action:** After the existing sentence ending with "obserwacja sama w sobie interesująca, sugerująca silną nieliniowość przestrzeni decyzyjnej.", append one new sentence:

> Bardziej prawdopodobną interpretacją tej liczby jest terminologiczny błąd w oryginalnym opisie: autor stosuje XGBRegression (model regresyjny, nie klasyfikacyjny), a wartość rzędu 2% jest niemożliwa jako trafność klasyfikacji binarnej (poniżej losowego baseline ≈50%), lecz jest plausibilnym małym współczynnikiem determinacji R² dla zadania regresji z wąskim rozkładem różnicy rankingowej; raportowana „trafność" prawdopodobnie odnosi się do R², nie do trafności klasyfikacyjnej [REVIEW: F6.9 Pass-2 verify — odczyt oryginalnego tekstu Xie 2020 Medium post].

**Gate:**
- Net new flags: +1 [REVIEW].
- Existing sentence preserved (hypothesis annotation is APPENDED, not replacing).
- Interpretation is clearly hedged ("bardziej prawdopodobną interpretacją", "prawdopodobnie odnosi się do").

### T06 — F6.10 bib edit for Porcpine2020EloAoE + §3.4.4 prose annotation

**File:** `thesis/references.bib` lines 95–102 (`@misc{Porcpine2020EloAoE, ...}`).

**Action (bib):**
- `url = {https://porcpine1967.github.io/aoe2/elo.html}` → `url = {https://porcpine1967.github.io/aoe2_comparisons/elo/}` (verified live via WebFetch 2026-04-20).
- `howpublished = {GitHub Pages (community analysis)}` → `howpublished = {GitHub Pages (\\url{https://porcpine1967.github.io/aoe2_comparisons/}); code at \\url{https://github.com/porcpine1967/aoe2_comparisons}}`.
- `note = {Community analysis; aoe2.net API; 908{,}940 matches; Tier 3 grey literature}` → `note = {Community analysis; aoe2.net API; 908{,}940 matches; r=0.96 computed on bin-aggregated win-percentages per rating-difference bin (inflated relative to raw-binary match signal); Tier 3 grey literature}`.

**File:** `thesis/chapters/03_related_work.md` §3.4.4 (line 163, Porcpine2020EloAoE paragraph).

**Action (prose):** After the existing sentence "Regresja liniowa prawdopodobieństwa zwycięstwa na różnicy Elo daje współczynnik korelacji r=0,96 i nachylenie 0,0011 na punkt rankingowy", insert one clarifying sentence before continuation "co stanowi empiryczną ilustrację liniowości":

> Należy jednak zaznaczyć, że wartość r=0,96 jest korelacją liczoną na zagregowanych wskaźnikach wygranej w obrębie kubełków różnicy rankingowej (bin-aggregation), nie na surowym sygnale binarnym wygrana/przegrana — co znacząco zawyża korelację względem estymaty liczonej bezpośrednio na danych binarnych.

**Gate:**
- Bib edit: URL corrected (404 → live); howpublished + note extended; no new fields/entries, no removed fields.
- Prose: one new sentence appended; existing r=0,96 + nachylenie sentence preserved.
- No [REVIEW] flag needed (bin-aggregation is a methodological observation derivable from the Porcpine analysis itself, not a primary-source claim).

### T07 — REVIEW_QUEUE.md + WRITING_STATUS.md updates

**Files:** `thesis/chapters/REVIEW_QUEUE.md`, `thesis/WRITING_STATUS.md`.

**Action:** Append `**2026-04-20 (PR-TG6b):**` bolded note to the affected rows:
- **§2.2** row (both files): F6.4 Liquipedia→Vinyals citation substitution at 22.4 figure — existing line-49 [REVIEW] flag **harvested and replaced** by the new F6.4 flag (net zero flag change at that locus, one flag total); F6.5 Patch 2.0.8 date inline parenthetical (2013-05-07 NA / 2013-05-08 EU/KR) using the existing `[BlizzardS2Protocol]` bibkey (no new bib entry).
- **§2.5** row (both files): F6.6 EsportsBench v8.0 versioning parenthetical at §2.5.5 with [REVIEW] flag (v8.0/2025-12-31 vs audit-cited v1.0-v7.0/2025-09-30 reconciliation deferred to Pass-2 HuggingFace release notes).
- **§3.2** row (both files) OR §3.2.4 if enumerated: F6.6 EsportsBench versioning parenthetical at §3.2.4 with [REVIEW] flag (same reconciliation deferral as §2.5).
- **§3.3** row (both files) — prose + REVIEW_QUEUE deferral entry (per R5 / F6.1 symmetry):
  - Prose: F6.7 §3.3.1 Yang — single qualitative [REVIEW]-flagged sentence on random-not-temporal 9:1 split semantics (only).
  - REVIEW_QUEUE-only deferral row: "F6.7 — Yang2017Dota (§3.3.1): audit asserts 58,69% is Kinkade-et-al. reimplementation while own LR on hero features = 60,07% (pass2_dispatch.md:193 + A8 line 373–374); WebSearch 2026-04-20 did not surface 60,07%; defer figure-reassignment until Pass-2 PDF read confirms. Existing 58,69/71,49/93,73 framing in §3.3.1 retained unchanged pending closure." This deferral row is REVIEW_QUEUE-only — no prose change for the numeric reclassification, per F6.1 precedent.
- **§3.4** row (both files): F6.9 Xie R²-vs-accuracy hypothesis flag (+1 [REVIEW] flag); F6.10 Porcpine bin-aggregation prose caveat.
- **§bib** row (both files, if present; else general notes section): F6.8 Silva2018LoL pages+ISSN + adjacent bib-comment hedge on ISSN; F6.10 Porcpine URL correction + note extension.

**Gate:**
- 5–6 row updates; consistent dated-note convention.
- REVIEW_QUEUE additionally carries one new §3.3 deferral row (R5 / F6.1 symmetry) documenting the 60,07%/Kinkade numeric reclassification held out of prose.
- Net prose flag deltas: §2.2 +0 (harvest-and-replace of existing line-49 flag); §2.5 +1 (F6.6); §3.2 +1 (F6.6); §3.3 +1 (F6.7 random-not-temporal only); §3.4 +1 (F6.9); **total +4 new [REVIEW] flags in prose** across both chapters. The 60,07%/Kinkade question is tracked in REVIEW_QUEUE only, not as a prose flag.

### T08 — Version bump + CHANGELOG

**Files:** `pyproject.toml`, `CHANGELOG.md`.

**Action:**
- `pyproject.toml`: `version = "3.36.0"` → `version = "3.37.0"` (minor bump for docs per `.claude/rules/git-workflow.md` §Version).
- `CHANGELOG.md`: move `[Unreleased]` contents (if any non-empty) to a new `[3.37.0] — 2026-04-20 (PR #TBD: docs/thesis-pass2-tg6b-bib-hygiene-minor-prose)` heading. Add empty `[Unreleased]` block with `### Added / Changed / Fixed / Removed` headers. Populate `[3.37.0]` `### Changed` with: "docs(thesis): Pass-2 PR-6b — F6.4 §2.2.4 Vinyals2017 citation substitution for 22.4 loops/sec (Liquipedia kept for 5734/4096 fixed-point; existing line-49 [REVIEW] flag harvested and replaced by F6.4 flag — one flag total); F6.5 §2.2.4 Patch 2.0.8 release date (2013-05-07 NA / 2013-05-08 EU/KR) using existing [BlizzardS2Protocol] bibkey (no new bib entry); F6.6 §2.5.5 + §3.2.4 EsportsBench v8.0 version footnote with [REVIEW] flags (×2) reconciling v8.0/2025-12-31 vs audit-cited v1.0-v7.0/2025-09-30; F6.7 §3.3.1 Yang 2017 qualitative split-semantics clarification (random-not-temporal) with [REVIEW] flag — 60.07%/Kinkade numeric reclassification deferred to REVIEW_QUEUE per F6.1 precedent; F6.8 Silva2018LoL bib pages 639-642 + ISSN 2179-2259 with adjacent bib-comment hedge on unverified ISSN; F6.9 §3.4.4 Xie R²-vs-accuracy hypothesis flag; F6.10 Porcpine2020EloAoE bib URL fix (404 → live) + r=0.96 bin-aggregation caveat. F6.11 skipped (resolved in TG4); F6.12 deferred (tooling regression risk). 4 new [REVIEW] flags in prose, zero new bib entries."

**Gate:**
- pyproject.toml version exact "3.37.0".
- CHANGELOG `[3.37.0]` block populated; `[Unreleased]` reset to empty.

### T09 — Cleanup confirmation

**Action:** Verify no residual changes outside the 7-file manifest. Run `git diff --stat` locally (writer-thesis judgment).

## File Manifest

Exactly these files modified:

| File | Nature of change | Scope |
|---|---|---|
| `thesis/chapters/02_theoretical_background.md` | §2.2.4 F6.4+F6.5 edits; §2.5.5 F6.6 edit | 3 prose annotations + 1 citation substitution + 1 [REVIEW] flag |
| `thesis/chapters/03_related_work.md` | §3.2.4 F6.6; §3.3.1 F6.7; §3.4.4 F6.9+F6.10-prose | 4 prose annotations + 3 [REVIEW] flags |
| `thesis/references.bib` | F6.8 Silva2018LoL edit; F6.10 Porcpine2020EloAoE edit | 2 existing entries edited; 0 new entries |
| `thesis/WRITING_STATUS.md` | dated notes to affected §-rows | ~5 row updates |
| `thesis/chapters/REVIEW_QUEUE.md` | dated notes to affected §-rows | ~5 row updates |
| `pyproject.toml` | 3.36.0 → 3.37.0 | single line |
| `CHANGELOG.md` | [Unreleased] → [3.37.0] release entry | two block swaps |
| `planning/current_plan.md` | this file (overwrites PR-6a plan) | whole file |

No other files modified. `.github/tmp/commit.txt` and `.github/tmp/pr.txt` are created during commit/PR stages and deleted at cleanup.

## Dispatch sequence

1. This plan written. Planning-drift hook validates all 8 Cat F sections.
2. `/critic planning/current_plan.md` — max 3 iterations per cap. Parent orchestrates 4 critics → merger → RECOMMENDED subset → writer-thesis for plan revision if needed.
3. If iteration 3 completes with residual BLOCKERs, halt and return choice to user (land-as-is vs follow-up PR) before proceeding to Mode A.
4. `reviewer-adversarial` Mode A — one run; writes `planning/current_plan.critique.md`. If REVISE: apply once within symmetric 1-revision cap; if REDESIGN: halt.
5. `writer-thesis` — dispatched against this plan with T01–T09.
6. `reviewer-adversarial` Mode C — one run; if REVISE: apply once; if REDESIGN: halt.
7. Pre-commit validation — planning-drift + ruff (N/A no .py) + mypy (N/A no .py).
8. Commit via `git commit -F .github/tmp/commit.txt`.
9. PR via `gh pr create --body-file .github/tmp/pr.txt`.
10. Merge via `gh pr merge --merge --delete-branch`.
11. Cleanup: `rm .github/tmp/pr.txt .github/tmp/commit.txt`.
12. Halt after merge — PR-6b is the last scheduled Pass-2 PR; report to user and pause.

## Risk mitigation

- **Risk: writer-thesis invents a non-existent bibkey for F6.5 patch date.** Mitigation: T01 F6.5 action is one unambiguous path — the existing `[BlizzardS2Protocol]` bibkey (already present in `references.bib`) is reused as the grey-literature anchor for Patch 2.0.8's release date. No `Liquipedia_SC2Patches` bibkey is referenced anywhere in the plan, and no new bib entry is introduced (chore discipline preserved).
- **Risk: F6.4 Vinyals2017 does NOT contain 22.4 upon Pass-2 PDF read.** Mitigation: [REVIEW] flag explicitly names this as Pass-2 verification item. If paper doesn't contain the figure, the Vinyals citation can be RETRACTED and Liquipedia citation restored (minor patch PR post-Pass-2). The audit A16 claim is the only support for the substitution; our WebFetch failed to verify.
- **Risk: F6.7 Yang 60.07% doesn't match PDF.** Mitigation: per R5, the 60,07%/Kinkade numeric reclassification is **not** planted into thesis prose — it lives only in REVIEW_QUEUE §3.3 as a deferral row (mirroring the F6.1 precedent). If Pass-2 PDF shows a different value (or the audit's Appendix-B reading is wrong), the REVIEW_QUEUE entry either closes or is revised without any chapter-prose retraction. Only the qualitative random-not-temporal sentence sits in prose, flagged [REVIEW]; it can be dropped cleanly if Pass-2 contradicts the split semantics. Existing 58,69/71,49/93,73 framing in §3.3.1 is preserved unchanged.
- **Risk: F6.6 EsportsBench v8.0 cutoff date disagrees with §3.5 wording.** Mitigation: plan explicitly says "Resolve in favor of §3.5 existing wording (v8.0 2025-12-31) unless writer-thesis identifies a HuggingFace release-note source that clarifies" — writer resolves this via existing-chapter consistency, not independent verification.
- **Risk: ISSN 2179-2259 wrong.** Mitigation: audit is source; low-risk metadata. If Pass-2 finds different ISSN, one-line bib edit.
- **Risk: F6.10 URL second form also goes dead between now and Pass-2.** Mitigation: tracked via [REVIEW] in REVIEW_QUEUE §3.4 row; alternate route is archive.org snapshot if live URL breaks.

## Non-negotiable invariants during execution

- **I2 (reproducibility):** Every new/changed citation has DOI/URL/arXiv anchor. Vinyals2017 has arXiv:1708.04782 (bib line 16); Silva2018LoL edit adds pages+ISSN without removing existing fields; Porcpine URL change corrects 404 to working URL.
- **I7 (no magic numbers):** Numbers added in prose (22.4, 2013-05-07, 60.07%, 908 940, r=0.96) all trace to existing artifacts or planted [REVIEW] for Pass-2 verification of the two audit-only claims.
- **I8/I9 (raw data / pipeline immutability):** No `src/`, `reports/`, `sandbox/` changes.
- **Honesty clause:** Two audit claims (F6.4 Vinyals, F6.7 Yang) NOT independently verified — [REVIEW] flags explicitly disclose the gap and name Pass-2 closure mechanism. Do not land claims that cannot survive PDF review without the hedge.
- **No thesis prose without a source:** Every new claim either cites an existing bib entry or plants [REVIEW] flag. No invented references.

## Post-merge

- Update `thesis/reviews_and_others/pass2_status.md` to reflect PR-6b merge (version 3.37.0; F6.4/F6.5/F6.6/F6.7/F6.8/F6.9/F6.10 closed with 4 new [REVIEW] residuals; F6.11 skipped — done in TG4; F6.12 deferred; Pass-2 now has only post-Pass-2 F5.6 Demšar swap + PR-6b [REVIEW] resolutions remaining).
- PR-6b is the FINAL scheduled Pass-2 PR — no authorization to continue to follow-ups without explicit user instruction.
