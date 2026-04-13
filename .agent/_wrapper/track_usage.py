#!/usr/bin/env python3
"""track_usage.py — invoke a Spacetime Lab .agent/workflow via the claude CLI
and log token usage + timing to a durable per-run directory.

Usage:
    python .agent/_wrapper/track_usage.py <workflow_slug> [extra claude args...]

Writes:
    .agent/runs/<RUN_ID>/
        workflow.md     -- snapshot of the workflow prompt used
        output.json     -- claude --output-format=json full response
        usage.log       -- claude stderr (verbose tool calls + usage)
        meta.json       -- workflow, start/end, exit code, token usage
    .agent/runs/_summary.jsonl
        one line per run with aggregated fields

No external deps: Python 3.10+ only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AGENT_DIR = REPO_ROOT / ".agent"
RUNS_DIR = AGENT_DIR / "runs"
WORKFLOWS_DIR = AGENT_DIR / "workflows"
SUMMARY_FILE = RUNS_DIR / "_summary.jsonl"


def pick(obj: Any, paths: list[list[str]]) -> Any:
    """Return the first non-None value found at any of the given paths."""
    for path in paths:
        cur: Any = obj
        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                cur = None
                break
            cur = cur[key]
        if cur is not None:
            return cur
    return None


def extract_usage(output_json: Path) -> dict[str, Any]:
    """Defensive usage extraction: supports several claude-CLI JSON shapes."""
    if not output_json.exists() or output_json.stat().st_size == 0:
        return {}
    try:
        obj = json.loads(output_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {
        "input_tokens": pick(
            obj,
            [
                ["usage", "input_tokens"],
                ["message", "usage", "input_tokens"],
                ["input_tokens"],
            ],
        ),
        "output_tokens": pick(
            obj,
            [
                ["usage", "output_tokens"],
                ["message", "usage", "output_tokens"],
                ["output_tokens"],
            ],
        ),
        "cache_creation_tokens": pick(
            obj,
            [
                ["usage", "cache_creation_input_tokens"],
                ["message", "usage", "cache_creation_input_tokens"],
                ["cache_creation_tokens"],
            ],
        ),
        "cache_read_tokens": pick(
            obj,
            [
                ["usage", "cache_read_input_tokens"],
                ["message", "usage", "cache_read_input_tokens"],
                ["cache_read_tokens"],
            ],
        ),
        "total_cost_usd": pick(
            obj, [["total_cost_usd"], ["cost_usd"]]
        ),
        "stop_reason": pick(
            obj, [["stop_reason"], ["message", "stop_reason"]]
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", help="workflow slug (filename without .md)")
    parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="extra args passed through to claude CLI",
    )
    args = parser.parse_args()

    wf_file = WORKFLOWS_DIR / f"{args.workflow}.md"
    if not wf_file.exists():
        print(f"workflow not found: {wf_file}", file=sys.stderr)
        return 2

    claude_bin = shutil.which("claude")
    if not claude_bin:
        print("claude CLI not found on PATH", file=sys.stderr)
        return 2

    now = dt.datetime.now(dt.timezone.utc)
    run_id = now.strftime("%Y%m%dT%H%M%S") + f"_{args.workflow}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Snapshot the workflow prompt used
    shutil.copy2(wf_file, run_dir / "workflow.md")

    start = now
    prompt_text = wf_file.read_text(encoding="utf-8")

    cmd = [
        claude_bin,
        "--headless",
        "--output-format",
        "json",
        "--prompt",
        prompt_text,
    ] + list(args.extra or [])

    with (
        (run_dir / "output.json").open("wb") as out_f,
        (run_dir / "usage.log").open("wb") as err_f,
    ):
        proc = subprocess.run(cmd, stdout=out_f, stderr=err_f, check=False)

    end = dt.datetime.now(dt.timezone.utc)
    duration_s = int((end - start).total_seconds())
    usage = extract_usage(run_dir / "output.json")

    meta: dict[str, Any] = {
        "run_id": run_id,
        "workflow": args.workflow,
        "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_s": duration_s,
        "exit_code": proc.returncode,
        "usage": usage,
    }

    (run_dir / "meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    RUNS_DIR.mkdir(exist_ok=True)
    with SUMMARY_FILE.open("a", encoding="utf-8") as summary_f:
        summary_f.write(json.dumps(meta) + "\n")

    def fmt(v: Any) -> str:
        return str(v) if v is not None else "-"

    print(f"Run {run_id}")
    print(f"  workflow:  {args.workflow}")
    print(f"  exit_code: {proc.returncode}")
    print(f"  duration:  {duration_s}s")
    print(
        f"  tokens:    in={fmt(usage.get('input_tokens'))} "
        f"out={fmt(usage.get('output_tokens'))} "
        f"cache_read={fmt(usage.get('cache_read_tokens'))} "
        f"cache_creation={fmt(usage.get('cache_creation_tokens'))}"
    )
    cost = usage.get("total_cost_usd")
    if cost is not None:
        print(f"  cost:      ${cost}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
