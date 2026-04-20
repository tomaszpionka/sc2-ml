# Adversarial Review — Plan (Mode A) — TG6-PR-6b

**Plan:** `planning/current_plan.md` (TG6-PR-6b — §2.2.4 + §3.3.1 + §3.4.4 + bib hygiene)
**Branch:** `docs/thesis-pass2-tg6b-bib-hygiene-minor-prose`
**Base:** `master` @ `48d557f6` (post-PR #194, version 3.36.0)
**Date:** 2026-04-20
**Reviewer:** reviewer-adversarial, Mode A (pre-execution)

## Lens summary

| Lens | Verdict |
|---|---|
| Temporal discipline | N/A |
| Statistical methodology | SOUND |
| Feature engineering | N/A |
| Thesis defensibility | ADEQUATE — 1 BLOCKER + 2 WARNINGs |
| Cross-game comparability | MAINTAINED |

## BLOCKER / WARNING / NOTE

1. **[BLOCKER] F6.5 citation-content mismatch** — `[BlizzardS2Protocol]` cited for Patch 2.0.8 release date but the bibkey content (s2protocol GitHub README) documents protocol version only, not patch release date. [REVIEW] flag documents the mismatch but does not fix it.
   **Fix option (c) adopted:** move the date into the [REVIEW] flag; prose stays unchanged. F6.5 deferred to Pass-2 for proper citation.

2. **[WARNING] F6.6 v8.0/2025-12-31 fragility multiplier** — audit cites v1.0-v7.0/2025-09-30; plan propagates v8.0/2025-12-31 from §3.5 to §2.5.5 + §3.2.4 without independent verification. 3-locus exposure.
   **Fix:** WebFetch HuggingFace EsportsBench page pre-execution. If v8.0 absent, use version-agnostic wording.

3. **[WARNING] F6.4 citation substitution before verification** — plan swaps Liquipedia→Vinyals at 22.4 locus before WebFetch-verifying Vinyals contains the figure. Existing line-49 flag preempted this.
   **Fix:** WebFetch Vinyals2017 arXiv PDF pre-execution. If found, drop new [REVIEW] flag. If not, keep Liquipedia + add Vinyals as secondary anchor.

4. **[NOTE] F6.8 bib-comment placement** — `%` comment inside `@inproceedings{}` body may break legacy bibtex parsers. Move OUTSIDE the entry block for parser safety.

## Verdict: REVISE BEFORE EXECUTION

Required revisions:
1. Adopt BLOCKER 1 option (c): F6.5 defer date to [REVIEW] flag; keep §2.2.4 prose unchanged.
2. WebFetch HuggingFace EsportsBench dataset page to verify v8.0 (F6.6).
3. WebFetch Vinyals2017 arXiv PDF to verify "22.4 times per second" (F6.4).
4. Move F6.8 `%` bib-comment outside `@inproceedings{}` block.

Symmetric 1-revision cap consumed; post-revision proceed to writer-thesis.
