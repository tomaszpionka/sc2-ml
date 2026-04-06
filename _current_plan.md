# Plan: docs/manual-patch (Category E — Docs only)

**Branch:** `docs/manual-patch`
**Source:** `manual_patch.md`
**Files touched:** `docs/THESIS_WRITING_MANUAL.md`, `docs/DATA_EXPLORATION_MANUAL.md`, `pyproject.toml`, `CHANGELOG.md`

## Critical Finding

Patches 3A, 3B, 3C (`docs/FEATURE_ENGINEERING_MANUAL.md`) are **already applied** on `master`:
- `### AI-assisted feature engineering disclosure` (Patch 3A) — present
- `### A note on Bayesian model comparison and feature importance` (Patch 3B) — present
- All 4 reference link definitions (Patch 3C) — present

**SKIP all FEATURE_ENGINEERING_MANUAL.md patches.**

---

## Steps

### Step 1 — Create branch
```bash
git checkout -b docs/manual-patch
```
Verify: `git branch --show-current` returns `docs/manual-patch`

---

### Step 2 — Patch 1A: Replace Section 3.2 in THESIS_WRITING_MANUAL.md

Replace the existing `### 3.2 Statistical testing for model comparison` subsection (up to but not including `### 3.3 Evaluation protocol`) with the expanded version from `manual_patch.md` lines 17–34.

**old_string** (current content of §3.2):
```
### 3.2 Statistical testing for model comparison

A bigger accuracy number does not mean a better model — differences may reflect random variation. For your thesis comparing 3+ methods across 2 games, [Demšar 2006][demsar] recommends the **Friedman test with Nemenyi post-hoc analysis**, presented using Critical Difference (CD) diagrams showing average ranks and statistical significance groupings. Additional requirements:

- For pairwise comparisons, the **Wilcoxon signed-rank test** is preferred over paired t-tests, which underestimate variance in resampled evaluations.
- Report **effect sizes alongside p-values** — a statistically significant but tiny improvement may lack practical meaning.
- When performing multiple comparisons, apply **Bonferroni or Holm-Bonferroni corrections** to control family-wise error rate.
- [Raschka 2018][raschka] provides an accessible reference for model evaluation and selection methodology.
```

**new_string:** Full expanded §3.2 block from `manual_patch.md` (lines 17–34).

Verify: `grep -n "Nemenyi post-hoc test is no longer" docs/THESIS_WRITING_MANUAL.md` returns a match; `grep "Friedman test with Nemenyi post-hoc analysis" docs/THESIS_WRITING_MANUAL.md` returns no match.

---

### Step 3 — Patch 1B: Insert new Section 8 (GenAI Transparency) + renumber old §8 to §9

**Step 3a** — Rename old Section 8 header:

old_string: `## 8. What Separates an Excellent Thesis from a Passing One`
new_string: `## 9. What Separates an Excellent Thesis from a Passing One`

**Step 3b** — Insert new Section 8 block (from `manual_patch.md` lines 42–91) before the (now renumbered) `## 9.` header. Use the `---` separator and surrounding context as the anchor.

Verify: `grep -n "## 8. GenAI Transparency" docs/THESIS_WRITING_MANUAL.md` returns a match; `grep -n "## 9. What Separates" docs/THESIS_WRITING_MANUAL.md` returns a match.

---

### Step 4 (optional, pending approval) — Fix stale Nemenyi reference in Section 9

In the now-renumbered Section 9, the bullet still reads:
```
- Results that are **statistically validated** with appropriate tests (Friedman + Nemenyi for multi-method comparison)
```
This is inconsistent with Patch 1A. Proposed fix:
```
- Results that are **statistically validated** with appropriate tests (Friedman + Wilcoxon/Holm for multi-method comparison, with Bayesian signed-rank as complement)
```
Verify: `grep "Nemenyi" docs/THESIS_WRITING_MANUAL.md` returns no matches.

**Awaiting user approval before executing Step 4.**

---

### Step 5 — Patch 1C: Append 10 new references to THESIS_WRITING_MANUAL.md

Append the 10 reference link definitions from `manual_patch.md` (lines 98–110) after the last existing reference line (currently `[pressbooks-timeline]: ...`).

Verify: `grep -c "\[benavoli-2016\]\|\[benavoli-2017\]\|\[garcia-herrera-2008\]\|\[garcia-2010\]\|\[baycomp\]\|\[corani-2017\]\|\[kuleuven-genai\]\|\[apa-chatgpt\]\|\[elsevier-ai\]\|\[uw-ai-guidelines\]" docs/THESIS_WRITING_MANUAL.md` returns 10.

---

### Step 6 — Patch 2A: Insert 8th pitfall in DATA_EXPLORATION_MANUAL.md

Insert the "Not documenting AI-assisted exploration" paragraph (from `manual_patch.md` lines 122–131) after the existing 7th pitfall ("Failing to document decisions") and before the `---` separator preceding `## 8. Conclusion`.

Verify: `grep -n "Not documenting AI-assisted" docs/DATA_EXPLORATION_MANUAL.md` returns a match.

---

### Step 7 — Patch 2B: Append 1 reference to DATA_EXPLORATION_MANUAL.md

Append `[kuleuven-genai]: ...` (from `manual_patch.md` line 139) after the last existing reference line (currently `[stratos-ida]: ...`).

Verify: `grep "kuleuven-genai" docs/DATA_EXPLORATION_MANUAL.md` returns a match.

---

### Step 8 — Version bump

Bump minor version in `pyproject.toml` and add entry to `CHANGELOG.md`.

---

### Step 9 — Commit and PR

Single commit:
```
docs(manuals): add statistical testing evolution, GenAI transparency, and AI-assisted exploration guidance
```

PR targets `master`.

---

## Risk Checklist

| Risk | Mitigation |
|------|-----------|
| Duplicate refs if patches re-applied | Confirmed 3A–3C already on master; excluded |
| Section numbering inconsistency | Rename §8→§9 (Step 3a) before inserting new §8 (Step 3b) |
| Stale Nemenyi reference in §9 | Step 4 (pending approval) |
| Broken ref links in new text | After all edits, grep for each `[ref-name]` used and confirm definition exists |

---

## Gate Condition

All 5 new reference-link anchor tokens used in new text have a matching `[token]:` definition in the same file. No markdown linting errors.
