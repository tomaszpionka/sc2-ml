#!/usr/bin/env python3
"""Phase 02 readiness contracts validator (T05).

Deterministic, read-only validator that audits the cross-dataset Phase 02
readiness contract bundle (T01-T04 outputs) against locked sibling specs,
the SC2 tracker eligibility CSV, and source-specific AoE2 ladder
provenance. Emits a machine-readable JSON report and a human-readable
Markdown report.

Spec source: planning/current_plan.md T05 (T05A amendment, 2026-05-05) and
.claude/rules/data-analysis-lineage.md anti-GIGO discipline.

Constraints (enforced by this script's design):
- read-only outside the two declared output paths;
- stdlib-only (no third-party deps);
- no network access;
- no raw-data reads;
- deterministic: same input state -> same output (apart from `run_date`);
- stable list/dict ordering throughout the JSON payload;
- JSON output uses sorted keys and 2-space indent;
- non-zero exit code if any BLOCKER fires.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

SPEC_ID = "CROSS-02-04-v1"
SCHEMA_VERSION = "v1"

T01_CLOSEOUT = REPO_ROOT / "thesis/pass2_evidence/phase01_closeout_summary.md"
T02_LINEAGE_RULE = REPO_ROOT / ".claude/rules/data-analysis-lineage.md"
T03_FE_PLAN = REPO_ROOT / "reports/specs/02_02_feature_engineering_plan.md"
T04_AUDIT_PROTOCOL = REPO_ROOT / "reports/specs/02_03_temporal_feature_audit_protocol.md"

LOCKED_INPUT_CONTRACT = REPO_ROOT / "reports/specs/02_00_feature_input_contract.md"
LOCKED_LEAKAGE_AUDIT = REPO_ROOT / "reports/specs/02_01_leakage_audit_protocol.md"

TRACKER_CSV = (
    REPO_ROOT
    / "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts"
    / "01_exploration/03_profiling/tracker_events_feature_eligibility.csv"
)

PLANNING_PLAN = REPO_ROOT / "planning/current_plan.md"
PLANNING_CRITIQUE = REPO_ROOT / "planning/current_plan.critique.md"
PLANNING_CRITIQUE_RESOLUTION = REPO_ROOT / "planning/current_plan.critique_resolution.md"
PLANNING_INDEX = REPO_ROOT / "planning/INDEX.md"

EXPECTED_PR_FILES: list[str] = sorted(
    [
        ".claude/rules/data-analysis-lineage.md",
        "planning/INDEX.md",
        "planning/current_plan.md",
        "planning/current_plan.critique.md",
        "planning/current_plan.critique_resolution.md",
        "reports/specs/02_02_feature_engineering_plan.md",
        "reports/specs/02_03_temporal_feature_audit_protocol.md",
        "thesis/pass2_evidence/phase01_closeout_summary.md",
    ]
)

T05_DECLARED_OUTPUTS: list[str] = sorted(
    [
        "scripts/validate_phase02_readiness_contracts.py",
        "reports/specs/02_04_cross_spec_consistency_report.json",
        "reports/specs/02_04_cross_spec_consistency_report.md",
    ]
)

REQUIRED_PHRASES_T01: list[str] = [
    "GATE-14A6 outcome: narrowed",
    "full tracker scope is not closed",
    "aoestats Tier 4",
    "aoe2companion mixed-mode",
    "tracker-derived features are never pre-game",
]
REQUIRED_PHRASES_T02: list[str] = [
    "A generated artifact is not evidence",
    "halt before artifact generation",
    "aoestats is Tier 4",
    "aoe2companion ID 6 + ID 18 is mixed-mode",
]
REQUIRED_PHRASES_T03: list[str] = [
    "tracker-derived features are never pre-game",
    "history_time < target_time",
    "event.loop <= cutoff_loop",
    "aoestats Tier 4",
    "aoe2companion mixed-mode",
    "GATE-14A6 outcome: narrowed",
    "full tracker scope is not closed",
]
REQUIRED_PHRASES_T04: list[str] = [
    "history_time < target_time",
    "event.loop <= cutoff_loop",
    "tracker-derived features are never pre-game",
    "GATE-14A6 outcome: narrowed",
    "full tracker scope is not closed",
    "aoestats Tier 4",
    "aoe2companion mixed-mode",
    "does not replace CROSS-02-01-v1.0.1",
]

FORBIDDEN_SUBSTRINGS: list[str] = [
    "ranked ladder only",
    "tracker-derived pre-game",
    "full tracker scope closed",
    "feature tables generated",
    "replaces CROSS-02-01",
    "supersedes CROSS-02-01",
]

TRACKER_EXPECTED_ELIGIBLE_NOW: list[str] = sorted(
    [
        "count_units_built_by_cutoff_loop",
        "count_units_killed_by_cutoff_loop",
        "morph_count_by_cutoff_loop",
        "building_construction_count_by_cutoff_loop",
        "slot_identity_consistency",
    ]
)
TRACKER_EXPECTED_ELIGIBLE_WITH_CAVEAT: list[str] = sorted(
    [
        "minerals_collection_rate_history_mean",
        "army_value_at_5min_snapshot",
        "supply_used_at_cutoff_snapshot",
        "food_used_max_history",
        "time_to_first_expansion_loop",
        "count_units_lost_by_cutoff_loop",
        "count_upgrades_by_cutoff_loop",
    ]
)
TRACKER_EXPECTED_BLOCKED: list[str] = sorted(
    [
        "mind_control_event_count",
        "army_centroid_at_cutoff_snapshot",
        "playerstats_cumulative_economy_fields",
    ]
)
TRACKER_SANITY_GATE_FAMILY = "slot_identity_consistency"

CROSS_02_03_DIMENSIONS: list[str] = [f"D{i}" for i in range(1, 16)]

CROSS_02_03_FUTURE_SCHEMA_FIELDS: list[str] = [
    "spec_version",
    "feature_family_id",
    "dataset",
    "prediction_setting",
    "source_table_or_event_family",
    "source_grain",
    "model_input_grain",
    "temporal_anchor",
    "cutoff_rule",
    "audit_dimensions_passed",
    "caveats",
    "blocking_reason",
    "verdict",
    "reviewer_notes",
]

DATASET_ANCHORS: dict[str, str] = {
    "sc2egset": "details_timeUTC",
    "aoestats": "started_timestamp",
    "aoe2companion": "started",
}


@dataclass
class Finding:
    """A single check observation classified by severity."""

    severity: str
    location: str
    description: str

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "location": self.location,
            "description": self.description,
        }


@dataclass
class Check:
    """A single named validation dimension."""

    name: str
    verdict: str
    details: str
    evidence: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "verdict": self.verdict,
            "details": self.details,
            "evidence": list(self.evidence),
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class ValidatorContext:
    base_ref: str
    head_sha: str
    branch: str
    run_date: str
    command_line: str
    diff_files: list[str]
    diff_stat: str


def run_git(*args: str) -> str:
    """Run a read-only git command and return stripped stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def read_text(path: Path) -> str:
    """Read a file as UTF-8 text. Returns empty string if missing."""
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def find_lines_containing(text: str, needle: str) -> list[tuple[int, str]]:
    """Return [(1-based line number, line text)] for every line containing the needle."""
    out: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            out.append((i, line))
    return out


def get_context_window(lines: list[str], line_no: int, radius: int = 1) -> str:
    """Return joined text of a context window around line_no (1-based).

    The window spans
    ``[max(1, line_no - radius) .. min(len(lines), line_no + radius)]``,
    joined with a single space so phrases whose meaning straddles physical
    line breaks remain matchable. This makes the ranked-language classifiers
    robust to Markdown line-wrapping that splits negation markers from their
    target substring (e.g., 'MUST NOT be called' on one line, 'unqualified
    ranked ladder' on the next).

    Boundary-clipped: returns an empty string if `lines` is empty or
    `line_no < 1`.
    """
    if not lines or line_no < 1:
        return ""
    start = max(1, line_no - radius)
    end = min(len(lines), line_no + radius)
    return " ".join(lines[start - 1:end])


def classify_ranked_only_context(context_text: str) -> str:
    """Classify a context window containing 'ranked-only'.

    The argument is a joined multi-line context window (see
    `get_context_window`) so negation markers wrapped across Markdown line
    breaks are still detected.

    Returns 'OK_NEGATION' if the context uses 'ranked-only' inside a known
    negation, prohibition, or falsifier counter-example pattern;
    returns 'BLOCKER' otherwise.
    """
    lower = context_text.lower()
    if "not ranked-only" in lower:
        return "OK_NEGATION"
    if "must not" in lower and "ranked-only" in lower:
        return "OK_NEGATION"
    if "as ranked-only" in lower:
        return "OK_NEGATION"
    if "asserts that" in lower and "ranked-only" in lower:
        return "OK_NEGATION"
    if "no new doc" in lower and "ranked-only" in lower:
        return "OK_NEGATION"
    return "BLOCKER"


def classify_ranked_ladder_context(context_text: str) -> str:
    """Classify a context window containing 'ranked ladder'.

    Caller is responsible for filtering out 'ranked ladder only' before
    calling this classifier. The argument is a joined multi-line context
    window (see `get_context_window`) so ID-6 / negation context wrapped
    across line breaks is still detected.

    Returns 'OK_SOURCE_SPECIFIC' only when the context carries explicit ID-6
    ranked-candidate context: 'ranked candidate', 'ID 6', or 'rm_1v1'. The
    bare phrase 'ranked 1v1' is NOT sufficient by itself.

    Returns 'OK_NEGATION' for prohibition / falsifier patterns;
    returns 'BLOCKER' otherwise.
    """
    lower = context_text.lower()
    # Source-specific OK requires explicit ID 6 / rm_1v1 / ranked-candidate context.
    # Generic 'ranked 1v1' alone is insufficient — it does not pin the source.
    if "ranked candidate" in lower:
        return "OK_SOURCE_SPECIFIC"
    if "id 6" in lower or "rm_1v1" in lower:
        return "OK_SOURCE_SPECIFIC"
    if "must not" in lower and "ranked ladder" in lower:
        return "OK_NEGATION"
    if "no new doc" in lower and "ranked ladder" in lower:
        return "OK_NEGATION"
    falsifier_markers = (
        "is described as",
        "any aoe2 source is called",
        "is called unqualified",
        "is referred to as",
    )
    for marker in falsifier_markers:
        if marker in lower:
            return "OK_NEGATION"
    return "BLOCKER"


def check_pr_file_scope(ctx: ValidatorContext) -> Check:
    name = "1. PR file scope"
    diff_files = sorted(ctx.diff_files)
    expected = sorted(EXPECTED_PR_FILES)
    declared_outputs = set(T05_DECLARED_OUTPUTS)
    findings: list[Finding] = []

    extras = [f for f in diff_files if f not in expected and f not in declared_outputs]
    missing = [f for f in expected if f not in diff_files]

    for path in extras:
        findings.append(
            Finding(
                severity="BLOCKER",
                location=path,
                description=f"PR includes path not in declared File Manifest: {path}",
            )
        )
    for path in missing:
        findings.append(
            Finding(
                severity="BLOCKER",
                location=path,
                description=f"Declared File Manifest path missing from PR diff: {path}",
            )
        )

    if findings:
        verdict = "BLOCKED"
        details = (
            f"PR diff contains {len(extras)} unexpected and {len(missing)} missing paths."
        )
    else:
        verdict = "PASS"
        details = (
            f"PR diff matches declared File Manifest "
            f"({len(expected)} expected paths; T05 outputs allowed if present)."
        )

    evidence: list[str] = [f"git diff --name-only {ctx.base_ref}..HEAD"]
    evidence.extend(diff_files)

    return Check(
        name=name,
        verdict=verdict,
        details=details,
        evidence=evidence,
        findings=findings,
    )


def check_required_phrases() -> Check:
    name = "2. Required positive phrases"
    findings: list[Finding] = []
    evidence: list[str] = []

    file_phrase_map = (
        (T01_CLOSEOUT, REQUIRED_PHRASES_T01),
        (T02_LINEAGE_RULE, REQUIRED_PHRASES_T02),
        (T03_FE_PLAN, REQUIRED_PHRASES_T03),
        (T04_AUDIT_PROTOCOL, REQUIRED_PHRASES_T04),
    )
    for path, phrases in file_phrase_map:
        rel = str(path.relative_to(REPO_ROOT))
        if not path.is_file():
            findings.append(
                Finding(
                    severity="BLOCKER",
                    location=rel,
                    description=f"Required input file missing: {rel}",
                )
            )
            continue
        text = read_text(path)
        for phrase in phrases:
            if phrase not in text:
                findings.append(
                    Finding(
                        severity="BLOCKER",
                        location=rel,
                        description=f"Required phrase missing: {phrase!r}",
                    )
                )
            else:
                evidence.append(f"{rel}: {phrase!r} x{text.count(phrase)}")

    blockers = [f for f in findings if f.severity == "BLOCKER"]
    if blockers:
        verdict = "BLOCKED"
        details = f"{len(blockers)} required phrase(s) missing across T01-T04 outputs."
    else:
        verdict = "PASS"
        details = "All required positive phrases present in their mandated files."

    evidence.sort()
    return Check(
        name=name,
        verdict=verdict,
        details=details,
        evidence=evidence,
        findings=findings,
    )


def check_forbidden_substrings() -> Check:
    name = "3. Forbidden substrings"
    findings: list[Finding] = []
    evidence: list[str] = []
    paths = (T01_CLOSEOUT, T02_LINEAGE_RULE, T03_FE_PLAN, T04_AUDIT_PROTOCOL)

    for path in paths:
        text = read_text(path)
        rel = str(path.relative_to(REPO_ROOT))
        if not text:
            continue
        text_lines = text.splitlines()
        for substr in FORBIDDEN_SUBSTRINGS:
            for line_no, line in find_lines_containing(text, substr):
                findings.append(
                    Finding(
                        severity="BLOCKER",
                        location=f"{rel}:{line_no}",
                        description=(
                            f"Forbidden substring {substr!r} present: "
                            f"{line.strip()[:200]}"
                        ),
                    )
                )

        for line_no, line in find_lines_containing(text, "ranked-only"):
            context_text = get_context_window(text_lines, line_no, radius=1)
            classification = classify_ranked_only_context(context_text)
            if classification == "BLOCKER":
                findings.append(
                    Finding(
                        severity="BLOCKER",
                        location=f"{rel}:{line_no}",
                        description=(
                            "'ranked-only' not in negation about aoe2companion "
                            "mixed-mode (1-line context window). Line: "
                            f"{line.strip()[:120]} | Context: "
                            f"{context_text.strip()[:240]}"
                        ),
                    )
                )
            else:
                evidence.append(
                    f"{rel}:{line_no} {classification} (ranked-only): "
                    f"line='{line.strip()[:80]}' "
                    f"ctx='{context_text.strip()[:160]}'"
                )

        for line_no, line in find_lines_containing(text, "ranked ladder"):
            if "ranked ladder only" in line:
                continue
            context_text = get_context_window(text_lines, line_no, radius=1)
            classification = classify_ranked_ladder_context(context_text)
            if classification == "BLOCKER":
                findings.append(
                    Finding(
                        severity="BLOCKER",
                        location=f"{rel}:{line_no}",
                        description=(
                            "'ranked ladder' not in negation/source-specific "
                            "context (1-line context window). Line: "
                            f"{line.strip()[:120]} | Context: "
                            f"{context_text.strip()[:240]}"
                        ),
                    )
                )
            else:
                evidence.append(
                    f"{rel}:{line_no} {classification} (ranked ladder): "
                    f"line='{line.strip()[:80]}' "
                    f"ctx='{context_text.strip()[:160]}'"
                )

    blockers = [f for f in findings if f.severity == "BLOCKER"]
    if blockers:
        verdict = "BLOCKED"
        details = (
            f"{len(blockers)} forbidden substring or unclassified ranked-language "
            "line(s) detected."
        )
    else:
        verdict = "PASS"
        details = (
            "No forbidden substrings; all 'ranked ladder' / 'ranked-only' "
            "occurrences in negation or source-specific context."
        )

    evidence.sort()
    return Check(
        name=name,
        verdict=verdict,
        details=details,
        evidence=evidence,
        findings=findings,
    )


def check_non_supersession() -> Check:
    name = "4. Non-supersession of CROSS-02-00-v3.0.1 and CROSS-02-01-v1.0.1"
    findings: list[Finding] = []
    evidence: list[str] = []

    expected = (
        (T03_FE_PLAN, ("does not supersede or amend", "supersedes: null")),
        (T04_AUDIT_PROTOCOL, ("does not replace CROSS-02-01-v1.0.1", "supersedes: null")),
    )
    for path, phrases in expected:
        rel = str(path.relative_to(REPO_ROOT))
        text = read_text(path)
        for phrase in phrases:
            if phrase not in text:
                findings.append(
                    Finding(
                        severity="BLOCKER",
                        location=rel,
                        description=f"Non-supersession marker missing: {phrase!r}",
                    )
                )
            else:
                evidence.append(f"{rel}: {phrase!r} present")

    blockers = [f for f in findings if f.severity == "BLOCKER"]
    if blockers:
        verdict = "BLOCKED"
        details = f"{len(blockers)} non-supersession marker(s) missing."
    else:
        verdict = "PASS"
        details = (
            "CROSS-02-02-v1 and CROSS-02-03-v1 explicitly declare non-supersession "
            "of locked sibling specs."
        )

    evidence.sort()
    return Check(
        name=name,
        verdict=verdict,
        details=details,
        evidence=evidence,
        findings=findings,
    )


def _read_tracker_csv() -> tuple[list[str], list[str], list[str], list[str]]:
    """Read the SC2 tracker eligibility CSV; return (eligible_now, caveat, blocked, other)."""
    eligible_now: list[str] = []
    eligible_caveat: list[str] = []
    blocked: list[str] = []
    other: list[str] = []
    if not TRACKER_CSV.is_file():
        return eligible_now, eligible_caveat, blocked, other
    with TRACKER_CSV.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            family = (row.get("feature_family") or "").strip()
            status = (row.get("status_in_game_snapshot") or "").strip()
            if status == "eligible_for_phase02_now":
                eligible_now.append(family)
            elif status == "eligible_with_caveat":
                eligible_caveat.append(family)
            elif status == "blocked_until_additional_validation":
                blocked.append(family)
            else:
                other.append(f"{family}::{status}")
    return eligible_now, eligible_caveat, blocked, other


def check_tracker_csv() -> Check:
    name = "5. SC2 tracker eligibility consistency"
    findings: list[Finding] = []
    evidence: list[str] = []

    if not TRACKER_CSV.is_file():
        findings.append(
            Finding(
                severity="BLOCKER",
                location=str(TRACKER_CSV.relative_to(REPO_ROOT)),
                description="Tracker eligibility CSV not found",
            )
        )
        return Check(
            name=name,
            verdict="BLOCKED",
            details="Tracker CSV missing.",
            evidence=evidence,
            findings=findings,
        )

    eligible_now, eligible_caveat, blocked, other = _read_tracker_csv()
    eligible_now_sorted = sorted(eligible_now)
    eligible_caveat_sorted = sorted(eligible_caveat)
    blocked_sorted = sorted(blocked)

    evidence.append(
        f"eligible_for_phase02_now ({len(eligible_now_sorted)}): "
        f"{', '.join(eligible_now_sorted)}"
    )
    evidence.append(
        f"eligible_with_caveat ({len(eligible_caveat_sorted)}): "
        f"{', '.join(eligible_caveat_sorted)}"
    )
    evidence.append(
        f"blocked_until_additional_validation ({len(blocked_sorted)}): "
        f"{', '.join(blocked_sorted)}"
    )

    csv_rel = str(TRACKER_CSV.relative_to(REPO_ROOT))

    if other:
        for entry in other:
            findings.append(
                Finding(
                    severity="WARNING",
                    location=csv_rel,
                    description=f"Unexpected tracker row status: {entry}",
                )
            )

    if len(eligible_now_sorted) != 5:
        findings.append(
            Finding(
                severity="BLOCKER",
                location=csv_rel,
                description=(
                    f"Expected 5 eligible_for_phase02_now rows; got "
                    f"{len(eligible_now_sorted)}"
                ),
            )
        )
    if len(eligible_caveat_sorted) != 7:
        findings.append(
            Finding(
                severity="BLOCKER",
                location=csv_rel,
                description=(
                    f"Expected 7 eligible_with_caveat rows; got "
                    f"{len(eligible_caveat_sorted)}"
                ),
            )
        )
    if len(blocked_sorted) != 3:
        findings.append(
            Finding(
                severity="BLOCKER",
                location=csv_rel,
                description=(
                    f"Expected 3 blocked_until_additional_validation rows; got "
                    f"{len(blocked_sorted)}"
                ),
            )
        )

    if eligible_now_sorted != TRACKER_EXPECTED_ELIGIBLE_NOW:
        findings.append(
            Finding(
                severity="BLOCKER",
                location=csv_rel,
                description=(
                    f"eligible_for_phase02_now family set mismatch. "
                    f"Expected {TRACKER_EXPECTED_ELIGIBLE_NOW}; got "
                    f"{eligible_now_sorted}"
                ),
            )
        )
    if eligible_caveat_sorted != TRACKER_EXPECTED_ELIGIBLE_WITH_CAVEAT:
        findings.append(
            Finding(
                severity="BLOCKER",
                location=csv_rel,
                description=(
                    f"eligible_with_caveat family set mismatch. "
                    f"Expected {TRACKER_EXPECTED_ELIGIBLE_WITH_CAVEAT}; got "
                    f"{eligible_caveat_sorted}"
                ),
            )
        )
    if blocked_sorted != TRACKER_EXPECTED_BLOCKED:
        findings.append(
            Finding(
                severity="BLOCKER",
                location=csv_rel,
                description=(
                    f"blocked family set mismatch. Expected "
                    f"{TRACKER_EXPECTED_BLOCKED}; got {blocked_sorted}"
                ),
            )
        )

    text_t03 = read_text(T03_FE_PLAN)
    t03_rel = str(T03_FE_PLAN.relative_to(REPO_ROOT))
    for family in eligible_now_sorted + eligible_caveat_sorted + blocked_sorted:
        if family not in text_t03:
            findings.append(
                Finding(
                    severity="BLOCKER",
                    location=t03_rel,
                    description=(
                        f"Tracker family {family!r} not represented in CROSS-02-02"
                    ),
                )
            )

    if TRACKER_SANITY_GATE_FAMILY in text_t03:
        sanity_pattern = re.compile(
            rf"{re.escape(TRACKER_SANITY_GATE_FAMILY)}.{{0,400}}sanity[\s_-]*gate"
            r"|"
            rf"sanity[\s_-]*gate.{{0,400}}{re.escape(TRACKER_SANITY_GATE_FAMILY)}",
            re.IGNORECASE | re.DOTALL,
        )
        if sanity_pattern.search(text_t03) is None:
            findings.append(
                Finding(
                    severity="BLOCKER",
                    location=t03_rel,
                    description=(
                        f"{TRACKER_SANITY_GATE_FAMILY} not marked as a sanity gate"
                    ),
                )
            )
        else:
            evidence.append(
                f"{t03_rel}: {TRACKER_SANITY_GATE_FAMILY} marked as sanity gate"
            )

    text_t04 = read_text(T04_AUDIT_PROTOCOL)
    t04_rel = str(T04_AUDIT_PROTOCOL.relative_to(REPO_ROOT))
    for blocked_fam in blocked_sorted:
        if blocked_fam not in text_t04:
            findings.append(
                Finding(
                    severity="BLOCKER",
                    location=t04_rel,
                    description=(
                        f"Blocked tracker family {blocked_fam!r} not enumerated "
                        "in CROSS-02-03"
                    ),
                )
            )

    for path in (T03_FE_PLAN, T04_AUDIT_PROTOCOL):
        rel = str(path.relative_to(REPO_ROOT))
        text = read_text(path)
        if "GATE-14A6 outcome: narrowed" not in text:
            findings.append(
                Finding(
                    severity="BLOCKER",
                    location=rel,
                    description="'GATE-14A6 outcome: narrowed' missing",
                )
            )
        if "full tracker scope is not closed" not in text:
            findings.append(
                Finding(
                    severity="BLOCKER",
                    location=rel,
                    description="'full tracker scope is not closed' missing",
                )
            )
        if "22.4" not in text:
            findings.append(
                Finding(
                    severity="WARNING",
                    location=rel,
                    description=(
                        "loops/seconds factor 22.4 not cited; V1 caveat may be "
                        "unsupported"
                    ),
                )
            )

    blockers = [f for f in findings if f.severity == "BLOCKER"]
    warnings = [f for f in findings if f.severity == "WARNING"]
    if blockers:
        verdict = "BLOCKED"
        details = (
            f"{len(blockers)} BLOCKER(s) in tracker eligibility consistency; "
            f"{len(warnings)} WARNING(s)."
        )
    elif warnings:
        verdict = "PASS_WITH_WARNINGS"
        details = (
            f"Tracker counts and family names verified against CSV; "
            f"{len(warnings)} WARNING(s) recorded."
        )
    else:
        verdict = "PASS"
        details = (
            "Tracker counts (5/7/3) and family names verified against CSV; "
            "T03/T04 represent all 15 families with correct status."
        )

    evidence.sort()
    return Check(
        name=name,
        verdict=verdict,
        details=details,
        evidence=evidence,
        findings=findings,
    )


def check_aoe2_source_labels() -> Check:
    name = "6. AoE2 source-label discipline"
    findings: list[Finding] = []
    evidence: list[str] = []

    for path in (T01_CLOSEOUT, T02_LINEAGE_RULE, T03_FE_PLAN, T04_AUDIT_PROTOCOL):
        text = read_text(path)
        rel = str(path.relative_to(REPO_ROOT))
        if path != T02_LINEAGE_RULE:
            if "aoestats Tier 4" not in text:
                findings.append(
                    Finding(
                        severity="BLOCKER",
                        location=rel,
                        description="'aoestats Tier 4' label missing",
                    )
                )
            else:
                evidence.append(
                    f"{rel}: 'aoestats Tier 4' x{text.count('aoestats Tier 4')}"
                )
        if path in (T01_CLOSEOUT, T03_FE_PLAN, T04_AUDIT_PROTOCOL):
            if "aoe2companion mixed-mode" not in text:
                findings.append(
                    Finding(
                        severity="BLOCKER",
                        location=rel,
                        description="'aoe2companion mixed-mode' label missing",
                    )
                )
            else:
                evidence.append(
                    f"{rel}: 'aoe2companion mixed-mode' "
                    f"x{text.count('aoe2companion mixed-mode')}"
                )

    for path in (T03_FE_PLAN, T04_AUDIT_PROTOCOL):
        text = read_text(path)
        rel = str(path.relative_to(REPO_ROOT))
        for required in ("ID 6", "rm_1v1", "ID 18", "qp_rm_1v1"):
            if required not in text:
                findings.append(
                    Finding(
                        severity="BLOCKER",
                        location=rel,
                        description=(
                            f"AoE2 source-label component missing: {required!r}"
                        ),
                    )
                )
        if "ranked candidate" not in text:
            findings.append(
                Finding(
                    severity="WARNING",
                    location=rel,
                    description="'ranked candidate' qualifier for ID 6 not present",
                )
            )
        lower = text.lower()
        if "quickplay" not in lower or "matchmaking" not in lower:
            findings.append(
                Finding(
                    severity="BLOCKER",
                    location=rel,
                    description="quickplay/matchmaking qualifier for ID 18 missing",
                )
            )

    blockers = [f for f in findings if f.severity == "BLOCKER"]
    warnings = [f for f in findings if f.severity == "WARNING"]
    if blockers:
        verdict = "BLOCKED"
        details = (
            f"{len(blockers)} AoE2 source-label BLOCKER(s); "
            f"{len(warnings)} WARNING(s)."
        )
    elif warnings:
        verdict = "PASS_WITH_WARNINGS"
        details = (
            f"AoE2 source labels present; {len(warnings)} optional qualifier(s) "
            "absent."
        )
    else:
        verdict = "PASS"
        details = (
            "AoE2 source labels (Tier 4, mixed-mode, ID 6 ranked candidate, "
            "ID 18 quickplay/matchmaking) all preserved."
        )

    evidence.sort()
    return Check(
        name=name,
        verdict=verdict,
        details=details,
        evidence=evidence,
        findings=findings,
    )


def check_temporal_leakage_rules() -> Check:
    name = "7. Temporal leakage rules"
    findings: list[Finding] = []
    evidence: list[str] = []

    for path in (T03_FE_PLAN, T04_AUDIT_PROTOCOL):
        text = read_text(path)
        rel = str(path.relative_to(REPO_ROOT))
        for rule in ("history_time < target_time", "event.loop <= cutoff_loop"):
            if rule not in text:
                findings.append(
                    Finding(
                        severity="BLOCKER",
                        location=rel,
                        description=f"Temporal rule missing: {rule!r}",
                    )
                )
            else:
                evidence.append(f"{rel}: {rule!r} x{text.count(rule)}")
        for dataset, anchor in DATASET_ANCHORS.items():
            if anchor not in text:
                findings.append(
                    Finding(
                        severity="BLOCKER",
                        location=rel,
                        description=(
                            f"Per-dataset anchor missing for {dataset}: {anchor!r}"
                        ),
                    )
                )
        if "UTC" not in text:
            findings.append(
                Finding(
                    severity="BLOCKER",
                    location=rel,
                    description="UTC session discipline marker absent",
                )
            )
        lower = text.lower()
        if "full-replay" not in lower and "full replay" not in lower:
            findings.append(
                Finding(
                    severity="WARNING",
                    location=rel,
                    description=(
                        "full-replay aggregate exclusion not explicitly mentioned"
                    ),
                )
            )

    blockers = [f for f in findings if f.severity == "BLOCKER"]
    warnings = [f for f in findings if f.severity == "WARNING"]
    if blockers:
        verdict = "BLOCKED"
        details = (
            f"{len(blockers)} temporal-leakage rule BLOCKER(s); "
            f"{len(warnings)} WARNING(s)."
        )
    elif warnings:
        verdict = "PASS_WITH_WARNINGS"
        details = f"Temporal rules present; {len(warnings)} WARNING(s)."
    else:
        verdict = "PASS"
        details = (
            "history_time < target_time, event.loop <= cutoff_loop, per-dataset "
            "anchors, and UTC discipline all preserved."
        )

    evidence.sort()
    return Check(
        name=name,
        verdict=verdict,
        details=details,
        evidence=evidence,
        findings=findings,
    )


def check_cold_start_gates() -> Check:
    name = "8. Cold-start / no-magic-number gates"
    findings: list[Finding] = []
    evidence: list[str] = []

    gate_markers = (
        "gates, not constants",
        "No magic",
        "training fold",
        "training-fold",
        "Invariant I7",
    )
    suspicious_pattern = re.compile(
        r"\b(?:pseudocount|smoothing strength|threshold)\s*[mKα]?\s*=\s*\d+",
        re.IGNORECASE,
    )

    for path in (T03_FE_PLAN, T04_AUDIT_PROTOCOL):
        text = read_text(path)
        rel = str(path.relative_to(REPO_ROOT))
        any_gate = any(marker in text for marker in gate_markers)
        if not any_gate:
            findings.append(
                Finding(
                    severity="BLOCKER",
                    location=rel,
                    description=(
                        "Cold-start gate language ('gates, not constants' / "
                        "'No magic' / 'training fold' / 'I7') absent"
                    ),
                )
            )
        else:
            for marker in gate_markers:
                if marker in text:
                    evidence.append(f"{rel}: gate marker {marker!r} present")

        for line_no, line in enumerate(text.splitlines(), start=1):
            if not suspicious_pattern.search(line):
                continue
            lower = line.lower()
            negation_signals = (
                "no ",
                "not ",
                "forbidden",
                "must not",
                "without",
                "shall not",
                "no fixed",
                "without empirical",
            )
            if any(signal in lower for signal in negation_signals):
                continue
            findings.append(
                Finding(
                    severity="BLOCKER",
                    location=f"{rel}:{line_no}",
                    description=(
                        f"Suspicious magic-number commit: {line.strip()[:200]}"
                    ),
                )
            )

    blockers = [f for f in findings if f.severity == "BLOCKER"]
    if blockers:
        verdict = "BLOCKED"
        details = f"{len(blockers)} cold-start gate BLOCKER(s)."
    else:
        verdict = "PASS"
        details = "Cold-start gates declared; no magic-number commits detected."

    evidence.sort()
    return Check(
        name=name,
        verdict=verdict,
        details=details,
        evidence=evidence,
        findings=findings,
    )


def check_cross_02_03_completeness() -> Check:
    name = "9. CROSS-02-03 D1-D15 + future audit schema completeness"
    findings: list[Finding] = []
    evidence: list[str] = []
    text = read_text(T04_AUDIT_PROTOCOL)
    rel = str(T04_AUDIT_PROTOCOL.relative_to(REPO_ROOT))

    if not text:
        findings.append(
            Finding(
                severity="BLOCKER",
                location=rel,
                description="CROSS-02-03 file missing",
            )
        )
        return Check(
            name=name,
            verdict="BLOCKED",
            details="CROSS-02-03 file missing.",
            evidence=evidence,
            findings=findings,
        )

    for did in CROSS_02_03_DIMENSIONS:
        if re.search(rf"\*\*{did}\*\*", text) is None:
            findings.append(
                Finding(
                    severity="BLOCKER",
                    location=rel,
                    description=f"Audit dimension {did} not declared",
                )
            )
        else:
            evidence.append(f"{rel}: dimension {did} declared")

    for field_name in CROSS_02_03_FUTURE_SCHEMA_FIELDS:
        if f"`{field_name}`" in text:
            evidence.append(
                f"{rel}: future schema field {field_name!r} declared (backticked)"
            )
        elif field_name in text:
            evidence.append(
                f"{rel}: future schema field {field_name!r} declared "
                "(non-backticked)"
            )
        else:
            findings.append(
                Finding(
                    severity="BLOCKER",
                    location=rel,
                    description=(
                        f"Future audit artifact field missing: {field_name!r}"
                    ),
                )
            )

    no_artifact_markers = (
        "No design-time audit artifact",
        "no generated artifact",
        "No notebook is created",
    )
    if not any(marker in text for marker in no_artifact_markers):
        findings.append(
            Finding(
                severity="BLOCKER",
                location=rel,
                description=(
                    "T04 step's no-artifact / no-notebook self-declaration not found"
                ),
            )
        )

    blockers = [f for f in findings if f.severity == "BLOCKER"]
    if blockers:
        verdict = "BLOCKED"
        details = f"{len(blockers)} BLOCKER(s) in CROSS-02-03 completeness."
    else:
        verdict = "PASS"
        details = (
            f"D1-D15 declared ({len(CROSS_02_03_DIMENSIONS)}); future audit artifact "
            f"schema covers all {len(CROSS_02_03_FUTURE_SCHEMA_FIELDS)} fields; "
            "T04 declares no artifact/notebook generated."
        )

    evidence.sort()
    return Check(
        name=name,
        verdict=verdict,
        details=details,
        evidence=evidence,
        findings=findings,
    )


def aggregate_verdict(checks: list[Check]) -> str:
    if any(c.verdict == "BLOCKED" for c in checks):
        return "BLOCKED"
    if any(c.verdict == "PASS_WITH_WARNINGS" for c in checks):
        return "PASS_WITH_WARNINGS"
    return "PASS"


def collect_findings(
    checks: list[Check],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    notes: list[dict[str, str]] = []
    for check in checks:
        for finding in check.findings:
            entry = {"check": check.name, **finding.to_dict()}
            if finding.severity == "BLOCKER":
                blockers.append(entry)
            elif finding.severity == "WARNING":
                warnings.append(entry)
            else:
                notes.append(entry)
    blockers.sort(key=lambda d: (d["check"], d["location"], d["description"]))
    warnings.sort(key=lambda d: (d["check"], d["location"], d["description"]))
    notes.sort(key=lambda d: (d["check"], d["location"], d["description"]))
    return blockers, warnings, notes


def build_report_payload(
    ctx: ValidatorContext, checks: list[Check]
) -> dict[str, Any]:
    blockers, warnings, notes = collect_findings(checks)
    input_files = sorted(
        [
            str(T01_CLOSEOUT.relative_to(REPO_ROOT)),
            str(T02_LINEAGE_RULE.relative_to(REPO_ROOT)),
            str(T03_FE_PLAN.relative_to(REPO_ROOT)),
            str(T04_AUDIT_PROTOCOL.relative_to(REPO_ROOT)),
            str(LOCKED_INPUT_CONTRACT.relative_to(REPO_ROOT)),
            str(LOCKED_LEAKAGE_AUDIT.relative_to(REPO_ROOT)),
            str(TRACKER_CSV.relative_to(REPO_ROOT)),
            str(PLANNING_PLAN.relative_to(REPO_ROOT)),
            str(PLANNING_CRITIQUE.relative_to(REPO_ROOT)),
            str(PLANNING_CRITIQUE_RESOLUTION.relative_to(REPO_ROOT)),
            str(PLANNING_INDEX.relative_to(REPO_ROOT)),
        ]
    )
    declared_generated_outputs = [
        path
        for path in T05_DECLARED_OUTPUTS
        if path.endswith(".json") or path.endswith(".md")
    ]
    reproducibility_note = (
        "These reports are generated from the validator script at the recorded "
        "head_sha BEFORE the reports themselves are committed. The recorded "
        "head_sha therefore does NOT include the run's report files; the report "
        "commit lands afterwards. To reproduce a previous run byte-for-byte "
        "(apart from the run_date field), check out the recorded head_sha and "
        "re-run the recorded command_line. Determinism is guaranteed by the "
        "validator's stable list/dict ordering, sort_keys JSON output, and "
        "stdlib-only construction."
    )
    return {
        "spec_id": SPEC_ID,
        "spec_version": SPEC_ID,
        "schema_version": SCHEMA_VERSION,
        "script_path": "scripts/validate_phase02_readiness_contracts.py",
        "command_line": ctx.command_line,
        "branch": ctx.branch,
        "base_ref": ctx.base_ref,
        "head_sha": ctx.head_sha,
        "run_date": ctx.run_date,
        "declared_generated_outputs": declared_generated_outputs,
        "reproducibility_note": reproducibility_note,
        "input_files": input_files,
        "assumptions": [
            (
                "tracker_events_feature_eligibility.csv (15 rows; 5/7/3 split) is the "
                "authoritative SC2 in-game-snapshot contract per Amendment 2 of "
                "PR #208."
            ),
            (
                "CROSS-02-00-v3.0.1 and CROSS-02-01-v1.0.1 are LOCKED and binding; "
                "CROSS-02-02-v1 and CROSS-02-03-v1 must not supersede or amend them."
            ),
            (
                "AoE2 four-tier ladder governance per "
                "thesis/pass2_evidence/aoe2_ladder_provenance_audit.md is binding "
                "(aoestats Tier 4; aoe2companion ID 6 = rm_1v1 ranked candidate; "
                "ID 18 = qp_rm_1v1 quickplay/matchmaking-derived; combined = "
                "mixed-mode)."
            ),
            (
                "GATE-14A6 outcome is narrowed; full tracker scope is not closed "
                "(PR #208 14A.6 POST-VALIDATION UPDATE)."
            ),
            (
                "T01-T04 outputs are documentation/specification only; no notebooks, "
                "generated artifacts, raw data, ROADMAPs, research_logs, status "
                "YAMLs, or thesis chapters are touched in this PR."
            ),
        ],
        "sanity_checks": [
            (
                "Working tree state and git diff against base reflect only the "
                "declared File Manifest plus T05 reports."
            ),
            (
                "Each T01-T04 output contains its required positive phrases and "
                "zero literal banned substrings."
            ),
            "Tracker CSV split (5/7/3) and family names match the canonical contract.",
            (
                "CROSS-02-02-v1 and CROSS-02-03-v1 frontmatter declare "
                "supersedes: null."
            ),
        ],
        "falsifiers": [
            "Any out-of-manifest file in the PR diff is a BLOCKER.",
            "Any required phrase missing in its mandated file is a BLOCKER.",
            "Any forbidden substring present is a BLOCKER.",
            (
                "Any AoE2 source-label regression (unqualified ranked ladder for "
                "aoestats; combined scope as ranked-only) is a BLOCKER."
            ),
            (
                "Any tracker-derived feature in pre_game/history_enriched_pre_game "
                "is a BLOCKER."
            ),
            "Any 'full tracker scope is closed' assertion is a BLOCKER.",
            (
                "Any commit of CROSS-02-03 framed as replacing CROSS-02-01-v1.0.1 is "
                "a BLOCKER."
            ),
        ],
        "checks": [c.to_dict() for c in checks],
        "blockers": blockers,
        "warnings": warnings,
        "notes": notes,
        "verdict": aggregate_verdict(checks),
    }


def write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Phase 02 Readiness Contracts Cross-Spec Consistency Report")
    lines.append("")
    lines.append(f"**Spec:** {payload['spec_id']}  ")
    lines.append(f"**Schema version:** {payload['schema_version']}  ")
    lines.append(f"**Run date:** {payload['run_date']}  ")
    lines.append(f"**Branch:** `{payload['branch']}`  ")
    lines.append(f"**Base ref:** `{payload['base_ref']}`  ")
    lines.append(f"**HEAD SHA:** `{payload['head_sha']}`  ")
    lines.append(f"**Verdict:** **{payload['verdict']}**")
    lines.append("")

    lines.append("## Reproduction")
    lines.append("")
    lines.append("```")
    lines.append(payload["command_line"])
    lines.append("```")
    lines.append("")

    lines.append("## Generated outputs")
    lines.append("")
    lines.append(
        "These reports are written by "
        "`scripts/validate_phase02_readiness_contracts.py`. They are NOT "
        "hand-edited; their canonical regeneration path is the validator script."
    )
    lines.append("")
    for path in payload["declared_generated_outputs"]:
        lines.append(f"- `{path}`")
    lines.append("")

    lines.append("## Reproducibility note")
    lines.append("")
    lines.append(payload["reproducibility_note"])
    lines.append("")

    lines.append("## Inputs read")
    lines.append("")
    for path in payload["input_files"]:
        lines.append(f"- `{path}`")
    lines.append("")

    lines.append("## Assumptions")
    lines.append("")
    for assumption in payload["assumptions"]:
        lines.append(f"- {assumption}")
    lines.append("")

    lines.append("## Sanity checks")
    lines.append("")
    for sanity in payload["sanity_checks"]:
        lines.append(f"- {sanity}")
    lines.append("")

    lines.append("## Falsifiers")
    lines.append("")
    for falsifier in payload["falsifiers"]:
        lines.append(f"- {falsifier}")
    lines.append("")

    lines.append("## Checks summary")
    lines.append("")
    lines.append("| # | Check | Verdict | Details |")
    lines.append("|---|---|---|---|")
    for check in payload["checks"]:
        details = check["details"].replace("|", "\\|")
        ck_name = check["name"].replace("|", "\\|")
        prefix = check["name"].split(".", 1)[0]
        lines.append(f"| {prefix} | {ck_name} | {check['verdict']} | {details} |")
    lines.append("")

    if payload["blockers"]:
        lines.append("## Blockers")
        lines.append("")
        for blocker in payload["blockers"]:
            lines.append(
                f"- **[{blocker['check']}]** `{blocker['location']}` — "
                f"{blocker['description']}"
            )
        lines.append("")
    if payload["warnings"]:
        lines.append("## Warnings")
        lines.append("")
        for warning in payload["warnings"]:
            lines.append(
                f"- **[{warning['check']}]** `{warning['location']}` — "
                f"{warning['description']}"
            )
        lines.append("")
    if payload["notes"]:
        lines.append("## Notes")
        lines.append("")
        for note in payload["notes"]:
            lines.append(
                f"- **[{note['check']}]** `{note['location']}` — "
                f"{note['description']}"
            )
        lines.append("")

    lines.append("## Per-check evidence")
    lines.append("")
    for check in payload["checks"]:
        lines.append(f"### {check['name']}")
        lines.append("")
        if check["evidence"]:
            for entry in check["evidence"]:
                lines.append(f"- {entry}")
        else:
            lines.append("- (no evidence collected)")
        lines.append("")
    return "\n".join(lines) + "\n"


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(payload), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 02 readiness contracts validator (T05).",
    )
    parser.add_argument(
        "--base",
        default="master",
        help="Base ref for git diff (default: master).",
    )
    parser.add_argument(
        "--out-json",
        default="reports/specs/02_04_cross_spec_consistency_report.json",
        help="Output path for JSON report (default: reports/specs/02_04_*.json).",
    )
    parser.add_argument(
        "--out-md",
        default="reports/specs/02_04_cross_spec_consistency_report.md",
        help="Output path for Markdown report (default: reports/specs/02_04_*.md).",
    )
    parser.add_argument(
        "--run-date",
        required=True,
        help="ISO date for the run (e.g., 2026-05-05).",
    )
    return parser.parse_args(argv)


def build_context(args: argparse.Namespace) -> ValidatorContext:
    head_sha = run_git("rev-parse", "HEAD")
    branch = run_git("rev-parse", "--abbrev-ref", "HEAD")
    diff_files_raw = run_git("diff", "--name-only", f"{args.base}..HEAD")
    diff_files = [line for line in diff_files_raw.splitlines() if line.strip()]
    diff_stat = run_git("diff", "--stat", f"{args.base}..HEAD")
    quoted_args = " ".join(
        shlex.quote(part)
        for part in [
            "scripts/validate_phase02_readiness_contracts.py",
            "--base",
            args.base,
            "--out-json",
            args.out_json,
            "--out-md",
            args.out_md,
            "--run-date",
            args.run_date,
        ]
    )
    # Record the repo-standard reproduction command (per CLAUDE.md commands table)
    # rather than a bare `python3 ...` invocation. The shell prefix is intentionally
    # unquoted so the recorded string is directly executable in zsh.
    command_line = (
        "source .venv/bin/activate && poetry run python " + quoted_args
    )
    return ValidatorContext(
        base_ref=args.base,
        head_sha=head_sha,
        branch=branch,
        run_date=args.run_date,
        command_line=command_line,
        diff_files=sorted(diff_files),
        diff_stat=diff_stat,
    )


def run_all_checks(ctx: ValidatorContext) -> list[Check]:
    return [
        check_pr_file_scope(ctx),
        check_required_phrases(),
        check_forbidden_substrings(),
        check_non_supersession(),
        check_tracker_csv(),
        check_aoe2_source_labels(),
        check_temporal_leakage_rules(),
        check_cold_start_gates(),
        check_cross_02_03_completeness(),
    ]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ctx = build_context(args)
    checks = run_all_checks(ctx)
    payload = build_report_payload(ctx, checks)

    out_json = REPO_ROOT / args.out_json
    out_md = REPO_ROOT / args.out_md
    write_json(payload, out_json)
    write_markdown(payload, out_md)

    print(f"verdict: {payload['verdict']}")
    print(f"blockers: {len(payload['blockers'])}")
    print(f"warnings: {len(payload['warnings'])}")
    print(f"notes: {len(payload['notes'])}")
    print(f"json: {args.out_json}")
    print(f"md: {args.out_md}")

    return 1 if payload["verdict"] == "BLOCKED" else 0


if __name__ == "__main__":
    sys.exit(main())
