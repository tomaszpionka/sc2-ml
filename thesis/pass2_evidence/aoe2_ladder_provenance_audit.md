# AoE2 Ladder Provenance Audit

**Generated:** 2026-04-26
**Task:** T05 (thesis/audit-methodology-lineage-cleanup)
**Scope:** aoestats and aoe2companion datasets, Chapters 1–4 terminology classification
**Author:** T05 executor (claude-sonnet-4-6)

---

## Fallback rule (BLOCKER-1 fix — recorded explicitly)

> If external documentation is ambiguous or unavailable regarding the queue semantics of an
> `internalLeaderboardId`, treat that ID as **quickplay/matchmaking-derived, NOT ranked ladder**.
> Never default to "ranked ladder" on ambiguity.

This rule governs every classification decision in §§ 4.1 and 4.2 below.

---

## 4.1 aoestats sub-audit

### 4.1.1 Source fields retained

| Field | Value in scope | Note |
|-------|---------------|------|
| `leaderboard` | `'random_map'` | String value; constant after R02 filter |
| `num_players` | 2 | Structural 1v1 |
| `profile_id` | non-NULL BIGINT | NULL rows excluded by R03 in `player_history_all` |
| `winner` | complementary pair | R03 excludes inconsistent-winner rows |
| `old_rating` / `new_rating` | present; `new_rating` POST-GAME excluded | sentinel=0 for ~0.027% of rows |

No `queue`, `match_type`, `lobby_type`, or equivalent column exists in `matches_raw`.
`raw_match_type` is 0.04% NULL and is redundant given the `leaderboard` scope filter; R02
treats it as DROP_COLUMN.

### 4.1.2 On-disk evidence

**01_03_02_true_1v1_profile.md** (2026-04-16) provides the primary on-disk evidence:

- True 1v1 matches (exactly 2 player rows): 18,438,769
- `leaderboard = 'random_map'` within true 1v1: 17,815,944 (96.62%)
- Jaccard index (true 1v1 ∩ ranked 1v1) / (true 1v1 ∪ ranked 1v1) = **0.958755**
- The remaining true 1v1 rows outside `random_map` are `co_random_map` (622,817),
  `team_random_map` (7), `co_team_random_map` (1) — these are cooperative modes,
  explicitly excluded by R02.

**01_04_01_data_cleaning.md** R02 rule: "player_count != 2 OR leaderboard != 'random_map' →
EXCLUDE from matches_1v1_clean VIEW".

**01_04_01_data_cleaning.md** CONSORT flow: Stage 3 = 17,815,944 rows, Stage 4 = 17,814,947.

**INVARIANTS.md §1**: confirms `matches_1v1_clean` is `17,814,947 rows (rm_1v1 scope,
leaderboard='random_map')`.

### 4.1.3 External documentation lookup

**URL consulted:** https://aoestats.io/ (accessed 2026-04-26)

The aoestats.io homepage meta description reads: "aoestats aggregates the latest **ranked
matches** for Age of Empires II DE (aoe2) and provides indepth data and statistics on a
civilization basis; stats include: win rate, play rate, win rate vs. game length, and more!"

The homepage asserts "ranked matches" but does **not** enumerate leaderboard IDs, does not
distinguish `random_map` from `co_random_map` or quickplay variants, and does not expose API
documentation that defines the `leaderboard` string values or their mapping to the
official AoE2 DE matchmaking queue types.

No GitHub source repository for aoestats.io was found (the site does not link to one). No API
documentation URL is exposed by the homepage. Archive.org and README documentation are not
accessible via the homepage.

**Conclusion from external lookup:** The aoestats.io source is **silent** on whether
`leaderboard='random_map'` exclusively identifies the official ranked AoE2 DE Random Map 1v1
queue, or whether it may include quickplay, custom-lobby, or other Random Map sub-queues.
The homepage's use of "ranked matches" is a marketing description, not a schema definition.

**Scope note on relevant external documentation for aoestats.** The authoritative external
documentation for the aoestats data source is the aoestats.io site / API / DB-dump
documentation (not `aoe2.net`, which is a separate ecosystem service unrelated to aoestats
lineage — see §4.2.4a). Aoestats does expose source fields such as `leaderboard`,
`raw_match_type`, and `game_type` in its DB dumps, but those fields do not conclusively
prove queue semantics: `leaderboard='random_map'` is an upstream-aggregator label whose
mapping to the official AoE2 DE matchmaking queue types is undocumented at aoestats.io.
The Tier 4 semantic-opacity conclusion therefore stands.

### 4.1.4 AI-filter and human-only evidence

`INVARIANTS.md §1`: "No `name` column in `players_raw`." `profile_id` NULL rows (1,185)
excluded by `player_history_all` filter. No explicit AI-player flag (`profileId=-1` sentinel
is an aoe2companion concept; aoestats carries no such sentinel). The dataset does not carry
explicit human/AI annotation beyond the `profile_id IS NOT NULL` filter.

### 4.1.5 Residual risks

1. **Quickplay contamination.** The `leaderboard='random_map'` value is an upstream API string.
   If the aoestats crawler calls an aoe2insights.com endpoint that aggregates multiple queue
   types under the `random_map` label (e.g., both the ranked and the quickplay RM queues),
   the scope is broader than "ranked ladder" without being documented as such. No on-disk
   evidence rules this out; external documentation is silent.

2. **Custom-lobby contamination.** Custom lobbies on the same map pool may carry a
   `leaderboard='random_map'` value in the upstream API if set up with ranked settings. This
   risk is unquantifiable without API schema documentation.

3. **Missing/ambiguous queue metadata.** The `raw_match_type` column (0.04% NULL) is the
   only candidate for a queue-type discriminator beyond `leaderboard`. Its nullable nature
   and the decision to DROP it (DS-AOESTATS-04) remove any residual guard.

4. **Team-game contamination.** The structural 1v1 filter (R02 `player_count=2`) effectively
   guards against team-game contamination. This is a strong filter. Residual risk: co-op
   1v1-with-AI games where the AI player carries no `profile_id` (excluded by NULL filter).

5. **Upstream-aggregator limitation.** aoestats is a third-party aggregator, not a direct
   API consumer with documented filter semantics. The crawling logic and its treatment of
   queue type are opaque.

### 4.1.6 Evidence strength

**WEAK / OPAQUE.** The Jaccard index of 0.958755 between structural 1v1 and `leaderboard='random_map'`
shows high internal consistency within the aoestats dataset, but it does not resolve what
`random_map` means to the upstream API. The on-disk evidence is internally consistent;
the external source is silent on the precise queue semantics.

### 4.1.7 Recommended terminology for aoestats

Per the four-tier terminology ladder (plan §6 Stage 4.3) and the fallback rule:

> **Recommended label:** "third-party 1v1 Random Map match records aggregated by aoestats.io
> (source label `leaderboard='random_map'`; queue semantics unverified against upstream API
> documentation)"

Shorter thesis-safe form: "aoestats 1v1 Random Map records (source-specific aggregation,
semantic opacity on queue type)".

This maps to **Tier 4** of the terminology ladder: "source-specific aggregation with semantic
opacity". The thesis MUST NOT call this population "ranked ladder" without a hedge. The
phrase "Ladder rankingowy 1v1 random_map" used in Tabela 4.4a line 177 of
`04_data_and_methodology.md` requires weakening.

---

## 4.2 aoe2companion sub-audit

### 4.2.1 Source fields retained

| Field | Values in scope | Note |
|-------|----------------|------|
| `internalLeaderboardId` | 6, 18 | Two distinct leaderboard IDs |
| `won` | complementary pair | R03 excludes non-complementary rows |
| `profileId` | non-(-1) INTEGER | sentinel=-1 excluded |
| `rating` | non-zero DOUBLE | sentinel=0 for lb=6, ~26% NULL overall |

No `queue_type`, `lobby_type`, or explicit ranked/quickplay Boolean column exists in
`matches_raw`.

### 4.2.2 On-disk evidence for ID 6 = rm_1v1

**01_04_01_data_cleaning.md** (aoe2companion) CONSORT flow: "S1 Scope-restricted: R01:
`internalLeaderboardId IN (6, 18)`".

**research_log.md line 872** (2026-04-16 Step 01_04_00): leaderboard_raw top values include
"6/rm_1v1 (54M), … 18/qp_rm_1v1 (7M)".

**INVARIANTS.md §2** (aoe2companion): identity scope rates computed on
"`internalLeaderboardId IN (6, 18)` … rm_1v1 analytical scope". The scope note in INVARIANTS
explicitly labels the combined scope as "rm_1v1 analytical scope" but immediately clarifies
it covers both IDs 6 and 18.

**01_05_03_stratification.py lines 17–24**: "Critique fix M-02: Secondary regime is rm_1v1
(lb=6) vs rm_team; but since rm_team is out-of-analytical-scope per 01_04_01 R01, we use
**rm_1v1 (lb=6) vs qp_rm_1v1 (lb=18)** as the within-aoec secondary regime. Documented as
scope-stratification, not ladder-segmentation."

**01_05_03_stratification.py lines 22–24** (Hypothesis): "PSI magnitudes on pre-game features
differ systematically between **internalLeaderboardId=6 (rm_1v1) and =18 (qp_rm_1v1)**".

**Conclusion for ID 6:** On-disk evidence consistently and explicitly labels ID 6 as `rm_1v1`
(ranked 1v1 Random Map). This is a strong internal classification.

### 4.2.3 On-disk evidence for ID 18 = qp_rm_1v1

The on-disk classification is unambiguous:

- `research_log.md line 872`: "18/qp_rm_1v1 (7M)"
- `01_05_03_stratification.py line 23`: "internalLeaderboardId=6 (rm_1v1) and **=18 (qp_rm_1v1)**"
- `INVARIANTS.md §2` scope note: "rm_1v1 (internalLeaderboardId IN (6, 18))" — the combined
  scope is labelled `rm_1v1` for brevity but the individual ID 18 is consistently annotated
  as `qp_rm_1v1` (quickplay) in the two most specific artifacts.

The "qp_" prefix in `qp_rm_1v1` stands for "quickplay". This interpretation is consistent
across all on-disk artifacts that reference ID 18 specifically.

### 4.2.4 External verification for ID 18

**URLs consulted:**

1. `https://aoe2companion.com/api/leaderboard?leaderboardId=18&page=1&count=1` — accessed
   2026-04-26 — returns an HTML web app page (404-style redirect); REST API no longer
   accessible at this path.

2. `https://aoe2.net/api/leaderboard?game=aoe2de&leaderboard_id=18&start=1&count=1` —
   accessed 2026-04-26 — returns an HTML 404 page; the aoe2.net REST API has been deprecated
   or migrated.

3. `https://aoe2.net/api/strings?game=aoe2de&language=en` — accessed 2026-04-26 — returns an
   HTML 404 page.

4. `https://raw.githubusercontent.com/SiegeEngineers/aoe2companion/main/app/src/service/data.tsx`
   — accessed 2026-04-26 — returns a 404 (file path not found at this URL).

5. `https://raw.githubusercontent.com/SiegeEngineers/aoe2companion/main/app/src/helper/leaderboard.tsx`
   — accessed 2026-04-26 — returns a 404.

6. `https://aoecompanion.com/` — accessed 2026-04-26 — returns a redirected web application
   with no machine-readable API or schema documentation accessible.

**External documentation verdict:** UNAVAILABLE. The aoe2.net REST API (which was the
upstream source for aoe2companion leaderboard ID semantics) is no longer accessible at its
documented endpoints as of 2026-04-26. No alternative authoritative source for the mapping
of `internalLeaderboardId=18` to a named queue type was found.

**Fallback rule applied:** Per the T05 fallback rule, in the absence of external
documentation, ID 18 is treated as **quickplay/matchmaking-derived, NOT ranked ladder**.
This is consistent with the on-disk `qp_rm_1v1` label.

The primary evidence for the aoe2companion classification is **repo-local / on-disk**:
`sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_03_stratification.py`
labels `internalLeaderboardId=6` as `rm_1v1` and `internalLeaderboardId=18` as `qp_rm_1v1`,
and `research_log.md:872` lists the corresponding row counts (~54M and ~7M). The external
documentation lookup did **not** overturn that on-disk evidence.

### 4.2.4a Role of aoe2.net in this audit

`aoe2.net` is **not** an input data source in this thesis. The thesis uses only **aoestats**
and **aoe2companion** as AoE2 data sources, and **no dataset lineage** is attributed to
`aoe2.net` in any ROADMAP, schema, research_log, or thesis chapter.

`aoe2.net` URLs were consulted in §4.2.4 only as a **historical / external-ecosystem
documentation probe**, because earlier community tools and wrappers (including the
aoe2companion app stack itself, prior to its API migration) have at times used or documented
`aoe2.net` leaderboard endpoints to expose `leaderboardId` semantics. The probes were a
best-effort attempt to find an authoritative external mapping for `internalLeaderboardId=18`.

The failed/deprecated lookup (HTTP 404 across all `aoe2.net` API endpoints accessed
2026-04-26) is **negative evidence only**: it means the audit could not use `aoe2.net` to
**overturn** the repo-local classification of `internalLeaderboardId=18` as `qp_rm_1v1`
(quickplay). It does not weaken or strengthen the on-disk evidence; it leaves it as the
sole authoritative basis for the ID-18 classification.

The conservative fallback therefore remains: **ID 18 is quickplay/matchmaking-derived
unless source-specific evidence explicitly proves otherwise.**

> The presence of aoe2.net in this audit must not be interpreted as adding a third AoE2
> data source; it is only a failed historical-documentation probe for leaderboard semantics.

### 4.2.5 Decision on combining ID 6 and ID 18

On-disk volumes: ID 6 (~54M rows), ID 18 (~7M rows). ID 6 is approximately 88.5% of the
combined scope.

The stratification notebook (01_05_03) explicitly uses the lb=6 vs lb=18 split as a
"scope-stratification", and documents a hypothesis that PSI magnitudes differ between the two.
This framing treats them as different populations worthy of separate characterization.

The `data_quality_report_aoe2companion.md` R01 rule retains both in `matches_1v1_clean`:
"R01: `internalLeaderboardId IN (6, 18)` — Retain 1v1 ranked ladder only". The description
"1v1 ranked ladder only" is a **mis-label** (see §5 below) because ID 18 is `qp_rm_1v1`
(quickplay), not ranked ladder.

**Decision recommendation:** Retain both IDs in the analytical scope but describe them
separately in the thesis with cautious combined wording. The recommended framing is:

- ID 6 alone: "1v1 ranked Random Map ladder matches (`internalLeaderboardId=6`, `rm_1v1`)"
- ID 18 alone: "1v1 quickplay/matchmaking Random Map matches (`internalLeaderboardId=18`,
  `qp_rm_1v1`, per on-disk classification; external API documentation unavailable as of
  2026-04-26)"
- Combined: "1v1 Random Map records combining ranked ladder (ID 6, ~54M rows) and
  quickplay/matchmaking (ID 18, ~7M rows)"

The combined population should NOT be called "ranked ladder" without explicit qualification
that ID 18 may represent quickplay-matchmaking records.

The combination is methodologically defensible as a robustness/scope decision if the thesis
acknowledges the heterogeneity and treats ID 18 as a sensitivity or control population.

### 4.2.6 Evidence strength

**MODERATE (for ID 6) / WEAK/OPAQUE (for ID 18 external verification).**
On-disk evidence for ID 18 = `qp_rm_1v1` is consistent and explicit. External verification
was not possible due to API deprecation. Per the fallback rule, the on-disk classification
stands as the operative classification.

---

## 4.3 Recommended terminology (four-tier ladder mapping)

### Tier 1 — "publicly indexed 1v1 ranked Random Map ladder matches" (strong external evidence)
Not applicable to either dataset. Would require an authoritative API response confirming
that the leaderboard ID maps exclusively to the official ranked queue.

### Tier 2 — "third-party 1v1 Random Map ladder records with moderate external verification"
Applicable to **aoe2companion ID 6 (`rm_1v1`)** only, with the caveat that external API
documentation is currently unavailable. The on-disk label `rm_1v1` is consistent and was
evidently derived from an aoe2insights.com API source at the time of data collection.

### Tier 3 — "third-party 1v1 Random Map matchmaking/quickplay records"
Applicable to **aoe2companion ID 18 (`qp_rm_1v1`)** per on-disk classification and fallback
rule.

### Tier 4 — "source-specific aggregation with semantic opacity"
Applicable to **aoestats** (leaderboard='random_map'), where the external source does not
document the precise queue semantics.

### Summary table

| Dataset | Population | Tier | Recommended thesis label |
|---------|-----------|------|--------------------------|
| aoestats | `leaderboard='random_map'`, 1v1 | Tier 4 | "aoestats 1v1 Random Map records (source label `random_map`; queue semantics unverified)" |
| aoe2companion ID 6 | `internalLeaderboardId=6` (`rm_1v1`) | Tier 2 | "aoe2companion ranked 1v1 Random Map records (`rm_1v1`, ID 6, ~54M rows)" |
| aoe2companion ID 18 | `internalLeaderboardId=18` (`qp_rm_1v1`) | Tier 3 | "aoe2companion quickplay/matchmaking 1v1 Random Map records (`qp_rm_1v1`, ID 18, ~7M rows; external API unavailable)" |
| aoe2companion ID 6 + 18 combined | `internalLeaderboardId IN (6, 18)` | Tier 2/3 mixed | "aoe2companion 1v1 Random Map records combining ranked (ID 6) and quickplay/matchmaking (ID 18)" |

---

## 4.4 Thesis-occurrence classification (Chapters 1–4)

All occurrences of "ranked ladder", "ladder", "quickplay", "matchmaking", and Polish equivalents
("rankingowy", "drabinkowy", "ladderowy") identified via grep, classified per source.

### Occurrence table

| File:line | Occurrence (verbatim or paraphrase) | Source context | Classification | Proposed wording |
|-----------|-------------------------------------|----------------|----------------|------------------|
| `04_data_and_methodology.md:177` | "Ladder rankingowy 1v1 random_map" (aoestats column in Tabela 4.4a) | aoestats population | **revise** | "aoestats 1v1 Random Map records (source label `random_map`; queue type unverified)" |
| `04_data_and_methodology.md:177` | "Ladder rankingowy 1v1 (rm_1v1 + qp_rm_1v1)" (aoe2companion column in Tabela 4.4a) | aoe2companion ID 6+18 | **revise** | "aoe2companion 1v1 Random Map records (ranked: rm_1v1 + quickplay: qp_rm_1v1)" |
| `04_data_and_methodology.md:187` | "30 531 196 (1v1 ranked: rm_1v1 + qp_rm_1v1)" in Tabela 4.4b row "Liczba meczów" | aoe2companion combined | **revise** | "30 531 196 (1v1 Random Map: rm_1v1 ranked + qp_rm_1v1 quickplay)" |
| `04_data_and_methodology.md:211` | "aoe2companion i aoestats reprezentują dwie różnie próbkowane populacje rankingowe ladderowe (`[POP:ranked_ladder]`)" | both datasets | **revise** | weaken `[POP:ranked_ladder]` for aoestats (Tier 4) and aoe2companion ID 18; retain for aoe2companion ID 6 only |
| `04_data_and_methodology.md:255` | "ladder 1v1 random_map" (aoestats in Tabela 4.5 row "Populacja scope") | aoestats | **revise** | "1v1 Random Map records (source label `random_map`; queue type unverified)" |
| `04_data_and_methodology.md:255` | "ladder 1v1 (rm_1v1 + qp_rm_1v1)" (aoe2companion in Tabela 4.5 row "Populacja scope") | aoe2companion ID 6+18 | **revise** | "1v1 Random Map: rm_1v1 ranked (ID 6) + qp_rm_1v1 quickplay (ID 18)" |
| `04_data_and_methodology.md:79` | "rankingowe ladderowe (dwa korpusy AoE2)" | both AoE2 datasets | **revise** | "1v1 Random Map matchmaking records (two AoE2 corpora; ranking/quickplay composition differs by source)" |
| `04_data_and_methodology.md:41` | "ladderowego systemu rankingowego (ang. *unrated professional*)" | SC2 MMR context | **OK** | describing Battle.net SC2 ladder — correct use |
| `04_data_and_methodology.md:43` | "ladderowych, a większość meczów turniejowych jest rozgrywana na kontach … nieprzypisanych do ladderowego systemu matchmakingu" | SC2 context | **OK** | correct — SC2 ladder/matchmaking description |
| `04_data_and_methodology.md:53` | "brak meczów z ladderowego systemu matchmakingu" | SC2EGSet context | **OK** | correct — SC2EGSet is explicitly not ladder |
| `02_theoretical_background.md:37` | "meczer rankingowy ladderowych (ang. *ladder*) trybu Battle.net" | SC2 context | **OK** | correct SC2 ladder reference |
| `02_theoretical_background.md:77` | "System rankingowy Age of Empires II: Definitive Edition opiera się na klasycznym Elo … z pojedynczym skalarem Elo na gracza … tryb (1v1 Random Map …)" | AoE2 system description | **OK** | describes official system, not dataset population |
| `02_theoretical_background.md:171` | "nie obejmują meczów drabinkowych z systemu rankingowego Battle.net" | Aligulac/SC2 context | **OK** | SC2 context, correct |
| `01_introduction.md:45` | "szeroki przekrój ladderowych graczy rankingowych" (aoestats) | aoestats population | **revise** | weaken to "broad cross-section of 1v1 Random Map players (source: aoestats.io aggregator)" |
| `03_related_work.md:143` | "korpusem 1 261 288 meczów rankingowych z serwisu aoestats.io" (Lin2024NCT paper) | citing another paper's data | **source-specific** | this describes another paper's data; add a note that the paper uses "ranked matches" per aoestats.io labelling |
| `data_quality_report_aoe2companion.md:29` | "Retain 1v1 ranked ladder only" (R01 description) | generated artifact | **unsupported** | "Retain 1v1 rm_1v1 and qp_rm_1v1 scope (leaderboard IDs 6 and 18)" (repair required — see §6) |

**Classification counts:**
- **OK:** 7 occurrences (all SC2-context or general AoE2-system descriptions, or correctly
  attributed literature references)
- **revise:** 7 occurrences in thesis chapters 1–4
- **unsupported:** 1 occurrence (generated artifact `data_quality_report_aoe2companion.md:29`)
- **source-specific:** 1 occurrence (Lin2024NCT paper's use of aoestats "ranked matches")

**Total classified:** 16 occurrences.

---

## 5. Mis-label propagation trace

### Origin

`src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoe2companion.md` **line 29**:

```
| R01 | `internalLeaderboardId IN (6, 18)` (rm/ew scope) | Retain 1v1 ranked ladder only | 216,027,260 rows excluded |
```

The description "Retain 1v1 ranked ladder only" is a mis-label. The actual filter retains
both `rm_1v1` (ranked, ID 6) and `qp_rm_1v1` (quickplay, ID 18).

### Propagation path

1. **Generated artifact origin** — `data_quality_report_aoe2companion.md:29` (mis-label)
   — generated by notebook `01_06_02_data_quality_report.py` (aoe2companion).

2. **Thesis Chapter 4 §4.1.3, line 177** — Tabela 4.4a row "Populacja":
   "Ladder rankingowy 1v1 (rm_1v1 + qp_rm_1v1)" — the term "ladder rankingowy" inherits
   the ranked-ladder framing while acknowledging qp_rm_1v1; the combination is described
   with "ranked ladder" umbrella terminology.

3. **Thesis Chapter 4 §4.2.3, line 187** (Tabela 4.4b row "Liczba meczów"):
   "30 531 196 (1v1 ranked: rm_1v1 + qp_rm_1v1)" — "1v1 ranked" is applied to the combined
   scope including ID 18.

4. **Thesis Chapter 4 §4.1.4, line 211** — "aoe2companion i aoestats reprezentują dwie
   różnie próbkowane populacje rankingowe ladderowe (`[POP:ranked_ladder]`)" — the `[POP:ranked_ladder]`
   tag is applied to aoe2companion without qualification of the qp_rm_1v1 component.

5. **Thesis Chapter 4 Tabela 4.5, line 255** — "ladder 1v1 (rm_1v1 + qp_rm_1v1)" in the
   "Populacja scope" row for aoe2companion — "ladder" umbrella term.

6. **INVARIANTS.md §2 (aoe2companion) scope note** — "rm_1v1 analytical scope
   (`internalLeaderboardId IN (6, 18)`)" — uses `rm_1v1` as shorthand for the combined
   scope; this is a dataset-internal convention, not a mis-label per se, but it
   contributes to the "ranked ladder" framing in downstream artifacts.

7. **Thesis Chapter 4 §4.1.2.2 (aoe2companion)** — multiple paragraphs describe the scope
   as "rankingowe ladderowe" without explicitly separating the ID 6 (ranked) and ID 18
   (quickplay) populations.

### T11 action targets (propagation repair)

For T11 to apply corrected terminology, the following exact locations must be updated:

| Location | Current text | Corrected text |
|----------|-------------|----------------|
| `04_data_and_methodology.md:177` | "Ladder rankingowy 1v1 (rm_1v1 + qp_rm_1v1)" | "1v1 Random Map: rm_1v1 (ID 6, ranked) + qp_rm_1v1 (ID 18, quickplay)" |
| `04_data_and_methodology.md:187` | "30 531 196 (1v1 ranked: rm_1v1 + qp_rm_1v1)" | "30 531 196 (1v1 Random Map: rm_1v1 ranked + qp_rm_1v1 quickplay)" |
| `04_data_and_methodology.md:211` | "`[POP:ranked_ladder]`" (aoe2companion context) | "`[POP:rm_1v1_and_qp_rm_1v1]`" or weaken to "`[POP:1v1_random_map_matchmaking]`" |
| `04_data_and_methodology.md:255` | "ladder 1v1 (rm_1v1 + qp_rm_1v1)" | "1v1 Random Map: rm_1v1 (ID 6) + qp_rm_1v1 (ID 18)" |

Also: `01_introduction.md:45` description of aoestats as "ladderowych graczy rankingowych"
should be weakened to reflect Tier 4 evidence strength.

---

## 6. Generated-artifact repair determination

### Step 01_06_02 — data_quality_report_aoe2companion.md

**File:** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoe2companion.md`

**Line 29 (mis-label):**
```
| R01 | `internalLeaderboardId IN (6, 18)` (rm/ew scope) | Retain 1v1 ranked ladder only | 216,027,260 rows excluded |
```

The description "Retain 1v1 ranked ladder only" is factually incorrect: the filter retains
both `rm_1v1` (ranked, ID 6) and `qp_rm_1v1` (quickplay, ID 18). The label mis-classifies
ID 18 as ranked ladder.

**Repair required: YES.**

**Rationale:** The artifact is generated by notebook
`sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_02_data_quality_report.py`.
The mis-label is a string literal in the R01 description column of the cleaning rule table.
The repair must follow the ROADMAP → notebook → artifact → research_log → STEP_STATUS path
(T16 14A.1 BLOCKER-1 sub-check 6 extension):

1. Update the upstream notebook `01_06_02_data_quality_report.py` to correct the R01
   description string from "Retain 1v1 ranked ladder only" to
   "Retain 1v1 rm_1v1 (ID 6) and qp_rm_1v1 (ID 18) scope".
2. Regenerate the artifact `data_quality_report_aoe2companion.md` via `nbconvert --execute`.
3. Update `research_log.md` (aoe2companion) with a new entry documenting the correction.
4. Update `STEP_STATUS.yaml` Step 01_06_02 if needed.
5. Do NOT repair the artifact manually — only regenerate via the upstream notebook.

**T05 action:** Identified and documented only. Repair deferred to T16 per plan scope.

---

## 7. Cleanup-ledger entries informed/resolved by T05

### F-078 — AoE2 ranked-ladder/quickplay/matchmaking provenance (BLOCKER-1)

**Status: SUBSTANTIVELY ADDRESSED by T05.**

T05 establishes:
- aoestats `leaderboard='random_map'` is Tier 4 (semantic opacity); thesis must weaken
  "ranked ladder" claims for aoestats.
- aoe2companion ID 6 is Tier 2 (rm_1v1, moderate confidence).
- aoe2companion ID 18 is Tier 3 (qp_rm_1v1, quickplay/matchmaking by fallback rule).
- Combined aoe2companion scope should NOT be called "ranked ladder" without qualification.
- Exact locations for T11 rewrites are enumerated in §5 above.

Remaining action: T11 applies the corrected terminology to thesis chapters. Full resolution
requires T11 execution.

### F-090 — Ch4 §4.1.2 BLOCKER-1 propagation in CONSORT row (line 151)

**Status: INFORMED by T05; resolution path defined for T11.**

The CONSORT flow table in §4.1.2 aoe2companion section (referenced by F-090 as line 151)
carries the "rm_1v1 + qp_rm_1v1" framing. T05 establishes that the correction is:
"rm_1v1 (ID 6, ranked) + qp_rm_1v1 (ID 18, quickplay/matchmaking)". T11 must update the
CONSORT row description and the surrounding prose.

Remaining action: T11 applies the corrected terminology.

### F-098 — notebook `01_04_03b_canonical_slot_amendment.py` (BACKLOG F1 status)

**Status: RESOLVED by T05 F1-status determination.**

**F1 status on master: EXECUTED AND MERGED.**

Evidence:
- Git log on master: commit `939946ea` = "Merge pull request #185 from
  tomaszpionka/feat/aoestats-canonical-slot" (PR #185 = feat/aoestats-canonical-slot).
- Commit `a5f633ca` = "feat(aoestats): add canonical_slot column to matches_history_minimal
  (BACKLOG F1 + W4)".
- Artifact `01_04_03b_canonical_slot_amendment.md` and `.json` exist in
  `reports/artifacts/01_exploration/04_cleaning/` (confirmed by directory listing).
- `INVARIANTS.md §4` records: "Amendment (2026-04-20 — BACKLOG F1 + W4). The
  `canonical_slot VARCHAR` column is added to `matches_history_minimal`."
- `data_quality_report_aoestats.md` line 52: "`matches_history_minimal` 35,629,894 player rows
  10 (Phase-02-ready, post-canonical_slot amendment 2026-04-20 per PR #185 / BACKLOG F1+W4)".

**Reclassification of F-098:** Notebook `01_04_03b_canonical_slot_amendment.py` is
**confirmed_intact** (artifact exists, PR merged, INVARIANTS updated). Reclassify from
`not_yet_assessed` to `confirmed_intact`.

Downstream action: T11 should rewrite §4.4.6 closure narrative from ACTIVE to HISTORICAL
and replace "PR #TBD" references with "PR #185 (feat/aoestats-canonical-slot, 2026-04-20)".

### F-079 — aoestats `random_map` source semantics

**Status: SUBSTANTIVELY ADDRESSED by T05.**

T05 establishes: aoestats.io external documentation is silent on `random_map` queue semantics.
The Jaccard index 0.958755 (01_03_02) confirms high internal consistency but does not
establish whether `random_map` includes quickplay. Classification is Tier 4 (semantic
opacity). Thesis must weaken "ranked ladder" language for aoestats.

Remaining action: T11 rewrites affected prose using the Tier 4 label. Full resolution
requires T11 execution.

---

## 8. Notebook/Step regeneration candidates

### aoe2companion Step 01_06_02

**Regeneration required: YES** (repair determination in §6 above).
The upstream notebook `01_06_02_data_quality_report.py` must be updated to correct the R01
description string before the artifact is regenerated. This is a generated artifact; manual
repair is prohibited.

### All other Steps

No additional regeneration candidates were identified in T05 scope:
- aoestats steps: all `complete` per STEP_STATUS.yaml; no mis-labels found in generated
  aoestats artifacts that require notebook-level correction (the `data_quality_report_aoestats.md`
  uses "Restrict to ranked 1v1 ladder" for R02, which is also semantically imprecise under
  Tier 4 classification, but the R02 action is defensible as scope restriction — not the
  same class of error as mis-labelling qp_rm_1v1 as ranked ladder).
- aoe2companion steps: only Step 01_06_02 carries the BLOCKER-1 mis-label.

---

## 9. Open questions for T10 review

1. **aoestats `random_map` tier assignment.** The Tier 4 classification (semantic opacity)
   is conservative. If T10 is able to locate archived aoestats.io API documentation or
   the aoe2insights.com source schema from the data collection period, the tier might be
   upgradeable to Tier 2 or Tier 3. T10 should attempt an archive.org lookup.

2. **aoe2companion ID 18 external verification.** The aoe2.net REST API was the source for
   the `qp_rm_1v1` label. T10 should verify: (a) whether the Internet Archive preserves
   a snapshot of the aoe2.net API `/strings` endpoint from 2020–2024; (b) whether the
   SiegeEngineers/aoe2companion GitHub repository contains any leaderboard ID mapping in
   its commit history that explicitly labels ID 18 as quickplay.

3. **Combined scope thesis framing.** If both IDs are retained in `matches_1v1_clean`, should
   the thesis present them as: (a) a single population with caveats; (b) two populations with
   separate rows in Tabela 4.4; or (c) ID 18 relegated to a footnote or sensitivity analysis?
   T10 should stress-test whether the "combined with cautious wording" recommendation in §4.2.5
   above is methodologically sufficient, or whether the 7M quickplay rows should be excluded
   to preserve a "cleaner" ranked-only claim.

4. **aoestats `data_quality_report_aoestats.md` R02 label.** The R02 description is
   "Restrict to ranked 1v1 ladder". This is also semantically imprecise under Tier 4 but is
   a weaker mis-label than the aoe2companion BLOCKER-1. T10 should decide whether this
   requires a separate regeneration ticket or is resolvable with a thesis-level hedge only.

5. **[POP:ranked_ladder] tag in aoestats Phase 06 interface.** Per §4.1.4 of Chapter 4 and
   per the git log (PR #180 backfilled `[POP:ranked_ladder]` into `phase06_interface_aoestats.csv`),
   the tag `[POP:ranked_ladder]` now appears on 136/136 rows of the aoestats Phase 06 CSV.
   Under Tier 4 classification, this tag is semantically imprecise. T10 should decide whether
   the tag should be changed to `[POP:1v1_random_map]` in a follow-up PR, or whether the
   existing tag is acceptable with a prose-level caveat in the thesis.

---

## 10. External documentation probes

This section enumerates the **external documentation probes** attempted during the audit.
None of the URLs below is a data-source lineage entry for the thesis; the only AoE2 data
sources used by the thesis are **aoestats** and **aoe2companion**. The probes were
best-effort attempts to find authoritative external schema/API documentation that could
either confirm or overturn the repo-local on-disk classifications. Where probes returned
HTTP 404 or no machine-readable schema, the audit fell back to on-disk evidence (per the
fallback rule recorded in §1).

In particular, see §4.2.4a for the explicit scoping note on `aoe2.net`: it is not a thesis
data source, and its deprecated endpoints are recorded here as **negative evidence only**.

| URL | Access date | Probe target | Result |
|-----|-------------|--------------|--------|
| https://aoestats.io/ | 2026-04-26 | aoestats site documentation (aoestats data source) | Homepage: "aggregates ranked matches for AoE2 DE". No API/DB-dump docs. No GitHub link. No leaderboard schema. |
| https://aoe2.net/api/leaderboard?game=aoe2de&leaderboard_id=6 | 2026-04-26 | Historical ecosystem documentation (NOT a thesis source) | HTTP 404 (API deprecated/migrated) |
| https://aoe2.net/api/leaderboard?game=aoe2de&leaderboard_id=18 | 2026-04-26 | Historical ecosystem documentation (NOT a thesis source) | HTTP 404 (API deprecated/migrated) |
| https://aoe2.net/api/strings?game=aoe2de&language=en | 2026-04-26 | Historical ecosystem documentation (NOT a thesis source) | HTTP 404 |
| https://raw.githubusercontent.com/SiegeEngineers/aoe2companion/main/app/src/service/data.tsx | 2026-04-26 | aoe2companion app source (aoe2companion data source) | HTTP 404 (file path not found) |
| https://raw.githubusercontent.com/SiegeEngineers/aoe2companion/main/app/src/helper/leaderboard.tsx | 2026-04-26 | aoe2companion app source (aoe2companion data source) | HTTP 404 |
| https://aoe2companion.com/api/leaderboard?leaderboardId=18&page=1&count=1 | 2026-04-26 | aoe2companion app/API (aoe2companion data source) | HTTP 404 / web app redirect |
| https://aoe2companion.com/api/leaderboard?leaderboardId=6&page=1&count=1 | 2026-04-26 | aoe2companion app/API (aoe2companion data source) | HTTP 404 / web app redirect |
| https://aoecompanion.com/ | 2026-04-26 | aoe2companion app/API (aoe2companion data source) | Web app (React Native); no machine-readable API docs accessible |
