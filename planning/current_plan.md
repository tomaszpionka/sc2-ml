---
category: A
date: 2026-04-18
branch: feat/01-04-04-sc2egset-worldwide-identity
phase: "01"
pipeline_section: "01_04"
step: "01_04_04b"
parent_step: "01_04_04"
dataset: sc2egset
game: sc2
title: "sc2egset worldwide identity — stub composite VIEW player_identity_worldwide"
manual_reference: "docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md §4 + §5"
invariants_touched: [I2, I6, I7, I9, I10]
predecessors: ["01_04_04 (PR #157)"]
plan_version: "R3 — Option 3 only (Option 1 killed by web-adversarial; Option 2 rejected by user)"
---

# sc2egset 01_04_04b — Stub composite `player_identity_worldwide`

## Problem Statement

Web-verified adversarial (R2) established:
- `.SC2Replay` region-scoped `toon_id = R-S2-G-P`; `P` region-silod by Blizzard design (structural, not empirical — stated as design property, not observed collision).
- **No external source provides (nickname → region-profile-id) mapping at bulk scale:** Liquipedia pages don't expose region-scoped profile-ids; Blizzard OAuth cannot bulk-resolve third-party battletags (requires each player's own consent); Aligulac uses internal IDs; sc2pulse is ladder-only + inherits region-scoping. Option 1 (external integration) is structurally dead.
- User rejected Option 2 (accept-as-limitation, zero-artifact).

**Option 3 — this plan:** deliver a deterministic stub composite VIEW so Phase 02 has a stable join key, with documented upgrade path if future manual tournament-roster curation enables cross-region merges.

**Scope:** ~2 hour delivery. One new VIEW + schema YAML + short MD report. No behavioral fingerprinting.

## Scope

sc2egset only. Create VIEW `player_identity_worldwide` over 2,495 `(region, realm, toon_id)` entities with a deterministic hash-derived `player_id_worldwide`. Additive (I9 — no raw/clean mutation). Provenance note explicitly flags this as a region-scoped artifact, not a globally-resolved identity.

**NOT in this plan:**
- Behavioral fingerprinting (APM-JSD, race-overlap, clanTag-Bayes, MMR-Jaccard, temporal-class)
- Union-Find module + pytest
- External-source scraping (Option 1 dead per R2 adversarial)
- Thesis chapter prose (Category F follow-up)

## Literature Context

- **Bialecki et al. (2023)** — SC2EGSet paper precedent for toon_id as entity key. Note: plan-level claim softened; Nature Scientific Data article full-text not accessible via WebFetch at plan time, so claim downgraded to "SC2EGSet documentation does not document a cross-region resolution step" (not "did not propose" — stronger claim required reading full paper).
- **sc2reader** — confirms `toon_handle = "<region>-S2-<subregion>-<toon_id>"` format; `toon_id` segment meaningful only within region context. [Source](https://github.com/GraylinKim/sc2reader/blob/master/sc2reader/objects.py)
- **Blizzard s2protocol** — confirms `m_toon = (m_region, m_programId, m_realm, m_id)` with region/realm siloed by design.

## Assumptions & Unknowns

- **A1 (structural, confirmed by web evidence):** cross-region profile-id linkage is not derivable from `.SC2Replay` alone.
- **A2 (sha256 collision safety):** 16-hex-char truncation = 64-bit space; for 2,495 entities, birthday collision probability ≈ 2^32 ⇒ ~1 in 4 billion pair-collision — safe by 5+ orders of magnitude. Documented in schema YAML I7 provenance.
- **A3 (toon_id storage format):** assume stored as full `R-S2-G-P` string in `replay_players_raw.toon_id`. If Cell A sanity reveals otherwise (just `P`), adjust VIEW DDL to compose `(region, realm, toon_id)` from separate columns — both paths produce the same composite hash.

## Execution Steps

### T01 — Structural audit + VIEW construction (~1 hour)

Notebook: `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_04b_worldwide_identity.py` (jupytext-paired). Read-only DuckDB for audit; write-mode only for CREATE OR REPLACE VIEW.

**Cell A** — imports + DB connection + row-count sanity.

**Cell B** — structural audit (not empirical falsification — I7 careful wording):
- Column-by-column table: every identity-capable column in `replay_players_raw` + `replays_meta_raw` (toon_id, nickname, userID, playerID, region, realm, clanTag) → cardinality + stability-within-region + cross-region-stability verdict
- **Explicitly phrase:** "Profile-id segment of toon_id is region-scoped by Blizzard design (sc2reader + s2protocol confirm); no cross-region uniqueness claim asserted from these 44,817 rows alone."
- `userID` cardinality forensics — resolve 01_04_04's "cardinality=16, slot index" open question. Report actual distribution + interpretation.

**Cell C** — DDL:
```sql
CREATE OR REPLACE VIEW player_identity_worldwide AS
SELECT DISTINCT
    region,
    realm,
    toon_id,
    nickname,
    -- Deterministic 16-hex-char (64-bit) composite identifier.
    -- I7: sha256 16-char truncation safe for 2,495 entities
    --     (birthday-pair collision ~1 in 4 billion).
    -- I2: case-sensitive nickname preserved (but not in hash input -- hash
    --     uses only server-scoping coordinates, so re-runs are stable
    --     even if nickname is later normalized).
    -- Upgrade path: future external-bridge PR may add a supplemental
    --     merge-mapping table without breaking existing player_id_worldwide.
    'sc2egset::wid::' || SUBSTR(
        LOWER(HEX(DIGEST('sc2egset|' || region || '|' || realm || '|' || toon_id, 'sha256'))),
        1, 16
    ) AS player_id_worldwide
FROM replay_players_raw
WHERE toon_id IS NOT NULL;
```

Use DuckDB's `DIGEST(text, 'sha256')` function (returns BLOB) + `HEX` + `LOWER` + `SUBSTR` for 16-char prefix. If DuckDB's SHA function differs, substitute the equivalent; verify via SQL smoke test.

**Cell D** — gate assertions:
- `SELECT COUNT(*) FROM player_identity_worldwide` = 2,495
- `SELECT COUNT(DISTINCT player_id_worldwide) FROM player_identity_worldwide` = 2,495 (no collisions — collision assertion, not birthday-probability estimate)
- `DESCRIBE` returns 5 columns, dtypes `[VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR]`
- Smoke test: for 3 hand-picked entities, recompute the hash in Python + compare to VIEW output (reproducibility).

### T02 — Schema YAML + artifacts

**Cell E** — write `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_identity_worldwide.yaml` with:
- 5 columns: region, realm, toon_id, nickname, player_id_worldwide
- invariants block I2/I6/I7/I9/I10
- provenance `source_tables: [replay_players_raw]`, `filter: "toon_id IS NOT NULL"`, `ddl` verbatim
- **Explicit limitation note in description:** "This VIEW provides a deterministic stable join key for Phase 02, but it is structurally a region-scoped identifier — a physical player active on multiple Battle.net regions is split across multiple `player_id_worldwide` values. Cross-region merge requires future external-data work (see 01_04_04 research_log + follow-up PR scope)."

**Cell F** — `01_04_04b_worldwide_identity.json` with:
- T01 SQL queries verbatim (audit + DDL + gate checks)
- T01 column audit table
- Web-research summary citing R2 adversarial findings (4 external sources + why each doesn't deliver cross-region bridge)
- Chosen option (3) + rationale
- `identity_key_temporal_scope` declaration
- `literature` citations (sc2reader URL, s2protocol URL, Liquipedia ToS URL, Aligulac API URL, sc2pulse URL, Blizzard forum URL)

**Cell G** — `01_04_04b_worldwide_identity.md` human-readable report:
- 1-paragraph problem restatement
- T01 audit summary
- External-bridge infeasibility (R2 adversarial findings summarized)
- VIEW DDL + collision-safety note
- Follow-up PR sketch (manual tournament-roster curation if ever warranted)

### T03 — Status + research_log + ROADMAP

**Cell H** — status file updates:
- STEP_STATUS.yaml: add `01_04_04b: {status: complete, completed_at: "2026-04-18"}`
- PIPELINE_SECTION_STATUS.yaml: 01_04 flip complete → in_progress → complete (roundtrip; matches 01_04_02/03 precedent for new-VIEW steps)
- PHASE_STATUS.yaml: unchanged

**Cell I** — research_log.md prepend dated entry with findings + chosen option 3 + explicit acknowledgment that Option 1 was killed by R2 web-adversarial.

**Cell J** — ROADMAP.md append `### Step 01_04_04b -- Stub composite player_identity_worldwide VIEW` block under the existing 01_04_04 block.

## File Manifest

**NEW:**
- `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_04b_worldwide_identity.{py,ipynb}`
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_identity_worldwide.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_04b_worldwide_identity.{json,md}`

**MODIFIED:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` (append 01_04_04b)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` (add 01_04_04b)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/PIPELINE_SECTION_STATUS.yaml` (01_04 roundtrip)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` (prepend)

**NOT touched (I9):**
- All existing sc2egset raw + view YAMLs (except new one)
- aoestats + aoec files
- PHASE_STATUS.yaml

## Gate Condition

- VIEW `player_identity_worldwide` exists with 2,495 rows (= K1 toon_ids from 01_04_04) and 2,495 distinct `player_id_worldwide` values (collision assertion)
- DESCRIBE returns 5 cols in spec order + dtypes
- Smoke test (3 hand-computed Python hashes) matches VIEW output
- schema YAML has 5 cols + I2/I6/I7/I9/I10 invariants block + explicit limitation note
- JSON has all T01 SQL verbatim + ≥5 literature URLs
- MD report non-empty
- STEP_STATUS 01_04_04b = complete; PIPELINE_SECTION 01_04 ending state = complete
- I9: `git diff --stat master..HEAD` on sc2egset raw + non-new view YAMLs = empty
- research_log dated entry prepended

## Open Questions

All resolved:
- Option selected → 3 (stub composite VIEW)
- Threshold magic numbers → removed (no Option 1 means no hit-rate threshold)
- External sources → documented as infeasible in T02 Cell F web-research summary
- sha256 collision safety → I7-documented (2^32 birthday bound vs 2,495 entities)
- userID cardinality=16 mystery → T01 Cell B resolves empirically

## Adversarial pre-approval

R2 adversarial verdict informed this R3 plan. Skip additional pre-execution adversarial per user "less ceremony" directive — R3 is a straightforward execution of the Option 3 scope confirmed by user approval. Post-execution review in Claude Chat recommended if thesis defense surfaces new concerns about the stub composite choice.
