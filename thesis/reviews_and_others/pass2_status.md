# Pass-2 Audit Status — Handoff Document

Prior session: 2026-04-21. Next session: resume here.

## At-a-glance

- **Audit source of truth:** `thesis/reviews_and_others/pass2_dispatch.md` (446 lines, saved 2026-04-20 from transcript `36812a12` line 6 for durable cross-session recovery)
- **Version:** 3.37.0 (post-PR #195); **3.38.0 pending** this refresh PR
- **Master HEAD:** `cd4ab339` (Merge of PR #195, 2026-04-20)
- **Active branch:** `docs/thesis-pass2-status-refresh-and-local-closures` (pre-merge — this refresh)
- **Pass-2 progress:** 8 scheduled audit PRs merged + 1 handoff-doc chore + 1 refresh chore = **all scheduled Pass-2 Code work complete**
- **Next work:** Claude Chat Pass-2 for remaining [REVIEW] / [NEEDS CITATION] flag resolutions (no more scheduled Pass-2 Code PRs)

## Merged PRs (Pass-2 sequence)

| PR | TG | Merged | Scope | Key outcomes |
|---|---|---|---|---|
| #187 | TG1 | 2026-04-20 | Methodological drift | §1.2/§2.6/§4.4.4 — un-commit Dimitriadis triptych; within-game protocol reframed as candidate-list |
| #188 | TG2 | 2026-04-20 | Factual contradictions | §2.2.2 SC2EGSet date range → 2016–2024; §2.3.2 AoE2 civ count → 50 (aoestats window 2022-08-28 — 2026-02-07) |
| #189 | TG3 | 2026-04-20 | Luka 3 narrowing | §3.5 four-constraint argued narrowing against EsportsBench v8.0; §3.2.4 + §1.3 + §2.5.5 cascade |
| #190 | TG4 | 2026-04-20 | 11+1 bibliography findings | references.bib author-name corrections (Thorrez Lucas→Clayton; Hodge Sherkat→canonical IEEE 6-author; BaekKim; Aligulac; Elbert Schenk+Stein; Lin Shih); Tarassoli phantom deleted; Khan MDPI pages fix |
| #191 | TG5-PR-5a | 2026-04-20 | Internal-consistency chore | F5.1 §1.1 flag count; F5.2 THESIS_STRUCTURE footer; F5.3 Aligulac calibration reframe; F5.5 Elbert §3.4 placement; F5.6 Demšar §3.2/§3.1.3 flag-planting |
| #192 | (handoff) | 2026-04-20 | Pass-2 handoff doc addition | Created this file (pre-refresh) |
| #193 | TG5-PR-5b | 2026-04-20 | F5.4 + F4.5 | §4.1.3 reference-window literature anchoring (Nakagawa2017 + Gelman2007 + Ukoumunne2003 + WuCrespiWong2012); §2.2.3 Thorrez2024 Glicko-2 80,13% academic-proxy insertion |
| #194 | TG6-PR-6a | 2026-04-20 | F6.1 + F6.2 + F6.3 | §3.5 Luka 1/2/4 prophylactic strengthening; Minami2024 as adjacent-reference-class witness; [NEEDS CITATION] flag for 4 unverified seed authors |
| #195 | TG6-PR-6b | 2026-04-20 | F6.4–F6.10 chore + F6.12 | §2.2.4/§2.5.5/§3.2.4/§3.3.1/§3.4.4 + bib hygiene; 5 net-new [REVIEW] flags in prose; 2 existing bib entries edited (Silva2018LoL pages+ISSN; Porcpine2020EloAoE URL fix) |
| #TBD | (refresh) | 2026-04-21 | Status refresh + F6.6/F6.8 local closures | HF commit history verified v8.0 released 2026-01-25 → §2.5.5/§3.2.4 parentheticals simplified + F6.6 flags removed; ISSN.org portal verified 2179-2259 → F6.8 bib-comment removed |

## Scheduled audit PRs — ALL COMPLETE

The original audit's F-findings map (Pass-2 Code side):

| Finding | Closure status | Closed in |
|---|---|---|
| F4.5 | CLOSED | PR #193 (§2.2.3 Thorrez proxy) |
| F5.1 | CLOSED | PR #191 (§1.1 flag count) |
| F5.2 | CLOSED | PR #191 (THESIS_STRUCTURE footer) |
| F5.3 | CLOSED | PR #191 (§2.2.3 calibration reframe) |
| F5.4 | CLOSED | PR #193 (§4.1.3 literature anchoring) |
| F5.5 | CLOSED | PR #191 (§3.4.3 Elbert placement) |
| F5.6 | FLAG-PLANTED | PR #191 (§3.2 → §3.1.3 swap deferred — readable Demšar 2006 PDF required) |
| F6.1 | CLOSED-WITH-FLAG | PR #194 (4 unverified audit-seed authors recorded in REVIEW_QUEUE §3.5) |
| F6.2 | CLOSED-WITH-FLAG | PR #194 (Elbert PDF verification deferred) |
| F6.3 | CLOSED | PR #194 (§3.5 Luka 4 short restatement) |
| F6.4 | CLOSED-WITH-FLAG | PR #195 (Vinyals2017 PDF section verification deferred; Liquipedia retained as primary) |
| F6.5 | DEFERRED | PR #195 (Patch 2.0.8 date deferred to Pass-2 — requires patch-notes source; standalone §2.2.4 [REVIEW] flag) |
| F6.6 | CLOSED | **PR #TBD (this refresh)** — HF commit `0482ab5` 2026-01-25 verified v8.0 released |
| F6.7 | CLOSED-WITH-FLAG | PR #195 (Yang 9:1 split random-not-temporal prose flag; 60,07%/Kinkade numeric reclassification held in REVIEW_QUEUE) |
| F6.8 | CLOSED | **PR #TBD (this refresh)** — ISSN.org portal verified 2179-2259 = SBGames Proceedings |
| F6.9 | CLOSED-WITH-FLAG | PR #195 (Xie R²-vs-accuracy hypothesis flag) |
| F6.10 | CLOSED | PR #195 (Porcpine URL 404→live + r=0,96 bin-aggregation caveat) |
| F6.11 | CLOSED | PR #190 (TG4 Elbert author corrections Stein Nora→Nikolai, Schenk Amadeus→Alicia) |
| F6.12 | DEFERRED | Blockquote convention — tooling-regression risk; indefinite |

## Remaining work (Claude Chat Pass-2 territory)

The remaining [REVIEW] / [NEEDS CITATION] flags are PDF-read or external-search items that belong in the Claude Chat Pass-2 workflow per `.claude/rules/thesis-writing.md`. They are NOT scheduled for further Claude Code PRs.

### Category 1 — Requires readable primary-source PDF

| Item | Locus | Pass-2 task |
|---|---|---|
| **F5.6 Demšar §3.2 → §3.1.3 swap** | 4 loci: `02_theoretical_background.md:211` (§2.6.3); `04_data_and_methodology.md:213` (§4.1.4); `04_data_and_methodology.md:375` (§4.4.4 inline); `04_data_and_methodology.md:377` (§4.4.4 bibkey) | Read Demšar 2006 JMLR PDF (https://www.jmlr.org/papers/volume7/demsar06a/demsar06a.pdf) §3.1.3 to confirm both N ≥ 5 (CV folds within-game) and N ≥ 10 (datasets cross-dataset) thresholds. If confirmed: swap `§3.2` → `§3.1.3` at all 4 loci and remove F5.6 flags. Line 373 of `04_data_and_methodology.md` already reads `§3.1.3` (TG1) — do NOT touch. García & Herrera 2008 may serve as alternative anchor if Demšar remains inaccessible. |
| **F6.4 Vinyals2017 SC2LE 22.4 loops/sec** | `02_theoretical_background.md:49` [REVIEW] flag | Read Vinyals et al. 2017 arXiv:1708.04782 §3 or §4 (game engine description). If 22.4 figure explicitly stated: promote Vinyals to primary anchor and demote Liquipedia_GameSpeed to secondary; retract line-49 flag. If not: keep both anchors as-is per current wording "[Liquipedia_GameSpeed; potwierdzenie peer-reviewed w Vinyals2017]". |
| **F6.7 Yang 9:1 split semantics + 60,07%/Kinkade numerics** | `03_related_work.md:91` prose flag + REVIEW_QUEUE §3.3 deferral | Read Yang et al. 2017 arXiv:1701.03162. Verify (a) 9:1 split is random not temporal (closes prose flag; retractable); (b) 58,69% is Kinkade-et-al. reimplementation; (c) Yang's own LR on hero features alone = 60,07%. If (b)+(c) confirmed: follow-up PR reclassifies prose numbers. |
| **F6.2 Elbert2025EC attribution method** | `03_related_work.md` §3.5 Luka 2 [REVIEW] flag | Read Elbert et al. 2025 arXiv:2506.04475 ACM EC 2025 extended abstract. Verify linear fixed-effects residualization architecture (vs SHAP marginal attribution). Current prose uses conditional hedge ("jeśli nasze odczytanie jest poprawne"). |
| **Minami2024 primary-source check** | §3.5 Luka 1 citation | Confirm Minami et al. 2024 (DOI 10.1016/j.chb.2024.108351) matches framing: EEG modality, FVG game type, multi-classifier without calibration metrics. |

### Category 2 — Requires external search / database access

| Item | Locus | Pass-2 task |
|---|---|---|
| **F6.1 four seed authors** | REVIEW_QUEUE §3.5 entry | Verify Brookhouse & Buckley 2025; Caldeira et al. 2025; Alhumaid & Tur 2025; Ferraz et al. 2025. WebSearch 2026-04-20 did not surface any (5 query formulations attempted). Claude Chat may have broader access to 2025 proceedings / preprints. |
| **F6.5 Patch 2.0.8 date citation** | `02_theoretical_background.md` §2.2.4 standalone [REVIEW] flag | Acquire patch-notes source for 2013-05-07 NA / 2013-05-08 EU/KR release date. Current `[BlizzardS2Protocol]` bibkey documents protocol version 2.0.8 only, not patch release date. Options: add Liquipedia_SC2Patches bib entry, or find Blizzard-side patch notes URL. |
| **F6.9 Xie2020 Medium R² vs accuracy** | `03_related_work.md` §3.4.4 [REVIEW] flag | Read Xie 2020 Medium post to confirm whether the <2% value is R² (regression context; our hypothesis) or accuracy (terminological error; alternative). Hypothesis planted in prose with explicit hedging; Medium-post read confirms or refutes. |

### Category 3 — Locally closed in this refresh PR

| Item | Closure mechanism |
|---|---|
| **F6.6 EsportsBench v8.0 release state** | HuggingFace commit history (dataset `EsportsBench/EsportsBench`, commit `0482ab5` dated 2026-01-25, message "update to 8.0", 20 parquet files updated, size 351.6 MB → 357.6 MB) verified v8.0 with cutoff 2025-12-31 IS released, not planned. §2.5.5 line 179 + §3.2.4 line 77 parentheticals simplified to `(wersja HuggingFace v8.0, cutoff 2025-12-31)`; F6.6 [REVIEW] flags removed from both loci. §3.5 Luka 3 wording already aligned. Net prose flag delta: −2. |
| **F6.8 SBGames Proceedings ISSN** | ISSN.org portal (https://portal.issn.org/resource/ISSN/2179-2259) verified 2179-2259 = SBGames Proceedings (Confirmed record, Online medium, Brazil, last modified 2024-10-08). Independently corroborated by SBGames 2013 front-matter PDF. `% [REVIEW: F6.8]` BibTeX comment at `references.bib:500` removed; `issn = {2179-2259}` bib field retained unchanged. |

## Current flag inventory (post-refresh)

Matching-line counts for pattern `[REVIEW:|[NEEDS CITATION]` in `thesis/chapters/*.md` (lines containing at least one flag; a single line can carry multiple flags — e.g., `03_related_work.md:77` post-refresh still matches because a pre-existing 80,13% [REVIEW] flag remained after the F6.6 flag removal):

| File | Matching lines | Flag-occurrence delta vs pre-refresh |
|---|---|---|
| `01_introduction.md` | 6 | unchanged |
| `02_theoretical_background.md` | 15 | **−1 occurrence, −1 line** (F6.6 §2.5.5 removed; line 179 no longer matches) |
| `03_related_work.md` | 15 | **−1 occurrence, 0 line delta** (F6.6 §3.2.4 removed at line 77; line retains pre-existing 80,13% flag, still matches) |
| `04_data_and_methodology.md` | 28 | unchanged |
| `07_conclusions.md` | 1 | unchanged |
| `REVIEW_QUEUE.md` (tracking) | 14 | +3 closure notes appended to existing §2.5/§3.2/§3.3 rows (dated annotations, not new flags) |
| **Chapter total (matching lines)** | **65** | **−1 line, −2 flag occurrences** |

## Critical gotchas / lessons

### 1. F5.6 Demšar PDF unverified (from TG5-PR-5a)
WebFetch + WebSearch could not confirm §3.1.3 location for N ≥ 10 threshold. Mode A flagged this as BLOCKER B1/B2 (landing unverified citation would reproduce the defect the audit exists to fix). Plan restructured to flag-planting only. **For any audit-claim primary-source citation, require independent verification before landing as prose.**

### 2. Polish dates — ISO only (from TG3)
User's explicit feedback: **"everyone understand dates in yyyy-mm-dd format... wtf"**. No "od sierpnia 2022 do lutego 2026"-style Polish-idiomatic date phrasing in chapter prose. Em-dash ranges: `2022-08-28 — 2026-02-07`. Saved as `feedback_iso_date_format.md`.

### 3. Cat F planning hook required sections
`.github/hooks/planning-drift` blocks commits where `planning/current_plan.md` lacks these sections (Category F): Problem Statement, Literature Context, Assumptions & Unknowns, Gate Condition, Open Questions, Scope, Execution Steps, File Manifest. **Put these in the plan from the start.**

### 4. `/critic` skill — 3-iteration max (symmetric with reviewer-adversarial)
Per `.claude/commands/critic.md`: dispatch 4 critics → merger → user subset → writer → next iter. Max 3 iterations. User's memory (`feedback_adversarial_cap_execution.md`) extends this cap symmetrically to Mode A/C reviewer-adversarial cycles.

### 5. Chore PR discipline
"No new claims, no bib additions, no methodology changes." F5.3 Thorrez-proxy insertion at §2.2.3 violated this in TG5-PR-5a iter 1 and got deferred to PR-5b. For chore PRs (e.g., PR-6b), keep edits strictly in: citation-location fixes, flag-presence reconciliations, documentation-of-decision sentences, metadata refreshes.

### 6. Three distinct review layers
- **`/critic` skill** — plan-level 4-critics dedup + merger.
- **`reviewer-adversarial` Mode A** — methodology stress-test BEFORE execution; writes `planning/current_plan.critique.md`.
- **`reviewer-adversarial` Mode C** — post-draft stress-test BEFORE commit; in-chat only.

Each catches different defects. Running all three necessary for Cat F thesis work.

### 7. Per-PR isolation + planning purge
Each TG = separate PR. Don't bundle. After merge, `planning/current_plan.md` + `planning/current_plan.critique.md` get purged by either (a) next PR's plan overwriting them, or (b) explicit purge chore PR.

### 8. F4.5 scope migration history (from TG5)
- Originally: audit F4.5 = TG4 science (pass2_dispatch.md:148).
- TG4 (PR #190) landed bibliography hygiene only.
- TG5-PR-5a iter 1 attempted to subsume F4.5 into F5.3; removed per /critic scope R6.
- PR-5b (#193) landed F4.5 at §2.2.3 as Thorrez2024 Glicko-2 80,13% academic-proxy.

### 9. Stale handoff-doc is a real risk (from this refresh)
Prior `pass2_status.md` was never updated after PR #191. It remained at "3.34.0 / 5 PRs merged / 3 remaining" through PR-5b + PR-6a + PR-6b. A stale handoff propagates wrong version trajectories into the next session. **Rule:** refresh `pass2_status.md` immediately after each audit PR merges, not as a deferred chore.

### 10. HuggingFace README ≠ HuggingFace data (from this refresh)
PR-6b drafted the F6.6 parenthetical from the dataset-card README text ("v7.0/v8.0 future planned"). The commit history at that time already had the v8.0 push from 2026-01-25. **Rule:** when verifying dataset-version claims on HuggingFace, check `commits/main` or `Files and versions` tab, not README text alone. README documentation can lag data pushes by months.

### 11. Rapid re-verification beats audit-trust
PR-6b landed factually-incorrect wording (v7.0 "publicznie dostępna"; v8.0 "planowana") despite a same-day WebFetch. The read missed v8.0 release because it followed the README. A 30-second recheck via commit history would have caught it pre-merge. **Lesson:** for date-of-release / version-state claims, verify via version-control artifacts (commits, tags, release notes) not documentation prose.

## Version trajectory (Pass-2 complete)

- 3.29.1 (pre-Pass-2)
- 3.30.0 — TG1 (PR #187)
- 3.31.0 — TG2 (PR #188)
- 3.32.0 — TG3 (PR #189)
- 3.33.0 — TG4 (PR #190)
- 3.34.0 — TG5-PR-5a (PR #191)
- 3.35.0 — TG5-PR-5b (PR #193)
- 3.36.0 — TG6-PR-6a (PR #194)
- 3.37.0 — TG6-PR-6b (PR #195)
- 3.38.0 — Status refresh + F6.6/F6.8 local closures (this PR — docs minor bump)

Post-refresh, the Pass-2 Code track is complete. Any future patch-level bumps (3.38.x) would be single-flag closure PRs (e.g., post-Demšar PDF F5.6 swap; post-Vinyals PDF F6.4 primary anchor swap) triggered by Claude Chat Pass-2 findings that require narrow Code-side cascade.

## How to resume Claude Chat Pass-2

When bringing sections to Claude Chat, provide:
1. The chapter text from `thesis/chapters/XX_*.md` at flag loci listed in the Category 1 / Category 2 tables above
2. The specific `[REVIEW: ...]` / `[NEEDS CITATION]` flag bodies (these name the Pass-2 closure mechanism)
3. Relevant REVIEW_QUEUE.md row entries
4. The PDF or external source being verified (Demšar 2006, Vinyals 2017, Yang 2017, Elbert 2025, Xie 2020 Medium, etc.)

Claude Chat returns: resolved flags, confirmed/rejected audit claims, suggested wording substitutions, any cascade implications for `references.bib` or other chapter prose.

Post-Pass-2 resolutions should be landed in Code as small patch-level PRs (3.38.1, 3.38.2, …) rather than bundled, so each primary-source resolution is traceable to the PDF read that closed it.

## Where to look

- **Audit:** `thesis/reviews_and_others/pass2_dispatch.md`
- **Chapter status:** `thesis/WRITING_STATUS.md` + `thesis/chapters/REVIEW_QUEUE.md`
- **Plan workflow:** `thesis/plans/writing_protocol.md` + `.claude/rules/thesis-writing.md` + `CLAUDE.md` §Plan / Execute Workflow
- **Hook requirements:** `.claude/rules/git-workflow.md` + `.github/hooks/planning-drift`
- **Critic skill:** `.claude/commands/critic.md`
- **Agent manual:** `docs/agents/AGENT_MANUAL.md`
- **This refresh PR scope:** `planning/current_plan.md` not used (housekeeping chore below Cat F threshold); commit + PR describe the scope inline.
