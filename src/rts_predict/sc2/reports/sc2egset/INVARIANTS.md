# SC2EGSet — dataset-specific invariants

These findings apply ONLY to the SC2EGSet dataset and were derived from
Phase 0/1 exploration. Universal scientific invariants live in
.claude/scientific-invariants.md. Methodology guidance lives in docs/INDEX.md.

---

## Identity

**For StarCraft II, the lowercased nickname is the canonical player identifier,
not the toon.** Toons are server-scoped. A player switching from KR to EU
server gets a new toon but keeps their nickname. Any feature indexed by toon
instead of canonical nickname is silently wrong. Multi-toon cases must be
classified (server switch, rename, ambiguous) in Phase 2.

---

## Domain constant — game loop to real time

**The SC2 game loop to real-time conversion is 22.4 loops per second at
Faster (competitive) speed.** The engine runs at 16 loops per game-second;
the Faster speed multiplier is 1.4×; thus:

```
real_time_seconds = game_loops / 22.4
```

The formula `game_loops / 16 / 60` produces **game-minutes** (engine time),
which is 1.4× longer than real-time minutes. Both representations are valid
but must be clearly labelled in all reports and artifacts.

Sources:
- Blizzard s2client-proto (`protocol.md`: "22.4 gameloops per second")
- Vinyals et al. 2017 (arXiv:1708.04782)
- Liquipedia Game Speed article

---

## Field status — APM (Actions Per Minute)

**APM from ToonPlayerDescMap is usable from 2017 onward.** Phase 0 found
97.5% of player slots have non-zero APM. The 2.5% zeros are concentrated
in 2016 tournaments (systematic — entire year missing) plus sporadic slots
in 2017–2024.

For feature engineering: use APM from 2017+ directly; impute or exclude
2016 rows.

Source: `src/rts_predict/sc2/reports/sc2egset/01_04_apm_mmr_audit.md`

---

## Field status — MMR (Matchmaking Rating)

**MMR from ToonPlayerDescMap is NOT usable as a direct feature.** Phase 0
found 83.6% of slots have zero MMR. The missingness is systematic: driven by
tournament organiser (lobby vs. ladder replays), year (near-zero from 2021+),
and `highestLeague` field availability.

Player skill must instead be derived from match history (Elo, Glicko-2, or
rolling win rate).

Source: `src/rts_predict/sc2/reports/sc2egset/01_04_apm_mmr_audit.md`
