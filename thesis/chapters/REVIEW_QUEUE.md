# Thesis Review Queue — Pass 1 → Pass 2 Handoff

This file tracks thesis sections that Claude Code has drafted (Pass 1) and
that need external validation in Claude Chat (Pass 2).

## Workflow

1. Claude Code drafts a section and runs the Critical Review Checklist
   (see `.claude/thesis-writing.md`)
2. Claude Code plants `[REVIEW: ...]` and other inline flags
3. Claude Code appends an entry to the Pending table below
4. User brings the section + referenced artifacts to Claude Chat for Pass 2
5. After Pass 2 corrections are applied, move the entry to Completed

## Pending Pass 2 reviews

| Section | Chapter file | Drafted date | Flag count | Key artifacts | Pass 2 status |
|---------|-------------|-------------|------------|---------------|---------------|
| §1.1 Background and motivation | thesis/chapters/01_introduction.md | 2026-04-13 | 0 | — (literature section, no data artifacts) | Pending — Pass 2 blocking items resolved |
| §2.5 Player skill rating systems | thesis/chapters/02_theoretical_background.md | 2026-04-17 | 4 [REVIEW] | thesis/reviews_and_others/related_work_rating_systems.md (seed bibliography); thesis/references.bib (12 new entries appended) | Pending — Gate 0.5 calibration draft. 17 keys cited. Polish ~13.4k chars. Key Pass 2 questions: (1) TrueSkill 2 independent RTS validation? (2) Liquipedia/Battle.net MMR grey-literature acceptability? (3) historical Aligulac snapshots for SC2EGSet retrospective ratings? (4) EsportsBench cross-system validation reference? |
| §1.3 Research questions | thesis/chapters/01_introduction.md | 2026-04-17 | 2 [REVIEW] | thesis/references.bib (Bois2025 added) | Pending — Pass 2 questions: (1) RQ4 cold-start strata thresholds — empirical match-count distribution to be confirmed after Phase 03; (2) RQ1 hypothesis on GBDT dominance in two-game cross comparison — verify Thorrez2024 EsportsBench reports cross-system comparability beyond per-system fit. |
| §1.4 Scope and limitations | thesis/chapters/01_introduction.md | 2026-04-17 | 1 [REVIEW] | — (literature/framing section) | Pending — Pass 2 questions: (1) AoE2 roadmap status — verify whether mgz parser inclusion remains out of scope after AoE2 phase planning; (2) AoE2 civilization count over corpus window — confirm 45 figure against actual data window vs. current Definitive Edition value. |
| §3.2 StarCraft prediction literature | thesis/chapters/03_related_work.md | 2026-04-17 | 6 [REVIEW] | thesis/reviews_and_others/related_work_historical_rts_prediction.md (seed bibliography); thesis/references.bib (15 new entries appended) | Pending — Pass 1 calibration draft. 28 distinct keys cited. Polish ~14.8k chars. Key Pass 2 questions: (1) confirm Tarassoli2024 bib deletion as SC-Phi2 misattribution; (2) verify SC-Phi2 quantified accuracy from MDPI AI version; (3) verify EsportsBench 80.13% exact figure for SC2 from Thorrez preprint; (4) verify Khan2024SCPhi2 venue (arXiv vs MDPI AI); (5) verify Vinyals2017 prediction baseline phrasing; (6) verify Bialecki2022 vs Bialecki2023 corpus relationship language |
| §2.4 ML methods for classification | thesis/chapters/02_theoretical_background.md | 2026-04-17 | 3 [REVIEW] | thesis/references.bib (13 new entries: Hastie2009ESL, Friedman2001GBM, Chen2016XGBoost, Ke2017LightGBM, Goodfellow2016DL, Breiman2001, CortesVapnik1995, Hochreiter1997LSTM, KipfWelling2017, NiculescuMizil2005, etc.) | Pending — Pass 1 calibration draft. 17 distinct keys. Polish ~14.7k chars. Key Pass 2 questions: (1) verify SVM-linear inclusion/exclusion decision after Phase 03; (2) confirm GNN deferral to §7.3 future work; (3) verify MLP role as bottom-of-hierarchy baseline post Phase 04. |
| §2.6 Evaluation metrics | thesis/chapters/02_theoretical_background.md | 2026-04-17 | 2 [REVIEW] | thesis/references.bib (13 new entries: Brier1950, Murphy1973, HanleyMcNeil1982, Friedman1937, Wilcoxon1945, Holm1979, GarciaHerrera2008, Garcia2010, Benavoli2016, Benavoli2017, Nadeau2003, Dietterich1998, Bouckaert2003) | Pending — Pass 1 calibration draft. 14 distinct keys. Polish ~12.8k chars. Key Pass 2 questions: (1) verify cross-game N=2 protocol concordance qualitative analysis after Phase 04; (2) verify F 5x2 cv test applicability with temporal splits (assumption of independent draws may be violated). |
| §3.1 Traditional sports prediction | thesis/chapters/03_related_work.md | 2026-04-17 | 0 [REVIEW] | thesis/references.bib (5 new entries: Dixon1997, Maher1982, Constantinou2013, Bunker2024, Glickman1995) | Pending — Pass 1 calibration draft. 11 distinct keys. Polish ~7.8k chars. Key Pass 2 questions: (1) confirm Glickman1995 American Chess Journal as canonical Glicko intro vs Glickman1999; (2) verify Constantinou2013 venue/pages; (3) verify Bunker2024 SAGE journal vol/issue/pages; (4) confirm Maher1982 as canonical pre-Dixon-Coles independent-Poisson reference. |
| §3.3 MOBA and other esports | thesis/chapters/03_related_work.md | 2026-04-17 | 2 [REVIEW] | thesis/references.bib (5 new entries: Yang2017Dota, Bahrololloomi2023, Akhmedov2021, Silva2018LoL, Yangibaev2025) | Pending — Pass 1 calibration draft. 13 distinct keys. Polish ~11.4k chars. Key Pass 2 questions: (1) replace Counter-Strike paragraph generic claims with peer-reviewed Xenopoulos et al. or canonical IEEE work; (2) validate Valorant claims with peer-reviewed source; (3) confirm Yangibaev2025 98.6% accuracy figure context (late-game timepoints); (4) verify Silva2018LoL SBGames pagination. |
| §2.1 Gry strategiczne czasu rzeczywistego | thesis/chapters/02_theoretical_background.md | 2026-04-17 | 1 [REVIEW] | thesis/references.bib (Buro2003 added) | Pending — Pass 1 calibration draft. 9 distinct keys cited. Polish ~12.0k chars. Key Pass 2 question: confirm after Phase 04 whether the empirical SC2 vs AoE2 difficulty asymmetry justifies strengthening or softening the closing claim. |
| §2.2 StarCraft II | thesis/chapters/02_theoretical_background.md | 2026-04-17 (post-adversarial revision) | 1 [REVIEW] | thesis/references.bib (4 new entries from Sprint 7: Liquipedia_GameSpeed, BlizzardS2Protocol, Wikipedia_SC2Esports, Liquipedia_ESLProTour) | Pending — Pass 1 + post-adversarial revision. Adversarial caught BLOCKER scope creep — §2.2.5 "Korpus SC2EGSet" subsection deleted entirely; SC2EGSet corpus statistics deferred to §4.1.1; UAlbertaBot orphan citation removed. 12 distinct keys cited. Polish ~12.5k chars (was 14.5k pre-fix). Remaining Pass 2 question: align grey-literature acceptability for Liquipedia_GameSpeed and BlizzardS2Protocol with §2.5.4 Battle.net MMR decision (peer-reviewed alternative would be Vinyals2017 if it explicitly states the timing constants). |
| §2.3 Age of Empires II | thesis/chapters/02_theoretical_background.md | 2026-04-17 (post-adversarial revision) | 2 [REVIEW] | thesis/references.bib (5 new entries retained: AoE2DE, MgzParser, AoEStats, AoeCompanion, AoE2MapPool) | Pending — Pass 1 + post-adversarial revision. Adversarial caught BLOCKER scope creep — §2.3.4 trimmed (corpus numbers moved to §4.1.2 staging); §2.3.3 first paragraph cut (player roster + Red Bull Wololo Londinium removed); K-factor paragraph forward-ref'd to §2.5.4. 7 distinct keys cited. Polish ~9.5k chars (was 13.8k pre-fix). Remaining Pass 2 questions: (1) verify exact civilization count for the corpus window; (2) verify Liquipedia + GitHub URLs grey-literature acceptability per PJAIT thesis guidelines. |

## Completed Pass 2 reviews

| Section | Reviewed date | Reviewer notes |
|---------|--------------|----------------|
| *(none yet)* | | |

## How to use this in Claude Chat

When bringing a section for Pass 2 review, provide Claude Chat with:
1. The section text from `thesis/chapters/XX_*.md`
2. The report artifacts listed in the "Key artifacts" column
3. The specific `[REVIEW: ...]` flags from the draft
4. Any `[NEEDS CITATION]` flags (Claude Chat will search the literature)

Claude Chat will return: resolved flags, suggested citations, methodology
alignment checks, and any corrections to statistical interpretation.
