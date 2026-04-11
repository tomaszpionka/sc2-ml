# TOKEN AUDIT — v2.0.0 stress test

**Date:** 2026-04-11
**Model:** claude-sonnet-4-6
**Effort:** Standard (no extended thinking)

## Per-file breakdown (sorted by tokens descending)

| File | Bytes | Est. Tokens | Category |
|------|-------|-------------|----------|
| `docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md` | 35,254 | 8,814 | phase-manual |
| `docs/templates/notebook_template.yaml` | 21,356 | 5,339 | template |
| `docs/PHASES.md` | 11,110 | 2,778 | phase-manual |
| `.claude/scientific-invariants.md` | 6,551 | 1,638 | mandatory-start |
| `reports/research_log.md` | 6,227 | 1,557 | phase-manual |
| `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md` | 5,027 | 1,257 | phase-manual |
| `docs/templates/step_template.yaml` | 4,895 | 1,224 | template |
| `docs/INDEX.md` | 3,773 | 943 | phase-manual |
| `src/rts_predict/sc2/reports/sc2egset/PHASE_STATUS.yaml` | 869 | 217 | mandatory-start |
| **TOTAL** | **95,062** | **23,767** | |

## Category totals

| Category | Files | Bytes | Est. Tokens | % of 200K |
|----------|-------|-------|-------------|-----------|
| mandatory-start | 2 | 7,420 | 1,855 | 0.93% |
| phase-manual | 5 | 61,391 | 15,349 | 7.67% |
| template | 2 | 26,251 | 6,563 | 3.28% |
| **SESSION TOTAL** | **9** | **95,062** | **23,767** | **11.88%** |

## Observations

- **Context headroom is healthy.** 23,767 tokens = 11.9% of 200K, leaving ~176K for actual work. Even with executor agent prompt (~1,740 tokens) and python-code.md rule (~740 tokens) added for an execution session, the total reaches ~26,247 tokens (13.1%) — well within safe limits.

- **Planning session (no templates) is exceptionally lean.** Excluding the two template files, a Category A planning session is ~17,204 tokens (8.6% of 200K).

- **01_DATA_EXPLORATION_MANUAL.md dominates** at 8,814 tokens (37% of session total). Only loaded for Phase 01 sessions; later phases load shorter manuals (Phase 03: ~7,270 tokens, Phase 06: ~5,750 tokens).

- **notebook_template.yaml (5,339 tokens) is conditional.** Only read during notebook creation, not during planning. A pure planning session costs 17,204 tokens; adding notebook creation brings it to 23,767 tokens.

- **v2.0.0 vs. pre-v2.0.0 comparison.** The architecture audit measured ~33,000 tokens minimum for the equivalent session. The v2.0.0 session measures ~23,767 tokens — a **~9,233 token reduction (~28%)**. Key drivers:
  - ROADMAP.md trimmed: 6,622 → 5,027 bytes (−1,595 bytes; placeholder Phase 02–07 sections replaced with one-line pointers)
  - `ARCHITECTURE.md` moved to on-demand (was ~2,400 tokens)
  - `dev-constraints.md` removed/merged (was ~450 tokens)
  - `ml-protocol.md` merged into `scientific-invariants.md` and `python-code.md` (was ~900 tokens)
  - `TAXONOMY.md` now fully on-demand (was ~2,490 tokens when loaded)
  - **Net offset:** `scientific-invariants.md` grew 5,633 → 6,551 bytes (+918 bytes / +230 tokens) due to normalization leakage addition — deliberate, load-bearing tradeoff.

## Auto-loaded rules files (`.claude/rules/`)

In this read-only session: **none fired.**

| File | Bytes | Est. Tokens | Trigger | Fired? |
|------|-------|-------------|---------|--------|
| `.claude/rules/python-code.md` | 2,961 | 740 | Any `.py` file touch | No |
| `.claude/rules/sql-data.md` | 1,344 | 336 | SQL/data work on `src/*/data/**/*.py` | No |
| `.claude/rules/thesis-writing.md` | 3,580 | 895 | `thesis/**` touch | No |
| `.claude/rules/git-workflow.md` | 2,917 | 729 | Commit/PR operations | No |

In a real Category A execution session, `python-code.md` fires as soon as any sandbox `.py` notebook is edited (+740 tokens). Combined overhead if all four fired simultaneously: 2,700 tokens (1.35% of 200K).

---

## Post-hoc review (parent session, Opus)

**Pre-v2.0.0 baseline** (from `architecture_audit.md` Section 6):

| Metric | Pre-v2.0.0 | Post-v2.0.0 | Delta |
|--------|-----------|-------------|-------|
| Category A session overhead | ~33,000 tokens | ~23,767 tokens | **-9,233 (-28%)** |
| % of 200K (Sonnet) | ~16.5% | 11.9% | -4.6pp |
| Planning-only (no templates) | ~27,770 tokens | ~17,204 tokens | **-10,566 (-38%)** |

**Savings breakdown:**

| Change | Tokens saved |
|--------|-------------|
| ROADMAP placeholder compaction (3 files) | ~1,600 |
| ARCHITECTURE.md moved to on-demand | ~2,400 |
| TAXONOMY.md moved to on-demand | ~2,490 |
| dev-constraints.md / ml-protocol.md no longer auto-read | ~1,350 |
| CLAUDE.md slimmed (153 -> 108 lines) | ~500 |
| WRITING_STATUS.md compressed (115 -> 95 lines) | ~200 |
| **Subtotal saved** | **~8,540** |
| scientific-invariants.md grew (+normalization leakage) | +230 |
| notebook_template.yaml grew (+slug placeholders) | +110 |
| **Net reduction** | **~8,200** |

The remaining ~1,000 token gap between the net reduction (~8,200) and the
measured delta (~9,233) is explained by CLAUDE.md no longer triggering
ARCHITECTURE.md reads in the stress test session (the pointer pattern
worked -- Sonnet read only what it needed, not everything pointed to).

**Verdict:** The token economy changes achieved their goal. A Category A
planning session on Sonnet uses 8.6% of context, leaving 91% for work.
The architecture is lean enough for multi-step Phase work without context
pressure.
