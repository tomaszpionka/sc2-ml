---
category: F
branch: docs/thesis-4.2.2-identity-meta-rule
date: 2026-04-19
planner_model: claude-opus-4-7
dataset: null
phase: null
pipeline_section: null
invariants_touched: [I2]
source_artifacts:
  - planning/BACKLOG.md
  - thesis/chapters/04_data_and_methodology.md
  - thesis/chapters/REVIEW_QUEUE.md
  - thesis/WRITING_STATUS.md
  - .claude/scientific-invariants.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/INVARIANTS.md
  - .claude/rules/thesis-writing.md
  - docs/templates/plan_template.md
  # sc2egset worldwide-identity artifact listed in T01 Read scope directly;
  # rates are re-cited via sc2egset INVARIANTS.md §2 (authoritative citation surface)
critique_required: true
research_log_ref: null
---

# Plan: thesis §4.2.2 revision + `Plan Phase 02 (I2)` row correction (F3)

## Scope

Closes BACKLOG F3. Revises `thesis/chapters/04_data_and_methodology.md`
§4.2.2 "Rozpoznanie tożsamości gracza" to reflect the **5-branch
decision procedure** from `.claude/scientific-invariants.md` I2
extended procedure (lines 31–127). Corrects the `Plan Phase 02 (I2)`
row of Tabela 4.5 to name each dataset's declared branch (sc2egset
(iii) / aoestats (v) / aoe2companion (i)). Updates REVIEW_QUEUE and
WRITING_STATUS (§4.2.2 DRAFTED → REVISED).

## Problem Statement

§4.2.2 drafted in PR #150 before I2 meta-rule extension in PR #160.
Each dataset's INVARIANTS.md §2 now declares a specific branch with
measured rates:

- **sc2egset** — Branch **(iii)** `player_id_worldwide`;
  `migration_rate ≈ 12%`, `collision_rate = 30.6%`
  (`INVARIANTS.md:50–51`).
- **aoestats** — Branch **(v)** structurally-forced `profile_id`;
  no visible-handle column, Steps 2–3 unevaluable
  (`INVARIANTS.md:24, 31, 41–42`).
- **aoe2companion** — Branch **(i)** `profileId`;
  `migration_rate = 2.57%`, `collision_rate = 3.55%`
  (`INVARIANTS.md:50–51`).

Current §4.2.2 prose treats `LOWER(nickname)` as default Phase 02
canonicalization; the `Plan Phase 02 (I2)` row of Tabela 4.5 reflects
the same pre-meta-rule framing. A committee examiner comparing §4.2.2 to any INVARIANTS.md
§2 will find contradiction.

Prose additions per F3 scope: **three worked examples** (one per
dataset) + **one framework-completeness note** stating that Branch (ii)
is available in the framework for replication work on handle-only ladder
exports but is not instantiated by any corpus in this thesis.

## Assumptions & unknowns

- **Assumption:** I2 extended procedure at
  `.claude/scientific-invariants.md:31–127` is authoritative. Each
  dataset's INVARIANTS.md §2 authoritative for its branch.
- **Assumption:** The §4.2.2 revision documents the 5-branch framework in
  terms of *the thesis's three real corpora* (sc2egset (iii), aoestats (v),
  aoe2companion (i)). Branch (ii) is included for framework-completeness
  only — it is not instantiated by any dataset in this thesis. The
  completeness note will state that Branch (ii) applies to replication
  work on handle-only ladder exports (e.g. chess.com-style platforms if
  their API-namespace ID were absent) and names chess.com as an indicative
  example, not as a worked case.
- **Assumption:** All rate figures verbatim-citable from INVARIANTS.md §2.
  The pre-execution reviewer-adversarial pass (2026-04-19) surfaced a
  three-way artifact disagreement on the aoe2companion collision_rate
  (INVARIANTS.md 3.7% vs 01_04_04 primary artifact 3.55% vs research_log
  2026-04-18 snapshot 3.7%); root cause was a missing rm_1v1 scope filter
  in the INVARIANTS.md SQL. Reconciled in this PR under Category D work
  (see aoe2companion research_log.md 2026-04-19 entry); INVARIANTS.md §2
  now reports 2.57% / 3.55% matching the 01_04_04 primary-artifact
  snapshot. No T01-time spot-check required.
- **Assumption:** `references.bib` retains [FellegiSunter1969] +
  [Christen2012DataMatching]; **no new bibkeys**.
- **Unknown:** Prune or retain existing REVIEW flag at line 235
  (`interpretacja toon_id > nickname`)? Resolved: **prune**.
  Justification: the Branch (iii) selection does not depend on
  resolving the rebranding-vs-generic-reuse sub-hypothesis — the
  aggregate bias documentation (12% `migration_rate`) is sufficient
  for I2 Step 4. The flag's underlying question is therefore not a
  blocker; pruning avoids an unresolvable open question in the final
  text.
- **Unknown:** `[Christen2012DataMatching]` "5% blocking threshold"
  framing? Resolved: **drop** that specific framing per
  `.claude/scientific-invariants.md:109–112` explicit disclaimer;
  textbook citation retained.

## Literature context

- **[FellegiSunter1969]** — retain.
- **[Christen2012DataMatching]** — retain, drop "5% threshold"
  framing.
- **`.claude/scientific-invariants.md` I2** — authoritative
  methodology source (file-path citation).
- **Per-dataset `INVARIANTS.md §2`** — authoritative per-corpus
  branch declarations.

**No new bibtex entries.**

### Polish-idiom dictionary (one-pass, pre-T01)

The following load-bearing English terms appear in every branch example
and in the framework definition. Resolved here to avoid global re-edit
during Pass 2:

| English | Polish |
|---|---|
| tolerance gate | próg tolerancji |
| API namespace ID | identyfikator przestrzeni nazw API |
| visible handle | pseudonim widoczny |
| rename-stable | odporny na zmianę pseudonimu |
| framework-completeness note | uwaga o kompletności ram decyzyjnych |

Executor uses these renderings verbatim in paragraphs 2–4 of §4.2.2. Any
deviation must be flagged as a Pass-2 REVIEW item.

### Citation-surface convention

"Read primary derivation artifact; cite `INVARIANTS.md §2` summary." This
convention holds *only when INVARIANTS.md §2 numerically matches the
primary derivation artifact*. As of this PR, all three datasets satisfy
that condition (sc2egset and aoestats inherently, aoe2companion after the
2026-04-19 reconciliation recorded in aoe2companion research_log.md).

## Execution Steps

> **Pre-execution (parent responsibility):** Parent dispatches
> `reviewer-adversarial` to produce `planning/current_plan.critique.md`
> before any executor begins T01. This file is not created by any of
> T01–T04; it is a prerequisite artifact owned by the parent/reviewer-
> adversarial agent. If `planning/current_plan.critique.md` is absent
> when T01 dispatch begins, executor halts and reports to parent before
> proceeding.

### T01 — §4.2.2 prose rewrite

**Objective:** Rewrite §4.2.2 paragraphs 2–4 (lines ~235, 237, 239 on
master `28800a2e`) with 5-branch procedure + 3 branch examples +
Branch (ii) framework-completeness note. Preserve paragraph 1
(FellegiSunter/Christen).
Retain paragraph 5 — minimalism (line 241) content; add one cross-ref
sentence. Preserve Forward reference structural role (line 261);
wording revised per step 8.

**Instructions:**
1. Read §4.2.2 lines 231–261 on master. Read I2 extended procedure
   `.claude/scientific-invariants.md:31–127`. Read each dataset's
   INVARIANTS.md §2. Also read sc2egset worldwide-identity artifact
   (`src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_04b_worldwide_identity.md`)
   as the primary source; rates are re-cited via sc2egset INVARIANTS.md
   §2 as the authoritative citation surface.
2. Keep paragraph 1 (line 233) unchanged.
3. **§4.2.2 currently contains exactly 3 REVIEW flags (lines 235, 239,
   261 on master `28800a2e`). Plan: prune 1 (line 235), retain 2
   (lines 239, 261), plant 2 new → total 4.**
4. Replace paragraphs 2–4 (lines 235, 237, 239) with a rewritten block
   (~2 200–3 400 Polish chars; estimated range includes a 50% buffer
   based on observed paragraph-expansion empirics in prior Cat F PRs):

   - **(a) Formal operationalisation.** I2 default `LOWER(nickname)`
     is deferred to Phase 02 as a *canonicalization step*, but
     **choice of canonical key** is dataset-specific and declared
     upstream via the 5-branch procedure. Cite
     `.claude/scientific-invariants.md` §I2 Step 1–4. Sketch the 5
     branches in 1–2 sentences each. **Bridge sentence** tying the
     new I2 framing to paragraph 1's classical record-linkage
     citations: frame the 5-branch procedure as an *a priori*
     identity-schema selection that, in the presence of structurally
     high-quality identifiers, reduces the classical Fellegi–Sunter
     match/non-match/possible-match decision to a choice among five
     pre-defined schemas — so paragraph 1's [FellegiSunter1969] +
     [Christen2012DataMatching] citations remain the formal backbone
     and I2 is the operationalisation for corpora with existing
     provider-level identifiers.
     `[REVIEW: Pass-2 — 5-branch procedure prose; Polish terms
     applied verbatim from plan dictionary (próg tolerancji,
     identyfikator przestrzeni nazw API, pseudonim widoczny, odporny
     na zmianę pseudonimu) — verify idiomatic fit in full paragraph
     context and flag any alternatives surfacing during supervisor
     review]`

   - **(b) sc2egset worked example — Branch (iii).** Name
     `player_id_worldwide` (full `R-S2-G-P` Battle.net toon_id).
     Cite `migration_rate ≈ 12%` + `collision_rate = 30.6%` with
     anchor (sc2egset `INVARIANTS.md:50–51`). Reject the
     `(LOWER(nickname), server-hash)` composite by citing
     INVARIANTS.md lines 61–62 (no measurable improvement over
     `player_id_worldwide`); note maintenance burden as secondary
     context only, not as the decision criterion. State that 12%
     cross-region fragmentation is accepted bias because (1) manual
     record-linkage recovery of the 294 Class A cross-region
     candidate pairs is deferred to future work (per sc2egset
     INVARIANTS.md §2 line 55 — "deferred to a future manual-curation
     upgrade path"), and (2) downstream Phase 02 does not join
     sc2egset rows to cross-region signals, so the fragmentation does
     not propagate leakage. Do not present this as a bare assertion.

   - **(c) aoe2companion worked example — Branch (i).** Name
     `profileId` (INTEGER) from aoe2insights.com API. Cite
     `migration_rate = 2.57%` + `collision_rate = 3.55%` (aoec
     `INVARIANTS.md:50–51`, reconciled 2026-04-19 to match 01_04_04
     primary artifact). Mirror I2 Step 3 Branch (i) definition
     verbatim: API-namespace ID preferred when
     `migration_rate < collision_rate` on the visible handle (here
     2.57% < 3.55%); the API-issued identifier is rename-stable and
     globally scoped within the aoe2insights.com namespace. Do not
     restructure I2's branch definition into a two-step test.

   - **(d) aoestats declared-branch example — Branch (v) (no
     in-dataset rate validation; cross-dataset namespace
     corroboration).** Name `profile_id` (BIGINT), honestly flagged
     Branch (v) structurally-forced. aoestats schema has no visible-
     handle column; Steps 2–3 unevaluable within aoestats alone. Cite
     aoestats `INVARIANTS.md:24, 31, 41–42` for the structural forced
     assignment. Then add one sentence citing the *cross-dataset
     namespace-coincidence check* (aoestats `INVARIANTS.md:46–61`,
     VERDICT A, 0.9960 agreement on a reservoir sample of 1,000
     matches): aoestats `profile_id` and aoe2companion `profileId`
     share the same namespace. This *corroborates* the namespace
     choice but does not transitively validate rate-based decidability
     within aoestats (rates remain structurally unevaluable); it
     reframes (d) from "forced by missing data" to "forced by missing
     data, namespace alignment corroborated across corpora."

   - **(e) Framework-completeness note — Branch (ii).** State
     explicitly that Branch (ii) — `LOWER(name)` canonicalisation —
     is not instantiated by any corpus in this thesis; it is
     preserved in the framework to accommodate *replication work on
     handle-only ladder exports* where no stable API-namespace ID
     exists and collision rate falls below a project-set tolerance
     (per I2 Step 3). Name chess.com-style handle-only platforms as
     an indicative class (not a worked example), and explicitly flag
     that the thesis does not empirically evaluate Branch (ii). This
     completeness note defends the framework's five-branch shape
     without over-claiming; examiners cannot challenge a worked
     example that the chapter declines to make.
     `[REVIEW: Pass-2 — Branch (ii) completeness-note prose; verify
     Polish idiom and confirm PJAIT acceptance of framework-
     completeness framing without empirical instantiation]`

5. Retain paragraph 5 — minimalism (line 241) content unchanged;
   append one sentence cross-referencing I2 extended procedure
   (lines 31–127). Preserve the Forward-reference paragraph's
   structural role; flag wording at line 261 revised per step 8.
6. **Prune** existing REVIEW flag at line 235 (pruned because (a)
   Branch (iii) selection does not depend on resolving the
   rebranding-vs-generic-reuse sub-hypothesis, AND (b) this
   interpretive question is unresolvable within §4.2.2's scope
   without additional empirical work beyond the PR's declared scope.
   Aggregate bias documentation (12% migration_rate) is sufficient
   for I2 Step 4; the sub-hypothesis decomposition is explicitly
   deferred to future work).
7. **Retain** existing REVIEW flag at line 239 (cardinality
   discrepancy 2 308 187 vs 2 468 478).
8. **Retain** existing REVIEW flag at line 261 (nickname
   wieloakcountowość) — revise wording to reference 5-branch
   framework; keep Pass-2 flag.

**Verification:**
- Paragraph 1 preserved; paragraph 5 retains minimalism content +
  gains one cross-ref sentence; Forward reference structural role
  preserved with revised flag wording; paragraphs 2–4 replaced.
- 3 branch examples with labels + file anchors (aoestats example
  records Steps 2–3 unevaluable per Branch (v), cross-validated by
  the aoec namespace bridge).
- 1 framework-completeness note stating Branch (ii) is not
  instantiated by any thesis corpus; chess.com-style handle-only
  platforms named as indicative class only, not a worked example.
- `scientific-invariants.md §I2` cited.
- 4 REVIEW flags total (2 new + 2 retained; pruned 1).
- Total §4.2.2 rewrite: 2 200–3 400 Polish chars.
- No '5% record-linkage blocking' or '5% threshold' phrase appears in
  the rewritten §4.2.2.

**File scope:**
- `thesis/chapters/04_data_and_methodology.md` (§4.2.2 paragraphs
  2–4)

**Read scope:**
- `.claude/scientific-invariants.md` §I2
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md` §2
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md` §2
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/INVARIANTS.md` §2
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_04b_worldwide_identity.md`
  (primary source for sc2egset worldwide-identity rates; citation surface = INVARIANTS.md §2)

---

### T02 — Tabela 4.5 `Plan Phase 02 (I2)` row correction

**Objective:** Correct the `Plan Phase 02 (I2)` row to name declared
branches; rename label to `Klucz kanoniczny (I2 §2)`.

**Instructions:**
1. Locate the "Plan Phase 02 (I2)" row in Tabela 4.5.
2. Replace values:
   - sc2egset: `player_id_worldwide (branch (iii)); ~12% cross-region accepted bias`
   - aoestats: `profile_id (branch (v), structurally-forced — no visible handle)`
   - aoe2companion: `profileId (branch (i)); rename-stable`
3. Rename row label `Plan Phase 02 (I2)` → `Klucz kanoniczny (I2 §2)`.

**Verification:**
- Row label renamed.
- Three cells name branches + keys matching INVARIANTS.md §2
  verbatim.

**File scope:**
- `thesis/chapters/04_data_and_methodology.md` (Tabela 4.5)

---

### T03 — REVIEW_QUEUE + WRITING_STATUS updates

**Instructions:**
1. Extend `thesis/chapters/REVIEW_QUEUE.md` §4.2.2 Notes cell with
   F3 revision summary. Record post-rewrite line anchors for the two
   *new* REVIEW flags planted in T01 step 4 — one in the Formal
   operationalisation paragraph (step 4(a)), one in the
   framework-completeness note (step 4(e)) — so Pass 2 can locate
   them without re-grepping. Also record post-rewrite anchors for the
   two retained flags (originally lines 239 and 261 on master
   `28800a2e`; the line numbers will shift after paragraphs 2–4 are
   replaced).
2. Flip `thesis/WRITING_STATUS.md` §4.2.2 status DRAFTED → REVISED;
   extend Notes; bump "Last updated: 2026-04-19".

**File scope:**
- `thesis/chapters/REVIEW_QUEUE.md`
- `thesis/WRITING_STATUS.md`

---

### T04 — Wrap-up

**Instructions:**
1. Remove F3 entry from `planning/BACKLOG.md`.
2. Verify `[3.26.3]` CHANGELOG header already reads `PR #180`
   (pre-applied in working tree; no edit needed).
3. Bump `pyproject.toml` 3.26.3 → 3.27.0 (minor per Category
   F/docs convention in git-workflow.md).
4. Insert CHANGELOG `[3.27.0]` entry summarising F3 work.

**File scope:**
- `planning/BACKLOG.md`
- `pyproject.toml`
- `CHANGELOG.md`

## File Manifest

| File | Action |
|------|--------|
| `thesis/chapters/04_data_and_methodology.md` | Update (§4.2.2 + Tabela 4.5 row) |
| `thesis/chapters/REVIEW_QUEUE.md` | Update |
| `thesis/WRITING_STATUS.md` | Update (DRAFTED → REVISED) |
| `planning/BACKLOG.md` | Update (remove F3) |
| `pyproject.toml` | Update (3.26.3 → 3.27.0) |
| `CHANGELOG.md` | Update (`[3.27.0]`; `[3.26.3]` already reads #180) |
| `planning/current_plan.md` | Update (provenance) |

## Gate Condition

- §4.2.2: 3 branch examples + Branch (ii) framework-completeness note.
- Tabela 4.5 `Plan Phase 02 (I2)` row renamed `Klucz kanoniczny
  (I2 §2)` with branch values.
- 4 REVIEW flags in §4.2.2 (2 new + 2 retained).
- REVIEW_QUEUE + WRITING_STATUS updated; §4.2.2 REVISED.
- BACKLOG F3 removed.
- Version 3.27.0; CHANGELOG `[3.27.0]`.
- Pre-commit hooks pass.
- Adversarial review completed; `planning/current_plan.critique.md`
  present on disk (parent responsibility, pre-T01).
- PR opened.

## Out of scope

- Other §4.2 subsections; other Chapter 4 tables.
- Phase 02 identity-resolution implementation.
- Revising per-dataset INVARIANTS.md §2.
- New bibtex entries.
- Pass-2 prose polish.

## Open questions

- **Q1:** chess.com stress-test hypothetical vs real? Resolved:
  neither — replaced with framework-completeness note (Branch (ii)
  not instantiated by any thesis corpus; chess.com named as
  indicative class only).
- **Q2:** Rename Tabela 4.5 row label? Resolved YES →
  `Klucz kanoniczny (I2 §2)`.
- **Q3:** Drop [Christen2012DataMatching]? Resolved NO; drop only
  "5% threshold" framing.
- **Q4:** Worked-example citations style? Resolved: line numbers.
