SPEC — Category C — .claude/ dataset-agnostic pass

## Goal
Separate universal scientific principles from SC2-specific empirical
findings in .claude/ rule files. Add explicit pointers to docs/INDEX.md
as the methodology source of truth. Do not invent new content.

## Files to read first (do not edit yet)
- .claude/scientific-invariants.md
- .claude/dev-constraints.md
- .claude/ml-protocol.md
- .claude/rules/thesis-writing.md
- .claude/agents/planner-science.md
- .claude/agents/executor.md (if exists)
- docs/INDEX.md
- src/rts_predict/sc2/reports/sc2egset/01_04_apm_mmr_audit.md
  (canonical home of the APM/MMR findings)

## Edit 1 — Split .claude/scientific-invariants.md

Read the current 10 invariants. Classify each one:

  UNIVERSAL — applies to any dataset, any game. Examples: temporal
  discipline, no magic numbers, symmetric player treatment, query
  reproducibility, cross-game evaluation protocol.

  DATASET-SPECIFIC — depends on a particular dataset's empirical
  findings or a particular game's mechanics. Examples: the 22.4 game
  loop constant (SC2-only), APM-from-2017 usability (SC2EGSet-only),
  MMR-83.6%-zero (SC2EGSet-only).

Rewrite .claude/scientific-invariants.md so that:

  - The header explicitly states: "These invariants are dataset-agnostic
    and game-agnostic. For methodology guidance see docs/INDEX.md.
    For dataset-specific empirical findings see the per-dataset
    invariants file under each game package."

  - Only UNIVERSAL invariants remain in the file, renumbered 1..N
    contiguously.

  - For every invariant that references methodology (cleaning,
    profiling, splitting, evaluation), append a one-line pointer:
    "See docs/INDEX.md → Manual NN_xxx for the authoritative methodology."

  - The cross-game comparability invariant (currently #10) explicitly
    points to docs/ml_experiment_lifecycle/06_CROSS_DOMAIN_TRANSFER_MANUAL.md.

  - Add a final "Per-dataset findings" section with this exact text:
    "Empirical findings about specific datasets (field availability,
    derived constants, observed distributions) live in per-dataset
    invariants files, not here. See:
      - src/rts_predict/sc2/reports/sc2egset/INVARIANTS.md (when created)
      - src/rts_predict/aoe2/reports/<dataset>/INVARIANTS.md (when created)
    These per-dataset files are populated as Phase 1 exploration
    surfaces verifiable findings."

## Edit 2 — Create src/rts_predict/sc2/reports/sc2egset/INVARIANTS.md

Move (not copy) the SC2-specific content out of scientific-invariants.md
into this new file. At minimum:

  - The 22.4 game loop / second derivation, with sources.
  - The APM-from-2017 finding, with a pointer to 01_04_apm_mmr_audit.md.
  - The MMR-83.6%-zero finding with the same pointer.

Header text for the new file:
  "# SC2EGSet — dataset-specific invariants
   These findings apply ONLY to the SC2EGSet dataset and were derived
   from Phase 0/1 exploration. Universal scientific invariants live in
   .claude/scientific-invariants.md. Methodology guidance lives in
   docs/INDEX.md."

## Edit 3 — Update .claude/agents/planner-science.md

In the "Read first" list, replace any SC2-specific references with the
dataset-agnostic equivalent. The new "Read first" list should be:

  1. .claude/scientific-invariants.md  (universal invariants)
  2. docs/INDEX.md  (authoritative methodology source)
  3. The PHASE_STATUS.yaml of the active game package
  4. The active dataset's ROADMAP.md (path determined from PHASE_STATUS)
  5. The active dataset's INVARIANTS.md (if it exists)
  6. reports/research_log.md

In the role description, replace "Plan Phase work (Phases 0-10 of the
SC2 roadmap)" with "Plan Phase work using the methodology defined in
docs/INDEX.md, scoped to the active dataset indicated by PHASE_STATUS.yaml."

Do NOT change anything else in this file. No constraint changes, no
permission changes.

## Edit 4 — Update .claude/rules/thesis-writing.md

Find the "Phase-to-Section Mapping" block at the bottom that uses old
SC2 phase numbers. Replace with:

  "## Phase-to-section mapping
   The authoritative phase vocabulary lives in docs/INDEX.md. Each
   ROADMAP.md's per-step 'Thesis mapping' field is the source of truth
   for which thesis section a given phase output feeds. Do not duplicate
   that mapping here."

Do NOT change anything else in this file.

## Edit 5 — Update CLAUDE.md "Key File Locations" table

Add one row:
  | Per-dataset invariants | `src/rts_predict/<game>/reports/<dataset>/INVARIANTS.md` |

Do NOT touch any other row.

## Hard constraints
- Do NOT touch any other file in the repo.
- Do NOT create new files beyond INVARIANTS.md.
- Do NOT change any code under src/rts_predict/.
- Do NOT touch THESIS_STRUCTURE.md or WRITING_STATUS.md (deferred to LATER.md).
- Preserve git history of moved content via `git mv` where applicable.
  Where content is moved across files (not just renames), preserve it
  via copy-then-delete in two commits within the same PR.

## Acceptance criteria
- .claude/scientific-invariants.md no longer mentions APM, MMR, "22.4",
  "loops/second", "2017", "highestLeague", or any other dataset-specific
  empirical claim.
- .claude/scientific-invariants.md contains at least 3 explicit pointers
  to "docs/INDEX.md" or "docs/ml_experiment_lifecycle/".
- src/rts_predict/sc2/reports/sc2egset/INVARIANTS.md exists and contains
  the moved content with intact source citations.
- .claude/agents/planner-science.md "Read first" list contains
  "docs/INDEX.md" and no longer hardcodes SC2 paths.
- ruff/mypy/pytest green (file moves should not break anything because
  no Python code references these files at import time).

## Out of scope
Anything not listed above. If you find other stale references while
reading, append them to LATER.md instead of fixing them in this PR.