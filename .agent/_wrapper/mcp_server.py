#!/usr/bin/env python3
"""mcp_server.py -- Bridge between claude.ai (mobile / web) and Spacetime
Lab dispatch state.

Exposes MCP tools over Streamable-HTTP transport with token-based
auth.  Designed to sit behind a public HTTPS endpoint (Caddy on a VPS)
reachable by claude.ai's backend, tunnelled into the developer's PC
via WireGuard.

Read tools
----------
- get_latest_dispatch() -> str
    The full contents of .agent/runs/LATEST.md.

- list_recent_runs(limit: int = 10) -> list[dict]
    The tail of .agent/runs/_summary.jsonl as parsed entries.

- get_run_artifacts(run_id: str) -> dict
    Full artifacts of a specific run: meta.json, effective-prompt.md,
    workflow.md, and the last 40 lines of output.txt.

Write tools (Phase D)
---------------------
- list_workflows() -> list[dict]
    Enumerate dispatchable workflows under .github/workflows/ with
    their inputs / types / defaults / choices.  Discovery for
    claude.ai before calling trigger_dispatch.

- trigger_dispatch(workflow: str, inputs: dict) -> dict
    Dispatch a workflow via the local `gh` CLI (uses the PC user's
    GitHub auth).  Workflow name is allowlisted against actual files
    in .github/workflows/; inputs are passed as separate argv entries
    to prevent shell injection.  Returns {run_id, url, status}.

- get_run_status(run_id: str) -> dict
    Poll status of a dispatched run.  Returns status / conclusion /
    started_at / updated_at / url.  Pairs with get_run_artifacts for
    the full lifecycle.

Auth
----
Every HTTP request must include the header `X-MCP-Token: <secret>`
matching the MCP_TOKEN environment variable.  The server refuses to
start without MCP_TOKEN set (fail-closed).

Environment
-----------
MCP_TOKEN    (required)  shared secret for request auth.  Set to a long
                         random string; rotate if it leaks.
MCP_BIND     (optional)  host:port to listen on, default 127.0.0.1:8765
MCP_LOG_DIR  (optional)  where to write run logs, default
                         <repo>/.agent/runs/_mcp/

Usage
-----
    export MCP_TOKEN=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    python .agent/_wrapper/mcp_server.py

For the initial MVP we bind to 127.0.0.1 so the server is only reachable
from the local machine.  When the VPS / WireGuard tunnel is online, switch
MCP_BIND to the WireGuard interface IP so the tunnel can forward to us.
"""
from __future__ import annotations

import json
import logging
import os
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUNS_DIR = REPO_ROOT / ".agent" / "runs"
SUMMARY_FILE = RUNS_DIR / "_summary.jsonl"
LATEST_FILE = RUNS_DIR / "LATEST.md"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

# Input-name guard: GitHub Actions accepts [a-z0-9_-], so we reject
# anything outside that to keep `gh workflow run -f k=v` calls
# injection-free regardless of subprocess argv semantics.
_INPUT_NAME_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")
_WORKFLOW_NAME_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")

LOG_DIR = Path(os.environ.get(
    "MCP_LOG_DIR",
    str(RUNS_DIR / "_mcp"),
))
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "server.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("mcp-server")


# ---------------------------------------------------------------------------
# Server + tools
# ---------------------------------------------------------------------------


server = FastMCP("spacetime-lab-dispatch")


@server.tool()
def get_latest_dispatch() -> str:
    """Return the full contents of .agent/runs/LATEST.md, which
    summarises the most recent dispatched workflow.  Call this first
    when you want to know what was just done on the user's PC."""
    log.info("tool: get_latest_dispatch")
    if not LATEST_FILE.exists():
        return "(no dispatches recorded yet)"
    return LATEST_FILE.read_text(encoding="utf-8")


@server.tool()
def list_recent_runs(limit: int = 10) -> list[dict]:
    """Return the most recent N dispatch log entries from
    .agent/runs/_summary.jsonl.  Each entry is a dict with run_id,
    workflow, start, end, exit_code, usage, and workflow-specific
    fields.  Useful for 'what did I trigger this week' queries."""
    log.info("tool: list_recent_runs limit=%d", limit)
    if not SUMMARY_FILE.exists():
        return []
    entries: list[dict] = []
    with SUMMARY_FILE.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                entries.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
    if limit <= 0:
        return []
    return entries[-limit:]


@server.tool()
def get_run_artifacts(run_id: str) -> dict:
    """Return the full artifacts of a specific dispatch run.

    For a given run_id prefix (e.g., '20260413T134519Z_bootstrap'),
    walks .agent/runs/<run_id>* and returns meta.json, the effective
    prompt the agent received, the original workflow.md, and the last
    40 lines of the agent output.  Use this to dig into a specific run
    after listing recent runs."""
    log.info("tool: get_run_artifacts run_id=%s", run_id)
    result: dict = {"run_id": run_id}

    # Always try the jsonl first.  Prepare-only dispatches (e.g.,
    # claude-dispatch without --executor) log here but do NOT create a
    # per-run directory, so this is the only source for them.
    if SUMMARY_FILE.exists():
        with SUMMARY_FILE.open("r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    entry = json.loads(ln)
                except json.JSONDecodeError:
                    continue
                if entry.get("run_id", "").startswith(run_id):
                    result["summary_entry"] = entry
                    break

    matches = sorted(RUNS_DIR.glob(f"{run_id}*"))
    # Filter out files that happen to match (LATEST.md, _summary.jsonl)
    dirs = [p for p in matches if p.is_dir()]
    if not dirs:
        if "summary_entry" not in result:
            result["error"] = (
                f"no run directory or summary entry found for run_id "
                f"prefix '{run_id}'"
            )
        else:
            result["note"] = (
                "summary-only run (prepare-style dispatch); no per-run "
                "artifacts on disk"
            )
        return result

    run_dir = dirs[0]
    result["run_dir"] = str(run_dir.relative_to(REPO_ROOT))
    for name in ("meta.json", "effective-prompt.md", "workflow.md"):
        f = run_dir / name
        if f.exists():
            try:
                result[name] = f.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                result[f"{name}_error"] = str(exc)
    output = run_dir / "output.txt"
    if output.exists():
        try:
            lines = output.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
            result["output_tail"] = "\n".join(lines[-40:])
            result["output_line_count"] = len(lines)
        except OSError as exc:
            result["output_error"] = str(exc)
    return result


# ---------------------------------------------------------------------------
# Write tools (Phase D) -- workflow discovery + dispatch + status
# ---------------------------------------------------------------------------


def _resolve_gh() -> str:
    """Locate the `gh` CLI.  Prefer PATH; fall back to the Windows
    default install location so the MCP server works even when the
    runner shell hasn't re-hashed PATH."""
    path_hit = shutil.which("gh")
    if path_hit:
        return path_hit
    fallback = Path(r"C:\Program Files\GitHub CLI\gh.exe")
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(
        "gh CLI not found.  Install it and ensure it's on PATH or at "
        r"C:\Program Files\GitHub CLI\gh.exe"
    )


def _list_workflow_files() -> list[Path]:
    if not WORKFLOWS_DIR.exists():
        return []
    return sorted(
        p for p in WORKFLOWS_DIR.iterdir()
        if p.is_file() and p.suffix in (".yml", ".yaml")
    )


def _parse_workflow(path: Path) -> dict:
    """Extract the dispatchable-input shape from a workflow YAML.

    Returns a summary dict with name (from `name:` or filename),
    filename (without extension, used as the `gh workflow run`
    argument), and inputs (list of {name, description, type, required,
    default, options})."""
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as exc:
        return {
            "filename": path.stem,
            "path": str(path.relative_to(REPO_ROOT)),
            "error": f"parse failed: {exc}",
        }

    name = data.get("name") or path.stem
    # YAML `on:` is parsed to Python True (boolean) because `on` is a
    # YAML 1.1 truthy keyword; fall back accordingly.
    on_block = data.get("on") or data.get(True) or {}
    dispatch_block = (on_block or {}).get("workflow_dispatch") if isinstance(on_block, dict) else None
    inputs_spec = (dispatch_block or {}).get("inputs", {}) if isinstance(dispatch_block, dict) else {}

    inputs = []
    for iname, spec in (inputs_spec or {}).items():
        spec = spec or {}
        entry = {
            "name": iname,
            "description": spec.get("description", ""),
            "type": spec.get("type", "string"),
            "required": bool(spec.get("required", False)),
        }
        if "default" in spec:
            entry["default"] = spec["default"]
        if "options" in spec:
            entry["options"] = spec["options"]
        inputs.append(entry)

    return {
        "name": name,
        "filename": path.stem,
        "path": str(path.relative_to(REPO_ROOT)),
        "dispatchable": dispatch_block is not None,
        "inputs": inputs,
    }


@server.tool()
def list_workflows() -> list[dict]:
    """Enumerate dispatchable workflows.

    Returns every `.github/workflows/*.yml` file in this repo along
    with its name, filename (used as the argument to trigger_dispatch),
    whether it accepts `workflow_dispatch`, and each input's name,
    description, type, required flag, default, and choice options.

    Use this BEFORE calling trigger_dispatch so you know what
    workflows exist and what inputs each accepts."""
    log.info("tool: list_workflows")
    return [_parse_workflow(p) for p in _list_workflow_files()]


@server.tool()
def trigger_dispatch(workflow: str, inputs: dict | None = None, ref: str = "master") -> dict:
    """Dispatch a GitHub workflow on this repo.

    Args:
        workflow: The workflow filename without extension (e.g.
            'bootstrap-new-project').  Must match an existing file
            under .github/workflows/; other names are rejected.
        inputs: Dict of input-name -> value for the workflow's
            dispatchable inputs.  Values are coerced to strings.
            Unknown input names are rejected (caller should consult
            list_workflows first).
        ref: Branch or tag to dispatch from; defaults to 'master'.

    Returns:
        dict with keys {run_id, url, status, dispatched_at} on success,
        or {error: ...} on failure.  After a successful dispatch,
        poll get_run_status(run_id) until status='completed', then
        call get_run_artifacts(run_id) for the result.

    Security: workflow name is allowlisted against actual files;
    inputs are passed as separate argv entries to gh (no shell
    string interpolation) and input names must be [a-zA-Z0-9_-]."""
    log.info("tool: trigger_dispatch workflow=%s inputs=%s ref=%s", workflow, inputs, ref)

    inputs = inputs or {}

    # 1. Validate workflow name + file exists.
    if not _WORKFLOW_NAME_RE.match(workflow):
        return {"error": f"invalid workflow name: {workflow!r}"}
    wf_path = WORKFLOWS_DIR / f"{workflow}.yml"
    if not wf_path.exists():
        wf_path = WORKFLOWS_DIR / f"{workflow}.yaml"
    if not wf_path.exists():
        return {
            "error": f"workflow not found: {workflow!r} (no matching "
                     f".yml/.yaml under .github/workflows/)"
        }

    # 2. Validate inputs against the workflow's declared spec.
    spec = _parse_workflow(wf_path)
    if not spec.get("dispatchable"):
        return {"error": f"workflow {workflow!r} does not accept workflow_dispatch"}
    declared = {i["name"]: i for i in spec.get("inputs", [])}
    for iname in inputs:
        if not _INPUT_NAME_RE.match(iname):
            return {"error": f"invalid input name: {iname!r}"}
        if iname not in declared:
            return {
                "error": f"unknown input {iname!r} for {workflow!r}; "
                         f"declared: {sorted(declared)}"
            }
    missing = [
        n for n, i in declared.items()
        if i.get("required") and n not in inputs and "default" not in i
    ]
    if missing:
        return {"error": f"missing required inputs: {missing}"}

    # 3. Resolve gh + build argv.  Each -f pair is a separate argv entry
    #    so no shell quoting/interpolation happens.
    try:
        gh = _resolve_gh()
    except RuntimeError as exc:
        return {"error": str(exc)}

    argv = [gh, "workflow", "run", wf_path.name, "--ref", ref]
    for k, v in inputs.items():
        argv.extend(["-f", f"{k}={v}"])

    import datetime as dt
    dispatched_at = dt.datetime.now(dt.timezone.utc).isoformat()

    try:
        proc = subprocess.run(
            argv,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"error": "gh workflow run timed out after 30s"}
    except OSError as exc:
        return {"error": f"failed to invoke gh: {exc}"}

    if proc.returncode != 0:
        return {
            "error": "gh workflow run failed",
            "exit_code": proc.returncode,
            "stderr": proc.stderr.strip(),
            "stdout": proc.stdout.strip(),
        }

    # 4. Find the run ID we just queued.  gh doesn't return it directly
    #    so we list recent runs for this workflow and pick the newest
    #    one created after dispatched_at.
    list_proc = subprocess.run(
        [gh, "run", "list", "--workflow", wf_path.name, "--limit", "5",
         "--json", "databaseId,status,createdAt,url,displayTitle"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    run_id: int | None = None
    run_url = ""
    run_status = "queued"
    if list_proc.returncode == 0:
        try:
            runs = json.loads(list_proc.stdout)
            # Pick the run whose createdAt is >= dispatched_at.
            for r in runs:
                if r.get("createdAt", "") >= dispatched_at[:19]:
                    run_id = r.get("databaseId")
                    run_url = r.get("url", "")
                    run_status = r.get("status", "queued")
                    break
        except json.JSONDecodeError:
            pass

    result = {
        "workflow": workflow,
        "ref": ref,
        "inputs": inputs,
        "dispatched_at": dispatched_at,
        "status": run_status,
    }
    if run_id is not None:
        result["run_id"] = run_id
        result["url"] = run_url
    else:
        result["note"] = (
            "dispatched, but run_id not resolvable yet; retry "
            "list_recent_runs or get_run_status in a few seconds"
        )
    return result


@server.tool()
def get_run_status(run_id: int | str) -> dict:
    """Poll the status of a dispatched workflow run.

    Args:
        run_id: The numeric GitHub run ID returned by
            trigger_dispatch.  Strings are accepted and coerced.

    Returns:
        dict with keys {status, conclusion, started_at, updated_at,
        url, display_title, jobs} on success, or {error: ...} on
        failure.  `status` is one of 'queued', 'in_progress',
        'completed'.  `conclusion` is populated when status is
        'completed': 'success', 'failure', 'cancelled', etc.

    Poll this after trigger_dispatch until status='completed', then
    call get_run_artifacts(run_id) with the zero-padded UTC timestamp
    prefix for the full output."""
    log.info("tool: get_run_status run_id=%s", run_id)
    try:
        rid = str(int(run_id))
    except (TypeError, ValueError):
        return {"error": f"invalid run_id: {run_id!r}"}

    try:
        gh = _resolve_gh()
    except RuntimeError as exc:
        return {"error": str(exc)}

    proc = subprocess.run(
        [gh, "run", "view", rid,
         "--json", "status,conclusion,createdAt,updatedAt,url,"
                   "displayTitle,jobs,workflowName"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if proc.returncode != 0:
        return {
            "error": "gh run view failed",
            "exit_code": proc.returncode,
            "stderr": proc.stderr.strip(),
        }
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {"error": f"could not parse gh output: {exc}"}

    # Summarize jobs (status + conclusion only; full steps are verbose).
    jobs = []
    for j in data.get("jobs", []) or []:
        jobs.append({
            "name": j.get("name"),
            "status": j.get("status"),
            "conclusion": j.get("conclusion"),
        })

    return {
        "run_id": int(rid),
        "workflow": data.get("workflowName"),
        "status": data.get("status"),
        "conclusion": data.get("conclusion"),
        "started_at": data.get("createdAt"),
        "updated_at": data.get("updatedAt"),
        "url": data.get("url"),
        "display_title": data.get("displayTitle"),
        "jobs": jobs,
    }


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------


class TokenAuth(BaseHTTPMiddleware):
    """Reject any request that doesn't carry the expected MCP token.

    Token is read from the `X-MCP-Token` header.  Fail-closed: if the
    server's expected token is empty, every request is refused with
    503."""

    def __init__(self, app, expected_token: str) -> None:
        super().__init__(app)
        self.expected = expected_token

    async def dispatch(self, request, call_next):
        if not self.expected:
            log.warning("MCP_TOKEN not configured; rejecting request")
            return JSONResponse(
                {"error": "server not configured"},
                status_code=503,
            )
        provided = request.headers.get("x-mcp-token", "")
        # Constant-time comparison to avoid timing attacks
        if not secrets.compare_digest(provided, self.expected):
            log.info(
                "auth failed from %s path=%s",
                request.client.host if request.client else "?",
                request.url.path,
            )
            return JSONResponse(
                {"error": "unauthorized"},
                status_code=401,
            )
        return await call_next(request)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> int:
    import uvicorn

    token = os.environ.get("MCP_TOKEN", "").strip()
    if not token:
        print(
            "ERROR: MCP_TOKEN env var is required (set to a long random string)",
            file=sys.stderr,
        )
        print(
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"",
            file=sys.stderr,
        )
        return 2

    bind = os.environ.get("MCP_BIND", "127.0.0.1:8765")
    try:
        host, port_str = bind.rsplit(":", 1)
        port = int(port_str)
    except ValueError:
        print(f"ERROR: invalid MCP_BIND={bind}, expected host:port", file=sys.stderr)
        return 2

    log.info("starting MCP server on http://%s:%d", host, port)
    log.info("  token fingerprint: %s...%s", token[:4], token[-4:])
    log.info("  repo root: %s", REPO_ROOT)

    app = server.streamable_http_app()
    app.add_middleware(TokenAuth, expected_token=token)

    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
