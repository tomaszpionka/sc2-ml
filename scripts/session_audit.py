#!/usr/bin/env python3
"""Session audit dashboard.

Reads session telemetry (JSONL), subagent audit logs, and PR data (gh CLI)
to produce a markdown report on stdout. Stdlib only.

Usage:
    python scripts/session_audit.py                      # full report
    python scripts/session_audit.py --since 2026-04-09   # filter by date
    python scripts/session_audit.py --pr-range 90-108    # filter by PR range
    python scripts/session_audit.py --format csv          # tab-separated
    python scripts/session_audit.py --verbose             # per-session detail
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JSONL_DIR = os.path.expanduser(
    "~/.claude/projects/"
    "-Users-tomaszpionka-Projects-rts-outcome-prediction"
)
AGENT_LOG = os.path.expanduser(
    "~/Projects/tp-claude-logs/agent-audit.log"
)

# Era boundaries (hardcoded at PR #107)
ERA_BOUNDARIES = [
    (1, 106, "pre-DAG"),
    (107, 107, "DAG impl"),
    (108, 99999, "post-DAG"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def fmt_int(n: int) -> str:
    """Format integer with comma separators."""
    return f"{n:,}"


def parse_iso_timestamp(ts: str) -> datetime:
    """Parse ISO 8601 timestamp with Z suffix."""
    # Handle both 'Z' suffix and '+00:00'
    ts = ts.replace("Z", "+00:00")
    # Python 3.10 doesn't handle fractional seconds well with fromisoformat
    # on some formats, so strip timezone for date extraction
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        # Fallback: strip fractional seconds
        base = ts.split(".")[0]
        return datetime.fromisoformat(base)


def date_str(ts: str) -> str:
    """Extract YYYY-MM-DD from an ISO timestamp."""
    return parse_iso_timestamp(ts).strftime("%Y-%m-%d")


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render a markdown table."""
    if not rows:
        return "(no data)\n"
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))
    hdr = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)) + " |"
    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    lines = [hdr, sep]
    for row in rows:
        padded = []
        for i, w in enumerate(widths):
            cell = row[i] if i < len(row) else ""
            padded.append(cell.ljust(w))
        lines.append("| " + " | ".join(padded) + " |")
    return "\n".join(lines) + "\n"


def tsv_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render a tab-separated table."""
    lines = ["\t".join(headers)]
    for row in rows:
        lines.append("\t".join(row))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Data loading: Session JSONLs
# ---------------------------------------------------------------------------


def load_session_records(
    since: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Load assistant records from session JSONL files.

    Returns dict keyed by sessionId, values are lists of deduplicated
    assistant records.

    CRITICAL: Deduplicates by record["message"]["id"] (format: msg_01DPxX...).
    The JSONL emits 3-4 records per API response with DIFFERENT record-level
    "uuid" values but the SAME "message.id". Using "uuid" would overcount
    tokens 3-4x.
    """
    pattern = os.path.join(JSONL_DIR, "*.jsonl")
    files = glob.glob(pattern)
    if not files:
        return {}

    sessions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_msg_ids: set[str] = set()

    for fpath in files:
        try:
            with open(fpath, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Only assistant records with usage data
                    if rec.get("type") != "assistant":
                        continue
                    msg = rec.get("message", {})
                    if not isinstance(msg, dict):
                        continue
                    if "usage" not in msg:
                        continue

                    # Deduplicate by message.id
                    msg_id = msg.get("id", "")
                    if not msg_id or msg_id in seen_msg_ids:
                        continue
                    seen_msg_ids.add(msg_id)

                    # Date filter
                    ts = rec.get("timestamp", "")
                    if since and ts:
                        rec_date = date_str(ts)
                        if rec_date < since:
                            continue

                    session_id = rec.get("sessionId", "unknown")
                    sessions[session_id].append(rec)
        except (OSError, PermissionError):
            continue

    return dict(sessions)


# ---------------------------------------------------------------------------
# Data loading: Agent audit log
# ---------------------------------------------------------------------------


def load_agent_log(
    since: str | None = None,
) -> list[dict[str, str]]:
    """Parse the agent audit log into structured events.

    Format: [YYYY-MM-DD HH:MM:SS] EventType key=value key=value ...
    """
    if not os.path.isfile(AGENT_LOG):
        return []

    events: list[dict[str, str]] = []
    pattern = re.compile(
        r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+(\S+)\s+(.*)"
    )

    try:
        with open(AGENT_LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                m = pattern.match(line)
                if not m:
                    continue
                ts_str, event_type, kv_str = m.groups()
                rec_date = ts_str[:10]
                if since and rec_date < since:
                    continue

                event: dict[str, str] = {
                    "timestamp": ts_str,
                    "date": rec_date,
                    "event": event_type,
                }
                # Parse key=value pairs
                for kv_match in re.finditer(r"(\w+)=(\S+)", kv_str):
                    event[kv_match.group(1)] = kv_match.group(2)
                events.append(event)
    except (OSError, PermissionError):
        return []

    return events


# ---------------------------------------------------------------------------
# Data loading: PR data from gh CLI
# ---------------------------------------------------------------------------


def load_pr_data(
    pr_range: tuple[int, int] | None = None,
) -> list[dict[str, Any]]:
    """Fetch PR data via gh CLI. Graceful fallback on failure."""
    try:
        result = subprocess.run(
            [
                "gh", "pr", "list",
                "--state", "all",
                "--limit", "200",
                "--json",
                "number,title,headRefName,mergedAt,additions,deletions,state",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        prs = json.loads(result.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return []

    if pr_range:
        lo, hi = pr_range
        prs = [p for p in prs if lo <= p.get("number", 0) <= hi]

    # Sort by PR number
    prs.sort(key=lambda p: p.get("number", 0))
    return prs


# ---------------------------------------------------------------------------
# Section 1: Daily token usage
# ---------------------------------------------------------------------------


def section_daily_tokens(
    sessions: dict[str, list[dict[str, Any]]],
    fmt: str,
) -> str:
    """Daily token usage table from session JSONLs."""
    daily: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "sessions": 0,
            "msgs": 0,
            "input": 0,
            "output": 0,
            "cache_read": 0,
            "cache_create": 0,
        }
    )
    sessions_per_day: dict[str, set[str]] = defaultdict(set)

    for sid, records in sessions.items():
        for rec in records:
            ts = rec.get("timestamp", "")
            if not ts:
                continue
            day = date_str(ts)
            sessions_per_day[day].add(sid)
            usage = rec["message"]["usage"]
            daily[day]["msgs"] += 1
            daily[day]["input"] += usage.get("input_tokens", 0)
            daily[day]["output"] += usage.get("output_tokens", 0)
            daily[day]["cache_read"] += usage.get(
                "cache_read_input_tokens", 0
            )
            daily[day]["cache_create"] += usage.get(
                "cache_creation_input_tokens", 0
            )

    for day, sids in sessions_per_day.items():
        daily[day]["sessions"] = len(sids)

    headers = [
        "Date", "Sessions", "Msgs", "Input", "Output",
        "Cache Read", "Cache Create",
    ]
    rows = []
    totals = {k: 0 for k in ["sessions", "msgs", "input", "output",
                              "cache_read", "cache_create"]}
    for day in sorted(daily):
        d = daily[day]
        rows.append([
            day,
            str(d["sessions"]),
            fmt_int(d["msgs"]),
            fmt_int(d["input"]),
            fmt_int(d["output"]),
            fmt_int(d["cache_read"]),
            fmt_int(d["cache_create"]),
        ])
        for k in totals:
            totals[k] += d[k]

    rows.append([
        "**Total**",
        f"**{totals['sessions']}**",
        f"**{fmt_int(totals['msgs'])}**",
        f"**{fmt_int(totals['input'])}**",
        f"**{fmt_int(totals['output'])}**",
        f"**{fmt_int(totals['cache_read'])}**",
        f"**{fmt_int(totals['cache_create'])}**",
    ])

    if fmt == "csv":
        return "# Daily token usage\n" + tsv_table(headers, rows)
    return "## Daily token usage\n\n" + md_table(headers, rows)


# ---------------------------------------------------------------------------
# Section 2: Daily efficiency
# ---------------------------------------------------------------------------


def section_daily_efficiency(
    sessions: dict[str, list[dict[str, Any]]],
    prs: list[dict[str, Any]],
    fmt: str,
) -> str:
    """Lines changed vs output tokens per day."""
    # Aggregate output tokens per day
    daily_output: dict[str, int] = defaultdict(int)
    daily_sessions: dict[str, set[str]] = defaultdict(set)
    for sid, records in sessions.items():
        for rec in records:
            ts = rec.get("timestamp", "")
            if not ts:
                continue
            day = date_str(ts)
            daily_output[day] += rec["message"]["usage"].get(
                "output_tokens", 0
            )
            daily_sessions[day].add(sid)

    # Aggregate lines changed per day from PRs
    daily_prs: dict[str, dict[str, int]] = defaultdict(
        lambda: {"count": 0, "lines": 0}
    )
    for pr in prs:
        merged = pr.get("mergedAt", "")
        if not merged:
            continue
        day = date_str(merged)
        adds = pr.get("additions", 0)
        dels = pr.get("deletions", 0)
        daily_prs[day]["count"] += 1
        daily_prs[day]["lines"] += adds + dels

    all_days = sorted(set(list(daily_output.keys()) + list(daily_prs.keys())))

    headers = [
        "Date", "PRs", "Lines Changed", "Output Tokens",
        "Lines/K-Out", "Sessions",
    ]
    rows = []
    for day in all_days:
        pr_info = daily_prs.get(day, {"count": 0, "lines": 0})
        out_tok = daily_output.get(day, 0)
        n_sessions = len(daily_sessions.get(day, set()))
        if out_tok > 0:
            ratio = f"{pr_info['lines'] / (out_tok / 1000):.1f}"
        else:
            ratio = "--"
        rows.append([
            day,
            str(pr_info["count"]),
            fmt_int(pr_info["lines"]),
            fmt_int(out_tok) if out_tok > 0 else "--",
            ratio,
            str(n_sessions) if n_sessions > 0 else "(no data)",
        ])

    if fmt == "csv":
        return "# Daily efficiency\n" + tsv_table(headers, rows)
    return "## Daily efficiency\n\n" + md_table(headers, rows)


# ---------------------------------------------------------------------------
# Section 3: Model usage
# ---------------------------------------------------------------------------


def section_model_usage(
    sessions: dict[str, list[dict[str, Any]]],
    fmt: str,
) -> str:
    """Breakdown by primary session model."""
    model_stats: dict[str, dict[str, int]] = defaultdict(
        lambda: {"sessions": 0, "msgs": 0, "output": 0}
    )
    # Determine primary model per session (most messages)
    for sid, records in sessions.items():
        model_counts: dict[str, int] = defaultdict(int)
        for rec in records:
            model = rec.get("message", {}).get("model", "unknown")
            model_counts[model] += 1
        if not model_counts:
            continue
        primary_model = max(model_counts, key=model_counts.get)  # type: ignore[arg-type]
        model_stats[primary_model]["sessions"] += 1
        for rec in records:
            model_stats[primary_model]["msgs"] += 1
            model_stats[primary_model]["output"] += (
                rec["message"]["usage"].get("output_tokens", 0)
            )

    total_output = sum(v["output"] for v in model_stats.values())

    headers = ["Model", "Sessions", "Messages", "Output", "% of Output"]
    rows = []
    for model in sorted(
        model_stats, key=lambda m: model_stats[m]["output"], reverse=True
    ):
        s = model_stats[model]
        pct = (s["output"] / total_output * 100) if total_output > 0 else 0
        rows.append([
            model,
            str(s["sessions"]),
            fmt_int(s["msgs"]),
            fmt_int(s["output"]),
            f"{pct:.1f}%",
        ])

    if fmt == "csv":
        return "# Model usage\n" + tsv_table(headers, rows)
    return "## Model usage\n\n" + md_table(headers, rows)


# ---------------------------------------------------------------------------
# Section 4: PR history
# ---------------------------------------------------------------------------


def section_pr_history(
    prs: list[dict[str, Any]],
    fmt: str,
) -> str:
    """Full PR table from gh API."""
    if not prs:
        return (
            "## PR history\n\n"
            "> Warning: no PR data available "
            "(gh CLI failed or returned no results)\n"
        )

    headers = ["PR", "Branch", "+Lines", "-Lines", "Total", "Merged"]
    rows = []
    for pr in prs:
        num = pr.get("number", 0)
        branch = pr.get("headRefName", "")
        adds = pr.get("additions", 0)
        dels = pr.get("deletions", 0)
        merged = pr.get("mergedAt", "")
        merged_date = date_str(merged) if merged else pr.get("state", "open")
        rows.append([
            f"#{num}",
            branch,
            fmt_int(adds),
            fmt_int(dels),
            fmt_int(adds + dels),
            merged_date,
        ])

    if fmt == "csv":
        return "# PR history\n" + tsv_table(headers, rows)
    return "## PR history\n\n" + md_table(headers, rows)


# ---------------------------------------------------------------------------
# Section 5: Era analysis
# ---------------------------------------------------------------------------


def section_era_analysis(
    prs: list[dict[str, Any]],
    fmt: str,
) -> str:
    """Era analysis with hardcoded boundary at PR #107."""
    era_stats: dict[str, dict[str, Any]] = {}
    for lo, hi, name in ERA_BOUNDARIES:
        era_stats[name] = {
            "count": 0,
            "lines": 0,
            "dates": [],
        }

    for pr in prs:
        num = pr.get("number", 0)
        adds = pr.get("additions", 0)
        dels = pr.get("deletions", 0)
        merged = pr.get("mergedAt", "")
        for lo, hi, name in ERA_BOUNDARIES:
            if lo <= num <= hi:
                era_stats[name]["count"] += 1
                era_stats[name]["lines"] += adds + dels
                if merged:
                    era_stats[name]["dates"].append(date_str(merged))
                break

    headers = ["Era", "PRs", "Lines", "Avg Lines/PR", "Dates"]
    rows = []
    for _lo, _hi, name in ERA_BOUNDARIES:
        s = era_stats[name]
        avg = s["lines"] // s["count"] if s["count"] > 0 else 0
        dates = sorted(set(s["dates"]))
        date_range = (
            f"{dates[0]} -- {dates[-1]}" if len(dates) > 1
            else dates[0] if dates else "--"
        )
        rows.append([
            name,
            str(s["count"]),
            fmt_int(s["lines"]),
            fmt_int(avg),
            date_range,
        ])

    if fmt == "csv":
        return "# Era analysis\n" + tsv_table(headers, rows)
    return "## Era analysis\n\n" + md_table(headers, rows)


# ---------------------------------------------------------------------------
# Section 6: Subagent analysis
# ---------------------------------------------------------------------------


def section_subagent_analysis(
    events: list[dict[str, str]],
    fmt: str,
) -> str:
    """Subagent token economics from agent audit log."""
    if not events:
        return (
            "## Subagent analysis\n\n"
            "> No subagent data available "
            f"({AGENT_LOG} not found or empty)\n"
        )

    # Build agent type stats from SubagentStop events
    type_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "count": 0,
            "in": 0,
            "out": 0,
            "cache_read": 0,
            "durations": [],
        }
    )

    # Track start times for duration calculation
    start_times: dict[str, str] = {}  # agent_id -> timestamp

    for ev in events:
        event_type = ev.get("event", "")
        agent_id = ev.get("agent", "")
        agent_type = ev.get("type", "unknown")

        if event_type == "SubagentStart" and agent_id:
            start_times[agent_id] = ev["timestamp"]

        elif event_type == "SubagentStop" and agent_id:
            type_stats[agent_type]["count"] += 1

            # Token fields
            in_tok = ev.get("in", "0")
            out_tok = ev.get("out", "0")
            cr_tok = ev.get("cache_read", "0")

            if in_tok != "unavailable":
                type_stats[agent_type]["in"] += int(in_tok)
            if out_tok != "unavailable":
                type_stats[agent_type]["out"] += int(out_tok)
            if cr_tok != "unavailable":
                type_stats[agent_type]["cache_read"] += int(cr_tok)

            # Duration
            if agent_id in start_times:
                try:
                    t_start = datetime.strptime(
                        start_times[agent_id], "%Y-%m-%d %H:%M:%S"
                    )
                    t_stop = datetime.strptime(
                        ev["timestamp"], "%Y-%m-%d %H:%M:%S"
                    )
                    dur_sec = (t_stop - t_start).total_seconds()
                    type_stats[agent_type]["durations"].append(dur_sec)
                except ValueError:
                    pass

    if not type_stats:
        return (
            "## Subagent analysis\n\n"
            "> No SubagentStop events found in the audit log\n"
        )

    # Sort by total output descending
    sorted_types = sorted(
        type_stats.items(), key=lambda kv: kv[1]["out"], reverse=True
    )

    total_out = sum(s["out"] for _, s in sorted_types)

    headers = [
        "Agent Type", "Count", "Total Output", "Avg Output",
        "Avg Duration", "Cache Hit",
    ]
    rows = []
    for atype, s in sorted_types:
        avg_out = s["out"] // s["count"] if s["count"] > 0 else 0
        durations = s["durations"]
        if durations:
            avg_dur = sum(durations) / len(durations)
            dur_str = f"{avg_dur / 60:.1f} min"
        else:
            dur_str = "--"
        total_input = s["in"] + s["cache_read"]
        if total_input > 0:
            cache_pct = s["cache_read"] / total_input * 100
            cache_str = f"{cache_pct:.1f}%"
        else:
            cache_str = "--"
        rows.append([
            atype,
            str(s["count"]),
            fmt_int(s["out"]),
            fmt_int(avg_out),
            dur_str,
            cache_str,
        ])

    if fmt == "csv":
        return "# Subagent analysis\n" + tsv_table(headers, rows)

    output = "## Subagent analysis\n\n"
    output += "### Agent type token economics\n\n"
    output += md_table(headers, rows) + "\n"

    # Token share bar chart
    if total_out > 0:
        output += "### Token share by agent type\n\n```\n"
        max_bar = 40
        for atype, s in sorted_types:
            pct = s["out"] / total_out * 100
            bar_len = int(pct / 100 * max_bar)
            bar = "\u2588" * bar_len
            output += f"{atype:<25} {bar:<{max_bar}}  {pct:4.1f}%  ({fmt_int(s['out'])})\n"
        output += "```\n"

    return output


# ---------------------------------------------------------------------------
# Section 7: Session detail (--verbose only)
# ---------------------------------------------------------------------------


def section_session_detail(
    sessions: dict[str, list[dict[str, Any]]],
    fmt: str,
) -> str:
    """Per-session breakdown (only with --verbose)."""
    headers = [
        "Session", "Date", "Model", "Msgs", "Input", "Output",
        "Cache Read", "Cache Create",
    ]
    rows = []

    session_summaries: list[tuple[str, str, str, int, int, int, int, int]] = []
    for sid, records in sessions.items():
        if not records:
            continue
        # Primary model
        model_counts: dict[str, int] = defaultdict(int)
        total_in = 0
        total_out = 0
        total_cr = 0
        total_cc = 0
        earliest_ts = ""
        for rec in records:
            model = rec.get("message", {}).get("model", "unknown")
            model_counts[model] += 1
            usage = rec["message"]["usage"]
            total_in += usage.get("input_tokens", 0)
            total_out += usage.get("output_tokens", 0)
            total_cr += usage.get("cache_read_input_tokens", 0)
            total_cc += usage.get("cache_creation_input_tokens", 0)
            ts = rec.get("timestamp", "")
            if not earliest_ts or (ts and ts < earliest_ts):
                earliest_ts = ts
        primary_model = max(model_counts, key=model_counts.get)  # type: ignore[arg-type]
        day = date_str(earliest_ts) if earliest_ts else "--"
        session_summaries.append((
            sid[:12], day, primary_model, len(records),
            total_in, total_out, total_cr, total_cc,
        ))

    # Sort by date then session ID
    session_summaries.sort(key=lambda x: (x[1], x[0]))

    for s in session_summaries:
        rows.append([
            s[0],
            s[1],
            s[2],
            str(s[3]),
            fmt_int(s[4]),
            fmt_int(s[5]),
            fmt_int(s[6]),
            fmt_int(s[7]),
        ])

    if fmt == "csv":
        return "# Session detail\n" + tsv_table(headers, rows)
    return "## Session detail\n\n" + md_table(headers, rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Session audit dashboard — token economy report",
    )
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Filter data from this date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--pr-range",
        type=str,
        default=None,
        help="Filter PRs by range (e.g. 90-108)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["markdown", "csv"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include per-session detail section",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()

    since: str | None = args.since
    fmt: str = args.format

    # Parse PR range
    pr_range: tuple[int, int] | None = None
    if args.pr_range:
        try:
            parts = args.pr_range.split("-")
            pr_range = (int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            print(
                f"Warning: invalid --pr-range '{args.pr_range}', "
                "expected format: N-M",
                file=sys.stderr,
            )

    # Load data
    sessions = load_session_records(since=since)
    events = load_agent_log(since=since)
    prs = load_pr_data(pr_range=pr_range)

    # Header
    scope_parts = []
    if since:
        scope_parts.append(f"since {since}")
    if pr_range:
        scope_parts.append(f"PRs #{pr_range[0]}-#{pr_range[1]}")
    scope = ", ".join(scope_parts) if scope_parts else "all data"

    if fmt == "markdown":
        print("# Session Audit Dashboard\n")
        print(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"**Scope:** {scope}")
        print(f"**Sessions:** {len(sessions)}")
        total_msgs = sum(len(recs) for recs in sessions.values())
        print(f"**Messages:** {fmt_int(total_msgs)}")
        print()
    else:
        print("# Session Audit Dashboard")
        print(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"# Scope: {scope}")
        print()

    # Sections
    sections = [
        section_daily_tokens(sessions, fmt),
        section_daily_efficiency(sessions, prs, fmt),
        section_model_usage(sessions, fmt),
        section_pr_history(prs, fmt),
        section_era_analysis(prs, fmt),
        section_subagent_analysis(events, fmt),
    ]

    if args.verbose:
        sections.append(section_session_detail(sessions, fmt))

    separator = "\n" if fmt == "csv" else "\n---\n\n"
    print(separator.join(sections))


if __name__ == "__main__":
    main()
