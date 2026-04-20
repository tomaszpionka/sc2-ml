# Plan Critique — reviewer-adversarial Mode A (TG4)

**Target:** `planning/current_plan.md` (439 lines)
**Date:** 2026-04-20

## Verdict: REQUIRE_MINOR_REVISION

1 BLOCKER (B1 — Baek bibkey undercount) + 3 WARNINGs + 3 NOTEs.

## Findings

### BLOCKER B1 — `[Baek2022]` has THREE occurrences in 01_introduction.md, not two
Plan line numbers 11 and 69 are wrong. Line 11 is GarciaMendez, not Baek. Actual `[Baek2022]` sites: **13, 25, 69**.

**Fix:** T02 step 2 must replace all three; verification grep → 3 hits for `[BaekKim2022]`, 0 for `[Baek2022]`.

### WARNING W1 — EsportsBench URL + title disagreement
HuggingFace page actually titled "EsportsBench: A Collection of Datasets for Benchmarking Rating Systems in Esports"; bib keeps "Rating System Evaluation for Esports".

**Fix:** add annotation to `note` field: "Title reflects preprint front matter; HuggingFace dataset page uses subtitle 'A Collection of Datasets for Benchmarking Rating Systems in Esports'." Closes disagreement surface.

### WARNING W2 — Hodge2021 Open Q 5 default unclear
Plan Open Q 5 deferred to Mode A. **Default:** adopt full first names (IEEE Xplore canonical) per Bunker2024 pattern already in bib.

### WARNING W3 — Aligulac Option (c) preferred over (a)
`{Fonn, Eivind and {Aligulac contributors}}` is more defensible than `{Fonn, Eivind}` alone (acknowledges 15-year community project with multiple contributors). **Adopt (c) as planner resolution.**

### NOTE N1 — Chapter-local References block in 01_introduction.md becomes orphaned after global-bib migration
Hygiene debt; Pass 2 item.

### NOTE N2 — `reviews_and_others/related_work_rating_systems.md:393` carries "Thorrez, Calvin" (third divergent first-name)
Post-TG4 repo has Lucas (deleted), Clayton (new bib), Calvin (scratchpad). Add REVIEW_QUEUE entry for Pass 2.

### NOTE N3 — Khan2024SCPhi2 title variance (preprint "Macromanagement Tasks" vs MDPI "Build Order Prediction")
Normal preprint→journal retitling. MDPI canonical is correct. No action.

## Probes answered

- 11+1 enumeration table: accurate
- Lin Shih "Yu-Wei" (not Yi-Wei): arXiv confirms
- Tarassoli2024 deletion: 0 chapter `[Tarassoli2024]` citations — safe
- Hodge2021 pages 368–379: IEEE Xplore confirms
- Khan2024SCPhi2 pages 2338–2352: MDPI confirms

## Recommendation

**REQUIRE_MINOR_REVISION.** Four edits:
1. B1: T02 replaces `[Baek2022]` at three lines (13, 25, 69); verification updated
2. W1: annotate EsportsBench `note` field about HuggingFace title variance
3. W2: ratify full first-name convention for Hodge2021 in Open Q 5
4. W3: adopt Option (c) for Aligulac in Open Q 1

Plus N2: add REVIEW_QUEUE entry for triple-divergent Thorrez first-name in scratchpad.
