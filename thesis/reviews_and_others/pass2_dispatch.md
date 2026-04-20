# Pass-2 dispatch prompt — thesis Chapter 1–4 review findings

**Audience:** Claude Code planner-science Opus running locally in the `rts-outcome-prediction` repo.
**Purpose:** Route the findings from the Claude Chat Pass-2 review (combined internal-consistency pass + web-research verification) to executor agents through the standard Category-F thesis-writing workflow.
**Input artifact:** The two-part review delivered in chat, reproduced inline in Appendix A and Appendix B of this document.
**Your role:** Plan. Do not execute. Produce `planning/current_plan.md` + `planning/current_plan.critique.md` per the two-layer template. Dispatch to executor agents one task group at a time with halt-and-review gates between groups.

---

## 0. Pre-flight — before planning

Before producing any plan, confirm the following by reading the sources of truth yourself:

1. Read `.claude/scientific-invariants.md` (all invariants). Note which invariants each finding interacts with.
2. Read `docs/TAXONOMY.md` and `docs/PHASES.md` to confirm the vocabulary used below matches canon (Phase / Pipeline Section / Step; dataset-scoped not game-scoped).
3. Read `docs/THESIS_WRITING_MANUAL.md` §§ on citation format, reference style, Polish academic register, and the `[REVIEW:]` flag convention.
4. Read `thesis/chapters/REVIEW_QUEUE.md` to see the current Pass-2 pending list and understand how this dispatch integrates with the existing queue.
5. Read `thesis/WRITING_STATUS.md` to understand current section statuses.

If any of the findings below contradict a higher tier of the Sources-of-Truth hierarchy, **flag it rather than paper over it** — escalate to the user before dispatching.

---

## 1. Scope, constraints, and discipline

### 1.1 What this dispatch covers

- Corrections to `thesis/chapters/01_introduction.md` (§1.1, §1.2, §1.3, §1.4 as drafted).
- Corrections to `thesis/chapters/02_theoretical_background.md` (all drafted subsections).
- Corrections to `thesis/chapters/03_related_work.md` (all drafted subsections).
- Corrections to `thesis/chapters/04_data_and_methodology.md` (§4.1 drafted subsections and §4.4.4 / §4.4.5 / §4.4.6 drafted subsections — other §4.x subsections remain BLOCKED).
- Corrections to `thesis/references.bib` (eight bib entries need material edits; one needs deletion).
- Updates to `thesis/WRITING_STATUS.md` and `thesis/chapters/REVIEW_QUEUE.md` to reflect post-Pass-2 state.
- Updates to `thesis/THESIS_STRUCTURE.md` (one inconsistency).

### 1.2 What this dispatch does NOT cover

- Any new empirical claims (forbidden — invariant #6: no claim without a notebook).
- Any thesis prose for sections still BLOCKED (Chapter 5, 6, 7; §4.2 beyond the three drafted subsections; §4.3; rest of §4.4).
- Any modification of Phase 01 artifacts (invariant #9: raw data + ledger immutability). If a Phase 01 ledger is inconsistent with the thesis prose, the thesis prose is what changes, not the ledger. One exception: if a ledger contains an outright factual error identified during Pass 2, escalate as Category-D backlog item.

### 1.3 Binding discipline for this plan

- **Sequential PR execution**, not parallel. One task group per PR. Halt-and-review between groups.
- **Scope-gate on critique**: `science` scope → full five-section critique; `code` scope → reduced critique; `chore` scope → skip critique.
- **Polish register** for all thesis prose — impersonal academic Polish, reference-style `[AuthorYear]` citations, no first-person.
- **No claim without traceability.** Each correction either (i) cites the verified primary source from Appendix B below, or (ii) is a pure internal-consistency fix with repo-local anchor.
- **Plant `[REVIEW:]` flags** for any correction that cannot be fully resolved without information the executor agent does not yet have.
- **Do not silently paper over contradictions.** If two sources of truth disagree (e.g., WRITING_STATUS vs. actual draft; THESIS_STRUCTURE vs. what chapter actually does), flag the contradiction and escalate before choosing.

---

## 2. Findings to route (priority-ordered)

Findings are organized in six task groups. Task groups 1–4 are P0/P1 substantive corrections requiring `science` scope. Task groups 5–6 are P2/P3 hygiene and unresolved flags requiring `chore` or mixed scope.

### Task Group 1 — BLOCKER: Methodological commitment drift (§1.2 ↔ §2.6 ↔ §4.4.4)

**Severity:** Blocker. Directly violates project instruction §4.4 ("do not hard-commit to a post-hoc method yet") and contradicts `user_memories` (Dimitriadis triptych was explicitly de-committed as the adopted evaluation framework).

**Findings:**

- **F1.1 — Dimitriadis triptych drift.** §1.2 paragraph 1 hedges the triptych as "potencjalną ramę ewaluacyjną […] zostanie rozważone". §2.6.2 and §2.6.5 then present it as the adopted framework. §4.4.4 silently substitutes ECE + reliability curves for the triptych it claims to use. Three-way inconsistency.
- **F1.2 — Friedman + Wilcoxon-Holm + Bayesian signed-rank hard-commit.** §4.4.4 commits to all three in one sentence. §2.6.3 commits to Wilcoxon-Holm as "aktualnie rekomendowany protokół" and to Bayesian signed-rank with fixed ROPE = ±0.01. Project instruction §4.4 forbids this premature commitment.

**Required actions:**

- Rewrite §1.2 paragraph 1 to present the triptych as **one** candidate diagnostic framework, explicitly flagging that the final evaluation framework will be fixed in the methodology chapter after experiment design.
- Rewrite §2.6 to reframe: Nemenyi's limitations are to be **noted** per Benavoli et al. 2016; Wilcoxon-Holm, Bayesian signed-rank, and 5×2 cv F-test are to be presented as **candidate alternatives** whose final selection awaits experiment design. ROPE width should not be fixed.
- Rewrite §4.4.4 to either (i) genuinely commit to the triptych and ECE drops out, or (ii) present ECE + reliability diagrams as the operational diagnostic and note the triptych as an alternative full-diagnostic framework. Cannot silently substitute.
- Keep all three sections mutually consistent after rewrite.

**Scope:** science. **Critique:** full five-section. **PR boundary:** single PR; do not mix with any other task group.

---

### Task Group 2 — BLOCKER: Within-chapter factual contradictions

**Findings:**

- **F2.1 — §4.1.1 temporal coverage contradicts itself.** §4.1.1.1 paragraph 2 states SC2EGSet coverage 2016-01-07 → 2024-12-01. §4.1.1.2 last paragraph states "SC2EGSet rozciąga się na lata 2016–2022". Second statement is wrong; corpus is v2.1.0 covering through 2024. Verify against `01_02_04_univariate_census.md` for `details.timeUTC` range, then correct the §4.1.1.2 phrasing.

- **F2.2 — AoE2 Mountain Royals release date.** Thesis currently implies May 2024; correct release is **31 October 2023**. Find every occurrence in §2.3 and §4.1.2 and correct.

- **F2.3 — AoE2 ranked civilization count is window-dependent.** The "45 civilizations" figure is correct only for Nov 2023 – 5 May 2025. After Three Kingdoms DLC (6 May 2025) = 50. After Last Chieftains (17 Feb 2026) = 53. Locate the corpus cutoff date for aoestats and aoe2companion in the Phase 01 artifacts (likely `01_01_01_file_inventory.md` or `01_02_04_univariate_census.md`), then state the civilization count **conditional on that cutoff** in §1.1, §2.3, §2.3.2, §3.4.2, §4.1.2. If the cutoff spans multiple DLC windows, write the count as a range with a footnote explaining the DLC boundaries.

**Scope:** science (requires artifact cross-checks). **Critique:** full five-section. **PR boundary:** single PR.

---

### Task Group 3 — BLOCKER: Luka 3 narrowing (RQ3 defensibility against EsportsBench)

**Severity:** Blocker for the thesis contribution argument. Without narrowing, a reviewer can argue Thorrez 2024 largely pre-empts the RQ3 contribution.

**Threat:** EsportsBench (Thorrez 2024) overlaps the RQ3 gap on 3 of 5 criteria: ≥2 RTS games (SC1, SC2, WC3), pre-game features only, 1v1 format. Fails on: probabilistic-metric scope (log loss only; no Brier, no reliability, no ECE) and method scope (rating systems only; no feature-based ML classifiers).

**Required actions (per the three-part amendment specified in the review):**

- Rewrite Luka 3 in §3.5 to insert three specifiers:
  1. "feature-based ML classifiers (beyond paired-comparison rating systems and their Bayesian/Kalman variants)"
  2. "Brier score, log loss, reliability diagrams, AND ECE reported jointly"
  3. Explicit acknowledgement of Thorrez (2024) as closest prior art, with distinguishing criteria enumerated.
- Propagate the narrowed framing to RQ3 in §1.3 and to §6.3 (Generalisability — currently BLOCKED, but add a forward-ref comment so the wording lands when §6.3 is drafted).
- Add a new reference-card-style paragraph in §3.2.3 (or a new §3.2.5) positioning Thorrez 2024 as a 3-RTS rating-system benchmark, with log-loss-only evaluation, and noting the distinction from the present thesis.

- **Residual risk to guard against:** if the eventual methodology uses Elo/TrueSkill outputs as stacked features for ML classifiers, this MUST be stated explicitly in §4.4, otherwise the "beyond rating systems" distinction erodes.

**Scope:** science. **Critique:** full five-section. **PR boundary:** single PR.

---

### Task Group 4 — P0: Bibliography material corrections + Elbert 2025 integration

**Findings (all P0; each is a substantive factual error or missing high-profile citation):**

- **F4.1 — A1: García-Méndez & de Arriba-Pérez 2025 target game is CS:GO, not Dota 2.** Correct §1.1 wherever `GarciaMendez2025` is cited; confirm with ScienceDirect DOI 10.1016/j.entcom.2025.101027 and arXiv:2510.19671. Also correct the "streaming" framing — it refers to stream-based incremental ML (Apache Kafka/Spark prequential validation), not livestream broadcast.

- **F4.2 — A9: Hodge et al. 2021 author list is wrong.** Current bib has "Hodge, V. J. and Sherkat, Sam and Sherkat, Ehsan and others". Correct: **Victoria J. Hodge, Sam Devlin, Nick Sephton, Florian Block, Peter I. Cowling, Anders Drachen.** Replace entirely. Also soften architecture claim from "LightGBM architecture" to "LR/RF/LightGBM comparison, RF deployed live." Affects §1.1 and §3.3.1.

- **F4.3 — A10: Bunker et al. 2024 dataset scope is wrong.** Thesis currently says "2020–2024 Grand Slam tournaments." Correct: **ATP tennis 2005–2020, all levels, 14 test years 2007–2020.** Correct in §3.1.3. Volume/issue/pages: Proc. IMechE Part P, 238(4), 305–316, DOI 10.1177/17543371231212235.

- **F4.4 — A3: SC-Phi2 MDPI page range is wrong.** Current: 2444–2462. Correct: **2338–2352.** Also delete the duplicated `Tarassoli2024` bib entry (it is a misattribution of the same paper; `user_memories` flagged this as already-known; pending since). Verify no citing location remains that uses `Tarassoli2024`.

- **F4.5 — A15: Aligulac ~80% claim is a misreading.** The 80% describes **calibration** ("actual winrate close to predicted winrate up to about 80%"), not classification accuracy. Reframe §2.2.3 and §2.5.4 to (i) state what the FAQ actually claims, and (ii) cite Thorrez 2024's 80.13% Glicko-2 on Aligulac SC2 data as the closest academic proxy.

- **F4.6 — Elbert et al. 2025 integration.** This 2025 ACM EC paper (arXiv:2506.04475, DOI 10.1145/3736252.3742618) is a high-profile AoE2 match-prediction paper. The thesis already cites it in §3.4.3 and §3.5 but should strengthen the differentiation:
  - API-level aggregates (aoe2insights.com, 1,623,828 team matches) vs. replay-parsing (out of scope per §1.4).
  - Team matches 2v2/3v3/4v4 only for outcome-prediction task vs. 1v1 in this thesis.
  - Pseudo-R² (0.0744 S1.3; 0.1004 S2.4) + accuracy only — no Brier, no reliability, no ECE.
  - Author list: Nico Elbert, Alicia von Schenk, Fabian Kosse, Victor Klockmann, Nikolai Stein, Christoph Flath. Fix any `Stein, Nora` to `Stein, Nikolai`. Verify all first names in current bib entry.

- **F4.7 — A2: EsportsBench citation form.** No arXiv ID exists; venue is author-hosted preprint. Current bib `@misc` with "year=2024" is acceptable but underspecified — add `howpublished={Preprint (under review)}` and the author-hosted URL. Also clarify in §2.5.5 and §3.2.4 that 411,030 is the **train subset**, not total (test ≈ 22,343; total ≈ 433,373).

- **F4.8 — A7: Baek & Kim 2022 88.6% attribution.** Currently implied as Q4-specific; actually full-game 50-frame-sampled input. Q1–Q2 < 60% stands. Fix phrasing in §3.2.3.

- **F4.9 — A14: Glickman 1995 replacement.** Replace `Glickman1995` (American Chess Journal) as the canonical reference for Glicko with:
  - **Glicko:** Glickman 1999, JRSS-C, 48(3), 377–394, DOI 10.1111/1467-9876.00159 (already in bib as `Glickman1999`).
  - **Glicko-2:** Glickman 2001, JAS, 28(6), 673–689, DOI 10.1080/02664760120059219 (already in bib as `Glickman2001`).
  - Retain ACJ citation only as pedagogical supplement if needed; do not use as primary source.

- **F4.10 — A6: Lin et al. 2024 TMLR gap framing nuance.** The paper DOES evaluate composition-level strength-relation classification (BT 64.5% test, NCT M=81 75.4% test on AoE2). Current thesis framing "does NOT benchmark ML classifiers for match-outcome prediction" is too strong. Rewrite §3.4.2 and §3.5 Luka 3 framing to: "does NOT benchmark **per-match classifiers with individual-match pre-game features**" — carving out composition-level Bradley-Terry as a different task scope.

- **F4.11 — A4: Çetin Taş & Müngen 2023 unverified claims.** IEEE Xplore PDF not retrieved during Pass 2. User must retrieve through PJAIT subscription and verify: (i) ~86% accuracy figure, (ii) NB+DT classifier set vs. the title's "Regression Analysis", (iii) validation protocol. Keep a `[REVIEW: verify from primary source]` flag on §3.4.1 until resolved. This is ALREADY flagged in current §3.4 [REVIEW:] list — reinforce.

**Scope:** science for F4.1–F4.6 and F4.10 (content corrections); chore for F4.7–F4.9 (bibliographic hygiene); chore for F4.11 (flag maintenance).

**PR boundary:** Split into two PRs:
  - **PR-4a (science):** F4.1, F4.2, F4.3, F4.4, F4.5, F4.6, F4.10 — prose rewrites with citation impact.
  - **PR-4b (chore):** F4.7, F4.8, F4.9, F4.11 — bibliographic hygiene and flag maintenance.

---

### Task Group 5 — HIGH: Internal-consistency fixes flagged during the review

**Findings:**

- **F5.1 — WRITING_STATUS.md drift for §1.1.** Current entry says "0 [REVIEW] flags" but the §1.1 draft has three `[REVIEW:]` tags (GarciaMendez2025, Shin1993/Forrest2005 sports-market generalization, Mangat2024). Update WRITING_STATUS entry and add §1.1 to REVIEW_QUEUE Pending table with explicit flag enumeration.

- **F5.2 — THESIS_STRUCTURE.md Chapter 1 feed attribution.** Current footer says "Fed by: Background reading, literature review. No roadmap phase directly." But §1.2's data-asymmetry framing references the Phase 01 cross-corpus finding from Tabela 4.4b. Update footer to acknowledge Phase 01 characterization as a motivational feed (not as empirical findings; Chapter 1 remains literature/framing).

- **F5.3 — §2.2.3 vs. §2.5.4 Aligulac 80% inconsistency.** §2.5.4 has a [REVIEW] flag on the 80% claim; §2.2.3 states it as fact without flag. Same claim, same source; the flag belongs on both instances or neither. Apply the reframing from F4.5 to both locations consistently.

- **F5.4 — §4.1.3 "Ramy okna referencyjnego" circular justification.** The paragraph defends asymmetric reference windows by citing spec §7, but spec §7 was authored by the same team. Rewrite to either (i) substantively argue why patch-regime homogeneity dominates window-length comparability in ICC estimation (cite literature), or (ii) concede it's a judgment call and add a sensitivity-axis acknowledgement.

- **F5.5 — §3.4.3 and §3.3.5 framing reconciliation.** Elbert 2025 appears in §3.4 (AoE2-specific) but not in §3.3 (MOBA + other esports team-game predictors). Check whether Elbert belongs also in §3.3 as an AoE2-team-games data point, or whether the §3.4 placement is correct. Decision criterion: if §3.3 covers team games across MOBA/FPS, Elbert fits there too; if §3.3 is strictly MOBA, leave in §3.4. Document the decision in the prose.

- **F5.6 — §4.4.4 Demsar §3.2 corollary citation.** The N ≥ 10 recommendation for Friedman is in **Demsar 2006 §3.1.3 (The Friedman test)**, not §3.2 (which is about Holm post-hoc for pairwise-with-control). Correct the citation.

**Scope:** chore (F5.1, F5.2, F5.3, F5.5, F5.6); science (F5.4 — methodology defence).

**PR boundary:** Two PRs.
  - **PR-5a (chore):** F5.1, F5.2, F5.3, F5.5, F5.6 — hygiene.
  - **PR-5b (science):** F5.4 — methodological defence rewrite.

---

### Task Group 6 — MEDIUM/LOW: Prophylactic hedges and low-priority fixes

**Findings:**

- **F6.1 — Luka 1 prophylactic strengthening.** Even though Luka 1 survives, the contribution statement can be strengthened by explicitly naming the 2024–2026 papers that cover multi-family classifiers without probabilistic metrics (Brookhouse & Buckley 2025; Caldeira et al. 2025; Alhumaid & Tur 2025; Minami et al. 2024; García-Méndez & de Arriba-Pérez 2025) and the one with single-model calibration (Ferraz et al. 2025). Update §3.5 Luka 1 paragraph accordingly.

- **F6.2 — Luka 2 prophylactic hedge.** Tighten §3.5 Luka 2 to: "no prior peer-reviewed or preprint study on AoE2 outcome prediction reports SHAP (or equivalent additive feature-attribution) analysis combined with leave-one-category-out ablation over pre-game feature groups." Explicitly distinguish Elbert et al. 2025's econometric residualization from SHAP.

- **F6.3 — Luka 4 cold-start disambiguation.** Add footnote to §3.5 Luka 4: García-Méndez & de Arriba-Pérez 2025 use "cold start" for classifier warm-up phase, not player match-history length. Reinforce that no esports prediction paper stratifies accuracy by player history length.

- **F6.4 — §2.2.4 Vinyals 2017 for 22.4 loops/sec.** SC2LE explicitly states "22.4 (at 'fast speed') times per second." Replace the Liquipedia grey-literature citation with SC2LE (Vinyals et al. 2017) for this specific figure. Keep Liquipedia (or s2protocol README) only as a footnote for the 5734/4096 fixed-point constant.

- **F6.5 — §2.2.4 s2protocol 2.0.8 confirmation.** Tracker events in 2.0.8 confirmed against Blizzard/s2protocol README (*"Tracker events are new in version 2.0.8"*) and StarCraft II patch notes (Patch 2.0.8 released 7 May 2013). Add parenthetical date if thesis currently omits it.

- **F6.6 — §2.5 and §3.2.4 EsportsBench dataset versioning.** HuggingFace has rolling versions v1.0–v7.0 through cutoff 2025-09-30 (schema-stable refreshes). Add a footnote acknowledging this and specifying which version the thesis relies on (if any) for any cited figure.

- **F6.7 — A8: Yang et al. 2017 protocol clarification.** Minor: mention the 9:1 split is **random**, not temporal, and note that the 58.69% baseline is Kinkade et al. reimplemented (Yang's own LR on hero features alone = 60.07%). Affects §3.3.1.

- **F6.8 — A11: Silva et al. 2018 pagination.** Add SBGames 2018 proceedings pages 639–642, ISSN 2179-2259. Update bib.

- **F6.9 — A12: Xie 2020 R² vs. accuracy flag.** Explicitly note in §3.4.4 (grey-literature paragraph) that Xie's <2% "linear regression accuracy" is almost certainly R² misreported as accuracy (evidence enumerated in review). Flag the terminological error in the prose rather than citing the figure uncritically.

- **F6.10 — A13: Porcpine 2020 venue correction.** Venue is **GitHub Pages** (porcpine1967.github.io/aoe2_comparisons/elo/), with code at github.com/porcpine1967/aoe2_comparisons. Update bib. Also note r = 0.96 is computed on aggregated win-percentages per rating-difference bin, which inflates correlation vs. raw binary match data.

- **F6.11 — Bib hygiene for Elbert2025 authors.** Verify the current bib entry `Elbert2025EC` matches the full verified author list: **Nico Elbert, Alicia von Schenk, Fabian Kosse, Victor Klockmann, Nikolai Stein, Christoph Flath.** Current bib has `Stein, Nora` — change to `Stein, Nikolai`.

- **F6.12 — Minor stylistic: `[REVIEW:]` typography.** L4 from the internal-consistency pass suggests standardizing `[REVIEW:]` flags as blockquotes to increase visibility in compiled output. Consider a consistent convention (e.g., `> [REVIEW: ...]`). This is optional — only adopt if it doesn't break existing tooling that parses flags.

**Scope:** chore for all F6.x items except F6.1–F6.3 (prophylactic prose strengthening → science-lite, document the rationale). 

**PR boundary:** Two PRs.
  - **PR-6a (science-lite):** F6.1, F6.2, F6.3 — gap-claim strengthening.
  - **PR-6b (chore):** F6.4–F6.12 — bibliographic hygiene and minor prose touch-ups.

---

## 3. Execution order and gates

Execute the six task groups sequentially in this order. Do not start a task group until the previous one has passed its reviewer gate and the halt-and-review discussion has concluded.

```
PR-1 (science, BLOCKER) → Task Group 1 — Methodological commitment drift
  ↓ halt, user review
PR-2 (science, BLOCKER) → Task Group 2 — Factual contradictions (temporal coverage, Mountain Royals, civ count)
  ↓ halt, user review
PR-3 (science, BLOCKER) → Task Group 3 — Luka 3 narrowing
  ↓ halt, user review
PR-4a (science, P0)     → Task Group 4, part 1 — prose+citation corrections (F4.1–F4.6, F4.10)
PR-4b (chore, P0)       → Task Group 4, part 2 — bib hygiene + flag maintenance (F4.7–F4.9, F4.11)
  ↓ halt, user review
PR-5a (chore, HIGH)     → Task Group 5, part 1 — internal-consistency hygiene (F5.1, F5.2, F5.3, F5.5, F5.6)
PR-5b (science, HIGH)   → Task Group 5, part 2 — methodological defence (F5.4)
  ↓ halt, user review
PR-6a (science-lite, P2)→ Task Group 6, part 1 — gap-claim strengthening (F6.1, F6.2, F6.3)
PR-6b (chore, P2)       → Task Group 6, part 2 — bib and minor prose (F6.4–F6.12)
  ↓ final review, update WRITING_STATUS + REVIEW_QUEUE
```

---

## 4. Planner output requirements

Produce these artifacts before dispatching any executor:

1. **`planning/current_plan.md`** — full DAG with one node per task group. Each node must specify:
   - Task group ID (TG1, TG2, etc.) and PR number.
   - Scope (`science` | `code` | `chore`).
   - Files touched (from the findings above).
   - Predecessor task groups (sequential, so this is trivial — TGn depends on TG(n-1)).
   - Executor agent (Sonnet thesis-writer).
   - Reviewer agent gate.
   - Acceptance criteria (enumerated from findings).
   - Verification artifacts (which source the executor must cite).

2. **`planning/current_plan.critique.md`** — adversarial critique of the plan itself. Required sections:
   - **Defensibility:** "Would this plan be defensible at an MSc exam?" — specifically, does it address the blocker items in the correct order?
   - **Known weaknesses:** What could fail? (e.g., F4.11 blocks on user retrieving a PDF; TG3 may require re-work if user retrieval changes Çetin Taş interpretation.)
   - **Alternatives considered:** Why split PR-4 and PR-5 as shown? Why not bundle?
   - **Escalation triggers:** What would cause the plan to halt mid-execution and return to planner?
   - **Invariant audit:** Which invariants (#1–#10) are most at risk of violation during execution? For each, name the mitigation.

3. **No executor dispatch until the user reviews both artifacts.** This is a hard gate.

---

## 5. Dispatch protocol per task group

For each task group, after planner artifacts are approved:

1. Executor agent reads `planning/current_plan.md` for the task group's scope.
2. Executor agent makes the edits, plants `[REVIEW:]` flags for anything not fully resolvable.
3. Executor agent updates `thesis/WRITING_STATUS.md` and `thesis/chapters/REVIEW_QUEUE.md` at the end of the PR.
4. Reviewer agent runs the Critical Review Checklist from `.claude/rules/thesis-writing.md`.
5. Reviewer agent produces an adversarial verdict: `PASS` | `REQUIRE_MINOR_REVISION` | `REQUIRE_SUBSTANTIAL_REVISION`.
6. If `REQUIRE_SUBSTANTIAL_REVISION`, return to planner with the verdict; do not proceed to next PR.
7. If `PASS` or `REQUIRE_MINOR_REVISION` (after revision), halt for user review before starting the next PR.

---

## 6. Non-negotiable invariants during execution

- **I1 (symmetry):** N/A — no experimental work in scope.
- **I2 (reproducibility):** Every primary-source citation must include DOI or arXiv ID or permanent URL. No "personal communication" or "data on file."
- **I3 (temporal discipline):** N/A — no feature engineering in scope.
- **I4 (target-row consistency):** N/A — no experimental work in scope.
- **I5 (focal/opponent randomization):** N/A — no experimental work in scope.
- **I6 (SQL shipped with findings):** N/A — no new empirical claims added. Corrections that reference Phase 01 findings must cite the artifact path (e.g., `01_02_04_univariate_census.md`), not re-derive the number.
- **I7 (no magic numbers):** All new numeric claims in prose must cite either (a) a Phase 01 artifact, or (b) a primary-source citation from Appendix B. No unanchored figures.
- **I8 (raw data + ledger immutability):** Do not modify `src/**/data/*/raw/**` or any Phase 01 artifact ledger. If a ledger error is discovered, escalate as Category-D backlog.
- **I9 (raw data immutability):** See I8.
- **I10 (prowenancja surowych tabel):** N/A — no ingestion work.

Additional project-level invariants (from the project instructions, not `.claude/scientific-invariants.md`):

- **Honesty clause:** Push back on any finding that seems structurally wrong. If the dispatch as written would violate an invariant, return to user.
- **No thesis prose without an experiment behind it.** This dispatch adds no new empirical claims; it corrects existing prose against verified primary sources. Confirm no scope creep.

---

## Appendix A — Pass-2 internal-consistency review (reproduced for agent context)

### Blockers

- **B1. §1.2 and §2.6 hard-commit to the Dimitriadis triptych.** §1.2 hedges ("zostanie rozważone"); §2.6.2 and §2.6.5 present as adopted ("pełny tryptyk diagnostyczny"); §4.4.4 substitutes ECE without discussion. Three-way drift. `user_memories` explicitly records triptych was de-committed.
- **B2. §4.4.4 hard-commits to Friedman + Wilcoxon-Holm + Bayesian signed-rank.** Direct violation of project instruction §4.4 ("do not hard-commit to a post-hoc method yet"). Even ROPE width (±0.01) is fixed.
- **B3. §3.5 Luka 3 "pierwsza znana nam praca" claim is hedged against four qualifiers simultaneously.** Each qualifier reduces the claim's value; an examiner will ask why all four must hold. Also: if post-2024 literature surfaces a paper satisfying all criteria, Luka 3 collapses. (Confirmed in Part B: narrowing is required against Thorrez 2024.)
- **B4. §4.1.1.1 says 2016–2024; §4.1.1.2 says 2016–2022.** Within-section contradiction.

### High-priority issues

- **H1.** WRITING_STATUS.md says §1.1 has 0 flags; draft has 3.
- **H2.** §2.2.3 and §2.5.4 both cite Aligulac 80% — §2.5 has [REVIEW] flag, §2.2 does not.
- **H3.** §4.4.4 cites Demsar §3.2 corollary; actual reference for N ≥ 10 is §3.1.3.
- **H4.** §4.1.3 reference-window justification is circular (defends spec by citing spec).
- **H5.** Elbert 2025 used in §3.3 and §3.4 without reconciliation between the two placements.

### Medium issues

- **M1.** THESIS_STRUCTURE.md Chapter 1 footer ("No roadmap phase directly") contradicts §1.2 use of Phase 01 asymmetry findings.
- **M2.** §2.5.5 cross-reference from §1.3 needs verification of subsection ID.
- **M3.** `Tarassoli2024` bib entry is misattributed and still present despite being flagged.
- **M4.** §4.4.5 Tabela 4.7 has `[UNVERIFIED:]` token in a rendered cell.
- **M5.** §3.1.3 Bunker 2024 "2020–2024 Grand Slam" date range not flagged (confirmed wrong in Part B — ATP 2005–2020).
- **M6.** §4.2.3 80% threshold defence has a bootstrap-circular feel.

### Low-priority / stylistic

- **L1–L4.** Stylistic polish (Vinyals 10^26 specifier; Zermelo 1929 attribution; inline tables for Elbert; `[REVIEW:]` blockquote convention).

---

## Appendix B — Pass-2 research verification (primary-source findings, reproduced for agent context)

### A1. García-Méndez & de Arriba-Pérez 2025 — CORRECTION NEEDED (target game)
- Target game: **CS:GO**, not Dota 2.
- Streaming = stream-based incremental ML, not livestream broadcast.
- Accuracy "higher than 90%"; exceeds Makarov et al. by 30.51pp, Hodge et al. by 15pp.
- Two authors only; DOI 10.1016/j.entcom.2025.101027; arXiv:2510.19671.

### A2. EsportsBench (Thorrez 2024) — PARTIAL CORRECTION
- No arXiv ID; author-hosted preprint, under review.
- Glicko-2 = **0.8013** accuracy on SC2 VERIFIED (log-loss 0.4135).
- 411,030 is train subset; test ≈ 22,343; total ≈ 433,373.
- HuggingFace dataset versions v1.0–v7.0 through 2025-09-30.

### A3. SC-Phi2 (Khan & Sukthankar 2024) — CORRECTION NEEDED
- Page range **2338–2352** (not 2444–2462). DOI 10.3390/ai5040115 correct; arXiv:2409.18989.
- Build-order accuracies Table 4: TvT 76.82, PvP 78.49, ZvZ 77.07, PvT 79.62, PvZ 80.37, TvZ 78.74.
- No standalone "global state prediction" accuracy.
- NO calibration metrics (no Brier, no ECE, no reliability).

### A4. Çetin Taş & Müngen 2023 — METADATA VERIFIED, METHOD CLAIMS UNVERIFIABLE
- DOI 10.1109/UBMK59864.2023.10391048 correct.
- Abstract confirms features include civilization/nationality and map.
- ~86% accuracy, NB+DT classifier set, validation protocol: UNVERIFIABLE without PJAIT IEEE access.

### A5. Elbert et al. 2025 — VERIFIED (with citation-form refinement)
- Authors: Elbert, **Alicia** von Schenk, Kosse, Klockmann, **Nikolai** Stein, Flath.
- Pseudo-R² = 0.0744 (S1.3, n=811,914) and 0.1004 (S2.4, n=710,817) VERIFIED.
- Team matches only (2v2/3v3/4v4) for outcome task; 1v1 used only to extract Solo Elo + eAPM features.
- aoe2insights.com; 14,000 focal players; 1,623,828 team matches.
- DOI 10.1145/3736252.3742618; ACM EC '25, p. 761; Stanford, 2 July 2025.

### A6. Lin et al. 2024 TMLR — VERIFIED with nuance
- TMLR OpenReview ID **2D36otXvBE**.
- AoE2 matches 1,261,288 from aoestats.io January 2024 VERIFIED.
- Paper DOES evaluate composition-level strength-relation classification (BT 64.5%, NCT M=81 75.4% test).
- Does NOT benchmark **per-match classifiers with individual-match features**.

### A7. Baek & Kim 2022 PLOS ONE — MOSTLY VERIFIED
- 88.6% is from **full-game 50-frame-sampled input** (Table 3), not Q4-specific.
- Q1–Q2 <60% VERIFIED.
- 1,725 replays (1,227 train + 498 test) VERIFIED.

### A8. Yang et al. 2017 arXiv:1701.03162 — FULLY VERIFIED
- 78,362 matches (20,631 with replay data) VERIFIED.
- 58.69% / 71.49% / 93.73% VERIFIED.
- Dota 2 VERIFIED. Split is random 9:1, not temporal.
- 58.69% baseline is Kinkade reimplemented; Yang's own LR on hero features = 60.07%.

### A9. Hodge et al. 2021 IEEE ToG — CRITICAL AUTHOR CORRECTION
- Correct authors: **Victoria J. Hodge, Sam Devlin, Nick Sephton, Florian Block, Peter I. Cowling, Anders Drachen.**
- Remove "Sherkat, Sam and Sherkat, Ehsan" — erroneous.
- IEEE Trans. Games 13(4), 368–379, DOI 10.1109/TG.2019.2948469.
- 85%-at-5-minutes is live ESL One Hamburg 2017 deployment (N=28).
- Soften architecture: LR/RF/LightGBM compared; RF deployed live.

### A10. Bunker et al. 2024 SAGE — SUBSTANTIVE CORRECTION
- Proc. IMechE Part P, 238(4), 305–316, DOI 10.1177/17543371231212235.
- Dataset: **ATP tennis 2005–2020, all levels**, not "2020–2024 Grand Slam."
- ADTrees + LR as only ML models beating Elo VERIFIED.

### A11. Silva et al. 2018 SBGames — FULLY VERIFIED
- Proceedings pages 639–642, ISSN 2179-2259.
- 7,621 matches 2015–2018 VERIFIED.
- Accuracy curve VERIFIED (63.91 / 68.69 / 75.23 / 80.18 / 83.54 across 5-min bins).
- Simple RNN > GRU > LSTM VERIFIED.

### A12. Xie 2020 Medium — GREY LIT; R² CONFUSION CONFIRMED
- 77% / 73% / 62% AUC figures verbatim.
- 205,317 Voobly matches VERIFIED.
- <2% linear regression "accuracy" is almost certainly **R²**, not accuracy (evidence: uses XBGRegression; 2% is impossible as accuracy for binary task; R² ≈ 0.02 plausible for binary targets with tight Elo distributions).

### A13. Porcpine 2020 — VENUE CORRECTED
- GitHub Pages: porcpine1967.github.io/aoe2_comparisons/elo/
- r = 0.96 is on aggregated bin data, not raw binary match data.
- 908,940 matches (= 913,201 total − 4,261 contradicted).

### A14. Glickman 1995 — CANONICAL CITATION REPLACEMENT
- Use Glickman 1999 JRSS-C 48(3), 377–394 for Glicko.
- Use Glickman 2001 JAS 28(6), 673–689 for Glicko-2.
- ACJ manuscript only as pedagogical.

### A15. Aligulac 80% — MISREADING CONFIRMED
- FAQ describes **calibration** ("actual winrate close to predicted winrate up to about 80%"), not classification accuracy.
- No direct academic validation of Aligulac's bespoke algorithm.
- Thorrez 2024's 80.13% Glicko-2 is closest academic proxy.

### A16. SC2 22.4 loops/sec — PEER-REVIEWED REPLACEMENT
- Vinyals et al. 2017 SC2LE explicitly states "22.4 (at 'fast speed') times per second."
- Use Vinyals for the 22.4 figure; Liquipedia/s2protocol README only for 5734/4096 constant.

### A17. Tracker events in s2protocol 2.0.8 — VERIFIED
- Blizzard/s2protocol README: "Tracker events are new in version 2.0.8."
- Patch 2.0.8 released 7 May 2013 (first post-HotS patch).

### A18. AoE2:DE civilization count — CORRECTIONS
- Mountain Royals released **31 Oct 2023**, not May 2024.
- 45 civs correct for Nov 2023 – 5 May 2025.
- Three Kingdoms (6 May 2025) adds 5 ranked → 50.
- Last Chieftains (17 Feb 2026) adds 3 ranked → 53.
- Chronicles DLCs (Battle for Greece Nov 2024; Alexander the Great Oct 2025) are NOT ranked — handle correctly.

### Part B — Adversarial sweep verdicts
- **Luka 1 (multi-family + probabilistic):** SURVIVES. 2024–2026 pattern is accuracy+AUC only.
- **Luka 2 (SHAP + ablation on AoE2):** SURVIVES. Requires prophylactic tightening.
- **Luka 3 (cross-RTS pre-game 1v1 probabilistic):** SURVIVES WITH NARROWING. EsportsBench (Thorrez 2024) overlaps on 3 of 5 criteria (≥2 RTS, pre-game, 1v1) but fails on method (rating systems only) and probabilistic-metric scope (log-loss only; no Brier/ECE/reliability). Three-part amendment REQUIRED.
- **Luka 4 (cold-start stratification):** SURVIVES. García-Méndez "cold start" is streaming warm-up, not player history — disambiguate in footnote.

### Cross-cutting findings
- Aligulac academic use 2024–2026: only Thorrez 2024.
- EsportsBench successors: none; dataset refreshes only.
- AoE2 replay-parsing ML 2024–2026: none found via aoc-mgz; Elbert 2025 uses API aggregates.
- Lin–Wu 2025 follow-up: remains on toy RPS tasks; does not threaten Luka 1 or Luka 3.

---

## End of dispatch prompt

The planner should now read `.claude/scientific-invariants.md`, `docs/TAXONOMY.md`, `docs/PHASES.md`, and `docs/THESIS_WRITING_MANUAL.md`, produce the two planning artifacts, and halt for user review.