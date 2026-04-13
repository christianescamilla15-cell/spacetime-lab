---
description: Inspect deploy status of spacetime-lab, nexusforge, and related projects via Chrome DevTools Protocol on localhost:9222. Reports summary + screenshots without opening visible windows.
---

# Check deploy status via Chrome DevTools Protocol

Uses the already-running Chrome that Antigravity launched on
`localhost:9222`. Does **not** spawn a separate browser. Does **not**
require auth.

## Required

- Antigravity must be running (so port 9222 is alive).
  Sanity check: `curl -s http://localhost:9222/json/version` returns a
  `Browser: Chrome/...` JSON blob.

## Targets checked

By default:

| Project | URL | What to extract |
|---|---|---|
| Spacetime Lab (Vercel) | https://spacetime-lab.vercel.app | `window.performance.timing`, HTTP status, title |
| Spacetime Lab releases | https://github.com/christianescamilla15-cell/spacetime-lab/releases | Latest tag, publish date |
| Spacetime Lab Actions | https://github.com/christianescamilla15-cell/spacetime-lab/actions | Last 5 workflow runs + their conclusion |
| NexusForge | https://nexusforge-two.vercel.app | Status, latest deploy timestamp |
| Render API | https://spacetime-lab-api.onrender.com/health | 200 vs 5xx |

The user can override the target list with `targets: [url1, url2, ...]`
in the invocation.

## Procedure

### 1. Preflight

```bash
# Verify CDP is up
curl -sf http://localhost:9222/json/version > /dev/null || {
  echo "CDP not available. Is Antigravity running?" >&2
  exit 2
}
```

### 2. Open a dedicated tab per target (via Playwright connect_over_cdp)

```python
from playwright.sync_api import sync_playwright

def check(url, timeout_ms=15_000):
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        page = ctx.new_page()             # dedicated tab
        try:
            response = page.goto(url, timeout=timeout_ms)
            status = response.status if response else None
            title = page.title()
            # For GitHub Actions pages, extract last-5 workflow runs
            if "github.com" in url and "/actions" in url:
                rows = page.query_selector_all("a[href*='/actions/runs/']")
                runs = [r.inner_text().splitlines()[0] for r in rows[:5]]
            else:
                runs = None
            shot = page.screenshot(type="png")   # bytes
            return {"url": url, "status": status, "title": title,
                    "runs": runs, "screenshot_bytes": len(shot)}
        finally:
            page.close()                   # don't touch Antigravity's tabs
```

### 3. Summary report

Produce a single text block:

```
=== DEPLOY STATUS 2026-04-13 ===

✓ spacetime-lab.vercel.app         HTTP 200   "Spacetime Lab"
✓ nexusforge-two.vercel.app        HTTP 200   "NexusForge"
⚠ spacetime-lab-api.onrender.com   HTTP 503   (service sleeping; cold-start expected)
✓ GitHub Actions spacetime-lab     last 5 runs all ✓
? GitHub releases                  latest = v2.1.0 (2026-04-12)
```

Use `✓` for 200 + expected title, `⚠` for Render cold-start (503 → retry after 30s),
`✗` for genuine failure (500/connection refused/unreachable), `?` for
ambiguous (no title match).

### 4. Surface issues

- If any target returns `✗`, **stop** and ask the user if they want to
  dig into logs (next workflow: `inspect-deploy-failure.md`).
- If Render returns `⚠` (503), wait 30s and retry once. Mark `✓` if second
  attempt succeeds, `✗` otherwise.

## Do not

- Do not close or navigate tabs that Antigravity already has open. Always
  create a **new** tab via `browser.new_context()` or `ctx.new_page()` and
  close only that tab when done.
- Do not install Chromium (`playwright install chromium`) — we're reusing
  the browser Antigravity already manages. Only `pip install playwright`.
- Do not expose screenshot bytes in the summary report; save them to
  `.agent/runs/<timestamp>/<slug>.png` if the user asks for visual
  evidence.
