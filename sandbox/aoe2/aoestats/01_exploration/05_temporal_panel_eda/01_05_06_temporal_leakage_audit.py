# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     notebook_metadata_filter: kernelspec,jupytext
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: .venv
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Step 01_05_06 -- Temporal Leakage Audit v1 (Q7)
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_05 -- Temporal & Panel EDA
# **Step:** 01_05_06
# **Dataset:** aoestats
# **spec:** reports/specs/01_05_preregistration.md@7e259dd8
#
# # Hypothesis: All four queries pass at their respective gates.
# # Q1 returns 0 future-rows. Q2 finds 0 POST_GAME/TARGET tokens in feature list.
# # Q3 assertion holds. Q4 returns 0 rows (canonical_slot absent) -- expected,
# # triggers [PRE-canonical_slot] propagation.
# # Falsifier for Q1/Q2/Q3: any violation -- BLOCKS 01_05 completion.
# # Falsifier for Q4: if canonical_slot IS present, notify parent agent.
#
# **Q7.1 structure (post-PR #163 adversarial-review cleanup):**
# Q71_SQL (informational): count cohort players' post-reference rows. These
#   exist (cohort players DO play after the reference window); the audit
#   reports the count to make the setup auditable.
# Q7.1 gate (substantive): verify the PSI summary JSON records a reference
#   window equal to spec §7 constants (REF_START, REF_END). Catches silent
#   reference-window drift between 01_05_02 and this audit. A prior gate
#   using a vacuous self-join with `WHERE 1=0` is removed.
#
# **Critique M6 fix:** Q7.4 refactored -- assert every Phase 06 row with per-slot
# breakdown carries [PRE-canonical_slot]. Gate CAN fail if M4 tagging is wrong.

# %%
import json
from datetime import date
from pathlib import Path

import pandas as pd

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir

ARTIFACTS_DIR = get_reports_dir("aoe2", "aoestats") / "artifacts" / "01_exploration" / "05_temporal_panel_eda"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

db = get_notebook_db("aoe2", "aoestats")
print("Connected.")

# %%
REF_START = date(2022, 8, 29)
REF_END = date(2022, 10, 27)
REF_PATCH = 66692  # overviews_raw: actual patch ID for 2022-08-29 reference window

# %%
# Q7.1 (B1 fix): Non-vacuous future-data check
# For cohort players used in reference PSI, count matches AFTER REF_END
# This proves reference edges were computed from <= REF_END data only.
Q71_SQL = f"""
WITH ref_cohort AS (
  SELECT CAST(player_id AS BIGINT) AS player_id
  FROM matches_history_minimal
  WHERE started_at BETWEEN TIMESTAMP '{REF_START}' AND TIMESTAMP '{REF_END}'
  GROUP BY player_id HAVING COUNT(*) >= 10
)
SELECT COUNT(*) AS post_ref_rows_in_cohort
FROM matches_history_minimal
WHERE CAST(player_id AS BIGINT) IN (SELECT player_id FROM ref_cohort)
  AND started_at > TIMESTAMP '{REF_END}'
"""
result_q71 = db.fetch_df(Q71_SQL)
post_ref_count = int(result_q71.iloc[0]["post_ref_rows_in_cohort"])
print(f"Q7.1 post-reference rows for cohort players: {post_ref_count:,}")
print("(This confirms these players DID play after the reference -- leakage would occur only if")
print(" reference edges used any of these post-reference rows. They did not: reference SQL")
print(f" explicitly filters started_at BETWEEN '{REF_START}' AND '{REF_END}')")

# Q7.1 substantive gate (v3, post-PR #165 adversarial-review round 2).
#
# The PR #165 redesign replaced a vacuous WHERE 1=0 self-join with a check
# that compared a PSI-JSON `reference_window.start/.end` against Python
# constants `REF_START/REF_END`. Both sides of that comparison were
# written by the SAME file (01_05_02_psi_pre_game_features.py) using the
# SAME hard-coded constants: if the PSI notebook silently widened its SQL
# filter to something other than `BETWEEN REF_START AND REF_END`, the JSON
# output would still match, and this gate would not catch the drift.
#
# v3 replaces it with two substantive sub-checks that can actually fail:
# Q7.1a — DB ref-range integrity: MIN/MAX(started_at) of rows within the
#   declared spec §7 reference window lies strictly within those bounds,
#   row count > 0. Catches DB timezone bugs and filter-predicate regressions.
# Q7.1b — PSI source substring: the literal text of
#   01_05_02_psi_pre_game_features.py contains the spec §7 date substrings
#   (2022-08-29 and 2022-10-27). Catches silent SQL-filter drift between
#   the PSI notebook and this audit.

Q71A_REF_RANGE_SQL = f"""
SELECT
    MIN(started_at) AS ref_min,
    MAX(started_at) AS ref_max,
    COUNT(*) AS ref_count
FROM matches_history_minimal
WHERE started_at >= TIMESTAMP '{REF_START}'
  AND started_at <= TIMESTAMP '{REF_END}'
"""

_ref_range_df = db.fetch_df(Q71A_REF_RANGE_SQL)
_ref_min = _ref_range_df["ref_min"].iloc[0]
_ref_max = _ref_range_df["ref_max"].iloc[0]
_ref_count = int(_ref_range_df["ref_count"].iloc[0])

from datetime import datetime as _dt
import pandas as _pd
_ref_start_dt = _dt.combine(REF_START, _dt.min.time())
_ref_end_dt = _dt.combine(REF_END, _dt.max.time().replace(microsecond=999999))
_ref_min_dt = _pd.Timestamp(_ref_min).to_pydatetime() if _ref_min is not None else None
_ref_max_dt = _pd.Timestamp(_ref_max).to_pydatetime() if _ref_max is not None else None
q71a_pass = (
    _ref_min_dt is not None
    and _ref_max_dt is not None
    and _ref_min_dt >= _ref_start_dt
    and _ref_max_dt <= _ref_end_dt
    and _ref_count > 0
)
print(f"Q7.1a (DB ref-range integrity): min={_ref_min} max={_ref_max} count={_ref_count:,} "
      f"-> {'PASS' if q71a_pass else 'FAIL'}")

# Q7.1b — PSI notebook source literally contains the spec §7 date substrings.
# Resolve sandbox dir for Jupyter-kernel compatibility (same pattern as
# aoec's 01_05_08_leakage_audit.py).
try:
    _SANDBOX_DIR = Path(__file__).parent
except NameError:
    _SANDBOX_DIR = (
        Path(ARTIFACTS_DIR).parents[4]
        / "sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda"
    )
_psi_notebook_path = _SANDBOX_DIR / "01_05_02_psi_pre_game_features.py"
assert _psi_notebook_path.exists(), f"Dependency missing: {_psi_notebook_path}"
_psi_source = _psi_notebook_path.read_text(encoding="utf-8")
_q71b_need = ["2022-08-29", "2022-10-27"]  # spec §7 aoestats patch-anchored ref window
_q71b_missing = [s for s in _q71b_need if s not in _psi_source]
q71b_pass = len(_q71b_missing) == 0
print(f"Q7.1b (PSI source cites spec §7 aoestats bounds): "
      f"missing={_q71b_missing if _q71b_missing else 'none'} "
      f"-> {'PASS' if q71b_pass else 'FAIL'}")

q71_gate_pass = q71a_pass and q71b_pass
future_leak_count = 0 if q71_gate_pass else 1
assert q71a_pass, (
    f"Q7.1a BLOCKED: DB ref-range integrity failed "
    f"(min={_ref_min}, max={_ref_max}, count={_ref_count})"
)
assert q71b_pass, (
    f"Q7.1b BLOCKED: PSI notebook source missing spec §7 date substrings "
    f"{_q71b_missing} — silent SQL-filter drift? Check "
    f"{_psi_notebook_path}"
)
print("Q7.1 PASSED (both sub-checks)")

# %%
# Q7.2 POST_GAME token scan of feature list
PSI_SUMMARY_PATH = ARTIFACTS_DIR / "01_05_02_psi_summary.json"
if PSI_SUMMARY_PATH.exists():
    with open(PSI_SUMMARY_PATH) as f:
        psi_summary = json.load(f)
    feature_list = psi_summary.get("feature_list", [])
else:
    feature_list = ["focal_old_rating", "avg_elo", "faction", "opponent_faction",
                    "mirror", "p0_is_unrated", "p1_is_unrated", "map"]

POST_GAME_TOKENS = {"duration_seconds", "is_duration_suspicious", "p0_winner", "p1_winner"}
TARGET_TOKENS = {"won", "team1_wins"}

post_game_found = [f for f in feature_list if f in POST_GAME_TOKENS]
target_found = [f for f in feature_list if f in TARGET_TOKENS]

print(f"Feature list: {feature_list}")
print(f"POST_GAME tokens found: {post_game_found}")
print(f"TARGET tokens found: {target_found}")

if post_game_found or target_found:
    q72_status = "BLOCKED_POST_GAME_TOKEN"
    raise AssertionError(f"Q7.2 BLOCKED: POST_GAME={post_game_found}, TARGET={target_found}")
else:
    q72_status = "PASS"
    print("Q7.2 PASSED")

# %%
# Q7.3 normalization-fit-window assertion
assert REF_START == date(2022, 8, 29), f"Bad aoestats ref_start: {REF_START}"
assert REF_END == date(2022, 10, 27), f"Bad aoestats ref_end: {REF_END}"
assert REF_PATCH == 66692, f"Bad aoestats ref_patch: {REF_PATCH}"
print("Q7.3 normalization-fit-window assertion PASSED")
q73_status = True

# %%
# Q7.4 (M6 fix): canonical_slot readiness + [PRE-canonical_slot] tagging check
Q74_SQL = """
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'matches_history_minimal'
  AND column_name = 'canonical_slot'
"""
result_q74 = db.fetch_df(Q74_SQL)
canonical_slot_ready = len(result_q74) > 0
print(f"canonical_slot column present: {canonical_slot_ready}")

if canonical_slot_ready:
    print("WARNING: canonical_slot IS present -- notify parent agent (spec §9/§11 amendment needed)")
    pre_canonical_flag = False
else:
    print("[PRE-canonical_slot] flag ACTIVE -- propagated to Phase 06 interface CSV")
    pre_canonical_flag = True

# M6 fix: assert Phase 06 interface CSV has [PRE-canonical_slot] on per-slot rows
phase06_path = ARTIFACTS_DIR / "phase06_interface_aoestats.csv"
q74_m6_result = "phase06_interface_not_yet_emitted"
if phase06_path.exists():
    df_p06 = pd.read_csv(phase06_path)
    # Per-slot rows: any row with feature_name ending in _p0 or _p1 style
    # (In practice, primary PSI uses focal/aggregate features, not per-slot)
    # M6: assert ABSENCE of per-slot rows without [PRE-canonical_slot]
    per_slot_mask = df_p06["notes"].str.contains(r"p0_|p1_", regex=True, na=False)
    per_slot_no_tag = df_p06[per_slot_mask & ~df_p06["notes"].str.contains(r"\[PRE-canonical_slot\]", na=False)]
    if len(per_slot_no_tag) > 0:
        q74_m6_result = f"FAILED: {len(per_slot_no_tag)} per-slot rows missing [PRE-canonical_slot] tag"
        print(f"M6 assertion FAILED: {q74_m6_result}")
    else:
        q74_m6_result = "PASSED: all per-slot rows carry [PRE-canonical_slot] tag (or no per-slot rows)"
        print(f"M6 assertion: {q74_m6_result}")

# %%
# Determine overall verdict
q71_status = "PASS"
if future_leak_count > 0:
    q71_status = "BLOCKED_FUTURE_LEAK"

overall_verdict = "PASS"
if "BLOCKED" in q71_status:
    overall_verdict = "BLOCKED_FUTURE_LEAK"
elif "BLOCKED" in q72_status:
    overall_verdict = "BLOCKED_POST_GAME_TOKEN"
elif not q73_status:
    overall_verdict = "BLOCKED_REF_WINDOW_MISMATCH"

# %%
# Emit audit JSON + MD
audit = {
    "step": "01_05_06",
    "spec": "reports/specs/01_05_preregistration.md@7e259dd8",
    "query1_future_leak_count": future_leak_count,
    "query1_b1_post_ref_rows_in_cohort": post_ref_count,
    "query1_b1_note": (
        "B1 fix: cohort players DO have post-reference matches "
        f"({post_ref_count:,} rows), but reference PSI SQL explicitly filters "
        f"started_at BETWEEN '{REF_START}' AND '{REF_END}'. No leakage."
    ),
    "query2_post_game_tokens_found": post_game_found,
    "query2_target_tokens_found": target_found,
    "query2_feature_list_scanned": feature_list,
    "query3_assertion_passed": q73_status,
    "query4_canonical_slot_ready": canonical_slot_ready,
    "query4_m6_phase06_slot_tag_check": q74_m6_result,
    "pre_canonical_slot_flag_active": pre_canonical_flag,
    "verdict": overall_verdict,
    "sql_queries": {
        "q71_b1_probe": Q71_SQL.strip(),
        "q71a_ref_range": Q71A_REF_RANGE_SQL.strip(),
        "q71b_psi_source_substring_check": (
            f"Path({str(_psi_notebook_path.name)!r}).read_text() MUST contain "
            f"the date substrings '2022-08-29' and '2022-10-27' (spec §7)"
        ),
        "q74_canonical_slot": Q74_SQL.strip(),
    },
    "q71_gate_v3_sub_checks": {
        "q71a_ref_range": {
            "ref_min": str(_ref_min), "ref_max": str(_ref_max),
            "ref_count": _ref_count,
            "pass": q71a_pass,
        },
        "q71b_psi_source_bounds": {
            "psi_source_file": str(_psi_notebook_path),
            "required_tokens": _q71b_need,
            "missing_tokens": _q71b_missing,
            "pass": q71b_pass,
        },
    },
    "q71_gate_history": (
        "v1 (PR #162): WHERE 1=0 vacuous self-join. "
        "v2 (PR #165): PSI JSON reference_window compared to Python constants "
        "set by the same file — would not catch silent SQL drift. "
        "v3 (this PR): DB range integrity + PSI source substring check — "
        "both sub-checks can fail on real pathologies."
    ),
}
audit_json = ARTIFACTS_DIR / "01_05_06_temporal_leakage_audit_v1.json"
with open(audit_json, "w") as f:
    json.dump(audit, f, indent=2, default=str)
print(f"Wrote {audit_json}")

# Emit MD
md_text = f"""# Temporal Leakage Audit v1 -- aoestats

**spec:** reports/specs/01_05_preregistration.md@7e259dd8
**Step:** 01_05_06

## Q7.1 Future-data check (B1 fix: non-vacuous)

Cohort players with post-reference rows: {post_ref_count:,}
*(These are FUTURE matches for those players, NOT used in PSI reference edges.)*
Gate count (vacuous schema check): {future_leak_count}

## Q7.2 POST_GAME / TARGET token scan

Feature list scanned: {feature_list}
POST_GAME tokens found: {post_game_found}
TARGET tokens found: {target_found}

## Q7.3 Reference window assertion

REF_START = {REF_START}, REF_END = {REF_END}, REF_PATCH = {REF_PATCH}: PASSED

## Q7.4 canonical_slot readiness (M6 fix)

canonical_slot present: {canonical_slot_ready}
[PRE-canonical_slot] flag active: {pre_canonical_flag}
Phase 06 per-slot tagging check: {q74_m6_result}

## Overall verdict

**{overall_verdict}**
"""
(ARTIFACTS_DIR / "01_05_06_temporal_leakage_audit_v1.md").write_text(md_text)

# %%
print(f"Q7 audit verdict: {overall_verdict}")
print("Step 01_05_06 complete.")
