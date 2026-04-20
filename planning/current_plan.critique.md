# Plan Critique — reviewer-adversarial Mode A (TG2)

**Target:** `planning/current_plan.md` (333 lines)
**Date:** 2026-04-20

## Verdict: BLOCKER

T01 and T02 are individually defensible. T03's §2.3.2 "53 total, 3 Chronicles excluded" parenthetical is factually WRONG and must be revised before execution.

## Findings

### BLOCKER A1 — "53 total, 3 Chronicles excluded" parenthetical is factually incorrect
Chronicles shipped in TWO parts:
- **Chronicles: Battle for Greece** (2024-11, 3 civs: Achaemenids, Athenians, Spartans)
- **Chronicles: Alexander the Great** (2025-10-14, 3 civs: Macedonians, Thracians, Puru)

**Chronicles-excluded = 6 civs, not 3.**

Additionally unaccounted in the DLC chronology:
- Three Kingdoms (2025-05-06, +5 civs) — within aoestats window
- Last Chieftains (2026-02-17, +3 civs) — after window

"53 total" is a constructed value (50 ranked + 3 Chronicles Greece) not matching any authoritative source. Liquipedia portal gives ~49-55 depending on accounting convention.

**Consequence:** post-T03 the thesis would assert "pięćdziesiąt cywilizacji... 53 total, 3 Chronicles excluded" while an examiner cross-checking ageofempires.com would find:
(i) Three Kingdoms unaccounted
(ii) Chronicles-exclusion understated as 3 when it is 6
(iii) "53 total" unanchored to any citation

**Fix (recommended option a):** DROP the parenthetical entirely. Revert to pure 45→50 + window substitution. The R18 addition was meant to close a "reader-visible DLC arithmetic gap" but introduces a larger gap. §2.3.2:67 is already flagged for Pass-2 review — full-roster accounting can wait.

Alternatively (option b): hedge non-numerically — "(pełny roster gry przekracza liczbę cywilizacji rankingowych; część zawartości DLC Chronicles pozostaje wyłączona z rywalizacji rankingowej)".

### MAJOR A2 — DLC chronology missing Three Kingdoms + Last Chieftains
§2.3.2:67 DLC chronology parenthetical (preserved from the removed `[REVIEW:]` flag) omits Three Kingdoms (2025-05-06) and Last Chieftains (2026-02-17). Under A1 remedy (a), the flag-removal silently promotes an incomplete DLC enumeration from DRAFT to THESIS CONTENT.

**Fix:** retain a reduced-scope `[REVIEW:]` flag: *"[REVIEW: DLC chronology completeness — zweryfikować w Pass 2, czy lista DLC obejmuje Three Kingdoms (2025-05-06) i Last Chieftains (2026-02-17)]"*.

### MAJOR A3 — Window forward-reference inconsistency
T01 step 5 instructs inserting "(Tabela 4.4a w §4.1.3)" at §2.2.2:33. T03 does NOT add analogous forward-reference at §1.4:45 and §2.3.2:67 where the aoestats window is substituted. Inconsistent convention across sites.

**Fix:** require T03 to append "(Tabela 4.4a)" forward-reference at §1.4 and §2.3.2 window-substitution sites.

### MINOR A4 — Dash character convention inconsistency
Tabela 4.4a uses em-dash "—" (2022-08-28 — 2026-02-07). Plan substitution uses arrow "→" (2022-08-28 → 2026-02-07). Different characters in different contexts.

**Fix:** pick one character and apply consistently. Recommend em-dash to match Tabela 4.4a source.

### MINOR A5 — Acquisition vs observation window precision
Plan uses filename-derived acquisition window (2022-08-28 → 2026-02-07 per Tabela 4.4a). aoestats INVARIANTS.md:74 gives first-observation window as (2022-08-29, 2026-02-06) — 1 day tighter at each boundary. Defensible per thesis convention but worth explicit framing.

## Probes answered

1. Hardest-to-catch risk: **CONFIRMED BLOCKER.** See A1.
2. Arithmetic: $\binom{50}{2}=1225$, $+50=1275$ ✓
3. Bibkey integrity: T02 single-token edit verified operational ✓
4. Cross-section consistency: 9-site enumeration complete ✓
5. Window consistency: See A4 (dash character) and A5 (acquisition vs observation)
6. DLC chronology preservation: See A2 (incomplete chronology promoted to thesis content)
7. REVIEW_QUEUE row split: consistent with existing conventions ✓
8. Scope creep: File Manifest holds at 8 files ✓
9. Mountain Royals year: 2023-10-31 confirmed via Steam, Neowin, ageofempires.com, Wikipedia, Fandom ✓
10. Flag lifecycle: See A2 — reduced-scope flag should be retained
11. §4.1.1.x no-regression: T01 edits only §2.2.2 + §3.x:55 ✓
12. Dispatch shorthand: consistent with sec_4_1_crosswalk.md:14 ✓

## Recommendation

**REQUIRE_MINOR_REVISION of T03 before execution.** Four revisions needed:

1. **A1 (BLOCKER):** drop the "53 total, 3 Chronicles excluded" parenthetical entirely. Revert to pure 45→50 + window substitution.
2. **A2 (MAJOR):** retain reduced-scope `[REVIEW:]` flag at §2.3.2:67 covering DLC chronology completeness.
3. **A3 (MAJOR):** add "(Tabela 4.4a)" forward-references at §1.4:45 and §2.3.2:67 window-substitution sites.
4. **A4 (MINOR):** pick em-dash consistently for window dash-character.

T01 and T02 are independently defensible. T03 requires revision.

## Sources

- Fandom wiki: Mountain Royals, Last Chieftains, Three Kingdoms pages
- Neowin: Mountain Royals 2023-10-31 release
- ageofempires.com: official news
- Liquipedia: Civilizations portal
- Steam: DLC listings
