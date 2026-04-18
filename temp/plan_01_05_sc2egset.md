# Plan: Phase 01 / Pipeline Section 01_05 — Temporal & Panel EDA (sc2egset)

This is a **FUTURE-SESSION candidate plan**. The parent will not promote it to `planning/current_plan.md`; it will live at `temp/plan_01_05_sc2egset.md` pending user approval in the next session. Frontmatter is a stub because the plan is not yet active.

```yaml
---
# Layer 1 — frontmatter (stub — plan not yet active)
category: A
branch: feat/sc2-sc2egset-phase01-pipeline-section-01_05
date: 2026-04-18
planner_model: claude-opus-4-7
dataset: sc2egset
phase: "01"
pipeline_section: "01_05"
invariants_touched: [I3, I4, I6, I7, I9, I10]
source_artifacts:
  - docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md  # §5.1-5.5
  - docs/PHASES.md  # canonical section list: 01_05 = Temporal & Panel EDA
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md  # 01_04_* predecessors
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/matches_flat_clean.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_history_all.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md  # temporal_coverage, temporal_month_gaps, calendar gap count = 32
  - thesis/chapters/04_data_and_methodology.md  # §4.1.3 Tabela 4.4a (temporal-density row pointer), §4.4.1 (split-strategy feeder)
  - .claude/scientific-invariants.md  # I3, I4, I9 discipline
critique_required: true
research_log_ref: src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md#2026-XX-XX-phase01-01_05-temporal-panel-eda
---
```

---

## Scope

Phase 01 / Pipeline Section **01_05 Temporal & Panel EDA** for **sc2egset only**. Produces three sequential steps (01_05_01 → 01_05_02 → 01_05_03) that characterise (i) the corpus's temporal density and regime structure (patch / game-version / tournament-episode boundaries), (ii) the per-player panel shape (activity distribution, cold-start vs veteran stratification, survivorship risk), and (iii) split-design inputs feeding Phase 03 — minimum history length, cold-start threshold candidates, purge/embargo window sizing evidence — along with a formal temporal-leakage audit of both analytical views. All three steps are read-only over `matches_flat_clean` and `player_history_all`; no VIEW DDL changes, no raw-table changes, no feature engineering (that is Phase 02). This plan is single-dataset; cross-game/cross-dataset synthesis is explicitly deferred.

## Problem Statement

Phase 01 has established the cleaned corpus (22,209 true-1v1 decisive replays spanning 2016-01-07 to 2024-12-01, 2,470 distinct `toon_id` in `matches_flat_clean`, 2,495 in `player_history_all`) and documented column-level provenance via the I3 category tags in the schema YAMLs. What remains before Phase 01 can close (`01_06 Decision Gates`) is the **temporal and panel dimension** of the data — distinct from the column-wise profiling already completed. Specifically, the downstream decisions that cannot be made without 01_05 outputs are:

1. **Temporal split window sizing (§4.4.1).** Phase 03 must decide the test-holdout unit (last-tournament-per-player? last-N-games-per-player? calendar window?) and the purge/embargo discipline between folds. That decision requires knowing the per-player temporal density: how many players have enough history to support an N-game holdout, how long are the typical gaps between consecutive games for a given player, and whether the corpus's tournament-episodic structure (70 tournament directories, 32 calendar-month gaps confirmed in 01_03_01) violates the independence assumption that stock PurgedKFold implementations rest on (de Prado 2018).

2. **Thesis Tabela 4.4a "Pokrycie czasowe" row enrichment.** The current entry reads "2016-01-07 — 2024-12-01 (turniejowe, nieciągłe, 32 luki miesięczne)" — true but thin. To defend cross-corpus comparability against aoestats/aoe2companion (both of which are continuous-ladder feeds), the thesis needs: density per active month, per-tournament clustering, patch-boundary regime shifts, and whether the 32 gap months are genuinely empty or artefacts of upstream indexing.

3. **§4.4.1 per-player split justification.** Invariant I1 says "the split is per-player, not per-game." Defending this requires an empirical panel-shape story: mean, median, P10/P90 games per player; what fraction of players have fewer than 3 games (cold-start); what fraction of players appear only in a single tournament; the within-player vs between-player variance decomposition of the target (Manual §5.3).

4. **§6.5 generalisation-limits argument.** The thesis's threats-to-validity chapter needs a quantified survivorship-bias assessment (Manual §5.4; Czeisler 2021; STRATOS/Lusa 2024) and a temporal-leakage audit artifact it can cite.

01_05 produces the four artifacts that close these gaps. 01_06 then formalises the Phase 01 exit decision based on them.

## Assumptions & unknowns

- **Assumption:** `details_timeUTC` is a usable temporal anchor when CAST via `TRY_STRPTIME` or `TRY_CAST AS TIMESTAMP` — it is ISO-8601 with a trailing `Z` suffix and fractional seconds. Validated empirically on the live DuckDB (min=`2016-01-07T02:21:46.002Z`, max=`2024-12-01T23:48:45.2511615Z`). The step must test for CAST failures and report the count in the artifact.
- **Assumption:** The tournament directory name is a valid episode-grouping key, recoverable from `matches_flat_clean.filename` via `split_part(filename, '/', 1)`. Confirmed via a 5-row probe (top tournaments range from 1,582 to 2,582 player-rows).
- **Assumption:** `metadata_gameVersion` (46 distinct values per 01_03_01 drafting) is a valid patch-regime proxy. The step must validate this by tabulating rows-per-version with min/max timestamps per version, and flag any non-monotonic version introduction (version X appearing before version X-1's last timestamp) as an anomaly in the ledger.
- **Assumption:** Panel data structure uses `toon_id` as the player identity key — consistent with the `IDENTITY` tag in both schema YAMLs. Invariant I2 (canonical nickname) is a Phase-02 feature-engineering concern; for 01_05, the per-player panel uses `toon_id` as the grouping key, with a cross-check count of how many `toon_id`s share a nickname and vice versa (multi-account/rename-detection staging, not resolution).
- **Unknown:** Whether the 32 calendar-month gaps are genuine empty months or indexing artefacts. Resolved during T01 by cross-referencing `tournament_dir` temporal coverage against the month-gap list.
- **Unknown:** Whether `metadata_gameVersion` alone is a sufficient patch-regime proxy, or whether `header_version` / `metadata_baseBuild` / `metadata_dataBuild` provide more stable boundaries. Resolved during T01 by comparing cardinalities and regime-shift counts across the four candidate columns.
- **Unknown:** User-decisions on cold-start threshold, minimum-history length, purge window, embargo window — see Open questions. The plan proposes candidates derived empirically from the distribution; the user selects before 01_06.
- **Unknown:** Whether survivorship bias is quantitatively severe enough to require a restriction to "survivors" or merely a threats-to-validity footnote. T02 reports the evidence; 01_06 decides.

## Literature context

**Temporal validation without random splits.** [de Prado (2018), *Advances in Financial Machine Learning*, Ch. 7] establishes purging and embargoing as the discipline for cross-validation when the IID assumption fails because target labels have overlapping information horizons. The PurgedKFold paradigm is explicit about what 01_05 must measure: the information horizon length (how far ahead a target game "reaches back" via features) and the embargo (how long after a test fold's end before the next training sample is admissible). In SC2, the information horizon for a typical pre-game feature (e.g., rolling 30-day win rate) is 30 days; the embargo corresponds to how long a patch-boundary effect propagates into player behaviour. Both of these are empirical quantities that 01_05 characterises. See also [Arlot & Celisse (2010)] for the variance-bias trade-off framing and the normalization-leakage warning cited in Invariant I3.

**Panel data and non-stationarity in esports.** [Chitayat et al. (2023)] explicitly document that esports titles change so rapidly that analytics models have a short life-span — the meta shifts with each patch, producing abrupt changes in feature-target relationships. [Davis et al. (2024), *Machine Learning* 113:6977–7010] is the most comprehensive recent sports-analytics-methodology paper; they identify nested dependencies (matches within seasons, players within teams, games within patches) as the central source of optimistic-bias in sports outcome models. Both are already in `references.bib` (cited in 01_04_01). The [ADF test] (null: non-stationarity) and [KPSS test] (null: stationarity) are the complementary formal stationarity checks; [PSI] (Population Stability Index) and [KS / Wasserstein] the distributional-shift detection methods.

**Survivorship bias.** [Czeisler et al. (2021)] demonstrated in longitudinal survey data that restricting analysis to "survivors" produces systematically optimistic conclusions. The [STRATOS Initiative / Lusa et al. (2024), *PLOS ONE*] IDA checklist for longitudinal studies formalises five screening explorations; 01_05_02 follows this checklist's panel-profile, missingness-by-time, and attrition-pattern branches. In the sc2egset corpus, the relevant threat is that professional players who stop performing well may exit the pro-tournament circuit, so their trajectory is censored — and if quit-probability correlates with loss rate, the observed win-rate distribution is biased.

**Change-point / regime-shift detection.** For patch-boundary regime-shift characterisation, [BEAST / Bayesian change-point detection] is the canonical Bayesian method; the TensorFlow Probability tutorial "Multiple changepoint detection and Bayesian model selection" gives a reference implementation. For a thesis-grade Phase 01 audit, the less-ambitious frequentist alternative is sufficient: bin rows by `metadata_gameVersion` and run a Kruskal-Wallis test on within-bin target rate (win-rate for `side=0`) against between-bin variation, augmented by visual inspection of target-rate-over-time plotted at monthly granularity with version boundaries overlaid. Bayesian change-point is listed as an optional stretch task (T01 variant).

**Temporal leakage audit.** Manual §5.5's "for every feature, ask *could this value be computed strictly before the prediction timestamp?*" is the operational rule. For 01_05 there are no Phase-02 features yet, so the audit is structural: confirm that every non-IDENTITY, non-CONTEXT, non-PRE_GAME column in both VIEWs is tagged IN_GAME_HISTORICAL or POST_GAME_HISTORICAL (already established by 01_04_02), and verify that the `details_timeUTC` temporal anchor is present, non-null, and monotonic-across-`toon_id`-trajectories to a tolerance consistent with tournament scheduling. This forms the I3 baseline for Phase 02 to inherit.

**Not load-bearing but worth citing once.** [Gebru et al. *Datasheets*] for the panel-shape documentation convention; [CRISP-ML(Q)] for the quality-gate framing carried forward to 01_06; [STRATOS/Lusa 2024] for the IDA longitudinal-analysis taxonomy.

[OPINION] Bayesian change-point detection (BEAST / BOCPD) is mentioned in the prompt's WebSearch list as an option; my read is that for a Phase 01 EDA step whose purpose is hypothesis generation (not confirmatory inference), the frequentist approach of "bin by version, plot target rate, Kruskal-Wallis test" is proportionate and defensible. Bayesian change-point is deferred to Phase 05 if the thesis needs a formal regime-identification argument.

## Execution Steps

### T01 — 01_05_01 Temporal profiling

**Objective.** Characterise the corpus's temporal structure at three levels — calendar-continuous, tournament-episodic, patch-regime — and produce the evidence that closes Tabela 4.4a's "Pokrycie czasowe" row. Test stationarity, detect regime shifts, and quantify the gap structure.

**Inputs.**
- `matches_flat_clean` (28 cols, 44,418 rows, 22,209 replays) — read-only.
- `player_history_all` (37 cols, 44,817 rows, 22,390 replays) — read-only.
- `artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md` (temporal_coverage, temporal_month_gaps, calendar-month-gap count 32).
- `schemas/views/matches_flat_clean.yaml` (column provenance: `details_timeUTC`, `metadata_gameVersion`, `header_version`).

**Outputs.**
- Notebook: `sandbox/sc2/sc2egset/01_exploration/05_temporal_and_panel_eda/01_05_01_temporal_profiling.py` + paired `.ipynb`.
- `reports/artifacts/01_exploration/05_temporal_and_panel_eda/01_05_01_temporal_profiling.json` (machine-readable summary + all SQL verbatim).
- `reports/artifacts/01_exploration/05_temporal_and_panel_eda/01_05_01_temporal_profiling.md` (narrative + tables).
- Plots in `reports/artifacts/01_exploration/05_temporal_and_panel_eda/plots/`:
  - `01_05_01_monthly_match_density.png` — rows-per-calendar-month with gaps highlighted.
  - `01_05_01_tournament_episode_timeline.png` — Gantt-style plot of tournament min/max timestamps, showing clustering.
  - `01_05_01_version_regime_target_rate.png` — target rate for `side=0` over time, with `metadata_gameVersion` boundaries overlaid.
  - `01_05_01_gap_overlay.png` — the 32 calendar-month gaps from 01_03_01 overlaid on tournament episodes, to confirm whether gaps are between-tournament or within-tournament-with-zero-density.

**SQL queries (verbatim; all stored in `sql_queries` JSON block per I6).**

```sql
-- Q01: per-calendar-month match density.
SELECT
    strftime(TRY_CAST(details_timeUTC AS TIMESTAMP), '%Y-%m') AS year_month,
    COUNT(DISTINCT replay_id) AS replays,
    COUNT(*) AS player_rows,
    COUNT(DISTINCT toon_id) AS distinct_players,
    COUNT(DISTINCT split_part(filename, '/', 1)) AS distinct_tournament_dirs
FROM matches_flat_clean
WHERE details_timeUTC IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- Q02: per-tournament-directory temporal envelope.
SELECT
    split_part(filename, '/', 1) AS tournament_dir,
    COUNT(DISTINCT replay_id) AS replays,
    MIN(TRY_CAST(details_timeUTC AS TIMESTAMP)) AS t_min,
    MAX(TRY_CAST(details_timeUTC AS TIMESTAMP)) AS t_max,
    EXTRACT(EPOCH FROM (MAX(TRY_CAST(details_timeUTC AS TIMESTAMP))
                      - MIN(TRY_CAST(details_timeUTC AS TIMESTAMP)))) / 86400.0 AS span_days
FROM matches_flat_clean
WHERE details_timeUTC IS NOT NULL
GROUP BY 1
ORDER BY t_min;

-- Q03: patch-regime proxy candidates — cardinality and monotonicity check.
SELECT
    'metadata_gameVersion' AS col,
    COUNT(DISTINCT metadata_gameVersion) AS n_distinct,
    COUNT(*) FILTER (WHERE metadata_gameVersion IS NULL) AS n_null
FROM matches_flat_clean
UNION ALL
SELECT 'header_version', COUNT(DISTINCT header_version), COUNT(*) FILTER (WHERE header_version IS NULL) FROM matches_flat_clean
UNION ALL
SELECT 'metadata_baseBuild', COUNT(DISTINCT metadata_baseBuild), COUNT(*) FILTER (WHERE metadata_baseBuild IS NULL) FROM matches_flat_clean
UNION ALL
SELECT 'metadata_dataBuild', COUNT(DISTINCT metadata_dataBuild), COUNT(*) FILTER (WHERE metadata_dataBuild IS NULL) FROM matches_flat_clean;

-- Q04: per-version target rate for side=0 (to expose patch-regime shifts).
WITH side0 AS (
    SELECT replay_id, MAX(CASE WHEN playerID = 0 THEN result END) AS side0_result,
           MAX(metadata_gameVersion) AS ver,
           MIN(TRY_CAST(details_timeUTC AS TIMESTAMP)) AS t_min
    FROM matches_flat_clean
    GROUP BY 1
)
SELECT
    ver,
    COUNT(*) AS n_replays,
    MIN(t_min) AS first_seen,
    MAX(t_min) AS last_seen,
    COUNT(*) FILTER (WHERE side0_result = 'Win') * 1.0 / COUNT(*) AS side0_win_rate
FROM side0
WHERE ver IS NOT NULL
GROUP BY 1
ORDER BY first_seen;

-- Q05: calendar-continuous target rate (monthly) for regime-shift visualisation.
WITH side0 AS (
    SELECT replay_id,
           MAX(CASE WHEN playerID = 0 THEN result END) AS side0_result,
           MIN(TRY_CAST(details_timeUTC AS TIMESTAMP)) AS t_min
    FROM matches_flat_clean
    GROUP BY 1
)
SELECT
    strftime(t_min, '%Y-%m') AS year_month,
    COUNT(*) AS n_replays,
    COUNT(*) FILTER (WHERE side0_result = 'Win') * 1.0 / COUNT(*) AS side0_win_rate
FROM side0
WHERE t_min IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- Q06: gap validation — confirm 32 gap months from 01_03_01 against clean-VIEW data.
WITH months AS (
    SELECT DISTINCT strftime(TRY_CAST(details_timeUTC AS TIMESTAMP), '%Y-%m') AS year_month
    FROM matches_flat_clean
    WHERE details_timeUTC IS NOT NULL
),
calendar AS (
    SELECT strftime(dte, '%Y-%m') AS year_month
    FROM generate_series(
        DATE '2016-01-01',
        DATE '2024-12-01',
        INTERVAL 1 MONTH
    ) AS t(dte)
    GROUP BY 1
)
SELECT cal.year_month AS missing_month
FROM calendar cal
LEFT JOIN months m ON cal.year_month = m.year_month
WHERE m.year_month IS NULL
ORDER BY 1;

-- Q07: CAST-failure audit (I6 reproducibility).
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE details_timeUTC IS NULL) AS null_rows,
    COUNT(*) FILTER (WHERE details_timeUTC IS NOT NULL AND TRY_CAST(details_timeUTC AS TIMESTAMP) IS NULL) AS cast_failures
FROM matches_flat_clean;
```

**Statistical tests (run in Python on the SQL outputs).**
- **ADF test** on monthly match count series: H0 = non-stationary. Report p-value + test stat.
- **KPSS test** on the same series: H0 = stationary. Complementary to ADF.
- **Kruskal-Wallis** on monthly `side=0` win-rate across version regimes (groups = `metadata_gameVersion`): H0 = equal medians. Report H-statistic + p-value.
- **Levene** on monthly replay count by year bucket (2016-2017 / 2018-2020 / 2021-2024): H0 = equal variances.

**Verification.**
- All 7 SQL queries executable on `src/rts_predict/games/sc2/datasets/sc2egset/data/db/db.duckdb` and returning non-empty results.
- JSON artifact contains `sql_queries` block with all 7 queries verbatim, `results_summary` block with numerical findings, `statistical_tests` block with ADF/KPSS/Kruskal-Wallis/Levene outputs.
- MD artifact contains 4 PNG plots, a "Temporal profile findings" summary table, a "Gap validation" table (32 months from 01_03_01 ↔ re-derived list), a "Patch-regime candidates comparison" table (4 columns ranked by cardinality / gap-free coverage).
- Gap validation cross-check: Q06 output must have exactly 32 rows (consistency with 01_03_01 finding); if it differs, MD must document the discrepancy and adjudicate.
- CAST-failure count (Q07) must be 0 (or documented explicitly if non-zero).

**Halt conditions.**
- More than 1% of `details_timeUTC` rows fail to cast to TIMESTAMP (suggests upstream corruption).
- Gap validation discrepancy (Q06 ≠ 32) that cannot be attributed to an adjudicated cause.
- Kruskal-Wallis p < 0.001 AND effect size (eta²) > 0.15 simultaneously across the largest 5 versions — this would be a strong enough regime-shift signal that 01_05_03's split-design inputs must explicitly plan to bin train/test by regime.

**Char budget for doc artifacts.**
- `.json`: target 20-40 KB (SQL + tests + raw results + per-month densities).
- `.md`: target 14-22 KB (narrative + 4 tables + 4 figure references).

---

### T02 — 01_05_02 Panel profiling

**Objective.** Characterise the per-player panel structure: distribution of games per player, active-window lengths, cold-start vs veteran distribution, within-player vs between-player variance decomposition of the target (Manual §5.3), and a quantified survivorship-bias assessment (Manual §5.4; Czeisler 2021 / STRATOS-Lusa 2024). Produces the evidence that 01_05_03 uses to size split windows and that §4.4.1 uses to defend per-player splitting.

**Inputs.**
- `matches_flat_clean` and `player_history_all` (read-only).
- T01's output `01_05_01_temporal_profiling.json` (reads tournament/version structure to stratify panel shape).

**Outputs.**
- Notebook: `sandbox/sc2/sc2egset/01_exploration/05_temporal_and_panel_eda/01_05_02_panel_profiling.py` + paired `.ipynb`.
- `reports/artifacts/01_exploration/05_temporal_and_panel_eda/01_05_02_panel_profiling.json`.
- `reports/artifacts/01_exploration/05_temporal_and_panel_eda/01_05_02_panel_profiling.md`.
- Plots:
  - `01_05_02_games_per_player_distribution.png` — log-log histogram of per-player game counts (expect power-law-ish shape).
  - `01_05_02_active_window_per_player.png` — distribution of (`t_max - t_min`) per `toon_id`.
  - `01_05_02_inter_game_gap_per_player.png` — distribution of consecutive-game gaps within `toon_id` trajectories.
  - `01_05_02_win_rate_by_games_played.png` — mean `side=0` win-rate bucketed by player's total game count (survivorship diagnostic: if win-rate rises with game count, surviving players are winners).
  - `01_05_02_tournament_coverage_per_player.png` — number of tournament directories a player appears in (single-event vs career pros).

**SQL queries (verbatim).**

```sql
-- Q01: panel size summary.
SELECT
    COUNT(DISTINCT toon_id) AS n_players,
    COUNT(*) AS n_player_rows,
    AVG(n_games) AS mean_games_per_player,
    quantile_cont(n_games, 0.50) AS p50,
    quantile_cont(n_games, 0.10) AS p10,
    quantile_cont(n_games, 0.90) AS p90,
    quantile_cont(n_games, 0.99) AS p99,
    MIN(n_games) AS min_games,
    MAX(n_games) AS max_games
FROM (SELECT toon_id, COUNT(*) AS n_games FROM matches_flat_clean GROUP BY 1);

-- Q02: cold-start / veteran banding (candidate thresholds; user selects in Open questions).
SELECT
    CASE
        WHEN n_games = 1 THEN 'singleton (1 game)'
        WHEN n_games BETWEEN 2 AND 4 THEN 'cold-start (2-4)'
        WHEN n_games BETWEEN 5 AND 19 THEN 'regular (5-19)'
        WHEN n_games BETWEEN 20 AND 99 THEN 'active (20-99)'
        ELSE 'veteran (100+)'
    END AS band,
    COUNT(*) AS n_players,
    COUNT(*) * 1.0 / SUM(COUNT(*)) OVER () AS pct_players,
    SUM(n_games) AS n_rows_band,
    SUM(n_games) * 1.0 / SUM(SUM(n_games)) OVER () AS pct_rows
FROM (SELECT toon_id, COUNT(*) AS n_games FROM matches_flat_clean GROUP BY 1)
GROUP BY 1
ORDER BY MIN(n_games);

-- Q03: per-player active window + inter-game gap statistics.
WITH events AS (
    SELECT
        toon_id,
        TRY_CAST(details_timeUTC AS TIMESTAMP) AS ts,
        ROW_NUMBER() OVER (PARTITION BY toon_id ORDER BY TRY_CAST(details_timeUTC AS TIMESTAMP)) AS rn
    FROM matches_flat_clean
    WHERE details_timeUTC IS NOT NULL
),
per_player AS (
    SELECT
        toon_id,
        MIN(ts) AS t_first,
        MAX(ts) AS t_last,
        EXTRACT(EPOCH FROM (MAX(ts) - MIN(ts))) / 86400.0 AS active_window_days,
        COUNT(*) AS n_games
    FROM events
    GROUP BY toon_id
)
SELECT
    COUNT(*) AS n_players,
    quantile_cont(active_window_days, 0.50) AS median_active_days,
    quantile_cont(active_window_days, 0.10) AS p10_active_days,
    quantile_cont(active_window_days, 0.90) AS p90_active_days,
    quantile_cont(active_window_days, 0.99) AS p99_active_days
FROM per_player
WHERE n_games >= 2;

-- Q04: inter-game gap distribution (consecutive match spacing within player).
WITH events AS (
    SELECT
        toon_id,
        TRY_CAST(details_timeUTC AS TIMESTAMP) AS ts,
        LAG(TRY_CAST(details_timeUTC AS TIMESTAMP))
            OVER (PARTITION BY toon_id ORDER BY TRY_CAST(details_timeUTC AS TIMESTAMP)) AS prev_ts
    FROM matches_flat_clean
    WHERE details_timeUTC IS NOT NULL
)
SELECT
    COUNT(*) AS n_intervals,
    quantile_cont(EXTRACT(EPOCH FROM (ts - prev_ts)) / 86400.0, 0.10) AS p10_gap_days,
    quantile_cont(EXTRACT(EPOCH FROM (ts - prev_ts)) / 86400.0, 0.50) AS p50_gap_days,
    quantile_cont(EXTRACT(EPOCH FROM (ts - prev_ts)) / 86400.0, 0.90) AS p90_gap_days,
    quantile_cont(EXTRACT(EPOCH FROM (ts - prev_ts)) / 86400.0, 0.99) AS p99_gap_days,
    MAX(EXTRACT(EPOCH FROM (ts - prev_ts)) / 86400.0) AS max_gap_days
FROM events
WHERE prev_ts IS NOT NULL;

-- Q05: survivorship-bias diagnostic — target rate by player-game-count band.
WITH per_player_stats AS (
    SELECT
        toon_id,
        COUNT(*) AS n_games,
        AVG(CASE WHEN result = 'Win' THEN 1.0 ELSE 0.0 END) AS win_rate
    FROM matches_flat_clean
    GROUP BY 1
)
SELECT
    CASE
        WHEN n_games = 1 THEN 'singleton'
        WHEN n_games BETWEEN 2 AND 4 THEN 'cold-start'
        WHEN n_games BETWEEN 5 AND 19 THEN 'regular'
        WHEN n_games BETWEEN 20 AND 99 THEN 'active'
        ELSE 'veteran'
    END AS band,
    COUNT(*) AS n_players,
    AVG(win_rate) AS mean_win_rate,
    quantile_cont(win_rate, 0.50) AS median_win_rate,
    STDDEV(win_rate) AS sd_win_rate
FROM per_player_stats
GROUP BY 1
ORDER BY MIN(n_games);

-- Q06: tournament-coverage per player (single-event vs career distribution).
SELECT
    n_tournaments,
    COUNT(*) AS n_players
FROM (
    SELECT
        toon_id,
        COUNT(DISTINCT split_part(filename, '/', 1)) AS n_tournaments
    FROM matches_flat_clean
    GROUP BY 1
)
GROUP BY 1
ORDER BY 1;

-- Q07: within-player vs between-player variance decomposition of target (Manual §5.3).
WITH player_mean AS (
    SELECT toon_id,
           AVG(CASE WHEN result = 'Win' THEN 1.0 ELSE 0.0 END) AS mu_i,
           COUNT(*) AS n_i
    FROM matches_flat_clean
    GROUP BY 1
    HAVING COUNT(*) >= 2  -- variance undefined for singleton players
),
grand_mean AS (SELECT AVG(mu_i) AS mu FROM player_mean),
components AS (
    SELECT
        SUM(pm.n_i * POWER(pm.mu_i - gm.mu, 2)) AS between_ss,
        COUNT(*) AS n_players
    FROM player_mean pm CROSS JOIN grand_mean gm
)
SELECT * FROM components;
-- within-SS computed in Python = sum over rows of (y_ij - mu_i)^2; intra-class correlation (ICC)
-- = between_ss / (between_ss + within_ss). Reported in artifact.

-- Q08: toon_id <-> nickname ambiguity staging (for §4.2.2 identity-resolution context; not resolved here).
SELECT
    COUNT(*) AS n_toon_nickname_pairs,
    COUNT(DISTINCT toon_id) AS n_distinct_toon_id,
    COUNT(DISTINCT nickname) AS n_distinct_nickname,
    COUNT(DISTINCT toon_id) FILTER (
        WHERE toon_id IN (
            SELECT toon_id FROM matches_flat_clean
            GROUP BY toon_id HAVING COUNT(DISTINCT nickname) > 1
        )
    ) AS n_toon_with_multiple_nicknames,
    COUNT(DISTINCT nickname) FILTER (
        WHERE nickname IN (
            SELECT nickname FROM matches_flat_clean
            GROUP BY nickname HAVING COUNT(DISTINCT toon_id) > 1
        )
    ) AS n_nickname_with_multiple_toons
FROM (
    SELECT DISTINCT toon_id, nickname FROM matches_flat_clean WHERE toon_id IS NOT NULL AND nickname IS NOT NULL
);
```

**Verification.**
- All 8 SQL queries return non-empty results.
- JSON has `sql_queries` + `panel_summary` + `variance_decomposition` (with ICC computed) + `survivorship_diagnostic` + `identity_ambiguity_staging` blocks.
- MD has Panel Summary table, Cold-start / Veteran Banding table, Active-window Quantiles table, Inter-game Gap Quantiles table, Win-rate-by-band table, Tournament-coverage histogram, Variance-decomposition block with ICC, Identity-ambiguity staging note (pointing forward to §4.2.2).
- Cross-check: sum of `n_players` across bands (Q02) must equal Q01 `n_players` = 2470.
- Cross-check: sum of `n_rows_band` (Q02) must equal 44,418.
- Variance decomposition: ICC in [0, 1]; report with bootstrap 95% CI (2000 resamples).

**Halt conditions.**
- ICC > 0.95 (suggests data is essentially between-player only and the per-player split is trivially sensible) OR < 0.05 (within-player variation dominates, which would argue for a different split regime). Either extreme warrants a user-visible note before 01_05_03.
- Survivorship bias score — defined as `|mean_win_rate(veteran) - mean_win_rate(singleton)|` — > 0.15. Would warrant a §6.5 threats-to-validity paragraph but should not halt the step.
- More than 10% of `toon_id`s have multiple distinct nicknames OR more than 10% of nicknames map to multiple `toon_id`s. Escalates to §4.2.2 priority.

**Char budget.**
- `.json`: 25-45 KB.
- `.md`: 16-24 KB.

---

### T03 — 01_05_03 Split-design inputs & temporal leakage audit

**Objective.** Consolidate T01 and T02 findings into the explicit, numbered inputs that Phase 03 §4.4.1 requires — candidate minimum-history length, candidate cold-start threshold, candidate purge window, candidate embargo window, candidate holdout-unit options — AND run the I3 temporal-leakage audit on both VIEWs. Produces the structural checklist that 01_06 Decision Gates uses as its input.

**Inputs.**
- `matches_flat_clean`, `player_history_all` (read-only).
- T01 output (`01_05_01_temporal_profiling.json` + `.md`).
- T02 output (`01_05_02_panel_profiling.json` + `.md`).
- `data/db/schemas/views/matches_flat_clean.yaml`, `data/db/schemas/views/player_history_all.yaml` (provenance-tag source of truth for the I3 audit).

**Outputs.**
- Notebook: `sandbox/sc2/sc2egset/01_exploration/05_temporal_and_panel_eda/01_05_03_split_design_and_leakage_audit.py` + paired `.ipynb`.
- `reports/artifacts/01_exploration/05_temporal_and_panel_eda/01_05_03_split_design_and_leakage_audit.json`.
- `reports/artifacts/01_exploration/05_temporal_and_panel_eda/01_05_03_split_design_and_leakage_audit.md`.
- (Optional) `01_05_03_holdout_unit_feasibility.png` — bar chart: for each candidate holdout rule (last-tournament-per-player, last-3-games-per-player, last-30-days-per-player, last-calendar-year-slice), the fraction of the 2,470 players who remain with sufficient training history. Empirical input to the user-decision on split strategy.

**SQL queries (verbatim).**

```sql
-- Q01: per-VIEW column provenance audit (I3 baseline for Phase 02).
-- Uses the YAML-schema-derived tag inventory cross-checked against current DuckDB schema.
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'matches_flat_clean'
ORDER BY ordinal_position;

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'player_history_all'
ORDER BY ordinal_position;

-- Q02: monotonicity check — for each toon_id, are consecutive details_timeUTC values strictly
-- non-decreasing? Violations are candidates for timestamp-precision concerns / duplicate records.
WITH ordered AS (
    SELECT
        toon_id,
        TRY_CAST(details_timeUTC AS TIMESTAMP) AS ts,
        LAG(TRY_CAST(details_timeUTC AS TIMESTAMP))
            OVER (PARTITION BY toon_id ORDER BY TRY_CAST(details_timeUTC AS TIMESTAMP)) AS prev_ts,
        replay_id
    FROM matches_flat_clean
    WHERE details_timeUTC IS NOT NULL
)
SELECT
    COUNT(*) AS total_intervals,
    COUNT(*) FILTER (WHERE prev_ts IS NOT NULL AND ts < prev_ts) AS monotonicity_violations,
    COUNT(*) FILTER (WHERE prev_ts IS NOT NULL AND ts = prev_ts) AS simultaneous_timestamps
FROM ordered;

-- Q03: candidate holdout-unit feasibility counts.
-- Rule A: last-tournament-per-player. A player is eligible if they played in >=2 tournaments.
WITH tour_counts AS (
    SELECT toon_id, COUNT(DISTINCT split_part(filename, '/', 1)) AS n_tour
    FROM matches_flat_clean
    GROUP BY 1
)
SELECT
    'last_tournament_per_player' AS rule,
    COUNT(*) AS n_players_total,
    COUNT(*) FILTER (WHERE n_tour >= 2) AS n_players_eligible,
    COUNT(*) FILTER (WHERE n_tour >= 3) AS n_players_with_train_val_test
FROM tour_counts;

-- Rule B: last-3-games-per-player. Player eligible if they have >=6 games (3 train + 3 holdout minimum).
WITH game_counts AS (SELECT toon_id, COUNT(*) AS n_games FROM matches_flat_clean GROUP BY 1)
SELECT
    'last_3_games_per_player' AS rule,
    COUNT(*) AS n_players_total,
    COUNT(*) FILTER (WHERE n_games >= 6) AS n_players_eligible,
    COUNT(*) FILTER (WHERE n_games >= 10) AS n_players_comfortable
FROM game_counts;

-- Rule C: calendar-slice holdout (last 12 months = 2023-12-01 .. 2024-12-01).
WITH per_player AS (
    SELECT toon_id,
           MIN(TRY_CAST(details_timeUTC AS TIMESTAMP)) AS t_first,
           MAX(TRY_CAST(details_timeUTC AS TIMESTAMP)) AS t_last,
           COUNT(*) FILTER (WHERE TRY_CAST(details_timeUTC AS TIMESTAMP) >= TIMESTAMP '2023-12-01') AS n_holdout,
           COUNT(*) FILTER (WHERE TRY_CAST(details_timeUTC AS TIMESTAMP) < TIMESTAMP '2023-12-01') AS n_train
    FROM matches_flat_clean
    WHERE details_timeUTC IS NOT NULL
    GROUP BY 1
)
SELECT
    'calendar_slice_last_12_months' AS rule,
    COUNT(*) AS n_players_total,
    COUNT(*) FILTER (WHERE n_holdout >= 1) AS n_players_with_any_holdout,
    COUNT(*) FILTER (WHERE n_holdout >= 1 AND n_train >= 3) AS n_players_with_holdout_and_training,
    AVG(CASE WHEN n_holdout >= 1 THEN n_holdout ELSE 0 END) AS mean_holdout_games
FROM per_player;

-- Q04: purge/embargo window sizing — quantile of within-player inter-game gap.
-- Used to choose purge length: if P99 gap is 60 days, a 60-day purge covers 99% of natural between-game spacing.
WITH events AS (
    SELECT toon_id, TRY_CAST(details_timeUTC AS TIMESTAMP) AS ts,
           LAG(TRY_CAST(details_timeUTC AS TIMESTAMP)) OVER (PARTITION BY toon_id
               ORDER BY TRY_CAST(details_timeUTC AS TIMESTAMP)) AS prev_ts
    FROM matches_flat_clean
    WHERE details_timeUTC IS NOT NULL
)
SELECT
    quantile_cont(EXTRACT(EPOCH FROM (ts - prev_ts)) / 86400.0, 0.50) AS gap_p50_days,
    quantile_cont(EXTRACT(EPOCH FROM (ts - prev_ts)) / 86400.0, 0.90) AS gap_p90_days,
    quantile_cont(EXTRACT(EPOCH FROM (ts - prev_ts)) / 86400.0, 0.95) AS gap_p95_days,
    quantile_cont(EXTRACT(EPOCH FROM (ts - prev_ts)) / 86400.0, 0.99) AS gap_p99_days
FROM events
WHERE prev_ts IS NOT NULL;

-- Q05: forbidden-column scan (I3 structural audit).
-- Expected result: both lists empty. Names derive from 01_04_02 post-cleaning validation.
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'matches_flat_clean'
  AND column_name IN ('APM','SQ','supplyCappedPercent','header_elapsedGameLoops','MMR','highestLeague','clanTag','handicap');
-- Expect 0 rows.
```

**Python analyses.**
- From T01's monthly density series, compute the **information horizon** candidate: the minimum window W such that the rolling 30-day player-row volume is approximately stationary (ADF rejects at p < 0.05). This is the Phase-03 candidate feature-window length.
- From T02's inter-game gap distribution, propose the embargo candidate: the 95th percentile of within-player inter-game gaps (i.e., if a test-fold ends at time T, training must resume at T + embargo).
- Build the `candidate_split_inputs` block summarising: `min_history_length_candidates = [1, 3, 5, 10]`, `cold_start_thresholds = [1, 3, 5]`, `purge_windows_days = [7, 14, 30]`, `embargo_windows_days = [derived P95, P99 from Q04]`, `holdout_rule_options = {last_tournament, last_N_games, calendar_slice}` with eligibility counts from Q03.

**Verification.**
- Q02 monotonicity report: violations logged; expected low (tournament games scheduled minutes apart could register as equal-timestamp — those are expected; strictly-less-than violations should be very rare and individually investigable).
- Q05 returns zero rows (forbidden columns absent; corroborates 01_04_02 assertion).
- MD contains a "Candidate split-design inputs" section with the four numbered candidate sets + an "Unresolved" column identifying which require user decision before 01_06 (see Open questions).
- MD contains a "Temporal leakage audit" section pointing at both VIEW schema YAMLs' provenance-category blocks and asserting that the I3 baseline is documented.

**Halt conditions.**
- Q02 monotonicity violations > 5% of intervals (would indicate timestamp reliability problem incompatible with temporal splitting).
- Q05 returns any rows (forbidden column has re-appeared — 01_04_02 regression).
- No holdout rule in Q03 yields ≥ 50% eligible players under the strictest variant (would force a user-decision to re-scope Phase 03 holdout strategy).

**Char budget.**
- `.json`: 25-40 KB.
- `.md`: 18-26 KB (this step carries more narrative because it bundles the checklist for 01_06).

---

## File Manifest

| File | Action |
|------|--------|
| `sandbox/sc2/sc2egset/01_exploration/05_temporal_and_panel_eda/01_05_01_temporal_profiling.py` | Create |
| `sandbox/sc2/sc2egset/01_exploration/05_temporal_and_panel_eda/01_05_01_temporal_profiling.ipynb` | Create |
| `sandbox/sc2/sc2egset/01_exploration/05_temporal_and_panel_eda/01_05_02_panel_profiling.py` | Create |
| `sandbox/sc2/sc2egset/01_exploration/05_temporal_and_panel_eda/01_05_02_panel_profiling.ipynb` | Create |
| `sandbox/sc2/sc2egset/01_exploration/05_temporal_and_panel_eda/01_05_03_split_design_and_leakage_audit.py` | Create |
| `sandbox/sc2/sc2egset/01_exploration/05_temporal_and_panel_eda/01_05_03_split_design_and_leakage_audit.ipynb` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_and_panel_eda/01_05_01_temporal_profiling.json` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_and_panel_eda/01_05_01_temporal_profiling.md` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_and_panel_eda/01_05_02_panel_profiling.json` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_and_panel_eda/01_05_02_panel_profiling.md` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_and_panel_eda/01_05_03_split_design_and_leakage_audit.json` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_and_panel_eda/01_05_03_split_design_and_leakage_audit.md` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_and_panel_eda/plots/*.png` | Create (4 plots T01, 5 plots T02, 1 plot T03) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` | Update (3 new step entries: 01_05_01, 01_05_02, 01_05_03) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | Update (add 3 step YAML blocks under the "01_05 — Temporal & Panel EDA" heading) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/PIPELINE_SECTION_STATUS.yaml` | Update (01_05 → in_progress → complete after T03) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` | Update (one entry per step, reverse chronological) |

Note: no DuckDB VIEW / raw-table / schema-YAML changes (read-only over the I3-audited VIEWs from 01_04_02).

## Gate Condition

Pipeline Section 01_05 is `complete` when **all** of the following hold:

1. All three step JSON artifacts exist, non-empty, each containing a `sql_queries` block with every SQL verbatim (I6).
2. All three step MD artifacts exist, each documenting findings in tables that trace numerically to `sql_queries` outputs (I6).
3. All 10 plots (4 + 5 + 1) exist as PNG files at the expected paths.
4. `STEP_STATUS.yaml` has `01_05_01`, `01_05_02`, `01_05_03` → `complete` with `completed_at` dates.
5. `PIPELINE_SECTION_STATUS.yaml` has `01_05` → `complete` (derived from all three steps complete).
6. `ROADMAP.md` has the three new step YAML blocks under the "01_05 — Temporal & Panel EDA" heading, each with the full schema (phase, pipeline_section, predecessors, inputs, outputs, scientific_invariants_applied with I3/I6/I7/I9, gate, thesis_mapping, research_log_entry).
7. Three `research_log.md` entries exist, one per step, each referencing the artifact paths and summarising findings.
8. T03 output's "Candidate split-design inputs" section populated, with the "Unresolved" column clearly identifying which candidates require user decision before 01_06 can advance.
9. T03 output's "Temporal leakage audit" section asserts: (a) zero forbidden columns in `matches_flat_clean` (corroborates 01_04_02); (b) zero CAST failures of `details_timeUTC` (or <0.1% with documented adjudication); (c) monotonicity violations quantified and adjudicated.
10. No I3/I6/I9 regression: no raw-table changes, no VIEW DDL changes, no Phase 02 feature computation performed.

## Out of scope

- **Phase 02 feature engineering of any kind.** No rolling win rates, no Elo/Glicko computation, no one-hot encoding. 01_05 produces evidence about the data; Phase 02 produces features from it. Attempting to materialise features in this section violates I9 pipeline discipline.
- **Split materialisation.** This step produces *candidate* split inputs for Phase 03 to select among. It does not write any fold indices, hold-out sets, or materialised splits.
- **Player identity resolution (I2 canonical-nickname).** The Q08 `toon_id <-> nickname` staging in T02 surfaces evidence only. Actual multi-account / server-switch / rename classification is the §4.2.2 concern and a candidate Phase 01.5 task or Phase 02 prerequisite — not 01_05.
- **Imputation decisions.** The APM NULL created by 01_04_02 NULLIF (1,132 rows) is observable in the panel-profile but not imputed here. Phase 02 owns imputation.
- **Cross-dataset temporal comparison.** No comparison with aoestats or aoe2companion temporal structure in this plan. Cross-corpus synthesis happens in thesis §4.1.3 with inputs from each dataset's own 01_05 output.
- **Bayesian change-point detection.** Deferred per the [OPINION] rationale in Literature context — Phase 01 EDA uses frequentist regime-shift visualisation plus Kruskal-Wallis; BEAST/BOCPD reserved for Phase 05 if a confirmatory regime-identification claim is needed.
- **PSI / KS / Wasserstein distributional-shift metrics across patch-regimes.** These are Phase 02 feature-quality concerns (Manual 02 §5); 01_05 surfaces regime boundaries but does not quantify per-feature shift magnitudes (no features yet exist).
- **Writing thesis §4.1.3 temporal-density row revision or §4.4.1 prose.** This is Category F work and happens in a separate session after the user approves 01_05 outputs.
- **01_06 Decision Gates.** Separate Pipeline Section and separate plan.

## Open questions

All six require **user decision** before execution can proceed — the plan records the candidates derived empirically; the user selects.

1. **Holdout-unit candidate.** Which of the three Q03 rules (last-tournament-per-player / last-3-games-per-player / calendar-slice last-12-months) does the thesis adopt as the primary split? The plan computes eligibility counts for all three; the user picks the one whose eligibility fraction and semantic match §4.4.1's "last tournament = test, penultimate = val" narrative. Resolver: user decision, informed by T03 Q03.
2. **Cold-start threshold.** Given T02 Q02's five-band scheme (singleton / cold-start 2-4 / regular 5-19 / active 20-99 / veteran 100+), which band is the "veterans" cut-off for the ml-protocol's "veterans only (3+ historical matches)" reporting convention? Candidate options: 3, 5, 10. Resolver: user decision, justified against T02 Q02 distribution + Davis 2024 methodology precedent.
3. **Embargo window.** From Q04 gap quantiles, which percentile (P90 / P95 / P99) does the user adopt as the embargo length? Trade-off: larger embargo = stronger isolation from temporal leakage but fewer training samples near the test boundary. Resolver: user decision, informed by Q04 + [de Prado 2018] precedent (typically P95 for finance; patch-boundary effects in esports may warrant longer).
4. **Patch-regime proxy column.** T01 Q03 ranks `metadata_gameVersion`, `header_version`, `metadata_baseBuild`, `metadata_dataBuild` by cardinality + null-rate + monotonicity. Which one does the thesis adopt as *the* patch-regime boundary column for §4.4.1? Resolver: user decision, defaulting to the highest-cardinality gap-free candidate unless user directs otherwise.
5. **Survivorship adjustment.** If T02 Q05 shows a survivorship-bias score > 0.10 (i.e., veterans' mean win-rate exceeds singletons' by more than 10 percentage points), does the thesis (a) note it in §6.5 and proceed full-corpus, (b) report a secondary restricted-to-veterans analysis as a sensitivity arm, or (c) restrict the primary analysis to veterans with a §4.2.2-style exclusion rule? Resolver: user decision, informed by T02 Q05 + [Czeisler 2021].
6. **Monthly calendar gaps.** Should training windows span across the 32 empty calendar months, or should folds be constructed to respect episode boundaries (tournament-aware folds)? Resolver: user decision, informed by T01 Q02 Gantt plot + [Davis 2024] "nested dependencies" framing.

Additional methodological questions not requiring user decision:
- Is the ADF/KPSS pair on monthly match-count series sufficient stationarity evidence, or does the thesis need per-tournament or per-version stationarity? Resolver: planner default — per-corpus + per-major-version.
- Do we report ICC with a parametric bootstrap CI (2000 resamples) or analytical? Resolver: planner default — bootstrap, per Manual §5.3.

## Adversarial-defence rehearsal

Five likely BLOCKER challenges that reviewer-adversarial could raise, with pre-emption strategies:

1. **"The 32-calendar-month gaps are treated as empty, but you have not confirmed they are empty for a reason rather than an indexing artefact of the 2016-2023 Dreamhack hiatus. If they are methodological rather than physical, calendar-continuous density plots mislead."**
   *Pre-emption:* T01 Q06 re-derives the gap list from `matches_flat_clean` (post-cleaning) and cross-checks against 01_03_01's count of 32. T01 Q02's per-tournament temporal envelope then overlays the gaps on the tournament timeline; the MD explicitly tags each gap as either (a) between two tournaments (natural) or (b) within a tournament's envelope (indexing artefact). Any discrepancy against 01_03_01's count is adjudicated inline. The gap list is reported verbatim, not summarised.

2. **"Your ICC / variance decomposition treats each `toon_id` as an independent panel unit, but if multi-account / server-switch cases are common, the panel is fragmented and between-player variance is overestimated. You cannot defend per-player-split methodology on ICC alone without identity resolution."**
   *Pre-emption:* T02 Q08 stages the `toon_id ↔ nickname` ambiguity up front and reports `n_toon_with_multiple_nicknames` and `n_nickname_with_multiple_toons`. The MD explicitly flags this as a Phase-02-prerequisite identity-resolution concern (§4.2.2) and frames the T02 variance decomposition as *upper-bound for between-player ICC under the current toon_id grouping*. The thesis §4.4.1 split defence will cite the ICC subject to this caveat, and §6.5 carries the identity-fragmentation risk as an explicit threat to validity. No claim is made about identity uniqueness here; the staging is what 01_05 delivers, resolution is deferred.

3. **"Your purge/embargo-window candidate derivation from within-player inter-game gaps is the wrong statistic. The correct quantity for de Prado's embargo is the information-horizon of a feature (e.g., rolling-30-day win rate reaches 30 days back), not the gap between games. You are conflating two unrelated timescales."**
   *Pre-emption:* The plan already distinguishes these. Information horizon for a *pre-game* feature is a Phase-02 concern (length of the rolling window used by the feature); 01_05 only reports the *empirical* within-player gap distribution as a lower-bound datum for Phase 03 to use when selecting embargo. The MD in T03 must state explicitly: "the inter-game gap distribution is a *candidate lower bound* on embargo length — Phase 02 adds the information-horizon upper bound derived from the longest rolling window feature." T03's "Candidate split-design inputs" section labels the embargo candidate accordingly.

4. **"The frequentist Kruskal-Wallis test for regime-shift detection across 46 `metadata_gameVersion` bins is multiple-comparison-hostile and likely finds any regime shift by chance alone. Without Bayesian change-point detection or at least Bonferroni correction, the regime-shift claim is under-powered."**
   *Pre-emption:* Kruskal-Wallis is the *omnibus* test (single p-value for "any difference across groups"), not a pairwise test — so no multiple-comparison concern for the omnibus. The plan reports H-statistic plus the **eta² effect size** alongside p, so the reviewer can evaluate practical significance independently of p-value inflation. Post-hoc pairwise bin comparisons are explicitly not conducted in 01_05 (out of scope; regime-specific modelling is Phase 04). If the H-test rejects at p < 0.001 *and* eta² > 0.15 (the halt condition), the plan flags this for a user decision on whether to bin-stratify splits; it does not silently claim "regimes exist." Bayesian change-point remains a Phase-05 option for confirmatory work.

5. **"`details_timeUTC` is VARCHAR with mixed ISO formats (some with fractional seconds like `2024-12-01T23:48:45.2511615Z`, some without). `TRY_CAST AS TIMESTAMP` will silently fail on some rows and you will under-count panel activity without noticing. The entire temporal analysis rests on an unvalidated assumption about DuckDB parsing."**
   *Pre-emption:* T01 Q07 is explicitly the CAST-failure audit: it counts `details_timeUTC IS NOT NULL AND TRY_CAST(...) IS NULL`. The halt condition is `cast_failures > 1%`. The JSON reports the exact count; the MD documents any non-zero result with the first 10 offending filenames for audit. Empirical validation on the live DuckDB confirmed min=`2016-01-07T02:21:46.002Z`, max=`2024-12-01T23:48:45.2511615Z`; 01_03_01's `temporal_coverage` was computed off the same column and matched the same bounds, so DuckDB parses both formats. The plan makes the assumption explicit, empirically tests it, and halts if violated.

Additional critiques reviewer-adversarial is likely to raise (not rated BLOCKER but worth pre-empting):

6. *"Tournament-episode detection from `split_part(filename, '/', 1)` is fragile — will fail if filename is a bare basename."* Pre-emption: I10 established that `filename` stores path relative to `raw_dir` (tournament-prefixed form `2022_03_DH_SC2_Masters_Atlanta/...`), corroborated by the 5-row probe returning tournament-directory names. T01 adds a sanity assertion: `COUNT(*) FILTER (WHERE filename LIKE '/%' OR filename NOT LIKE '%/%')` must return 0.

7. *"Survivorship-bias quantification using a win-rate-by-band comparison is observational — you cannot distinguish survivorship from skill heterogeneity."* Pre-emption: Q05 is an observational diagnostic, not a causal claim. MD wording should be "consistent with survivorship" / "candidate survivorship pattern," never "demonstrates survivorship." §6.5 citation to Czeisler 2021 preserves the honest framing.

8. *"You are doing EDA checklists (Manual §5.1 stationarity, §5.2 concept drift, §5.3 variance decomposition, §5.4 survivorship) but the thesis will need to demonstrate these were *used* rather than *performed*."* Pre-emption: Every finding in T03 MD must end with a "Consequence for §4.4.1 / §4.3 / §6.5" clause. Findings without downstream consequence are noted but labeled non-load-bearing.

## Thesis mapping

Outputs from 01_05 feed the following thesis sections (per ROADMAP's per-step `thesis_mapping` convention):

- **§4.1.3 Asymetria korpusów / Tabela 4.4a "Pokrycie czasowe" row.** 01_05_01 outputs replace the current single-sentence "turniejowe, nieciągłe, 32 luki miesięczne" with the enriched row: per-active-month density statistics, per-tournament clustering count, patch-regime proxy column selection, gap-type taxonomy (between-tournament vs within-tournament-empty).
- **§4.2.2 Player identity resolution.** 01_05_02 Q08 `toon_id ↔ nickname` staging provides the empirical basis for the identity-fragmentation discussion (currently a placeholder). No claim of resolution; staging only.
- **§4.2.3 Cleaning rules and valid corpus.** 01_05_02's panel summary (games per player, cold-start distribution) feeds the "Data-driven duration threshold derivation (from Phase 01 EDA distribution)" row — though the primary duration-threshold derivation already happened in 01_03. 01_05 adds the *panel-shape* justification rather than duration.
- **§4.3.1 Common pre-game feature set.** 01_05_02's variance-decomposition ICC argument underwrites the rolling-window activity features (games in last 30/90 days) — if within-player variance is low, features like "games in last 30 days" carry little signal; if high, they are predictive. The ICC finding is cited in the activity-feature motivation paragraph.
- **§4.4.1 Train/validation/test split strategy.** 01_05_03 is the primary feeder. The "Per-player temporal split (last tournament = test, penultimate = val)" claim in the thesis becomes defensible once T03 reports eligibility counts for the last-tournament-per-player rule; the "Why per-game splits cause leakage" argument draws on the within-player ICC and inter-game-gap distribution; the "Comparison with naïve global temporal split" argument uses the regime-shift evidence from T01.
- **§4.4.4 Evaluation metrics (stratified analysis).** The cold-start / veteran banding from T02 Q02 underwrites "cold-start stratification" in the evaluation-metrics section.
- **§6.5 Threats to validity.** T02's survivorship-bias diagnostic (Q05) populates the internal-validity threats discussion. T01's patch-regime-shift evidence populates the construct-validity discussion ("is a single model valid across patches, or should the evaluation be per-regime?"). T03's temporal-leakage audit populates the internal-validity "no future-to-past leakage" guarantee.
- **(Indirect) Chapter 7 Future work.** The Phase-02 identity-resolution prerequisite (flagged in T02 Q08) and the potential Bayesian change-point confirmation (deferred from T01) both graduate to the future-work list.

---

## Critique instruction

For Category A, adversarial critique is required before execution. After this plan is approved by the user and the parent persists it to `temp/plan_01_05_sc2egset.md`, dispatch **reviewer-adversarial** to produce `temp/plan_01_05_sc2egset.critique.md` covering all plan sections before any execution begins. The critique should stress-test the five adversarial-defence rehearsal items above plus any additional weaknesses the reviewer identifies, at the standard 3-round cap (symmetric per the memory note).

---

## Sources

- [PurgedKFold / embargo — de Prado 2018 framing](https://antonio-velazquez-bustamante.medium.com/kfold-cross-validation-with-purging-and-embargo-the-ultimate-cross-validation-technique-for-time-2d656ea6f476)
- [Purged cross-validation — Wikipedia](https://en.wikipedia.org/wiki/Purged_cross-validation)
- [Combinatorial Purged CV — Quantinsti blog](https://blog.quantinsti.com/cross-validation-embargo-purging-combinatorial/)
- [skfolio CombinatorialPurgedCV reference](https://skfolio.org/generated/skfolio.model_selection.CombinatorialPurgedCV.html)
- [de Prado — "Why Most ML Funds Fail" (GARP whitepaper, extends AFML Ch.7)](https://www.garp.org/hubfs/Whitepapers/a1Z1W0000054x6lUAA.pdf)
- [Survival analysis of League of Legends churn — SNU](https://snu.elsevierpure.com/en/publications/analyzing-player-churn-in-esports-games-a-survival-analysis-of-le/)
- [Game Data Mining Competition on Churn Prediction (arXiv 1802.02301)](https://arxiv.org/pdf/1802.02301)
- [PLOS ONE — Churn prediction in casual games](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0180735)
- [KDD'23 — Data-driven decision support for player churn](https://dl.acm.org/doi/10.1145/3580305.3599759)
- [MDPI Data — Imputation for online game churn with non-login periods](https://www.mdpi.com/2306-5729/10/7/96)
- [BEAST Bayesian change-point detection](https://github.com/zhaokg/Rbeast)
- [TensorFlow Probability — Multiple change-point detection tutorial](https://www.tensorflow.org/probability/examples/Multiple_changepoint_detection_and_Bayesian_model_selection)
- [Turner et al. 2009 — Adaptive sequential Bayesian change-point detection](https://mlg.eng.cam.ac.uk/pub/pdf/TurSaaRas09.pdf)
- [NCBI PMC — Survey of time-series change-point detection methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC5464762/)