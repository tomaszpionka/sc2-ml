# Literature Chapter Writing Manual

Operational manual for producing dataset-agnostic thesis chapters using
Claude Code subagents. Covers the full flow from calibration through Chat
handoff.

Created: 2026-04-13. Supersedes ad-hoc dispatch — follow this sequence.

---

## Prerequisites

**Model/effort.** Set your Claude Code session to Opus max before starting:

    /model opus

All three subagents (planner-science, writer-thesis, reviewer-adversarial)
are defined as `model: opus, effort: max` in `.claude/agents/`. The session
model affects the orchestrator's dispatch quality.

**No commits during drafting.** The orchestrator will modify thesis files.
Review diffs before committing.

---

## Recommended Chapter Order

| Order | What | Sections | Why this order |
|-------|------|----------|---------------|
| 1 | Gate 0 | §1.1 | Voice calibration — must pass first |
| 2 | Gate 0.5 | §2.5 | Literature calibration — must pass before scaling |
| 3 | Ch 1 production | §1.2, §1.3, §1.4 | Framing chapter, low risk |
| 4 | Ch 2 production | §2.1, §2.4, §2.6 | Theory chapter (§2.2 partial, §2.3 blocked) |
| 5 | Ch 3 production | §3.1, §3.2, §3.3 | Related work (§3.4-§3.5 blocked) |
| 6 | Standalone | §4.4.4, §6.5, §7.3 | Small independent sections |

---

## Phase 1: Calibration

### Session A — Gate 0 (§1.1)

Gate 0 has no plan. Dispatch writer-thesis directly. The draft is real (not
throwaway) — if it passes, §1.1 is DRAFTED.

**Prompt to paste:**

```
Dispatch writer-thesis to draft §1.1 (Background and motivation) as a
Gate 0 voice calibration.

This is a literature section — follow the literature variant from
.claude/rules/thesis-writing.md.

Section scope (from THESIS_STRUCTURE.md):
- Growth of esports as a domain for data science research
- Real-time strategy games as particularly rich prediction problems
  (imperfect information, asymmetric factions, complex decision trees)
- Practical applications: broadcasting, betting markets, coaching tools,
  AI agent evaluation

Target: ~2 pages of Polish academic prose.

After drafting, produce a Chat Handoff Summary with citation count and
flag count.
```

**What to evaluate (all four must pass):**

1. Does the register sound like Polish academic CS prose, not translated
   from English? Check for: natural szyk zdania, Polish hedging idioms
   ("zaobserwowano", "na podstawie analizy można stwierdzić"), no
   anglicisms where Polish equivalents exist.
2. Is argumentative structure present? Not just "esports grow" but "why
   RTS games are harder to predict than turn-based, and why that matters."
3. Does hedging appear in appropriate places?
4. Are citations present and from primary sources (no Wikipedia)?

**If any criterion fails:** Diagnose (style brief issue, agent
calibration, or source material). Fix before proceeding to Gate 0.5.

**If all pass:** Proceed to Gate 0.5.

---

### Session B — Gate 0.5 (§2.5)

Same pattern: no plan, direct writer-thesis dispatch. If it passes, §2.5
is DRAFTED.

**Prompt to paste:**

```
Dispatch writer-thesis to draft §2.5 (Player skill rating systems) as a
Gate 0.5 literature calibration.

This is a literature section — follow the literature variant from
.claude/rules/thesis-writing.md.

Section scope (from THESIS_STRUCTURE.md):
- Elo (Elo 1978): logistic model, K-factor, expected score formula
- Glicko / Glicko-2 (Glickman 1999, 2001): rating deviation, volatility
- TrueSkill (Herbrich et al. 2006): Bayesian factor graphs
- Aligulac's race-matchup-specific Glicko variant for SC2
- How derived ratings serve as features in ML models

Canonical references that MUST appear:
- Elo, A. E. (1978). The Rating of Chessplayers, Past and Present.
- Glickman, M. E. (1999). Parameter estimation in large dynamic paired
  comparison experiments. Applied Statistics, 48(3).
- Glickman, M. E. (2001). Dynamic paired comparison models with
  stochastic variances. Journal of Applied Statistics, 28(6).
- Herbrich, R., Minka, T., & Graepel, T. (2006). TrueSkill: A Bayesian
  Skill Rating System. NeurIPS.

Target: ~3 pages of Polish academic prose. Each rating system presented
with the same depth pattern (formulation, assumptions, strengths,
weaknesses). Connect rating systems to the thesis prediction task —
explain why derived ratings serve as ML features.

After drafting, produce a Chat Handoff Summary with citation count and
flag count.
```

**What to evaluate (all four must pass):**

1. **Citation density:** >= 2 references per page
2. **Canonical coverage:** All 4 mandatory references present and
   correctly characterized
3. **Structural coherence:** Each rating system has the same depth pattern
4. **Critical evaluation:** Not just "Elo works as follows" — connects
   to the thesis, explains why derived ratings matter for prediction

**If any criterion fails:** Diagnose and fix. Do not scale.

**If all pass:** Proceed to production.

---

## Phase 2: Production (per chapter)

Each chapter follows a 6-step flow. Steps 1-3 (plan, review, approve) run
in one session. Steps 4-6 (write, review, handoff) run in a fresh session.

### Step 1 — Plan

**Prompt to paste** (example for Chapter 1, §1.2-§1.4):

```
Dispatch planner-science to produce a Category F literature plan for
Chapter 1 remaining sections: §1.2 (Problem statement), §1.3 (Research
questions), §1.4 (Scope and limitations).

This is a literature chapter plan — use the literature variant:
- Per section: seed bibliography (5-10 key refs), structural principle,
  "must contrast" list, "must cite" list, expected length
- source_artifacts: THESIS_STRUCTURE.md, author-style-brief-pl.md,
  scientific-invariants.md, thesis/chapters/01_introduction.md (§1.1
  already drafted)
- DAG with task groups for parallel batches. Per the parallelism map:
  §1.2 || §1.3 (parallel-safe), then §1.4 (depends on §1.2 and §1.3)

Plan goes to planning/current_plan.md. Include a Suggested Execution
Graph section with spec_file paths.
```

**What to check in the plan output:**

- Each section has a seed bibliography (not "feeding artifacts")
- Each section has a structural principle (not "must justify")
- "Must cite" list covers canonical references for each topic
- DAG structure respects the parallelism map
- Expected lengths are reasonable

**After approval, write the plan and materialize:**

```
Write the plan to planning/current_plan.md and run /materialize_plan
```

### Step 2 — Adversarial Review of Plan

**Prompt to paste:**

```
Dispatch reviewer-adversarial (Mode A — Plan Review) on
planning/current_plan.md.

This is a literature chapter plan. In addition to standard review:
- Verify the seed bibliography: for each entry, WebSearch to confirm the
  paper exists and says what the plan claims
- Flag any topic where the seed bibliography misses a canonical reference
- Check that structural principles make sense for each section's
  rhetorical purpose
```

**What to check:** Verdict should be PROCEED or REVISE. If REVISE, fix
the plan before Step 3.

### Step 3 — Approve

Read the adversarial review. If the plan needs revision, tell Claude Code
what to change. When satisfied, proceed to Step 4.

### Step 4 — Write

Start a **fresh session** for writing. This keeps the orchestrator's
context clean for potentially multiple writer-thesis dispatches.

**Prompt to paste** (example: writing §1.2 and §1.3 in parallel):

```
Execute the DAG in planning/dags/DAG.yaml for the Chapter 1 literature
plan.

For each writer-thesis dispatch: this is a literature section. The spec
file has the section details. Dispatch writer-thesis with:
- A pointer to the spec file
- "This is a literature section — follow the literature variant from
  .claude/rules/thesis-writing.md"
- "Follow the Literature Search Protocol from
  thesis/plans/idea_audit.md"

Maximum 2 parallel writer-thesis dispatches. After all sections in a task
group complete, proceed to the next group.
```

**What to check in writer-thesis output:**

- Draft is in Polish academic prose (not bullets, not English)
- `## References` section appended at chapter file end
- WRITING_STATUS.md updated to DRAFTED
- REVIEW_QUEUE.md updated
- Chat Handoff Summary produced with citation count

### Step 5 — Adversarial Review of Draft

**Prompt to paste:**

```
Dispatch reviewer-adversarial (Mode C — Thesis Chapter Review) on
thesis/chapters/01_introduction.md.

This is a literature chapter — use tiered citation verification:
- Tier 1 (must verify): Every reference from the plan's seed bibliography
  — confirm via WebSearch that the paper exists and the draft's
  characterization is accurate
- Tier 2 (spot check): 30-50% of self-discovered references in
  peer-reviewed venues
- Tier 3 (defer): Flag supplementary references for Pass 2

Also provide: path to planning/current_plan.md for cross-checking the
seed bibliography and structural principles against the actual draft.
```

### Step 5.5 — Consistency Pass

Only after ALL sections in the chapter pass Step 5. This is a manual
check or a lightweight reviewer dispatch.

**Prompt for reviewer dispatch (optional):**

```
Dispatch reviewer on thesis/chapters/01_introduction.md for a chapter
consistency pass.

Check across all sections:
1. Terminology consistency (same concepts use same terms)
2. No redundant coverage between sections
3. Structural balance (no section >2x the length of siblings)
4. Cross-references between sections are accurate
5. Voice consistency across sections
```

**Or do it yourself:** Read the full chapter file, check the 5 items
above, fix issues directly.

### Step 6 — Chat Handoff

Take to Claude Chat (claude.ai):
- The drafted chapter file
- The Chat Handoff Summary from Step 4
- The adversarial review from Step 5
- Tier 3 citations flagged for verification

Chat does: literature validation, citation checking, [REVIEW:] flag
resolution.

---

## Chapter-Specific Prompts

### Chapter 2 (§2.1, §2.4, §2.6 — after Gate 0.5)

**Step 1 plan prompt:**

```
Dispatch planner-science to produce a Category F literature plan for
Chapter 2 remaining draftable sections: §2.1 (RTS game characteristics),
§2.4 (ML methods for binary classification), §2.6 (Evaluation metrics
and statistical comparison).

This is a literature chapter plan — use the literature variant:
- Per section: seed bibliography, structural principle, "must contrast"
  list, "must cite" list, expected length
- source_artifacts: THESIS_STRUCTURE.md, author-style-brief-pl.md,
  scientific-invariants.md, thesis/chapters/02_theoretical_background.md
  (§2.5 already drafted)
- All three sections are parallel-safe (disjoint topics). DAG: one task
  group with all three sections, max 2 parallel writer-thesis dispatches.
- §2.2 excluded (needs Phase 01 data). §2.3 excluded (blocked on AoE2).

Plan goes to planning/current_plan.md.
```

### Chapter 3 (§3.1, §3.2, §3.3)

**Step 1 plan prompt:**

```
Dispatch planner-science to produce a Category F literature plan for
Chapter 3 draftable sections: §3.1 (Outcome prediction in traditional
sports), §3.2 (StarCraft prediction literature), §3.3 (MOBA and other
esports prediction).

This is a literature chapter plan — use the literature variant:
- Per section: seed bibliography, structural principle, "must contrast"
  list, "must cite" list, expected length
- source_artifacts: THESIS_STRUCTURE.md, author-style-brief-pl.md,
  scientific-invariants.md
- All three sections are parallel-safe. DAG: one task group, max 2
  parallel writer-thesis dispatches.
- §3.4 excluded (blocked on AoE2). §3.5 excluded (blocked on §3.4).

Key references already identified in THESIS_STRUCTURE.md §3.2:
Erickson & Buro 2014, Ravari et al. 2016, Wu et al. 2017, Baek & Kim
2022, Khan et al. 2021, Lin et al. 2019, EsportsBench (Thorrez 2024).

Plan goes to planning/current_plan.md.
```

### Standalone Sections (§4.4.4, §6.5, §7.3)

These are small enough to skip the full plan cycle. Direct writer-thesis
dispatch, then adversarial review.

**§4.4.4 (Evaluation metrics):**

```
Dispatch writer-thesis to draft §4.4.4 (Evaluation metrics) as a
standalone literature section.

Follow the literature variant from .claude/rules/thesis-writing.md.

Section scope (from THESIS_STRUCTURE.md):
- Primary (probabilistic quality): Brier score with Murphy decomposition,
  log-loss
- Discrimination: accuracy, ROC-AUC, calibration curves, ECE
- Stratified analysis: per-matchup, cold-start, prediction sharpness
- Cross-game comparison: per-game rankings with bootstrapped CIs,
  5x2 cv F-test, qualitative concordance (Friedman inapplicable with
  N=2 games; Demsar 2006 requires N >= 5)

Must cite: Demsar (2006), Garcia & Herrera (2008), Benavoli et al.
(2017), Alpaydin (1999), Murphy (1973) for Brier decomposition.

Target: ~2 pages. Connect every metric to why it matters for THIS thesis
(comparing methods across two games with different data richness).
```

**§6.5 (Threats to validity):**

```
Dispatch writer-thesis to draft §6.5 (Threats to validity) as a
standalone literature section.

Follow the literature variant from .claude/rules/thesis-writing.md.

Section scope: Start listing known threats. This is a living section that
will be revised after experiments.

Structure:
- Internal validity: data quality, identity resolution errors, timestamp
  precision, potential leakage vectors
- External validity: professional-only data may not generalise to casual
- Construct validity: win/loss is binary — doesn't capture game quality

Target: ~1-2 pages. Flag with [REVIEW:] any threats that need
quantification from future experiment results.
```

**§7.3 (Future work):**

```
Dispatch writer-thesis to draft §7.3 (Future work) as a standalone
literature section.

Follow the literature variant from .claude/rules/thesis-writing.md.

Section scope: Accumulate concrete future research directions.
- Transfer learning between games
- Sequence models (LSTM/Transformer) on SC2 time series
- AoE2 replay parsing for in-game features
- Extension to team games
- Real-time prediction systems

Target: ~1 page. Each direction should have a brief justification for
why it's promising, ideally with a citation to related work.
```

---

## Quick Reference: Agent Routing

| Step | Agent | How to trigger |
|------|-------|---------------|
| Gate 0, 0.5 | writer-thesis | "Dispatch writer-thesis to draft §X.Y" |
| Step 1 (Plan) | planner-science | "Dispatch planner-science to produce a Category F literature plan" |
| Step 2 (Review plan) | reviewer-adversarial | "Dispatch reviewer-adversarial (Mode A) on planning/current_plan.md" |
| Step 3 (Approve) | — | User reads + approves, then /materialize_plan |
| Step 4 (Write) | writer-thesis | "Execute the DAG" (orchestrator dispatches per DAG) |
| Step 5 (Review draft) | reviewer-adversarial | "Dispatch reviewer-adversarial (Mode C) on thesis/chapters/XX_*.md" |
| Step 5.5 (Consistency) | reviewer or manual | "Dispatch reviewer for consistency pass" or read it yourself |
| Step 6 (Chat) | — | User takes files to claude.ai |

## Session Boundaries

- **Gates:** One session per gate. Evaluate output before next session.
- **Steps 1-3:** Can run in one session (plan → review → approve).
- **Steps 4-5.5:** Fresh session recommended (clean context for
  writer-thesis dispatches).
- **Step 6:** External (Claude Chat, not Claude Code).
