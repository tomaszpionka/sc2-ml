# AoE2 Source Inventory & Feasibility Audit — Execution Plan

**Category:** A (Phase work — pre-Phase 0 prerequisite for AoE2 roadmap)
**Branch:** `docs/aoe2-source-inventory`
**Output artifact:** `src/rts_predict/aoe2/reports/00_01_source_inventory.md`
**Invariants in scope:** #3 (temporal discipline), #8 (no magic numbers), #9 (reproducibility), #10 (cross-game comparability)
**Constraint:** Read-only for all code artifacts. Only the report file and reports directory may be created.

---

## Key Findings from Manifest Analysis (discovered during planning)

Before execution, note corrections to the initial briefing:

1. **aoestats has 16 zero-count entries, not 8.** Four distinct gap ranges:
   - 6 weeks Jul–Aug 2024 (all share checksum `e055cea7b273b88de75465ddf17d95ac` — patch transition)
   - 1 week Sep–Oct 2024 (same empty checksum — isolated failure)
   - 1 week Mar 2025 (null checksum — manifest generation error, unique failure mode)
   - 8 weeks 2026-02-08 to 2026-04-04 (service stopped publishing; final non-zero week is 2026-02-01)

2. **aoestats players/matches ratio = 3.53** (not 2.0). Dataset includes team games. The 1v1 RM subset will be substantially smaller than the total 30.7M matches.

3. **aoe2companion rating CSVs are effectively empty before 2025-06-27.** Files are 63–476 bytes (header-only or minimal) from 2020-08-01 through mid-2025, then jump to 8–12 MB overnight on 2025-06-27. Self-computed ELO is mandatory for both games — methodologically parallel to SC2 (where MMR is 83.6% zero, Invariant #7).

4. **aoe2companion has zero date gaps** across 2,073 days, daily granularity, and longer coverage (2020-08-01 vs. 2022-08-28). Clear frontrunner as primary source.

5. **Preliminary recommendation:** aoe2companion as primary source, aoestats as validation/cross-check for the overlapping period 2022-09 to 2026-02.

---

## Prerequisite

Create the reports directory (does not yet exist):

```bash
mkdir -p src/rts_predict/aoe2/reports/
```

---

## Step 1 — Manifest-Based Inventory (no downloads)

All statistics derived from the two JSON manifests already on disk. Every number in the report must include the exact Python code that produced it (Invariant #9).

### 1a. aoestats manifest (`src/rts_predict/aoe2/data/aoestats/api/db_dump_list.json`)

Compute and report the following table:

| Metric | Value | Code |
|--------|-------|------|
| Total manifest entries | 188 | `len(data['db_dumps'])` |
| Non-zero entries | 172 | `len([d for d in dumps if d['num_matches'] > 0])` |
| Zero-count entries | 16 | 4 gap ranges (see Key Findings above) |
| Date range (non-zero) | 2022-08-28 to 2026-02-07 | sorted by start_date |
| Total matches | 30,690,651 | `sum(d['num_matches'] for d in dumps)` |
| Total player records | 108,303,693 | `sum(d['num_players'] for d in dumps)` |
| Weekly match count: min/mean/median/max | 11,615 / 178,434 / ~213K / ~265K | computed from non-zero weeks |
| Players/matches ratio | 3.53 | implies team games present |
| Granularity | Weekly (matches.parquet + players.parquet per week) | 344 files total |
| File sizes | NOT in manifest — requires sampling (Step 2) | — |

**Gap analysis table** (include all four ranges in the report):

| Gap range | Weeks | Checksum | Probable cause |
|-----------|-------|----------|----------------|
| 2024-07-21 to 2024-08-31 | 6 | `e055cea7...` (empty file) | Patch transition |
| 2024-09-29 to 2024-10-05 | 1 | `e055cea7...` (empty file) | Isolated data collection failure |
| 2025-03-23 to 2025-03-29 | 1 | null | Manifest generation error |
| 2026-02-08 to 2026-04-04 | 8 | `e055cea7...` (empty file) | Service stopped publishing |

**Quarterly volume table:** compute matches/week by quarter from 2022-Q3 to 2026-Q1, show the dramatic ramp-up from ~14K/week (Q3 2022) to ~235K/week (Q2 2023), then stable 170–230K/week through 2025.

### 1b. aoe2companion manifest (`src/rts_predict/aoe2/data/aoe2companion/api/api_dump_list.json`)

Compute and report this file-type breakdown:

| File type | Count | Total size | Date range | Notes |
|-----------|-------|-----------|------------|-------|
| `match-{date}.parquet` | 2,073 | 6.94 GB | 2020-08-01 to 2026-04-04 | Zero gaps |
| `match-{date}.csv` | 2,072 | 43.14 GB | 2020-08-01 to 2026-04-04 | CSV avoided — use parquet |
| `rating-{date}.csv` | 2,072 | 2.64 GB | 2020-08-01 to 2026-04-04 | Effectively empty pre-2025-06-27 |
| `leaderboard.parquet` | 1 | 87 MB | Latest snapshot | — |
| `leaderboard.csv` | 1 | 749 MB | Latest snapshot | CSV avoided |
| `profile.parquet` | 1 | 170 MB | Latest snapshot | — |
| `profile.csv` | 1 | 663 MB | Latest snapshot | CSV avoided |
| test files | 3 | ~5 MB | — | Ignorable |

**Yearly match parquet size table** (computed from manifest sizes):

| Year | Files | Total | Avg/day | Range |
|------|-------|-------|---------|-------|
| 2020 | 153 | 0.10 GB | 0.66 MB | 0.37–1.44 MB |
| 2021 | 365 | 0.36 GB | 1.00 MB | 0.61–1.63 MB |
| 2022 | 365 | 0.92 GB | 2.53 MB | 0.77–6.95 MB |
| 2023 | 365 | 1.96 GB | 5.37 MB | 2.65–13.83 MB |
| 2024 | 366 | 1.56 GB | 4.26 MB | 2.99–5.68 MB |
| 2025 | 365 | 1.59 GB | 4.37 MB | 3.29–5.69 MB |
| 2026 | 94 | 0.44 GB | 4.72 MB | 3.46–6.03 MB |

**Rating CSV three-phase finding** (document with transition dates):

| Period | File size behavior | Interpretation |
|--------|-------------------|----------------|
| 2020-08-01 to ~2022-09-09 | 63 bytes each (header-only) | Export not yet implemented |
| 2022-09-10 to 2025-06-26 | 147–476 bytes (minimal) | Sparse entries — handful of changes per day |
| 2025-06-27 to 2026-04-04 | 8–12 MB each | Full daily ELO snapshots |

---

## Step 2 — Sample Downloads for Schema Profiling

**Hard limit:** ≤10 files from aoestats, ≤7 files from aoe2companion. Do not exceed this.

Save all samples to a `tmp/` directory under the respective dataset directory (per ARCHITECTURE.md these directories must eventually exist; for the audit they serve as temporary landing pads).

### 2a. aoestats — 10 files (5 weeks × 2 files per week)

Download the following weeks, chosen to span the full temporal range and capture schema evolution:

| Sample | Week start | Matches | Rationale |
|--------|-----------|---------|-----------|
| S1 | 2022-08-28 | 11,615 | Earliest week — baseline schema |
| S2 | 2023-03-05 | ~95K | Early growth — check schema evolution |
| S3 | 2024-04-21 | ~241K | Peak volume |
| S4 | 2025-06-29 | ~190K | Near aoe2companion rating transition date |
| S5 | 2026-02-01 | 118,661 | Last non-zero — final schema |

Each week: download `matches_url` + `players_url` from the manifest. Construct full URL as `https://aoestats.io` + the manifest path field.

**Schema profiling code to run on each file:**

```python
import pyarrow.parquet as pq

for path in sample_paths:
    table = pq.read_table(path)
    print(f"\n=== {path} ===")
    print(f"  Rows: {table.num_rows:,}")
    print(f"  Columns: {table.num_columns}")
    print(f"  Schema:")
    for field in table.schema:
        print(f"    {field.name}: {field.type} (nullable={field.nullable})")
    df = table.to_pandas()
    print(df.head(3).to_string())
    print(f"  File size: {os.path.getsize(path):,} bytes")
    print(f"  Bytes/row: {os.path.getsize(path) / table.num_rows:.1f}")
```

**What to extract per file:**
- Row count and file size (for size extrapolation)
- Full column schema (name, type, nullable)
- Value domains for: match_type/leaderboard_id, player_id field name, civ field, result/won field, timestamp field, map field, rating/elo field
- Note any schema differences across the 5 sampled weeks

### 2b. aoe2companion — 7 files

| Sample | File | Size (manifest) | Rationale |
|--------|------|-----------------|-----------|
| M1 | `match-2020-08-01.parquet` | 592 KB | Earliest — baseline schema |
| M2 | `match-2022-09-10.parquet` | ~2.5 MB | Overlap start with aoestats |
| M3 | `match-2023-06-15.parquet` | ~5.4 MB | Mid-peak period |
| M4 | `match-2025-06-27.parquet` | ~4.4 MB | Rating transition date |
| M5 | `match-2026-04-01.parquet` | ~4.7 MB | Latest data |
| R1 | `rating-2025-07-01.csv` | ~8 MB | First month of full rating data |
| L1 | `leaderboard.parquet` | 87 MB | Current leaderboard snapshot |

URLs are provided directly in the manifest (`url` field — `https://dump.cdn.aoe2companion.com/{key}`).

**What to measure:**
- Match files: same schema profiling as aoestats (above)
- Rating CSV (R1): column schema, whether it contains per-player daily ELO snapshots or delta changes, player ID field
- Leaderboard (L1): column schema, player ID field, rating/rank/wins/losses fields, leaderboard type encoding — identify 1v1 RM leaderboard ID

### 2c. Size extrapolation for aoestats

Since aoestats manifest has no file sizes, extrapolate from the 10 sampled files:

```python
# For each sampled matches.parquet:
bytes_per_match = file_size_bytes / row_count

# Extrapolate total corpus size:
# total_est = sum(week.num_matches * bytes_per_match_for_nearest_sample)
# Report as range: use min and max bytes_per_match across all 5 samples
total_matches_by_week = {d['start_date']: d['num_matches'] for d in dumps if d['num_matches'] > 0}
# Assign each week the bytes_per_match from its nearest sampled week
```

Report the extrapolated total as a range (min/max) to capture schema evolution uncertainty. Same approach for players.parquet.

---

## Step 3 — Storage Feasibility & Architecture Decision

Populate this table using data from Steps 1 and 2:

| Source | Format | Raw size | 1v1 RM filtered est. | Recommendation |
|--------|--------|---------|----------------------|----------------|
| aoe2companion match parquet | Parquet | 6.94 GB (exact) | TBD from schema profiling | Local |
| aoe2companion rating CSV (2025+ only) | CSV | ~1.7 GB (281 files × ~8 MB) | ~1.7 GB | Local or Skip — decide based on R1 schema |
| aoe2companion leaderboard | Parquet | 87 MB (exact) | 87 MB | Local |
| aoe2companion profile | Parquet | 170 MB (exact) | 170 MB | Local |
| aoestats matches | Parquet | TBD from extrapolation | TBD | TBD |
| aoestats players | Parquet | TBD from extrapolation | TBD | TBD |

**Architecture contract check:** For each dataset directory that will be downloaded, confirm the directory layout per ARCHITECTURE.md:
- `raw/` — raw parquet/CSV files (gitignored contents, README tracked)
- `staging/` — intermediate artifacts (gitignored, README tracked)
- `db/` — DuckDB database file (gitignored, `.gitkeep` tracked)
- `tmp/` — DuckDB spill-to-disk (gitignored, `.gitkeep` tracked)

Document which directories need to be created as action items.

---

## Step 4 — Cross-Source Overlap & Deduplication Assessment

**Overlap period:** 2022-08-28 to 2026-02-07 (~3.4 years).

From the sampled files in the overlap period (S1–S5 from aoestats, M2 from aoe2companion on 2022-09-10):

1. **Player ID namespace:** Are the player ID fields in both sources the same identifier? (Likely `profile_id` from the AoE2 game API.) If yes, cross-source matching is direct. If no, check whether `profile.parquet` from aoe2companion provides a mapping.

2. **Match ID:** Is there a shared match identifier? If both sources expose `match_id`, deduplication is trivial. If not, document the approximate matching approach: `(started_at_timestamp, player1_profile_id, player2_profile_id)`.

3. **Match count comparison:** For a sampled overlapping week (e.g., 2022-09-04 to 2022-09-10), compare match counts from aoestats manifest (`num_matches = 13,793`) vs. counting rows in aoe2companion's daily files for the same 7 days. If aoestats is pre-filtered to 1v1 RM and aoe2companion includes all match types, explain the ratio.

4. **Match type taxonomy:** Map match type values from each source to a common vocabulary. Document which value(s) = 1v1 Random Map in each.

---

## Step 5 — Thesis Implications

### 5a. Cross-game feature mapping table (Invariant #10)

| Feature category | SC2 source | AoE2 source | Methodological note |
|-----------------|------------|-------------|---------------------|
| Skill rating (ELO/Glicko) | Derived from match history (MMR 83.6% zero) | Derived from match history (rating CSV sparse pre-2025) | Both require self-computed ratings. Parallel methodology. |
| Win rate | Match history | Match history | Direct analogue |
| Activity (games played, recency) | Match timestamps | Match timestamps | Direct analogue |
| Faction/civ matchup | Race (T/P/Z, 3 values) | Civilization (42 civs in AoE2 DE) | Higher cardinality in AoE2 — may need grouping or embedding |
| Map | 188 maps in SC2EGSet | TBD from schema | — |
| Head-to-head | Derived from match pairs | Derived from match pairs | Direct analogue |
| In-game state | TrackerEvents, GameEvents | NOT AVAILABLE | Controlled experimental variable (Invariant #10) |

### 5b. Thesis §4.1.2 draft paragraph

Include a paragraph covering: source provenance, corpus size (post 1v1 RM filtering), date range, known limitations (no in-game state, rating coverage gap), and snapshot date for reproducibility.

### 5c. Reproducibility flag

State whether acquisition can be fully scripted from the manifest files. Both sources use static CDN/parquet URLs derivable from the manifests on disk — fully reproducible. Document the manifest snapshot date (aoestats manifest fetched ~2026-04-05, aoe2companion manifest fetched ~2026-04-05).

---

## Report Skeleton

```markdown
# AoE2 Source Inventory — Feasibility Audit
**Report date:** 2026-04-05
**Phase:** Pre-Phase 0
**Author:** Claude Code

## Executive Summary

- [Primary source recommendation with one-line justification]
- [Total corpus size estimate for primary source (raw, and 1v1 RM filtered)]
- [Key limitation: no in-game state; rating CSV sparse pre-2025; self-computed ELO required]

## 1. Source Inventory

### 1.1 Overview Table

[Provider | URL | Granularity | Date range | Match count | File count |
 Format | Size est | Player ID | Integrity]

### 1.2 aoestats.io

[Manifest statistics table, quarterly volume table, gap analysis table (all 4 ranges)]

### 1.3 aoe2companion.com

[File-type breakdown table, yearly size table, rating CSV three-phase table,
date continuity finding]

## 2. Data Content Profiling

### 2.1 aoestats Schema

[Column-level schema for matches.parquet and players.parquet.
Schema evolution notes across sampled weeks (if any).]

### 2.2 aoe2companion Match Schema

[Column-level schema for match-{date}.parquet.
Schema evolution notes across sampled files (if any).]

### 2.3 aoe2companion Rating Schema

[Column-level schema from rating-2025-07-01.csv.
Whether it contains per-player daily ELO or delta changes.]

### 2.4 aoe2companion Leaderboard Schema

[Column-level schema from leaderboard.parquet.]

### 2.5 Match Type Taxonomy

[Table: source / field name / value / human label.
Identify the 1v1 Random Map filter predicate for each source.]

### 2.6 Player Identity

[Field names per source. Shared namespace determination.
Cross-referencing strategy if namespaces differ.]

### 2.7 Field Completeness (sample-based)

[For each schema field in the sampled files: null rate in sample.
Flag fields >50% null or suspiciously low cardinality.]

## 3. Storage Feasibility

### 3.1 Size Estimation

[aoestats: extrapolation with min/max range, formula shown.
aoe2companion: exact from manifest.]

### 3.2 Architecture Decision

[Recommendation table: source / format / raw size / 1v1 RM filtered / action.
Directory layout requirements per ARCHITECTURE.md.]

## 4. Cross-Source Overlap

### 4.1 Temporal Overlap

[Date range overlap. Match count comparison for sampled overlapping period.]

### 4.2 Schema Compatibility

[Side-by-side column mapping. Shared match ID determination.]

### 4.3 Deduplication Strategy

[Recommended approach for the overlap period.]

## 5. Thesis Implications

### 5.1 Cross-Game Feature Mapping (Invariant #10)

[Feature category table — all 7 categories]

### 5.2 Temporal Discipline (Invariant #3)

[Rating availability analysis. Self-computed ELO recommendation.]

### 5.3 Data Description for Thesis §4.1.2

[Draft paragraph — ~150 words, thesis-ready prose.]

### 5.4 Reproducibility

[Manifest snapshot dates. Scripted acquisition assessment.]

## Action Items

[Numbered list — prerequisites for AoE2 Phase 0:]
1. Create download script for primary source (checksum verified, idempotent)
2. Create raw/staging/db/tmp directory layout per ARCHITECTURE.md
3. Create AOE2_THESIS_ROADMAP.md
4. Update PHASE_STATUS.yaml to reference the roadmap
5. Define 1v1 RM filter predicate (exact field+value from §2.5)

## Appendix: Manifest Analysis Code

[All Python code used to derive the statistics in this report, by section.]
```

---

## Gate Condition

The report `src/rts_predict/aoe2/reports/00_01_source_inventory.md` is complete when ALL of the following are true:

1. Every number in the report is accompanied by the exact Python code that produced it (Invariant #9).
2. The 1v1 RM filter predicate is identified for at least the primary source, with the exact field name and value(s) from a sampled file (not guessed).
3. The player ID field is identified for both sources, with a shared-namespace determination.
4. The aoestats size estimate is derived from ≥5 sampled weeks (10 files), with the extrapolation formula shown explicitly.
5. All 16 zero-count entries are documented across all 4 gap ranges.
6. The rating CSV three-phase pattern is documented with exact transition dates.
7. The cross-game feature mapping table covers all 7 Invariant #10 categories.
8. A primary source recommendation is made with explicit justification against at least 4 criteria.
9. The action items list is specific enough to serve as input for an AoE2 Phase 0 roadmap.
10. No more than 10 files were downloaded from aoestats and 7 from aoe2companion.
