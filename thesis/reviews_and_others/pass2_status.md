# Pass-2 Audit Status — Handoff Document

Prior session: 2026-04-20. Next session: resume here.

## At-a-glance

- **Audit source of truth:** `thesis/reviews_and_others/pass2_dispatch.md` (446 lines, saved 2026-04-20 from transcript `36812a12` line 6 for durable cross-session recovery)
- **Version:** 3.34.0 (post-PR #191)
- **Master HEAD:** `b2a2d84b` (Merge of PR #191)
- **Active branch:** master, clean
- **Pass-2 total progress:** 5 PRs merged, 3 remaining + 1 post-audit cleanup

## Merged PRs

| PR | TG | Scope | Key outcomes |
|---|---|---|---|
| #187 | TG1 | Methodological drift | §1.2/§2.6/§4.4.4 — un-commit Dimitriadis triptych; within-game protocol reframed as candidate-list |
| #188 | TG2 | Factual contradictions | §2.2.2 SC2EGSet date range → 2016–2024; §2.3.2 AoE2 civ count → 50 (aoestats window 2022-08-28 — 2026-02-07) |
| #189 | TG3 | Luka 3 narrowing | §3.5 four-constraint argued narrowing against EsportsBench v8.0; §3.2.4 + §1.3 + §2.5.5 cascade |
| #190 | TG4 | 11+1 bibliography findings | references.bib author-name corrections (Thorrez Lucas→Clayton; Hodge Sherkat→canonical IEEE 6-author; BaekKim; Aligulac; Elbert Schenk+Stein; Lin Shih); Tarassoli phantom deleted; Khan MDPI pages fix |
| #191 | TG5-PR-5a | Internal-consistency chore | F5.1 §1.1 flag count; F5.2 THESIS_STRUCTURE footer; F5.3 Aligulac calibration reframe; F5.5 Elbert §3.4 placement; F5.6 Demšar §3.2 / §3.1.3 flag-planting |

## Remaining work (in priority order)

### PR-5b (science-lite) — NEXT

**Scope:** F5.4 + F4.5 (expanded scope per TG5-PR-5a Mode A W2 resolution)

- **F5.4** — §4.1.3 "Ramy okna referencyjnego" circular spec-reference. Audit pass2_dispatch.md:163. Rewrite to either:
  - (i) substantively argue why patch-regime homogeneity dominates window-length comparability in ICC estimation (cite literature — likely Nakagawa 2017 + Gelman 2007 + Ukoumunne 2003, which are already in references.bib from §4.4.5), OR
  - (ii) concede it's a judgment call and add a sensitivity-axis acknowledgement (simpler; stays within chore-adjacent scope).
- **F4.5** — Insert Thorrez2024 Glicko-2 (80.13% SC2 accuracy) academic-proxy comparator sentence at §2.2.3. Previously attempted in TG5-PR-5a iter 1 but removed per R6 revision to maintain chore discipline; scope inherits here. Audit pass2_dispatch.md:124 + Appendix B A15 (lines 410–414). The Thorrez2024 bib entry already exists (bib line 144); this is a prose-only insertion, not a bib addition.

**Effort estimate:** 1 Cat F planning + execution cycle (~8–10 agent dispatches through the full /critic → Mode A → writer-thesis → Mode C → commit+PR workflow).

### PR-6a (science-lite)

**Scope:** F6.1 + F6.2 + F6.3 — §3.5 Luka prophylactic strengthening

- **F6.1** — Luka 1: name the 2024–2026 papers covering multi-family classifiers **without** probabilistic metrics (audit pass2_dispatch.md:181 names these: Brookhouse & Buckley 2025; Caldeira et al. 2025; Alhumaid & Tur 2025; Minami et al. 2024; García-Méndez & de Arriba-Pérez 2025). Plus Ferraz et al. 2025 as single-model calibration example. **All these bib entries need verification via WebSearch before inclusion — none currently exist in references.bib.**
- **F6.2** — Luka 2: tighten "§3.5 SHAP + leave-one-category-out ablation" hedge. Explicitly distinguish Elbert 2025's econometric residualization from SHAP. No new bib entries expected.
- **F6.3** — Luka 4: add footnote that García-Méndez & de Arriba-Pérez 2025 use "cold start" for classifier warm-up phase, not player match-history length. Reinforces that no esports prediction paper stratifies accuracy by player history length.

**Effort estimate:** 1 Cat F cycle + possibly 5+ new bib entries with WebSearch verification per `.claude/rules/thesis-writing.md` Literature Search Protocol.

### PR-6b (chore)

**Scope:** F6.4–F6.12 **minus F6.11** (already landed in TG4)

- **F6.4** — §2.2.4 — Replace Liquipedia citation for 22.4 loops/sec with Vinyals 2017 (SC2LE). Keep Liquipedia only for 5734/4096 fixed-point constant footnote. Bib: Vinyals2017 already exists.
- **F6.5** — §2.2.4 — Add 2013-05-07 patch date for s2protocol 2.0.8 tracker events.
- **F6.6** — §2.5 + §3.2.4 — EsportsBench version footnote (HuggingFace v1.0–v7.0 through cutoff 2025-09-30; thesis relies on v8.0 per TG3).
- **F6.7** — §3.3.1 (Yang 2017 Dota paragraph) — Note 9:1 split is **random**, not temporal; Yang's own LR on hero features alone = 60.07%, not 58.69%.
- **F6.8** — bib (Silva2018LoL): add pages 639–642, ISSN 2179-2259.
- **F6.9** — §3.4.4 (Xie 2020 grey-lit paragraph) — Flag that Xie's <2% "linear regression accuracy" is likely R² misreported as accuracy.
- **F6.10** — bib (Porcpine2020): venue = GitHub Pages (porcpine1967.github.io/aoe2_comparisons/elo/); code at github.com/porcpine1967/aoe2_comparisons. Note r=0.96 is computed on aggregated bin-level data → inflation vs raw binary.
- ~~**F6.11**~~ — DONE in TG4 (Elbert bib: Stein Nora→Nikolai, Schenk Amadeus→Alicia). Drop from scope.
- **F6.12** — Optional [REVIEW:] flag blockquote convention — only if no tooling regression.

**Effort estimate:** 1 Cat F cycle, mostly bib hygiene. ~10 small edits across ch02/ch03 prose + references.bib.

### Post-Pass-2 cleanup

**F5.6 §3.2 → §3.1.3 swap** — TG5-PR-5a planted `[REVIEW: audit H3]` flags at 4 loci:
- `02_theoretical_background.md:211` (§2.6.3)
- `04_data_and_methodology.md:213` (§4.1.4)
- `04_data_and_methodology.md:375` (§4.4.4 inline)
- `04_data_and_methodology.md:377` (§4.4.4 bibkey)

Once a readable Demšar 2006 PDF confirms §3.1.3 contains both N ≥ 5 (CV folds within-game) and N ≥ 10 (datasets cross-dataset) thresholds, swap all 4 `§3.2` references to `§3.1.3` and remove the F5.6 flags. Line 373 of `04_data_and_methodology.md` is ALREADY `§3.1.3` from TG1 — do NOT touch it again.

**Blocker for Pass 2:** WebFetch on https://www.jmlr.org/papers/volume7/demsar06a/demsar06a.pdf returned unreachable in the prior session. García & Herrera 2008 (https://www.jmlr.org/papers/volume9/garcia08a/garcia08a.pdf) may serve as alternative anchor if Demšar 2006 remains inaccessible.

## Critical gotchas / lessons from TG5-PR-5a

### 1. F5.6 Demšar PDF unverified
WebFetch + WebSearch could not confirm §3.1.3 location for N ≥ 10 threshold. Mode A flagged this as BLOCKER B1/B2 (landing an unverified citation to master would reproduce the defect the audit exists to fix). Plan restructured to flag-planting only. **For PR-5b and later, treat ALL audit-claim primary-source citations as requiring independent verification before landing as prose.**

### 2. Polish dates — ISO only
User's prior explicit feedback (2026-04-20, TG3 session): **"everyone understand dates in yyyy-mm-dd format... wtf"**. No "od sierpnia 2022 do lutego 2026"-style Polish-idiomatic date phrasing in chapter prose. Em-dash ranges: `2022-08-28 — 2026-02-07`. Saved as `feedback_iso_date_format.md` in user memory.

### 3. Cat F planning hook required sections
The `.github/hooks/planning-drift` pre-commit hook blocks commits where `planning/current_plan.md` lacks these sections (Category F):
- `## Problem Statement`
- `## Literature Context`
- `## Assumptions & Unknowns`
- `## Gate Condition`
- `## Open Questions`
- `## Scope`
- `## Execution Steps`
- `## File Manifest`

TG5-PR-5a first commit failed on this; fix was adding all 8 sections as section anchors (some with 1-line content pointing to the full body below). **Put these in the plan from the start.**

### 4. `/critic` skill — 3-iteration max
Per `.claude/commands/critic.md`: dispatch 4 critics → merger → user subset → writer → next iter. Max 3 iterations. After that, if BLOCKERs remain, either (a) land as-is with issues flagged in PR body, or (b) open a follow-up PR for remaining items. User's memory (`feedback_adversarial_cap_execution.md`) extends this cap symmetrically to Mode A/C reviewer-adversarial cycles.

### 5. Chore PR discipline
"No new claims, no bib additions, no methodology changes." The F5.3 Thorrez-proxy insertion at §2.2.3 violated this in TG5-PR-5a iter 1 and got deferred to PR-5b (now bundled with F5.4). For chore PRs, keep edits strictly in: citation-location fixes, flag-presence reconciliations, documentation-of-decision sentences, metadata refreshes. For science-lite PRs (PR-5b, PR-6a), the constraint relaxes slightly for prose insertions but stays tight on methodology.

### 6. Three distinct review layers
- **`/critic` skill** — plan-level 4-critics dedup + merger. Inside `.claude/commands/critic.md`.
- **`reviewer-adversarial` Mode A** — methodology stress-test BEFORE execution. Writes to `planning/current_plan.critique.md`.
- **`reviewer-adversarial` Mode C** — post-draft stress-test BEFORE commit. Emits in chat; no file output.

Each catches different defects. TG5-PR-5a: /critic converged at iter 3 (all BLOCKERs resolved), but Mode A surfaced 2 NEW BLOCKERs (Demšar PDF + Elbert rationale misreference) that /critic missed because they were methodology-level, not protocol-level. Running all three is necessary for Cat F thesis work.

### 7. Per-PR isolation + planning purge
Each TG = separate PR. Don't bundle. After merge, `planning/current_plan.md` + `planning/current_plan.critique.md` get purged by either:
- (a) the next PR's plan overwriting them (TG1–TG5a pattern), OR
- (b) an explicit purge chore PR (PR #186 pattern).
Both work; (a) is simpler for sequential TG PRs.

### 8. F4.5 scope migration history
- Originally: audit F4.5 = TG4 science (pass2_dispatch.md:148 "PR-4a (science)").
- TG4 (PR #190) landed only bibliography hygiene (PR-4b-equivalent); did NOT include F4.5 prose insertion.
- TG5-PR-5a iter 1 attempted to subsume F4.5 into F5.3 at §2.2.3; removed per /critic scope R6 revision (chore violation).
- TG5-PR-5a iter 1 Mode A W2: F4.5 has no scheduled home. Mode A resolution: explicitly add F4.5 to PR-5b scope. Reflected in pass2_status.md / plan §1.2.

**When planning PR-5b:** include both F5.4 + F4.5 in §1.1 "What this PR covers".

## Workflow checklist for the next PR (PR-5b template)

1. `git checkout master && git pull --ff-only && git checkout -b docs/thesis-pass2-tg5b-<title>`
2. Read `thesis/reviews_and_others/pass2_dispatch.md` §F5.4 (line 163) + §F4.5 (line 124) + Appendix B A15 (lines 410–414) for full context.
3. Read `thesis/reviews_and_others/pass2_status.md` (this file) for gotchas.
4. Read `thesis/chapters/02_theoretical_background.md` §2.2.3 (line 39) + `thesis/chapters/04_data_and_methodology.md` §4.1.3 ("Ramy okna referencyjnego" — grep for the subsection heading).
5. Write `planning/current_plan.md` (Cat F; include all 8 required sections for the hook; branch: docs/thesis-pass2-tg5b-*).
6. Dispatch `/critic planning/current_plan.md` — max 3 iterations.
7. Dispatch `reviewer-adversarial` Mode A.
8. Dispatch `writer-thesis` to execute T01–T0n.
9. Dispatch `reviewer-adversarial` Mode C post-draft.
10. Bump pyproject.toml `3.34.0 → 3.35.0` + CHANGELOG entry.
11. Commit via `git commit -F .github/tmp/commit.txt` + PR body at `.github/tmp/pr.txt` + `gh pr create --body-file` + `gh pr merge --merge --delete-branch`.
12. `rm .github/tmp/pr.txt .github/tmp/commit.txt` cleanup.

## Where to look

- **Audit:** `thesis/reviews_and_others/pass2_dispatch.md`
- **Chapter status:** `thesis/WRITING_STATUS.md` + `thesis/chapters/REVIEW_QUEUE.md`
- **Plan workflow:** `thesis/plans/writing_protocol.md` + `.claude/rules/thesis-writing.md` + `CLAUDE.md` §Plan / Execute Workflow
- **Hook requirements:** `.claude/rules/git-workflow.md` + `.github/hooks/planning-drift` (if exposed)
- **Critic skill:** `.claude/commands/critic.md`
- **Agent manual:** `docs/agents/AGENT_MANUAL.md`

## Version trajectory (Pass 2 to date)

- 3.29.1 (pre-Pass-2)
- 3.30.0 — TG1 (PR #187)
- 3.31.0 — TG2 (PR #188)
- 3.32.0 — TG3 (PR #189)
- 3.33.0 — TG4 (PR #190)
- 3.34.0 — TG5-PR-5a (PR #191)
- 3.35.0 — PR-5b (planned)
- 3.36.0 — PR-6a (planned)
- 3.37.0 — PR-6b (planned)
- 3.37.1 (patch) — post-Pass-2 F5.6 swap when Demšar PDF resolves
