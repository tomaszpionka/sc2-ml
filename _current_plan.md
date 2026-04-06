# Current Plan: Per-Dataset Reports Structure Migration

**Category:** Chore (code infrastructure)
**Branch:** `chore/per-dataset-reports`
**Estimated steps:** 12
**Complexity:** Low per step, high total surface area (many files touched)

---

## Context

Reports currently live flat in `src/rts_predict/<game>/reports/`. This works for
SC2 (one dataset: sc2egset) but breaks for AoE2 (two datasets: aoe2companion,
aoestats) — Phase 0–2 artifacts would collide on filenames like `00_01_*.json`.

The fix: introduce per-dataset report subdirectories for dataset-scoped work
(Phases 0–2), keep game-level reports in the parent `reports/` for game-scoped
work (Phases 3+). Split the monolithic `SC2_THESIS_ROADMAP.md` into a
dataset-level ROADMAP and a game-level ROADMAP.

**Design decision (from Claude Chat analysis):**

```
src/rts_predict/<game>/reports/
├── <dataset>/                    # Dataset-scoped artifacts (Phases 0–2)
│   ├── ROADMAP.md                # Dataset-level roadmap
│   └── 00_01_source_audit.json   # Phase artifacts
├── ROADMAP.md                    # Game-level roadmap (Phases 3+)
└── 03_01_games_table.md          # Game-scoped artifacts (future)
```

---

## Pre-flight checks

Before starting, verify:
- [ ] `git status` is clean (no uncommitted changes)
- [ ] All tests pass: `poetry run pytest`
- [ ] You are on `main` or a clean feature branch

---

## Step 1 — Create dataset report directories

Create the subdirectory structure. No files moved yet.

```bash
mkdir -p src/rts_predict/sc2/reports/sc2egset
mkdir -p src/rts_predict/aoe2/reports/aoe2companion
mkdir -p src/rts_predict/aoe2/reports/aoestats
```

**Verification:** `ls -d src/rts_predict/*/reports/*/` shows all three dirs.

---

## Step 2 — Move SC2 Phase 0 artifacts into `reports/sc2egset/`

Use `git mv` to preserve history. These are all dataset-scoped (produced by
Phase 0 ingestion audit against sc2egset data).

```bash
cd src/rts_predict/sc2/reports
git mv 00_01_source_audit.json sc2egset/
git mv 00_02_tournament_name_validation.txt sc2egset/
git mv 00_03_replay_id_spec.md sc2egset/
git mv 00_04_path_a_smoke_test.md sc2egset/
git mv 00_05_full_ingestion_log.txt sc2egset/
git mv 00_07_path_b_extraction_log.txt sc2egset/
git mv 00_08_join_validation.md sc2egset/
git mv 00_09_map_translation_coverage.csv sc2egset/
```

**Verification:** `ls sc2egset/00_*` shows 8 files. `ls 00_*` in parent shows nothing.

---

## Step 3 — Move SC2 Phase 1 artifacts into `reports/sc2egset/`

Same pattern — all Phase 1 exploration artifacts are dataset-scoped.

```bash
# Still in src/rts_predict/sc2/reports/
git mv 01_01_corpus_summary.json sc2egset/
git mv 01_01_player_count_anomalies.csv sc2egset/
git mv 01_01_result_field_audit.md sc2egset/
git mv 01_01_duplicate_detection.md sc2egset/
git mv 01_02_parse_quality_by_tournament.csv sc2egset/
git mv 01_02_parse_quality_summary.md sc2egset/
git mv 01_03_duration_distribution.csv sc2egset/
git mv 01_03_duration_distribution_full.png sc2egset/
git mv 01_03_duration_distribution_short_tail.png sc2egset/
git mv 01_04_apm_mmr_audit.md sc2egset/
git mv 01_05_patch_landscape.csv sc2egset/
git mv 01_06_event_type_inventory.csv sc2egset/
git mv 01_06_event_count_distribution.csv sc2egset/
git mv 01_06_event_density_by_year.csv sc2egset/
git mv 01_06_event_density_by_tournament.csv sc2egset/
git mv 01_07_playerstats_sampling_check.csv sc2egset/
```

**Note:** If any files from Step 1.8 (game settings audit) already exist
(`01_game_settings_audit.md`, `01_field_completeness_summary.csv`,
`01_error_flags_audit.csv`), move those too. If they don't exist yet,
no action needed — they'll be created directly in `sc2egset/` when Step 1.8
is executed.

**Verification:** `ls sc2egset/01_*` shows 16 files. `ls 01_*` in parent shows nothing.

---

## Step 4 — Move the `archive/` directory

If `src/rts_predict/sc2/reports/archive/` exists (containing `ARCHIVE_SUMMARY.md`),
move it into the dataset subdirectory — it's sc2egset-specific historical content.

```bash
# Only if archive/ exists:
git mv archive sc2egset/archive
```

**Verification:** Check. If `archive/` didn't exist, skip.

---

## Step 5 — Split `SC2_THESIS_ROADMAP.md` into two files

This is the most important step. The current monolithic roadmap must be split:

**A) Dataset-level roadmap → `reports/sc2egset/ROADMAP.md`**

Contents: everything from the top of `SC2_THESIS_ROADMAP.md` through Phase 2
(inclusive), including the reference section (game loop timing table), Phase 0,
Phase 1, Phase 2, and the Appendix — Artifact index (updated for new paths).

Add a header note:

```markdown
# SC2EGSet Dataset Roadmap — Phases 0–2

**Scope:** Dataset-specific exploration, profiling, and player identity resolution
for the SC2EGSet v2.1.0 dataset.

**Game-level roadmap (Phases 3–10):** `../ROADMAP.md`

---
```

**B) Game-level roadmap → `reports/ROADMAP.md`**

Contents: Phases 3–10 from the current `SC2_THESIS_ROADMAP.md`.

Add a header note:

```markdown
# SC2 Game Roadmap — Phases 3–10

**Scope:** Game-level pipeline from games table construction through model
evaluation. Operates on unified analytical views, not raw dataset artifacts.

**Dataset roadmap (Phases 0–2):** `sc2egset/ROADMAP.md`

---
```

**C) Delete the old file:**

```bash
git rm src/rts_predict/sc2/reports/SC2_THESIS_ROADMAP.md
```

**Important details for the split:**

- All `reports/XX_YY_name.ext` references within Phases 0–2 must be updated
  to just the filename (since they're now relative to the dataset directory).
  No path prefix needed — the ROADMAP lives in the same directory as the artifacts.
- All `reports/XX_YY_name.ext` references within Phases 3–10 keep their
  current form (game-level artifacts stay in the parent `reports/` directory).
- The Phase 2 artifacts list includes DuckDB tables (`player_appearances`,
  `canonical_players`) — these are dataset-scoped (they live in the sc2egset
  DuckDB file), so they belong in the dataset roadmap.

**Verification:**
- `wc -l reports/sc2egset/ROADMAP.md` and `wc -l reports/ROADMAP.md` should
  roughly sum to the original line count of `SC2_THESIS_ROADMAP.md` plus ~20
  lines for headers/cross-references.
- `grep -c 'reports/' reports/sc2egset/ROADMAP.md` — zero hits (all refs are
  now relative filenames within the same dir). Exception: cross-references to
  `../ROADMAP.md` in the header.

---

## Step 6 — Move `sanity_validation.md` if it exists

Check if `src/rts_predict/sc2/reports/sanity_validation.md` exists. If yes,
it's dataset-scoped → `git mv` to `sc2egset/`.

---

## Step 7 — Update `src/rts_predict/sc2/config.py`

Add the dataset-scoped reports path constant:

```python
# After the existing REPORTS_DIR line:
DATASET_REPORTS_DIR: Path = REPORTS_DIR / "sc2egset"
```

**Do NOT remove `REPORTS_DIR`** — it's still needed for game-level reports.

---

## Step 8 — Update `src/rts_predict/aoe2/config.py`

Add dataset-scoped report path constants:

```python
# After the existing REPORTS_DIR line:
AOE2COMPANION_REPORTS_DIR: Path = REPORTS_DIR / "aoe2companion"
AOESTATS_REPORTS_DIR: Path = REPORTS_DIR / "aoestats"
```

---

## Step 9 — Update `audit.py` and `exploration.py` output paths

These modules write report artifacts. All output paths must point to
`DATASET_REPORTS_DIR` instead of `REPORTS_DIR`.

**File: `src/rts_predict/sc2/data/audit.py`**

Find every `REPORTS_DIR /` reference in output path construction and replace
with `DATASET_REPORTS_DIR`. Import `DATASET_REPORTS_DIR` from config.

Affected functions (check each one):
- `audit_raw_data_availability()` → writes `00_01_source_audit.json`
- `validate_tournament_names()` → writes `00_02_*`
- `validate_replay_ids()` → writes `00_03_*`
- `run_path_a_smoke_test()` → writes `00_04_*`
- `validate_path_ab_join()` → writes `00_08_*`
- `run_map_translation_audit()` → writes `00_09_*`

**File: `src/rts_predict/sc2/data/exploration.py`**

Same pattern. Import `DATASET_REPORTS_DIR`, replace all `REPORTS_DIR /` in
output path construction.

Affected functions (all Step 1.x outputs):
- `step_1_1_corpus_counts()` → writes `01_01_*`
- `step_1_2_parse_quality()` → writes `01_02_*`
- `step_1_3_duration_distribution()` → writes `01_03_*`
- `step_1_4_apm_mmr_audit()` → writes `01_04_*`
- `step_1_5_patch_landscape()` → writes `01_05_*`
- `step_1_6_event_inventory()` → writes `01_06_*`
- `step_1_7_playerstats_check()` → writes `01_07_*`

**Verification:** `grep -rn 'REPORTS_DIR' src/rts_predict/sc2/data/audit.py`
should show zero hits for direct artifact writes (only `DATASET_REPORTS_DIR`).
Same for `exploration.py`. `REPORTS_DIR` may still appear in imports or
non-artifact contexts — that's fine.

---

## Step 10 — Update PHASE_STATUS.yaml files

**SC2 (`src/rts_predict/sc2/PHASE_STATUS.yaml`):**

Replace:
```yaml
roadmap: src/rts_predict/sc2/reports/SC2_THESIS_ROADMAP.md
```

With:
```yaml
dataset_roadmap: src/rts_predict/sc2/reports/sc2egset/ROADMAP.md
game_roadmap: src/rts_predict/sc2/reports/ROADMAP.md
current_dataset: sc2egset
```

**AoE2 (`src/rts_predict/aoe2/PHASE_STATUS.yaml`):**

Replace:
```yaml
roadmap: src/rts_predict/aoe2/reports/AOE2_THESIS_ROADMAP.md
```

With:
```yaml
dataset_roadmap: null  # Will be set when first dataset roadmap is created
game_roadmap: src/rts_predict/aoe2/reports/ROADMAP.md
current_dataset: null
```

Delete `src/rts_predict/aoe2/reports/AOE2_THESIS_ROADMAP.md` (placeholder)
and create `src/rts_predict/aoe2/reports/ROADMAP.md` as a placeholder instead:

```markdown
# AoE2 Game Roadmap — Phases 3+

**Status:** Placeholder. Will be authored after SC2 pipeline reaches Phase 3.

Dataset roadmaps will be created per-dataset when AoE2 work begins:
- `aoe2companion/ROADMAP.md`
- `aoestats/ROADMAP.md`
```

---

## Step 11 — Update ARCHITECTURE.md and documentation

**A) `ARCHITECTURE.md` — Game package contract table:**

Replace the row:
```
| `reports/<GAME>_THESIS_ROADMAP.md` | Authoritative execution plan | Yes |
```

With:
```
| `reports/ROADMAP.md` | Game-level execution plan (Phases 3+) | Yes |
| `reports/<dataset>/ROADMAP.md` | Dataset-level execution plan (Phases 0–2) | Per dataset |
| `reports/<dataset>/` | Dataset-scoped phase artifacts | Per dataset |
```

**B) `ARCHITECTURE.md` — "Adding a new game" section:**

Update step 3 from:
```
3. Create `<GAME>_THESIS_ROADMAP.md` in the reports directory
```

To:
```
3. Create `reports/ROADMAP.md` (game-level placeholder)
4. Create `reports/<dataset>/ROADMAP.md` per dataset
```

Renumber subsequent steps.

**C) `CLAUDE.md` — Key File Locations table:**

Replace:
```
| Roadmap | `src/rts_predict/sc2/reports/SC2_THESIS_ROADMAP.md` |
```

With:
```
| SC2 dataset roadmap | `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md` |
| SC2 game roadmap | `src/rts_predict/sc2/reports/ROADMAP.md` |
```

**D) `.claude/agents/planner-science.md` — "Read first" section:**

Replace:
```
- `src/rts_predict/sc2/reports/SC2_THESIS_ROADMAP.md`
```

With:
```
- `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md` (dataset-level, Phases 0–2)
- `src/rts_predict/sc2/reports/ROADMAP.md` (game-level, Phases 3+)
```

**E) `.claude/dev-constraints.md`:**

If it references `SC2_THESIS_ROADMAP.md`, update to the new paths.

**F) `reports/research_log.md`:**

If it contains any `reports/00_*` or `reports/01_*` paths (it does, in the
Phase 0 and Phase 1 entries), update them to `reports/sc2egset/00_*` etc.
These are historical log entries — add a one-line note at the top of
affected entries: `> Path note: artifacts moved to reports/sc2egset/ in v0.X.Y.`

**G) `thesis/WRITING_STATUS.md` and `thesis/THESIS_STRUCTURE.md`:**

Search for any `SC2_THESIS_ROADMAP.md` references and update.

---

## Step 12 — Update tests and verify

**A) Update test imports/paths:**

`grep -rn 'REPORTS_DIR' src/rts_predict/sc2/data/tests/` — any test that
constructs expected output paths using `REPORTS_DIR` must be updated to
`DATASET_REPORTS_DIR`.

Key files to check:
- `src/rts_predict/sc2/data/tests/test_exploration.py`
- `src/rts_predict/sc2/data/tests/test_audit.py` (if it exists)
- `src/rts_predict/sc2/tests/` (CLI tests that reference report paths)

**B) Run full verification:**

```bash
poetry run pytest                              # All tests pass
poetry run ruff check src/                     # No lint errors
poetry run mypy src/rts_predict/sc2/config.py  # New constant typed correctly
```

**C) Verify no broken references:**

```bash
# No remaining references to the deleted file
grep -rn 'SC2_THESIS_ROADMAP' src/ .claude/ CLAUDE.md ARCHITECTURE.md docs/ thesis/ reports/
# Should return zero hits (or only CHANGELOG.md historical entries, which are fine)
```

**D) Verify git status is clean:**

```bash
git status  # Only expected changes, no untracked files from old locations
git diff --stat  # Review the full change set
```

---

## Post-completion

- [ ] Add CHANGELOG.md entry under new version
- [ ] Update `reports/research_log.md` with a chore entry
- [ ] Commit with message: `chore: migrate to per-dataset reports structure`
- [ ] Create PR: `chore/per-dataset-reports`

---

## Gate condition

All of the following are true:
1. `src/rts_predict/sc2/reports/SC2_THESIS_ROADMAP.md` does not exist
2. `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md` exists and contains Phases 0–2
3. `src/rts_predict/sc2/reports/ROADMAP.md` exists and contains Phases 3–10
4. All Phase 0 artifacts (`00_*`) live in `reports/sc2egset/`
5. All Phase 1 artifacts (`01_*`) live in `reports/sc2egset/`
6. `audit.py` and `exploration.py` write to `DATASET_REPORTS_DIR`
7. `PHASE_STATUS.yaml` references both `dataset_roadmap` and `game_roadmap`
8. `grep -rn 'SC2_THESIS_ROADMAP'` returns zero hits outside `CHANGELOG.md`
9. All tests pass, ruff clean, no broken imports