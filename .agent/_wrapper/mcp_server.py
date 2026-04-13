#!/usr/bin/env python3
"""mcp_server.py -- Bridge between claude.ai (mobile / web) and Spacetime
Lab dispatch state.

Exposes three read-only MCP tools over Streamable-HTTP transport with
token-based auth.  Designed to sit behind a public HTTPS endpoint
(Caddy on a VPS) reachable by claude.ai's backend, tunnelled into the
developer's PC via WireGuard.

Tools
-----
- get_latest_dispatch() -> str
    The full contents of .agent/runs/LATEST.md.

- list_recent_runs(limit: int = 10) -> list[dict]
    The tail of .agent/runs/_summary.jsonl as parsed entries.

- get_run_artifacts(run_id: str) -> dict
    Full artifacts of a specific run: meta.json, effective-prompt.md,
    workflow.md, and the last 40 lines of output.txt.

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
import secrets
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUNS_DIR = REPO_ROOT / ".agent" / "runs"
SUMMARY_FILE = RUNS_DIR / "_summary.jsonl"
LATEST_FILE = RUNS_DIR / "LATEST.md"

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
