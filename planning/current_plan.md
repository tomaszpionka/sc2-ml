---
category: A
branch: feat/sc2egset-cross-region-annotation
date: 2026-04-21
planner_model: claude-opus-4-7
dataset: sc2egset
phase: "01"
pipeline_section: 01_04
invariants_touched: [I2, I6, I7]
source_artifacts:
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/cross_region_history_impact_sc2egset.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_04b_worldwide_identity.md
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_history_all.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md
  - sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py
  - reports/specs/02_00_feature_input_contract.md
  - reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md
  - .claude/scientific-invariants.md
  - docs/PHASES.md
critique_required: true
research_log_ref: src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md#2026-04-21-cross-region-annotation
---

# Plan: WP-7 — sc2egset cross-region fragmentation Phase 01 annotation (REVISED 2026-04-21 post Mode A)

## Scope

Address the WP-3 FAIL finding retroactively inside Phase 01 per user directive 2026-04-21 ("don't spill responsibilities of docs/PHASES.md between phases; address issues even retroactively"). WP-3 (PR #200 / step 01_05_10) empirically demonstrated material rolling-window bias (median_rolling30_undercount=16, p95=29) from the 246 cross-region nicknames (12% of sc2egset players). WP-7 applies mitigation candidate (2) `is_cross_region_fragmented` flag at Phase 01 source per docs/PHASES.md §Phase 01 01_04 (Data Cleaning) discipline.

**Fix:** add derived column `is_cross_region_fragmented` BOOLEAN to the sc2egset `player_history_all` VIEW via DDL amendment. Flag TRUE for any row whose `toon_id` belongs to the set of cross-region toon_ids (toons whose LOWER(nickname) appears in 2+ regions in `replay_players_raw`). Update INVARIANTS.md §2 accepted-bias paragraph with Phase 01 operationalization sentence. Amend spec 02_00 CROSS-02-00-v2 → v3 per §7.

**Post-Mode-A revision summary (2026-04-21):** Mode A surfaced 2 BLOCKERs + 5 WARNINGs + 6 NOTEs. All 6 applicable revisions applied within symmetric 1-revision cap:
- **BLOCKER-1 (column arithmetic):** Original plan assumed 51 → 52 cols. Actual: yaml has 37 cols, spec §2.1 currently says 36 (pre-existing spec-vs-yaml drift). T01 verifies actual counts; downstream strings template off T01 output; §7 amendment log reconciles the spec-vs-yaml drift.
- **BLOCKER-2 (VIEW source alias):** Original plan used `pha.` placeholder. Actual VIEW source is `FROM matches_flat mf WHERE mf.replay_id IS NOT NULL` (per `sandbox/.../01_04_02_data_cleaning_execution.py:440`). T02 uses `mf.toon_id` in the IN-clause, prepends the cross_region_toons CTE, no source rename.
- **WARNING-3 + WARNING-4:** ±5 drift tolerance removed; halt-on-any-drift per WP-3/WP-4 precedent; §Assumptions / T01 / §Open questions aligned to one policy.
- **WARNING-6:** T03 §3 and T05 INVARIANTS §2 sentence explicitly argue blanket-flag conservatism vs handle-length filter (false-positive bound cited from plan's own length breakdown).
- **WARNING-7:** T06 step 4 corrected §5.1 → §5.4 (§5.1 is sc2egset MHM; §5.4 is sc2egset PH).
- **NOTE-8:** T07 scope reduced — no "51 cols" current-state references to update (grep returned zero); T07 only adds 01_04_05 step entry.

Symmetric 1-revision cap consumed.

Scope: 1 new Phase 01 step 01_04_05 (notebook + MD + JSON) + VIEW DDL amendment + YAML schema update + INVARIANTS.md §2 update + spec 02_00 v3 amendment + research_log + ROADMAP step entry + version bump. 11 git-diff-scope files.

## Problem Statement

WP-3 (PR #200 / 01_05_10) empirically falsified the "accepted bias" framing:
- Primary per-(player, match) rolling-window undercount at W=30: median=16.0, p95=29.0 (FAIL).
- Sensitivity: W=5 (0/5), W=10 (0/9), W=30 (16/29), W=100 (61/98) — progressive breakdown with window size.
- MMR-fragmentation Spearman ρ bootstrap 95% CI upper=0.29 (threshold <0.20; FAIL).
- Rare-handle subsample (length ≥ 8) confirms genuine fragmentation, not handle-collision artifact.
- Root cause: professional-tournament structure — top players accumulate multi-region careers.

INVARIANTS.md §2 currently states "accepted bias because no stable worldwide alternative exists"; PR #200 appended a WP-3 quantitative impact sentence. The classification is accepted but not OPERATIONALIZED — Phase 02 consumers cannot apply the bias-mitigation without re-deriving the cross-region set per query.

Per docs/PHASES.md §Phase 01 Pipeline Section 01_04 (Data Cleaning) is the right locus for this annotation. WP-7 adds the Phase 01-native `is_cross_region_fragmented` BOOLEAN column; Phase 02 filters cleanly without re-derivation. The classification remains "accepted bias" — WP-7 adds the operationalization mechanism, not a revision of the I2 branch choice.

## Assumptions & unknowns

- **Assumption (VIEW DDL amendment pattern):** canonical_slot + WP-6 `time_since_prior_match_days` precedents apply.
- **Assumption (flag granularity = per-toon):** flag TRUE iff `toon_id` ∈ cross-region set. Rationale: rolling-window features are computed per `player_id_worldwide` (= toon_id); bias is per-toon.
- **Assumption (BOOLEAN, no NULL):** flag is populated for all rows; no NULL semantics; no SQL precedence edge cases.
- **Assumption (zero drift tolerance):** WP-3/WP-4 precedent — if T01 finds any drift vs INVARIANTS.md §2 recorded counts (246 nicknames), halt and supersede authoritatively before proceeding. No ±tolerance.
- **Assumption (VIEW source is `matches_flat mf`):** confirmed via `sandbox/.../01_04_02_data_cleaning_execution.py:440` — `CREATE OR REPLACE VIEW player_history_all AS SELECT <cols> FROM matches_flat mf WHERE mf.replay_id IS NOT NULL`. T02 amendment preserves this source + alias.
- **Assumption (pre-existing spec-vs-yaml drift):** spec 02_00 §2.1 LOCKED v2 says 36 cols; yaml says 37. This is a pre-existing drift to reconcile during the amendment (T06 §7 amendment log documents both the WP-7 addition AND the prior-drift correction).
- **Unknown (exact toon_id count):** INVARIANTS.md §2 says "294 Class A cross-region candidate pairs" (pair-level) + "246 case-sensitive nicknames" but does not cite the corresponding toon_id count. T01 computes it (expected ~2,495 from WP-3 artifact context).
- **Unknown (handle-length distribution of flagged toons):** T02 reports breakdown for Phase 02 context + T03/T05 conservatism argument.

## Literature context

Not applicable — internal Phase 01 cleaning annotation. References:
- `.claude/scientific-invariants.md` I2 (identity branch), I6 (SQL verbatim), I7 (no magic numbers).
- `docs/PHASES.md §Phase 01` Pipeline Section 01_04.
- `cross_region_history_impact_sc2egset.{md,json}` (WP-3 empirical evidence).
- `01_04_04b_worldwide_identity.md` (I2 Branch iii decision).
- WP-6 precedent `01_04_07_old_rating_conditional_annotation.{py,md}` (DDL-amendment-as-annotation pattern).

## Execution Steps

### T01 — Verify current column counts + cross-region set counts

**Objective:** Before amendment, resolve the spec-vs-yaml column-count drift + re-confirm the 246 cross-region nickname count and compute the exact toon_id count. Establish the authoritative counts that all downstream amendment strings will use.

**Instructions:**
1. Read `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_history_all.yaml` — count columns in the `columns:` section (expected 37 per post-01_04_02 state).
2. Read `reports/specs/02_00_feature_input_contract.md` §2.1 line 90 — record current LOCKED value (expected 36; a pre-existing drift to be reconciled in T06 §7 amendment log).
3. Read `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py:440` — confirm VIEW source is `FROM matches_flat mf WHERE mf.replay_id IS NOT NULL`.
4. Re-run SQL from INVARIANTS.md §2 lines 40-47 (cross-region nickname detection). Record: nickname_count (expected 246), toon_id_count (expected ~2,495). **Halt on any drift** (zero tolerance per WP-3/WP-4 precedent); if drift detected, supersede INVARIANTS.md §2 authoritatively before proceeding.
5. Capture authoritative count pair: `N_yaml_pre` (expected 37), `N_yaml_post` (expected N_yaml_pre + 1 = 38). Spec §2.1 post-amendment should read 38 with the §7 log noting the prior-drift correction.

**Verification:**
- N_yaml_pre, N_yaml_post recorded.
- nickname_count and toon_id_count recorded.
- Pre-existing spec-vs-yaml drift (36 vs N_yaml_pre) documented for T06 §7.
- No drift vs INVARIANTS.md §2 or halt-escalation triggered.

**File scope:** None (read-only).
**Read scope:** listed yaml + md + py artifacts.

---

### T02 — Write sandbox notebook `01_04_05_cross_region_annotation.py`

**Objective:** Amend `player_history_all` VIEW DDL via Phase 01 step. Add `is_cross_region_fragmented` BOOLEAN column using the actual source alias `mf` and matching the existing DDL structure.

**Instructions:**
1. Create `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_05_cross_region_annotation.py` (jupytext auto-pairs).
2. Notebook structure:
   - **Header cell:** step description; motivation (WP-3 FAIL → Phase 01 01_04 annotation per user directive); I6 discipline note.
   - **Motivation cell:** cite WP-3 `cross_region_history_impact_sc2egset.json` numbers.
   - **Cross-region set construction cell:**
     - CTE `cross_region_nicknames`: `SELECT LOWER(nickname) AS nick_lower FROM replay_players_raw GROUP BY LOWER(nickname) HAVING COUNT(DISTINCT region) > 1`.
     - CTE `cross_region_toons`: `SELECT DISTINCT toon_id FROM replay_players_raw WHERE LOWER(nickname) IN (SELECT nick_lower FROM cross_region_nicknames)`.
     - Counts: nickname_count (expected 246); toon_id_count (expected ~2,495).
   - **Handle-length breakdown cell:** count flagged toons by `LENGTH(nickname)` bucket `{< 5, 5-7, ≥ 8}`. Report for Phase 02 context + WP-3 §6 rare-handle alignment.
   - **Current VIEW DDL** verbatim from T01 (`CREATE OR REPLACE VIEW player_history_all AS SELECT ... FROM matches_flat mf WHERE mf.replay_id IS NOT NULL`).
   - **Amended VIEW DDL (BLOCKER-2 fix — uses actual `mf` alias):**
     ```sql
     CREATE OR REPLACE VIEW player_history_all AS
     WITH cross_region_toons AS (
         SELECT DISTINCT toon_id
         FROM replay_players_raw
         WHERE LOWER(nickname) IN (
             SELECT LOWER(nickname)
             FROM replay_players_raw
             GROUP BY LOWER(nickname)
             HAVING COUNT(DISTINCT region) > 1
         )
     )
     SELECT
       <existing 37 columns projected from matches_flat mf, preserved verbatim>,
       (mf.toon_id IN (SELECT toon_id FROM cross_region_toons)) AS is_cross_region_fragmented
     FROM matches_flat mf
     WHERE mf.replay_id IS NOT NULL;
     ```
     - Prepend the `WITH cross_region_toons AS (...)` CTE; append the new BOOLEAN column as the 38th projected column; preserve the existing FROM/WHERE clauses exactly.
   - **Execution cell:** DROP + CREATE the VIEW; verify `SELECT COUNT(*)` unchanged (44,817); `DESCRIBE` shows 38 columns.
   - **Verification cells:**
     - Flag distribution: `SELECT is_cross_region_fragmented, COUNT(*) FROM player_history_all GROUP BY 1`.
     - Distinct flagged toons in PH (should equal toon_id_count from the cross_region_toons CTE).
     - No NULL in BOOLEAN column.
   - **Summary cell:** print nickname_count, toon_id_count, handle-length breakdown, flag distribution, row count invariance.
   - **Artifact export cell:** write JSON + MD to `reports/artifacts/01_exploration/04_cleaning/`.
3. Human-readable headers; no plan codes.

**Verification:**
- Notebook runs end-to-end; VIEW amendment preserves row count; column present.
- Flag distribution + handle-length breakdown reported.
- BOOLEAN fully populated (no NULL).

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_05_cross_region_annotation.py` (Create)
- `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_05_cross_region_annotation.ipynb` (Create; jupytext)

**Read scope:** `replay_players_raw`, `matches_flat`, `player_history_all`, `INVARIANTS.md §2`.

---

### T03 — Write artifact MD + JSON

**Objective:** Canonical artifact; argue blanket-flag conservatism explicitly (WARNING-6 fix).

**Instructions:**
1. Write `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_05_cross_region_annotation.md`:
   - **§1 Scope and motivation** — WP-3 FAIL → Phase 01 01_04 annotation per docs/PHASES.md.
   - **§2 SQL verbatim (I6)** — cross_region_toons CTE + before-and-after VIEW DDL using `mf` alias.
   - **§3 Column definition** — BOOLEAN semantics; no NULL; flag TRUE iff `toon_id` ∈ cross-region set.
   - **§4 Flag population statistics** — rows TRUE/FALSE, distinct flagged toons = toon_id_count.
   - **§5 Handle-length breakdown** — `{< 5, 5-7, ≥ 8}` distribution of flagged toons.
   - **§6 Blanket-flag conservatism argument (WARNING-6 fix):** "The flag is blanket (no length filter) by design. Rationale: length-filtered flags (e.g., length ≥ 8 per WP-3 §6 rare-handle subsample) could miss genuine cross-region players with short handles. False-positive rate bounded by the length-<5 count (reported in §5): these short-handle toons are more likely handle-collision artifacts than genuine same-player fragmentation. Phase 02 may subset to length ≥ 8 via an additional JOIN for strict sensitivity analysis; the blanket flag is the conservative default. Trade-off: under-flagging misses real bias; over-flagging dilutes sensitivity signal. Plan chooses over-flagging as the safer Phase-02-informing default."
   - **§7 Phase 02 usage guidance** — filter `WHERE NOT is_cross_region_fragmented` (safe subset) OR dual feature paths OR sensitivity indicator.
2. Write `01_04_05_cross_region_annotation.json`:
   - Fields: `step` ("01_04_05"), `view_amended` ("player_history_all"), `view_source_alias` ("matches_flat mf"), `column_added` ("is_cross_region_fragmented"), `column_type` ("BOOLEAN"), `row_count_pre` (int), `row_count_post` (int; must equal pre), `column_count_yaml_pre` (int = T01), `column_count_yaml_post` (int = yaml_pre + 1), `column_count_spec_pre_locked` (int = T01 spec §2.1 value, e.g., 36), `column_count_spec_drift_reconciled` (bool = true iff yaml_pre != spec_pre_locked), `nickname_count` (int — expected 246), `toon_id_count` (int — expected ~2,495), `rows_flagged_true` (int), `rows_flagged_false` (int), `flagged_toons_distinct` (int; must equal toon_id_count), `handle_length_breakdown` (dict — `{lt_5, 5_to_7, ge_8}`), `conservatism_argument` (string — blanket-flag rationale), `audit_date` (ISO = "2026-04-21").

**Verification:**
- Both files exist; MD §2 has SQL verbatim; §6 argues conservatism.
- JSON parses; flagged_toons_distinct == toon_id_count; all fields populated.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_05_cross_region_annotation.md` (Create)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_05_cross_region_annotation.json` (Create)

**Read scope:** T02 notebook.

---

### T04 — Update `player_history_all.yaml` schema (descriptive-string versioning per WP-6 precedent)

**Objective:** Document new column + schema_version using canonical_slot + WP-6 descriptive-string precedent. Counts templated from T01.

**Instructions:**
1. Edit `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_history_all.yaml`.
2. ADD `schema_version` field: `schema_version: '<N_post>-col (AMENDMENT: is_cross_region_fragmented added 2026-04-21 per 01_04_05)'` where `<N_post>` = T01's N_yaml_post (expected 38).
3. Append column entry:
   ```yaml
   - name: is_cross_region_fragmented
     type: BOOLEAN
     nullable: false
     description: TRUE iff this row's toon_id is in the set of cross-region toon_ids (toons whose LOWER(nickname) appears in 2+ regions in replay_players_raw). Derived flag; no NULL by construction.
     notes: CONTEXT. Operationalizes INVARIANTS.md §2 accepted-bias framing as a Phase 02-consumable filter. Phase 02 rolling features over player_id_worldwide should apply `WHERE NOT is_cross_region_fragmented` as safe-subset filter, OR use dual feature paths, OR use as sensitivity indicator. Blanket flag (no handle-length filter) by design — false positives bounded by short-handle count (see 01_04_05 §6 conservatism argument). Empirical grounding from WP-3 (01_05_10): median_rolling30_undercount=16, p95=29 on flagged toons. Derivation in 01_04_05 artifact.
   ```

**Verification:**
- `schema_version` field present with descriptive string.
- `is_cross_region_fragmented` column entry appended.
- Descriptive-string format (not semver).

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_history_all.yaml` (Update)

---

### T05 — Update `INVARIANTS.md §2` — Phase 01 operationalization + conservatism note

**Objective:** Append Phase 01 operationalization sentence to the existing §2 accepted-bias paragraph. Include conservatism argument (WARNING-6 fix).

**Instructions:**
1. Edit `src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md §2`.
2. Locate the "Tolerance and accepted bias" paragraph (around line 55). Following the WP-3 PR #200 appended sentence, add:

   "**Phase 01 operationalization (01_04_05, 2026-04-21):** `player_history_all` VIEW carries `is_cross_region_fragmented` BOOLEAN column — TRUE iff `toon_id` belongs to the set of `<toon_id_count>` cross-region toon_ids (toons whose LOWER(nickname) appears in 2+ regions per `replay_players_raw`; `<nickname_count>` distinct nicknames × regional variants). The flag is blanket (no handle-length filter): over-flagging short-handle toons (likely collision artifacts; distribution in 01_04_05 §5 breakdown) is preferred to under-flagging genuine cross-region players with short handles. Phase 02 rolling-window features over `player_id_worldwide` operationalize the accepted-bias framing via this flag (safe-subset filter `WHERE NOT is_cross_region_fragmented`, dual feature paths, or sensitivity indicator); Phase 02 may further subset to `LENGTH(nickname) ≥ 8` for strict analysis. See `reports/artifacts/01_exploration/04_cleaning/01_04_05_cross_region_annotation.md` for derivation + conservatism argument. (01_04_04 + 01_04_05 + 01_05_10)"

   Placeholders `<toon_id_count>` and `<nickname_count>` filled from T03 JSON.

3. Preserve existing §2 content (original accepted-bias + WP-3 sentences + surrounding text).

**Verification:**
- `grep "01_04_05" src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md` returns new citation.
- No `<PLACEHOLDER>` literals.
- `grep "is_cross_region_fragmented" ...` returns column reference in §2.
- Existing §2 content preserved.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md` (Update)

**Read scope:** T03 JSON.

---

### T06 — Amend `reports/specs/02_00_feature_input_contract.md` CROSS-02-00-v2 → CROSS-02-00-v3

**Objective:** Per §7 change protocol, adding a column to sc2egset PH is §2 column-count commitment change — major bump v2 → v3. §7 amendment log reconciles BOTH the WP-7 addition AND the pre-existing spec-vs-yaml drift (36 vs 37 per T01).

**Instructions:**
1. Edit `reports/specs/02_00_feature_input_contract.md`.
2. Frontmatter: `spec_id: CROSS-02-00-v3`, `version: CROSS-02-00-v3`, `supersedes: CROSS-02-00-v2`, `date: 2026-04-21`.
3. **§2.1 sc2egset `player_history_all`** (line ~90): update "Column count" from 36 → `<N_yaml_post>` (expected 38); update "Schema version" row with new descriptive string.
4. **§5.4 sc2egset `player_history_all` classification table** (line ~379; CORRECTED from earlier §5.1 reference — §5.1 is MHM sc2egset) — add row:
   `| is_cross_region_fragmented | BOOLEAN | CONTEXT | TRUE iff row's toon_id in cross-region set. Phase 02 operationalization: filter `WHERE NOT is_cross_region_fragmented` (safe subset), dual feature paths, OR sensitivity indicator. Blanket flag; false positives bounded by short-handle count per 01_04_05 §6. No NULL. Added 01_04_05 (2026-04-21). |`
5. **§7 Spec change protocol amendment log** — add entry:
   "**2026-04-21 — CROSS-02-00-v2 → CROSS-02-00-v3.** sc2egset §5.4 `player_history_all` adds `is_cross_region_fragmented` (BOOLEAN, CONTEXT) per WP-7 / 01_04_05. §2.1 column count corrected: the spec's LOCKED v2 value was 36 while the yaml has been 37 (pre-existing spec-vs-yaml drift; reconciled during this amendment). Post-amendment value is `<N_yaml_post>` (expected 38). Motivation: WP-3 (01_05_10) empirical FAIL of accepted-bias framing; Phase 01-level annotation per docs/PHASES.md §Phase 01 01_04 discipline. Major version bump per §7 (§2 column-count commitment change)."

**Verification:**
- `grep "CROSS-02-00-v3" reports/specs/02_00_feature_input_contract.md` returns new version.
- §2.1 column count reflects N_yaml_post (expected 38).
- §5.4 (NOT §5.1) has new row for `is_cross_region_fragmented`.
- §7 amendment log has 2026-04-21 v2→v3 entry WITH the spec-vs-yaml drift reconciliation note.

**File scope:**
- `reports/specs/02_00_feature_input_contract.md` (Update)

---

### T07 — Add 01_04_05 step entry to `ROADMAP.md` (no count references to update)

**Objective:** Add new step entry to dataset ROADMAP. Per Mode A NOTE-8: grep returned zero matches for "51 cols / 52 cols / 37 cols / 38 cols" current-state references — no count updates needed; only step entry addition.

**Instructions:**
1. Edit `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`.
2. Add a new 01_04_05 step entry parallel to WP-6 precedent's 01_04_07 pattern (docs/templates/step_template.yaml-style). Include: step_number, description, motivation (WP-3 FAIL → Phase 01 annotation), outputs (notebook, MD, JSON paths + view_amended line with post-amendment column count), category (A), gate_met (per notebook execution).
3. Do NOT modify historical step entries or fabricate new count-references.

**Verification:**
- New 01_04_05 entry present.
- `grep "01_04_05" sc2egset/reports/ROADMAP.md` returns the entry.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` (Update)

---

### T08 — Append research_log entry

**Objective:** Document step per per-dataset protocol.

**Instructions:**
1. Prepend new entry to `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`.
2. Entry:
   - Date header: `## 2026-04-21 — [Phase 01 / Step 01_04_05] Cross-region fragmentation Phase 01 annotation`
   - **Category:** A.
   - **Dataset:** sc2egset.
   - **Step scope:** WP-3 FAIL → Phase 01 01_04 annotation per docs/PHASES.md; adds `is_cross_region_fragmented` BOOLEAN to `player_history_all`.
   - **Artifacts produced:** T03 MD + JSON; T02 notebook.
   - **What:** VIEW DDL amended (source `FROM matches_flat mf`; CTE prepended; new BOOLEAN column at position 38); 2,495 cross-region toon_ids flagged; row count preserved at 44,817.
   - **Why:** User directive 2026-04-21 requires Phase 01-level fix.
   - **How (reproducibility):** Notebook 01_04_05; SQL verbatim per I6; canonical_slot + WP-6 DDL-amendment-pattern precedent.
   - **Findings:** nickname_count, toon_id_count, handle_length_breakdown, rows_flagged_{true,false} — from T03 JSON.
   - **Decisions taken:** per-toon flag granularity (not per-nickname); blanket flag with length breakdown for Phase 02 context; no handle-length filter baked in.
   - **Decisions deferred:** Phase 02 chooses filter/sensitivity strategy.
   - **Thesis mapping:** §4.2.2 WP-3 quantitative caveat + WP-7 operationalization. Pass-2 Chat.
   - **Open questions / follow-ups:** manual curation of 294 Class A pairs remains available if Phase 02 findings warrant.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` (Update)

---

### T09 — Version bump + CHANGELOG

**Objective:** Version 3.42.0 → 3.43.0 (minor, feat).

**Instructions:**
1. `pyproject.toml`: `3.42.0` → `3.43.0`.
2. `CHANGELOG.md`: move `[Unreleased]` aside; add `[3.43.0] — 2026-04-21 (PR #TBD: feat/sc2egset-cross-region-annotation)`:
   - `### Added`: New Phase 01 step 01_04_05 — sc2egset cross-region fragmentation annotation. `player_history_all` VIEW amended via DDL to add `is_cross_region_fragmented` BOOLEAN column (row count preserved at 44,817; source `matches_flat mf`). Notebook + MD + JSON artifacts. Flag TRUE for cross-region toon_ids (toons whose LOWER(nickname) appears in 2+ regions — ~2,495 toons from 246 nicknames per INVARIANTS.md §2). Applies WP-3 FAIL finding as Phase 01 cleaning annotation per user directive 2026-04-21.
   - `### Changed`: `INVARIANTS.md §2` — "Tolerance and accepted bias" paragraph extended with Phase 01 operationalization sentence citing `is_cross_region_fragmented` column + 01_04_05 artifact + blanket-flag conservatism argument. `player_history_all.yaml` schema_version descriptive string introduced per canonical_slot + WP-6 precedent. `reports/specs/02_00_feature_input_contract.md` CROSS-02-00-v2 → CROSS-02-00-v3 per §7 (§2.1 column count corrected post-amendment; §5.4 adds column row; §7 amendment log reconciles both WP-7 addition AND pre-existing spec-vs-yaml drift from 36 → 37 → 38). `sc2egset/reports/ROADMAP.md` 01_04_05 step entry added.
3. Reset `[Unreleased]`.

**Verification:**
- `pyproject.toml` `version = "3.43.0"`.
- `CHANGELOG.md` `[3.43.0]` populated.

**File scope:**
- `pyproject.toml` (Update)
- `CHANGELOG.md` (Update)

---

## File Manifest

| File | Action |
|------|--------|
| `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_05_cross_region_annotation.py` | Create |
| `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_05_cross_region_annotation.ipynb` | Create (jupytext) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_05_cross_region_annotation.md` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_05_cross_region_annotation.json` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_history_all.yaml` | Update |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md` | Update |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | Update |
| `reports/specs/02_00_feature_input_contract.md` | Update |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` | Update |
| `pyproject.toml` | Update |
| `CHANGELOG.md` | Update |
| `planning/current_plan.md` | (this plan; tracked separately) |
| `planning/current_plan.critique.md` | (Mode A) |

11 git-diff-scope files (4 new + 7 modified) + 2 planning meta.

## Gate Condition

- Notebook 01_04_05 runs end-to-end; VIEW amendment with `FROM matches_flat mf` preserves row count at 44,817.
- `is_cross_region_fragmented` BOOLEAN column present; fully populated (no NULL); flag distribution reported.
- T01 verified column counts: yaml pre (expected 37) + yaml post (expected 38) + spec §2.1 LOCKED v2 (expected 36, documented drift).
- **Count integrity:** nickname_count matches 246 (zero-tolerance halt on any drift); toon_id_count computed (expected ~2,495).
- **Blanket-flag conservatism argued** in T03 §6 + T05 INVARIANTS.md §2.
- INVARIANTS.md §2 Phase 01 operationalization sentence appended with filled placeholders (no `<PLACEHOLDER>` literals).
- Spec 02_00 bumped v2 → v3; §2.1 column count post-amendment; §5.4 (CORRECTED from §5.1) has new row; §7 amendment log reconciles WP-7 addition + pre-existing spec-vs-yaml drift.
- `player_history_all.yaml` schema_version descriptive-string format per precedent.
- Research log 01_04_05 entry complete.
- `pyproject.toml` 3.43.0; CHANGELOG `[3.43.0]` populated.
- All three `PHASE_STATUS.yaml` unchanged.
- `git diff --stat` touches exactly 11 git-diff-scope files + planning meta.
- **Phase responsibility discipline:** amendment in Phase 01 01_04; INVARIANTS.md §2 is Phase 01 documentation; spec §5.4 is Phase 01 cross-dataset summary. No Phase 02 responsibilities spilled.

## Out of scope

- **Phase 02 usage decisions** — filter vs dual-paths vs sensitivity. Phase 02 planner-science decides.
- **Manual curation of 294 Class A pairs** — WP-3 candidate (1). Agent-infeasible; deferred.
- **Revised I2 branch** — WP-3 candidate (3). Out of scope.
- **aoestats / aoe2companion analogous annotations** — different I2 branches; not applicable.
- **Retroactive modification of 01_04_04 / 01_04_04b artifacts** — preserved.
- **Thesis §4.2.2 prose edits** — Pass-2 Chat.
- **Handle-length-filtered flag variant** — Phase 02 can apply via JOIN if desired; not baked into the annotation.

## Open questions

- **Q1 (resolved):** Flag granularity — per-toon. Rationale in §Assumptions.
- **Q2 (resolved):** NULL handling — BOOLEAN by construction; no NULL.
- **Q3 (resolved):** Manual curation — deferred.
- **Q4 (resolved):** Zero-tolerance drift per WP-3/WP-4 precedent; halt on any mismatch vs INVARIANTS.md §2 counts.

## Dispatch sequence

1. This plan at `planning/current_plan.md` on branch `feat/sc2egset-cross-region-annotation`.
2. `reviewer-adversarial` Mode A invoked 2026-04-21 — verdict REVISE with 2 BLOCKERs + 5 WARNINGs + 6 NOTEs. **Revision round applied 2026-04-21:** all 6 applicable findings addressed (column arithmetic via T01 count verification; VIEW source alias `mf`; drift tolerance removed; conservatism argument; §5.1 → §5.4 correction; T07 scope reduction). Critique preserved. Symmetric 1-revision cap consumed.
3. Executor dispatched with T01–T09.
4. `reviewer-adversarial` Mode C post-draft (Cat A default).
5. Pre-commit (ruff/mypy N/A; planning-drift passes; jupytext sync; no 01_05 binding).
6. Commit + PR + merge.
7. Post-merge: **all mitigation backlog closed.** Phase 02 kickoff unblocked.
