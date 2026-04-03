# Thesis Writing Status

Last updated: 2026-04-03

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
| §2.2 StarCraft II | `SKELETON` | Phase 0–1 (timing, mechanics) | Game loop derivation sourced |
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
| §4.1.1 SC2EGSet description | `DRAFTABLE` | Phase 0, Phase 1 | Phase 0 complete; draft after Phase 1 for full stats |
| §4.1.2 AoE2 match data | `BLOCKED` | AoE2 roadmap | Future |
| §4.1.3 Data asymmetry | `BLOCKED` | Both datasets | Future |
| §4.2.1 Ingestion and validation | `DRAFTABLE` | Phase 0 | Phase 0 complete |
| §4.2.2 Player identity resolution | `BLOCKED` | Phase 2 | |
| §4.2.3 Cleaning rules | `BLOCKED` | Phase 6 | |
| §4.3.1 Common pre-game features | `BLOCKED` | Phase 7 | |
| §4.3.2 SC2 in-game features | `BLOCKED` | Phase 4 | |
| §4.3.3 AoE2-specific features | `BLOCKED` | AoE2 roadmap | Future |
| §4.4.1 Split strategy | `BLOCKED` | Phase 8 | |
| §4.4.2 Model configurations | `BLOCKED` | Phase 9–10 | |
| §4.4.3 Hyperparameter tuning | `BLOCKED` | Phase 10 | |
| §4.4.4 Evaluation metrics | `SKELETON` | — | Can draft from literature |

## Chapter 5 — Experiments and Results

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §5.1.1 SC2 baselines | `BLOCKED` | Phase 9 | |
| §5.1.2 SC2 pre-game prediction | `BLOCKED` | Phase 10 | |
| §5.1.3 SC2 in-game prediction | `BLOCKED` | Phase 10 | |
| §5.1.4 SC2 per-matchup / cold-start | `BLOCKED` | Phase 10 | |
| §5.2 AoE2 results | `BLOCKED` | AoE2 phases | Future |
| §5.3 Cross-game comparison | `BLOCKED` | Both complete | Future |

## Chapter 6 — Discussion

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §6.1 Interpretation | `BLOCKED` | Chapter 5 | |
| §6.2 Comparison with literature | `BLOCKED` | Chapter 5 | |
| §6.3 Generalisability | `BLOCKED` | Chapter 5 | |
| §6.4 Practical implications | `BLOCKED` | Chapter 5 | |
| §6.5 Threats to validity | `SKELETON` | — | Can start listing now |

## Chapter 7 — Conclusions

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §7.1 Summary of contributions | `BLOCKED` | All | Write last |
| §7.2 Key findings | `BLOCKED` | Chapter 5–6 | |
| §7.3 Future work | `SKELETON` | — | Can accumulate ideas throughout |

## Appendices

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| Appendix A — Infrastructure | `DRAFTABLE` | Phase 0 | Pipeline arch, schema |
| Appendix B — Feature lists | `BLOCKED` | Phase 7 | |
| Appendix C — Hyperparameters | `BLOCKED` | Phase 10 | |
| Appendix D — Additional results | `BLOCKED` | Phase 10 | |
| Appendix E — Code repository | `SKELETON` | — | Repo structure description |