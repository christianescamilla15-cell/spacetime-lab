#!/usr/bin/env python3
"""write_latest.py -- render the tail of .agent/runs/_summary.jsonl
as a human+LLM-friendly markdown briefing at .agent/runs/LATEST.md.

Called by every dispatch workflow as its penultimate step (before the
auto-commit), so any new Claude / Antigravity / shell session that
opens the repo can read LATEST.md and know exactly what was just
dispatched -- workflow, inputs, outputs, repo URL, duration, tokens.

No deps: Python 3.10+ stdlib.

Usage:
    python .agent/_wrapper/write_latest.py
        # Defaults: reads last line of _summary.jsonl, writes LATEST.md

    python .agent/_wrapper/write_latest.py --run-id 20260413T134519Z_bootstrap
        # Reads that specific run's meta.json if newer than the jsonl tail.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUNS_DIR = REPO_ROOT / ".agent" / "runs"
SUMMARY_FILE = RUNS_DIR / "_summary.jsonl"
LATEST_FILE = RUNS_DIR / "LATEST.md"


def read_last_jsonl_entry(path: Path) -> dict[str, Any] | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    last: dict[str, Any] | None = None
    with path.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                last = json.loads(ln)
            except json.JSONDecodeError:
                continue
    return last


def read_run_meta(run_id: str) -> dict[str, Any] | None:
    """Read .agent/runs/<run_id>/meta.json if present."""
    for d in RUNS_DIR.glob(f"{run_id}*"):
        meta = d / "meta.json"
        if meta.exists():
            try:
                return json.loads(meta.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
    return None


def tail_lines(path: Path, n: int = 40) -> list[str]:
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    lines = text.splitlines()
    return lines[-n:]


def fmt_scalar(v: Any) -> str:
    if v is None:
        return "_(none)_"
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def render_markdown(entry: dict[str, Any]) -> str:
    """Render a dispatch-log entry into a markdown briefing."""
    run_id = entry.get("run_id", "?")
    wf = entry.get("workflow", "?")
    kind = entry.get("kind") or entry.get("executor") or "dispatch"
    start = entry.get("start", "?")
    end = entry.get("end", start)
    duration = entry.get("duration_s")
    exit_code = entry.get("exit_code")

    lines: list[str] = []
    lines.append("# Latest dispatch")
    lines.append("")
    lines.append(
        "> Auto-generated from `.agent/runs/_summary.jsonl`. Read "
        "this whenever you open a new Claude / Antigravity / shell "
        "session in this repo to pick up where the last dispatch "
        "left off."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    lines.append(f"| Run ID | `{run_id}` |")
    lines.append(f"| Workflow | `{wf}` |")
    lines.append(f"| Kind | `{kind}` |")
    lines.append(f"| Start | `{start}` |")
    lines.append(f"| End | `{end}` |")
    if duration is not None:
        lines.append(f"| Duration | {duration}s |")
    if exit_code is not None:
        lines.append(f"| Exit code | `{exit_code}` |")

    for key, label in [
        ("model", "Model"),
        ("project", "Project"),
        ("stack", "Stack"),
        ("visibility", "Visibility"),
        ("repo_url", "Repo URL"),
        ("repo_path", "Repo path"),
        ("task", "Task"),
    ]:
        if key in entry and entry[key]:
            val = entry[key]
            if key == "repo_url":
                val = f"<{val}>"
            lines.append(f"| {label} | {val} |")

    inputs = entry.get("inputs") or {}
    if isinstance(inputs, dict) and inputs:
        for k, v in inputs.items():
            lines.append(f"| input.{k} | {fmt_scalar(v)} |")

    usage = entry.get("usage") or {}
    if isinstance(usage, dict) and usage:
        lines.append("")
        lines.append("## Usage")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|---|---|")
        for k in (
            "executor", "model", "input_tokens", "output_tokens",
            "cache_read_tokens", "cache_creation_tokens",
            "total_cost_usd", "turns", "stop_reason",
        ):
            if k in usage and usage[k] is not None:
                lines.append(f"| {k} | {fmt_scalar(usage[k])} |")

    run_dir_matches = list(RUNS_DIR.glob(f"{run_id}*"))
    if run_dir_matches:
        run_dir = run_dir_matches[0]
        effective = run_dir / "effective-prompt.md"
        output = run_dir / "output.txt"
        if effective.exists():
            lines.append("")
            lines.append("## Effective prompt")
            lines.append("")
            lines.append("<details><summary>Show</summary>")
            lines.append("")
            lines.append("```markdown")
            lines.append(effective.read_text(encoding="utf-8", errors="replace"))
            lines.append("```")
            lines.append("")
            lines.append("</details>")
        if output.exists():
            tail = tail_lines(output, n=40)
            if tail:
                lines.append("")
                lines.append("## Agent output tail (last 40 lines)")
                lines.append("")
                lines.append("```")
                lines.extend(tail)
                lines.append("```")

    lines.append("")
    lines.append("## How to act on this")
    lines.append("")
    if kind == "bootstrap-new-project":
        repo_url = entry.get("repo_url")
        if repo_url:
            lines.append(
                f"A new repo was created at {repo_url}. If the user "
                "wants to iterate on it, treat the new repo as the "
                "working target. Files scaffolded by a local model may "
                "need a manual review -- small models sometimes emit "
                "whole-edit-format glitches. Check `git log` in the new "
                "repo and clean up any weird artifacts before layering "
                "new work."
            )
    elif kind == "dispatch-prepare":
        lines.append(
            "This was a prepare-only dispatch (0-token). The runner "
            "opened the IDE / dashboards for you; the agent work "
            "happens right here, interactively. Pick up the task "
            "described in the referenced workflow file."
        )
    elif kind == "aider":
        lines.append(
            "Aider ran autonomously with a local Ollama model. Check "
            "the agent output tail above for what happened. If there "
            "are uncommitted changes in the target repo, they are the "
            "most recent state and may need review before further work."
        )
    else:
        lines.append(
            "Generic dispatch. Consult the effective prompt and the "
            "agent output tail above. Ask the user whether to iterate "
            "on this run or start fresh."
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-id",
        default=None,
        help="Specific run_id to render (default: latest jsonl entry).",
    )
    args = parser.parse_args()

    entry = read_last_jsonl_entry(SUMMARY_FILE)
    if args.run_id:
        meta = read_run_meta(args.run_id)
        if meta:
            entry = meta

    if not entry:
        print("no dispatch entries found", file=sys.stderr)
        return 1

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_FILE.write_text(render_markdown(entry), encoding="utf-8")
    print(f"wrote {LATEST_FILE} ({entry.get('run_id', '?')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
