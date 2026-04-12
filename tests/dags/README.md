# DAG Smoke Tests

Manual smoke tests for the DAG execution pipeline. These are not pytest tests —
they are artifacts for running canary tests in fresh Claude Code sessions to
verify the orchestration mechanics work correctly.

## How to run

1. Copy the desired test's DAG and specs into `planning/dags/` and `planning/specs/`
2. Open a fresh Claude Code session
3. Run `/dag` (or `execute the DAG`)
4. Compare results against expected outcomes below

After testing, restore the real DAG and specs (or `git checkout -- planning/`).

---

## Test 01: Single-Job Pointer Dispatch

**Date first run:** 2026-04-12
**Purpose:** Verify that executors follow spec content (not the dispatch prompt)
when dispatched with pointer-style prompts via the DAG.

**Setup:**
- `test_01_single_job/DAG.yaml` — 1 job, 1 task group, 2 parallel tasks
- `test_01_single_job/specs/spec_01_canary_alpha.md` — create `canary/01.txt`
- `test_01_single_job/specs/spec_02_canary_beta.md` — create `canary/02.txt`

**What to check:**

| # | Check | Expected |
|---|-------|----------|
| 1 | Orchestrator reads specs before dispatching? | NO — only reads DAG |
| 2 | Executor creates canary files? | YES |
| 3 | Canary file content matches spec? | YES (random suffixes prove spec was read) |
| 4 | Review gate runs? | YES |

**Results (2026-04-12):**

All checks passed. Additionally, the user modified spec_01's `file_scope` to
`canary/123456.txt` (deliberately mismatching the DAG's `canary/01.txt`).
The executor followed the SPEC filename, not the DAG — proving spec is the
contract, DAG is the routing structure. The reviewer caught the DAG/spec drift
and flagged it as a blocker.

Key findings:
- Specs are load-bearing at execution time (not just for audit/review)
- Pointer dispatch prevents content duplication
- Priority: spec content > DAG metadata > dispatch prompt
- Review gates catch spec/DAG drift

---

## Test 02: Multi-Job DAG with /dag Skill

**Date first run:** 2026-04-12
**Purpose:** Verify that the `/dag` skill correctly handles multiple independent
jobs (simulating parallel dataset work) and that multi-job orchestration works.

**Setup:**
- `test_02_multi_job/DAG.yaml` — 2 independent jobs (J01_alpha, J02_beta),
  each with 1 task group and 1 task
- `test_02_multi_job/specs/spec_01_canary_alpha.md` — create `canary/alpha.txt`
  in J01_alpha
- `test_02_multi_job/specs/spec_02_canary_beta.md` — create `canary/beta.txt`
  in J02_beta

**What to check:**

| # | Check | Expected |
|---|-------|----------|
| 1 | `/dag` skill fires correctly? | YES |
| 2 | Orchestrator sees 2 jobs and dispatches them? | YES |
| 3 | Pointer dispatch (no spec reading)? | YES |
| 4 | Both canary files created with correct content? | YES |
| 5 | Review gates run per job? | YES |
| 6 | Final review runs across all jobs? | YES |

**Results (2026-04-12):**

All checks passed:
- `/dag` skill fired correctly
- Both jobs dispatched (J01_alpha, J02_beta)
- Both tasks completed (T01, T02)
- Both review gates: APPROVE
- Final review: BLOCKER (correctly flagged uncommitted canary artifacts — the
  DAG and specs were not committed before testing, so the reviewer saw a
  git state inconsistency; this is the reviewer working correctly, not a
  system failure)

Key findings:
- Multi-job DAGs work — independent jobs dispatch and execute
- The `/dag` skill codifies the execution protocol successfully
- Per-job review gates work independently
- Final review sees the full cross-job diff

---

## Baseline Runs (Pre-Fix, 2026-04-12)

Two baseline tests were run BEFORE adding the dispatch rules to CLAUDE.md
and the spec-first protocol to executor.md. Both failed:

**Baseline 1:** Orchestrator read `current_plan.md` despite being told to
execute the DAG. Noticed the DAG was "stale" and invoked `/materialize_plan`
autonomously, deleting existing specs.

**Baseline 2:** Same behavior — orchestrator read the plan even with a NEVER
rule in Critical Rules, because the DAG's `branch:` field didn't match the
current branch. The orchestrator treated the inconsistency as justification
to override the rule.

**Root cause:** Without explicit dispatch rules AND a consistent DAG, the
orchestrator defaults to "gather context" behavior (reading the plan). The
fix was two-fold: (1) add dispatch rules to CLAUDE.md, (2) ensure the canary
DAG was consistent with the current branch.
