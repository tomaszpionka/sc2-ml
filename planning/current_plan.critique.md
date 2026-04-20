# Adversarial Review — planning/current_plan.md (BACKLOG F1)

**Plan:** `planning/current_plan.md` (BACKLOG F1 + coupled W4 — aoestats `canonical_slot`)
**Phase:** aoestats Phase 02 unblocker (amendment to Phase-01 closed VIEW `matches_history_minimal`)
**Branch:** `feat/aoestats-canonical-slot`
**Category:** A (science)
**Date:** 2026-04-20

## Pass 1 (2026-04-19): **REDESIGN**

Planner's default derivation (A1 `profile_id`-ordered, "lo_id"/"hi_id") directly contradicted the upstream 01_04_05 Q4 verdict which explicitly rejected profile_id ordering as a slot-neutralizing technique (Q4 showed `lower_id_first_win_rate = 0.5066 (+0.66pp)` — *larger* than the team=1 artefact being neutralized — because account age correlates with skill via early-adopter effect).

**I9 violation:** plan overwrote the upstream step's verdict using the same numerical evidence without any artifact or CROSS-log justification.

**Additional BLOCKER (I7):** `0.015` orthogonality threshold reused from spec §11 CMH-stratified effect floor — a different diagnostic. Magic-number threshold laundering.

**Verdict:** REDESIGN, not fix-in-place. Three options presented:
- A1 `profile_id` (reject — 01_04_05 Q4 verdict stands)
- A2 `old_rating` (honest but skill-coupled by construction)
- Hash on sorted `(min, max)` tuple (also inherits skill correlation; rejected by user + reviewer on second pass)

## User decision (2026-04-20)

Hash-based selected. Clarification: hash on `match_id` (match-level identifier), NOT on player-ordering signals.

Reviewer's original "hash on sorted IDs" suggestion was itself flawed because it still depends on player-property magnitudes. Correct skill-orthogonal approach is hash of `match_id`, which does not encode any player property.

## Pass 1 revision (2026-04-20)

Plan rewritten with hash-on-`match_id` as the sole derivation:
- Problem Statement "Two atomic derivation candidates" block replaced with "Derivation: hash of match_id, skill-orthogonal by construction" + explicit rejection block for all three alternatives (profile_id, old_rating, hash-on-sorted-IDs).
- Assumption A1: hash-on-match_id with falsifier = "if match_id encoded player identity, orthogonality would fail; verified in 01_02_02 schema profiling that match_id is a monotonic crawler counter".
- Unknown U1: RESOLVED 2026-04-20 (user selected hash).
- Literature context: hash-on-match_id directly adopts 01_04_05 Q3 null-reference `hash(game_id) % 2` pattern.
- T01 step 2 DDL: replaced with `CASE WHEN (hash(match_id) + focal_team) % 2 = 0 THEN 'slot_A' ELSE 'slot_B' END` for both p0_half and p1_half.
- T01 step 5 assertions: `0.015` magic-number threshold removed. Skill-orthogonality established by construction (hash depends only on match_id); per-slot balance reported as evidence, not gated.
- T02 YAML column description, T03 invariants note, T04 INVARIANTS row, T05 spec §14 v1.1.0 text, T08 research logs, T09 CHANGELOG bullet, Gate Condition, Open Questions Q1, Critique section Q1 — all updated to hash-on-match_id framing.
- Two intentional historical references to profile_id Q4 retained in the "alternatives rejected" explanatory block and in the Pass 1 critique-defence section — these are records of the decision rationale, not stale claims.

## Verdict status

**Pending Pass 2 reviewer-adversarial** on the revised plan. Expected verdict: EXECUTE (contingent on reviewer confirming that hash-on-match_id addresses the BLOCKERs cleanly and introduces no new ones).

Pass 2 dispatch: automatic after this critique file commits; user asleep until ~+4h from 2026-04-20 wake-up.
