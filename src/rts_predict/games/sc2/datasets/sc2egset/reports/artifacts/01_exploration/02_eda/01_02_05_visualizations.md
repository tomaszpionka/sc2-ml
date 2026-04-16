# Step 01_02_05 -- Univariate EDA Visualizations

**Dataset:** sc2egset
**Phase:** 01 -- Data Exploration
**Pipeline Section:** 01_02 -- EDA (Tukey-style)
**Predecessor:** 01_02_04 (univariate census)
**Invariants applied:** #3 (IN-GAME annotations), #6 (SQL queries inlined), #7 (no magic numbers), #9 (step scope: visualize)

## Plot Index

| # | Title | Filename | Observation | Temporal Annotation |
|---|-------|----------|-------------|---------------------|
| 1 | Result Distribution | 01_02_05_result_bar.png | Near-perfect 50/50 Win/Loss split (22,382 vs 22,409). Undecided=24 and Tie=2 excluded (13 replays total). Confirms clean binary outcome for modeling. | N/A |
| 2 | Categorical Distributions | 01_02_05_categorical_bars.png | race: Prot/Zerg/Terr ~36/35/29%. highestLeague: 72% Unknown, 14% Master, 11% Grandmaster. region: 47% Europe, 28% US. | N/A |
| 3 | selectedRace Distribution | 01_02_05_selectedrace_bar.png | 1,110 empty strings (2.48%, red bar) and 10 Rand picks; anomalous entries absent from the race column. | N/A |
| 4 | MMR Split View | 01_02_05_mmr_split.png | Left panel dominated by zero-spike (83.65% sentinel). Right panel (MMR>0) reveals unimodal distribution with long right tail toward Grandmaster. | N/A |
| 5 | APM Histogram | 01_02_05_apm_hist.png | Near-symmetric distribution (skewness=-0.20) centered around median. Esports-grade players: median ~349 APM. | IN-GAME (Inv. #3) |
| 6 | SQ Split View | 01_02_05_sq_split.png | Left panel shows INT32_MIN sentinel as isolated spike far below main mass. Right panel (sentinel excluded) shows continuous distribution in -51 to 187 range. | IN-GAME (Inv. #3) |
| 7 | supplyCappedPercent Histogram | 01_02_05_supplycapped_hist.png | Right-skewed (skewness=2.25) with median near 6; 95th percentile at 16, confirming most players rarely hit supply cap. | IN-GAME (Inv. #3) |
| 8 | Duration Dual-Panel | 01_02_05_duration_hist.png | Body panel clipped at p95=22.5 min shows main mass. Full-range log-y panel reveals extreme outliers. SC2 games shorter than AoE2 (cf. 63 min / 79 min). | POST-GAME (Inv. #3) |
| 9 | MMR Zero Cross-Tab | 01_02_05_mmr_zero_interpretation.png | MMR=0 rate uniform across result categories (~83%) and league tiers, confirming zero is a missing-data sentinel not correlated with outcome. | N/A |
| 10 | Temporal Coverage | 01_02_05_temporal_coverage.png | 2016-2024 span. Monthly volume generally increases through mid-period with visible gap in early 2016. Low-count months annotated. | N/A |
| 11 | isInClan Bar | 01_02_05_isinclan_bar.png | 74% not in clan, 26% in clan. Minority feature worth retaining for feature engineering. | N/A |
| 12 | clanTag Top-20 | 01_02_05_clantag_top20.png | Top esports organizations dominate clan tags; top-20 clans account for a substantial share of non-empty clan entries. | N/A |
| 13 | Map Top-20 | 01_02_05_map_top20.png | 188 distinct maps. Top-20 shown as barh with count and percentage. Ladder map rotation pattern visible. | N/A |
| 14 | Player Repeat Frequency | 01_02_05_player_repeat_frequency.png | 2,495 unique players across 44,817 rows (~18 games/player average). Heavily right-skewed: small pool of recurring tournament regulars. Informs Phase 03 player-aware splitting strategy. | N/A |

## SQL Queries

All DuckDB SQL queries used in this notebook (Invariant #6: reproducibility):

**hist_mmr:**
```sql
SELECT MMR FROM replay_players_raw WHERE MMR IS NOT NULL
```

**hist_apm:**
```sql
SELECT APM FROM replay_players_raw WHERE APM IS NOT NULL
```

**hist_sq:**
```sql
SELECT SQ FROM replay_players_raw WHERE SQ IS NOT NULL
```

**hist_supplycapped:**
```sql
SELECT supplyCappedPercent FROM replay_players_raw WHERE supplyCappedPercent IS NOT NULL
```

**hist_duration:**
```sql
SELECT header.elapsedGameLoops AS elapsed_game_loops FROM replays_meta_raw WHERE header.elapsedGameLoops IS NOT NULL
```

**hist_player_repeat:**
```sql
SELECT games_per_player, COUNT(*) AS player_count
FROM (
    SELECT toon_id, COUNT(*) AS games_per_player
    FROM replay_players_raw
    GROUP BY toon_id
)
GROUP BY games_per_player
ORDER BY games_per_player
```

## Data Sources

- `replay_players_raw` (DuckDB persistent table): player-level fields
- `replays_meta_raw` (DuckDB persistent table): replay-level metadata including elapsed_game_loops
- `01_02_04_univariate_census.json`: pre-computed distributions for result, categorical profiles,
  monthly counts, MMR zero-spike cross-tabulation, isInClan, clanTag top-20, cardinality
