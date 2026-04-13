#!/usr/bin/env python3
"""summarize_runs.py — LLM-free aggregator over .agent/runs/_summary.jsonl.

Usage:
    python .agent/_wrapper/summarize_runs.py              # all time
    python .agent/_wrapper/summarize_runs.py 2026-04      # only April 2026
    python .agent/_wrapper/summarize_runs.py last-7d      # last 7 days
    python .agent/_wrapper/summarize_runs.py last-30d     # last 30 days

Zero tokens consumed.  Pure stdlib.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SUMMARY_FILE = REPO_ROOT / ".agent" / "runs" / "_summary.jsonl"


def parse_filter(raw: str) -> tuple[str, Any]:
    """Return (human_label, predicate).  predicate: dict-entry -> bool."""
    if raw == "all":
        return "ALL TIME", lambda e: True
    m = re.fullmatch(r"last-(\d+)d", raw)
    if m:
        days = int(m.group(1))
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
        cutoff_iso = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
        return f"LAST {days} DAYS (since {cutoff_iso})", (
            lambda e: e.get("start", "") >= cutoff_iso
        )
    if re.fullmatch(r"20\d{2}-[01]\d", raw):
        return raw, lambda e: e.get("start", "").startswith(raw)
    raise SystemExit(f"unrecognised filter: {raw!r} (valid: all | last-Nd | YYYY-MM)")


def safe_int(v: Any) -> int:
    return int(v) if isinstance(v, (int, float)) else 0


def safe_float(v: Any) -> float:
    return float(v) if isinstance(v, (int, float)) else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "filter",
        nargs="?",
        default="all",
        help="all | last-7d | last-30d | YYYY-MM",
    )
    args = parser.parse_args()

    if not SUMMARY_FILE.exists() or SUMMARY_FILE.stat().st_size == 0:
        print(f"no runs recorded yet at {SUMMARY_FILE}", file=sys.stderr)
        return 0

    label, predicate = parse_filter(args.filter)

    entries: list[dict[str, Any]] = []
    with SUMMARY_FILE.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                entries.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
    entries = [e for e in entries if predicate(e)]

    by_wf: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in entries:
        by_wf[e.get("workflow", "?")].append(e)

    rows: list[tuple[str, int, int, int, int, float, int]] = []
    for wf, runs in by_wf.items():
        tin = sum(safe_int(r.get("usage", {}).get("input_tokens")) for r in runs)
        tout = sum(safe_int(r.get("usage", {}).get("output_tokens")) for r in runs)
        tcr = sum(safe_int(r.get("usage", {}).get("cache_read_tokens")) for r in runs)
        tcost = sum(
            safe_float(r.get("usage", {}).get("total_cost_usd")) for r in runs
        )
        hit_rate = int(round(tcr / (tcr + tin) * 100)) if (tcr + tin) > 0 else 0
        rows.append((wf, len(runs), tin, tout, tcr, tcost, hit_rate))
    rows.sort(key=lambda r: -r[1])

    print(f"=== USAGE REPORT  {label} ===")
    print()
    if not rows:
        print("(no runs in this window)")
        return 0

    headers = ("workflow", "runs", "in", "out", "cache_read", "cost_$", "cache_hit_%")
    widths = [
        max(len(str(h)), max(len(str(row[i])) for row in rows))
        for i, h in enumerate(headers)
    ]

    def fmt_row(values: tuple[Any, ...]) -> str:
        parts: list[str] = []
        for i, v in enumerate(values):
            if isinstance(v, float):
                cell = f"{v:.4f}"
            else:
                cell = str(v)
            parts.append(cell.ljust(widths[i]) if i == 0 else cell.rjust(widths[i]))
        return "  ".join(parts)

    print(fmt_row(headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt_row(row))

    print()
    total_cost = sum(r[5] for r in rows)
    total_runs = sum(r[1] for r in rows)
    print(f"Total runs: {total_runs}")
    print(f"Total cost: ${total_cost:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
