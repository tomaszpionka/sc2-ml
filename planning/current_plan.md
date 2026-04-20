---
category: F
branch: docs/thesis-pass2-tg2-factual-contradictions
date: 2026-04-20
planner_model: claude-opus-4-7
dataset: null
phase: null
pipeline_section: "Phase 01 — Data Exploration (thesis-writing adaptation)"
invariants_touched: [I9]
source_artifacts:
  - thesis/chapters/01_introduction.md
  - thesis/chapters/02_theoretical_background.md
  - thesis/chapters/03_related_work.md
  - thesis/chapters/04_data_and_methodology.md
  - thesis/references.bib
  - thesis/WRITING_STATUS.md
  - thesis/chapters/REVIEW_QUEUE.md
  - thesis/pass2_evidence/sec_4_1_crosswalk.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_1v1_clean.yaml
  - .claude/author-style-brief-pl.md
  - .claude/scientific-invariants.md
  - .claude/rules/thesis-writing.md
critique_required: true
research_log_ref: "thesis/WRITING_STATUS.md (PR-TG2 notes)"
---

# Plan: Pass-2 TG2 — Factual contradictions (SC2 date range §2.2.2, Mountain Royals year in references.bib, AoE2 civ count §1.1/§1.2/§1.4/§2.3.2)

## Scope

This is a **revision** of previously-DRAFTED sections (§1.1, §1.2, §1.3, §1.4, §2.2, §2.3, §2.5, §3.x). No figures or tables are created; `Tabela 4.4a` in §4.1.3 is referenced as a read-only authoritative source for the aoestats data window and is not modified.

This plan executes Task Group 2 of the Pass-2 dispatch. It corrects three factual contradictions surfaced during TG1 review but deferred to a separate PR: (i) SC2EGSet date range mis-stated as 2016–2022 in §2.2.2 and §3.x:55 versus the correct 2016–2024 consistently stated in §4.1.1.1, Tabela 4.4a, and the 01_02_04 univariate census artifact; (ii) The Mountain Royals DLC assigned to year 2024 in `references.bib:791` (inside the `AoE2DE` entry's `note` field) versus the actual 2023-10-31 release; (iii) AoE2 civilization count stated as 45 at nine sites across §1.1, §1.2, §1.3, §1.4, §2.3.2, and §3.x versus the empirically observed 50 distinct civilizations in the aoestats data window (2022-08-28 — 2026-02-07). The plan produces one PR (PR-2) and defers TG3–TG6 to sequential follow-up plans per the dispatch's halt-and-review protocol. No empirical artifacts are touched; work is prose-only across three chapter files, one references.bib entry's `note` field, and the two tracker files (WRITING_STATUS.md, REVIEW_QUEUE.md).

## Problem Statement

The three findings operate at different epistemic levels and must be resolved independently.

**Finding 1 — SC2EGSet date range contradiction (§2.2.2 and §3.x vs §4.1.1.1).** §2.2.2 (`02_theoretical_background.md:33`) closes its third paragraph with: *"korpusy obejmujące długi okres czasowy (SC2EGSet rozciąga się na lata 2016–2022 zgodnie z findingiem Phase 01)"*. §3.x (`03_related_work.md:55`) contains "55 paczek turniejowych z lat 2016–2022". §4.1.1.1 (`04_data_and_methodology.md:17`) states *"z lat 2016–2024"* and §4.1.1.1 line 19 gives the exact endpoints *"2016-01-07 do 2024-12-01"*. The canonical Tabela 4.4a (`04_data_and_methodology.md:175`) gives the identical range. The authoritative source is `sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` Section F: *"earliest 2016-01-07T02:21:46.002Z / latest 2024-12-01T23:48:45.2511615Z"*. This contradiction is already documented in `thesis/pass2_evidence/sec_4_1_crosswalk.md:14` as a MIGRATION CANDIDATE flagged for a follow-up chore commit. The dispatch's phrasing *"§4.1.1.1 vs §4.1.1.2 date range"* is shorthand — the actual contradiction is §2.2.2 and §3.x (incorrect sites) vs §4.1.1.1 (authoritative site). §4.1.1.2 is about event-stream structure and carries no date-range claim.

**Finding 2 — The Mountain Royals DLC year in references.bib.** The `AoE2DE` entry at `references.bib:791` assigns The Mountain Royals to year 2024 in its `note` field. The DLC was announced 2023-10-16 and released 2023-10-31 per Steam, Wikipedia, Neowin, and ageofempires.com. The thesis chapter prose (§2.3.2 line 67) enumerates Mountain Royals in a DLC list but without an explicit date, so the only site requiring correction is the `references.bib` `note` field. Note: this is the only factual edit to the bibliography file in this plan; the bibkey itself, author list, URL, and all other fields remain untouched. The edit is a single-word change inside the `note` field.

**Finding 3 — AoE2 civ count at nine sites across three chapters.** The claim "45 cywilizacji" (or equivalent) appears at:
- `01_introduction.md:13` (§1.1 lead sentence): *"pomimo milionów aktywnych graczy, 45 asymetrycznych cywilizacji dostępnych w rankingowym trybie gry w okresie objętym analizowanymi zbiorami danych"*
- `01_introduction.md:15` (§1.1): *"990 unikalnych par cywilizacji ($\binom{45}{2}$) … 45 cywilizacji"*
- `01_introduction.md:23` (§1.2): *"45 cywilizacji wobec 3 ras w SC2"*
- `01_introduction.md:35` (§1.3 RQ3): *"990 unikalnych par cywilizacji wobec 9 par rasowych"*
- `01_introduction.md:45` (§1.4): *"dla AoE2 — 45 cywilizacji dostępnych w okresie analizy, generujących 990 unikalnych par"*
- `02_theoretical_background.md:67` (§2.3.2 para 1): *"W okresie objętym analizowanymi danymi (2024–2026) Age of Empires II: Definitive Edition oferuje czterdzieści pięć cywilizacji"* — already carrying a `[REVIEW:]` flag
- `02_theoretical_background.md:69` (§2.3.2 para 2): cascade $\binom{45}{2}+45=1035$ uporządkowanych par (lub 990 non-mirror)
- `02_theoretical_background.md:171` (§2.5.4): *"przestrzeń 990 par cywilizacji (dla 45 cywilizacji...)"*
- `03_related_work.md:17` (§3.x): *"45 cywilizacji w Age of Empires II, generujących 990 unikalnych zestawień"*

The empirically observed count in aoestats data is **50 distinct civilizations** across the window 2022-08-28 — 2026-02-07 (per `aoestats/INVARIANTS.md:10`, `research_log.md:456, 1184`, and `matches_1v1_clean.yaml:70, 99`). The §2.3.2 sub-claim *"W okresie objętym analizowanymi danymi (2024–2026)"* is also temporally wrong — the aoestats window starts 2022-08-28. Both the count and the window framing are incorrect. The target end-state replaces "45" with "50" and anchors the count empirically to the aoestats data window at all nine sites. The cascading arithmetic — "990 unikalnych par" and "1035 uporządkowanych" — must be recomputed: $\binom{50}{2}=1\,225$ unordered non-mirror; $\binom{50}{2}+50=1\,275$ ordered; at all applicable sites.

**Target end-state.** After execution: (i) §2.2.2 and §3.x:55 state "2016–2024" consistently with §4.1.1.1 and Tabela 4.4a; (ii) `references.bib:791` `note` field assigns Mountain Royals to 2023; (iii) all nine sites cite "50 cywilizacji" anchored to the aoestats data window, with cascading arithmetic corrected (990 → 1 225 and 1035 → 1 275 at applicable sites). The `[REVIEW:]` flag at §2.3.2 line 67 has its civ-count question removed (resolved) and is replaced by a reduced-scope flag covering DLC-chronology completeness (Three Kingdoms 2025-05-06, Chronicles: Alexander the Great 2025-10-14, Last Chieftains 2026-02-17). The `REVIEW_QUEUE.md` entry for §1.4 at line 23 is updated to record the resolution. No empirical artifacts are touched. No new bibkeys are introduced. §4.1.1.x (which already carries correct dates) is NOT re-written; the TG2 edits go to the inconsistent sites, not the authoritative sites.

## Assumptions & unknowns

### Pre-flight facts (verified 2026-04-20 via Read/Grep/WebSearch)

- §2.2.2 still contains the *"2016–2022"* date range at line 33. Verified via Read of `02_theoretical_background.md:33`.
- `references.bib:791` (inside `AoE2DE` note field) still contains "The Mountain Royals (2024)". Verified via Read.
- Nine sites carry the "45 cywilizacji" or equivalent "990"/"czterdzieści pięć"/"45 asymetrycznych cywilizacji" claims — §1.1 line 13 ("45 asymetrycznych cywilizacji"), §1.1 line 15, §1.2 line 23, §1.3 line 35, §1.4 line 45, §2.3.2 line 67, §2.3.2 line 69, §2.5.4 line 171, §3.x line 17. Verified via grep of `01_introduction.md`, `02_theoretical_background.md`, and `03_related_work.md`.
- aoestats observed civ count is 50 in the full window. Verified via `aoestats/INVARIANTS.md:10`, `research_log.md:456`, `matches_1v1_clean.yaml:70, 99`.
- Mountain Royals release date 2023-10-31. Verified via WebSearch returning Wikipedia, Steam, Neowin, ageofempires.com. All four sources concur.
- `03_related_work.md:55` contains "55 paczek turniejowych z lat 2016–2022". Verified via Read.
- The §4.1.1.1 date range 2016–2024 is the correct version and should be preserved. Verified by the `sec_4_1_crosswalk.md` audit which cites the artifact `01_02_04_univariate_census.md` Section F as the source of truth.
- §4.1.3 is the subsection heading housing Tabela 4.4a. Verified via `grep -n "Tabela 4.4a\|### 4.1.3" thesis/chapters/04_data_and_methodology.md`: result shows `### 4.1.3` heading at line 163 and Tabela 4.4a at line 167. T01's parenthetical "(Tabela 4.4a w §4.1.3)" is confirmed correct.
- Gate grep pattern verified (pre-execution): `grep -rnE "\b45 +[a-ząśłżźćńóę]* *cywili|\b990\b\s*(par|unikalnych|jeśli|non)|czterdzieści pięć|1035" thesis/chapters/01_introduction.md thesis/chapters/02_theoretical_background.md thesis/chapters/03_related_work.md` returns 9+ matches (all nine civ-count sites) and does NOT match `02_theoretical_background.md:43` (the SC2 engine constant `$1{,}3999023438$`), because `\b990\b` requires word boundaries which the embedded constant does not satisfy.

### Assumptions

- Assumption (principle, unstated in dispatch): the plan edits the prose-downstream-of-artifact site (§2.2.2, §3.x) and preserves the artifact-nearest site (§4.1.1.1 with its direct citation of `01_02_04_univariate_census.md`). This principle guides R1's direction; if the user wants the opposite, a plan revision is needed.
- **Unknown — deferred:** Whether the AoE2 civ count should be anchored to aoestats only (50) or also document the aoe2companion cardinality (wider vocabulary ~68 per `aoe2companion/01_02_04_univariate_census.md:359`, including campaign-only civs not ranked-available). **Resolution:** the thesis framing is "ranked 1v1", so aoestats observed-in-ranked count (50) is the right anchor; aoe2companion broader cardinality is a separate scoping question handled in §4.1.2. The TG2 edit uses 50 and flags the broader aoe2companion cardinality as out-of-scope.
- **Unknown — resolved by reviewer-adversarial Mode A:** Whether the 990 → 1 225 arithmetic substitution at §1.1 and §1.4 introduces a new methodological claim (e.g., that the matchup space is exactly 1 225 including mirrors vs. 1 225 excluding mirrors). Decision: preserve "unikalne pary" framing (unordered non-mirror, matching $\binom{n}{2}$), update arithmetic only.

## Literature context

This plan's rewrites do not introduce new bibkeys. All factual claims are anchored to existing Phase 01 artifacts and existing `references.bib` entries:

- `sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` — authoritative source for SC2EGSet temporal range (Section F: earliest/latest timeUTC).
- `[Bialecki2023]` — the SC2EGSet dataset paper; no edits here, but its corpus describes the 2016-2024 data used in this thesis.
- `[AoE2DE]` bibkey in `references.bib:786–792` — edited at line 791 only (inside `note` field: "The Mountain Royals (2024)" → "The Mountain Royals (2023)"). Citing conventions, URL, and author list preserved.
- `aoestats/reports/INVARIANTS.md:10` — authoritative source for aoestats observed civ count (50 in window 2022-08-28 — 2026-02-07).
- `[AoEStats]` bibkey in `references.bib:802–808` — no edits; the corpus this cite references is the source of the 50-civ figure.

Secondary external verification (WebSearch, 2026-04-20): Mountain Royals 2023-10-31 release confirmed via Steam store listing, Wikipedia "Age of Empires II: Definitive Edition", Neowin 2023 news article, and ageofempires.com official news post. AoE2 DE full-roster cardinality is NOT cited anywhere in this plan's thesis-prose edits — the 50-civ figure is an aoestats-window empirical observation, and full-roster audit (including Three Kingdoms 2025-05-06, Chronicles: Alexander the Great 2025-10-14, and Last Chieftains 2026-02-17) is deferred to a dedicated Pass-2 cardinality-accounting edit.

This plan does NOT modify `.claude/scientific-invariants.md` or any per-dataset `INVARIANTS.md`. The empirical findings already live in those files; the thesis prose adapts to them, not the reverse (invariant #9 compliance).

Note on plan provenance: this plan body is authored in a planning session (Claude Code opusplan) and applied to the working tree by the human before Commit B fires. Commits A and B encode that tree state onto the new branch; they are not self-generated by the plan.

## Pre-flight (branch-creation operation, not a numbered task)

Before any content edits, the branch-creation commit purges the merged TG1 artifacts:
- Overwrite `planning/current_plan.md` with this TG2 plan body.
- Delete `planning/current_plan.critique.md` (the TG1 Mode A critique).

Per git-workflow atomicity, this is split into TWO commits on the new branch before any content work begins:
- Commit A: `chore(planning): purge merged TG1 critique` — deletes `current_plan.critique.md` only.
- Commit B: `chore(planning): seed TG2 plan` — overwrites `current_plan.md` only.

These two commits are not part of the Execution Steps DAG; they establish the planning state before T01 begins.

## Execution Steps

Each task uses the `writer-thesis` agent as executor (per `thesis/plans/writing_protocol.md` section 6.4). Tasks T01, T02, T03 are parallel-safe in principle (they touch disjoint files), but are executed in the stated order for simplicity and to let T03 reference T02's completed state when updating trackers.

For shared tracker files (`WRITING_STATUS.md`, `REVIEW_QUEUE.md`), each task appends row notes only to rows it owns (per File Manifest attribution). Task sequencing T01 → T02 → T03 guarantees no concurrent tracker write. Writer-thesis must re-read the tracker file immediately before each edit.

---

### T01 — SC2 date range correction (§2.2.2 + §3.x:55)

**Objective:** Correct the SC2EGSet date range from "2016–2022" to "2016–2024" at two sites — §2.2.2 line 33 in `02_theoretical_background.md` and line 55 in `03_related_work.md` — so that both chapters are consistent with §4.1.1.1 and Tabela 4.4a. Each is a single-sentence clarification-only edit; surrounding paragraphs require no rewriting.

**Instructions:**
1. Read `thesis/chapters/02_theoretical_background.md` §2.2.2 line 33 in full (the "Trzeci wymiar dryfu" paragraph beginning at the start of the §2.2.2 numbered subsection).
2. Read `thesis/chapters/03_related_work.md` line 55 in full to confirm the "2016–2022" wording.
3. Read `thesis/chapters/04_data_and_methodology.md:17, 19, 175` to confirm the 2016–2024 range is authoritative.
4. Read `.claude/author-style-brief-pl.md` for voice constraints (no bullets, hedging idiomatycznie polski, no first-person plural).
5. Apply a minimal-substitution edit at `02_theoretical_background.md:33`: replace *"SC2EGSet rozciąga się na lata 2016–2022 zgodnie z findingiem Phase 01"* with *"SC2EGSet rozciąga się na lata 2016–2024 zgodnie z findingiem Phase 01 (Tabela 4.4a w §4.1.3)"*. The parenthetical forward-reference to Tabela 4.4a anchors the figure to the corpus-description locus.
6. Apply a minimal-substitution edit at `03_related_work.md:55`: change "2022" → "2024" in the SC2EGSet date span, using the same parenthetical cross-reference pattern as the §2.2.2 fix.
7. Do NOT rewrite any other prose in §2.2.2 or §3.x. The patch-drift argument and surrounding context remain compatible with the extended window.
8. Do NOT introduce new bibkeys. Do NOT modify `thesis/references.bib`.
9. Update §2.2 row in `thesis/WRITING_STATUS.md` with a dated Notes entry: *"2026-04-20 (PR-TG2): §2.2.2 line 33 date range 2016–2022 → 2016–2024 corrected per Pass-2 TG2 dispatch; contradiction with §4.1.1.1 and Tabela 4.4a closed."*
10. Update §3 row in `thesis/WRITING_STATUS.md` with a dated Notes entry: *"2026-04-20 (PR-TG2): §3.x line 55 SC2EGSet date range 2016–2022 → 2016–2024 corrected for consistency with §2.2.2 and §4.1.1.1."*
11. Update the existing §2.2 Pending row in `thesis/chapters/REVIEW_QUEUE.md` (line 30): append a 2026-04-20 PR-TG2 revision note to the Pass 2 status column. Existing flag count remains at 1 [REVIEW] (the grey-literature Liquipedia/BlizzardS2Protocol flag, which TG2 does not address).
12. Produce writer-thesis Chat Handoff Summary per `.claude/rules/thesis-writing.md`.

**Verification:**
- `grep -rnE "2016.{1,5}2022" thesis/chapters/02_theoretical_background.md thesis/chapters/03_related_work.md | wc -l` returns 0.
- `grep -rn "SC2EGSet rozciąga się na lata 2016[–-]2024" thesis/chapters/02_theoretical_background.md | wc -l` returns 1 (match in §2.2.2 line range).
- `grep -rn "2016[–-]2024" thesis/chapters/03_related_work.md | wc -l` returns at least 1 (match at §3.x:55).
- [sanity-check, not blocking] §2.2.2 total character count unchanged ± 200 characters.
- `thesis/WRITING_STATUS.md` §2.2 and §3 rows contain 2026-04-20 PR-TG2 notes.
- `thesis/chapters/REVIEW_QUEUE.md` §2.2 row has PR-TG2 revision note appended.

**File scope:**
- `thesis/chapters/02_theoretical_background.md` (Update §2.2.2 line 33 only)
- `thesis/chapters/03_related_work.md` (Update line 55 only — SC2 date range)
- `thesis/WRITING_STATUS.md` (Update §2.2 and §3 row notes)
- `thesis/chapters/REVIEW_QUEUE.md` (Append to existing §2.2 row)

**Read scope:**
- `thesis/chapters/04_data_and_methodology.md` §4.1.1.1 + Tabela 4.4a (authoritative dates)
- `thesis/pass2_evidence/sec_4_1_crosswalk.md` (pre-existing audit flag §2.2.2)
- `.claude/author-style-brief-pl.md`
- `.claude/rules/thesis-writing.md`

---

### T02 — Mountain Royals DLC year correction in references.bib

**Objective:** Correct the `AoE2DE` bibliography entry's `note` field to assign The Mountain Royals DLC to 2023 rather than 2024. This is a single-token change inside a `note` field; no bibkey, author list, URL, or other field is modified.

**Instructions:**
1. Read `thesis/references.bib:786–792` (the `AoE2DE` entry in full) to confirm the current `note` field wording.
2. Apply the minimal-substitution edit at line 791 only: change *"The Mountain Royals (2024)"* to *"The Mountain Royals (2023)"*. All other tokens in the `note` field — *"Initial release: 14 November 2019"*, *"Lords of the West (2021)"*, *"Dawn of the Dukes (2021)"*, *"Dynasties of India (2022)"*, *"Return of Rome (2023)"*, *"Chronicles: Battle for Greece (November 2024)"* — remain verbatim.
3. Do NOT modify any other entry in `references.bib`.
4. Do NOT modify any chapter prose under this task. §2.3.2 line 67 enumerates Mountain Royals in a DLC list; all §2.3.2 prose edits (including DLC-chronology positional verification and any year-stamp addition) are T03's responsibility, because T03 owns all §2.3.2 edits.
5. No `WRITING_STATUS.md` update under T02 (no chapter touched). No `REVIEW_QUEUE.md` row under T02 (bibliography edit is not a review-queue item per existing convention).
6. Produce writer-thesis Chat Handoff Summary.

**Verification:**
- `grep -n "The Mountain Royals" thesis/references.bib` returns exactly 1 match, and the adjacent year is 2023 (not 2024).
- `grep -rn "The Mountain Royals.*2024\|The Mountain Royals (2024)" thesis/references.bib | wc -l` returns 0.
- No other lines in `references.bib` are changed. Verified via `git diff --stat thesis/references.bib` showing a single-file-single-line change.

**File scope:**
- `thesis/references.bib` (Update line 791 only, `AoE2DE` entry `note` field)

**Read scope:**
- `thesis/chapters/02_theoretical_background.md` §2.3.2 (confirm no prose assertion of Mountain Royals year)
- `.claude/author-style-brief-pl.md`
- `.claude/rules/thesis-writing.md`

---

### T03 — AoE2 civ count correction across §1.1, §1.2, §1.3, §1.4, §2.3.2, §2.5.4, §3.x (nine sites)

**Objective:** Replace the "45 cywilizacji" claim at nine sites with the empirically observed 50 civilizations, anchored to the aoestats data window. Recompute the cascading $\binom{n}{2}$ arithmetic at all applicable sites (990 → 1 225 unordered non-mirror; 1035 → 1 275 ordered). Correct the incorrectly-cited window "2024–2026" at §2.3.2:67 to the ISO form (2022-08-28 — 2026-02-07). Remove the now-resolved `[REVIEW:]` flag at §2.3.2 line 67 (civ-count question); full-roster / Chronicles-exclusion narrative remains deferred to a future scope-expansion edit (no one-clause parenthetical added — see Open Q 1). Update the §1.4 Pending row in REVIEW_QUEUE.md to record the resolution.

**Instructions:**
1. Read `thesis/chapters/01_introduction.md` §1.1 line 13, §1.1 line 15, §1.2 line 23, §1.3 line 35, §1.4 line 45.
2. Read `thesis/chapters/02_theoretical_background.md` §2.3.2 lines 67–69, §2.5.4 line 171.
3. Read `thesis/chapters/03_related_work.md` line 17.
4. Read `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md:10` to confirm the 50-civ figure.
5. Read `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_1v1_clean.yaml:66–70, 95–99` to confirm "50 distinct civilizations in scope" on both p0_civ and p1_civ.
6. Read `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md:456` to confirm "Faction vocabulary (top 10 of 50 distinct)".
7. Read `.claude/author-style-brief-pl.md`, `.claude/rules/thesis-writing.md`.
8. Apply edits at the nine sites. Each edit is a substitution anchored to the aoestats data window, plus the cascading arithmetic updates:
   - **§1.1 line 13 (`01_introduction.md:13`):** substitute "45 asymetrycznych cywilizacji" → "50 asymetrycznych cywilizacji". Preserve the "asymetrycznych" qualifier (it is semantically load-bearing — it distinguishes AoE2's civilization-asymmetric design from race-symmetric designs). Anchor the claim to the aoestats data window as for the other §1.x sites. Do NOT change surrounding prose.
   - **§1.1 line 15 (`01_introduction.md:15`):** substitute "45" → "50" and "$\binom{45}{2}$" → "$\binom{50}{2}$"; update "990" → "1 225" where the formula appears in this line.
   - **§1.2 line 23 (`01_introduction.md:23`):** *"45 cywilizacji wobec 3 ras w SC2"* → *"50 cywilizacji wobec 3 ras w SC2"*.
   - **§1.3 line 35 (`01_introduction.md:35`):** *"990 unikalnych par cywilizacji wobec 9 par rasowych"* → *"1 225 unikalnych par cywilizacji wobec 9 par rasowych"*.
   - **§1.4 line 45 (`01_introduction.md:45`):** *"45 cywilizacji dostępnych w okresie analizy, generujących 990 unikalnych par"* → *"50 cywilizacji dostępnych w oknie aoestats (2022-08-28 — 2026-02-07, Tabela 4.4a), generujących 1 225 unikalnych par"*.
   - **§2.3.2 line 67 (`02_theoretical_background.md:67`):** Substitute "czterdzieści pięć cywilizacji" → "pięćdziesiąt cywilizacji" and correct the window "(2024–2026)" → "(2022-08-28 — 2026-02-07, Tabela 4.4a)". No full-roster or Chronicles-exclusion parenthetical is added (Mode A reviewer-adversarial BLOCKER A1 flagged prior "53 total, 3 Chronicles excluded" wording as factually wrong: Chronicles shipped in two parts for 6 civs total, not 3; Three Kingdoms and Last Chieftains also omitted). The `[REVIEW:]` flag's civ-count question is removed (now resolved); the DLC chronology parenthetical in the flag is preserved verbatim as a brief parenthetical. A reduced-scope `[REVIEW:]` flag is planted in its place: *"[REVIEW: DLC chronology completeness — zweryfikować w Pass 2, czy lista obejmuje Three Kingdoms (2025-05-06, +5 civ), Chronicles: Alexander the Great (2025-10-14, +3 civ) i Last Chieftains (2026-02-17, +3 civ)]"* — full-roster cardinality audit deferred to Pass 2.
   - **Mountain Royals positional verification (§2.3.2):** After the §2.3.2:67 substitution is applied, confirm the DLC chronology parenthetical places Mountain Royals adjacent to Return of Rome (2023) and before Chronicles: Battle for Greece (November 2024). Operational trigger: if any DLC entry between Return of Rome (2023) and Chronicles (November 2024) lacks an explicit date parenthetical, add "(2023)" inline with Mountain Royals; otherwise, preserve positional transmission verbatim. This verification is T03's responsibility because T03 owns all §2.3.2 edits.
   - **§2.3.2 line 69 (`02_theoretical_background.md:69`):** Recompute arithmetic only: 45→50, $\binom{45}{2}+45=1035$ → $\binom{50}{2}+50=1\,275$, 990→1 225. Preserve the ordered/unordered explicit treatment.
   - **§2.5.4 line 171 (`02_theoretical_background.md:171`):** *"przestrzeń 990 par cywilizacji (dla 45 cywilizacji...)"* → *"przestrzeń 1 225 par cywilizacji (dla 50 cywilizacji...)"*.
   - **§3.x line 17 (`03_related_work.md:17`):** *"45 cywilizacji w Age of Empires II, generujących 990 unikalnych zestawień"* → *"50 cywilizacji w Age of Empires II, generujących 1 225 unikalnych zestawień"*.
9. Preserve cross-references and framing: §1.1 continues to introduce the research gap; §1.2 continues to motivate matchup-conditioned ranking; §1.3 continues to frame research questions; §1.4 continues to enumerate scope limitations; §2.3.2 continues to characterise AoE2's matchup combinatorics. No section-level rewrites beyond the targeted numerical substitutions and the §2.3.2 window correction.
10. Do NOT introduce new bibkeys. Do NOT modify `thesis/references.bib` (T02 owns that file).
11. Update four rows in `thesis/WRITING_STATUS.md`:
    - §1.1: add dated Notes entry *"2026-04-20 (PR-TG2): §1.1 line 15 AoE2 civ count 45 → 50 corrected, anchored to aoestats data window per Pass-2 TG2 dispatch."*
    - §1.2: append to existing TG1 note: *"2026-04-20 (PR-TG2, sequential): §1.2 line 23 AoE2 civ count 45 → 50 corrected."*
    - §1.4: preserve the existing mgz-parser flag; append dated 2026-04-20 PR-TG2 note: *"2026-04-20 (PR-TG2): §1.4 line 45 AoE2 civ count 45 → 50 + arithmetic 990 → 1 225 corrected; REVIEW_QUEUE civ-count question resolved."*
    - §2.3: append dated Notes entry *"2026-04-20 (PR-TG2): §2.3.2 lines 67, 69 AoE2 civ count corrected to 50 (anchored to aoestats INVARIANTS.md:10 window 2022-08-28 — 2026-02-07); cascade arithmetic 1035→1275, 990→1225; original civ-count [REVIEW:] flag resolved; reduced-scope [REVIEW:] flag for DLC-chronology completeness (Three Kingdoms, Chronicles: Alexander the Great, Last Chieftains) planted per Mode A A2."* Keep existing remaining `[REVIEW]` flags (Liquipedia/GitHub URLs grey-literature) unchanged.
12. Update two rows in `thesis/chapters/REVIEW_QUEUE.md`:
    - §1.4 row (line 23): append dated 2026-04-20 closure notation to question (2) (civ count resolved); leave row Pending with question (1) (mgz parser) unresolved.
    - §2.3 row (line 31): append dated PR-TG2 revision note *"2026-04-20 (PR-TG2): §2.3.2 line 67 civ count resolved to 50 observed in aoestats window; original [REVIEW:] flag's civ-count question resolved; new reduced-scope [REVIEW:] flag planted for DLC-chronology completeness (Three Kingdoms 2025-05-06, Chronicles: Alexander the Great 2025-10-14, Last Chieftains 2026-02-17). Remaining Pass 2 flags on Liquipedia/GitHub grey-literature unchanged."*
13. Produce writer-thesis Chat Handoff Summary.

**Verification:**
- `grep -rnE "\b45 +[a-ząśłżźćńóę]* *cywili|\b990\b\s*(par|unikalnych|jeśli|non)|czterdzieści pięć|1035" thesis/chapters/01_introduction.md thesis/chapters/02_theoretical_background.md thesis/chapters/03_related_work.md | wc -l` returns 0. (Pattern anchored with word-boundaries to avoid false-positive on the SC2 engine constant `$1{,}3999023438$` at `02_theoretical_background.md:43`; the "\b45 +[a-ząśłżźćńóę]* *cywili" branch catches both "45 cywilizacji" and "45 asymetrycznych cywilizacji".) `grep -rnF '\binom{45}{2}' thesis/chapters/01_introduction.md thesis/chapters/02_theoretical_background.md thesis/chapters/03_related_work.md | wc -l` returns 0.
- `grep -rn -e "50 cywilizacji" -e "pięćdziesiąt" thesis/chapters/01_introduction.md thesis/chapters/02_theoretical_background.md thesis/chapters/03_related_work.md | wc -l` returns at least 4 (§1.1, §1.4, §2.3.2, §3.x). `grep -rn -F '\binom{50}{2}' thesis/chapters/01_introduction.md thesis/chapters/02_theoretical_background.md thesis/chapters/03_related_work.md | wc -l` returns at least 1 (§1.1 or §2.3.2).
- `grep -rn "990 unikalnych par" thesis/chapters/01_introduction.md | wc -l` returns 0 (990 arithmetic fully replaced by 1 225).
- `grep -rn "1 225" thesis/chapters/01_introduction.md | wc -l` returns at least 2 (§1.1 and §1.4). `grep -rn -F '\binom{50}{2}' thesis/chapters/01_introduction.md | wc -l` returns at least 1.
- `grep -rnE "2024.{1,10}2026" thesis/chapters/02_theoretical_background.md | wc -l` returns 0 at §2.3.2 line 67 (incorrect window removed).
- `grep -rn "2022-08-28\|aoestats/INVARIANTS.md:10" thesis/chapters/02_theoretical_background.md | wc -l` returns at least 1 (match at §2.3.2 line 67).
- [sanity-check, not blocking] §1.1 + §1.2 + §1.3 + §1.4 + §2.3.2 + §2.5.4 + §3.x combined character count increase ≤ 1 500 characters (arithmetic and window substitutions; no substantive expansions).
- `thesis/WRITING_STATUS.md` four rows updated (§1.1, §1.2, §1.4, §2.3).
- `thesis/chapters/REVIEW_QUEUE.md` §1.4 row has 2026-04-20 closure notation for question (2) appended; row remains Pending; §2.3 row has PR-TG2 revision note appended.
- No net-additive substance: the T03 rewrites at all nine sites are empirical-count corrections anchored to existing aoestats Phase 01 artifacts. No new methodological claim, new bibkey, or new window definition is introduced beyond what aoestats Phase 01 already established.

**File scope:**
- `thesis/chapters/01_introduction.md` (Update §1.1 line 13, §1.1 line 15, §1.2 line 23, §1.3 line 35, §1.4 line 45 — five substitutions)
- `thesis/chapters/02_theoretical_background.md` (Update §2.3.2 lines 67, 69 and §2.5.4 line 171 — three substitutions)
- `thesis/chapters/03_related_work.md` (Update §3.x line 17 — civ count + arithmetic; note: line 55 is owned by T01)
- `thesis/WRITING_STATUS.md` (Update §1.1, §1.2, §1.4, §2.3 rows)
- `thesis/chapters/REVIEW_QUEUE.md` (Append to §1.4 row; append to §2.3 row)

**Read scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md:10` (authoritative: 50 civs)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md:456, 1184` (top-10 of 50 distinct)
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_1v1_clean.yaml:66–99` (50 distinct in scope)
- `thesis/chapters/04_data_and_methodology.md:175` (Tabela 4.4a — aoestats window 2022-08-28 — 2026-02-07)
- `.claude/author-style-brief-pl.md`
- `.claude/rules/thesis-writing.md`
- `.claude/scientific-invariants.md` (#9 — no empirical-artifact modification)

---

## File Manifest

| File | Action |
|------|--------|
| `planning/current_plan.md` | Overwrite (Pre-flight — with this TG2 plan) |
| `planning/current_plan.critique.md` | Delete (Pre-flight — purge merged TG1 critique) |
| `thesis/chapters/01_introduction.md` | Update (§1.1 line 13 "asymetrycznych" site, §1.1 line 15, §1.2 line 23, §1.3 line 35, §1.4 line 45 — civ count + arithmetic) |
| `thesis/chapters/02_theoretical_background.md` | Update (§2.2.2 line 33 SC2 date range — T01; §2.3.2 lines 67, 69 AoE2 civ count + window — T03; §2.5.4 line 171 — T03) |
| `thesis/chapters/03_related_work.md` | Update (line 55 SC2 date range — T01; line 17 civ-count + arithmetic — T03) |
| `thesis/references.bib` | Update (`AoE2DE` entry line 791 only, `note` field: 2024 → 2023 for Mountain Royals — T02) |
| `thesis/WRITING_STATUS.md` | Update (§1.1, §1.2, §1.4, §2.2, §2.3, §3 rows) |
| `thesis/chapters/REVIEW_QUEUE.md` | Update (append closure notation to §1.4 row question (2); append PR-TG2 notes to §2.2 and §2.3 rows) |

## Gate Condition

All conditions must hold after execution for PR-2 to merge.

- `planning/current_plan.md` contains the TG2 plan (not the TG1 plan). `planning/current_plan.critique.md` does not exist.
- §2.2.2 at `02_theoretical_background.md:33` states "2016–2024" not "2016–2022". `grep` confirms zero "2016–2022" matches in theoretical background chapter.
- §3.x at `03_related_work.md:55` states "2016–2024" not "2016–2022". `grep` confirms zero "2016–2022" matches in related work chapter.
- §2.2.2 carries a parenthetical forward-reference to Tabela 4.4a (§4.1.3) anchoring the 2016–2024 figure.
- `references.bib:791` assigns Mountain Royals to 2023 inside the `AoE2DE` `note` field. No other bibkey field is modified. `grep` confirms zero "Mountain Royals (2024)" matches in references.bib.
- §1.1 line 13, §1.1 line 15, §1.2 line 23, §1.3 line 35, §1.4 line 45, §2.3.2 lines 67, 69, §2.5.4 line 171, §3.x line 17 — all nine sites state "50 cywilizacji" or equivalent (pięćdziesiąt/1 225/$\binom{50}{2}$) anchored to the aoestats data window. `grep` sweep confirms zero residual matches: `grep -rnE "\b45 +[a-ząśłżźćńóę]* *cywili|\b990\b\s*(par|unikalnych|jeśli|non)|czterdzieści pięć|1035" thesis/chapters/01_introduction.md thesis/chapters/02_theoretical_background.md thesis/chapters/03_related_work.md | wc -l` returns 0. `grep -rnF '\binom{45}{2}' thesis/chapters/01_introduction.md thesis/chapters/02_theoretical_background.md thesis/chapters/03_related_work.md | wc -l` returns 0. (Word-boundary anchors prevent false-positive on SC2 engine constant `$1{,}3999023438$` at `02_theoretical_background.md:43`.)
- §1.1 and §1.4 arithmetic updated: "990 unikalnych par" → "1 225 unikalnych par" ($\binom{50}{2}$ substitution). `grep -rn "990 unikalnych par" thesis/chapters/01_introduction.md | wc -l` returns 0.
- §2.3.2 line 69 arithmetic updated: 1035 → 1 275 ordered, 990 → 1 225 non-mirror.
- §2.3.2 line 67 — the incorrect window phrase *"W okresie objętym analizowanymi danymi (2024–2026)"* is replaced with the ISO aoestats window reference (2022-08-28 — 2026-02-07). The rewrite is 45→50 + window correction only; no full-roster or Chronicles-exclusion parenthetical is added. No net-additive claims are introduced.
- §2.3.2 line 67 — the original `[REVIEW:]` flag's civ-count question is removed (resolved); the DLC chronology parenthetical is retained; a reduced-scope `[REVIEW:]` flag covering DLC-chronology completeness (Three Kingdoms, Chronicles: Alexander the Great, Last Chieftains) is planted per Mode A A2.
- `thesis/WRITING_STATUS.md` updated with six row notes (§1.1, §1.2, §1.4, §2.2, §2.3, §3).
- `thesis/chapters/REVIEW_QUEUE.md` — §1.4 row carries 2026-04-20 closure notation for question (2) (civ count) appended in-place; row remains Pending for question (1) (mgz parser); §2.2 and §2.3 rows carry PR-TG2 revision notes.
- No new bibkeys introduced (`git diff thesis/references.bib` shows only the single-line `note` edit).
- No edits outside the File Manifest. `git diff --stat` shows exactly 8 files changed (with `planning/current_plan.critique.md` deleted).
- No net-additive substance: TG2 is a factual-correction plan. No new methodological claim, protocol, diagnostic, or threshold is introduced. All substitutions are anchored to existing Phase 01 artifacts or to external sources (Wikipedia, Steam) whose citations via existing `[AoE2DE]` bibkey remain sufficient.
- Post-rewrite cross-section consistency sweep: `grep -rnE "2016[–-]2022|Mountain Royals.*2024" thesis/chapters/01_introduction.md thesis/chapters/02_theoretical_background.md thesis/chapters/03_related_work.md thesis/references.bib | wc -l` returns 0. `grep -rnE "\b45 +[a-ząśłżźćńóę]* *cywili|45 cywilizacji" thesis/chapters/01_introduction.md thesis/chapters/02_theoretical_background.md thesis/chapters/03_related_work.md | wc -l` returns 0.
- reviewer-adversarial Mode C draft review returns PASS or REQUIRE_MINOR_REVISION.
- Post-merge halt: TG3 planning does not begin until the user reviews the merged PR-2 diff and explicitly requests re-planning.

## Rollback plan

If PR-2 is rejected at review, all edits can be individually reverted via `git revert` of the PR merge commit. The three-finding decomposition (T01, T02, T03) allows cherry-picking a partial revert — e.g., preserving T01's SC2 date fix while reverting T03's civ-count cascade — if a specific finding is disputed. The `WRITING_STATUS.md` and `REVIEW_QUEUE.md` updates are single-row edits. No empirical artifacts or new bibkeys are introduced, so rollback carries no data-layer risk.

## Out of scope

- **TG3** — Luka 3 narrowing (§3.5 amendment against Thorrez 2024 EsportsBench; 3-part edit). Separate PR.
- **TG4** — 11 bibliography findings (García-Méndez, Hodge, Bunker, SC-Phi2, Aligulac, Elbert, EsportsBench, Baek, Glickman, Lin, Çetin Taş). Separate PR.
- **TG5** — 6 internal-consistency fixes (other than the three TG2 findings, which are factual contradictions, not internal-consistency pedantry). Separate PR.
- **TG6** — 12 prophylactic/hygiene fixes. Separate PR.
- **§4.1.1.x rewrites** — §4.1.1.1 already carries the correct date range. TG2 edits only the chapters that are inconsistent with §4.1.1.1, not §4.1.1.1 itself (no-regression principle).
- **aoe2companion civ cardinality (~68)** — broader vocabulary including campaign-only civs not ranked-available. Out of TG2 scope; the 50 figure anchors the ranked-1v1 scope.
- **Full 53-total-roster narrative at §2.3.2** — deferred entirely to a future scope-expansion edit. Mode A reviewer-adversarial BLOCKER A1 showed that the prior "53 total, 3 Chronicles excluded" parenthetical was factually wrong (Chronicles shipped in two parts = 6 civs excluded, not 3; Three Kingdoms 2025-05-06 and Last Chieftains 2026-02-17 also omitted from the DLC chronology). A defensible full-roster audit requires a dedicated Pass-2 cardinality-accounting edit with fresh WebSearch verification against Fandom, Liquipedia, and ageofempires.com; out of TG2 scope.
- **Chronicles: Battle for Greece date in references.bib** — currently cited as "November 2024" in `references.bib:791` `note` field. This is factually correct (released 2024-11-14) and is NOT modified.
- **AoE2 DE 2025–2026 DLCs not yet cited in references.bib** — Three Kingdoms (2025-05-06), Chronicles: Alexander the Great (2025-10-14), Last Chieftains (2026-02-17). Out of TG2 scope.
- **`.claude/scientific-invariants.md`** — not modified; the "45-civs" is not a repository invariant.
- **Chapter 5 / 6 / 7 forward-refs** — BLOCKED in WRITING_STATUS.md; no prose touches them.
- **New empirical claims** — none. Prose-only rewriting and single-token bibliography edit.
- **Phase 01 artifact modification** — invariant #9 forbids; nothing in TG2 requires it.

## Open questions

- **Open Q 1 (civ count anchor choice — resolved).** Single-anchor at 50 observed (aoestats-sourced), no full-roster parenthetical at §2.3.2:67. Mode A reviewer-adversarial A1 showed the previously-proposed "53 total, 3 Chronicles excluded" parenthetical was factually wrong: Chronicles shipped in two parts (Battle for Greece 2024-11 + Alexander the Great 2025-10-14) for 6 civs total; Three Kingdoms 2025-05-06 (+5) and Last Chieftains 2026-02-17 (+3) are also omitted from the DLC chronology prose. Full-roster audit deferred to a dedicated Pass-2 edit with fresh source verification.
- **Open Q 2 (aoe2companion cardinality — out of scope but recorded).** aoe2companion's `civ` field has cardinality ~68 per `aoe2companion/01_02_04_univariate_census.md:359`. TG2 deliberately anchors to aoestats (ranked-1v1 scope). If a reviewer asks why aoe2companion's 68 is not cited, the answer is: aoe2companion's vocabulary includes non-ranked-1v1 civs.
- **Open Q 3 (Mountain Royals prose mention at §2.3.2).** §2.3.2 line 67 enumerates Mountain Royals in a DLC chronology without a year. The positional ordering (Return of Rome (2023) → Mountain Royals → Chronicles (Nov 2024)) transmits an implicit 2023 cue. T03's Mountain Royals positional verification sub-step handles this: if ambiguity remains after the §2.3.2 rewrite, an explicit year-stamp "(2023)" is added inline.
- **Open Q 4 (990 → 1 225 arithmetic framing).** Preserve "unikalne pary" framing (unordered-non-mirror, which matches $\binom{n}{2}$), update the number only. The existing ordered/unordered explicit treatment at §2.3.2:69 is preserved and recomputed.
- **Open Q 5 (REVIEW_QUEUE.md §1.4 row update).** Resolved as in-place update: append 2026-04-20 closure notation to question (2) only; leave row Pending with question (1) unresolved.
- **Open Q 6 (Dispatch-shorthand interpretation).** The planner reinterpreted "§4.1.1.1 vs §4.1.1.2" as shorthand for "§2.2.2 vs §4.1.1.1". Reviewer-adversarial Mode A should confirm the reinterpretation.

---

**Adversarial critique triggers for Step 2** (reviewer-adversarial Mode A targeting recommendations — NOT the critique itself):

- **Hardest-to-catch risk.** Whether T03's §2.3.2 tightened rewrite (45→50 + window correction, no 53-total additions) correctly limits scope to substitution-plus-clarification without introducing net-additive substance.
- **Arithmetic correctness.** Reviewer should independently verify $\binom{50}{2} = 1\,225$, $\binom{50}{2}+50 = 1\,275$, and confirm no off-by-one or ordering-ambiguity slippage.
- **Bibkey integrity.** T02's single-token edit to `references.bib:791` must not accidentally touch other lines of the `AoE2DE` entry. Reviewer should diff the entire entry post-T02 against pre-T02.
- **Cross-section consistency.** Post-T03, all nine sites must carry "50" / "pięćdziesiąt" / "1 225" / "$\binom{50}{2}$" consistently; no site left at 45/990/1035/czterdzieści pięć/45 asymetrycznych. Reviewer should run the Gate grep sweep.
- **Window consistency at §2.3.2.** The replacement window "2022-08-28 — 2026-02-07" must match Tabela 4.4a line 175 exactly. Reviewer should verify character-level identity.
- **DLC chronology preservation at §2.3.2.** The existing DLC chronology narrative is preserved; the `[REVIEW:]` flag's civ-count question is removed; the chronology text is retained.
- **REVIEW_QUEUE.md §1.4 row in-place update.** Verify that question (2) is closed in-place (not moved to Completed table) and question (1) remains Pending — consistent with in-place-update convention (Open Q 5 resolved).
- **Scope creep guardrails.** Verify File Manifest is strictly limited to the eight listed files (7 + the purged critique). No task prescribes edits to §4.1.1.x, `.claude/scientific-invariants.md`, per-dataset INVARIANTS.md, or any Chapter 5/6/7 file.
- **Mountain Royals year verification.** Reviewer should independently WebSearch Mountain Royals release date to confirm 2023-10-31 (recommend: Steam DLC page + Wikipedia cross-check).
- **Pass-2 flag lifecycle.** The §2.3.2 `[REVIEW:]` flag's civ-count question is removed (resolved) and replaced by a reduced-scope DLC-chronology-completeness flag per Mode A A2. Flag count at §2.3.2:67 remains 1 (one out, one in).
- **No-regression at §4.1.1.x.** §4.1.1.1 already carries the correct 2016–2024 range. T01 edits §2.2.2 and §3.x:55 (inconsistent sites), NOT §4.1.1.1. Reviewer should confirm no accidental edit to §4.1.1.x.
- **Dispatch shorthand.** Reviewer-adversarial Mode A should confirm the "§4.1.1.1 vs §4.1.1.2" shorthand reinterpretation (Open Q 6).

---

This plan is Category F. Adversarial critique via reviewer-adversarial is required before execution begins. Dispatch reviewer-adversarial; output: `planning/current_plan.critique.md`.
