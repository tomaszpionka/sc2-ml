# Research Log Decentralization: Design Proposal

**Date:** 2026-04-12
**Category:** C (chore) — infrastructure
**Status:** Proposal (not yet planned or approved)
**Triggered by:** LATER.md item "Per-dataset research log split"

---

## 1. Problem Statement

The research log is the only reporting artifact that doesn't follow the
per-dataset pattern. Everything else is already isolated:

| Artifact | Per-dataset? | Location |
|----------|-------------|----------|
| ROADMAP.md | Yes | `src/rts_predict/<game>/reports/<dataset>/` |
| PHASE_STATUS.yaml | Yes | `src/rts_predict/<game>/reports/<dataset>/` |
| PIPELINE_SECTION_STATUS.yaml | Yes | `src/rts_predict/<game>/reports/<dataset>/` |
| STEP_STATUS.yaml | Yes | `src/rts_predict/<game>/reports/<dataset>/` |
| artifacts/ | Yes | `src/rts_predict/<game>/reports/<dataset>/artifacts/` |
| **research_log.md** | **No** | **`reports/research_log.md` (single file)** |

This anomaly creates three problems:

1. **Scale.** 3 datasets x 7 phases x multiple steps = hundreds of entries.
   An executor working on SC2 Phase 03 must scan through AoE2 entries to
   find relevant context.

2. **Agent scope.** Executors, reviewers, and planners all read the full log
   even when only one dataset is relevant. This wastes context window and
   dilutes attention.

3. **Parallel safety.** Two executors working on SC2 and AoE2 simultaneously
   would both need to append to the same file.

---

## 2. Current State

### Location
- Single unified log: `reports/research_log.md`
- 2 entries (as of 2026-04-11)
- Entry schema: `docs/templates/research_log_entry_template.yaml`
- Log schema: `docs/templates/research_log_template.yaml`

### Current entries

**Entry 1:** `[CROSS] AoE2 Dataset Strategy Decision` (2026-04-11)
- Category C — cross-dataset decision about aoe2companion vs aoestats roles
- Retracted same day (deferred role assignment to Phase 01 Step 01_06)

**Entry 2:** `[Phase 01 / Step 01_01_01] File Inventory` (2026-04-09)
- Category A — file inventories for all 3 datasets
- SC2: 22,390 files (~214.1 GB), AoE2 companion: 4,154 files, AoE2 stats: 349 files

### References across the codebase (~30 files)

- `CLAUDE.md` — "update reports/research_log.md after each Category A step"
- `.claude/agents/executor.md` — Category A rule: update research_log.md
- `.claude/agents/reviewer-deep.md` — read recent entries, check for contradictions
- `.claude/agents/reviewer-adversarial.md` — read recent entries
- `.claude/agents/planner-science.md` — check for sibling dataset decisions
- `.claude/agents/reviewer.md` — verify entry exists for Phase work
- `.claude/rules/git-workflow.md` — end-of-session checklist
- `.claude/rules/thesis-writing.md` — read relevant phase entry before writing
- `ARCHITECTURE.md` — cross-cutting files table
- `docs/INDEX.md`, `docs/TAXONOMY.md`, `docs/PHASES.md`, `docs/STEPS.md`
- `docs/templates/research_log_template.yaml`, `step_template.yaml`
- `docs/agents/AGENT_MANUAL.md`
- `docs/research/RESEARCH_LOG.md`, `RESEARCH_LOG_ENTRY.md`
- `README.md`

---

## 3. Proposed Design

### New directory layout

```
reports/
└── research_log.md              ← INDEX + [CROSS] entries only

src/rts_predict/sc2/reports/sc2egset/
├── research_log.md              ← SC2 findings
├── ROADMAP.md
├── PHASE_STATUS.yaml
├── STEP_STATUS.yaml
├── artifacts/
└── ...

src/rts_predict/aoe2/reports/aoe2companion/
├── research_log.md              ← aoe2companion findings
├── ROADMAP.md
├── ...

src/rts_predict/aoe2/reports/aoestats/
├── research_log.md              ← aoestats findings
├── ROADMAP.md
├── ...
```

### Root log (`reports/research_log.md`)

Becomes a thin index + cross-game findings only:

```markdown
# Research Log — Master Index

> Per-dataset findings live in each dataset's `research_log.md`.
> This file contains only cross-game/cross-dataset entries and
> pointers to the dataset logs.

## Dataset Logs
| Dataset | Log | Last entry |
|---------|-----|------------|
| sc2egset | [SC2 log](../src/rts_predict/sc2/reports/sc2egset/research_log.md) | YYYY-MM-DD |
| aoe2companion | [AoE2 companion log](../src/rts_predict/aoe2/reports/aoe2companion/research_log.md) | YYYY-MM-DD |
| aoestats | [AoE2 stats log](../src/rts_predict/aoe2/reports/aoestats/research_log.md) | YYYY-MM-DD |

## Cross-Game Entries

<Entries tagged [CROSS]: methodology decisions affecting all datasets,
cross-game comparison findings (Invariant #8), shared protocol decisions.
Reverse chronological order.>
```

### Per-dataset logs

Same entry template (`research_log_entry_template.yaml`), same schema,
same reverse-chronological order. The `dataset:` field stays for
machine-readability even though it's implied by the file location.

### Routing table: where things go

| Finding type | Log location | Example |
|-------------|-------------|---------|
| Dataset-specific step findings | `<dataset>/research_log.md` | "SC2 has 22,390 replay files" |
| Dataset-specific methodology | `<dataset>/research_log.md` | "SC2 data has 2-second gaps" |
| Cross-dataset strategy | `reports/research_log.md` [CROSS] | "aoe2companion primary, aoestats validation" |
| Cross-game comparison | `reports/research_log.md` [CROSS] | "Expanding windows show leakage in both" |
| Shared methodology decision | `reports/research_log.md` [CROSS] | "Use per-player split for all datasets" |
| Phase 06+ comparison results | `reports/research_log.md` [CROSS] | "SC2 model outperforms AoE2 by X" |

---

## 4. Migration Plan

### Entry 1 → root CROSS log

`[CROSS] AoE2 Dataset Strategy Decision` — stays in root. This is
genuinely cross-dataset (aoe2companion vs aoestats relationship).

### Entry 2 → split into 3 per-dataset entries

`[Phase 01 / Step 01_01_01] File Inventory` covers all 3 datasets.
Split into 3 entries, one per dataset. Each gets:
- The dataset-specific findings (file counts, sizes, gaps, date ranges)
- The shared methodology as context ("file inventory step across all datasets")
- Artifacts pointer to the dataset's own `artifacts/01_exploration/01_acquisition/`

---

## 5. Reference Updates

All ~30 references follow the same pattern:
`reports/research_log.md` → the active dataset's `research_log.md`

The executor already knows which dataset it's working on (from
PHASE_STATUS.yaml), so the resolution is natural.

### Agent definitions

| File | Current | New |
|------|---------|-----|
| `CLAUDE.md` | "update `reports/research_log.md`" | "update the active dataset's `research_log.md`" |
| `executor.md` | "Update `reports/research_log.md` after each step" | "Update the active dataset's `research_log.md` after each step" |
| `reviewer-deep.md` | "Read `reports/research_log.md` recent entries" | "Read the active dataset's `research_log.md` + root CROSS log" |
| `reviewer-adversarial.md` | Same as reviewer-deep | Same pattern |
| `planner-science.md` | "check `reports/research_log.md` for sibling decisions" | "check root CROSS log + sibling dataset logs if relevant" |
| `reviewer.md` | "verify entry exists" | "verify entry exists in active dataset's log" |

### Documentation

| File | Change |
|------|--------|
| `ARCHITECTURE.md` | Update cross-cutting files table: root log is index + CROSS; per-dataset logs are the primary |
| `docs/INDEX.md` | Update research log entry to show new structure |
| `docs/TAXONOMY.md` | Update Step output requirements to reference per-dataset log |
| `docs/PHASES.md` | Update Phase 07 exit gate to reference per-dataset logs |
| `docs/STEPS.md` | Update per-Step research log requirement |
| `git-workflow.md` | End-of-session checklist: update active dataset's log |
| `thesis-writing.md` | Read relevant dataset's log before writing |
| `research_log_template.yaml` | Add variant for root index vs per-dataset |
| `step_template.yaml` | Update research_log_entry pointer |
| `AGENT_MANUAL.md` | Update references |
| `README.md` | Update key document list |

---

## 6. Invariant #8 Risk and Mitigation

The one real risk: cross-game findings getting siloed in per-dataset
logs. If someone records "expanding windows show leakage in SC2" in
the SC2 log but doesn't check whether the same applies to AoE2,
Invariant #8 is violated silently.

### Mitigation: cross-game implication check

Add to planner-science.md and executor.md (Category A):

> After recording a finding in a dataset log, check whether it has
> cross-game implications. If the finding affects feature design,
> evaluation protocol, or splitting strategy, add a [CROSS] entry
> to the root log noting: which dataset the finding originated in,
> what the implication is for other datasets, and whether action is
> needed.

This makes cross-game awareness explicit rather than relying on someone
scanning a unified log and noticing patterns.

---

## 7. Timing Recommendation

**Do it before Phase 01 Step 01_01_02.**

LATER.md says "Do not touch until SC2EGSet Phase 1 closes." But this is
a strategic infrastructure decision affecting every future entry. With
only 2 entries today, migration is trivial (split 1 entry, move 1 entry).
After Phase 01 completes (~10+ entries per dataset), it becomes a real
project.

The template rewrite (current branch `chore/plan-template-rewrite`) and
the research log split are independent — they can run in parallel or
sequentially on separate branches.

**Proposed branch:** `chore/research-log-split`
**Estimated scope:** ~30 file edits (reference updates) + 3 new log files
+ 1 root log rewrite + 2 entry migrations

---

## 8. What Stays the Same

- Entry template (`research_log_entry_template.yaml`) — same schema
- Mandatory for Category A — every Step must have an entry
- Reverse chronological order within each log
- Invariant #6 compliance — "How (reproducibility)" field mandatory
- Phase 07 exit gate — all entries must be thesis-citable
- Schema compliance requirements

---

*Proposal drafted 2026-04-12 from codebase analysis of ~30 reference files
and the existing research log at reports/research_log.md.*
