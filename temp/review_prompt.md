                                                                                                                                                                                                                      
Agent 1 — AoE2 datasets (aoe2companion + aoestats)                                                                                                                                                                         
                                                                                                                                                                                                                            
You are a reviewer-adversarial agent conducting a gap analysis of two univariate                                                                                                                                           
census notebooks for a Master's thesis on RTS match outcome prediction. Your job                                                                                                                                           
is to determine what is STILL MISSING from each notebook for a complete univariate                                                                                                                                         
census, independent of plans that have already been written. Be adversarial and                                                                                                                                            
precise — do not give the notebooks the benefit of the doubt.                                                                                                                                                              
                                                                                                                                                                                                                            
## Context                                                                                                                                                                                                                 
                                                                                                                                                                                                                            
Scientific invariants live in .claude/scientific-invariants.md. Read them first.                                                                                                                                           
The canonical EDA Manual requirements for a univariate census (Section 3.1) are:
- Null/missing count and percentage for every column                                                                                                                                                                     
- Zero count for every numeric column
- Cardinality (distinct count) for every column                                                                                                                                                                          
- Top-K for categoricals
- Histograms for numerics                                                                                                                                                                                                
- Temporal range (min, max) for timestamp columns                                                                                                                                                                        
- Distribution shape (skewness, kurtosis) — DEFERRED to step 01_03, skip
- Outlier detection (IQR fences) — DEFERRED to step 01_03, skip                                                                                                                                                          
- Post-game / leakage field annotation (Invariant #3)
- All SQL queries verbatim in the markdown artifact (Invariant #6)                                                                                                                                                       
- No magic number thresholds without citation (Invariant #7)                                                                                                                                                             
                                                                                                                                                                                                                            
## What to read                                                                                                                                                                                                            
                
For aoe2companion:                                                                                                                                                                                                         
1. .claude/scientific-invariants.md
2. src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/matches_raw.yaml                                                                                                                                  
3. src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/ratings_raw.yaml                                                                                                                                  
4. src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/leaderboards_raw.yaml                                                                                                                             
5. src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/profiles_raw.yaml                                                                                                                                 
6. sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_04_univariate_census.py                                                                                                                                          
7. planning/plan_aoe2companion_01_02_04*.md                                                                                                                                                                             
8. planning/plan_aoe2companion_01_02_04*.critique.md
                                                                                                                                                                                                                            
For aoestats:   
1. src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/matches_raw.yaml                                                                                                                                       
2. src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/players_raw.yaml                                                                                                                                       
3. src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/overviews_raw.yaml
4. sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_04_univariate_census.py                                                                                                                                               
5. planning/plan_aoestats_01_02_04*.md                                                                                                                                                                                  
6. planning/plan_aoestats_01_02_04*.critique.md                                                                                                                                                                         
                                                                                                                                                                                                                            
## What to produce
                                                                                                                                                                                                                            
For EACH dataset (aoe2companion, aoestats), output a structured report with:                                                                                                                                               

### A. What the notebook currently computes                                                                                                                                                                                
List which EDA Manual 3.1 items are present and correct in the .py source as it
stands today (before the fix plan is applied).                                                                                                                                                                             
                                                                                                                                                                                                                            
### B. What the fix plan addresses                                                                                                                                                                                         
List which gaps from the fix plan (T01, T02, ...) correspond to which EDA Manual                                                                                                                                           
3.1 items. Note any fix plan task that does NOT correspond to a 3.1 requirement                                                                                                                                            
(e.g., artifact consistency fixes).                                                                                                                                                                                        
                                                                                                                                                                                                                            
### C. What is still missing after the fix plan                                                                                                                                                                            
After applying every task in the fix plan, what EDA Manual 3.1 items would still                                                                                                                                           
be absent? Be column-level specific. Cross-reference the schema files to enumerate                                                                                                                                         
every column that needs coverage — do not assume the plan is exhaustive.                                                                                                                                                   
                                                                                                                                                                                                                            
### D. Invariant violations                                                                                                                                                                                                
Any Invariant #3 (temporal leakage), #6 (SQL verbatim), or #7 (magic numbers)                                                                                                                                              
violations still present in the notebook that the fix plan does NOT address.                                                                                                                                               
                                                                                                                                                                                                                            
### E. Verdict per dataset                                                                                                                                                                                                 
READY (fix plan is sufficient for a complete census) or GAPS REMAIN (list blockers).                                                                                                                                       
                                                                                                                                                                                                                            
Do NOT suggest fixes — only diagnose gaps. Be specific to column names and SQL                                                                                                                                             
sections. Report in under 600 words per dataset.                                                                                                                                                                           
                                                                                                                                                                                                                            
---             
Agent 2 — SC2 dataset (sc2egset)                                                                                                                                                                                           
                
You are a reviewer-adversarial agent conducting a gap analysis of the sc2egset
univariate census notebook for a Master's thesis on RTS match outcome prediction.                                                                                                                                          
Your job is to determine what is STILL MISSING from the notebook for a complete
univariate census, independent of plans already written. Be adversarial and precise                                                                                                                                        
— do not give the notebook the benefit of the doubt.
                                                                                                                                                                                                                            
## Context      
                                                                                                                                                                                                                            
Scientific invariants live in .claude/scientific-invariants.md. Read them first.
The canonical EDA Manual requirements for a univariate census (Section 3.1) are:
- Null/missing count and percentage for every column
- Zero count for every numeric column                                                                                                                                                                                    
- Cardinality (distinct count) for every column
- Top-K for categoricals                                                                                                                                                                                                 
- Histograms for numerics
- Temporal range (min, max) for timestamp columns
- Distribution shape (skewness, kurtosis) — DEFERRED to step 01_03, skip                                                                                                                                                 
- Outlier detection (IQR fences) — DEFERRED to step 01_03, skip
- Post-game / in-game field annotation (Invariant #3 — sc2egset has                                                                                                                                                      
    in-game telemetry tables; annotate which fields are known pre-game vs                                                                                                                                                  
    only available in-game)                                                                                                                                                                                                
- All SQL queries verbatim in the markdown artifact (Invariant #6)                                                                                                                                                       
- No magic number thresholds without citation (Invariant #7)                                                                                                                                                             
                                                                                                                                                                                                                            
## What to read
                                                                                                                                                                                                                            
1. .claude/scientific-invariants.md
2. src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replays_meta_raw.yaml
3. src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replay_players_raw.yaml                                                                                                                                 
4. src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/game_events_raw.yaml
5. src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/tracker_events_raw.yaml                                                                                                                                 
6. src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/message_events_raw.yaml                                                                                                                                 
7. src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/map_aliases_raw.yaml                                                                                                                                    
8. sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py                                                                                                                                                
9. planning/plan_sc2egset_01_02_04*.md                                                                                                                                                                                  
10. planning/plan_sc2egset_01_02_04*.critique.md
                                                                                                                                                                                                                            
## What to produce
                                                                                                                                                                                                                            
### A. What the notebook currently computes
List which EDA Manual 3.1 items are present and correct in the .py source as it
stands today (before the fix plan is applied). Be table-level and column-level                                                                                                                                             
specific.
                                                                                                                                                                                                                            
### B. What the fix plan addresses
List which gaps from the fix plan (T01, T02, ...) correspond to which EDA Manual
3.1 items. Note any fix plan task that does NOT correspond to a 3.1 requirement                                                                                                                                            
(e.g., artifact consistency fixes, prose corrections).
                                                                                                                                                                                                                            
### C. What is still missing after the fix plan
After applying every task in the fix plan, what EDA Manual 3.1 items would still                                                                                                                                           
be absent? sc2egset has 6 raw tables — enumerate which ones receive each type of
profiling and which do not. Cross-reference the schema files column-by-column.                                                                                                                                             
Note: game_events_raw and tracker_events_raw are event-log tables with millions                                                                                                                                            
of rows per replay — if the notebook deliberately profiles these differently                                                                                                                                               
(e.g., by event_type rather than column), flag whether that is justified or a gap.                                                                                                                                         
                                                                                                                                                                                                                            
### D. Invariant violations                                                                                                                                                                                                
Any Invariant #3 (temporal leakage — pre-game vs in-game fields), #6 (SQL verbatim                                                                                                                                         
in artifact), or #7 (magic numbers) violations still present in the notebook that                                                                                                                                          
the fix plan does NOT address.
                                                                                                                                                                                                                            
### E. Verdict                                                                                                                                                                                                             
READY (fix plan is sufficient for a complete census) or GAPS REMAIN (list blockers).
                                                                                                                                                                                                                            
Do NOT suggest fixes — only diagnose gaps. Be specific to table names, column names,                                                                                                                                       
and notebook section labels. Report in under 700 words.
                                                                                                                                                                                                                            
---             
Split rationale: Agent 1 covers the two AoE2 datasets because they share a similar table structure (matches + player stats + ratings) and the fix plans have overlapping themes. Agent 2 takes SC2 solo because sc2egset
has a fundamentally different schema (event-log tables, 6 raw tables vs 3-4) requiring a separate line of reasoning — especially the in-game vs pre-game field boundary which doesn't exist in AoE2.                       
