---
# Layer 1 — fixed frontmatter (mechanically validated)
category: F
branch: docs/thesis-ch4-canonical-slot-flag
date: 2026-04-19
planner_model: claude-opus-4-7
dataset: null
phase: null
pipeline_section: null
invariants_touched: [I5]
source_artifacts:
  - planning/CHAPTER_4_DEFEND_IN_THESIS.md
  - planning/BACKLOG.md
  - thesis/chapters/04_data_and_methodology.md
  - thesis/chapters/REVIEW_QUEUE.md
  - thesis/WRITING_STATUS.md
  - reports/specs/01_05_preregistration.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/phase06_interface_aoestats.csv
  - .claude/scientific-invariants.md
  - .claude/rules/thesis-writing.md
  - docs/templates/plan_template.md
critique_required: true
research_log_ref: null
---

# Plan: Chapter 4 DEFEND-IN-THESIS residuals — canonical_slot flag (PR-3 of 3, final)

## Scope

Third and **final** Cat F PR in the DEFEND-IN-THESIS sequence. Closes
**residual #5** (`[PRE-canonical_slot]` flag definition) by creating a
new §4.4.6 "Flaga `[PRE-canonical_slot]` dla aoestats per-slot
analyz" and adding a footnote at §4.1.2.1 at the aoestats
team-conditioned discussion. Also updates `planning/BACKLOG.md` F1
`canonical_slot` Predecessors bullet to reference this PR as the
thesis-side provenance. Small, focused PR (~2.4k Polish chars).

## Problem Statement

PR-1 (`docs/thesis-ch4-corpus-framing-residuals`, merged as PR #175)
and PR-2 (`docs/thesis-ch4-stat-methodology-residuals`, merged as PR
#176) addressed 4 of 6 DEFEND-IN-THESIS residuals. Residual #5 remains:

**The fact.** aoestats `team` column carries a W3 ARTEFACT_EDGE
upstream-API bias (commit `ab23ab1d`): in 1v1 ranked matches, the
higher-ELO player is assigned `team=1` in 80.3% of games with mean
ELO-diff +11.9 (team=1 vs team=0). This is NOT a game-mechanical
asymmetry — it is a data-acquisition artifact. Per spec §11 W3
ARTEFACT_EDGE binding and spec §1 line 71, any 01_05 finding
conditioned on aoestats `team` carries the `[PRE-canonical_slot]`
flag — signaling that the result is **provisional** pending the
Phase 02 `canonical_slot` VARCHAR column that neutralizes the
upstream assignment.

**The examiner question.** "Your aoestats team-conditioned features
are flagged `[PRE-canonical_slot]`. What does that flag mean for
Chapter 4 interpretation?"

**The defense framing (per DEFEND doc line 158–166).** The flag
indicates any team-conditional interpretation is **provisional**
pending a Phase 02 amendment that adds `canonical_slot` to the
aoestats `matches_history_minimal` VIEW. The 01_05 PSI / ICC / DGP
outputs are valid for cross-dataset comparison as long as the flag
is honored — **aggregate (UNION-ALL-symmetric) features are
unaffected** (`faction`, `opponent_faction`, `won` aggregate); only
**per-slot breakdowns** carry the flag. Chapter 4 must enumerate the
flag at every appearance and explicitly defer team-conditional claims
to a post-`canonical_slot` re-analysis. The W3 commit `ab23ab1d`
provides the empirical evidence the examiner can audit.

**Note on artifact state (honest-match principle from PR-1 B1).**
The `[PRE-canonical_slot]` tag is defined in spec §1 line 71 but is
**NOT populated in the aoestats Phase 06 CSV** (grep returns 0
matches in `phase06_interface_aoestats.csv`). This artifact-vs-spec
divergence was identified in PR-1 round-1 critique B1 secondary
finding and filed as Category-D chore in `planning/BACKLOG.md` F6
alongside the `[POP:]` tag backfill. PR-3 §4.4.6 prose describes the
flag as a **methodological convention** from spec §1 (not an
empirical tag visible in the current CSV), documenting the
artifact-vs-spec divergence inline and cross-referencing F6 for the
Category-D closure.

## Assumptions & unknowns

- **Assumption:** Residual #5's DEFEND framing (line 158–166 of
  `CHAPTER_4_DEFEND_IN_THESIS.md`) is authoritative for the flag-
  definition paragraph content.
- **Assumption:** BACKLOG F1 exists and needs a Predecessors bullet
  update to reference "PR-3 of DEFEND-IN-THESIS sequence (§4.4.6 flag
  definition + §4.1.2.1 footnote)". Verify at plan time.
- **Assumption:** §4.1.2.1 currently discusses aoestats team-conditioned
  findings in the "Jakość danych" paragraph (post-PR-1) — the
  specific sentence about "team=1 wygrywa 52,27% meczów" is the
  natural anchor for the footnote. Writer-thesis identifies the
  exact location at draft time.
- **Assumption:** §4.4.6 as a sibling to §4.4.5 uses `###` header.
  Resolved (consistent with B2 precedent from PR-1).
- **Unknown:** Whether BACKLOG F1 has already been updated to
  reference PR-1's F6 entry (PR-1 scope may have touched F1 lightly).
  Writer-thesis re-reads at draft time.
- **Unknown:** Whether §4.1.2.1 needs one footnote (at the 52,27%
  sentence) or two (e.g., also at Tabela 4.2 CONSORT flow if it
  breaks down by team). DEFEND doc says "Chapter 4 footnote at every
  aoestats team-conditioned table" — so if Tabela 4.2 is team-
  conditioned, it needs a footnote too. Verify at draft time.

## Literature context

Primary citations (writer-thesis uses existing bibkeys only; NO new
bibtex entries):

- **Spec §11 W3 ARTEFACT_EDGE binding** (file-path citation):
  `reports/specs/01_05_preregistration.md` §11, line range TBD.
  Defines the `[PRE-canonical_slot]` scope tag.
- **Spec §1 line 71** (file-path citation): definitional statement
  that "any 01_05 finding conditioned on aoestats `team` is flagged
  `[PRE-canonical_slot]`".
- **W3 commit `ab23ab1d`** (commit-hash citation): empirical evidence
  — 80.3% team-to-ELO correlation in aoestats upstream API.
- **`planning/BACKLOG.md` F1** (file-path citation): the Phase 02
  canonical_slot Phase 02 unblocker; PR-3 updates its Predecessors
  bullet.
- **`planning/BACKLOG.md` F6** (file-path citation): Category-D chore
  for aoestats CSV `[POP:]` + `[PRE-canonical_slot]` tag backfill
  (from PR-1); PR-3 cross-references this for the
  artifact-vs-spec divergence note.
- **[AoEStats]** and **[AoeCompanion]** existing bibkeys from §4.1.2.
- **Invariant #5** (`.claude/scientific-invariants.md` #5) —
  symmetric player treatment (per PR-2 M1 fix — this is the correct
  invariant for slot symmetry). §4.4.6 may cite invariant #5 as the
  reason that `canonical_slot` matters: symmetric treatment under
  randomization is the I5 requirement, and `canonical_slot` supports
  it by removing the upstream skill-correlated slot assignment.

No new bibtex entries. All citations use existing bibkeys or
file-path references.

## Execution Steps

### T01 — NEW §4.4.6: Flaga `[PRE-canonical_slot]` dla aoestats per-slot analyz

**Objective:** Create new subsection `### 4.4.6 Flaga
[PRE-canonical_slot] dla aoestats per-slot analyz` after §4.4.5
(post-PR-2 boundary). Defines the flag's scope (per-slot vs
aggregate), attributes its motivation to W3 ARTEFACT_EDGE (commit
`ab23ab1d`), enumerates what the flag covers in Chapter 4, and
cross-references BACKLOG F1 as the Phase 02 unblocker. Documents
the artifact-vs-spec divergence (tag defined in spec §1 but not
populated in aoestats Phase 06 CSV; closes in BACKLOG F6).

**Instructions:**
1. Read §4.4.5 post-PR-2 state (lines TBD — locate via Grep for
   `### 4.4.5`). Confirm §4.4.5 ends cleanly and §4.4.6 fits as a
   sibling `###` header.
2. Read `planning/BACKLOG.md` F1 entry in full to understand the
   Phase 02 canonical_slot unblocker scope. The §4.4.6 prose
   cross-references F1 at the closure paragraph.
3. Draft 3 Polish paragraphs under `### 4.4.6 Flaga
   [PRE-canonical_slot] dla aoestats per-slot analyz`:
   - (a) `**Geneza flagi.**` (~600–800 chars) State the W3
     ARTEFACT_EDGE finding: kolumna `team` w aoestats 1v1 ranked
     wykazuje upstream-API zaburzenie — w 80,3% meczów gracz o
     wyższym ELO ma przypisanie `team=1` (mean ELO-diff +11,9).
     Cytowane z commit `ab23ab1d` oraz spec §11 W3 ARTEFACT_EDGE
     binding (`reports/specs/01_05_preregistration.md` §11). Nie
     jest to asymetria game-mechanical — jest artefakt akwizycji
     danych. Spec §1 linia 71 definiuje flagę `[PRE-canonical_slot]`
     jako scope-tag dla każdego 01_05 findingu uwarunkowanego na
     aoestats `team`.
   - (b) `**Zakres flagi — per-slot vs aggregate.**` (~700–900
     chars) Ranowanie: **per-slot breakdowns** (np. win-rate per
     `team=0` vs `team=1`, ICC stratyfikowane per-slot, PSI feature
     computation na per-slot cechach) niosą flagę jako provisional.
     **(M1 fix — disambiguate raw-schema vs post-Phase-02
     aggregate.)** W schemacie `matches_1v1_clean` civilizacja
     aoestats jest zakodowana per-slot jako dwie kolumny `p0_civ`
     i `p1_civ` (`matches_1v1_clean.yaml:66–70, 95–99`); slot-
     agnostyczne agregaty `faction`, `opponent_faction`, `won`
     (per-gracz, symetryczne) powstają **w Phase 02 po UNION-ALL
     per-gracz** — dopiero tam są one nieobciążone W3 artefaktem
     i nie wymagają flagi. ICC na `won` bez stratyfikacji slot-wise
     (per-gracz UNION-ALL grouping) jest aggregate w tym samym
     sensie — dlatego Tabela 4.7 (§4.4.5) nie nosi flagi. Natomiast
     surowe per-slot cechy z `matches_1v1_clean` wymagają flagi do
     czasu Phase 02 amendment. Randomizacja *focal*/*opponent* w
     Phase 02 (niezmiennik I5 symmetric player treatment)
     neutralizuje zaburzenie na poziomie cech historycznych;
     `canonical_slot` robi to explicite na poziomie widoku
     `matches_history_minimal`.
   - (c) `**Zastosowania flagi w rozdziale 4 i plan zamknięcia.**`
     (~600–800 chars) Chapter 4 wylicza flagę przy każdym per-slot
     rezultacie aoestats — §4.1.2.1 ma przypis `P[PRE]` (patrz T02)
     przy zdaniu o asymetrii stron (team=1 wygrywa 52,27% meczów).
     Tabela 4.2 (CONSORT flow) jest aggregate — bez flagi. Tabela
     4.7 (§4.4.5) jest aggregate ICC na `won` — bez flagi.
     Zamknięcie flagi wymaga Phase 02 amendment dodającego kolumnę
     `canonical_slot VARCHAR` do widoku `matches_history_minimal`
     (per `planning/BACKLOG.md` F1 — priorytet 1, Phase 02
     unblocker). Uzupełniająco, `planning/BACKLOG.md` F6 rejestruje
     artefact-vs-spec rozbieżność: flaga zdefiniowana w spec §1 linia
     71 nie jest explicite populowana w `phase06_interface_aoestats.csv`
     (tag pozostaje **metodologiczną konwencją**, nie metadaną
     artefaktu — zamknięcie via F6).
4. Plant 2 mandatory flags:
   - `[REVIEW: Pass-2 — [PRE-canonical_slot] flag scope per-slot vs
     aggregate; weryfikować, czy raw-schema `p0_civ`/`p1_civ`
     taxonomy + post-Phase-02 UNION-ALL aggregate distinction jest
     czytelna dla examinera]` at end of (b).
   - **(m1 fix — re-scope self-verifying flag)**
     `[REVIEW: Pass-2 — §4.4.6 (c) closure narrative assumes F1
     unexecuted; weryfikować czy stan F1 na master awansował poza
     Predecessors bullet do czasu Pass-2]` at end of (c).
5. Update `thesis/chapters/REVIEW_QUEUE.md`: add a new Pending row
   for §4.4.6. Key artifacts:
   `planning/CHAPTER_4_DEFEND_IN_THESIS.md` Residual #5,
   `planning/BACKLOG.md` F1 + F6, spec §1 line 71 + §11 W3,
   W3 commit `ab23ab1d`.
6. Update `thesis/WRITING_STATUS.md`: add a new row for §4.4.6
   after §4.4.5 row. Status `DRAFTED`, Feeds from: Phase 01 (01_05
   W3 finding + spec §11 binding), Notes: `Drafted 2026-04-19 via
   Residual #5 of CHAPTER_4_DEFEND_IN_THESIS. ~2.0k znaków polskich.
   2 [REVIEW] flags. Defines [PRE-canonical_slot] scope (per-slot
   vs aggregate); cross-refs BACKLOG F1 (Phase 02 unblocker) and
   F6 (artefact backfill).`

**Verification:**
- §4.4.6 header level `###` (sibling to §4.4.5). Per B2 precedent.
- Subsection cites `reports/specs/01_05_preregistration.md` §11 + §1
  line 71 explicitly.
- Subsection cites W3 commit `ab23ab1d` in prose.
- Subsection cross-refs BACKLOG F1 and F6.
- Subsection invokes invariant #5 correctly (symmetric player
  treatment per PR-2 M1 precedent).
- Flag count 2.
- Total Polish chars §4.4.6: **1 800 – 3 500** (widened per M2 fix
  after PR-2 §4.4.5 delivered 5 020 chars at +67% over 3 000 budget;
  empirical pattern shows methodology subsections overshoot 50–70%
  despite planner estimates). If writer-thesis exceeds 3 500, flag
  in Chat Handoff Summary; no budget amendment unless > 4 000.
- REVIEW_QUEUE has new §4.4.6 Pending row.
- WRITING_STATUS has new §4.4.6 row `DRAFTED`.

**File scope:**
- `thesis/chapters/04_data_and_methodology.md` (new §4.4.6)
- `thesis/chapters/REVIEW_QUEUE.md`
- `thesis/WRITING_STATUS.md`

**Read scope:**
- `planning/CHAPTER_4_DEFEND_IN_THESIS.md` Residual #5
- `planning/BACKLOG.md` F1 + F6
- `reports/specs/01_05_preregistration.md` §1 line 71 + §11 W3
- `.claude/scientific-invariants.md` #5

---

### T02 — §4.1.2.1 footnote: `[PRE-canonical_slot]` at aoestats team-conditioned sentence

**Objective:** Add a footnote-style annotation at the §4.1.2.1
existing sentence discussing aoestats team-conditioned asymmetry
("team=1 wygrywa 52,27% meczów") that cross-references §4.4.6 for
the flag definition. This is the **primary enumeration** of the flag
in Chapter 4 per DEFEND doc line 168.

**Instructions:**
1. Read current §4.1.2.1 lines (post-PR-1 — use Grep to locate the
   "team=1 wygrywa 52,27%" sentence). Identify the insertion point.
2. Append to that sentence an inline footnote-style clause or
   bracketed note:
   - Option A (inline clause): Append `— per-slot finding flagowany
     `[PRE-canonical_slot]` (§4.4.6); wynik provisional do Phase 02
     `canonical_slot` unblocker (`planning/BACKLOG.md` F1).`
   - Option B (markdown footnote): Use a `[^pre-canonical-slot]`
     footnote reference; add footnote definition at the end of
     §4.1.2 subsection.
   - Recommend Option A (inline clause): existing §4.1.2.1 already
     uses inline bracketed `[REVIEW]` notes; footnote syntax would
     be inconsistent with established style.
3. Plant 1 flag at the end of the appended clause:
   `[REVIEW: Pass-2 — [PRE-canonical_slot] footnote at §4.1.2.1
   52,27% sentence; verify Polish idiom for "provisional finding"]`.
4. Update `thesis/chapters/REVIEW_QUEUE.md`: extend §4.1.2 Notes cell
   with `**2026-04-19:** [PRE-canonical_slot] footnote added at
   team=1 asymmetry sentence (Residual #5)`; increment flag count
   by 1.
5. Update `thesis/WRITING_STATUS.md`: extend §4.1.2 Notes cell with
   `**2026-04-19:** [PRE-canonical_slot] footnote added (Residual
   #5)`.

**Verification:**
- Footnote clause appears at the §4.1.2.1 "team=1 wygrywa 52,27%"
  sentence.
- Clause cross-references §4.4.6 explicitly.
- Clause cross-references BACKLOG F1 explicitly.
- 1 new flag planted.
- REVIEW_QUEUE §4.1.2 Notes cell extended; flag count incremented.
- WRITING_STATUS §4.1.2 Notes cell extended.

**File scope:**
- `thesis/chapters/04_data_and_methodology.md` (§4.1.2.1 only)
- `thesis/chapters/REVIEW_QUEUE.md`
- `thesis/WRITING_STATUS.md`

**Read scope:**
- `planning/CHAPTER_4_DEFEND_IN_THESIS.md` Residual #5 "where in
  Chapter 4" line 168

---

### T03 — BACKLOG F1 Predecessors bullet update

**Objective:** Update `planning/BACKLOG.md` F1
(`canonical_slot` Phase 02 unblocker) entry's Predecessors bullet
to reference PR-3 of the DEFEND-IN-THESIS sequence as the
thesis-side provenance.

**Instructions:**
1. Read current BACKLOG F1 entry in full. Note the existing
   Predecessors bullet and any other fields that may reference
   thesis state.
2. Append to the Predecessors bullet a line:
   `- Thesis-side provenance: PR-3 of DEFEND-IN-THESIS sequence
   (§4.4.6 flag definition + §4.1.2.1 footnote at 52,27% sentence;
   PR #TBD).`
3. If F1 has a "Priority" or "Status" field, do NOT change it
   (F1 remains priority 1 — Phase 02 unblocker).

**Verification:**
- F1 Predecessors bullet has new line referencing PR-3.
- F1 other fields unchanged.

**File scope:**
- `planning/BACKLOG.md`

**Read scope:**
- (none — self-contained)

---

### T04 — Wrap-up: version bump + CHANGELOG + DEFEND checkbox flip

**Objective:** Bump `pyproject.toml` 3.25.0 → 3.26.0 (minor per
docs-category), add CHANGELOG `[3.26.0]` entry, and flip DEFEND-
IN-THESIS residual #5 checkbox to `[x]`. This is the **final** PR
in the DEFEND-IN-THESIS sequence — all 6 residuals will be `[x]`
after merge.

**Instructions:**
1. Edit `pyproject.toml` line 3: `version = "3.25.0"` → `version = "3.26.0"`.
2. Edit `CHANGELOG.md`:
   - Insert `[3.26.0] — 2026-04-19 (PR #TBD: docs/thesis-ch4-canonical-slot-flag)`
     block between `[Unreleased]` and `[3.25.0]`.
   - Under `[3.26.0]` `### Changed`, list the residual addressed
     (#5), the new §4.4.6 subsection, the §4.1.2.1 footnote, and
     the BACKLOG F1 Predecessors update.
3. Edit `planning/CHAPTER_4_DEFEND_IN_THESIS.md` — flip residual #5
   checkbox:
   - `- [ ] Residual #5 — canonical_slot deferral ...` → `[x] ... (PR #TBD, §4.4.6 + §4.1.2.1 footnote)`
4. **(m2 fix — skip optional closing paragraph)** Do NOT add a
   "sequence complete" paragraph to the DEFEND doc. 6 × `[x]` is
   self-explanatory; a narrative footer is planning-artifact
   housekeeping beyond Cat F scope. Follow-up chore if needed.
5. Commit with message `chore(release): bump version to 3.26.0`.

**Verification:**
- `pyproject.toml` shows `version = "3.26.0"`.
- CHANGELOG `[3.26.0]` section exists.
- DEFEND doc residual #5 checkbox `[x]`.
- All 6 DEFEND residuals are now `[x]`.

**File scope:**
- `pyproject.toml`
- `CHANGELOG.md`
- `planning/CHAPTER_4_DEFEND_IN_THESIS.md`

**Read scope:**
- (none — self-contained admin step)

---

## File Manifest

| File | Action |
|------|--------|
| `thesis/chapters/04_data_and_methodology.md` | Update (NEW §4.4.6 + §4.1.2.1 footnote) |
| `thesis/chapters/REVIEW_QUEUE.md` | Update (1 new Pending row §4.4.6 + §4.1.2 Notes extended) |
| `thesis/WRITING_STATUS.md` | Update (new §4.4.6 row + §4.1.2 Notes extended) |
| `planning/BACKLOG.md` | Update (F1 Predecessors bullet extended) |
| `pyproject.toml` | Update (version 3.25.0 → 3.26.0) |
| `CHANGELOG.md` | Update (new `[3.26.0]` entry) |
| `planning/CHAPTER_4_DEFEND_IN_THESIS.md` | Update (flip residual #5 to `[x]`) |
| `planning/current_plan.md` | Update (this file — commit as provenance) |
| `planning/current_plan.critique.md` | Create (reviewer-adversarial output) |

## Gate Condition

- §4.4.6 present in `thesis/chapters/04_data_and_methodology.md` as
  `### 4.4.6 Flaga [PRE-canonical_slot] dla aoestats per-slot analyz`,
  following §4.4.5.
- §4.1.2.1 footnote appended to the 52,27% team-asymmetry sentence,
  cross-referencing §4.4.6 and BACKLOG F1.
- BACKLOG F1 Predecessors bullet updated with PR-3 thesis-side
  reference.
- 3 new `[REVIEW]` flags (2 in §4.4.6 + 1 in §4.1.2.1 footnote).
- REVIEW_QUEUE has 1 new Pending row (§4.4.6) + §4.1.2 Notes
  extended.
- WRITING_STATUS has new §4.4.6 row `DRAFTED` + §4.1.2 Notes
  extended.
- Total Polish chars: 1 800 – 2 500 (§4.4.6 bulk) + 100–200
  (§4.1.2.1 footnote clause) = 1 900 – 2 700.
- `pyproject.toml` version 3.26.0; CHANGELOG `[3.26.0]` entry
  present.
- DEFEND doc residual #5 checkbox `[x]`; all 6 residuals now `[x]`.
- `planning/current_plan.critique.md` exists and has been read by
  user before execution.
- Pre-commit hooks pass.
- New PR opened on branch `docs/thesis-ch4-canonical-slot-flag`.

## Out of scope

- **Residuals #1, #2, #3, #4, #6.** Already addressed in PR-1
  (#175) and PR-2 (#176). PR-3 touches only residual #5.
- **Category-D chore F6 execution** (aoestats CSV tag backfill).
  This remains a Phase 01 artifact fix scheduled separately from
  the thesis-side work. PR-3 §4.4.6 prose describes the artifact-
  vs-spec divergence honestly without attempting to close F6.
- **Phase 02 `canonical_slot` derivation.** That is BACKLOG F1
  proper — Category A phase work, not Category F thesis writing.
  PR-3 updates F1 Predecessors but does NOT execute F1.
- **Pass-2 resolution of any of the 17 accumulated flags** across
  PR-1 + PR-2 + PR-3. Pass-2 is a separate Claude Chat session.
- **Rewriting PR-1 §4.1.4 residue** ("N=2 Friedman inapplicable per
  Demsar" direct quote from PR-1 — m_r2_1 from PR-2 round 2).
  Deferred to Pass-2.
- **Pre-existing line-159 `#### 4.1.2 Podsumowanie` heading bug.**
  Still deferred to Category-E chore.
- **New bibtex entries.** PR-3 uses only existing bibkeys and
  file-path/commit-hash references.

## Open questions

- **Q1:** Should §4.4.6 cite `commit ab23ab1d` as a Git-hash
  reference or as a `[W3-VERDICT]` artifact shorthand? Resolves by:
  writer-thesis preference matching existing §4.1.2.1 convention
  (which uses `[W3]` or `commit abXXXX`). Verify at draft time.
- **Q2:** Does §4.1.2.1 need exactly ONE footnote (at 52,27%
  sentence) or TWO (also at Tabela 4.2 CONSORT flow if it has a
  per-slot breakdown)? Resolves by: Tabela 4.2 is an aggregate
  CONSORT (rows are stages, not slots), so ONE footnote is
  sufficient. Resolved.
- **Q3:** Should the DEFEND-IN-THESIS doc get a closing "sequence
  complete" paragraph in T04? Resolves by: writer-thesis judgment.
  Recommendation: YES — a 2-sentence footer confirming sequence
  completion (all 6 residuals addressed across 3 PRs, MM-DD-YYYY)
  helps future readers. Low-cost, high-readability.
- **Q4:** Does §4.4.6 need to define the term "aggregate
  (UNION-ALL-symmetric)" more precisely? Or is the examples
  approach (enumerating `faction`, `opponent_faction`, `won`)
  sufficient? Resolves by: writer-thesis preference. Recommendation:
  examples approach suffices for Chapter 4 methodology prose;
  formal definition belongs in §4.3 feature engineering when that
  section is drafted.
- **Q5:** §4.4.6 may cross-reference invariant #5 (symmetric player
  treatment). Verify the §4.4.6 usage does NOT repeat the PR-2 M1
  error (conflating invariant #5 with matchmaking-equalization).
  Resolves by: writer-thesis reviews M1 resolution in round-2
  critique before drafting; §4.4.6 references invariant #5 as "the
  requirement for symmetric player treatment" — which is the
  actual invariant #5 content.
