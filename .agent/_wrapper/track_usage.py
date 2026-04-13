#!/usr/bin/env python3
"""track_usage.py -- invoke a Spacetime Lab .agent/workflow via a local agent
runtime (claude CLI or aider) and log token usage + timing to a durable
per-run directory.

Usage:
    # Claude Code CLI (cloud model, tokens cost $$)
    python .agent/_wrapper/track_usage.py <workflow_slug>

    # Aider on local Ollama (zero-cloud inference)
    python .agent/_wrapper/track_usage.py <workflow_slug> \\
        --executor aider \\
        --model ollama/qwen2.5-coder:7b \\
        --repo-path C:/path/to/target/project

Writes (always under spacetime-lab/.agent/runs/):
    <RUN_ID>/
        workflow.md     -- snapshot of the workflow prompt used
        output.txt      -- agent stdout
        usage.log       -- agent stderr
        meta.json       -- workflow, start/end, exit code, token usage
    _summary.jsonl
        one line per run

No external deps: Python 3.10+ only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
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


# ---------------------------------------------------------------------------
# Claude CLI support (existing, preserved verbatim)
# ---------------------------------------------------------------------------


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


def extract_claude_usage(output_path: Path) -> dict[str, Any]:
    """Defensive usage extraction: supports several claude-CLI JSON shapes."""
    if not output_path.exists() or output_path.stat().st_size == 0:
        return {}
    try:
        obj = json.loads(output_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {
        "executor": "claude",
        "input_tokens": pick(
            obj,
            [["usage", "input_tokens"], ["message", "usage", "input_tokens"], ["input_tokens"]],
        ),
        "output_tokens": pick(
            obj,
            [["usage", "output_tokens"], ["message", "usage", "output_tokens"], ["output_tokens"]],
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
        "total_cost_usd": pick(obj, [["total_cost_usd"], ["cost_usd"]]),
        "stop_reason": pick(obj, [["stop_reason"], ["message", "stop_reason"]]),
    }


def run_claude(prompt_text: str, run_dir: Path, extra_args: list[str]) -> int:
    """Run the Claude CLI in headless mode; return exit code."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        print("claude CLI not found on PATH", file=sys.stderr)
        return 2
    cmd = [
        claude_bin,
        "--headless",
        "--output-format",
        "json",
        "--prompt",
        prompt_text,
    ] + list(extra_args)
    with (
        (run_dir / "output.txt").open("wb") as out_f,
        (run_dir / "usage.log").open("wb") as err_f,
    ):
        proc = subprocess.run(cmd, stdout=out_f, stderr=err_f, check=False)
    return proc.returncode


# ---------------------------------------------------------------------------
# Aider + local Ollama support (new in this revision)
# ---------------------------------------------------------------------------


# Aider prints token counts in two styles:
#   Tokens: 1,234 sent, 56 received
#   Tokens: 1.9k sent, 107 received
# We accept both, treating the 'k' suffix as * 1000.
_AIDER_TOKEN_RE = re.compile(
    r"Tokens:\s*([\d.,]+)(k?)\s*sent,\s*([\d.,]+)(k?)\s*received",
    re.IGNORECASE,
)


def _parse_count(s: str, suffix: str) -> int:
    s = s.replace(",", "")
    try:
        v = float(s)
    except ValueError:
        return 0
    if suffix and suffix.lower() == "k":
        v *= 1000
    return int(round(v))


def extract_aider_usage(output_path: Path, model: str) -> dict[str, Any]:
    """Parse 'Tokens: N sent, M received.' lines from aider stdout.

    Aider may emit multiple such lines if the conversation has several
    turns.  We sum them all so the total is the real work done.
    """
    if not output_path.exists() or output_path.stat().st_size == 0:
        return {"executor": "aider", "model": model}
    try:
        text = output_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"executor": "aider", "model": model}

    total_in, total_out, turns = 0, 0, 0
    for m in _AIDER_TOKEN_RE.finditer(text):
        total_in += _parse_count(m.group(1), m.group(2))
        total_out += _parse_count(m.group(3), m.group(4))
        turns += 1

    return {
        "executor": "aider",
        "model": model,
        "input_tokens": total_in,
        "output_tokens": total_out,
        "cache_creation_tokens": 0,
        "cache_read_tokens": 0,
        "total_cost_usd": 0.0,  # local inference = free
        "turns": turns,
        "stop_reason": None,
    }


def run_aider(
    prompt_text: str,
    run_dir: Path,
    model: str,
    repo_path: Path,
    extra_args: list[str],
) -> int:
    """Run aider non-interactively with the given workflow as a single message."""
    aider_invocations = [
        ["aider"],                       # if on PATH
        [sys.executable, "-m", "aider"], # fallback, always works
    ]
    # Write the prompt to a temp file aider reads via --message-file
    prompt_file = run_dir / "prompt.md"
    prompt_file.write_text(prompt_text, encoding="utf-8")

    # Baseline args for autonomous execution.  Choices explained:
    #   --yes, --no-check-update, --no-show-release-notes: no interactive UI
    #   --no-stream, --no-analytics:                       clean stdout, no
    #                                                       telemetry to aider's
    #                                                       servers
    #   --no-auto-lint, --no-auto-test:                    aider wouldn't know
    #                                                       how to lint/test this
    #                                                       arbitrary project; we
    #                                                       control those steps
    #                                                       externally
    #   --no-detect-urls:                                  the workflow .md may
    #                                                       contain URLs as
    #                                                       documentation (CDP
    #                                                       endpoints, Vercel
    #                                                       dashboards) - we do
    #                                                       NOT want aider to
    #                                                       open them as context
    #   --map-tokens 0:                                    disable repo-map
    #                                                       (re-enable per-run by
    #                                                       passing --map-tokens
    #                                                       <N> via extra args)
    #   --no-gitignore:                                    skip the
    #                                                       gitignore-writing
    #                                                       prompt; our wrappers
    #                                                       keep .aider* out of
    #                                                       _summary.jsonl
    #                                                       indirectly
    base_args = [
        "--yes",
        "--no-check-update",
        "--no-show-release-notes",
        "--no-stream",
        "--no-analytics",
        "--no-auto-lint",
        "--no-auto-test",
        "--no-detect-urls",
        "--no-gitignore",
        "--map-tokens", "0",
        "--model", model,
        "--message-file", str(prompt_file),
    ]

    env = {**os.environ, "OLLAMA_API_BASE": os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")}

    last_err: Exception | None = None
    for inv in aider_invocations:
        cmd = inv + base_args + list(extra_args)
        try:
            with (
                (run_dir / "output.txt").open("wb") as out_f,
                (run_dir / "usage.log").open("wb") as err_f,
            ):
                proc = subprocess.run(
                    cmd,
                    stdout=out_f,
                    stderr=err_f,
                    cwd=str(repo_path),
                    env=env,
                    check=False,
                )
            return proc.returncode
        except FileNotFoundError as e:
            last_err = e
            continue
    print(f"aider not found via any invocation: {last_err}", file=sys.stderr)
    return 2


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", help="workflow slug (filename without .md)")
    parser.add_argument(
        "--executor",
        choices=["claude", "aider"],
        default="claude",
        help="which agent runtime to invoke (default: claude)",
    )
    parser.add_argument(
        "--model",
        default="ollama/qwen2.5-coder:7b",
        help="model string (aider only; default: ollama/qwen2.5-coder:7b)",
    )
    parser.add_argument(
        "--repo-path",
        default=str(REPO_ROOT),
        help="target repository for aider to operate on "
        "(default: spacetime-lab itself)",
    )
    parser.add_argument(
        "--context-var",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Substitute {{KEY}} placeholders in the workflow prompt with "
            "VALUE before sending to the agent.  Repeatable."
        ),
    )
    parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="extra args passed through to the executor",
    )
    args = parser.parse_args()

    wf_file = WORKFLOWS_DIR / f"{args.workflow}.md"
    if not wf_file.exists():
        print(f"workflow not found: {wf_file}", file=sys.stderr)
        return 2

    now = dt.datetime.now(dt.timezone.utc)
    run_id = now.strftime("%Y%m%dT%H%M%S") + f"_{args.workflow}_{args.executor}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Snapshot the workflow prompt used
    shutil.copy2(wf_file, run_dir / "workflow.md")

    prompt_text = wf_file.read_text(encoding="utf-8")

    # Apply --context-var substitutions: {{KEY}} -> VALUE.
    for pair in args.context_var:
        if "=" not in pair:
            print(f"--context-var expects KEY=VALUE, got: {pair!r}",
                  file=sys.stderr)
            return 2
        key, _, value = pair.partition("=")
        prompt_text = prompt_text.replace("{{" + key + "}}", value)

    # Snapshot the (substituted) prompt the agent actually saw
    (run_dir / "effective-prompt.md").write_text(prompt_text, encoding="utf-8")

    start = now

    # Dispatch to the chosen executor
    extra = [a for a in (args.extra or []) if a != "--"]
    if args.executor == "claude":
        exit_code = run_claude(prompt_text, run_dir, extra)
        usage = extract_claude_usage(run_dir / "output.txt")
    else:  # aider
        exit_code = run_aider(
            prompt_text,
            run_dir,
            model=args.model,
            repo_path=Path(args.repo_path),
            extra_args=extra,
        )
        usage = extract_aider_usage(run_dir / "output.txt", model=args.model)

    end = dt.datetime.now(dt.timezone.utc)
    duration_s = int((end - start).total_seconds())

    meta: dict[str, Any] = {
        "run_id": run_id,
        "workflow": args.workflow,
        "executor": args.executor,
        "model": args.model if args.executor == "aider" else None,
        "repo_path": args.repo_path if args.executor == "aider" else None,
        "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_s": duration_s,
        "exit_code": exit_code,
        "usage": usage,
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    RUNS_DIR.mkdir(exist_ok=True)
    with SUMMARY_FILE.open("a", encoding="utf-8") as summary_f:
        summary_f.write(json.dumps(meta) + "\n")

    def fmt(v: Any) -> str:
        return str(v) if v is not None else "-"

    print(f"Run {run_id}")
    print(f"  workflow:  {args.workflow}")
    print(f"  executor:  {args.executor}")
    if args.executor == "aider":
        print(f"  model:     {args.model}")
        print(f"  repo:      {args.repo_path}")
    print(f"  exit_code: {exit_code}")
    print(f"  duration:  {duration_s}s")
    print(
        f"  tokens:    in={fmt(usage.get('input_tokens'))} "
        f"out={fmt(usage.get('output_tokens'))}"
    )
    if usage.get("turns") is not None:
        print(f"  turns:     {usage['turns']}")
    cost = usage.get("total_cost_usd")
    if cost is not None:
        print(f"  cost:      ${cost}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
