Sanity Validation: 16/25 checks passed
  [PASS] flat_players row count ratio: flat_players=44789, unique_matches=22377, ratio=2.00
  [PASS] matches_flat row count ratio: matches_flat=45088, unique_matches=22369, ratio=2.02
  [PASS] NULL rate audit: No NULL critical columns
  [PASS] match_time range: range: 2016-01-07 02:21:46.002000 to 2024-12-01 23:48:45.251161
  [FAIL] race distribution: unexpected races: ['BWPr', 'BWTe', 'BWZe'], all: ['BWPr', 'BWTe', 'BWZe', 'Protoss', 'Terran', 'Zerg']
  [FAIL] duplicate match_id check: 13 match_ids with != 2 rows (first: [('/Users/tomaszpionka/Downloads/SC2_Replays/2017_HomeStory_Cup_XVI/2017_HomeStory_Cup_XVI_data/6c8412ef7612d62a7fdc8f88b63b431e.SC2Replay.json', 4), ('/Users/tomaszpionka/Downloads/SC2_Replays/2017_HomeStory_Cup_XVI/2017_HomeStory_Cup_XVI_data/b9372ad82eda92aad170137c847529ac.SC2Replay.json', 8), ('/Users/tomaszpionka/Downloads/SC2_Replays/2024_05_EWC/2024_05_EWC_data/d6cdb5b7bc84ef247f4e1e65318b5654.SC2Replay.json', 8)])
  [PASS] series assignment coverage: 22369/22369 matches in series (100.0%)
  [PASS] target balance per split: all splits ~50% balanced
  [PASS] temporal leakage check: no temporal leakage
  [PASS] series containment: all series contained within one split
  [PASS] split size ratios: ratios: test=0.04, train=0.80, val=0.16
  [FAIL] constant feature check: 10 constant features: ['p1_pre_match_elo', 'p2_pre_match_elo', 'elo_diff', 'expected_win_prob', 'p1_race_BWPr', 'p1_race_BWTe', 'p1_race_BWZe', 'p2_race_BWPr', 'p2_race_BWTe', 'p2_race_BWZe']
  [FAIL] degenerate feature check: 17 degenerate features: [('elo_diff', '100.0%'), ('p1_race_BWPr', '100.0%'), ('p1_race_BWTe', '100.0%'), ('p1_race_BWZe', '100.0%'), ('p1_race_Protoss', '64.8%'), ('p1_race_Terran', '72.0%'), ('p1_race_Zerg', '63.2%'), ('p2_race_BWPr', '100.0%'), ('p2_race_BWTe', '100.0%'), ('p2_race_BWZe', '100.0%')]
  [FAIL] Elo distribution: p1_pre_match_elo std=0.0 too low; p2_pre_match_elo std=0.0 too low
  [PASS] cold-start handling: no NaN in historical features (checked 24 columns)
  [FAIL] feature correlations: 4 near-perfect correlations: [('p1_hist_winrate_smooth', 'p1_hist_winrate_as_race_smooth', 0.9965215961243133), ('p1_matches_last_7d', 'p2_matches_last_7d', 1.0), ('p1_matches_last_30d', 'p2_matches_last_30d', 1.0), ('series_game_number', 'series_length_so_far', 1.0)]
  [PASS] feature count plausibility: 64 numeric features
  [PASS] majority class baseline ~50%: majority baseline accuracy=0.5117
  [FAIL] Elo baseline above 50%: Elo-only accuracy=0.4883
  [FAIL] feature-target correlation cap: 5 features with high target correlation: [('p1_win_streak', 0.3806473810129346), ('p1_loss_streak', -0.37330884775773765), ('p2_win_streak', -0.3691219262566754), ('p2_loss_streak', 0.369385293301654), ('h2h_p1_winrate_smooth', -0.6245384263677645)]
  [FAIL] LightGBM subprocess: Subprocess exited with code -11
  [PASS] race dummies are int (not bool): all 16 race columns are non-bool
  [PASS] expanding excludes current match: first match for every player has 0 prior games
  [PASS] Elo deduplication: Elo consistent across match perspectives
  [PASS] rolling windows sparse players: no NaN in 17 form features
