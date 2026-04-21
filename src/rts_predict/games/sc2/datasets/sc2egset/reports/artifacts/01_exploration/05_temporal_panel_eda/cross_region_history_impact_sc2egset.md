# Cross-region History Fragmentation — Phase 02 Rolling-Feature Impact (sc2egset)

**Date:** 2026-04-21
**Notebook:** `sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_10_cross_region_history_impact.py`
**Dataset:** sc2egset
**Closes:** sc2egset WARNING 3 (`reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md §2`)

---

## §1 Scope and Method

### What this artifact measures

Phase 02 rolling-window features (e.g., `rolling_win_rate_past_30_games`,
`past_match_count`) are computed per `player_id_worldwide` (full Blizzard Battle.net
`R-S2-G-P` toon_id). For the ~12% of nicknames that appear across multiple regions
(accepted bias under I2 Branch iii, `INVARIANTS.md §2`), each region-specific
`player_id_worldwide` sees only the history from that region. A cross-region player
switching from EU to US gets a fresh Phase 02 history under their US toon_id, even
though their EU history is also present in the dataset.

This artifact quantifies the resulting bias as the **per-(player, match) rolling-window
undercount** — how many games Phase 02 under-counts relative to a hypothetical
unified-nickname baseline — at window=30 (primary) and sensitivity windows {5, 10, 100}.

### Hypothesis and 3-threshold falsifier

**H0:** Cross-region fragmentation produces negligible per-match rolling-window bias:

- **(a)** `median_rolling30_undercount ≤ 1 game`
- **(b)** `p95_rolling30_undercount ≤ 5 games` (below √30 ≈ 5.5 feature-noise floor)
- **(c)** `|bootstrap_CI_upper(mmr_spearman_rho)| < 0.2` (powered at n≈200, Hollander &
  Wolfe 1999 §11.2)

Any threshold violated → FAIL verdict. MARGINAL if violation < 50% of threshold.

**Threshold rationale (I7 — no magic numbers):**

- K=1 (median): win-rate shift from 1-game prefix difference among 30 is ≤ 3.3% absolute,
  below the typical 5–10% Phase 02 feature-signal contribution threshold.
- K=5 (p95): √30 ≈ 5.5 is the rolling-30 win-rate feature's own measurement noise at
  p=0.5 (binomial); p95 undercount below this level is statistically indistinguishable
  from feature noise.
- |ρ|<0.2: at n≈157 (achieved), Hollander & Wolfe (1999) §11.2 gives minimum detectable
  |ρ| ≈ 0.21 at α=0.05 two-sided 80% power. Threshold |ρ|<0.2 is thus powered — passing
  vacuously (underpowered) is not a risk at this sample size.

### Engines

- **Percentile engine:** DuckDB `PERCENTILE_CONT` (all percentile fields in JSON).
- **Bootstrap engine:** `scipy.stats.bootstrap + pandas` (Spearman ρ CI).

---

## §2 SQL Verbatim (I6)

All SQL blocks that produce reported results are preserved below verbatim.

### SQL 1 — Cross-region nickname identification

```sql
-- Cross-region nickname detection (INVARIANTS.md §2 verbatim)
SELECT
    COUNT(*) FILTER (WHERE region_count > 1) * 1.0 / COUNT(*) AS migration_rate,
    COUNT(*) FILTER (WHERE region_count > 1) AS cross_region_count,
    COUNT(*) AS total_nicknames
FROM (
    SELECT LOWER(nickname) AS nick, COUNT(DISTINCT region) AS region_count
    FROM replay_players_raw
    GROUP BY 1
) sub
```

### SQL 2 — Lifetime fragmentation ratio

```sql
WITH cross_region_nicks AS (
    SELECT LOWER(nickname) AS nick
    FROM replay_players_raw
    GROUP BY 1
    HAVING COUNT(DISTINCT region) > 1
),
per_region_counts AS (
    SELECT LOWER(r.nickname) AS nick,
           r.region,
           COUNT(*) AS games_in_region
    FROM replay_players_raw r
    INNER JOIN cross_region_nicks crn ON LOWER(r.nickname) = crn.nick
    GROUP BY 1, 2
),
per_nick AS (
    SELECT nick,
           MAX(games_in_region) AS max_region_games,
           SUM(games_in_region) AS total_games,
           MAX(games_in_region) * 1.0 / SUM(games_in_region) AS fragmentation_ratio
    FROM per_region_counts
    GROUP BY nick
)
SELECT
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY fragmentation_ratio) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY fragmentation_ratio) AS median,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY fragmentation_ratio) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY fragmentation_ratio) AS p95,
    COUNT(*) AS n_players
FROM per_nick
```

### SQL 3 — Per-(player, match) rolling-window undercount at window=30

```sql
WITH cross_region_nicks AS (
    SELECT LOWER(nickname) AS nick
    FROM replay_players_raw
    GROUP BY 1
    HAVING COUNT(DISTINCT region) > 1
),
player_matches AS (
    SELECT
        h.toon_id,
        LOWER(h.nickname) AS nick,
        h.details_timeUTC AS match_time,
        h.replay_id
    FROM player_history_all h
    INNER JOIN cross_region_nicks crn ON LOWER(h.nickname) = crn.nick
    WHERE h.details_timeUTC IS NOT NULL
),
ph_prior AS (
    SELECT
        pm.toon_id,
        pm.replay_id,
        pm.match_time,
        pm.nick,
        COALESCE(COUNT(*) OVER (
            PARTITION BY pm.toon_id
            ORDER BY pm.match_time
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0) AS ph_prior_count
    FROM player_matches pm
),
unified_prior AS (
    SELECT
        pm.toon_id,
        pm.replay_id,
        pm.match_time,
        COALESCE(COUNT(*) OVER (
            PARTITION BY pm.nick
            ORDER BY pm.match_time
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0) AS unified_prior_count
    FROM player_matches pm
),
combined AS (
    SELECT
        p.toon_id,
        p.nick,
        LEAST(30, u.unified_prior_count) - LEAST(30, p.ph_prior_count) AS rolling30_undercount
    FROM ph_prior p
    JOIN unified_prior u ON p.toon_id = u.toon_id AND p.replay_id = u.replay_id
)
SELECT
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY rolling30_undercount)
        AS median_rolling30_undercount,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY rolling30_undercount)
        AS p95_rolling30_undercount,
    COUNT(*) AS n_player_match_pairs,
    COUNT(DISTINCT toon_id) AS n_distinct_toon_ids,
    AVG(rolling30_undercount) AS mean_rolling30_undercount,
    MAX(rolling30_undercount) AS max_rolling30_undercount
FROM combined
```

**Temporal discipline note:** `ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING`
ordered by `details_timeUTC` (ISO-8601 VARCHAR, verified zero TRY_CAST failures;
lexicographic order = chronological order). No duplicate match times per toon_id
confirmed. This implements strict `<` (I3).

### SQL 4 — Sensitivity sweep across windows {5, 10, 30, 100}

```sql
WITH cross_region_nicks AS (
    SELECT LOWER(nickname) AS nick
    FROM replay_players_raw
    GROUP BY 1
    HAVING COUNT(DISTINCT region) > 1
),
player_matches AS (
    SELECT
        h.toon_id,
        LOWER(h.nickname) AS nick,
        h.details_timeUTC AS match_time,
        h.replay_id
    FROM player_history_all h
    INNER JOIN cross_region_nicks crn ON LOWER(h.nickname) = crn.nick
    WHERE h.details_timeUTC IS NOT NULL
),
ph_prior AS (
    SELECT
        pm.toon_id,
        pm.replay_id,
        pm.match_time,
        pm.nick,
        COALESCE(COUNT(*) OVER (
            PARTITION BY pm.toon_id
            ORDER BY pm.match_time
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0) AS ph_prior_count
    FROM player_matches pm
),
unified_prior AS (
    SELECT
        pm.toon_id,
        pm.replay_id,
        pm.match_time,
        COALESCE(COUNT(*) OVER (
            PARTITION BY pm.nick
            ORDER BY pm.match_time
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0) AS unified_prior_count
    FROM player_matches pm
),
combined AS (
    SELECT
        p.toon_id,
        p.nick,
        LEAST(5,   u.unified_prior_count) - LEAST(5,   p.ph_prior_count) AS uc5,
        LEAST(10,  u.unified_prior_count) - LEAST(10,  p.ph_prior_count) AS uc10,
        LEAST(30,  u.unified_prior_count) - LEAST(30,  p.ph_prior_count) AS uc30,
        LEAST(100, u.unified_prior_count) - LEAST(100, p.ph_prior_count) AS uc100
    FROM ph_prior p
    JOIN unified_prior u ON p.toon_id = u.toon_id AND p.replay_id = u.replay_id
)
SELECT
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY uc5)   AS median_w5,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY uc5)   AS p95_w5,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY uc10)  AS median_w10,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY uc10)  AS p95_w10,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY uc30)  AS median_w30,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY uc30)  AS p95_w30,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY uc100) AS median_w100,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY uc100) AS p95_w100,
    COUNT(*) AS n_pairs
FROM combined
```

### SQL 5 — MMR stratification (fragmentation ratio + median MMR per nickname)

```sql
WITH cross_region_nicks AS (
    SELECT LOWER(nickname) AS nick
    FROM replay_players_raw
    GROUP BY 1
    HAVING COUNT(DISTINCT region) > 1
),
per_region_counts AS (
    SELECT LOWER(r.nickname) AS nick,
           r.region,
           COUNT(*) AS games_in_region
    FROM replay_players_raw r
    INNER JOIN cross_region_nicks crn ON LOWER(r.nickname) = crn.nick
    GROUP BY 1, 2
),
frag_ratio AS (
    SELECT nick,
           MAX(games_in_region) * 1.0 / SUM(games_in_region) AS fragmentation_ratio
    FROM per_region_counts
    GROUP BY nick
),
mmr_per_nick AS (
    SELECT LOWER(r.nickname) AS nick,
           MEDIAN(r.MMR) FILTER (WHERE r.MMR > 0) AS median_mmr,
           COUNT(r.MMR) FILTER (WHERE r.MMR > 0) AS n_nonzero_mmr
    FROM replay_players_raw r
    INNER JOIN cross_region_nicks crn ON LOWER(r.nickname) = crn.nick
    GROUP BY 1
)
SELECT f.nick, f.fragmentation_ratio, m.median_mmr, m.n_nonzero_mmr
FROM frag_ratio f
JOIN mmr_per_nick m ON f.nick = m.nick
WHERE m.median_mmr IS NOT NULL AND m.median_mmr > 0
ORDER BY f.nick
```

**Bootstrap CI (Python):**

```python
from scipy import stats

boot_result = stats.bootstrap(
    (x_mmr, y_mmr),               # x = fragmentation_ratio, y = median_mmr
    lambda x, y: stats.spearmanr(x, y)[0],
    n_resamples=1000,
    confidence_level=0.95,
    random_state=42,
    paired=True,
    vectorized=False,
)
ci_low = boot_result.confidence_interval.low
ci_high = boot_result.confidence_interval.high
```

### SQL 6 — Rare-handle subsample (nickname length >= 8)

```sql
WITH cross_region_nicks AS (
    SELECT LOWER(nickname) AS nick
    FROM replay_players_raw
    GROUP BY 1
    HAVING COUNT(DISTINCT region) > 1
),
rare_handles AS (
    SELECT nick FROM cross_region_nicks
    WHERE LENGTH(nick) >= 8
),
player_matches AS (
    SELECT
        h.toon_id,
        LOWER(h.nickname) AS nick,
        h.details_timeUTC AS match_time,
        h.replay_id
    FROM player_history_all h
    INNER JOIN rare_handles rh ON LOWER(h.nickname) = rh.nick
    WHERE h.details_timeUTC IS NOT NULL
),
ph_prior AS (
    SELECT
        pm.toon_id,
        pm.replay_id,
        pm.match_time,
        pm.nick,
        COALESCE(COUNT(*) OVER (
            PARTITION BY pm.toon_id
            ORDER BY pm.match_time
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0) AS ph_prior_count
    FROM player_matches pm
),
unified_prior AS (
    SELECT
        pm.toon_id,
        pm.replay_id,
        pm.match_time,
        COALESCE(COUNT(*) OVER (
            PARTITION BY pm.nick
            ORDER BY pm.match_time
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0) AS unified_prior_count
    FROM player_matches pm
),
combined AS (
    SELECT
        p.toon_id,
        p.nick,
        LEAST(30, u.unified_prior_count) - LEAST(30, p.ph_prior_count) AS rolling30_undercount
    FROM ph_prior p
    JOIN unified_prior u ON p.toon_id = u.toon_id AND p.replay_id = u.replay_id
)
SELECT
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY rolling30_undercount) AS median_rolling30,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY rolling30_undercount) AS p95_rolling30,
    COUNT(*) AS n_pairs,
    COUNT(DISTINCT toon_id) AS n_toon_ids
FROM combined
```

---

## §3 Results

### §3.1 Cross-region nickname identification

- **Authoritative count:** 246 cross-region nicknames (of 1,045 distinct lowercased
  nicknames in `replay_players_raw`)
- **Migration rate:** 23.5% (246/1,045 lowercased nicknames appear in >1 region)
- **No drift detected:** current count matches the 246 figure in INVARIANTS.md §2.

### §3.2 Lifetime fragmentation ratio (descriptive — NOT primary metric)

| Percentile | fragmentation_ratio |
|---|---|
| p25 | 0.519 |
| p50 (median) | 0.650 |
| p75 | 0.791 |
| p95 | 0.946 |
| n players | 246 |

Interpretation: the median cross-region player concentrates 65% of their games in
their dominant region. This is a loose upper bound on Phase 02 bias (a player may
have already "saturated" their dominant-region rolling window before switching regions).

### §3.3 PRIMARY: Per-(player, match) rolling-window undercount at window=30

| Metric | Value |
|---|---|
| median_rolling30_undercount | **16.0 games** |
| p95_rolling30_undercount | **29.0 games** |
| mean_rolling30_undercount | 14.0 games |
| max_rolling30_undercount | 30 games |
| n (player, match) pairs | 32,031 |
| n distinct toon_ids | 1,923 |

At the median cross-region (player, match) pair, Phase 02 rolling-30 features
under-count by 16 games relative to a nickname-unified baseline. At p95, the
undercount reaches 29 games (essentially saturating the full 30-game window).

### §3.4 Sensitivity sweep across windows {5, 10, 30, 100}

| Window | Median undercount | p95 undercount | Threshold (a) med≤1 | Threshold (b) p95≤5 |
|---|---|---|---|---|
| W=5 | 0.0 | 5.0 | PASS | PASS (exactly at threshold) |
| W=10 | 0.0 | 9.0 | PASS | FAIL |
| W=30 | 16.0 | 29.0 | FAIL | FAIL |
| W=100 | 61.0 | 98.0 | FAIL | FAIL |

Note on W=5: p95=5.0 is exactly at the threshold boundary under the `≤ 5` rubric
(PASS at equality). Phase 02 rolling features at very small windows (W ≤ 5) are
essentially immune to cross-region fragmentation bias. At W=10 the p95 already
crosses (9 > 5). For the primary W=30 analysis, both thresholds are clearly
violated.

### §3.5 MMR stratification and bootstrap CI

| Metric | Value |
|---|---|
| n players with non-sentinel MMR | 157 (of 246) |
| Spearman ρ (point estimate) | 0.1384 |
| p-value | 0.0840 |
| Bootstrap 95% CI | [-0.0086, 0.2913] |
| \|CI_upper\| | 0.2913 |

The point estimate ρ=0.1384 suggests a weak positive association between fragmentation
and MMR (players who play more across regions may be more active and thus higher-skilled).
However, the wide CI [-0.01, 0.29] means the true ρ could range from near-zero to
materially positive. The upper bound 0.2913 > 0.2 threshold — threshold (c) is violated.

**Power commentary:** At n=157, Hollander & Wolfe (1999) §11.2 Table A.30 gives minimum
detectable |ρ| ≈ 0.21 at α=0.05 two-sided 80% power (interpolated from n=100 → 0.26 and
n=200 → 0.18). The CI upper bound 0.2913 exceeds the 0.2 threshold and exceeds the minimum
detectable effect size. We cannot rule out a meaningful positive bias-skill correlation.

### §3.6 Rare-handle subsample (length >= 8)

| Metric | Full sample (n=246) | Rare-handle (n=96) |
|---|---|---|
| n (player,match) pairs | 32,031 | 10,712 |
| median_rolling30_undercount | 16.0 | 7.0 |
| p95_rolling30_undercount | 29.0 | 29.0 |
| Spearman ρ (MMR) | 0.1384 | 0.1593 |
| Bootstrap CI_high (MMR) | 0.2913 | 0.3902 |

The rare-handle subsample (handles with length ≥ 8, reducing within-region
handle-collision contamination) shows a lower median undercount (7 vs 16 games),
suggesting that a portion of the full-sample result is driven by short handles
(e.g., "maru", "dark") where the "cross-region player" may be multiple physical
players sharing the same short handle. However, the rare-handle p95 (29.0) and
MMR CI upper bound (0.3902) remain worse than or equal to the full-sample values.
Both samples clearly fail all three thresholds.

---

## §4 Verdict

**VERDICT: FAIL**

| Threshold | Criterion | Value | Pass? |
|---|---|---|---|
| (a) median_rolling30 ≤ 1 | rolling-feature noise < 3.3% | 16.0 | FAIL |
| (b) p95_rolling30 ≤ 5 | below √30 ≈ 5.5 noise floor | 29.0 | FAIL |
| (c) \|bootstrap_CI_upper(ρ)\| < 0.2 | powered at n≈157 | 0.2913 | FAIL |

All 3 thresholds violated. MARGINAL condition (violation < 50% of threshold) does not
apply: median_rolling30=16 is 1600% over threshold, p95=29 is 480% over.

**Sensitivity robustness:** The FAIL at W=30 is robust — W=10 and W=100 also fail
threshold (b). Only W=5 has median=0 (passing threshold (a)), but its p95=5.0 is
borderline at threshold (b) and all higher windows fail decisively.

---

## §5 Thesis implication

At window=30, median undercount is 16.0 games and p95 is 29.0 games — both far above
the rolling-30 feature's √30 ≈ 5.5 measurement noise floor. Bootstrap 95% CI on the
MMR-fragmentation Spearman ρ is [-0.01, 0.29], with the upper bound 0.2913 exceeding
the |ρ|<0.2 threshold (powered at n≈157). Rolling-feature bias from cross-region
fragmentation materially exceeds the feature's own noise floor and the MMR correlation
cannot be ruled out above the power-detectable threshold. The I2 Branch (iii)
accepted-bias framing requires quantitative qualification in §4.2.2: either (a) Phase 02
must emit per-feature sensitivity analysis conditioned on `is_cross_region`, OR (b) the
294 Class A cross-region candidate pairs (INVARIANTS.md §2) must be manually curated and
unified in a follow-up Cat D PR. The rare-handle subsample (96 nicknames with length ≥ 8)
shows a lower median (7 games) but equal p95 (29 games), confirming the bias is not
solely an artifact of short-handle collision — it is a genuine fragmentation effect for
players with long, unambiguous handles. A future revision to this file will record the
Phase 02 mitigation decision.

---

## §6 Follow-up scope

Verdict is FAIL. Cat D mitigation candidates (to be decided in a separate PR):

1. **Manual-curation unification** of the 294 Class A cross-region candidate pairs
   (INVARIANTS.md §2). Assigns a unified key to confirmed same-physical-player
   cross-region pairs. Reduces the ~12% fragmentation rate for the curated subset.
   Cost: manual labour + Liquipedia/Aligulac cross-referencing for top players.

2. **Phase 02 `is_cross_region_fragmented` flag column.** Emit a boolean column
   alongside rolling-window features. Phase 02 sensitivity analysis can then compare
   model performance on cross-region vs. non-cross-region subsets. No identity
   unification required; bias is declared and controlled via stratification.

3. **Revised I2 branch decision.** If manual curation resolves the high-volume
   cross-region cases (top professional players who are overrepresented in this dataset),
   the residual ~12% may fall to an acceptable level under a re-measured threshold.

The 01_05_10 measurement is complete. Cat D scope selection is deferred to the Phase 02
planning session.
