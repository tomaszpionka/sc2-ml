# Thesis Writing Status

Last updated: 2026-04-11

---

## Status key

| Status | Meaning |
|--------|---------|
| `SKELETON` | Header and brief note exist. No prose. |
| `BLOCKED` | Feeding phase incomplete — cannot write yet. |
| `DRAFTABLE` | Feeding phase complete — ready to draft. |
| `DRAFTED` | First draft exists. May need revision later. |
| `REVISED` | Updated after later phase provided new context. |
| `FINAL` | Content-complete, ready for typesetting. |

---

## Formatting targets

Minimum length: **72,000 characters with spaces** (~40 normalized pages, typical 60–80).
Abstract: 400–1500 characters. Keywords: 3–5.
Full validation rules: `.claude/thesis-formatting-rules.yaml` → `content_thresholds`.
Source: `docs/thesis/PJAIT_THESIS_REQUIREMENTS.md`.

---

## Chapter 1 — Introduction

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §1.1 Background and motivation | `SKELETON` | — | Can write anytime |
| §1.2 Problem statement | `SKELETON` | — | Can write anytime |
| §1.3 Research questions | `SKELETON` | — | Can write anytime; finalise after experiments |
| §1.4 Scope and limitations | `SKELETON` | — | Can write anytime; revise after AoE2 data assessment |
| §1.5 Thesis outline | `BLOCKED` | All chapters | Write last |

## Chapter 2 — Theoretical Background

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §2.1 RTS game characteristics | `SKELETON` | — | Literature |
| §2.2 StarCraft II | `SKELETON` | Phase 01 (Data Exploration — timing, mechanics) | Game loop derivation available from literature; Phase 01 will re-derive from data. |
| §2.3 Age of Empires II | `BLOCKED` | AoE2 roadmap | Future |
| §2.4 ML methods for classification | `SKELETON` | — | Literature |
| §2.5 Player skill rating systems | `SKELETON` | — | Literature; Glicko-2 refs ready |
| §2.6 Evaluation metrics | `SKELETON` | — | Literature |

## Chapter 3 — Related Work

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §3.1 Traditional sports prediction | `SKELETON` | — | Literature |
| §3.2 StarCraft prediction literature | `SKELETON` | — | Key papers identified in research report |
| §3.3 MOBA and other esports | `SKELETON` | — | Literature |
| §3.4 AoE2 prediction | `BLOCKED` | AoE2 lit review | Future |
| §3.5 Research gap | `SKELETON` | — | Can draft now |

## Chapter 4 — Data and Methodology

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §4.1.1 SC2EGSet description | `BLOCKED` | Phase 01 (Data Exploration) | Steps 01_01–01_07 done; awaiting Step 01_08 (game settings + field completeness audit) |
| §4.4.4 Evaluation metrics | `SKELETON` | — | Can draft from literature |

Remaining 11 sections all `BLOCKED` — waiting on Phase 01–04 (SC2) and AoE2 roadmap phases.

## Chapter 5 — Experiments and Results

All 6 sections `BLOCKED` — waiting on Phases 03-05 (SC2) and AoE2 phases.

## Chapter 6 — Discussion

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §6.5 Threats to validity | `SKELETON` | — | Can start listing now |

Remaining 4 sections all `BLOCKED` — waiting on Chapter 5.

## Chapter 7 — Conclusions

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §7.3 Future work | `SKELETON` | — | Can accumulate ideas throughout |

Remaining 2 sections all `BLOCKED` — waiting on Chapters 5–6.

## Appendices

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| Appendix E — Code repository | `SKELETON` | — | Repo structure description |

Remaining 4 appendices all `BLOCKED` — waiting on Phase 01–05 artifacts.
