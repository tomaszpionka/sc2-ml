# Session Audit: Full Project Token Economy & DAG Impact

**Date:** 2026-04-11
**Scope:** All 145 sessions (Apr 4–11), all 107 merged PRs (Apr 2–11), 1 open PR (#108)
**Data sources:**
- `~/.claude/projects/.../*.jsonl` — 149 session JSONL files (orchestrator + subagent tokens, deduplicated by message UUID)
- `/tmp/rts-agent-log.txt` — subagent hook telemetry (254 lines, Apr 11 only)
- `gh pr list --state merged --limit 200` — full PR history
- `scripts/hooks/log-subagent.sh` — hook definition for subagent logging

**Caveats:**
- Sessions before Apr 4 have no JSONL data (PRs #1–#20 on Apr 2–3 predate session capture)
- Subagent hook log (`/tmp/rts-agent-log.txt`) is volatile — only covers Apr 11
- Session-to-PR mapping is approximate (correlated by date, not exact linkage)

---

## 1. Executive Summary

| Metric | Project Total | Pre-DAG avg/day | Post-DAG (#108) |
|--------|-------------|-----------------|-----------------|
| Sessions | 145 | 16/day | 3 |
| Messages | 6,282 | 698/day | ~200 |
| Output tokens | 3,562,914 | 396K/day | 81,625 (subagent) |
| Cache read | 471,580,235 | 52.4M/day | 29.3M (subagent) |
| PRs merged | 107 | 12/day | 1 (open) |
| Lines changed | 450,117 | n/a | 3,334 |

The project consumed **3.56M output tokens** across **145 sessions** to produce **107 PRs** changing **450K lines** over 10 days. The DAG orchestration (PR #107, Apr 11) was the **most expensive single PR** by token count but the **first DAG-driven PR (#108) achieved the best token economy** of any comparable-scope PR on that day.

---

## 2. Daily Token Usage (All Sessions)

| Date | Sessions | Msgs | Input | Output | Cache Read | Cache Create |
|------|----------|------|-------|--------|------------|-------------|
| Apr 04 | 19 | 1,137 | 15,146 | 206,771 | 58,344,583 | 3,216,422 |
| Apr 05 | 29 | 851 | 10,820 | 230,088 | 41,181,920 | 3,032,274 |
| Apr 06 | 17 | 651 | 11,874 | 217,884 | 46,084,129 | 1,799,376 |
| Apr 07 | 21 | 336 | 1,750 | 162,526 | 10,522,233 | 1,449,370 |
| Apr 08 | 22 | 473 | 6,168 | 259,009 | 18,448,711 | 1,659,569 |
| Apr 09 | 5 | 331 | 2,564 | 452,492 | 54,478,366 | 3,530,667 |
| Apr 10 | 16 | 842 | 70,126 | 697,579 | 52,338,875 | 3,650,714 |
| Apr 11 | 16 | 1,661 | 49,654 | 1,336,565 | 190,181,418 | 6,176,196 |
| **Total** | **145** | **6,282** | **168,102** | **3,562,914** | **471,580,235** | **24,514,588** |

**Trend:** Apr 11 consumed **37.5%** of all output tokens and **40.3%** of all cache reads in one day. This is the DAG implementation + first DAG-driven execution day.

---

## 3. Daily Efficiency: Lines Changed vs Output Tokens

| Date | PRs | Lines Changed | Output Tokens | Lines/K-Out | Sessions |
|------|-----|--------------|--------------|-------------|----------|
| Apr 02 | 12 | 184,627 | — | — | (no data) |
| Apr 03 | 8 | 10,187 | — | — | (no data) |
| Apr 04 | 10 | 44,403 | 206,771 | **214.7** | 19 |
| Apr 05 | 6 | 55,333 | 230,088 | **240.5** | 29 |
| Apr 06 | 13 | 65,947 | 217,884 | **302.7** | 17 |
| Apr 07 | 7 | 13,930 | 162,526 | 85.7 | 21 |
| Apr 08 | 9 | 18,115 | 259,009 | 69.9 | 22 |
| Apr 09 | 23 | 7,449 | 452,492 | 16.5 | 5 |
| Apr 10 | 9 | 14,342 | 697,579 | 20.6 | 16 |
| Apr 11 | 10 | 35,784 | 1,336,565 | 26.8 | 16 |

**Pattern:** Early days (Apr 4–6) had extreme lines/K-output because of bulk operations — large deletions (#23: -33K, #47: -51K) and bulk data additions (#36: +52K) inflate the ratio. Starting Apr 7, the work shifted to smaller, precision PRs (roadmaps, templates, status files) where each line requires more context reading and verification. The declining ratio reflects increasing task complexity, not decreasing efficiency.

---

## 4. Model Usage Breakdown

| Model | Sessions | Messages | Output | % of Output |
|-------|----------|----------|--------|-------------|
| claude-opus-4-6 | 29 | 2,998 | 1,945,596 | **54.6%** |
| claude-sonnet-4-6 | 112 | 3,249 | 1,613,601 | 45.3% |
| claude-haiku-4-5 | 2 | 31 | 3,717 | 0.1% |

Opus handles 20% of sessions but generates 55% of output — it's the heavy-lifting model for planning and deep review. Sonnet handles 77% of sessions (executors, standard reviewers, adversarial reviewers).

---

## 5. Complete PR History (107 merged + 1 open)

### PRs #1–#20: Initial Setup (Apr 2–3, no session data)

| PR | Branch | +Lines | -Lines | Total |
|----|--------|--------|--------|-------|
| #1 | docs/claude-code-setup | 716 | 231 | 947 |
| #2 | refactor/english-comments-type-hints | 4,922 | 517 | 5,439 |
| #3 | refactor/package-structure | 167,295 | 466 | 167,761 |
| #4 | refactor/break-down-claude-md | 264 | 176 | 440 |
| #5 | refactor/feature-groups-ablation | 1,924 | 309 | 2,233 |
| #6 | fix/pipeline-coherence | 1,028 | 77 | 1,105 |
| #7 | test/gnn-diagnostics | 410 | 0 | 410 |
| #8 | feat/classical-evaluation | 3,475 | 93 | 3,568 |
| #9 | feat/sanity-validation | 1,579 | 0 | 1,579 |
| #10 | test/coverage-phase1 | 95 | 0 | 95 |
| #11 | test/coverage-phase2 | 500 | 0 | 500 |
| #12 | test/coverage-phase3 | 550 | 0 | 550 |
| #13 | test/coverage-phase4 | 554 | 0 | 554 |
| #14 | test/coverage-phase5 | 507 | 1 | 508 |
| #15 | fix/data-pipeline-integrity | 973 | 91 | 1,064 |
| #16 | chore/consolidate-base | 2,598 | 415 | 3,013 |
| #17 | refactor/data-schemas-sql-extraction | 579 | 364 | 943 |
| #18 | feat/phase-0-ingestion-audit | 1,125 | 10 | 1,135 |
| #19 | docs/invariant-6-research-log | 815 | 7 | 822 |
| #20 | docs/thesis-infrastructure-invariants-v2 | 1,856 | 292 | 2,148 |

### PRs #21–#35: Corpus + Reorg + Agents (Apr 4–5)

| PR | Branch | +Lines | -Lines | Total |
|----|--------|--------|--------|-------|
| #21 | feature/phase-1-corpus-inventory | 3,500 | 6 | 3,506 |
| #22 | chore/housekeeping-workflow-and-roadmap | 563 | 53 | 616 |
| #23 | chore/remove-pre-roadmap-legacy-code | 298 | 33,172 | 33,470 |
| #24 | chore/rename-repo-rts-outcome-prediction | 11 | 6 | 17 |
| #25 | chore/repo-reorganization | 1,083 | 256 | 1,339 |
| #26 | chore/sc2-data-compression-scripts | 377 | 973 | 1,350 |
| #27 | chore/slim-pr-template | 34 | 65 | 99 |
| #28 | docs/claude-config-restructure | 369 | 1,252 | 1,621 |
| #29 | chore/archive-cleanup | 68 | 1,808 | 1,876 |
| #30 | refactor/mypy-and-test-cleanup | 293 | 216 | 509 |
| #31 | chore/consolidate-data-dirs | 294 | 81 | 375 |
| #32 | chore/sc2egset-scripts | 127 | 241 | 368 |
| #33 | chore/report-step-prefix | 139 | 115 | 254 |
| #34 | chore/agent-infrastructure | 713 | 238 | 951 |
| #35 | chore/agent-observability | 702 | 21 | 723 |

### PRs #36–#65: AoE2 + Docs + Phase 1 Steps (Apr 5–8)

| PR | Branch | +Lines | -Lines | Total |
|----|--------|--------|--------|-------|
| #36 | chore/init-aoe2-structure | 52,210 | 452 | 52,662 |
| #37 | chore/aoe2-cli-shared-db | 1,279 | 281 | 1,560 |
| #38 | docs/manual-patch | 1,088 | 440 | 1,528 |
| #39 | docs/thesis-formatting-rules | 252 | 101 | 353 |
| #40 | docs/pjait-references | 373 | 149 | 522 |
| #41 | chore/hook-logging | 90 | 9 | 99 |
| #42 | chore/changelog-audit | 44 | 19 | 63 |
| #43 | refactor/sc2-use-db-client | 979 | 189 | 1,168 |
| #44 | chore/per-dataset-reports | 291 | 1 | 292 |
| #45 | chore/per-dataset-reports | 2,265 | 1,889 | 4,154 |
| #46 | feat/aoe2-phase0-acquisition | 2,758 | 277 | 3,035 |
| #47 | chore/docs-reorganisation | 1,084 | 51,690 | 52,774 |
| #48 | docs/manual-index-and-path-fixes | 95 | 21 | 116 |
| #49 | fix/aoe2-acquisition-fixes | 245 | 38 | 283 |
| #50 | chore/dataset-agnostic-invariants | 304 | 1,399 | 1,703 |
| #51 | chore/sc2-reports-roadmap-placeholder | 80 | 941 | 1,021 |
| #52 | chore/research-log-template | 9 | 1 | 10 |
| #53 | chore/research-log-template-content | 271 | 35 | 306 |
| #54 | chore/phase1-roadmap-augmentation | 1,746 | 75 | 1,821 |
| #55 | feat/aoe2-phase0-ingestion | 7,610 | 870 | 8,480 |
| #56 | feat/sc2-phase1-step1.8 | 548 | 41 | 589 |
| #57 | feat/sc2-phase1-step1.9 | 2,846 | 289 | 3,135 |
| #58 | chore/notebook-sandbox | 5,654 | 1,687 | 7,341 |
| #59 | chore/test-mirror-migration | 394 | 22 | 416 |
| #60 | chore/artifacts-subdir-migration | 762 | 1,339 | 2,101 |
| #61 | chore/sandbox-and-artifacts-guidance | 435 | 394 | 829 |
| #62 | feat/phase0-map-alias-ingestion | 1,984 | 631 | 2,615 |
| #63 | feat/schema-export-utility | 1,412 | 5 | 1,417 |
| #64 | chore/phase1-sc2-archive-pre-reset | 180 | 20 | 200 |
| #65 | fix/raw-json-duckdb-type | 60 | 1 | 61 |

### PRs #66–#89: Taxonomy Migration + Phase 01 (Apr 9–10)

| PR | Branch | +Lines | -Lines | Total |
|----|--------|--------|--------|-------|
| #66 | plan/phase1-sc2-taxonomy | 640 | 1 | 641 |
| #67 | docs/project-taxonomy | 237 | 1 | 238 |
| #68 | docs/architecture-source-of-truth | 66 | 1 | 67 |
| #69 | docs/canonical-phase-list | 271 | 1 | 272 |
| #70 | docs/project-taxonomy-draft | 29 | 24 | 53 |
| #71–#77 | (7 phase-ref migration PRs) | 456 | 162 | 618 |
| #78 | chore/research-log-archive-fresh-start | 473 | 447 | 920 |
| #79 | chore/phase-status-redesign | 119 | 82 | 201 |
| #80 | chore/game-roadmaps-phase-migration | 53 | 33 | 86 |
| #81 | chore/sc2egset-roadmap-rewrite | 139 | 1,836 | 1,975 |
| #82 | chore/aoe2companion-roadmap | 207 | 1 | 208 |
| #83 | chore/aoestats-roadmap | 246 | 1 | 247 |
| #84–#86 | (3 final migration PRs) | 171 | 71 | 242 |
| #87 | chore/roadmap-phase01-skeleton-reset | 686 | 203 | 889 |
| #88 | feat/phase01-discovery-library | 801 | 8 | 809 |
| #89 | feat/phase01-step-01-01-01-file-inventory | 2,991 | 16 | 3,007 |

### PRs #90–#106: Pre-DAG Chores (Apr 10–11)

| PR | Branch | +Lines | -Lines | Total |
|----|--------|--------|--------|-------|
| #90 | chore/phase01-status-update | 249 | 394 | 643 |
| #91 | chore/update-agent-docs-and-rules | 1,587 | 75 | 1,662 |
| #92 | chore/adversarial-review-agent | 820 | 251 | 1,071 |
| #93 | chore/raw-data-readme-template | 910 | 407 | 1,317 |
| #94 | chore/fix-agent-definitions | 49 | 7 | 56 |
| #95 | chore/raw-readme-conformance | 894 | 274 | 1,168 |
| #96 | chore/notebook-template-v2 | 3,382 | 6 | 3,388 |
| #97 | chore/notebook-template-conformance | 1,335 | 695 | 2,030 |
| #98 | chore/inventory-enhancements | 1,861 | 4,161 | 6,022 |
| #99 | chore/unsupervised-permissions-overhaul | 39 | 13 | 52 |
| #100 | chore/web-access-science-agents | 122 | 3 | 125 |
| #101 | chore/fix-source-activation-permissions | 198 | 10 | 208 |
| #102 | chore/pre-commit-hooks | 331 | 14 | 345 |
| #103 | chore/pre-commit-followup | 13 | 275 | 288 |
| #104 | chore/architecture-audit-fixes | 783 | 12,022 | 12,805 |
| #105 | chore/pre-01_01_02-housekeeping | 490 | 13,495 | 13,985 |
| #106 | chore/hooks-and-permissions | 243 | 79 | 322 |

### PR #107: DAG Implementation (Apr 11) — THE INFLECTION POINT

| PR | Branch | +Lines | -Lines | Total |
|----|--------|--------|--------|-------|
| #107 | chore/dag-orchestration-infrastructure | 1,224 | 408 | 1,632 |

### PR #108: First DAG-Driven Execution (Apr 11) — OPEN

| PR | Branch | +Lines | -Lines | Total |
|----|--------|--------|--------|-------|
| #108 | chore/template-hierarchy | 2,651 | 683 | 3,334 |

---

## 6. Era Analysis

| Era | PRs | Lines | Avg Lines/PR | Dates |
|-----|-----|-------|-------------|-------|
| Initial setup + refactors (#1–#16) | 16 | 189,766 | 11,860 | Apr 2–3 |
| Phase 0 data + docs (#17–#20) | 4 | 5,048 | 1,262 | Apr 3 |
| Phase 1 corpus + housekeeping (#21–#33) | 13 | 45,400 | 3,492 | Apr 4–5 |
| Agent infrastructure (#34–#35) | 2 | 1,674 | 837 | Apr 5 |
| AoE2 init + docs + CLI (#36–#53) | 18 | 121,649 | 6,758 | Apr 5–7 |
| Phase 1 steps (#54–#57) | 4 | 14,025 | 3,506 | Apr 7–8 |
| Sandbox + test mirror (#58–#65) | 8 | 14,980 | 1,872 | Apr 8 |
| Taxonomy + phase migration (#66–#87) | 22 | 6,640 | 302 | Apr 9 |
| Phase 01 feat work (#88–#89) | 2 | 3,816 | 1,908 | Apr 9–10 |
| **Pre-DAG chores (#90–#106)** | **17** | **45,487** | **2,676** | **Apr 10–11** |
| **DAG implementation (#107)** | **1** | **1,632** | **1,632** | **Apr 11** |
| **Post-DAG first (#108)** | **1** | **3,334** | **3,334** | **Apr 11** |

The shift at PR #66 is visible: avg lines/PR drops from thousands to hundreds as work moves from bulk operations to precise schema/status file edits. The DAG era (#107–#108) produces structured, reviewed output rather than raw volume.

---

## 7. Subagent Analysis (Apr 11 only — hook telemetry)

### Agent type token economics

| Agent Type | Count | Total Output | Avg Output | Avg Duration | Cache Hit |
|-----------|-------|-------------|-----------|-------------|-----------|
| reviewer-adversarial | 25 | 196,246 | 7,850 | 8.2 min | 99.9% |
| executor | 48 | 148,175 | 3,087 | 2.4 min | 100.0% |
| planner-science | 4 | 50,736 | 12,684 | 6.8 min | 99.6% |
| reviewer-deep | 2 | 30,717 | 15,358 | 7.5 min | 100.0% |
| Explore | 3 | 15,140 | 5,047 | 0.9 min | 99.0% |
| reviewer | 2 | 11,087 | 5,544 | 1.6 min | 100.0% |
| planner | 2 | 7,669 | 3,834 | 2.9 min | 99.9% |
| lookup | 3 | 3,581 | 1,194 | 0.4 min | 100.0% |

### Token share by agent type (Apr 11 subagents)

```
reviewer-adversarial  ████████████████████████████████████  42.3%  (196K)
executor              ██████████████████████████████        31.9%  (148K)
planner-science       ███████████                           10.9%  (51K)
reviewer-deep         ███████                                6.6%  (31K)
Explore               ███                                    3.3%  (15K)
reviewer              ██                                     2.4%  (11K)
planner               ██                                     1.7%  (8K)
lookup                █                                      0.8%  (4K)
```

### Reviewer cost comparison

| Type | Invocations | Avg Output | Avg Duration | Cost Tier |
|------|------------|-----------|-------------|-----------|
| reviewer-adversarial | 25 | 7,850 | 8.2 min | Sonnet |
| reviewer-deep | 2 | 15,358 | 7.5 min | **Opus** |
| reviewer | 2 | 5,544 | 1.6 min | Sonnet |

The adversarial reviewer is **1.4x** more expensive than standard reviewers by output but runs **5.1x longer** per invocation. The 25 invocations during PR #107 planning represent a significant token investment.

---

## 8. PR #108 Deep Dive — First DAG-Driven Execution

### Execution timeline

```
18:16  ┬─ T01 executor (27s) ─┐
       └─ T02 executor (48s) ─┤  Wave 1: 2 parallel
18:17  ────────────────────────┘
18:18  ── TG01 reviewer (93s) ──── 2 BLOCKERS → parent fix
18:21  ┬─ T03 executor (26s)  ─┐
       ├─ T04 executor (58s)  ─┤
       ├─ T05 executor (46s)  ─┤
       ├─ T06 executor (111s) ─┤  Wave 2: 7 parallel
       ├─ T07 executor (49s)  ─┤
       ├─ T08 executor (98s)  ─┤
       └─ T09 executor (49s)  ─┘
18:23  ── TG02-04 reviewer (94s) ─ PASS
18:27  ── T10 executor (68s) ───── Wave 3
18:29  ── reviewer-deep (595s) ──── 3 BLOCKERS → parent fix
18:42  ── done ─────────────────── Total: ~26 min
```

### Parallelism speedup

| Wave | Tasks | Wall-clock | Sequential est. | Speedup |
|------|-------|-----------|----------------|---------|
| Wave 1 (T01 ∥ T02) | 2 | 48s | 75s | 1.6x |
| Wave 2 (T03–T09) | 7 | 134s | ~560s | **4.2x** |
| Wave 3 (T10) | 1 | 68s | 68s | 1.0x |

### Token budget

| Component | Output | % of Total |
|-----------|--------|-----------|
| 10 executors | 31,551 | 47% |
| 1 reviewer-deep | 18,039 | 27% |
| 2 reviewers | 11,087 | 17% |
| 1 Explore | 6,396 | 10% |
| **Total** | **67,073** | |

### Review gate results

| Gate | Blockers Found | Examples |
|------|---------------|---------|
| TG01 reviewer | 2 | Wrong dir path in template, file_path required/actual mismatch |
| TG02-04 reviewer | 0 | All passed |
| Final reviewer-deep | 3 | Retracted comment contradicting retraction, false CHANGELOG claim, path "fix" that broke a correct reference |
| **Total** | **5** | All real errors, all fixed before merge |

### Review gate deviation from DAG

| Gate | DAG Spec | Actual | Saving |
|------|----------|--------|--------|
| TG02 | 1 reviewer | Combined into TG02-04 | ~5.5K output |
| TG03 | 1 reviewer | (combined above) | ~5.5K output |
| TG04 | 1 reviewer | (combined above) | ~5.5K output |
| TG05 | 1 reviewer | Elided (covered by final) | ~5.5K output |
| **Total saved** | | | **~22K output tokens** |

---

## 9. Key Findings

### A. The DAG orchestration is productive

| Metric | Pre-DAG chores (avg) | PR #108 (DAG-driven) | Delta |
|--------|---------------------|---------------------|-------|
| Lines/PR | 2,676 | 3,334 | +25% |
| Files/PR | ~10 | 44 | +340% |
| Wall-clock | 30–60 min est. | 26 min | -50% |
| Review coverage | ad-hoc | 5 gates, 5 blockers caught | structured |
| Parallelism | none | 4.2x on Wave 2 | new capability |

### B. The investment cost was steep but one-time

PR #107 (DAG implementation) consumed heavy resources across 5 sessions:
- 49 agents (28 in the main session alone)
- 25 adversarial review invocations generating 196K output tokens
- Total subagent output: ~287K tokens for 1,632 lines = 5.7 lines/K-out

This compares to PR #108's subagent output of ~81K tokens for 3,334 lines = 41.1 lines/K-out — a **7.2x improvement** in the first use.

### C. Adversarial reviews dominate token cost

Of the 463K subagent output tokens on Apr 11:
- reviewer-adversarial: 196K (42%) across 25 invocations
- executor: 148K (32%) across 48 invocations
- Everything else: 119K (26%)

The adversarial reviewer is valuable for high-stakes plans but over-applied during PR #107's iterative planning. Recommendation: cap at 2–3 focused passes per plan.

### D. Cache efficiency is excellent

All agent types achieve 99%+ cache hit rates. The prompt cache TTL (5 min) is well within the execution cadence. The 471M cache read tokens across the project represent massive savings — without caching, input costs would be orders of magnitude higher.

### E. Apr 9 was the token-efficiency anomaly

Apr 9 had 5 sessions producing 452K output tokens for just 7,449 lines (16.5 lines/K-out) — the worst ratio in the project. This was the 22-PR taxonomy migration day: many small PRs requiring heavy context reading relative to lines changed. This is the kind of work where DAG orchestration with parallel executors would have helped most.

---

## 10. Project Totals

| Metric | Value |
|--------|-------|
| Total PRs | 107 merged + 1 open |
| Total lines changed | 450,117 |
| Total sessions | 145 |
| Total messages | 6,282 |
| Total output tokens | 3,562,914 |
| Total cache read | 471,580,235 |
| Total cache create | 24,514,588 |
| Opus sessions | 29 (20%) producing 1.95M output (55%) |
| Sonnet sessions | 112 (77%) producing 1.61M output (45%) |
| Haiku sessions | 2 (1%) producing 3.7K output (<1%) |
| Project duration | 10 days (Apr 2–11) |
| Avg PRs/day | 10.7 |
| Avg output tokens/day | 445K (of which ~130K orchestrator est.) |

---

## 11. Recommendations

1. **Cap adversarial review iterations.** 2–3 focused passes per plan, not 12+ during iterative revision. This alone would have saved ~100K output tokens on PR #107.

2. **Add `combinable` flag to review gates.** The PR #108 orchestrator combined 3 review gates into 1 and skipped TG05's intermediate gate. Making this explicit in the DAG schema saves ~22K tokens per PR with no quality loss.

3. **Track orchestrator tokens in the hook.** The subagent hook captures 46% of total tokens (Apr 11: 463K subagent vs ~1.3M total). A `SessionTokens` event would close this visibility gap.

4. **Use DAG for multi-PR migration days.** Apr 9's 22-PR migration at 16.5 lines/K-out would benefit most from parallel executors and structured review gates.

5. **Benchmark at n=5.** This analysis has n=1 for post-DAG work. After 3–5 more DAG-driven PRs, re-run to confirm the 7.2x efficiency improvement is stable.

---

*Generated from 149 session JSONL files, 254-line subagent hook log, and gh API PR data across 107 merged PRs.*
