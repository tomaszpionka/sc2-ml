❯ in @LATER.md there is a suggestion to to decentralize research logs - one per each dataset. IMO it makes sense, and the root reports log should be actually only pointer the 3 independent dataset researches  
  - what do you think about it? let it sink and go hard on it                                                                                                                                                    
  ⎿  Read LATER.md (14 lines)
  ⎿  ⧉ Selected 1 lines from .claude/agents/reviewer.md in Visual Studio Code

⏺ This is a good question that deserves proper analysis. Let me explore what exists today before proposing anything.

⏺ Explore(Research log structure and references)
  ⎿  Done (21 tool uses · 48.7k tokens · 1m 6s)
  (ctrl+o to expand)

⏺ This is worth going deep on because the research log is referenced in 30+ files across the entire project and the decision compounds with every future entry. Let me lay out the full analysis.

  ---
  Why Decentralization Is Right

  The research log is the only reporting artifact that doesn't follow the per-dataset pattern. Everything else is already isolated:

  ┌──────────────────────────────┬─────────────────────────────────────────────────┐
  │           Artifact           │                  Per-dataset?                   │
  ├──────────────────────────────┼─────────────────────────────────────────────────┤
  │ ROADMAP.md                   │ Yes — src/rts_predict/<game>/reports/<dataset>/ │
  ├──────────────────────────────┼─────────────────────────────────────────────────┤
  │ PHASE_STATUS.yaml            │ Yes                                             │
  ├──────────────────────────────┼─────────────────────────────────────────────────┤
  │ PIPELINE_SECTION_STATUS.yaml │ Yes                                             │
  ├──────────────────────────────┼─────────────────────────────────────────────────┤
  │ STEP_STATUS.yaml             │ Yes                                             │
  ├──────────────────────────────┼─────────────────────────────────────────────────┤
  │ artifacts/                   │ Yes                                             │
  ├──────────────────────────────┼─────────────────────────────────────────────────┤
  │ research_log.md              │ No — single file at reports/                    │
  └──────────────────────────────┴─────────────────────────────────────────────────┘

  This is an anomaly. The architecture doc calls it "cross-cutting" but the reality is: 90% of entries are dataset-specific. Entry 2 (file inventory) covers all 3 datasets but the findings are dataset-specific
   (SC2: 22,390 files, aoe2companion: 4,154, aoestats: 349). These are three observations, not one.

  The scale problem is coming. You have 3 datasets, 7 phases, and multiple steps per phase. By Phase 03, the unified log will have 50+ entries. An executor working on SC2 Phase 03 would need to scan through
  AoE2 entries to find relevant SC2 context. Per-dataset logs eliminate that noise.

  Agent scope narrows naturally. When an executor reads the SC2 research log, it gets only SC2 findings — better context, less attention waste. When reviewer-deep checks for contradictions, it reads the
  relevant dataset's log, not all 3.

  Parallel execution safety. Two executors working on SC2 and AoE2 simultaneously won't conflict on the same file.

  ---
  Proposed Design

  reports/
  └── research_log.md              ← INDEX + CROSS entries only

  src/rts_predict/sc2/reports/sc2egset/
  ├── research_log.md              ← SC2 findings
  ├── ROADMAP.md
  ├── PHASE_STATUS.yaml
  ├── STEP_STATUS.yaml
  ├── artifacts/
  └── ...

  src/rts_predict/aoe2/reports/aoe2companion/
  ├── research_log.md              ← aoe2companion findings
  ├── ...

  src/rts_predict/aoe2/reports/aoestats/
  ├── research_log.md              ← aoestats findings
  ├── ...

  Root log (reports/research_log.md)

  Becomes a thin index + cross-game findings:

  # Research Log — Master Index

  ## Dataset Logs
  - [SC2 / sc2egset](../src/rts_predict/sc2/reports/sc2egset/research_log.md)
  - [AoE2 / aoe2companion](../src/rts_predict/aoe2/reports/aoe2companion/research_log.md)
  - [AoE2 / aoestats](../src/rts_predict/aoe2/reports/aoestats/research_log.md)

  ## Cross-Game Entries
  <Only entries tagged [CROSS] — methodology decisions affecting all datasets,
  cross-game comparison findings, shared protocol decisions.>

  Per-dataset logs

  Same entry template, same schema, same reverse-chronological order. The dataset: field becomes redundant within the file but stays for machine-readability and consistency.

  Where things go
  ┌────────────────────────────────────────────────────┬─────────────────────────────────┐
  │                    Finding type                    │          Log location           │
  ├────────────────────────────────────────────────────┼─────────────────────────────────┤
  │ SC2 file inventory                                 │ sc2egset/research_log.md        │
  ├────────────────────────────────────────────────────┼─────────────────────────────────┤
  │ AoE2 companion schema discovery                    │ aoe2companion/research_log.md   │
  ├────────────────────────────────────────────────────┼─────────────────────────────────┤
  │ "Use expanding windows for all datasets"           │ reports/research_log.md [CROSS] │
  ├────────────────────────────────────────────────────┼─────────────────────────────────┤
  │ "SC2 data has 2-second gaps"                       │ sc2egset/research_log.md        │
  ├────────────────────────────────────────────────────┼─────────────────────────────────┤
  │ Phase 06 cross-game comparison results             │ reports/research_log.md [CROSS] │
  ├────────────────────────────────────────────────────┼─────────────────────────────────┤
  │ "aoe2companion is primary, aoestats is validation" │ reports/research_log.md [CROSS] │
  └────────────────────────────────────────────────────┴─────────────────────────────────┘

  ---
  What Needs Updating

  This is the real cost. Around 30 references across:

  - CLAUDE.md — "update reports/research_log.md" → "update the active dataset's research_log.md"
  - executor.md — same pattern, already knows the active dataset from PHASE_STATUS.yaml
  - reviewer-deep.md — reads "recent entries" → reads the relevant dataset's log
  - reviewer-adversarial.md — same
  - planner-science.md — "check research_log for sibling dataset decisions" → check root CROSS log
  - reviewer.md — verify entry exists → verify in the right dataset log
  - ARCHITECTURE.md — cross-cutting files table needs updating
  - docs/INDEX.md, docs/TAXONOMY.md, PHASES.md, STEPS.md — reference updates
  - research_log_template.yaml — add variant for root index vs per-dataset
  - git-workflow.md — end-of-session checklist

  The references mostly follow the same pattern: change reports/research_log.md to a path that resolves from the active dataset context. The executor already knows which dataset it's working on (from
  PHASE_STATUS.yaml), so the resolution is natural.

  ---
  Migration of Existing Entries

  Only 2 entries exist today:

  Entry 1 ([CROSS] AoE2 Dataset Strategy Decision) → stays in root as a CROSS entry. This is genuinely cross-dataset — it's about the relationship between aoe2companion and aoestats.

  Entry 2 ([Phase 01 / Step 01_01_01] File Inventory) → split into 3 entries, one per dataset. Each gets the dataset-specific findings (file counts, sizes, gaps). The shared methodology ("ran file inventory
  across all 3") stays as a brief note in each.

  ---
  Timing

  LATER.md says "Do not touch until SC2EGSet Phase 1 closes." But this is a strategic infrastructure decision that affects every future entry. The longer you wait, the more entries need splitting. With only 2
  entries today, migration is trivial. After Phase 01 completes (10+ entries per dataset), it's a real project.

  My recommendation: Do it as a separate Category C chore on its own branch, before Phase 01 Step 01_01_02. The template rewrite (current branch) and the research log split are independent — they can run in
  parallel or sequentially.

  ---
  Risk: Invariant #8 compliance

  The one real risk: cross-game findings getting lost in per-dataset logs. If someone logs "expanding windows show leakage in SC2" in the SC2 log but doesn't check whether the same applies to AoE2, Invariant
  #8 is violated silently.

  Mitigation: The root CROSS log becomes the place where cross-game implications are recorded. The planner-science agent already has a multi-dataset coordination rule — update it to say: "After recording a
  finding in a dataset log, check whether it has cross-game implications. If yes, add a CROSS entry to the root log."

  ---
  What's your take? If you want to proceed, this would be a separate plan/branch (chore/research-log-split or similar). I can draft it in a planning session.


✻ Brewed for 3m 11s

❯ write this all down to: @research_log_decentralization.md                                                                                                                                                      
  ⎿  Read research_log_decentralization.md (1 lines)         
                                                                                                                                                                                                                 
  Read 1 file (ctrl+o to expand)                                                                                                                                                                                 
                                                       
⏺ Write(research_log_decentralization.md)                                                                                                                                                                        
  ⎿  Wrote 256 lines to research_log_decentralization.md                                                                                                                                                         
       1 # Research Log Decentralization: Design Proposal                                                                                                                                                        
       2                                                                                                                                                                                                         
       3 **Date:** 2026-04-12                                                                                                                                                                                    
       4 **Category:** C (chore) — infrastructure                                                                                                                                                                
       5 **Status:** Proposal (not yet planned or approved)                                                                                                                                                      
       6 **Triggered by:** LATER.md item "Per-dataset research log split"                                                                                                                                        
       7                                                                                                                                                                                                         
       8 ---                                                                                                                                                                                                     
       9
      10 ## 1. Problem Statement
     … +246 lines (ctrl+o to expand)

⏺ Done. Written to research_log_decentralization.md — full proposal with 8 sections covering the design, migration, reference updates, Invariant #8 risk mitigation, and timing recommendation.