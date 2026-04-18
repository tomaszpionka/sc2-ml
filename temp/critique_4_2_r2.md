# Adversarial Critique R2 — temp/plan_4_2_v2.md

## Executive verdict: ESCALATE_TO_USER

Two R1 BLOCKERs closed (B1, B3). **B2 is only partially closed** — v2 removes the "primary-feature exception" framing in §4.2 prose, but the artifact itself (`01_04_01_data_cleaning.json:2198` and `01_04_01_data_cleaning.md:281`) still says verbatim *"Primary feature exception per Rule S4"*. The plan now silently contradicts its own authoritative source artifact. Separately, a WebSearch turned up **Madley-Dowd 2019 (J Clin Epi) which explicitly argues against using proportion-missing to drive imputation decisions** — directly relevant to the 80% heuristic. Author needs to decide: (a) also repair the two aoe2companion artifacts, or (b) cite Madley-Dowd 2019 / Jakobsen 2017 as genuine peer-reviewed anchors.

## R1 BLOCKER status

| R1 item | v2 fix | Verdict | Evidence |
|---|---|---|---|
| B1 MMR MAR/MNAR inconsistency | T05 sub-step 0 repairs `04_data_and_methodology.md` line 41 + line 195 per ledger row 35 | CLOSED | Ledger row 35 `mechanism=MAR` verified; repair wording matches ledger prose |
| B2 "primary-feature exception" + 80% threshold provenance | v2 drops "exception" framing; re-cites 26.20% as standard 5-40% MAR-FLAG; 80% reframed as "operational heuristic" | PARTIALLY CLOSED | `01_04_01_data_cleaning.json:2198` + `01_04_01_data_cleaning.md:281` STILL say "Primary feature exception per Rule S4". R1 was wrong to call this plan-side misread — plan faithfully reported artifact language. Artifact ITSELF has the I7 violation. |
| B3 char budget | Raised to 22.5–28.5k | CLOSED with caveat N4 | See NEW issues |

## R1 WARNING status

| R1 item | v2 fix | Verdict |
|---|---|---|
| W1 Christen 2012 | Reframed "standard introductory textbook" + neural-ER hedge | CLOSED |
| W2 Wilson 2017 | Moved to Appendix A forward-ref | CLOSED |
| W3 Tabela 4.6 sparsity | Restructured to ≥2-dataset rows; singletons → 4.6a | CLOSED with residual N5 |

## R1 unanticipated status

| Item | v2 fix | Verdict |
|---|---|---|
| D6a Tabela 4.6 grep-identity | T01 Instructions step 6 | CLOSED |
| D6b I9→I2 redirection | Verified `.claude/scientific-invariants.md:24-29` vs 163-197; redirection correct | CLOSED |
| D6c `read_csv_auto` VARCHAR | T01 step 7 anchors; T02 conditional | CLOSED |

## NEW issues introduced by v2

### N1 — [BLOCKER] Artifact-prose contradiction introduced by B2 closure

Thesis-side fix is scoped to §4.2 prose alone. But aoe2companion ledger artifact prose (`01_04_01_data_cleaning.json:2198` mechanism_justification; `01_04_01_data_cleaning.md:281` DS-AOEC-04 Question) STILL says *"Primary feature exception per Rule S4"*. After T04 executes, thesis reads "standard MAR-FLAG routing, not exception" while cited ledger reads "exception". Either:
- **Option A**: expand T05 to repair DS-AOEC-04 + ledger `mechanism_justification` (modifies Phase 01 artifact — I9 concern)
- **Option B**: §4.2.3 acknowledges divergence ("the artifact's 'exception' language is inexact — 26.20% falls in the 5-40% band where FLAG_FOR_IMPUTATION is standard; 'exception' refers to an unspecified rule hierarchy"). More honest, I9-compliant, adds ~400 chars.

### N2 — [WARNING] Madley-Dowd 2019 / Jakobsen 2017 gap

WebSearch found:
- **Jakobsen et al. 2017** (BMC Med Res Methodol, PMC5717805): ">40% missing on important variables → results only hypothesis-generating." Peer-reviewed anchor for 40% threshold, stronger than van Buuren prose
- **Madley-Dowd et al. 2019** (J Clin Epi, PMC6547017): argues against using proportion-missing to drive MI decisions; advocates FMI

Plan currently cites van Buuren for 30-40% and admits 80% is heuristic. Stronger move: cite Jakobsen 2017 for 40%, explicitly rebut Madley-Dowd 2019 ("We adopt rate-based routing rather than FMI-based because Phase 01 is fold-agnostic; FMI requires fold-aware imputation which is Phase 02 per I3"). Ignoring Madley-Dowd leaves examiner question unanswered.

### N3 — [WARNING] Branch naming contradicts expanded scope

`branch: docs/thesis-4.2-session` but execution also modifies §4.1 at line 41 + 195. Document the §4.1 repair scope in commit message / PR title to surface in review.

### N4 — [WARNING] T04 at 13k chars still under-budgeted vs. §4.1.2

§4.1.2 (two datasets, no typology, no defence) = 22.5k. §4.2.3 (three datasets + typology + defence + I7 provenance + MMR MAR commitment + two tables + §4.1 repair + restructure) at max 13k is ~58% of §4.1.2's char density per dataset. Recommend raising upper bound to 14-15k.

### N5 — [NIT] Tabela 4.6 row 5 fails ≥2-dataset rule

FLAG_FOR_IMPUTATION 5-40% MAR has SC2 `(nd)`, aoestats `(nd)`, aoe2companion invocations — singleton masquerading as typology row. Move to 4.6a OR acknowledge in prose "retained in main table because canonical mechanism for primary predictive feature."

### N6 — [NIT] `invariants_touched` inconsistency

Front matter lists `[I2, I3, I5, I6, I7, I8, I9, I10]`. Missing I4 (prediction target). §4.2.3 discusses target-row exclusions and POST_GAME discipline — touches I4. Add I4 or justify exclusion.

## Scientific integrity

MMR MAR-primary commitment (B1 closure) is methodologically correct — ledger reasoning satisfies Rubin MAR under "missingness depends on observed replay source". Routing invariance (≥80% → DROP regardless of mechanism) means classification dispute doesn't reach data. Strong methodological position.

B2 closure is weaker — v2 quietly disagrees with the artifact in thesis prose. The artifact itself contains an I7 violation ("exception" to unspecified rule hierarchy). N1 needs resolution.

80% operational-heuristic framing is honest but admits partial I7 violation. Madley-Dowd 2019 + Jakobsen 2017 strengthen considerably.

## Final verdict

**ESCALATE_TO_USER** — three user decisions needed:
1. N1 (BLOCKER): Option A (artifact repair) vs Option B (prose acknowledgment)?
2. N2 (WARNING): Add Jakobsen 2017 + Madley-Dowd 2019?
3. N3-N6: Minor; planner can resolve without user input.

Sources:
- Madley-Dowd 2019: https://pmc.ncbi.nlm.nih.gov/articles/PMC6547017/
- Jakobsen 2017: https://pmc.ncbi.nlm.nih.gov/articles/PMC5717805/
