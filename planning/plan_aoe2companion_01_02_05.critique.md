---
reviewer: reviewer-adversarial
plan: planning/plan_aoe2companion_01_02_05.md
date: 2026-04-15
verdict: APPROVE WITH CONDITIONS
blocking_count: 1
warning_count: 5
---

# Adversarial Review — aoe2companion 01_02_05 Plan

## Lens Assessments

- **Temporal discipline:** SOUND — Visualization-only step; no features computed. ratingDiff annotation (T03) correctly addresses Invariant #3.
- **Thesis defensibility:** ADEQUATE with conditions. The 16-plot set provides thesis-grade cross-dataset comparability only if the duration clip strategy inconsistency is resolved.
- **Cross-game comparability:** AT RISK — Duration histogram clip strategy diverges from aoestats without documented justification. See BLOCKER.

## Examiner's Questions

1. "You clip aoe2companion duration at p95=63 min, but aoestats clips at a fixed 120 min. How does this support the visual comparison you claim in Chapter 4?"
2. "The cross-cluster overlap heatmap says 'both clusters null = 428,321' but Cluster A's all-8-simultaneous count is 426,472. How can more rows have both clusters null than have all eight Cluster A columns null?"
3. "Why does the NULL co-occurrence heatmap use raw counts when cell values span six orders of magnitude?"

---

## T01 — ROADMAP Patch

**[NOTE] T01-1:** The current ROADMAP 01_02_05 YAML has no `scientific_invariants_applied` block. The plan says "Replace the block" — executor should be told this is an INSERT, not a REPLACE.

---

## T02 — Won Distribution 2-Bar

**[WARNING] T02-1:** The plan says "Extract only the True and False rows" but does not specify the filtering mechanism. After `json.load()`, JSON `null` becomes Python `None`. The filter must use `row["won"] is not None` (identity check), NOT `row["won"] == "NULL"` (string comparison, which fails silently and produces a 3-bar chart). The plan must explicitly specify this predicate.

---

## T03 — ratingDiff Leakage Annotation

**[WARNING] T03-1:** The ratingDiff plot cell (notebook line ~304) creates `fig, ax = plt.subplots(figsize=(10, 6))`. The plan's `ax.text(0.5, 0.97, ..., transform=ax.transAxes)` targets the correct axes. However, `y=0.97` with `va="top"` will overlap the existing multi-line title (N=, skew=, kurt= values). Executor must move annotation to `y=0.93` or increase figure height, or the plot will fail visual inspection at the gate.

---

## T04 — NULL Threshold Harmonization

**[NOTE] T04-1:** The existing code at notebook line 430 uses `null_df_sorted["null_pct"]` — exact variable name the plan references. 4-tier threshold logic is correct. No flaw.

---

## T05 — Duration Histogram (NEW)

**[BLOCKER] T05-1 — Duration clip strategy inconsistent with aoestats:**

The plan clips aoe2companion at p95=3,789s (63.15 min). The aoestats duration histogram clips at a fixed 120 min. The plan's Out of Scope section claims "aoestats clips at 120 min because its p95 is different" — this is **factually incorrect**. The aoestats p95 is 4,714.1s = 78.6 min (confirmed from the aoestats census artifact), yet aoestats clips at 120 min — well above its own p95. The two datasets use fundamentally different clip strategies.

For thesis defensibility: a reader placing the two left panels side-by-side will see different x-axis ranges and different clip philosophies with no explanation on either plot or in the markdown artifact.

Required fix — one of:
- **(a)** Add an annotation to the duration histogram subtitle (e.g., "Body clipped at p95=63 min; cf. aoestats fixed 120-min clip") AND a note in the markdown artifact explaining the asymmetry; OR
- **(b)** Change aoe2companion to clip at fixed 120 min to match aoestats; OR
- **(c)** Schedule an aoestats notebook revision to use p95-derived clipping (makes both consistent).

Option (a) is the minimum viable fix. The factual error in Out of Scope must be corrected regardless.

**[NOTE] T05-2:** JSON key path `census["match_duration_stats"][0]["p95_secs"]` confirmed correct (value 3,789.0). `census["duration_excluded_rows"][0]["non_positive_duration_count"]` confirmed (value 2,941). SQL `EXTRACT(EPOCH FROM (finished - started))` pattern confirmed in the existing 01_02_04 census notebook. All JSON paths valid.

**[NOTE] T05-3:** Insertion point "after T11 (monthly volume, line ~600)" is correct. Plan should say "before T12 (markdown artifact)" — same location, unambiguous for executor.

---

## T06 — NULL Co-occurrence Visualization (NEW)

**[NOTE] T06-1:** All 8 Cluster A column names (`allowCheats`, `lockSpeed`, `lockTeams`, `recordGame`, `sharedExploration`, `teamPositions`, `teamTogether`, `turboMode`) confirmed present in `matches_raw.yaml`. SQL is correct.

**[WARNING] T06-2 — Heatmap uses proxy, not strict cluster definition:** The `cross_cluster_overlap` values in the JSON were computed using single-column proxies (`allowCheats IS NULL` for Cluster A, `fullTechTree IS NULL` for Cluster B). Discrepancy: `allowCheats IS NULL` = 428,338 rows vs. all-eight-null simultaneously = 426,472 rows (1,866-row gap). The heatmap title "Cluster A vs Cluster B" is therefore inaccurate.

Fix: Relabel the heatmap as "allowCheats NULL (proxy for Cluster A) vs fullTechTree NULL (proxy for Cluster B)" with a footnote explaining the proxy relationship.

**[WARNING] T06-3:** The plan does not specify the Python code to retrieve `matches_raw_total_rows`. Executor may run a full COUNT(*) scan instead of `census["matches_raw_total_rows"]` (value: 277,099,059 confirmed in JSON). Add explicit code: `total_rows = census["matches_raw_total_rows"]`.

**[WARNING] T06-4 — imshow colormap failure:** With raw counts spanning 6 orders of magnitude (off-diagonal: 17 and 3,173; diagonal: 428,321 and 276,667,548), any linear colormap renders all non-maximum cells visually indistinguishable from zero.

Required fix — one of:
- **(a)** `sns.heatmap(annot=True, fmt=",", norm=LogNorm())`, OR
- **(b)** Row/column percentage normalization, OR
- **(c)** Drop the heatmap and use a simple annotated 2×2 table (recommended — 4 numbers need no heatmap).

---

## T07 — Artifact Regeneration

**[WARNING] T07-1 — Dict update alone insufficient for I6 compliance:** The existing T12 cell (notebook line 603–724) uses a **hardcoded** markdown generation block that manually appends each SQL query by name. Adding keys to `sql_queries` does NOT auto-include them in the markdown output. The executor must also add explicit hardcoded markdown sections for `hist_duration_body`, `hist_duration_full_log`, and `null_cooccurrence_monthly`. If only the dict is updated, Invariant #6 is violated silently (no error, missing SQL in artifact).

The plan must enumerate the three new markdown sections to add.

---

## Summary Table

| ID | Severity | Task | Finding |
|----|----------|------|---------|
| T02-1 | WARNING | T02 | NULL filter must use `is not None`; string comparison fails silently |
| T03-1 | WARNING | T03 | Annotation at `y=0.97` overlaps multi-line title |
| T05-1 | **BLOCKER** | T05 | Duration clip strategy (p95 vs fixed 120 min) inconsistent with aoestats; Out of Scope rationale factually incorrect |
| T06-2 | WARNING | T06 | Heatmap labels "Cluster A/B" but data uses single-column proxies; 1,866-row discrepancy |
| T06-3 | WARNING | T06 | `matches_raw_total_rows` retrieval unspecified; risk of full table scan |
| T06-4 | WARNING | T06 | imshow on 6-orders-of-magnitude counts produces uninformative heatmap |
| T07-1 | WARNING | T07 | Dict update alone insufficient; hardcoded markdown generation block must also be extended for I6 |

---

## VERDICT: APPROVE WITH CONDITIONS

**Blocking condition (must resolve before execution):**

1. **T05-1** — Correct the factual error in Out of Scope. Add cross-dataset clip strategy documentation to the plot and/or markdown artifact. Minimum fix: subtitle annotation on the duration histogram noting "Body clipped at p95=63 min; aoestats uses fixed 120-min editorial clip — see markdown artifact."

**Strongly recommended before gate sign-off:**

2. T02-1: Specify `row["won"] is not None` as the filter predicate.
3. T07-1: Enumerate the three new hardcoded markdown sections.
4. T06-2: Relabel heatmap to proxy language with footnote.
5. T06-4: Replace imshow with `sns.heatmap(annot=True, fmt=",", norm=LogNorm())` or a 2×2 annotated table.
