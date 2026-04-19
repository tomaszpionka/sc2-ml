---
category: D
branch: fix/aoestats-phase06-pop-tag-backfill
date: 2026-04-19
planner_model: claude-opus-4-7
dataset: aoestats
phase: "01"
pipeline_section: "Temporal & Panel EDA"
invariants_touched: [I5]
source_artifacts:
  - planning/BACKLOG.md  # F6 entry
  - sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface.py
  - sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_02_psi_pre_game_features.py
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/phase06_interface_aoestats.csv
  - reports/specs/01_05_preregistration.md  # §1 line 67–71
  - thesis/chapters/04_data_and_methodology.md  # §4.1.4 + §4.4.6 downstream consumers
critique_required: false
research_log_ref: src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md
---

# Plan: aoestats Phase 06 CSV — `[POP:]` and `[PRE-canonical_slot]` tag backfill

## Scope

Closes BACKLOG F6. Populate the `notes` column of
`phase06_interface_aoestats.csv` (currently 136 data rows, zero `[POP:]`
tags, zero `[PRE-canonical_slot]` tags) with:

- `[POP:ranked_ladder]` on **all 136 rows** (parity with sc2egset
  `[POP:tournament]` 35/35 and aoe2companion `[POP:ranked_ladder]`
  74/74).
- `[PRE-canonical_slot]` on rows where `feature_name` is literally
  per-slot: **`p0_is_unrated`** and **`p1_is_unrated`** (the only two
  feature names in the aoestats Phase 06 schema that directly index
  `team=0` / `team=1`; all other features — `focal_old_rating`,
  `avg_elo`, `faction`, `opponent_faction`, `mirror`, `map`, `won`,
  `duration_seconds` — are either randomized/UNION-ALL-symmetric or
  match-level aggregate per the 01_05_02 notebook's explicit
  symmetry comments).

After merge, thesis §4.1.4 + §4.4.6 prose ("implicit scope via spec
§0 + R02 cleaning filter") becomes revisable to direct citation of
the tagged artifact. That prose update is OUT OF SCOPE for this PR
(deferred to Pass-2 or a separate Category F follow-up).

## Problem Statement

Spec §1 line 67–71 defines `[PRE-canonical_slot]` as the scope tag
for aoestats features conditioned on `team` (pending Phase 02
`canonical_slot` derivation per BACKLOG F1). Spec §12 Phase 06
interface schema assumes the `notes` column carries per-row scoping
tags. Sibling datasets comply: sc2egset (35/35 `[POP:tournament]`)
and aoe2companion (74/74 `[POP:ranked_ladder]`). aoestats does
**not** — `grep` returns zero hits for both `[POP:]` and
`[PRE-canonical_slot]` on 136 data rows. Root cause: the
`01_05_08_phase06_interface.py` notebook loads
`pre_canonical_slot_flag_active` from the leakage audit (line 52–58)
but never stamps it onto rows, and never emits a `[POP:]` tag at
all. This PR fixes both gaps in one notebook edit.

## Assumptions & unknowns

- **Assumption:** `[POP:ranked_ladder]` is the correct aoestats
  population tag — spec §0 scope `leaderboard = 'random_map'` +
  spec §2 "aoestats: 2022-Q3 → 2024-Q4" population table confirm
  this is the ranked-ladder 1v1 random-map cohort.
- **Assumption:** `p0_is_unrated` and `p1_is_unrated` are the only
  per-slot (team-conditioned) features in the Phase 06 schema. All
  other features either (a) use `focal_old_rating` randomization
  (half-split), (b) aggregate via UNION-ALL (`faction`,
  `opponent_faction`), (c) are symmetric binary (`mirror`), or (d)
  are match-level (`map`, `won`, `duration_seconds`, `avg_elo`).
  Verified against `01_05_02_psi_pre_game_features.py` derivations
  2026-04-19.
- **Unknown:** Whether `focal_old_rating` should carry the flag
  given the `CASE WHEN half=0 THEN p0_old_rating ELSE p1_old_rating
  END` derivation. The notebook's existing intent is NO flag (half
  is random → aggregate). Writer accepts the notebook author's
  pre-existing classification rather than reopening the
  methodology question in a Category-D PR.
- **Unknown:** Whether ICC rows (feature_name = `won`) carry the
  flag. Notebook treats the ICC as per-player UNION-ALL aggregate →
  NO flag. Accept.

## Execution Steps

### T01 — Modify `01_05_08_phase06_interface.py` to stamp both tags

**Objective:** Add tag-emission logic to the Phase 06 interface
notebook so every CSV row carries `[POP:ranked_ladder]` and
per-slot rows additionally carry `[PRE-canonical_slot]`.

**Instructions:**
1. Read the current `01_05_08_phase06_interface.py` end-to-end.
2. Add a module-level constant near `M5_NOTE` (line 62):
   ```python
   POP_TAG = "[POP:ranked_ladder]"
   PRE_CANONICAL_SLOT_TAG = "[PRE-canonical_slot]"
   PER_SLOT_FEATURES = frozenset({"p0_is_unrated", "p1_is_unrated"})
   ```
3. Replace the existing `notes` enrichment block (currently lines
   235–237, which appends `M5_NOTE` to every row) with:
   ```python
   # F6: emit [POP:ranked_ladder] on every row + [PRE-canonical_slot]
   # on per-slot feature rows.
   def _tag_prefix(feature_name: str) -> str:
       parts = [POP_TAG]
       if feature_name in PER_SLOT_FEATURES:
           parts.append(PRE_CANONICAL_SLOT_TAG)
       return " ".join(parts)

   df_p06["notes"] = (
       df_p06["feature_name"].map(_tag_prefix) + " "
       + df_p06["notes"].fillna("").astype(str) + " "
       + M5_NOTE
   )
   df_p06["notes"] = df_p06["notes"].str.strip()
   ```
4. Update the existing "Verify [PRE-canonical_slot] is ABSENT from
   symmetric-aggregate rows" check (lines 240–248). Replace the
   faction/opponent_faction audit with a stronger assertion:
   ```python
   # F6 verification: exactly PER_SLOT_FEATURES carry the flag
   per_slot_rows = df_p06[df_p06["notes"].str.contains(
       r"\[PRE-canonical_slot\]", na=False, regex=True
   )]
   per_slot_features_observed = set(per_slot_rows["feature_name"].unique())
   assert per_slot_features_observed == PER_SLOT_FEATURES, (
       f"F6: expected [PRE-canonical_slot] exclusively on "
       f"{PER_SLOT_FEATURES}, got {per_slot_features_observed}"
   )

   # F6 verification: every row carries [POP:ranked_ladder]
   assert df_p06["notes"].str.contains(
       r"\[POP:ranked_ladder\]", na=False, regex=True
   ).all(), "F6: [POP:ranked_ladder] missing from some rows"

   print(
       f"F6 tagging verified: "
       f"[POP:ranked_ladder] on {len(df_p06)} / {len(df_p06)} rows; "
       f"[PRE-canonical_slot] on {len(per_slot_rows)} rows "
       f"(features: {sorted(per_slot_features_observed)})"
   )
   ```
5. Remove the unused `pre_canonical_flag` variable and the
   `audit_path` / `audit` loading block (lines 50–58) — superseded
   by the explicit `PER_SLOT_FEATURES` constant. The audit JSON
   still emits the flag but the notebook no longer needs to read
   it (this decoupling is a bonus robustness: flag activation is
   now controlled by the notebook constant, not a side-channel
   JSON read).

**Verification:**
- ruff + mypy pass on the notebook (pre-commit hook enforces).
- Notebook is still syntactically valid Python-percent / jupytext-
  pairable.
- All three edits (constant, tag logic, assertion) are in place.
- `pre_canonical_flag` variable is fully removed (grep returns 0
  matches in the notebook).

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface.py`

**Read scope:**
- `sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_02_psi_pre_game_features.py` (per-slot vs aggregate derivation context)

---

### T02 — Execute the modified notebook to regenerate the Phase 06 CSV

**Objective:** Re-run `01_05_08_phase06_interface.py` so
`phase06_interface_aoestats.csv` is re-emitted with the new tag
logic. Notebook is idempotent: no other artifacts change.

**Instructions:**
1. Activate venv: `source .venv/bin/activate`.
2. Re-sync .ipynb from .py via jupytext (pre-existing pattern):
   `poetry run jupytext --sync sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface.py`
3. Execute the notebook:
   `poetry run jupyter nbconvert --to notebook --execute --inplace sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface.ipynb`
4. Sync back to .py after execution:
   `poetry run jupytext --sync sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface.ipynb`
5. If execution fails, diagnose (most likely cause: import path or
   the upstream PSI CSVs being absent — both already present on
   master, so this should be a no-op regeneration).

**Verification:**
- `phase06_interface_aoestats.csv` last-modified within the current
  session.
- Row count still 136 (schema v1.0.5 11-column count preserved).
- Notebook's own F6 assertions print success.
- JSON validation artifact `01_05_08_phase06_interface_schema_validation.json`
  re-emitted.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface.ipynb` (synced)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/phase06_interface_aoestats.csv` (regenerated)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface_schema_validation.json` (re-emitted)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface_schema_validation.md` (re-emitted)

**Read scope:** (none — notebook is self-contained once T01 is in place)

---

### T03 — Verify tag counts + regression test ICC/PSI values unchanged

**Objective:** Confirm the backfill landed correctly and no metric
values regressed. Spec §12 schema contract still passes.

**Instructions:**
1. Run verification greps:
   ```bash
   grep -c '\[POP:ranked_ladder\]' src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/phase06_interface_aoestats.csv
   # Expected: 136 (all data rows, header excluded by grep -c on match content)
   grep -c '\[PRE-canonical_slot\]' src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/phase06_interface_aoestats.csv
   # Expected: 16 (p0_is_unrated 8 quarters + p1_is_unrated 8 quarters)
   ```
2. Spot-check ICC headline values unchanged: verify
   `icc_anova_observed_scale` row for `cohort_threshold=10` still
   shows `metric_value=0.0268`, `metric_ci_low=0.0148`,
   `metric_ci_high=0.0387` (post-v1.0.5 canonical numbers cited by
   thesis §4.4.5 Tabela 4.7).
3. Spot-check PSI headline values unchanged: verify 2023-Q1
   `focal_old_rating` PSI still reads `0.037`.
4. Verify header row count: `wc -l` on the CSV should show 137
   lines total (1 header + 136 data rows — unchanged).
5. Update aoestats `research_log.md` with a short "F6 tag backfill"
   entry dated 2026-04-19 (following research_log conventions;
   cite the commit SHA after commit is made).

**Verification:**
- `grep -c '\[POP:ranked_ladder\]'` returns 136.
- `grep -c '\[PRE-canonical_slot\]'` returns 16.
- Spot-checked ICC and PSI values match pre-F6 values.
- `wc -l` on CSV returns 137.
- `research_log.md` has new F6 entry.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md`

**Read scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/phase06_interface_aoestats.csv`

---

### T04 — Wrap-up: remove F6 from BACKLOG, version bump, CHANGELOG, TBD backfill

**Objective:** Close F6 in BACKLOG, bump patch version, CHANGELOG
entry, and opportunistically backfill CHANGELOG `[3.26.2]` TBD →
`#179` (inherited from the prior cleanup PR).

**Instructions:**
1. Delete the F6 entry from `planning/BACKLOG.md` (per
   planning/README.md "Claiming an item" protocol).
2. Backfill CHANGELOG `[3.26.2]` header: `PR #TBD` → `PR #179`.
3. Bump `pyproject.toml` 3.26.2 → 3.26.3.
4. Insert new CHANGELOG `[3.26.3]` entry:
   ```
   ## [3.26.3] — 2026-04-19 (PR #TBD: fix/aoestats-phase06-pop-tag-backfill)

   ### Changed
   - aoestats Phase 06 CSV `notes` column now carries
     `[POP:ranked_ladder]` on all 136 rows and `[PRE-canonical_slot]`
     on 16 per-slot rows (`p0_is_unrated` + `p1_is_unrated` × 8
     quarters). Closes BACKLOG F6. Parity achieved with sc2egset
     (`[POP:tournament]` 35/35) and aoe2companion (`[POP:ranked_ladder]`
     74/74). No metric-value regression.

   ### Removed
   - `pre_canonical_slot_flag_active` side-channel read in
     `01_05_08_phase06_interface.py` — superseded by explicit
     `PER_SLOT_FEATURES = {"p0_is_unrated", "p1_is_unrated"}`
     notebook constant.
   ```
5. Stage + commit.

**Verification:**
- `planning/BACKLOG.md` no longer contains an F6 entry.
- `pyproject.toml` shows `version = "3.26.3"`.
- CHANGELOG has `[3.26.3]` entry + `[3.26.2]` PR backfill to #179.

**File scope:**
- `planning/BACKLOG.md`
- `pyproject.toml`
- `CHANGELOG.md`

## File Manifest

| File | Action |
|------|--------|
| `sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface.py` | Update (tag logic + constants + assertions) |
| `sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface.ipynb` | Update (jupytext sync) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/phase06_interface_aoestats.csv` | Regenerate (same row count, notes column tagged) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface_schema_validation.json` | Regenerate |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface_schema_validation.md` | Regenerate |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` | Append F6 entry |
| `planning/BACKLOG.md` | Remove F6 entry |
| `planning/current_plan.md` | Update (this file — commit as provenance) |
| `pyproject.toml` | Update (version 3.26.2 → 3.26.3) |
| `CHANGELOG.md` | Update (new `[3.26.3]` + `[3.26.2]` TBD backfill) |

## Gate Condition

- `grep -c '\[POP:ranked_ladder\]'` on the aoestats Phase 06 CSV
  returns **136** (all data rows).
- `grep -c '\[PRE-canonical_slot\]'` on the aoestats Phase 06 CSV
  returns **16** (`p0_is_unrated` + `p1_is_unrated` × 8 primary
  quarters).
- ICC headline values at `cohort_threshold=10` unchanged
  (0.0268 / 0.0148 / 0.0387).
- PSI headline values unchanged (spot-check on 2023-Q1
  `focal_old_rating` = 0.037).
- Row count of CSV unchanged at 136 data rows (137 lines with
  header).
- Pre-commit hooks pass (ruff + mypy on the .py notebook).
- BACKLOG F6 entry removed.
- `pyproject.toml` version 3.26.3; CHANGELOG `[3.26.3]` entry.
- PR opened on branch `fix/aoestats-phase06-pop-tag-backfill`.

## Out of scope

- **Thesis §4.1.4 + §4.4.6 prose update** to drop "implicit scope"
  language (now that the tag is explicit). Deferred to Pass-2 or a
  separate Category F PR.
- **BACKLOG F1** (`canonical_slot` column Phase 02 unblocker) —
  the substantive downstream fix. F6 only closes the artifact-vs-spec
  divergence on the flag presence, not the underlying W3 bias.
- **Other aoestats notebook modifications** beyond the minimal
  tag-emission change. The `pre_canonical_flag` variable removal is
  bonus cleanup; anything else is scope creep.
- **Phase 06 schema version bump.** Spec §12 is unchanged; the
  notes column tagging is artifact-level, not schema-level.
- **Reviewer-adversarial** plan-side critique. `critique_required:
  false` for this Category-D fix per plan_template.md. Final review
  uses reviewer-deep on the diff per CLAUDE.md routing.

## Open questions

- **Q1:** Should `focal_old_rating` carry `[PRE-canonical_slot]`?
  Resolved NO per notebook author's intent (half-split
  randomization → aggregate). If Pass-2 challenges this, the
  `PER_SLOT_FEATURES` constant is the single point of change.
- **Q2:** Should the `[POP:]` tag use `[POP:ranked_ladder]` or
  `[POP:ranked_ladder_1v1_random_map]` (more specific)? Resolved
  short form for parity with aoe2companion (also `[POP:ranked_ladder]`);
  the specificity (1v1 random_map) is already captured in the M5
  note. Short form wins for cross-dataset tag comparability.
