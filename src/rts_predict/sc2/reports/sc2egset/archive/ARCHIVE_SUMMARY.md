# Archive Summary

> **All experiment runs (01–09) from the initial exploration phase are
> unreliable.** They were conducted without sufficient data preparation or
> exploration — the sanity validation found 9/25 checks failing (corrupted
> race dummies, frozen Elo, inverted baseline). All numerical results are
> invalid and must not be cited. These files have been removed; only
> cautionary lessons and untested hypotheses are preserved below.

---

## Critical Data Quality Issues Discovered

| Issue | Severity | Detail |
|-------|----------|--------|
| Corrupted race dummies | HIGH | `BWPr`, `BWTe`, `BWZe` mixed with SC2 races — BroodWar data leaking in |
| Frozen Elo (std=0) | HIGH | Both players have constant Elo across all matches |
| Elo baseline inverted | HIGH | Elo-only achieves 48.83% (below 50% majority) |
| Duplicate match_ids | MEDIUM | 13 matches with !=2 rows (violates dual-perspective) |
| Perfect feature correlations | MEDIUM | `p1_matches_last_7d == p2_matches_last_7d` (r=1.0) |
| Suspicious target correlation | MEDIUM | `h2h_p1_winrate_smooth` r=-0.625 with target |
| LightGBM SIGSEGV | LOW | Subprocess crash during baseline test |

## Ingestion Pitfalls (Relevant to Phase 0-1 Reiteration)

- Race field parsing can mix BroodWar and SC2 data — validate race enum strictly
- Elo system needs per-match verification, not just aggregate stats
- Match deduplication must enforce exactly 2 rows per match_id
- Historical features must exclude the current match (leakage found in run 07)
- Map names need canonical translation (1,488 raw -> 215 unique maps)

## Methodology Notes (from literature, not from these runs)

- Temporal CV (expanding window) is non-negotiable — k-fold inflates scores
- McNemar's test needed for model comparison
- Always check confusion matrix — majority-class collapse is easy to miss

## Models and Architectures from v1 Roadmap

**Pre-match (classical ML):**
- Logistic Regression (baseline/interpretable)
- LightGBM, XGBoost (primary workhorses per methodology)
- Random Forest (deprioritized vs LightGBM in methodology)

**In-game (sequential):**
- LSTM: 2-layer bidirectional + attention pooling + MLP head
- TCN: Dilated causal convolutions + global pooling + MLP head
- Early prediction curve: evaluate at 10%, 20%, ..., 100% game progress

**GNN (deprioritized to appendix):**
- GATv2 on player matchup graphs — collapsed to majority-class prediction
- Root cause: sparse binary graph, `pos_weight` not set, edge scaler leakage

**Fusion (planned only):**
- Dual-stream: pre-match MLP + in-game LSTM/TCN
- FT-Transformer: attention-based tabular DL (appendix only)

## Three Research Questions (Still Relevant)

1. **RQ1:** Pre-match prediction ceiling — how much do engineered features lift over Elo-only?
2. **RQ2:** In-game crossover point — when does in-game data surpass pre-match prediction?
3. **RQ3:** Tournament-aware sequential prediction vs single-match?
