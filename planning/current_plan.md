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
title: "sc2egset worldwide identity augmentation — 5-signal Fellegi-Sunter classifier + Union-Find composition"
manual_reference: "docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md §4 + §5"
invariants_touched: [I2, I3, I6, I7, I9]
predecessors: ["01_04_04 (PR #157)"]
---

# sc2egset 01_04_04b — Worldwide Player Identity Resolution

## Problem Statement

PR #157 (01_04_04) surfaced the problem but deferred resolution:
- toon_id is region×realm-scoped (0 cross-region) → useless alone for worldwide identity
- LOWER(nickname) has 30.6% within-region collision (6× Christen 2012 5% threshold)
- Case-sensitive `nickname`: 1,106 distinct vs 1,045 LOWER → 61 case-variant pairs
- 246 case-sensitive multi-region nicknames; 294 Class A overlap / 15,474 Class B disjoint / 317 Class C degenerate

User directive (2026-04-18): **resolve empirically now at Phase 01.04 using behavioral fingerprints** rather than defer to Phase 02 (circularity — Elo-backtest validates identity key, but needs it first).

Goal: deterministic 5-signal classifier producing `player_id_worldwide` per (region, realm, toon_id) entity such that physical players active on multiple servers get a single continuous Elo trajectory.

## Scope

sc2egset only. Follow-up sub-step `01_04_04b`. No raw mutation (I9). Optional new VIEW `player_identity_worldwide` gated on T06 go/no-go rule. No cross-dataset work (aoestats bridge deferred to future CROSS PR per VERDICT A).

**Hard constraints (user directives):**
- Case-sensitive `nickname` throughout. Never LOWER.
- Case-variant pairs stay SPLIT unless behavioral AND literal case match.
- Empirical thresholds only (I7 — no magic numbers).
- Hahn et al. 2020 DIRECTLY applies (APM-JSD is THE canonical SC2 fingerprint, not adjacent like aoestats civ-JSD).

## Literature Context

- **Hahn et al. (2020)** — *Characterization of Gaming Behavior in StarCraft II: APM distributions are idiosyncratic per player, stable across sessions.* Direct empirical warrant for APM-JSD as same-player signal.
- **Fellegi & Sunter (1969)** — probabilistic record-linkage framework; MERGE/SPLIT/UNCERTAIN = their M/U/P.
- **Christen (2012) Ch. 5** — blocking (case-sensitive nickname); 5% false-merge threshold.
- **Tarjan (1975)** — Union-Find with path-compression + union-by-rank; O(α(n)·n).
- **Lin (1991)** — Jensen-Shannon divergence (symmetric, bounded, zero-mass safe).

## Assumptions & Unknowns

**Assumptions:**
- `replay_players_raw` retains raw clanTag (VARCHAR) + MMR (INT, 0=unrated sentinel). matches_flat_clean drops both; raw retains.
- `player_history_all.APM` NULLIF-cleaned per 01_04_02 DS-SC2-10.
- Entities with `n_games_with_nonnull_APM < 5` insufficient for APM-JSD (CLT floor).
- Union-Find deterministic under sorted pair iteration `(nickname, toon_a_str, toon_b_str)`.

**Unknowns resolved at runtime:**
- How many of 16,085 pairs have APM-support ≥ 5 on both sides (T02).
- Empirical APM-JSD threshold via same-entity null p95 vs cross-entity control p05 (T03).
- Which of 5 signals discriminate (T03 diagnostic).
- MERGE/SPLIT/UNCERTAIN counts per sub-universe (T04).
- T06 sub-case: VIEW creation vs DEFER to Phase 02.

## Execution Steps

### T01 — Candidate block construction (case-sensitive blocking)

Create notebook `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_04b_worldwide_identity.py`. Cells A-F:
- A: imports + read-only DB connection
- B: I0 sanity (44,817 / 44,418 / 44,817 row counts)
- C: `ENTITY_SUPPORT_SQL` — per-`(region, realm, toon_id)` aggregates (n_games, n_games_with_apm, n_games_with_race, n_clantags, first/last game). Expected 2,495 entities.
- D: `PAIR_ENUMERATION_SQL` — two sub-universes: cross-region same-case-nick pairs + within-region collision pairs. Report case-sensitive vs LOWER delta
- E: temporal class re-attach (A/B/C) using case-sensitive nickname
- F: entity APM-support histogram PNG

### T02 — Per-pair agreement signals (5 channels)

Cells G-M:
- G: **APM-JSD** (direct Hahn 2020). Shared deciles of pooled non-null APM; Laplace-smoothed; JSD base-2 in [0,1]. Same-entity null (5-fold split, seed=42) + 1,000-pair cross-entity control. Skip pairs where either entity <5 games. **P1-WARNING mitigation:** same-entity null assumes single-human-per-(region,realm,toon_id); smurf handoff / account-selling documented in SC2 tournament scene could contaminate null. Report per-entity APM-JSD variance — if within-entity JSD is multimodal (two peaks detected via simple bimodality check), flag in MD as "contamination candidate". Threat-to-validity declared in T03 Cell N.
- H: **race_overlap** — sum of min(p_a[r], p_b[r]) over 3 races; Bhattacharyya-like
- I: **clanTag status** — {AGREE, OVERLAP, DISJOINT, ONE_EMPTY, BOTH_EMPTY_AGREE}
- J: **MMR trajectory overlap** — **P4-WARNING fix: Jaccard over p10-p90 intervals** (`|A∩B| / |A∪B|` — symmetric, penalizes size-mismatch) + guard: if `range_a < 200 OR range_b < 200` MMR points, mark `sufficient_data_mmr = false` (insufficient trajectory for discrimination — narrow-range entities produce spurious high-overlap scores). Skip entities <5 rated games.
- K: **temporal_class** — A/B/C from T01
- L: assemble `pairs_with_signals_df` → CSV
- M: 4-panel signal-distribution PNG

### T03 — Empirical threshold derivation (I7)

Cells N-T:
- N: APM-JSD threshold = midpoint(null_p95, control_p05). Discrimination check: if null_p95 ≥ control_p05 AND median entity ≥20 games → HALT.
- O: race threshold (same procedure, reversed direction)
- P: MMR threshold (same)
- Q: clanTag Bayesian decision table (4 statuses → P(same|status))
- R: temporal Bayesian decision table (A=AGREE, B=NEUTRAL, C=NEUTRAL+downweight)
- S: thresholds JSON with full provenance (Hahn 2020 cited)
- T: 3-panel threshold visualization PNG

### T04 — MERGE/SPLIT/UNCERTAIN classification

Cells U-Y:
- U: per-pair 5-element agreement vector
- V: composite rule:
  - **P2-BLOCKER fix (HARD-SPLIT case-variant guard):** BEFORE composite scoring runs, if `LOWER(nickname_a) == LOWER(nickname_b) AND nickname_a != nickname_b` → `decision = SPLIT` unconditionally (user directive: case-variants stay SPLIT unless literal case match — differ-by-case fails literal match by definition).
  - `n_agree ≥ 3 AND n_disagree ≤ 1` → MERGE
  - `n_disagree ≥ 3 AND n_agree ≤ 1` → SPLIT
  - otherwise → UNCERTAIN
  - **Within-region collision special-case:** same server + handle, MERGE only if temporal_class=A_overlap AND **P3-WARNING fix (shared-account disambiguator):** match-timestamps minute-granular overlap check — if two entities' timestamps interleave within a single day (minute granularity), downgrade to UNCERTAIN as "shared-account suspect" (pro-team coaching / smurfing practice accounts documented empirically in SC2 tournament scene).
- W: self-pair sanity (split-half same entity → MERGE). **P8-WARNING fix:** raise minimum to `n_games_with_apm ≥ 20` (10 per half; JSD variance O(1/n)). Report per-entity pass rate stratified by game count so low-game entities' reliability is visible. HALT if >5% fail at ≥20-games cohort (not at ≥10 as originally specified).
- X: decision-distribution PNG (MERGE/SPLIT/UNCERTAIN × cross-region/within-region × temporal_class)
- Y: UNCERTAIN audit CSV for manual review

### T05 — Union-Find composition → player_id_worldwide

Cells Z-FF:
- Z: Extract `UnionFind` to `src/rts_predict/common/union_find.py` + tests at `tests/rts_predict/common/test_union_find.py` (per sandbox "no inline defs" rule). Standard path-compression + union-by-rank with type hints.
- AA: Apply MERGE edges deterministically (sorted by nickname, toon_a, toon_b)
- BB: Extract components → player_id_worldwide = `"sc2egset::wid::" + sha256(representative_nick + "|" + canonical_region + "|" + component_fingerprint)[:16]`. **P7-BLOCKER fix:** `component_fingerprint` = sha256 of sorted-tuple string `"|".join(f"{r}:{rl}:{tid}" for r,rl,tid in sorted(component_entities))` — prevents two distinct components (both correctly SPLIT but sharing rep_nick + canonical_region; e.g., two different physical "Serral"s) from getting identical WIDs by construction. Representative = entity with most games in component.
- CC: `entity_to_wid_df` CSV
- DD: `component_detail` CSV
- EE: component-size-distribution PNG
- FF: sanity checks + **P7-BLOCKER assertion: `len(set(component_to_wid.values())) == n_components`** (every distinct component gets a distinct WID — catches construction-level hash collision if component_fingerprint weren't included). Plus: unique WID per entity mapping, every entity mapped exactly once.

### T06 — VIEW decision gate

Cell GG evaluates (**P6-BLOCKER fix — empirical threshold derivation in T03 + literature citation, NO magic numbers**):
- `uncertain_rate = n_uncertain / n_class_ab`
- **Thresholds derived in T03 Cell S (not embedded magic):**
  - `uncertain_rate_threshold` = the uncertain-fraction at which ≥4 of 5 signals achieve pairwise discrimination per the T03 null/control distributions. If 4/5 signals discriminate → threshold = p50 of expected-uncertain distribution over a simulated draw (inherit from Fellegi-Sunter 1969 "possible match" fraction bound at 0.5 * (u_prob + m_prob)). If only 3/5 discriminate → threshold relaxes. Derivation written to JSON + MD.
  - `self_pair_pass_rate_threshold` = 1 - (type-I-error budget for record-linkage false-split per Christen 2012 Ch. 6 "acceptable F-measure"). Christen's worked example uses type-I = 5%, hence 95%. Cite Christen 2012 Ch. 6 p. 167-180 directly in T06 Cell GG comment.
- **IF** uncertain_rate < uncertain_rate_threshold AND self_pair_pass_rate >= self_pair_pass_rate_threshold AND apm_jsd_discriminates → **sub-case A: CREATE VIEW**
- **ELSE** → **sub-case B: DEFER**

Sub-case A (HH-A, II-A, JJ-A): CREATE OR REPLACE VIEW player_identity_worldwide (5 cols) + schema YAML with I2/I3/I9/I10 invariants. PIPELINE_SECTION 01_04 flip-then-flip-back.

Sub-case B (HH-B): emit `defer_decision` artifact; no VIEW; no status change.

Cell KK: append DS-SC2-IDENTITY-01 ADDENDUM to new 01_04_04b JSON (not overwriting 01_04_04).

### T07 — Artifacts + research_log + status

Cells LL-QQ:
- LL: assemble `01_04_04b_worldwide_identity.json` (all sections + ≥8 SQL queries verbatim + ≥5 literature citations). **P10-WARNING fix (temporal scope declaration):** add top-level JSON key `identity_key_temporal_scope` = "computed from full entity history (all games per (region, realm, toon_id)); identity is offline cleaning-layer artifact, not per-game feature; methodologically defensible — standard record-linkage practice (Christen 2012 Ch. 5) — but downstream Phase 02 per-time-T rating features MUST filter matches by match_time < T independently of this identity grouping. No feature-level temporal leakage, but group membership at T is decided using T+Δ data. Declared as controlled assumption." **P5-WARNING fix (UNCERTAIN methodology declaration):** add key `uncertain_resolution_policy` = "UNCERTAIN pairs treated as SPLIT for composition (conservative default). Sensitivity analysis (all-UNCERTAIN-to-MERGE alternative) run in Cell LL and reported as additional `player_id_worldwide_sensitivity_merge_all` mapping. Difference in n_components between default and sensitivity is the measurement of UNCERTAIN's impact on Phase 02 rating backtests." CSV `01_04_04b_uncertain_pairs_for_review.csv` preserved for future manual review but with no blocking dependency.
- MM: MD report
- NN: research_log addendum (prepend dated entry, remove [REVIEW] if sub-case A, keep if B)
- OO: STEP_STATUS new step `01_04_04b: complete`. PHASE_STATUS unchanged.
- PP: ROADMAP.md append sub-step block under Step 01_04_04
- QQ: final gate checks

## File Manifest

**NEW:**
- `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_04b_worldwide_identity.{py,ipynb}`
- `src/rts_predict/common/union_find.py` + `tests/rts_predict/common/test_union_find.py`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_04b_worldwide_identity.{json,md}`
- 7 CSVs under `reports/artifacts/01_exploration/04_cleaning/01_04_04b_*.csv`:
  pairs_with_signals, apm_same_entity_null, apm_cross_entity_control, pair_decisions, uncertain_pairs_for_review, entity_to_wid_mapping, component_detail
- 5 PNGs under `reports/artifacts/01_exploration/04_cleaning/plots/01_04_04b_*.png`:
  entity_apm_support, signal_distributions, thresholds, decision_distribution, component_size_distribution
- **(Sub-case A only)** `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_identity_worldwide.yaml`

**MODIFIED:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` (append 01_04_04b sub-step)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` (add 01_04_04b)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/PIPELINE_SECTION_STATUS.yaml` (flip-then-flip-back if sub-case A; byte-identical if sub-case B)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` (prepend)

**NOT touched (I9):**
- All sc2egset raw tables + all view YAMLs except new one (sub-case A)
- aoestats + aoec files
- PHASE_STATUS.yaml

## Gate Condition

- 7 CSVs + 5 PNGs non-empty
- JSON has ≥8 sql_queries + ≥5 literature citations
- `pytest tests/rts_predict/common/test_union_find.py` passes
- Self-pair self-recognition ≥95% MERGE (T04 Cell W)
- ≥3 of 5 signals discriminate (T03)
- At least one multi-region component (T05 sanity)
- Every entity mapped to exactly one player_id_worldwide
- STEP_STATUS 01_04_04b = complete
- PIPELINE_SECTION 01_04 = complete (end state)
- **Sub-case A:** VIEW exists in DuckDB; schema YAML with 5 cols + I2/I3/I9/I10
- **Sub-case B:** `defer_decision` block with rule-violation reason
- I9 empty diff on all upstream sc2egset view + raw YAMLs

## Open Questions

- **Q1:** Include `component_size` in VIEW? Planner recommends NO (keep 5 cols minimal; metadata in CSV).
- **Q2:** UNCERTAIN pairs flag in sibling VIEW? Planner recommends NO (conservative SPLIT; revisit Phase 02 if needed).
- **Q3:** 5-game APM support floor too strict? Review T02 histogram before T03.
- **Q4:** Within-region collisions — same signals or separate analysis? Current plan uses same signals + within-region special-case in T04 V. User may split to T04a/T04b.
- **Q5:** Commit cadence — planner recommends 3 commits (T01-T02, T03-T05, T06-T07).

## Adversarial instruction

Category A — single pre-execution adversarial round per "less ceremony" directive. Focus: APM-JSD threshold derivation vs Hahn 2020, case-variant guard mechanism, UNCERTAIN loopback, VIEW+YAML+ROADMAP scope in T06/T07 sub-case A.
