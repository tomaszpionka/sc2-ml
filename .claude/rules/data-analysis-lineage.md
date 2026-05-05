# Data analysis lineage and anti-GIGO guardrail

A generated artifact is not evidence unless the notebook's assumptions, falsifiers, and sanity checks were reviewed before artifact generation.

This rule prevents a common data-science failure mode:

plan -> notebook -> artifact -> next step

without stopping to ask whether the notebook actually measures what it claims to measure. A formally complete ROADMAP -> notebook -> artifact -> research_log -> STEP_STATUS chain can still be GIGO if the assumptions, falsifiers, and sanity checks were not reviewed before artifact generation.

## Agent and model routing discipline

The parent Claude session may act as an Opus orchestrator, but it should not automatically perform every implementation step itself.

Use agent/model routing deliberately:

- Use `@planner-science` for data-science planning, methodology design, feature-engineering design, temporal-leakage protocol design, and cross-game comparability decisions. This agent is Opus and read-only.
- Use `@executor` for routine implementation tasks, documentation edits, mechanical file creation, validation reports, and bounded plan steps. This agent defaults to Sonnet.
- Use `@executor` on Sonnet when the task is mechanically specified and the plan already resolves the scientific/methodological decisions.
- Use Opus execution, or switch `/model opus` before continuing, when the implementation step itself requires subtle reasoning about temporal leakage, source semantics, data-generating process, SQL window semantics, tracker-event interpretation, cold-start gates, or thesis-facing methodological claims.
- Use `@reviewer` for ordinary post-change validation, tests, lint/type checks, mechanical scope checks, and first-pass review.
- Use `@reviewer-deep` for high-stakes multi-spec changes, methodology audits, scientific findings that will enter the thesis record, cross-cutting feature-engineering contracts, or any change where structural correctness matters more than speed. Reviewer-deep covers structural correctness, spec compliance, and invariant tracing.
- Use `@reviewer-adversarial` for methodology defensibility checks when the active plan requires it, when reviewer-deep raises an unresolved methodology BLOCKER, before Phase 03+ methodology-sensitive work, before thesis chapters that report quantitative findings, or whenever a methodology choice may not survive examination. Reviewer-adversarial covers scientific defensibility — should-this-design-exist and will-this-survive-examination.
- For this active Phase 02 readiness PR, do not invoke reviewer-adversarial unless the plan is amended or reviewer-deep raises a BLOCKER requiring adversarial methodology review.

Do not over-delegate. If a step depends on live context from the parent session, a single-file mechanical edit may be safer in the parent session. If a step is large, mechanical, or parallelizable with non-overlapping file scope, delegate it to `@executor`.

Do not under-delegate. The parent Opus session should not silently batch many routine edits when an `@executor` checkpoint would preserve clearer scope boundaries.

For every delegated execution step, the parent must specify:

- exact task ID;
- allowed files;
- forbidden files;
- stop condition;
- required validation report;
- whether Sonnet executor is sufficient or Opus execution is required.

## Non-batching rule for empirical work

Do not batch ROADMAP + notebook + artifact + next Step in one execution.

Each empirical Step must follow this sequence:

1. ROADMAP stub only.
2. Notebook scaffold + one validation module.
3. Execute and report.
4. User review.
5. Commit.
6. Next validation module.
7. Only after all validation modules pass, generate artifacts.
8. Then research_log / STEP_STATUS / manifest.
9. Then reviewer-deep.

If any result is surprising, halt before artifact generation.

## Required structure for every empirical analysis

Every empirical analysis must declare before execution:

- the assumption being tested;
- the measurement claim;
- the sanity check;
- the falsifier;
- the expected artifact or report;
- the lineage source;
- the downstream decision that depends on the result.

If the falsifier fails, halt and report. Do not generate downstream artifacts, update research_log, update STEP_STATUS, or proceed to the next Step until the failure is reviewed.

## Artifact discipline

Generated artifacts must be produced only through their upstream notebook or script lineage.

Do not manually patch generated artifacts.

If a notebook, script, SQL view, schema assumption, source filter, or semantic interpretation changes after an artifact is produced, the artifact is stale until regenerated through the canonical lineage.

A generated artifact may be cited as evidence only after:

1. the upstream notebook/script assumptions were reviewed;
2. the sanity checks passed;
3. the falsifier did not fail;
4. the artifact was generated from the reviewed notebook/script;
5. the lineage was recorded in the appropriate research_log / STEP_STATUS / manifest path.

## Notebook discipline

Do not create a full empirical notebook in the same execution that creates the ROADMAP entry for that Step.

The first notebook pass should be a scaffold plus one validation module only. Do not use the first pass to generate all final artifacts.

Notebook execution reports must summarize:

- what was measured;
- what was not measured;
- what assumptions remain unvalidated;
- whether the result supports, narrows, or blocks the intended downstream feature family;
- whether any surprising result requires halting before artifact generation.

## Feature-engineering discipline

Feature-engineering contracts and protocols may define planned feature families, grains, prediction settings, and leakage checks.

They must not silently execute feature generation.

Feature-generation notebooks require explicit user approval after the relevant contract/spec step is reviewed.

Every feature family must declare:

- dataset;
- source table/event family;
- prediction setting;
- feature table grain;
- temporal anchor;
- allowed cutoff rule;
- leakage falsifier;
- cold-start behavior;
- lineage artifact.

## Temporal leakage discipline

History features must use only records where:

history_time < target_time

In-game snapshot features must use only events where:

event.loop <= cutoff_loop

Tracker-derived SC2 features are never pre-game features.

Any feature using a post-outcome value, full-replay aggregate, target-game final state, or rolling window that includes the target game is leakage unless an explicit, reviewed exception is documented.

## SC2 tracker-event discipline

SC2 tracker-derived features are constrained by:

src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/tracker_events_feature_eligibility.csv

Only rows marked eligible_for_phase02_now or eligible_with_caveat may be used in initial Phase 02 feature engineering, and only under each row's eligibility_scope and caveat.

Blocked tracker families must remain excluded until a future dedicated validation Step resolves the blocking reason.

The full tracker_events_raw semantic scope is narrowed, not closed.

## AoE2 source-label discipline

AoE2 feature engineering must preserve source-specific labels:

- aoestats is Tier 4 semantic opacity and must not be called unqualified ranked ladder.
- aoe2companion ID 6 is rm_1v1 ranked candidate.
- aoe2companion ID 18 is qp_rm_1v1 quickplay/matchmaking-derived.
- aoe2companion ID 6 + ID 18 is mixed-mode and must not be called ranked-only.

## Stop conditions

Halt before artifact generation if:

- the notebook assumption is unreviewed;
- the falsifier fails;
- the sanity check produces a surprising result;
- a temporal cutoff is ambiguous;
- source semantics are unclear;
- a feature family lacks grain or prediction setting;
- a generated artifact would encode an unvalidated interpretation;
- the next Step would start before the current Step has a reviewed checkpoint commit.

Halt before delegating if:

- the task lacks exact allowed files;
- the task lacks exact forbidden files;
- the task lacks a stop condition;
- the task does not specify whether Sonnet executor is sufficient or Opus execution is required;
- the task would allow an executor to batch ROADMAP + notebook + artifact + next Step.
