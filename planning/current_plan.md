---
category: F
branch: docs/thesis-pass2-tg4-bibliography-findings
date: 2026-04-20
planner_model: claude-opus-4-7
dataset: null
phase: null
pipeline_section: "Phase 07 — Thesis Writing Wrap-up (Pass-2 TG4 bibliography fixes)"
invariants_touched: []
source_artifacts:
  - thesis/references.bib
  - thesis/chapters/01_introduction.md
  - thesis/chapters/03_related_work.md
  - thesis/THESIS_STRUCTURE.md
  - thesis/WRITING_STATUS.md
  - thesis/chapters/REVIEW_QUEUE.md
  - .claude/author-style-brief-pl.md
  - .claude/scientific-invariants.md
  - .claude/rules/thesis-writing.md
critique_required: true
research_log_ref: "thesis/WRITING_STATUS.md (PR-TG4 notes)"
---

# Plan: Pass-2 TG4 — Eleven bibliography findings audit and fixes

## Scope

This plan executes Task Group 4 of the Pass-2 dispatch: an audit and correction of eleven references in `thesis/references.bib` plus two carry-over items from TG3. Eleven bibkey-level fixes land: author name (Thorrez2024 Lucas→Clayton, Hodge2021 fabricated coauthors, BaekKim2022 both first names, Aligulac attribution, Elbert2025EC two first-name typos), metadata completeness (Glickman2001 DOI, Lin2024NCT arXiv id + author-name fix, Thorrez2024 preprint URL, Bunker2024 DOI-only confirmed), duplicate elimination (Tarassoli2024 removed as ghost-entry; Khan2024SCPhi2 pages 2444-2462→2338-2352), and one missing entry insertion (GarciaMendez2025 currently cited by bibkey in `01_introduction.md` but absent from global bib). Chapter prose propagation is minimal (three one-line updates plus one `[REVIEW:]` flag removal plus one `[Baek2022]`→`[BaekKim2022]` bibkey harmonisation in `01_introduction.md`). No empirical artifacts touched; no figures/tables; no new research claims. The plan produces one PR (PR-4) and defers TG5 (internal-consistency fixes) and TG6 (prophylactic/hygiene fixes) to separate plans.

A latent 12th finding was surfaced during /critic empirical verification (not in the original 11 findings): arXiv:2408.17180 names the second author "Yu-Wei Shih" (email yoway0430@gmail.com), not "Yi-Wei Shih" as stored in the current `Lin2024NCT` bib entry. This is a low-risk bibkey-field-only fix with no prose propagation — Polish prose cites by bibkey only. The fix is incorporated into T01 step 10.

## Problem Statement

Eleven bibliography entries currently contain author-attribution errors, missing metadata, or duplicate-entry bugs that would fail defence if examiners trace citations to source. Three distinct error classes are present.

**Class A — bibliography hygiene (pre-typesetting coauthor corrections).** Hodge2021 (line 60) lists "Sherkat, Sam and Sherkat, Ehsan and others" as coauthors alongside Victoria J. Hodge. These names do not appear in the paper (verified via IEEE Xplore and White Rose institutional repository). The actual coauthors are Devlin, Sephton, Block, Cowling, Drachen. This is a bib-scaffolding error that would propagate at typesetting time if not fixed; chapter prose at `01_introduction.md:67` and `03_related_work.md:93` already carries the correct author list, so this correction is purely in the global bib. BaekKim2022 (line 33) lists "Baek, Jihun and Kim, Jinyoung" — the actual authors are Insung Baek and Seoung Bum Kim (verified via PLOS ONE canonical page). Aligulac (line 157) lists "Kim, Espen" — the project maintainer is Eivind Fonn (TheBB on GitHub, verified via GitHub user profile). Thorrez2024 (line 148) lists "Thorrez, Lucas" — Clayton Thorrez per https://cthorrez.github.io/ and HuggingFace dataset ownership. Elbert2025EC (line 79) lists "Schenk, Amadeus" and "Stein, Nora" — the correct first names per arXiv:2506.04475 are Alicia von Schenk and Nikolai Stein.

**Class B — metadata incompleteness.** Glickman2001 (line 110) lacks the canonical DOI `10.1080/02664760120059219`. Lin2024NCT (line 243) lacks the arXiv identifier `2408.17180` despite being cited in chapter prose with that exact identifier. Thorrez2024 (line 147) lacks the canonical preprint URL (already known per TG3 references block). Bunker2024 (line 452) has the DOI but is missing optional volume/issue/pages metadata (low-risk addition; defer if uncertain).

**Class C — duplicate / ghost entry.** Tarassoli2024 (line 50–55) is a phantom bib entry for SC-Phi2 with fabricated first author "Tarassoli, Saeid"; the real authors of the same paper (Khan and Sukthankar) are at Khan2024SCPhi2 (line 406–416), which also has incorrect pages (2444-2462 vs canonical 2338-2352). A flagged `[REVIEW:]` in `03_related_work.md:69` already identifies the Tarassoli2024 entry as misattribution to be deleted "in morning review".

Additionally, GarciaMendez2025 is cited by bibkey at `01_introduction.md:11` (via inline `[GarciaMendez2025]`) but absent from the global `thesis/references.bib`. The fix is required for consistency with the cross-chapter bibkey convention per `.claude/rules/thesis-writing.md` (`Citations: [AuthorYear] keys in thesis/references.bib`) — the global bibliography must contain every inline-cited bibkey; absence at typesetting time would break BibTeX resolution. Current metadata in `01_introduction.md:81` local References is correct and can be promoted into the global bib.

**Finding enumeration (11 original + 1 latent).**

| # | Bibkey | Finding | Type |
|---|--------|---------|------|
| 1 | GarciaMendez2025 | Entry absent from global bib; cited by bibkey in `01_introduction.md:11` | promotion-new-entry |
| 2 | Hodge2021 | Fabricated coauthors ("Sherkat, Sam and Sherkat, Ehsan") replaced with canonical IEEE Xplore list; volume/issue/pages added | corrective-edit |
| 3 | Bunker2024 | DOI correct; no metadata errors found; pagination deferred | verification-no-op |
| 4 | Khan2024SCPhi2 | Pages 2444–2462 → 2338–2352 (MDPI canonical); note field cleaned | corrective-edit |
| 5 | Aligulac | Author "Kim, Espen" → "Fonn, Eivind" (GitHub TheBB profile) | corrective-edit |
| 6 | Elbert2025EC | Two first-name corrections: Amadeus→Alicia (von Schenk), Nora→Nikolai (Stein) | corrective-edit |
| 7 | Thorrez2024 | Author "Lucas"→"Clayton"; preprint URL added (TG3 carry-over) | corrective-edit |
| 8 | BaekKim2022 | Author "Baek, Jihun and Kim, Jinyoung" → "Baek, Insung and Kim, Seoung Bum" | corrective-edit |
| 9 | Glickman2001 | DOI `10.1080/02664760120059219` added | corrective-edit |
| 10 | Lin2024NCT | arXiv URL `2408.17180` added | corrective-edit |
| 11 | CetinTas2023 | Author names, DOI, venue verified correct; no fix required | verification-no-op |
| 12 | Lin2024NCT | (latent, surfaced during /critic) Author "Shih, Yi-Wei" → "Shih, Yu-Wei" per arXiv HTML | corrective-edit |

Also: Tarassoli2024 phantom entry deletion is bundled with finding 4 (Khan2024SCPhi2 reconciliation).

**Target end-state.** After execution: eleven corrected or added bib entries (plus latent 12th Shih author-name fix incorporated into T01 step 10); two one-line prose updates (Baek initials in `01_introduction.md:69`, Tarassoli→Khan in `THESIS_STRUCTURE.md:148`); one `[REVIEW:]` flag removed from `03_related_work.md:69` (Tarassoli/Khan reconciliation resolved); one `[Baek2022]`→`[BaekKim2022]` bibkey harmonisation in `01_introduction.md` (lines 13, 25, and 69 — three occurrences). TG3-planted `[REVIEW:]` flags and all other Pass-2 flags remain intact. No new citations introduced beyond GarciaMendez2025 promotion (already cited in prose; this is BibTeX-resolution fix, not new-content addition).

## Pre-flight facts (verified 2026-04-20 via Read/Grep/WebSearch/WebFetch)

- Thorrez2024 author: "Clayton" per https://cthorrez.github.io/ and https://www.claytonthorrez.com/ — verified. HuggingFace dataset ownership at https://huggingface.co/datasets/EsportsBench/EsportsBench lists this same person.
- Hodge2021 authors: Victoria J. Hodge, Sam M. Devlin, Nick J. Sephton, Florian O. Block, Peter I. Cowling, Anders Drachen — verified via IEEE Xplore at https://ieeexplore.ieee.org/document/8906016/ and the White Rose open-access PDF at https://eprints.whiterose.ac.uk/152931/. Volume 13, issue 4, pages 368–379. DOI `10.1109/TG.2019.2948469` correct in current bib.
- Bunker2024 authors (Rory Bunker, Calvin Yeung, Teo Susnjak, Chester Espie, Keisuke Fujii) verified via SAGE at https://journals.sagepub.com/doi/10.1177/17543371231212235. DOI `10.1177/17543371231212235` correct. Volume/issue/pages uncertain enough to justify NOT adding in TG4.
- Khan2024SCPhi2 pages: 2338–2352 per https://www.mdpi.com/2673-2688/5/4/115. Current bib has 2444–2462 — WRONG. DOI `10.3390/ai5040115`, volume 5, issue 4 correct.
- Tarassoli2024 is a phantom bib entry with fabricated author "Tarassoli, Saeid" for the same paper at Khan2024SCPhi2. `[REVIEW:]` at `03_related_work.md:69` explicitly flags it for removal "pending morning user review".
- Aligulac maintainer: Eivind Fonn (TheBB) — verified via https://github.com/TheBB GitHub user profile. Current bib "Kim, Espen and others" is unsupported.
- Elbert2025EC 5th author: Nikolai Stein (NOT Nora Stein); 2nd author: Alicia von Schenk (NOT Amadeus von Schenk). Verified via arXiv https://arxiv.org/abs/2506.04475 WebFetch metadata extraction.
- BaekKim2022 authors: Insung Baek and Seoung Bum Kim — verified via PLOS ONE canonical page and PubMed PMID 35239703. DOI `10.1371/journal.pone.0264550` correct.
- Glickman2001 DOI: `10.1080/02664760120059219` per Taylor & Francis (https://www.tandfonline.com/doi/abs/10.1080/02664760120059219). Verified.
- Lin2024NCT arXiv id: 2408.17180 per arXiv (https://arxiv.org/abs/2408.17180) and chapter prose at `01_introduction.md:93` and `03_related_work.md:141` that already references this identifier.
- CetinTas2023: author names, DOI, venue all correct in current bib — no fix required.
- GarciaMendez2025: currently cited via `[GarciaMendez2025]` bibkey in `01_introduction.md:11` but no `@article{GarciaMendez2025, ...}` entry exists in `thesis/references.bib`. Chapter-local References block at `01_introduction.md:81` contains the full citation (García-Méndez, S., & de Arriba-Pérez, F., Entertainment Computing, 55, 101027, DOI 10.1016/j.entcom.2025.101027) which can be promoted into the global bib.
- The ISO YYYY-MM-DD date format and em-dash "—" for ranges applies to any dates written in new bib notes or tracker prose.
- The 3-round adversarial cap applies to this plan's critique.

## Assumptions & unknowns

### Assumptions

- **Assumption (Hodge2021 coauthor list).** The coauthor order "Hodge, Devlin, Sephton, Block, Cowling, Drachen" matches IEEE Xplore. This is the authoritative order for the IEEE Transactions on Games publication. If the user has a preference for a different coauthor-ordering convention (e.g., shortened "Hodge et al."), the plan adopts IEEE Xplore's literal order by default.
- **Assumption (Bunker2024 pagination deferral).** Not adding volume/issue/pages in TG4 because WebSearch surfaced inconsistent "vol 12, page 17543371231212236" (SAGE online-first format, likely a placeholder). Adding wrong pagination is worse than omitting optional fields. Pass 2 may resolve definitively.
- **Assumption (Aligulac citation form).** Keeping year `2026` as an access-date proxy (consistent with other grey-lit entries: Liquipedia_GameSpeed, AoeCompanion, AoEStats). Author field changes to `{Fonn, Eivind and {Aligulac contributors}}` (Option c per Open Q 1 resolution: combined form names the attributable maintainer AND acknowledges collective authorship). The year field and all other fields are preserved verbatim.
- **Assumption (Tarassoli2024 deletion is safe).** Grep confirms no chapter file uses the bibkey `[Tarassoli2024]` — every SC-Phi2 citation already uses `[Khan2024SCPhi2]`. Deletion does not orphan any prose citation.
- **Assumption (Thorrez2024 bibkey preserved).** Per TG3 note (Open Q 2), the bibkey stays `Thorrez2024` even after the author first-name correction Lucas→Clayton. Alternative would be a destructive rename to `Thorrez2024Clayton` or similar, which would require updating every `[Thorrez2024]` citation in `01_introduction.md`, `02_theoretical_background.md`, `03_related_work.md`, `THESIS_STRUCTURE.md`, `06_discussion.md`, and `WRITING_STATUS.md` — high-risk destructive op, not justified when the error is purely first-name.
- **Assumption (GarciaMendez2025 promotion is BibTeX-resolution fix, not new content).** The citation exists in prose and is verified via DOI 10.1016/j.entcom.2025.101027 on ScienceDirect (https://www.sciencedirect.com/science/article/pii/S1875952125001077) and arXiv (https://arxiv.org/abs/2510.19671). Adding the `@article{GarciaMendez2025, ...}` entry into `references.bib` ensures consistency with the cross-chapter bibkey convention per `.claude/rules/thesis-writing.md` — the global bibliography must contain every inline-cited bibkey; absence at typesetting time would break BibTeX resolution. It is NOT a Pass-2 "new citation" because the reference is already approved and in use.

### Unknowns

- **Unknown — resolved by user decision before T01:** Whether Bunker2024 should receive optional volume/issue/pages (conservative: no) or whether SAGE's canonical pagination should be fetched for TG4. Planner default: omit volume/issue/pages; rely on DOI.
- **Resolved — Aligulac author attribution form (Open Q 1).** Adopt Option (c): `author = {Fonn, Eivind and {Aligulac contributors}}`. This was deferred to reviewer-adversarial Mode A and is now resolved: combined form names the attributable human maintainer (Eivind Fonn, TheBB on GitHub) AND acknowledges 15-year community-project collective authorship. T01 step 7 implements Option (c).
- **Unknown — deferred to Pass 2:** Whether `thesis/reviews_and_others/related_work_rating_systems.md:393` (listing "Thorrez, Calvin" — another variant of the same typo) should be harmonized. Planner recommendation: leave as-is; `reviews_and_others/` is not regenerated from bib, is a Pass-1 scratchpad, and is out of chapter scope. TG4 does not touch it.

## Literature context

- **[Thorrez2024]** — preprint, 20-title paired-comparison rating-systems benchmark; used in §2.5.5, §3.2.4, §3.5 as reference for EsportsBench. Author correction is the TG3 carry-over finding; bibkey stable.
- **[Hodge2021]** — IEEE Transactions on Games; peer-reviewed benchmark for LightGBM on Dota 2 live professional match prediction; coauthor list correction is a bibliography hygiene / pre-typesetting correction. Chapter prose at `01_introduction.md:67` and `03_related_work.md:93` already carries the correct author list; only the global bib entry is affected.
- **[Bunker2024]** — Proceedings of the Institution of Mechanical Engineers Part P; peer-reviewed Elo-vs-ML comparative study on tennis; verified metadata; no core fix required.
- **[BaekKim2022]** — PLOS ONE; 3D-ResNet on SC2 TvP; authors Insung Baek and Seoung Bum Kim (both first-name corrections); chapter prose already uses surname-only Polish declension, so propagation is limited to the References block of `01_introduction.md`.
- **[Elbert2025EC]** — ACM EC '25 proceedings; AoE2 team-player effect study; two first-name corrections (Alicia von Schenk, Nikolai Stein).
- **[Khan2024SCPhi2]** — AI (MDPI) journal; SC-Phi2 for SC2 build-order prediction; canonical pages 2338–2352 per MDPI journal metadata.
- **[Tarassoli2024]** — phantom bib entry for the same paper as Khan2024SCPhi2; scheduled for deletion.
- **[Aligulac]** — grey-literature citation for Aligulac project maintained by Eivind Fonn (TheBB); author attribution correction.
- **[Glickman2001]** — Journal of Applied Statistics; canonical Glicko-2 paper; DOI addition.
- **[Lin2024NCT]** — TMLR 2024; Bradley-Terry counter-relationship balance analysis on AoE2 + 3 other titles; arXiv id addition.
- **[CetinTas2023]** — UBMK 2023 IEEE conference; NB + DT on AoE2 DE; verified metadata; no fix required.
- **[GarciaMendez2025]** — Entertainment Computing 2025; explainable ML streaming e-sports win prediction; currently cited via bibkey but absent from bib; promotion ensures consistency with the cross-chapter bibkey convention per `.claude/rules/thesis-writing.md` (`Citations: [AuthorYear] keys in thesis/references.bib`) — the global bibliography must contain every inline-cited bibkey; absence at typesetting time would break BibTeX resolution.
- [OPINION] — TG4's approach of one-PR-for-11-bibkey-fixes is safe because no finding requires a bibkey rename, no chapter prose propagation exceeds three lines, and the fixes are mechanically isolated to `references.bib`. If TG5 or TG6 reveal additional bib entries needing correction, they become separate-PR items per dispatch discipline.

## Pre-flight (branch-creation operation, not a numbered task)

Per git-workflow atomicity, the branch-creation purge is split into three commits before content work begins:

- **Commit A** — `chore(planning): purge artifacts from merged PR #189 (TG3)` — deletes the TG3 `planning/current_plan.md` + `planning/current_plan.critique.md` inherited from master after the TG3 merge.
- **Commit B** — `chore(planning): seed TG4 plan (eleven bibliography findings audit and fixes)` — writes this TG4 plan to `planning/current_plan.md`.
- **Commit C** — `chore(planning): seed TG4 plan critique (reviewer-adversarial Mode A)` — writes `planning/current_plan.critique.md` after Mode A runs.

These commits establish the planning state before T01 begins.

## Execution Steps

Task sequencing T01 → T02 → T03 guarantees no concurrent edits to shared tracker files. Writer-thesis must re-read shared files immediately before each edit.

### T01 — Apply eleven bibliography corrections to `thesis/references.bib`

**Objective:** apply all eleven bibkey-level corrections in one atomic commit to `thesis/references.bib`. Scope is strictly the bib file; chapter prose changes are deferred to T02.

**Instructions:**

1. Re-read `thesis/references.bib` lines 30–60, 69–87, 110–118, 147–162, 243–249, 406–416, 452–458 to confirm current state matches the pre-flight facts above.

2. **Tarassoli2024 deletion.** Delete lines 50–55 entirely (`@article{Tarassoli2024, ...}`). This entry is a phantom; the real paper is at `Khan2024SCPhi2`.

3. **Thorrez2024 author correction + URL + note extension.** At `references.bib:148`, change `author = {Thorrez, Lucas}` to `author = {Thorrez, Clayton}`. Add `url = {https://huggingface.co/datasets/EsportsBench/EsportsBench}` on a new line before the closing `}` (canonical public-facing artifact per URL-selection rule: preprint PDF cannot be decoded to verify title match, so the HuggingFace dataset page is the default). Also extend the `note` field: the current note is "Evaluated 11 rating systems across 20 esports titles"; append to it (or replace with combined form): `note = {Evaluated 11 rating systems across 20 esports titles. Title reflects preprint front matter; HuggingFace dataset page uses subtitle 'A Collection of Datasets for Benchmarking Rating Systems in Esports'.}` — this documents the title variance between bib entry ("Rating System Evaluation for Esports") and the HuggingFace page title, closing the disagreement surface flagged in Open Q 3.

4. **Hodge2021 author correction + metadata completion.** At `references.bib:60`, replace `author = {Hodge, Victoria J. and Sherkat, Sam and Sherkat, Ehsan and others}` with `author = {Hodge, Victoria J. and Devlin, Sam M. and Sephton, Nick J. and Block, Florian O. and Cowling, Peter I. and Drachen, Anders}`. Add `volume = {13}`, `number = {4}`, `pages = {368--379}` (three new fields; preserve existing journal, DOI, year, bibkey).

5. **BaekKim2022 author correction.** At `references.bib:33`, change `author = {Baek, Jihun and Kim, Jinyoung}` to `author = {Baek, Insung and Kim, Seoung Bum}`. Preserve all other fields.

6. **Khan2024SCPhi2 pages correction + note cleanup.** At `references.bib:413`, change `pages = {2444--2462}` to `pages = {2338--2352}`. Replace the verbose note `note = {Preprint version: arXiv:2409.18989. NOTE: existing bib entry Tarassoli2024 is a misattribution of this same paper; user to reconcile in morning.}` with the terse form `note = {Preprint version: arXiv:2409.18989}`. Preserve all other fields.

7. **Aligulac author correction.** At `references.bib:157`, change `author = {Kim, Espen and others}` to `author = {Fonn, Eivind and {Aligulac contributors}}` (Option c per Open Q 1 resolution: names the attributable human maintainer AND acknowledges community-project collective authorship). Preserve title, howpublished, note, year verbatim.

8. **Elbert2025EC two first-name corrections.** At `references.bib:79`, change `author = {Elbert, Nico and von Schenk, Amadeus and Kosse, Fabian and Klockmann, Victor and Stein, Nora and Flath, Christoph}` to `author = {Elbert, Nico and von Schenk, Alicia and Kosse, Fabian and Klockmann, Victor and Stein, Nikolai and Flath, Christoph}`. Preserve all other fields.

9. **Glickman2001 DOI addition.** At `references.bib:117`, before the closing `}`, add `doi = {10.1080/02664760120059219}` on a new line.

10. **Lin2024NCT arXiv URL addition + author-name fix.** At `references.bib:248`, before the closing `}`, add `url = {https://arxiv.org/abs/2408.17180}` on a new line. Additionally, in the same entry's `author` field change `Shih, Yi-Wei` to `Shih, Yu-Wei` (latent typo surfaced during /critic empirical verification; arXiv:2408.17180 HTML names the author "Yu-Wei Shih", email yoway0430@gmail.com).

11. **GarciaMendez2025 new entry insertion.** At an appropriate location in the bib (end of the "Additions for §1.3" section or as a new section "Additions for §1.1 — esports streaming prediction"), insert:

    ```bibtex
    @article{GarciaMendez2025,
      author  = {Garc{\'i}a-M{\'e}ndez, Silvia and de Arriba-P{\'e}rez, Francisco},
      title   = {Explainable e-sports win prediction through Machine Learning classification in streaming},
      journal = {Entertainment Computing},
      year    = {2025},
      volume  = {55},
      pages   = {101027},
      doi     = {10.1016/j.entcom.2025.101027},
      url     = {https://arxiv.org/abs/2510.19671}
    }
    ```

12. Verify no other bib entries were modified inadvertently. Diff `thesis/references.bib` against master and confirm exactly 11 distinct change-regions (10 edits + 1 insertion; Tarassoli2024 deletion counts as part of the Khan2024SCPhi2 reconciliation batch).

13. Run the writer-thesis Critical Review Checklist (Literature variant):
    - Citation accuracy: every corrected field matches the verified canonical source.
    - Claim-citation alignment: GarciaMendez2025 promotion does not change any claim; existing prose citations remain correctly anchored.
    - Scope honesty: TG4 does not rename bibkeys and does not introduce new citations beyond BibTeX-resolution fixes (GarciaMendez2025 was already cited in prose).
    - Missing context flags: no new `[REVIEW:]` flags planted; one existing flag is removed in T02.

**Verification:**

- `grep -nF "Thorrez, Lucas" thesis/references.bib` returns zero hits (Thorrez correction applied).
- `grep -nF "Thorrez, Clayton" thesis/references.bib` returns exactly one hit.
- `grep -nF "Sherkat, Sam" thesis/references.bib` returns zero hits (fabricated Hodge coauthors removed).
- `grep -nF "Devlin, Sam M." thesis/references.bib` returns exactly one hit.
- `grep -nF "Sephton, Nick J." thesis/references.bib` returns exactly one hit.
- `grep -nF "Drachen, Anders" thesis/references.bib` returns exactly one hit.
- `grep -nF "Baek, Jihun" thesis/references.bib` returns zero hits.
- `grep -nF "Baek, Insung" thesis/references.bib` returns exactly one hit.
- `grep -nF "Kim, Seoung Bum" thesis/references.bib` returns exactly one hit.
- `grep -nF "2338--2352" thesis/references.bib` returns exactly one hit (Khan2024SCPhi2 canonical pages).
- `grep -nF "2444--2462" thesis/references.bib` returns zero hits.
- `grep -nF "@article{Tarassoli2024" thesis/references.bib` returns zero hits (phantom deleted).
- `grep -nF "Kim, Espen" thesis/references.bib` returns zero hits.
- `grep -nF "Fonn, Eivind" thesis/references.bib` returns exactly one hit (Option c combined form: `Fonn, Eivind and {Aligulac contributors}`).
- `grep -nF "Schenk, Amadeus" thesis/references.bib` returns zero hits.
- `grep -nF "Schenk, Alicia" thesis/references.bib` returns exactly one hit.
- `grep -nF "Stein, Nora" thesis/references.bib` returns zero hits.
- `grep -nF "Stein, Nikolai" thesis/references.bib` returns exactly one hit.
- `grep -nF "10.1080/02664760120059219" thesis/references.bib` returns exactly one hit (Glickman2001 DOI).
- `grep -nF "arxiv.org/abs/2408.17180" thesis/references.bib` returns exactly one hit (Lin2024NCT URL).
- `grep -nF "Shih, Yu-Wei" thesis/references.bib` returns exactly one hit (Lin2024NCT corrected author).
- `grep -nF "Shih, Yi-Wei" thesis/references.bib` returns zero hits.
- `grep -nF "@article{GarciaMendez2025" thesis/references.bib` returns exactly one hit (new entry present).
- `grep -nF "10.1016/j.entcom.2025.101027" thesis/references.bib` returns exactly one hit.
- `grep -cF "@" thesis/references.bib` returns a value equal to `(pre-edit count) + 1 - 1` (GarciaMendez2025 added, Tarassoli2024 removed, net zero change in entry count). Absolute value TBD; compute before/after to verify the single-line arithmetic.

**File scope:**
- `thesis/references.bib`

**Read scope:**
- (none — T01 edits one file in isolation)

---

### T02 — Propagate corrections to chapter prose and remove one `[REVIEW:]` flag

**Objective:** apply the two chapter-prose one-line updates and the one `[REVIEW:]` flag removal that the T01 bib corrections necessitate. Scope is strictly three chapter files with two prose updates and one flag deletion.

**Instructions:**

1. Read `thesis/chapters/01_introduction.md:65–75`, `thesis/chapters/03_related_work.md:66–72`, and `thesis/THESIS_STRUCTURE.md:146–150` to confirm exact current prose.

2. **`thesis/chapters/01_introduction.md` — `[Baek2022]` → `[BaekKim2022]` bibkey harmonisation.** `01_introduction.md:13`, `:25`, and `:69` use `[Baek2022]` but the global `references.bib` entry uses the key `BaekKim2022`, and `03_related_work.md` (lines 65, 117, 135, 137, 183, 191) already uses `[BaekKim2022]` consistently. To harmonise, change `[Baek2022]` to `[BaekKim2022]` at all three occurrences in `01_introduction.md` (line 13 first inline citation, line 25 second inline citation, and line 69 References block entry). Do NOT change the prose initials at this step — that is handled in step 3.

3. **`thesis/chapters/01_introduction.md:69` — Baek initials.** After the bibkey harmonisation above, locate the now-updated References block line `- [BaekKim2022] Baek, J., & Kim, S. (2022). 3-Dimensional convolutional neural networks for predicting StarCraft II results and extracting key game situations. PLOS ONE, 17(3), e0264550.`. Replace `Baek, J., & Kim, S.` with `Baek, I., & Kim, S. B.`. Result: `- [BaekKim2022] Baek, I., & Kim, S. B. (2022). 3-Dimensional convolutional neural networks for predicting StarCraft II results and extracting key game situations. PLOS ONE, 17(3), e0264550.`

4. **`thesis/chapters/03_related_work.md:69` — Tarassoli flag removal.** Locate the inline `[REVIEW: Tarassoli2024 w references.bib (lines 50-55) jest błędną atrybucją tej samej pracy — należy usunąć stary wpis i zachować wyłącznie Khan2024SCPhi2; deferowane do morning user review per autonomous-mode]` flag. Delete this flag entirely (including the square brackets). Preserve the preceding `[REVIEW: pełna ewaluacja SC-Phi2 wymaga sięgnięcia do wersji opublikowanej w MDPI AI (listopad 2024) zamiast preprintu arXiv (wrzesień 2024); konieczne wcielenie konkretnych liczb przed finalizacją]` flag unchanged.

5. **`thesis/THESIS_STRUCTURE.md:148` — Tarassoli to Khan2024SCPhi2 citation correction.** Locate the line `- Tarassoli et al. (2024): fine-tuned Phi-2 for build order prediction`. Replace `Tarassoli et al. (2024)` with `Khan & Sukthankar (2024)`. Result: `- Khan & Sukthankar (2024): fine-tuned Phi-2 for build order prediction`.

6. Verify no other chapter prose references "Tarassoli" (bibkey or surname) by `grep -rnF "Tarassoli" thesis/chapters/ thesis/THESIS_STRUCTURE.md thesis/WRITING_STATUS.md thesis/chapters/REVIEW_QUEUE.md` — expected zero hits after this task.

6a. **Confirm `THESIS_STRUCTURE.md:149` does NOT require update.** Line 149 reads "EsportsBench (Thorrez 2024): Glicko-2 at 80.13% on Aligulac SC2 data". The surname "Thorrez" is correct; the first name "Clayton" (corrected from "Lucas" in T01 step 3) is not expanded in this meta-doc entry. No edit needed; this step is a verification-only checkpoint.

7. Verify no other chapter prose references "Baek, J." as initials by `grep -rnE "Baek,?\\s?J\\." thesis/chapters/` — expected zero hits (confirming the fix is comprehensive and no siblings use the wrong initials).

8. Verify bibkey harmonisation: `grep -nF "[Baek2022]" thesis/chapters/01_introduction.md` returns zero hits (all three occurrences at lines 13, 25, and 69 replaced with `[BaekKim2022]`).

9. Run the writer-thesis Critical Review Checklist (Literature variant) on the updated sites:
   - Citation accuracy: Baek initials match PLOS ONE canonical (I., S. B.). Khan & Sukthankar attribution matches MDPI canonical. `[BaekKim2022]` bibkey matches global `references.bib` entry.
   - Claim-citation alignment: no edit changes any claim; only attribution and bibkey form are corrected.
   - Scope honesty: the edits are pure surface corrections, not content revisions.
   - Missing context flags: no new flags; one flag removed per T02.4.

**Verification:**

- `grep -nF "[Baek2022]" thesis/chapters/01_introduction.md` returns zero hits (all three occurrences at lines 13, 25, and 69 harmonised to `[BaekKim2022]`).
- `grep -nF "[BaekKim2022]" thesis/chapters/01_introduction.md` returns exactly three hits (line 13 first inline citation, line 25 second inline citation, and line 69 References block entry).
- `grep -nF "Baek, J." thesis/chapters/01_introduction.md` returns zero hits.
- `grep -nF "Baek, I." thesis/chapters/01_introduction.md` returns exactly one hit (at line 69).
- `grep -nF "Kim, S. B." thesis/chapters/01_introduction.md` returns exactly one hit.
- `grep -nF "Tarassoli" thesis/chapters/03_related_work.md` returns zero hits.
- `grep -nF "Tarassoli" thesis/THESIS_STRUCTURE.md` returns zero hits.
- `grep -nF "Khan & Sukthankar (2024)" thesis/THESIS_STRUCTURE.md` returns exactly one hit.
- `grep -nF "[REVIEW: Tarassoli2024" thesis/chapters/03_related_work.md` returns zero hits.
- `grep -nE "pełna ewaluacja SC-Phi2" thesis/chapters/03_related_work.md` returns exactly one hit (the other `[REVIEW:]` flag preserved).

**File scope:**
- `thesis/chapters/01_introduction.md`
- `thesis/chapters/03_related_work.md`
- `thesis/THESIS_STRUCTURE.md`

**Read scope:**
- `thesis/references.bib` (for T01 consistency — writer-thesis must confirm the bib changes land cleanly before propagating flag resolutions)

---

### T03 — Update WRITING_STATUS.md and REVIEW_QUEUE.md tracker entries

**Objective:** record TG4 revisions in the two trackers so the Pass 2 workflow state reflects the eleven bib corrections and the two prose propagations.

**Instructions:**

1. **WRITING_STATUS.md.** Append PR-TG4 notes to the affected sections:

   - §1.1 Motywacja (or wherever GarciaMendez2025 is first cited — line 35 per grep results): append `**2026-04-20 (PR-TG4): §1.1 bibliography reference for `[GarciaMendez2025]` promoted into global `thesis/references.bib` as `@article{GarciaMendez2025, ...}` per Pass-2 TG4 dispatch (previously cited by bibkey in prose but absent from global bib; absence at typesetting time would break BibTeX resolution — consistency with cross-chapter bibkey convention per `.claude/rules/thesis-writing.md`). Metadata per ScienceDirect (DOI 10.1016/j.entcom.2025.101027) and arXiv (2510.19671).**`
   - §1.3 Research questions: append `**2026-04-20 (PR-TG4): §1.3 Baek inline citations and References block entry updated: bibkey harmonised from `[Baek2022]` to `[BaekKim2022]` at three occurrences (lines 13, 25, and 69 — line 13 first inline citation, line 25 second inline citation, line 69 References block entry; to match global `references.bib` entry `BaekKim2022` and `03_related_work.md` usage); initials corrected from 'Baek, J., & Kim, S.' to 'Baek, I., & Kim, S. B.' per Pass-2 TG4 dispatch (PLOS ONE canonical: Insung Baek and Seoung Bum Kim). `thesis/references.bib` `BaekKim2022` entry author field corrected in the same PR.**`
   - §2.5 Player skill rating systems: append `**2026-04-20 (PR-TG4): §2.5.4 Aligulac author attribution in `thesis/references.bib` corrected from 'Kim, Espen and others' to 'Fonn, Eivind' per Pass-2 TG4 dispatch (GitHub profile TheBB = Eivind Fonn verified). `[Aligulac]` bibkey unchanged; no prose propagation.**`
   - §3.2 StarCraft prediction literature: append `**2026-04-20 (PR-TG4): §3.2.3 SC-Phi2 citation cleanup — `Tarassoli2024` phantom bib entry (fabricated attribution to 'Saeid Tarassoli') deleted from `thesis/references.bib`; `Khan2024SCPhi2` pages corrected from 2444–2462 to 2338–2352 (MDPI canonical) and note field cleaned to remove TG3-era reconciliation instruction. `[REVIEW: Tarassoli2024 misattribution]` inline flag at `03_related_work.md:69` resolved and removed. `[Hodge2021]` coauthors corrected from fabricated 'Sherkat, Sam and Sherkat, Ehsan' to canonical IEEE Xplore list (Devlin, Sephton, Block, Cowling, Drachen); volume/issue/pages (13/4/368-379) added. Chapter prose at `03_related_work.md:93` and `01_introduction.md:67` already uses canonical author list and is unaffected by bib correction. `THESIS_STRUCTURE.md:148` 'Tarassoli et al. (2024)' line updated to 'Khan & Sukthankar (2024)'.**`
   - §3.4 AoE2 prediction: append `**2026-04-20 (PR-TG4): §3.4.3 Elbert2025EC author first-name corrections applied in `thesis/references.bib` — 'Schenk, Amadeus' → 'Schenk, Alicia' and 'Stein, Nora' → 'Stein, Nikolai' per Pass-2 TG4 dispatch (arXiv:2506.04475 verified). Polish chapter prose uses surname-only declension and is unaffected. `[CetinTas2023]` verified correct — no fix.**`
   - §3.5 Research gap (if different from the §3.4 block): append as part of the same PR-TG4 note block or skip if redundant.

2. Additional entries per bibkey touch (Glickman2001 DOI, Lin2024NCT arXiv URL + Shih author-name fix, Thorrez2024 author correction) are consolidated under §2.5 and §3.0/§3.5 umbrella notes so WRITING_STATUS.md doesn't accumulate one row per bib fix. Consolidation format: mention in the umbrella section's PR-TG4 note that `Glickman2001 DOI (10.1080/02664760120059219) added; Lin2024NCT arXiv URL added + author "Shih, Yi-Wei" corrected to "Shih, Yu-Wei" (latent typo, surfaced by /critic); Thorrez2024 author corrected (Lucas → Clayton) + HuggingFace dataset URL added`. Also note the `[Baek2022]` → `[BaekKim2022]` bibkey harmonisation in `01_introduction.md` (lines 13, 25, and 69 — three occurrences) under the §1.3 PR-TG4 note.

3. **REVIEW_QUEUE.md.** Two entries updated / added:

   - Row for §3.2.3 SC-Phi2 (if present in the queue — look for `Tarassoli2024` or `Khan2024SCPhi2` or `[REVIEW: Tarassoli2024]` string): append `**RESOLVED 2026-04-20 (PR-TG4): Tarassoli2024 phantom bib entry deleted; Khan2024SCPhi2 metadata corrected; inline `[REVIEW:]` flag at `03_related_work.md:69` removed. Remaining Pass 2 question: verify SC-Phi2 MDPI exact trafność values (still pending; `[REVIEW: pełna ewaluacja SC-Phi2]` flag at `03_related_work.md:69` preserved as a separate Pass 2 verification item).**`

   - **New Pass 2 entry (triple-divergent Thorrez first-name).** Add a new row at `REVIEW_QUEUE.md` §2.5 row or §3.2 row (whichever exists; append if both): `Triple-divergence of Thorrez first-name across repo: references.bib now canonical "Clayton" (PR-TG4); \`reviews_and_others/related_work_rating_systems.md:393\` carries "Calvin" (scratchpad, out of chapter scope; regenerated in future refactor); previously "Lucas" in pre-TG4 bib (deleted). Pass 2 chore: verify final "Clayton" is correct when scratchpad is regenerated.` Note: the scratchpad file `reviews_and_others/related_work_rating_systems.md` is NOT edited by TG4 (out of scope); this REVIEW_QUEUE entry is a documentation action only.

4. Verify ISO date format and em-dash usage in the new notes.

**Verification:**

- `grep -cF "PR-TG4" thesis/WRITING_STATUS.md` returns a value between 4 and 6 (one per affected section; the exact count is flexible based on consolidation in instruction 2).
- `grep -cF "2026-04-20 (PR-TG4)" thesis/chapters/REVIEW_QUEUE.md` returns exactly 1 (the SC-Phi2 row update).
- `grep -nF "RESOLVED 2026-04-20 (PR-TG4)" thesis/chapters/REVIEW_QUEUE.md` returns exactly 1 hit.

**File scope:**
- `thesis/WRITING_STATUS.md`
- `thesis/chapters/REVIEW_QUEUE.md`

**Read scope:**
- `thesis/references.bib` (to confirm T01 changes landed)
- `thesis/chapters/01_introduction.md`
- `thesis/chapters/03_related_work.md`
- `thesis/THESIS_STRUCTURE.md`

## File Manifest

| File | Action |
|------|--------|
| `planning/current_plan.md` | Rewrite (TG4 plan) |
| `planning/current_plan.critique.md` | Rewrite (reviewer-adversarial Mode A critique) |
| `thesis/references.bib` | Update (12 bibkey corrections: 10 edits + 1 new entry + 1 deletion; 11 original findings + 1 latent Shih author-name fix) |
| `thesis/chapters/01_introduction.md` | Update (Baek initials in References block, line 69) |
| `thesis/chapters/03_related_work.md` | Update ([REVIEW: Tarassoli2024] flag removal, line 69) |
| `thesis/THESIS_STRUCTURE.md` | Update (Tarassoli → Khan & Sukthankar, line 148) |
| `thesis/WRITING_STATUS.md` | Update (4–6 PR-TG4 notes) |
| `thesis/chapters/REVIEW_QUEUE.md` | Update (1 SC-Phi2 row resolution) |

## Gate Condition

- `grep -nF "Thorrez, Lucas" thesis/references.bib` returns zero hits.
- `grep -nF "Sherkat" thesis/references.bib` returns zero hits.
- `grep -nF "Baek, Jihun" thesis/references.bib` returns zero hits.
- `grep -nF "Kim, Jinyoung" thesis/references.bib` returns zero hits.
- `grep -nF "@article{Tarassoli2024" thesis/references.bib` returns zero hits.
- `grep -nF "2444--2462" thesis/references.bib` returns zero hits.
- `grep -nF "Kim, Espen" thesis/references.bib` returns zero hits.
- `grep -nF "Schenk, Amadeus" thesis/references.bib` returns zero hits.
- `grep -nF "Stein, Nora" thesis/references.bib` returns zero hits.
- `grep -nF "@article{GarciaMendez2025" thesis/references.bib` returns exactly one hit.
- `grep -nF "10.1080/02664760120059219" thesis/references.bib` returns exactly one hit.
- `grep -nF "2408.17180" thesis/references.bib` returns exactly one hit (Lin2024NCT URL).
- `grep -nF "Shih, Yu-Wei" thesis/references.bib` returns exactly one hit.
- `grep -nF "Shih, Yi-Wei" thesis/references.bib` returns zero hits.
- `grep -nF "[Baek2022]" thesis/chapters/01_introduction.md` returns zero hits (all three occurrences at lines 13, 25, and 69 harmonised to `[BaekKim2022]`).
- `grep -nF "Baek, J." thesis/chapters/01_introduction.md` returns zero hits.
- `grep -nF "Tarassoli" thesis/chapters/ thesis/THESIS_STRUCTURE.md` returns zero hits.
- `grep -nF "Khan & Sukthankar (2024)" thesis/THESIS_STRUCTURE.md` returns exactly one hit.
- `grep -nF "[REVIEW: Tarassoli2024" thesis/chapters/03_related_work.md` returns zero hits.
- `grep -cF "PR-TG4" thesis/WRITING_STATUS.md` returns a value in [4, 6].
- `grep -cF "2026-04-20 (PR-TG4)" thesis/chapters/REVIEW_QUEUE.md` returns exactly 1.
- ISO YYYY-MM-DD format preserved in all new prose.
- Pre-commit hooks pass (ruff, mypy, markdown linting). No test coverage impact (prose + bib only).
- PR body generated from `.github/pull_request_template.md`; Summary lists the 11 bibliography findings and the two prose propagations.

## Rollback plan

If reviewer-adversarial Mode A flags a BLOCKER (e.g., an author attribution correction is disputed, or the Tarassoli2024 deletion is judged unsafe because of a non-chapter file reference), PAUSE execution and notify the user. Propose `git reset --hard origin/master` for explicit user confirmation before executing — do NOT autonomously rollback. If only WARNING or MINOR is raised, apply the surgical fix on the same branch and re-run the Gate Condition checks; do not ship PR-TG4 until the critique converges.

If TG4 lands but TG5 or TG6 later discovers a 12th bibliography finding not captured here, the plan does NOT expand retroactively — the new finding becomes a separate PR per dispatch discipline (one task group = one PR).

**Degradation-mode fallback for Hodge2021 coauthor-order disputes.** If a reviewer claims the IEEE Xplore coauthor order differs from what is proposed (e.g., insists on "Devlin, Sephton, Block" vs "Sephton, Devlin, Block"), verify against the PDF download from https://eprints.whiterose.ac.uk/id/eprint/152931/1/Win_Prediction_in_Multi_Player_Esports_Live_Professional_Match_Prediction.pdf (authoritative authors-on-title-page source). Adjust one-line and re-run.

## Out of scope

- **TG5** — 6 internal-consistency fixes. Separate PR.
- **TG6** — 12 prophylactic/hygiene fixes. Separate PR.
- **Bibkey renames.** No bibkey is renamed in TG4 (Thorrez2024 stays, BaekKim2022 stays, Khan2024SCPhi2 stays). Renaming would be destructive and requires a separate, explicitly-scoped PR.
- **`thesis/reviews_and_others/related_work_rating_systems.md:393`** (which lists "Thorrez, Calvin") — out of chapter scope; Pass-1 scratchpad; not regenerated from bib.
- **`thesis/plans/writing_protocol.md`** (if it cites Thorrez2024 anywhere) — out of chapter scope.
- **Bunker2024 volume/issue/pages.** Deferred because WebSearch surfaced inconsistent pagination. Pass 2 may resolve.
- **Thorrez2024 canonical title.** The HuggingFace dataset title is "A Collection of Datasets for Benchmarking Rating Systems" but the preprint PDF front matter (which WebFetch could not decode) may have a different title. TG4 preserves the current bib title "EsportsBench: Rating System Evaluation for Esports" as a defensible paraphrase; exact title verification is Pass 2 work pending preprint PDF text extraction.
- **Khan2024SCPhi2 and Tarassoli2024 mirror entries in `reviews_and_others/related_work_historical_rts_prediction.md`** (if any) — out of chapter scope.
- **`.claude/scientific-invariants.md`** — not touched.
- **EsportsBench v9.0+ version monitoring** — preserved from TG3's `[REVIEW:]` flag.
- **`01_introduction.md:81` local References block.** The inline reference entry is correct per WebSearch-verified metadata; the global bib is the one that needed a new entry. Do not duplicate the prose-local entry with a new prose-local edit — only add to global bib.

## Open questions

- **Open Q 1 (Aligulac citation form — RESOLVED: Option c).** Aligulac has no canonical academic author. Adopt `author = {Fonn, Eivind and {Aligulac contributors}}` — names the attributable human maintainer (Eivind Fonn, TheBB on GitHub) AND acknowledges 15-year community-project collective authorship. Option (a) `{Fonn, Eivind}` alone is thin at defense; Option (b) `{{Aligulac contributors}}` alone loses the attributable maintainer. Combined form mirrors academic practice for citing community projects with identifiable leads. **Resolves by:** T01 step 7 update — change author field to `author = {Fonn, Eivind and {Aligulac contributors}}`.
- **Open Q 2 (Bunker2024 pagination completion).** Whether to add volume/issue/pages in TG4 (higher-risk) or defer to Pass 2 (conservative). Planner default: defer. **Resolves by:** user decision before T01 begins.
- **Open Q 3 (Thorrez2024 canonical URL and title).** URL-selection rule: since the preprint PDF cannot be decoded to verify the title match, default to the HuggingFace dataset page (https://huggingface.co/datasets/EsportsBench/EsportsBench) as the canonical public-facing artifact. This is what T01 step 3 adds as the `url` field. For the title: "EsportsBench: Rating System Evaluation for Esports" (current bib) vs "A Collection of Datasets for Benchmarking Rating Systems" (HuggingFace page title). Planner default: preserve current bib title pending preprint PDF text extraction. **Resolves by:** Pass 2 manual preprint PDF read.
- **Open Q 4 (GarciaMendez2025 promotion — Pass-2 vs TG4 scope debate).** Whether promoting GarciaMendez2025 from prose-inline-only to global-bib is within TG4's stated scope (11 bibliography findings) or a separate TG scope. Planner recommendation: include in TG4 because the eleven-finding count already implicitly included the missing-entry bug (it is a bibliography finding by any reasonable interpretation). If user disagrees, relegate to a 12th TG4 task or defer to TG6 (prophylactic/hygiene). **Resolves by:** user confirmation before T01 begins.
- **Open Q 5 (Hodge2021 author-name style — RESOLVED).** Adopt full first names ('Hodge, Victoria J. and Devlin, Sam M. and Sephton, Nick J. and Block, Florian O. and Cowling, Peter I. and Drachen, Anders') to match IEEE Xplore canonical form and the Bunker2024 pattern already in the bib ('Bunker, Rory and Yeung, Calvin and ...'). Chapter prose at `01_introduction.md:67` uses initials-compact form ('Hodge, V. J., Devlin, S. M., ...') — stylistic asymmetry between bib full-names and prose initials is intentional: BibTeX renderer rationalizes at typesetting time. **Resolves by:** T01 step 4 default (already implements full first names).
- **Open Q 6 (Elbert2025EC booktitle string stability).** Whether "Proceedings of the 26th ACM Conference on Economics and Computation (EC '25)" should remain as current bib or be harmonized with ACM DL canonical format. Planner default: preserve current form as it matches dispatch expectations. **Resolves by:** no change in TG4.

## Adversarial critique triggers

The parent session must, after planner returns this plan, dispatch reviewer-adversarial Mode A to produce `planning/current_plan.critique.md`. Triggers for Mode A to look at specifically:

- Whether the eleven findings map cleanly to the TG1 Out-of-Scope enumeration (García-Méndez, Hodge, Bunker, SC-Phi2, Aligulac, Elbert, EsportsBench, Baek, Glickman, Lin, Çetin Taş) plus the TG3 Thorrez carry-over.
- Whether the Hodge2021 fabrication (Sherkat coauthors) is truly a fabrication or whether it represents a different publication that happens to share the same DOI.
- Whether the Tarassoli2024 deletion is safe (grep confirms zero bibkey uses; but any non-chapter file referenced in the compile pipeline?).
- Whether ISO YYYY-MM-DD dates and em-dash formatting are preserved in all new prose.
- Whether the Aligulac author attribution Fonn/TheBB is defensible as a grey-literature citation.
- Whether the scope-boundary between TG4 and TG5 is tight (i.e., nothing in TG4 constitutes an "internal-consistency fix" per TG5 scope).
- Whether the Khan2024SCPhi2 page-range correction (2444 → 2338) is strongly supported by both MDPI WebSearch hits independently.
- Whether GarciaMendez2025 promotion is within-scope or Pass-2-overflow.

> For Category A or F, adversarial critique is required before execution. Dispatch reviewer-adversarial to produce `planning/current_plan.critique.md`.

---

Sources:

- [García-Méndez & de Arriba-Pérez (2025) paper on ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1875952125001077)
- [García-Méndez & de Arriba-Pérez (2025) arXiv preprint](https://arxiv.org/abs/2510.19671)
- [Hodge et al. (2021) IEEE Xplore](https://ieeexplore.ieee.org/document/8906016/)
- [Hodge et al. (2021) White Rose open-access PDF](https://eprints.whiterose.ac.uk/id/eprint/152931/1/Win_Prediction_in_Multi_Player_Esports_Live_Professional_Match_Prediction.pdf)
- [Bunker et al. (2024) SAGE canonical page](https://journals.sagepub.com/doi/10.1177/17543371231212235)
- [Khan & Sukthankar (2024) SC-Phi2 MDPI AI](https://www.mdpi.com/2673-2688/5/4/115)
- [Khan & Sukthankar (2024) SC-Phi2 arXiv](https://arxiv.org/abs/2409.18989)
- [Aligulac GitHub repository](https://github.com/TheBB/aligulac)
- [TheBB (Eivind Fonn) GitHub profile](https://github.com/TheBB)
- [Elbert et al. (2025) arXiv:2506.04475](https://arxiv.org/abs/2506.04475)
- [EsportsBench HuggingFace dataset](https://huggingface.co/datasets/EsportsBench/EsportsBench)
- [Clayton Thorrez personal page](https://cthorrez.github.io/)
- [Baek & Kim (2022) PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0264550)
- [Baek & Kim (2022) PubMed](https://pubmed.ncbi.nlm.nih.gov/35239703/)
- [Glickman (2001) Taylor & Francis](https://www.tandfonline.com/doi/abs/10.1080/02664760120059219)
- [Lin et al. (2024) arXiv:2408.17180](https://arxiv.org/abs/2408.17180)
- [Lin et al. (2024) OpenReview TMLR](https://openreview.net/forum?id=2D36otXvBE)
- [Çetin Taş & Müngen (2023) ResearchGate](https://www.researchgate.net/publication/377541570)

---

## Summary

**Plan ready for approval.** Eleven bibliography findings verified against WebSearch / WebFetch of canonical sources; zero findings require bibkey renames; two chapter-prose propagation points (Baek initials in `01_introduction.md:69`, Tarassoli→Khan attribution in `THESIS_STRUCTURE.md:148`); one `[REVIEW:]` flag removal (`03_related_work.md:69`). One PR is recommended — the fixes are mechanically isolated to `references.bib` with a thin propagation layer.

**Critique gate.** For Category F, adversarial critique is required before execution. After this plan lands in `planning/current_plan.md`, dispatch reviewer-adversarial Mode A to produce `planning/current_plan.critique.md`. I have flagged eight critique triggers above that Mode A should specifically examine, with particular priority on the Hodge2021 fabrication and the Tarassoli2024 deletion safety.

**Next steps (user decision required before T01):**
1. Approve plan contents → parent writes to `planning/current_plan.md`.
2. Resolve Open Q 2 (Bunker2024 pagination, default: defer) and Open Q 4 (GarciaMendez2025 scope, default: include in TG4).
3. Dispatch reviewer-adversarial Mode A.

Sources:
- [García-Méndez & de Arriba-Pérez (2025) ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1875952125001077)
- [Hodge et al. (2021) IEEE Xplore](https://ieeexplore.ieee.org/document/8906016/)
- [Khan & Sukthankar (2024) SC-Phi2 MDPI AI](https://www.mdpi.com/2673-2688/5/4/115)
- [Aligulac GitHub — TheBB = Eivind Fonn](https://github.com/TheBB)
- [Elbert et al. (2025) arXiv:2506.04475](https://arxiv.org/abs/2506.04475)
- [Baek & Kim (2022) PLOS ONE canonical](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0264550)
- [Glickman (2001) Taylor & Francis DOI resolution](https://www.tandfonline.com/doi/abs/10.1080/02664760120059219)
- [EsportsBench dataset at HuggingFace](https://huggingface.co/datasets/EsportsBench/EsportsBench)
- [Clayton Thorrez personal page](https://cthorrez.github.io/)
- [Lin et al. (2024) arXiv:2408.17180](https://arxiv.org/abs/2408.17180)
- [Bunker et al. (2024) SAGE](https://journals.sagepub.com/doi/10.1177/17543371231212235)
