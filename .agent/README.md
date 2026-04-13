# `.agent/` — dispatch infrastructure for Spacetime Lab

Everything needed to trigger work on this repo from a phone, have it run
on a self-hosted runner on Christian's PC, and keep native-tool cost
accounting.

## Layout

```
.agent/
├── rules/              always_on rules injected into every agent session
├── workflows/          pre-written prompts + procedures (one per .md)
├── _wrapper/           Python + PowerShell helpers (setup, tracking)
└── runs/               per-dispatch output logs + aggregated _summary.jsonl
```

## One-time setup

### Option A — non-elevated (Startup-folder auto-start)

Works without admin.  Runner starts at user login via a `.cmd` in the
Windows Startup folder.  Recommended for a personal desktop.

```bash
# bash / git-bash — non-interactive
# 1. download + extract runner
mkdir -p /c/actions-runner && cd /c/actions-runner
curl -L -o actions-runner.zip https://github.com/actions/runner/releases/download/v2.319.1/actions-runner-win-x64-2.319.1.zip
powershell.exe -Command "Expand-Archive actions-runner.zip . -Force"

# 2. register with your registration token from:
#    https://github.com/christianescamilla15-cell/spacetime-lab/settings/actions/runners/new
cmd //c "C:\\actions-runner\\config.cmd --unattended --url https://github.com/christianescamilla15-cell/spacetime-lab --token <TOKEN> --name runner-desktop --labels self-hosted,windows,claude-dispatch --work _work --replace"

# 3. autostart at login
cp "$(dirname $0)/_wrapper/startup/github-actions-runner.cmd" \
   "$APPDATA/Microsoft/Windows/Start Menu/Programs/Startup/"
```

### Option B — elevated (Windows Service)

Slightly more robust (runs before login, proper SCM entry).  Requires
admin.

```powershell
# From an ELEVATED PowerShell prompt
cd C:\Users\DANNY\Desktop\spacetime-lab
.\.agent\_wrapper\setup-runner.ps1 -RegistrationToken <token>
```

### Migrate A → B

If you started with Option A and want to promote to Service:

```powershell
# From an ELEVATED PowerShell prompt
cd C:\Users\DANNY\Desktop\spacetime-lab
.\.agent\_wrapper\migrate-to-service.ps1
```

The migration script reuses the existing registration, so no new token
is needed.  It stops the Startup-folder runner, installs the Windows
Service, and starts it.

## Daily use

### Trigger from phone (GitHub mobile app)

Actions tab → **claude-dispatch** → Run workflow → pick:

- `workflow` — which `.agent/workflows/*.md` to focus on
- `task` — optional free-text context
- `open_ide` — reopen Antigravity focused on the workflow file
- `open_dashboards` — have Chrome tabs waiting with Vercel / Actions / releases

Result: by the time you're back at the PC, the environment is ready.
The agent work itself happens interactively inside Antigravity.

### Trigger from anywhere (`gh` CLI)

```bash
gh workflow run claude-dispatch.yml \
   -f workflow=check-deploys \
   -f task='check deploy status before bed' \
   -f open_ide=false \
   -f open_dashboards=true
```

## Accounting

Each dispatch appends a line to `.agent/runs/_summary.jsonl`.  Session
totals and monthly reports:

```bash
python .agent/_wrapper/summarize_runs.py            # all time
python .agent/_wrapper/summarize_runs.py last-7d    # last week
python .agent/_wrapper/summarize_runs.py 2026-04    # specific month
```

The dispatch itself is 0 tokens (pure shell + CDP).  LLM consumption
happens inside the Antigravity session that follows; `track_usage.py` is
available for standalone `claude` CLI runs (not currently installed on
this PC, so skipped by default).

## What lives where

| File | Role |
|---|---|
| `rules/physics-builder-methodology.md` | always_on: the 4-habit discipline |
| `rules/commit-and-release-style.md` | always_on: commit + release conventions |
| `workflows/ship-patch.md` | 8-step release flow with pause points |
| `workflows/verify-before-code.md` | Formula pinning before implementation |
| `workflows/check-deploys.md` | CDP-based deploy status inspection |
| `_wrapper/track_usage.py` | Optional: wrap a `claude` CLI call + log usage |
| `_wrapper/summarize_runs.py` | Aggregator over `_summary.jsonl` |
| `_wrapper/setup-runner.ps1` | One-time Windows runner install |
| `../.github/workflows/claude-dispatch.yml` | The dispatch workflow triggered from phone |

## Why this architecture

- **Zero cloud functions** — everything local, no cold starts, no billing
- **Zero tokens for dispatch-prepare step** — shell + CDP only
- **Rules cached in system prompt** — 5 min TTL means repeated workflow
  invocations are cheap for the first ~5 min; still reasonable after
- **CDP over vision** — extracting DOM / console via Chrome DevTools
  Protocol is ~100× cheaper than screenshot-and-VLM on the same dashboard
- **Native IDE agent handles reasoning** — Antigravity's session manages
  its own token accounting and context; we don't double-spend

Expected cost based on v1.x sprint usage patterns: **~$0.30/month** for
~30 dispatches/month, versus **~$3-8/month** for a Cloudflare-Worker +
vision-based equivalent.
