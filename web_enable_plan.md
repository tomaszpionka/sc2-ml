# Plan: Enable Web Access for Science-Facing Agents

**Category:** C — Chore
**Branch:** chore/web-access-science-agents

---

## Context

Neither `WebFetch` nor `WebSearch` are currently enabled in `settings.json` or any agent
frontmatter. Claude Code has two independent permission gates:

1. `settings.json` → `permissions.allow` — controls whether each call requires a user prompt
2. Agent `tools:` frontmatter — controls whether an agent can call a tool at all

Both gates must be open for an agent to use web tools without friction.

---

## Steps

### Step 1 — `settings.json`: add `WebFetch` and `WebSearch` to `permissions.allow`

File: `.claude/settings.json`

Add both tools to the existing `permissions.allow` array so the main session and any
sub-agent can call them without a per-call approval prompt.

### Step 2 — Enable web tools in three science-facing agents

For each agent below, append `WebFetch, WebSearch` to the `tools:` line in the YAML
frontmatter.

| Agent | File | Rationale |
|---|---|---|
| `reviewer-adversarial` | `.claude/agents/reviewer-adversarial.md` | Primary: challenges methodology claims against published standards |
| `planner-science` | `.claude/agents/planner-science.md` | Can validate planned approach against literature during planning |
| `reviewer-deep` | `.claude/agents/reviewer-deep.md` | Can cross-check invariants against external specs during heavy review |

**Agents that must NOT receive web access:**

| Agent | Reason |
|---|---|
| `executor` | Could pull unreviewed external code into implementation |
| `writer-thesis` | Thesis prose must cite only on-disk artifacts, not live web results |
| `planner` | Code/infra planner; no scientific validation use case |
| `reviewer` | Post-change validation; scope is local code correctness |
| `lookup` | Fast lookup; web would add latency and scope creep |

### Step 3 — Add usage guidance to `reviewer-adversarial`

In the body of `.claude/agents/reviewer-adversarial.md`, add a short block that instructs
the agent **when** to use web:

- **Use WebSearch/WebFetch** to verify factual methodology claims (e.g., standard practice
  for temporal CV, published baselines, statistical test assumptions).
- **Do not** use web to import code or cite non-peer-reviewed sources.
- **Prefer** arXiv, published conference proceedings (NeurIPS, ICML, AAAI, IJCAI), and
  reputable ML/stats textbooks as sources.

---

## Files Changed

| File | Change |
|---|---|
| `.claude/settings.json` | Add `WebFetch`, `WebSearch` to `permissions.allow` |
| `.claude/agents/reviewer-adversarial.md` | Add tools to frontmatter + usage guidance block |
| `.claude/agents/planner-science.md` | Add tools to frontmatter |
| `.claude/agents/reviewer-deep.md` | Add tools to frontmatter |

---

## Gate Condition

All four files saved. No tests required (config/docs only). Verify by opening each agent
file and confirming `WebFetch, WebSearch` appears in the `tools:` line.
