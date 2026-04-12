# DAG Orchestration Framework — Extraction & Standalone Repo Plan

## 1. What This Is

The thesis repo (`rts-outcome-prediction`) contains a mature, battle-tested
orchestration system for Claude Code. It manages the **full software delivery
lifecycle**: plan → critique → materialize → execute → review → commit →
changelog → PR → ship. This document plans the extraction of that system into
a standalone, repo-agnostic framework that anyone can install into their
Claude Code project.

The system is not just a "DAG executor" — it's a complete delivery workflow.
The DAG is the most novel piece, but the commit conventions, changelog
automation, and PR templating are what make it end-to-end. Extracting only
the middle (plan → execute) without the bookends (commit → ship) would leave
adopters to reinvent the same patterns the thesis repo already solved.

**Non-goal:** destroying or degrading the thesis repo. The extraction is
additive — the thesis repo keeps working as-is. The standalone repo is built
from a clean extraction, then hardened independently. Once polished, the
thesis repo can re-adopt it as an external dependency (or not).

---

## 2. Anatomy of the Current System

### 2.1 What's Generic (the diamond)

These pieces implement a domain-agnostic orchestration pattern. They reference
no thesis concepts, no ML phases, no scientific invariants, no dataset paths.

| Component | Current Location | Function |
|-----------|-----------------|----------|
| DAG schema | `docs/templates/dag_template.yaml` | `jobs > task_groups > tasks` execution graph |
| Spec schema | `docs/templates/spec_template.md` | Per-task contract (objective/instructions/verification) |
| `/materialize_plan` | `.claude/commands/materialize_plan.md` | Plan → specs + DAG.yaml (mechanical extraction) |
| `/dag` | `.claude/commands/dag.md` | DAG executor (parse graph, dispatch agents, review gates) |
| `/pr` | `.claude/commands/pr.md` | PR wrap-up (checks, version bump, CHANGELOG, create PR) |
| Commit formatting | `.github/tmp/commit.txt` convention | Temp-file commit messages (avoids zsh heredoc breakage) |
| CHANGELOG automation | `CHANGELOG.md` `[Unreleased]` protocol | Keep-a-Changelog with automated version promotion |
| PR templating | `.github/tmp/pr.txt` convention | Human-reviewable PR body before creation |
| PR body template | `.github/pull_request_template.md` | Summary / Motivation / Test plan structure |
| Planning scaffold | `planning/{README.md, INDEX.md, dags/, specs/}` | Directory structure + lifecycle rules |
| `log-subagent.sh` | `scripts/hooks/log-subagent.sh` | Agent audit trail (session/start/stop/tokens) |
| `log-bash.sh` | `scripts/hooks/log-bash.sh` | Bash command audit trail |
| `guard-write-path.sh` | `scripts/hooks/guard-write-path.sh` | Write containment (repo/home/outside) |
| `guard-master-branch.sh` | `scripts/hooks/guard-master-branch.sh` | Block writes on master/main |
| `session_audit.py` | `scripts/session_audit.py` | Token/efficiency dashboard (sections 1-4, 6-7) |
| `find-session.sh` | `scripts/debug/find-session.sh` | Debug: locate session dirs and transcripts |

### 2.2 What's Thesis-Coupled (stays behind)

These pieces are deeply entangled with the MSc thesis domain and will NOT be
extracted. They remain in the thesis repo and plug into the framework via
configuration or extension points.

| Component | Why It Stays |
|-----------|-------------|
| Category A–F taxonomy | Thesis-specific work classification (Phase work, Thesis chapters) |
| `planner-science` agent | Thesis methodology planner (invariants, phases, datasets) |
| `reviewer-adversarial` agent (5 lenses) | Thesis examination prep (temporal discipline, defensibility) |
| `writer-thesis` agent | Thesis prose drafting (WRITING_STATUS.md, claim-evidence) |
| Scientific invariants (8 rules) | Domain-specific data discipline |
| Phase/Step/Pipeline Section hierarchy | 7-phase ML experiment lifecycle |
| Notebook workflow (sandbox/) | Thesis code execution environment |
| `lint-on-edit.sh` | Project-specific (calls `ruff` via `poetry`) — but the _hook pattern_ is generic |
| `check_phases_drift.py`, `check_mirror_drift.py` | Project-specific consistency checks |
| Plan template thesis fields | `dataset`, `phase`, `pipeline_section`, `invariants_touched`, `research_log_ref` |
| Critique template thesis sections | Invariant checks, temporal discipline, defensibility |
| Executor's Category A/F rules | Scientific invariant checks, notebook workflow, research log updates |
| Reviewer's notebook/thesis checks | Jupytext compliance, cell size limits, phase boundary checks |

### 2.3 Mixed Components (need surgery)

These have a generic skeleton wrapped in thesis-specific content. Extraction
means keeping the skeleton, parameterizing the thesis bits.

| Component | Generic Part | Thesis Part |
|-----------|-------------|-------------|
| `executor.md` | Dispatch protocol, spec-reading, parallel rules, worktree rules | Category A/F rules, notebook workflow, data layout, test mirror tree |
| `reviewer.md` | Output format, check-run protocol, read-only constraint | Notebook checks, thesis chapter checks, mirror-drift, ruff/mypy/pytest commands |
| `planner.md` | Read-only constraint, DAG requirement, output contract | ML codebase context, python-code rules, critique routing |
| Plan template | Structural contract (Scope, Steps, File Manifest, Gate, Execution Graph) | Thesis-specific frontmatter fields, literature context, category-conditional requirements |
| Critique template | Structural contract (risks, weaknesses, alternatives) | 8 invariant checks, temporal discipline, supervisor questions |
| `session_audit.py` | Token parsing, efficiency calc, model usage, subagent analysis | Hardcoded JSONL_DIR, AGENT_LOG, ERA_BOUNDARIES |
| `log-subagent.sh` | Session lifecycle, token aggregation from transcripts | Hardcoded model mapping (case statement) |
| CLAUDE.md rules | Plan/execute workflow, dispatch rules, materialization gate | Category table, phase work execution, scientific invariants |

---

## 3. Standalone Repo Architecture

### 3.1 Proposed Name

Working title: **`claude-dag`** (short, descriptive, available). User picks
final name.

### 3.2 Directory Structure

```
claude-dag/
├── Makefile                          # `make install` bootstraps into target repo
├── README.md
├── dagrc.schema.yaml                 # Config schema (for validation)
├── dagrc.example.yaml                # Annotated example config
│
├── core/                             # The orchestration protocol
│   ├── templates/
│   │   ├── dag_template.yaml         # DAG schema (generic)
│   │   ├── spec_template.md          # Spec schema (generic)
│   │   ├── plan_template.md          # Plan template (generic skeleton)
│   │   └── plan_critique_template.md # Critique template (generic skeleton)
│   │
│   ├── commands/                     # Claude Code slash commands
│   │   ├── dag.md                    # DAG executor
│   │   ├── materialize_plan.md       # Plan → specs + DAG
│   │   ├── pr.md                     # PR wrap-up (full delivery pipeline)
│   │   └── commit.md                 # Commit helper (optional standalone use)
│   │
│   ├── agents/                       # Generic agent definitions
│   │   ├── executor.md               # Implementation agent (generic)
│   │   ├── reviewer.md               # Lightweight review gate (generic)
│   │   ├── reviewer-deep.md          # Heavyweight review gate (generic)
│   │   ├── planner.md                # Code infrastructure planner (generic)
│   │   └── lookup.md                 # Quick Q&A agent (generic)
│   │
│   ├── rules/                        # CLAUDE.md injectable snippets
│   │   ├── dag-workflow.md           # Plan/execute/dispatch rules
│   │   └── delivery-workflow.md      # Commit/changelog/PR conventions
│   │
│   ├── delivery/                     # Delivery pipeline assets
│   │   ├── CHANGELOG_TEMPLATE.md     # Seed CHANGELOG with [Unreleased] headers
│   │   ├── pull_request_template.md  # PR body structure (Summary/Motivation/Test plan)
│   │   └── commit_conventions.md     # Conventional commit reference + temp-file protocol
│   │
│   └── scaffold/                     # Planning directory structure
│       ├── planning/
│       │   ├── README.md
│       │   ├── INDEX.md
│       │   ├── dags/
│       │   │   └── README.md
│       │   └── specs/
│       │       └── README.md
│       └── .github/
│           ├── tmp/.gitkeep          # Ephemeral commit/PR body staging area
│           └── pull_request_template.md
│
├── hooks/                            # Observability & safety hooks
│   ├── log-subagent.sh               # Agent session lifecycle + tokens
│   ├── log-bash.sh                   # Bash command audit trail
│   ├── guard-write-path.sh           # Write containment
│   ├── guard-master-branch.sh        # Block writes on protected branches
│   └── hooks.json                    # Settings.json hook fragment (copy-pasteable)
│
├── audit/                            # Observability dashboard & analytics
│   ├── __init__.py
│   ├── cli.py                        # `claude-dag audit` CLI entrypoint
│   ├── parsers/
│   │   ├── session_jsonl.py          # Parse Claude Code native JSONL
│   │   ├── agent_audit_log.py        # Parse agent-audit.log
│   │   └── bash_audit_log.py         # Parse bash-audit.log
│   ├── reports/
│   │   ├── daily_tokens.py           # Section 1: daily token usage
│   │   ├── efficiency.py             # Section 2: lines/K-output
│   │   ├── model_usage.py            # Section 3: per-model breakdown
│   │   ├── pr_history.py             # Section 4: PR volume
│   │   ├── era_analysis.py           # Section 5: configurable era comparison
│   │   ├── subagent_economics.py     # Section 6: per-agent-type token economics
│   │   ├── session_detail.py         # Section 7: per-session detail
│   │   ├── dag_execution.py          # NEW: per-DAG execution report
│   │   └── cost_model.py             # NEW: token-to-dollar mapping
│   ├── visualize/
│   │   ├── charts.py                 # matplotlib/plotly time-series, bar charts
│   │   ├── dag_timeline.py           # Gantt-style DAG execution timeline
│   │   └── comparison.py             # Pre/post era overlay plots
│   └── health/
│       ├── dag_success_rate.py        # DAG completion vs. halt rate
│       ├── review_gate_stats.py       # First-pass vs. retry rate per gate
│       ├── parallelism_ratio.py       # Actual vs. theoretical parallelism
│       └── autonomy_score.py          # Human interventions per DAG
│
├── debug/
│   └── find-session.sh               # Locate session dirs and transcripts
│
└── docs/
    ├── GETTING_STARTED.md
    ├── CONFIGURATION.md
    ├── DELIVERY_WORKFLOW.md          # Commit, changelog, PR conventions
    ├── OBSERVABILITY.md
    ├── ARCHITECTURE.md               # How the orchestration protocol works
    └── MIGRATION.md                  # Migrating from embedded to standalone
```

### 3.3 Configuration (`dagrc.yaml`)

Lives in the target repo root. The single source of truth for project-specific
behavior. The framework reads this at hook/script runtime and templates
reference it during materialization.

```yaml
# dagrc.yaml — Claude DAG Orchestration Configuration
project_name: "my-project"

# --- Log location ---
# Where audit logs are written. Default: ~/.claude-dag/logs/<project_name>/
# Can be relative (to repo root) or absolute.
log_dir: "~/.claude-dag/logs"

# --- Work categories ---
# Define your project's work taxonomy. At minimum: a name and branch prefix.
# critique_required: whether adversarial review is needed before materialization.
# read_before_planning: files agents must read before planning in this category.
categories:
  feature:
    branch_prefix: "feat/"
    critique_required: true
    read_before_planning:
      - "docs/ARCHITECTURE.md"
  refactor:
    branch_prefix: "refactor/"
    critique_required: true
    read_before_planning: []
  chore:
    branch_prefix: "chore/"
    critique_required: false
    read_before_planning: []
  bugfix:
    branch_prefix: "fix/"
    critique_required: false
    read_before_planning: []
  docs:
    branch_prefix: "docs/"
    critique_required: false
    read_before_planning: []

# --- Agent roster ---
# Map agent names to models. Agents not listed here use the default.
# The framework ships with: executor, reviewer, reviewer-deep, planner, lookup.
# You can add custom agents (e.g., writer-thesis) that extend the framework.
agents:
  executor:
    model: "sonnet"
    effort: "high"
  reviewer:
    model: "sonnet"
    effort: "high"
  reviewer-deep:
    model: "opus"
    effort: "high"
  planner:
    model: "sonnet"
    effort: "high"
    permission_mode: "plan"
  lookup:
    model: "haiku"
    effort: "low"

# --- Review gate defaults ---
# Which reviewer agent handles which file types.
review_gate:
  heavyweight_patterns: ["*.py", "*.ts", "*.rs", "*.go", "*.java", "*.sql"]
  heavyweight_agent: "reviewer-deep"
  lightweight_agent: "reviewer"
  on_blocker: "halt"

# --- Delivery workflow ---
# Covers the full commit → changelog → PR pipeline.

commit:
  # Temp-file protocol: write message to this path, then `git commit -F <path>`.
  # Avoids zsh heredoc breakage and gives Claude Code a reliable commit path.
  staging_file: ".github/tmp/commit.txt"
  # Conventional commit format: type(scope): description
  # The framework maps branch prefixes to types automatically.
  prefix_to_type:
    "feat/":      "feat"
    "refactor/":  "refactor"
    "chore/":     "chore"
    "fix/":       "fix"
    "docs/":      "docs"
    "test/":      "test"
  # Co-author line appended to every commit (set null to disable)
  co_author: "Claude <noreply@anthropic.com>"

changelog:
  # Path to CHANGELOG.md (relative to repo root)
  file: "CHANGELOG.md"
  # Format: "keep-a-changelog" (only supported format for now)
  format: "keep-a-changelog"
  # Section headers under [Unreleased]
  sections: ["Added", "Changed", "Fixed", "Removed"]
  # Version heading format. Placeholders: {version}, {date}, {pr_number}, {branch}
  version_heading: "[{version}] — {date} (PR #{pr_number}: {branch})"

pr:
  # Temp-file protocol: write PR body here for human review before creation.
  # Human reads it, approves/edits, then `gh pr create --body-file <path>`.
  staging_file: ".github/tmp/pr.txt"
  # PR body template sections
  body_sections:
    - "## Summary"        # 1-5 bullets, auto-generated from diff + commit log
    - "## Motivation"     # optional — include only when reason is non-obvious
    - "## Test plan"      # concrete steps: commands run, artifacts verified
  # Footer appended to every PR body
  footer: "Generated with [Claude Code](https://claude.com/claude-code)"
  # Cleanup: delete staging files after PR creation
  cleanup_after_create: true
  # Version bump configuration
  version_file: "pyproject.toml"         # or package.json, Cargo.toml, VERSION
  version_path: "tool.poetry.version"    # TOML path / JSON path to version string
  # Branch prefix → bump type mapping
  bump_rules:
    minor: ["feat/", "refactor/", "docs/"]
    patch: ["fix/", "test/", "chore/"]
  # Pre-PR checks (project-specific commands)
  checks: []                             # populated per-project, e.g.:
    # - "npm test"
    # - "cargo test"
    # - "source .venv/bin/activate && poetry run pytest tests/ -v --cov"
  coverage_threshold: null               # integer or null to skip

# --- Observability ---
observability:
  enabled: true
  # Era boundaries for pre/post analysis. Each era is a PR range + label.
  era_boundaries:
    - { pr_start: 1, pr_end: 50, label: "pre-dag" }
    - { pr_start: 51, pr_end: 51, label: "dag-rollout" }
    - { pr_start: 52, pr_end: 99999, label: "post-dag" }
  # Token-to-dollar cost model (per million tokens)
  cost_per_million:
    "claude-opus-4-6":     { input: 15.00, output: 75.00, cache_read: 1.88 }
    "claude-sonnet-4-6":   { input: 3.00,  output: 15.00, cache_read: 0.30 }
    "claude-haiku-4-5":    { input: 0.80,  output: 4.00,  cache_read: 0.08 }

# --- Protected branches ---
protected_branches: ["master", "main"]

# --- Custom plan frontmatter fields ---
# Additional YAML frontmatter fields for your plan template.
# These are project-specific extensions to the base plan schema.
custom_plan_fields: {}
  # Example for the thesis repo:
  # dataset: "sc2egset | aoe2companion | null"
  # phase: "NN matching docs/PHASES.md"
  # invariants_touched: "list of invariant IDs"
```

### 3.4 The `make install` Flow

```makefile
# Makefile — claude-dag framework installer
SHELL := /bin/bash
CLAUDE_DAG_ROOT := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

.PHONY: install uninstall status

install:
	@echo "Installing claude-dag into $(TARGET)..."
	@test -n "$(TARGET)" || (echo "Usage: make install TARGET=/path/to/repo" && exit 1)
	@test -d "$(TARGET)" || (echo "ERROR: $(TARGET) is not a directory" && exit 1)

	# 1. Create planning scaffold
	@mkdir -p $(TARGET)/planning/{dags,specs}
	@cp -n $(CLAUDE_DAG_ROOT)/core/scaffold/planning/README.md   $(TARGET)/planning/
	@cp -n $(CLAUDE_DAG_ROOT)/core/scaffold/planning/INDEX.md    $(TARGET)/planning/
	@cp -n $(CLAUDE_DAG_ROOT)/core/scaffold/planning/dags/README.md  $(TARGET)/planning/dags/
	@cp -n $(CLAUDE_DAG_ROOT)/core/scaffold/planning/specs/README.md $(TARGET)/planning/specs/

	# 2. Copy templates
	@mkdir -p $(TARGET)/docs/templates
	@cp $(CLAUDE_DAG_ROOT)/core/templates/* $(TARGET)/docs/templates/

	# 3. Install agent definitions (merge, don't overwrite)
	@mkdir -p $(TARGET)/.claude/agents
	@for f in $(CLAUDE_DAG_ROOT)/core/agents/*.md; do \
	  name=$$(basename $$f); \
	  if [ ! -f "$(TARGET)/.claude/agents/$$name" ]; then \
	    cp $$f $(TARGET)/.claude/agents/; \
	    echo "  + agent: $$name"; \
	  else \
	    echo "  ~ agent: $$name (exists, skipped)"; \
	  fi; \
	done

	# 4. Install slash commands
	@mkdir -p $(TARGET)/.claude/commands
	@cp $(CLAUDE_DAG_ROOT)/core/commands/* $(TARGET)/.claude/commands/
	@echo "  + commands: dag.md, materialize_plan.md, pr.md, commit.md"

	# 4b. Install delivery workflow assets
	@mkdir -p $(TARGET)/.github/tmp
	@touch $(TARGET)/.github/tmp/.gitkeep
	@if [ ! -f "$(TARGET)/.github/pull_request_template.md" ]; then \
	  cp $(CLAUDE_DAG_ROOT)/core/delivery/pull_request_template.md $(TARGET)/.github/; \
	  echo "  + .github/pull_request_template.md"; \
	else \
	  echo "  ~ .github/pull_request_template.md (exists, skipped)"; \
	fi
	@if [ ! -f "$(TARGET)/CHANGELOG.md" ]; then \
	  cp $(CLAUDE_DAG_ROOT)/core/delivery/CHANGELOG_TEMPLATE.md $(TARGET)/CHANGELOG.md; \
	  echo "  + CHANGELOG.md (seeded from template)"; \
	else \
	  echo "  ~ CHANGELOG.md (exists, skipped)"; \
	fi
	@# Add .github/tmp/* to .gitignore (commit.txt and pr.txt are ephemeral)
	@if [ -f "$(TARGET)/.gitignore" ]; then \
	  grep -qF '.github/tmp/' $(TARGET)/.gitignore || \
	    echo '.github/tmp/*' >> $(TARGET)/.gitignore && \
	    echo '!.github/tmp/.gitkeep' >> $(TARGET)/.gitignore; \
	fi

	# 5. Install hooks
	@mkdir -p $(TARGET)/scripts/hooks
	@cp $(CLAUDE_DAG_ROOT)/hooks/log-subagent.sh    $(TARGET)/scripts/hooks/
	@cp $(CLAUDE_DAG_ROOT)/hooks/log-bash.sh         $(TARGET)/scripts/hooks/
	@cp $(CLAUDE_DAG_ROOT)/hooks/guard-write-path.sh $(TARGET)/scripts/hooks/
	@cp $(CLAUDE_DAG_ROOT)/hooks/guard-master-branch.sh $(TARGET)/scripts/hooks/
	@chmod +x $(TARGET)/scripts/hooks/*.sh

	# 6. Install audit tools
	@mkdir -p $(TARGET)/scripts/audit
	@cp -r $(CLAUDE_DAG_ROOT)/audit/* $(TARGET)/scripts/audit/
	@mkdir -p $(TARGET)/scripts/debug
	@cp $(CLAUDE_DAG_ROOT)/debug/find-session.sh $(TARGET)/scripts/debug/
	@chmod +x $(TARGET)/scripts/debug/*.sh

	# 7. Seed dagrc.yaml if not present
	@if [ ! -f "$(TARGET)/dagrc.yaml" ]; then \
	  cp $(CLAUDE_DAG_ROOT)/dagrc.example.yaml $(TARGET)/dagrc.yaml; \
	  echo "  + dagrc.yaml (edit this to configure)"; \
	else \
	  echo "  ~ dagrc.yaml (exists, skipped)"; \
	fi

	# 8. Print post-install instructions
	@echo ""
	@echo "Done. Next steps:"
	@echo "  1. Edit $(TARGET)/dagrc.yaml"
	@echo "  2. Merge hooks from $(CLAUDE_DAG_ROOT)/hooks/hooks.json into $(TARGET)/.claude/settings.json"
	@echo "  3. Add dag-workflow rules to your CLAUDE.md (see core/rules/dag-workflow.md)"

status:
	@test -n "$(TARGET)" || (echo "Usage: make status TARGET=/path/to/repo" && exit 1)
	@echo "Framework files in $(TARGET):"
	@for f in planning/README.md planning/INDEX.md dagrc.yaml \
	          .claude/commands/dag.md .claude/commands/materialize_plan.md \
	          .claude/commands/pr.md .claude/commands/commit.md \
	          .claude/agents/executor.md scripts/hooks/log-subagent.sh \
	          scripts/audit/cli.py CHANGELOG.md .github/tmp/.gitkeep \
	          .github/pull_request_template.md; do \
	  [ -f "$(TARGET)/$$f" ] && echo "  OK  $$f" || echo "  MISSING $$f"; \
	done

uninstall:
	@echo "NOTE: uninstall only removes framework-owned files."
	@echo "dagrc.yaml, custom agents, and planning/ contents are preserved."
	@# (list specific files to remove — never rm -rf)
```

---

## 4. Component Extraction — Detailed Cuts

### 4.1 `/dag` Executor (`.claude/commands/dag.md`)

**Current state:** 111 lines. Already 95% generic.

**What changes:**
- Remove the implied "Category" concept from the summary report (line 88: 
  `DAG ID, branch, category`). Replace with generic metadata from DAG.yaml.
- The dispatch prompt format (lines 52-57) is already fully generic.
- Review gate protocol (lines 61-68) is already generic.
- Final review dispatch (lines 75-79) is already generic.
- Commit staging rule (lines 108-110) is already generic.

**Extraction effort:** Minimal — mostly copy + strip one line.

### 4.2 `/materialize_plan` (`.claude/commands/materialize_plan.md`)

**Current state:** 153 lines. ~85% generic.

**What changes:**
- Pre-flight step 4 (lines 42-48): category A/F critique check. Generalize to
  read `critique_required` from plan frontmatter without assuming A/F semantics.
  The generic version checks: "if `critique_required: true` in plan frontmatter,
  verify critique file exists."
- Step 5 commit message format (lines 126-129): already generic.
- Everything else is mechanical plan → spec extraction. Already generic.

**Extraction effort:** Small — one conditional to generalize.

### 4.3 Delivery Workflow (commit + changelog + PR)

The thesis repo solved three problems that every Claude Code project hits.
These get promoted from "buried inside `/pr`" to first-class framework
features with their own config, conventions, and documentation.

#### 4.3.1 Commit Formatting

**The problem solved:** zsh heredocs break with Claude Code. Multiline commit
messages via `git commit -m "$(cat <<'EOF' ... EOF)"` fail silently or
mangle content in zsh. The thesis repo discovered a reliable alternative:
write the message to a temp file, then `git commit -F <path>`.

**Current implementation:**
- Write message to `.github/tmp/commit.txt` (the Write tool, not echo/heredoc)
- `git commit -F .github/tmp/commit.txt`
- Delete after commit succeeds
- Used by both `/materialize_plan` (for materialization commits) and `/pr`
  (for release commits)

**What the framework provides:**
- `commit.staging_file` config in dagrc.yaml (default: `.github/tmp/commit.txt`)
- `commit.prefix_to_type` mapping: branch prefix → conventional commit type
- `commit.co_author` config for the `Co-Authored-By` trailer
- Optional `/commit` slash command for standalone use (outside DAG flow)
- The `delivery-workflow.md` CLAUDE.md rule snippet that teaches Claude Code
  the temp-file protocol

**Extraction effort:** Low — the convention is already generic. Just needs
config reads instead of hardcoded paths.

#### 4.3.2 CHANGELOG Automation

**The problem solved:** manual CHANGELOG maintenance is error-prone and gets
skipped. The thesis repo automates it: an `[Unreleased]` section accumulates
changes, and at PR time the `/pr` command promotes it to a versioned heading.

**Current implementation:**
- CHANGELOG.md follows Keep-a-Changelog format
- `[Unreleased]` section has four headers: Added, Changed, Fixed, Removed
- On version bump: contents move to `[X.Y.Z] — YYYY-MM-DD (PR #N: branch)]`
- `[Unreleased]` is left empty with the standard headers

**What the framework provides:**
- `changelog.file` config (default: `CHANGELOG.md`)
- `changelog.sections` config (customizable section headers)
- `changelog.version_heading` format string with placeholders
- A seed `CHANGELOG_TEMPLATE.md` that `make install` copies if no CHANGELOG
  exists
- The `/pr` command reads changelog config from dagrc.yaml instead of
  hardcoding the format

**Extraction effort:** Low — the format is already Keep-a-Changelog standard.
The heading format string is the only parameterization needed.

#### 4.3.3 PR Templating

**The problem solved:** PR bodies generated by Claude Code go directly to
GitHub with no human review. The thesis repo adds a staging step: write the
body to a temp file, let the human read and approve it, then create the PR.
This prevents "oops, wrong PR body" and gives veto power.

**Current implementation:**
- Write PR body to `.github/tmp/pr.txt` using the Write tool
- Tell the user: "PR body written — please review"
- User reads, approves (or edits)
- `gh pr create --body-file .github/tmp/pr.txt`
- Delete `.github/tmp/pr.txt` after creation
- PR body follows `.github/pull_request_template.md`: Summary, Motivation
  (optional), Test plan

**What the framework provides:**
- `pr.staging_file` config (default: `.github/tmp/pr.txt`)
- `pr.body_sections` config (customizable section list)
- `pr.footer` config (customizable footer line)
- `pr.cleanup_after_create` flag
- A seed `pull_request_template.md` that `make install` places in `.github/`
- The `.github/tmp/` directory is scaffolded with a `.gitkeep` (the directory
  must exist for the Write tool to succeed; the temp files themselves are
  gitignored)

**Extraction effort:** Low — already generic. Just needs config reads.

#### 4.3.4 `/pr` Command (the orchestrator)

**Current state:** 113 lines. ~70% generic.

The `/pr` command ties all three together into a single delivery pipeline:

```
checks → version bump → changelog promotion → release commit → PR body → PR create → cleanup
```

**What changes for the standalone repo:**
- Step 1 checks: reads `pr.checks` list from dagrc.yaml instead of hardcoding
  `ruff`, `mypy`, `pytest`
- Step 2 version bump: reads `pr.version_file`, `pr.version_path`, and
  `pr.bump_rules` from config instead of hardcoding `pyproject.toml` and
  branch prefix mapping
- Step 3 changelog: reads `changelog.*` config instead of hardcoding format
- Step 4 commit: reads `commit.*` config instead of hardcoding path
- Step 5/6 PR: reads `pr.*` config instead of hardcoding template/staging path
- Step 7 cleanup: reads `pr.cleanup_after_create` flag

**Extraction effort:** Medium — needs config reads for each step. The
structure is unchanged; only the hardcoded values become config lookups.

#### 4.3.5 Version Bump Strategy

**Current implementation:** The branch prefix determines the bump type:
- `feat/`, `refactor/`, `docs/` → minor bump
- `fix/`, `test/`, `chore/` → patch bump

**What the framework provides:**
- `pr.bump_rules` config: maps bump types (major/minor/patch) to lists of
  branch prefixes
- `pr.version_file` + `pr.version_path`: where to read/write the version
- Support for multiple version file formats:
  - TOML (`pyproject.toml` via `tool.poetry.version` or `project.version`)
  - JSON (`package.json` via `version`)
  - Plain text (`VERSION` file)
  - TOML with Cargo conventions (`Cargo.toml` via `package.version`)
- The bump is always proposed to the user for confirmation — never automatic

### 4.4 Executor Agent (`executor.md`)

**Current state:** 144 lines. ~50% generic.

**Generic skeleton (keep):**
- Lines 21-30: Dispatch protocol (spec-first, plan fallback)
- Lines 35-40: Constraints (execute only specified steps, verify, no PRs)
- Lines 42-55: Parallel execution rules (no git ops, worktree rules)
- Lines 109-120: "Read first" protocol (spec → echo back → execute)

**Thesis-specific (remove):**
- Lines 56-66: Test placement rules (mirror tree, `src/rts_predict/` paths)
- Lines 68-80: Category A/F rules (invariants, research log, temporal discipline, thesis writing)
- Lines 82-107: Notebook workflow (sandbox/, jupytext, nbconvert)
- Lines 122-140: Data layout reference (SC2, AoE2 datasets)

**Extraction strategy:** The generic executor keeps the dispatch/parallel/spec
protocol. Projects add their own rules via a `## Project-specific rules`
section in the installed copy, or via a separate rules file that the executor
reads. The `dagrc.yaml` can point to project-specific executor extensions:

```yaml
agents:
  executor:
    model: "sonnet"
    extensions:
      - ".claude/rules/python-code.md"    # project-specific
      - ".claude/rules/notebook-workflow.md"
```

### 4.5 Reviewer Agent (`reviewer.md`)

**Current state:** 95 lines. ~40% generic.

**Generic skeleton:**
- Output format template (lines 74-86)
- Read-only constraint (line 88)
- Specificity requirement (line 89)

**Thesis-specific (remove):**
- Lines 23-38: Code checks (ruff, mypy, pytest, mirror-drift, diff-coverage —
  all project-specific commands)
- Lines 40-62: Notebook checks (template compliance, jupytext, cell size)
- Lines 63-70: Thesis chapter checks

**Extraction strategy:** The generic reviewer runs whatever checks are
configured in `dagrc.yaml` under `pr.checks`, then reads the diff and
evaluates it. Project-specific review criteria (notebook compliance, thesis
prose rules) are extensions added by the project.

### 4.6 Planner Agent (`planner.md`)

**Current state:** 38 lines. ~70% generic.

**Generic:** Read-only constraint, DAG requirement, max 20 steps, output contract.

**Thesis-specific:** "Python project architect for an ML thesis codebase
(Poetry, pytest, ruff, mypy, DuckDB)" identity; critique routing per category.

**Extraction strategy:** Generic planner is a "project architect" — language
and tooling are read from project context, not hardcoded in the agent def.

### 4.7 Plan Template (`plan_template.md`)

**Current state:** 249 lines of YAML frontmatter + markdown sections.

**Generic skeleton (keep):**
- Frontmatter: `category`, `branch`, `date`, `planner_model`, `critique_required`
- Sections: Scope, Execution Steps (T01–TNN rigid structure), File Manifest,
  Gate Condition, Out of scope, Open questions, Suggested Execution Graph

**Thesis-specific (remove from generic, add via `custom_plan_fields`):**
- Frontmatter: `dataset`, `phase`, `pipeline_section`, `invariants_touched`,
  `source_artifacts`, `research_log_ref`
- Sections: Problem Statement (required for A/F — becomes configurable),
  Assumptions & unknowns, Literature context

### 4.8 Audit Scripts

**`session_audit.py`** — 845 lines, the big one.

**Extraction strategy:** Decompose the monolith into modular report sections
under `audit/reports/`. Each section becomes its own file with a standard
interface (`def run(config, sessions, filters) -> str`). The CLI assembles
sections based on flags.

**What gets parameterized:**
- `JSONL_DIR` → derived from project name + Claude Code's path encoding
- `AGENT_LOG` → read from `dagrc.yaml` `log_dir`
- `ERA_BOUNDARIES` → read from `dagrc.yaml` `observability.era_boundaries`
- Model mapping in `log-subagent.sh` → read from `dagrc.yaml` `agents`

**`log-subagent.sh`** — 103 lines.

**What changes:** The hardcoded `case` statement (lines 20-29) for model lookup
becomes a config-driven lookup. Options:
1. Read `dagrc.yaml` at hook runtime (needs `yq` dependency — not ideal)
2. Generate a `.claude-dag/model-map.sh` during `make install` from dagrc.yaml
3. Pass model via Claude Code's hook payload (if available — check API)

Option 2 is cleanest: `make install` reads dagrc.yaml, writes a shell-sourceable
model map, hook sources it at runtime.

---

## 5. New Observability Features

These don't exist yet. They're the reason the standalone repo is worth building
— the thesis repo's audit system has major gaps for answering "are DAGs
actually better?"

### 5.1 DAG Execution Logger

**Problem:** When `/dag` runs, the execution trace is ephemeral (in the
conversation transcript). No persistent record of which DAGs were executed,
which groups passed/failed, which review gates blocked.

**Solution:** The `/dag` command writes a structured execution log after each
task group and at completion:

```
~/.claude-dag/logs/<project>/dag-executions.jsonl
```

Each line is a JSON object:

```json
{
  "timestamp": "2026-04-12T10:30:00Z",
  "dag_id": "dag_01_research_log_split",
  "session_id": "abc-123",
  "event": "group_complete",    // or "dag_start", "dag_complete", "gate_block", "dag_halt"
  "group_id": "TG01",
  "tasks_dispatched": 3,
  "tasks_completed": 3,
  "review_gate": "APPROVE",
  "wall_clock_seconds": 245,
  "agents_spawned": ["executor", "executor", "executor", "reviewer"]
}
```

**What this enables:**
- DAG completion rate (complete vs. halted)
- Average tasks per DAG
- Review gate pass rate (first-try vs. retry)
- Wall-clock time per task group

### 5.2 Per-Task Token Tracking

**Problem:** `log-subagent.sh` logs tokens per agent but has no concept of
which DAG task the agent was executing. You can see "executor used 13K output
tokens" but not "T03 (the complex one) used 13K while T01 and T02 used 2K each."

**Solution:** Extend the `/dag` command's dispatch prompt to include the
`task_id` in a structured way that hooks can extract. The hook already receives
`agent_id` — correlate it with the DAG execution log to map agent → task.

Alternatively, the `/dag` command itself writes per-task token summaries by
reading the agent's transcript JSONL after it completes (the same technique
`log-subagent.sh` already uses).

### 5.3 Cost Model

**Problem:** Token counts exist but nobody knows what they cost in dollars.
Different models have wildly different per-token prices.

**Solution:** `audit/reports/cost_model.py` reads the `cost_per_million` table
from `dagrc.yaml` and annotates every report with dollar amounts:

```
## Daily Cost
| Date       | Opus ($) | Sonnet ($) | Haiku ($) | Total ($) |
|------------|----------|------------|-----------|-----------|
| 2026-04-11 | $12.40   | $3.20      | $0.05     | $15.65    |
| 2026-04-12 | $8.90    | $5.10      | $0.02     | $14.02    |
```

And per-PR cost:
```
## Cost per PR
| PR  | Branch                  | Opus ($) | Sonnet ($) | Total ($) | $/Line |
|-----|-------------------------|----------|------------|-----------|--------|
| 110 | chore/research-log-split| $18.30   | $7.20      | $25.50    | $0.08  |
```

### 5.4 Visualization

**Problem:** All current output is markdown tables and one ASCII bar chart.
No time-series, no trends, no visual comparison of eras.

**Solution:** `audit/visualize/` generates charts (matplotlib or plotly) and
saves them as PNG/HTML. The CLI supports `--charts` to generate visual reports.

Proposed charts:
1. **Token usage over time** — stacked area chart (input/output/cache by day)
2. **Efficiency trend** — lines changed per K-output tokens over time
3. **Cost trend** — daily spend by model (stacked bar)
4. **DAG execution timeline** — Gantt chart: each task group as a bar, color-
   coded by agent type, showing parallelism
5. **Era comparison** — side-by-side metrics (pre-DAG vs post-DAG):
   tokens/PR, lines/PR, cost/PR, time/PR
6. **Agent token share** — pie/donut chart replacing the ASCII bar
7. **Review gate heatmap** — pass/fail rate by group position (do later groups
   fail more often?)

### 5.5 Health Checks

**Problem:** No aggregate metrics on DAG system health. Is it working? Is it
getting better? Is it worth the overhead?

**Solution:** `audit/health/` computes health metrics:

| Metric | Formula | Healthy | Concerning |
|--------|---------|---------|------------|
| DAG completion rate | completed / (completed + halted) | > 80% | < 60% |
| First-pass gate rate | gates passed on first try / total gates | > 70% | < 50% |
| Parallelism ratio | sum(agent durations) / wall-clock elapsed | > 1.5 | ≈ 1.0 |
| Autonomy score | DAGs with 0 human interventions / total DAGs | > 50% | < 20% |
| Cache efficiency | cache_read / total_input per session | > 60% | < 30% |
| Cost per line | total $ / total lines changed (post-DAG era) | baseline | > 2x baseline |

### 5.6 DAG vs. Direct Interaction Comparison

**The key question the user wants answered:** are DAGs actually better than
just talking to Claude directly?

**Metrics framework:**

```
claude-dag audit --compare-eras
```

Output:
```
## Era Comparison: pre-DAG vs post-DAG

| Metric                    | pre-DAG (PRs 1-106) | post-DAG (PRs 108+) | Change  |
|---------------------------|---------------------|---------------------|---------|
| Avg lines changed / PR    | 142                 | 287                 | +102%   |
| Avg output tokens / PR    | 45,000              | 62,000              | +38%    |
| Lines / K-output tokens   | 3.16                | 4.63                | +47%    |
| Est. cost / PR             | $8.20               | $14.50              | +77%    |
| Est. cost / line           | $0.058              | $0.051              | -12%    |
| Review gate first-pass %  | n/a                 | 78%                 | —       |
| Avg agents / PR            | 1.2                 | 4.8                 | +300%   |
```

This is the "was it worth it" dashboard. Lines/K-output (token efficiency)
and cost/line (dollar efficiency) are the key metrics. If post-DAG has higher
lines/K-output and lower cost/line, the DAG system is paying for itself.

---

## 6. Migration Strategy

### Phase 0: Repo Setup (day 1)

1. Create `claude-dag` repo on GitHub
2. Initialize with the directory structure from §3.2
3. Copy generic components from thesis repo (the §2.1 table)
4. First commit: raw extraction, no modifications

### Phase 1: Decouple (week 1)

For each mixed component (§2.3), perform the surgery:

1. **Executor agent:** Strip thesis rules (Category A/F, notebooks, data layout).
   Keep dispatch protocol, parallel rules, spec-reading. Add extension point
   for project-specific rules.
2. **Reviewer agent:** Strip project-specific checks (ruff/mypy/pytest,
   notebooks, thesis). Keep output format and read-only constraint. Add
   config-driven check list.
3. **Planner agent:** Strip ML thesis identity. Keep DAG requirement and
   output contract.
4. **Plan template:** Strip thesis frontmatter fields. Keep structural
   contract. Add `custom_plan_fields` extension mechanism.
5. **Critique template:** Strip 8 invariant checks. Keep structural skeleton
   (risks, weaknesses, alternatives).
6. **`session_audit.py`:** Decompose into modular sections. Parameterize
   JSONL_DIR, AGENT_LOG, ERA_BOUNDARIES.
7. **`log-subagent.sh`:** Replace hardcoded model map with generated config.
8. **CLAUDE.md rules:** Extract Plan/Execute/Dispatch rules into a standalone
   `dag-workflow.md` snippet. Strip category table and phase references.
9. **Delivery workflow:** Extract commit/changelog/PR conventions into:
   - `delivery-workflow.md` CLAUDE.md rule snippet
   - `commit.md` optional slash command
   - Config-driven `/pr` command reading from dagrc.yaml
   - Seed templates: `CHANGELOG_TEMPLATE.md`, `pull_request_template.md`,
     `commit_conventions.md`

### Phase 2: Harden (week 2)

1. Add `dagrc.yaml` config parsing and validation
2. Build `make install` / `make status` / `make uninstall`
3. Write `hooks.json` fragment for easy settings.json integration
4. Add the `dag-workflow.md` injectable CLAUDE.md snippet
5. Write documentation: GETTING_STARTED, CONFIGURATION, ARCHITECTURE
6. Test: install into a fresh repo, run a plan/materialize/execute cycle

### Phase 3: Observability (week 2-3)

1. Build DAG execution logger (§5.1)
2. Build per-task token tracking (§5.2)
3. Build cost model (§5.3)
4. Build visualization (§5.4)
5. Build health checks (§5.5)
6. Build era comparison dashboard (§5.6)
7. Write OBSERVABILITY.md docs

### Phase 4: Re-integration (when ready)

When the standalone repo is production-ready, the thesis repo can re-adopt it:

1. Run `make install TARGET=/path/to/rts-outcome-prediction`
2. The generic agents/commands/hooks overwrite the embedded copies
3. Thesis-specific extensions stay in the thesis repo:
   - `planner-science.md`, `reviewer-adversarial.md`, `writer-thesis.md`
   - `.claude/rules/python-code.md`, `thesis-writing.md`
   - Executor extensions for Category A/F rules, notebook workflow
4. `dagrc.yaml` configures the thesis project's categories (A–F), model
   assignments, review gate defaults, era boundaries
5. The audit dashboard uses the standalone scripts instead of the embedded
   `session_audit.py`

The thesis repo's CLAUDE.md gets shorter: the Plan/Execute/Dispatch rules
section becomes a one-liner: "See `core/rules/dag-workflow.md` for orchestration
protocol" or is replaced by the installed snippet.

---

## 7. Key Design Decisions

### 7.1 Copy-based, not symlink/submodule

`make install` copies files into the target repo. No fragile symlinks, no
git submodule pain. Trade-off: updates require re-running `make install`.
Mitigation: `make status` shows which files are outdated by comparing checksums.

### 7.2 `dagrc.yaml` over environment variables

A single YAML config beats scattered env vars. It's version-controlled,
self-documenting, and supports complex structures (category taxonomy, cost
model). Tools that need it at runtime (hooks, audit scripts) can read it
with `yq` or a tiny Python parser.

### 7.3 Stdlib-only Python for audit tools

The current `session_audit.py` is stdlib-only (no pip dependencies). The
standalone repo should maintain this for the core parsers and reports.
Visualization (`matplotlib`/`plotly`) is an optional extra — the CLI works
without it and falls back to ASCII/markdown tables.

### 7.4 Extension points over configuration bloat

Instead of trying to configure every possible project variation in dagrc.yaml,
the framework provides extension points:
- Agents can reference project-specific rule files
- The plan template supports `custom_plan_fields`
- The reviewer runs project-configured checks
- The executor reads project-specific rule files listed in dagrc.yaml

This keeps the core framework small and avoids the "1000-line config" antipattern.

### 7.5 Delivery workflow is not optional

The commit/changelog/PR pipeline ships as a core framework feature, not an
add-on. Rationale: every project that uses DAG orchestration eventually needs
to ship the results. The conventions are battle-tested (the thesis repo has
used them across 110+ PRs), and they solve real problems:

- **Commit temp file:** zsh heredoc breakage is a universal Claude Code issue.
  The temp-file protocol is the only reliable cross-shell approach discovered
  so far. Every user will hit this.
- **CHANGELOG automation:** without it, changelogs drift or get skipped
  entirely. The `[Unreleased]` promotion pattern is mechanical — no reason
  for humans to do it manually.
- **PR staging:** Claude Code generating a PR body and immediately pushing it
  to GitHub is a footgun. The staging step (write to file → human reviews →
  then create) prevents embarrassment and gives the human a clean veto point.

Projects can disable or customize each piece via dagrc.yaml, but the defaults
are opinionated: temp-file commits, Keep-a-Changelog, staged PR bodies.

### 7.6 Non-destructive migration

The thesis repo is never modified by the extraction process. The standalone
repo is built from clean copies. Re-integration is opt-in and reversible
(`make install` only overwrites framework-owned files, preserving custom agents
and project rules).

---

## 8. Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Over-engineering the config system | Delays shipping | Start with minimal dagrc.yaml. Add fields when real users need them. |
| Hooks need `yq` dependency | Friction on install | Generate shell-sourceable config during `make install`, avoid runtime YAML parsing in hooks. |
| Visualization scope creep | Never ships | Ship text-only first. Charts are Phase 3 — nice to have, not blocking. |
| Claude Code hook API changes | Breaks hooks | Pin to documented hook payload fields. Test against current Claude Code version. |
| Agent definitions drift between repos | Maintenance burden | `make status` shows checksums. Consider semantic versioning for agent defs. |
| dagrc.yaml becomes another CLAUDE.md | Config duplication | dagrc.yaml is for framework config only. Project conventions stay in CLAUDE.md. Clear boundary. |
| Session JSONL path encoding changes | Breaks audit parsers | Claude Code encodes paths as `slashes-to-dashes`. If this changes, one function in `parsers/session_jsonl.py` needs updating. |

---

## 9. Open Questions

1. **Name:** `claude-dag`? `cc-orchestrator`? `dagpilot`? Something else?
2. **License:** MIT? Apache 2.0?
3. **Distribution:** Makefile only? Or also a `pip install claude-dag` that
   provides a `claude-dag init` CLI?
4. **Hook payload:** Does Claude Code's hook payload include enough info to
   correlate agent → DAG task without the DAG executor writing its own log?
   (Probably not — the executor needs to log.)
5. **Multi-DAG support:** Should the framework support multiple simultaneous
   active DAGs? (The thesis repo uses one at a time. Multi-DAG is more
   complex but might be needed for monorepos.)
6. **Settings.json merging:** `make install` can't safely merge hooks into an
   existing `settings.json`. Options: (a) print instructions, (b) provide a
   merge script, (c) use `jq` to merge.
7. **Commit command scope:** Should `/commit` be a standalone slash command
   (useful outside DAG flow for manual commits) or just an internal protocol
   used by `/materialize_plan` and `/pr`? The thesis repo uses it as an
   internal protocol only. Standalone use adds value for any Claude Code project.
8. **CHANGELOG format extensibility:** Keep-a-Changelog is the only supported
   format. Should the framework support other formats (e.g., conventional-
   changelog, GitHub releases only, no changelog)? Start with one, add later.
9. **Version file auto-detection:** Should `make install` auto-detect the
   version file format (`pyproject.toml` vs `package.json` vs `Cargo.toml`)
   and pre-populate dagrc.yaml? Nice for onboarding.

---

## 10. First Steps

If you approve this plan, the immediate next actions are:

1. Create the `claude-dag` repo with the directory structure from §3.2
2. Copy the generic components (§2.1 table) — raw, unmodified
3. Perform the surgery on mixed components (§4.1–4.8)
4. Extract delivery workflow (§4.3): commit conventions, CHANGELOG template,
   PR template, `/commit` command, config-driven `/pr` command
5. Write `dagrc.example.yaml` and the Makefile
6. Test: install into a fresh repo, run the full lifecycle:
   plan → materialize → execute → commit → changelog → PR
7. Circle back to observability (§5) once the core is solid
