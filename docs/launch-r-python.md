# r/Python launch — engineering-first framing

**Why a separate doc:** r/Physics removed the previous post under the
"AI/LLM-generated" rule.  See `launch-postmortem-2026-04-30.md`.
This post reframes the project as a *scientific Python engineering
project that happens to be about GR*, not a *GR toolkit that happens
to be in Python*.  Different audience, different framing, different
hostile-reader reading.

**Live URLs (verified 2026-04-30):**
- Frontend: https://spacetime-lab.vercel.app
- Backend:  https://spacetime-lab-api.onrender.com
- Repo:     https://github.com/christianescamilla15-cell/spacetime-lab

---

## r/Python

**URL:** https://www.reddit.com/r/Python/submit
**Subreddit rules to verify before posting:**
- r/Python "Showcase" or "Resource" flair required for project posts
- Self-promotion limit: ~10% of contributions, but a single project
  post is fine
- Body must be substantive (rule 4 — no URL-only posts)
- Best window: Tuesday-Thursday, 8-10 AM Pacific = 11 AM-1 PM ET =
  10 AM-12 PM Mexico City

### Flair

```
Showcase
```

### Title (under 300 chars; keep ≤ 100 for visibility)

```
[Showcase] Spacetime Lab — Python package + FastAPI + React for interactive black-hole physics
```

### Body (markdown)

```
**Spacetime Lab** is an open-source scientific Python project I've
been building over the past 6 months.  It started as an excuse to
properly learn FastAPI, React + Three.js, and what a "production
scientific Python codebase" actually looks like end to end.  Six
months later it's a 790-test package + REST API + interactive web
app for general relativity calculations.

**Live demo:** https://spacetime-lab.vercel.app
**Code (MIT):** https://github.com/christianescamilla15-cell/spacetime-lab

## What's in the package

```
spacetime_lab/
  metrics/        # 7 spacetime metric classes (Pydantic-validated config)
  diagrams/       # Penrose diagram renderer (matplotlib SVG output)
  geodesics/      # Symplectic implicit-midpoint integrator
  horizons/       # Closed-form horizon + ISCO solvers
  waves/          # QNM wrapper around Leo Stein's `qnm` package
  entropy/        # Page curve calculation (toy model)
  holography/     # AdS-CFT calculations (BTZ + Cardy)
  utils/
```

Each module is `pip install`-able and has a corresponding REST
endpoint + frontend page.  Same numbers, same conventions,
same test gates everywhere.

## What was actually interesting to build

**Symplectic integrator (`geodesics/`).**  For Boyer-Lindquist
coordinates around a Kerr black hole, `t` and `phi` are cyclic, so
their conjugate momenta `E` (energy) and `L_z` (angular momentum)
are exact constants of motion.  An implicit-midpoint integrator
preserves these to machine precision; explicit RK4 drifts.  The
conservation panel in the geodesic explorer shows `E` and `L_z`
drift = 0 (literally `1e-16` machine epsilon noise) and Carter `Q`
drift growing as `O(h²)` per step, exactly as the symplectic
geometry predicts.  Watching this work in the browser is the
prettiest debug session I've had in months.

**Test gates against canonical references (`tests/`).**  790 pytest
tests, of which roughly 200 are bit-exact closed-form verification
gates against literature values:

* Brown-Henneaux 1986 central charge `c = 3L/(2G)` — gated to 1e-15
* Bardeen-Press-Teukolsky 1972 ISCO closed form — gated to 1e-12
* Strominger 1998 Cardy match for BTZ entropy — gated to 1e-15
* Carter constant drift O(h²) per integrator step — gated to 1.5x
  theoretical bound

If any of these break, CI fails.  This was a discipline I learned
from the `qnm` package and it has caught real bugs (a sign error in
the Kerr discriminant that other test types didn't surface).

**Pydantic v2 validation everywhere.**  `Kerr(M=1, a=0.95)` validates
spin within `[0, M]` at construction.  `KerrNewman(M=1, a=0.6, Q=0.8)`
validates the cosmic-censorship inequality `a² + Q² ≤ M²` (with a
1e-12 float tolerance for the boundary case — a fun bug to track
down because `0.6² + 0.8² = 1.0000000000000002` in IEEE 754).

**Frontend is React + Three.js + KaTeX.**  9 pages, mobile-responsive
via a `useMediaQuery` hook + plain CSS reset.  No CSS framework, no
state management library, just `useState` + a small `lib/api.js`.
The Three.js Kerr scene supports multiple simultaneous trajectories
and click-pick on the equatorial disk to launch a new geodesic from
that point.

## What's deployed

* **Frontend** on Vercel (auto-deploy from master).  Vite bundle
  ~330 KB gzipped.
* **Backend** on Render free tier (auto-deploy from master).  Cold-
  starts after 15 min idle so the first request takes 30-60 s — if
  the demo "looks broken," refresh.

## Stack

* Python 3.12, FastAPI, Pydantic v2, NumPy, SciPy, SymPy, pytest
* React 18, Vite 5, react-router v6, react-three-fiber, react-katex
* matplotlib (server-side SVG only — no GUI backend)

## Scope honesty

Things explicitly NOT in v3.2, with written specs in `docs/`
explaining the deferral:

* Real LIGO ringdown inference (would need Bilby + GWOSC API, ~4
  weeks)
* Full FLRW cosmology with arbitrary equation of state (needs the
  Friedmann ODE solver, ~2 weeks)
* HRT covariant entropy for time-dependent backgrounds (~1 week)

I'd rather have 7 working metrics + a clean test suite than 12 half-
finished ones.

PRs, "your test gate is wrong because [paper reference]" issues,
and questions all welcome.  MIT license.
```

---

## Why this framing should clear the LLM hostility bar

| Element | r/Physics post | r/Python post |
|---|---|---|
| **Lead** | "open-source platform for exploring exact solutions of GR" | "scientific Python project to learn FastAPI + React end-to-end" |
| **First proof** | seven physics page list | code organization + symplectic integrator story |
| **Hostile-reader prior** | "another LLM math toy" | "another scientific Python project, let's see the tests" |
| **Test-gate visibility** | mentioned mid-body | shown as engineering discipline up top |
| **Self-deprecation** | "I built this to learn GR" | "I built this to properly learn FastAPI + React" |

The r/Python community is more sympathetic to "I built X to learn Y"
because the underlying meta is "look at my engineering," not "look
at my physics."  The hostile-reader test ("does this read as LLM
output?") fails differently — r/Python skeptics ask "is the test
suite real?" and the answer is "yes, here's what's in it" with
specifics, not "trust me."

---

## Posting checklist (when actually submitting)

Before clicking Submit:

- [ ] Pre-warm Render backend (2-3 curl hits to `/api/health`) so
      the first reader doesn't hit a 30-60s cold start
- [ ] Verify https://spacetime-lab.vercel.app loads and the de Sitter
      / Kerr-Newman pages work (last things shipped)
- [ ] Confirm posting window: Tue-Thu, 8-10 AM Pacific
- [ ] Have the body text in clipboard, not retyping
- [ ] Have flair set to "Showcase" before submitting

After submitting:

- [ ] Set monitor running (`docs/monitor_reddit.sh` adapted to the new
      post URL) — log to `docs/r_python_log.txt`
- [ ] Do not reply to comments for first 2h (let community sort)
- [ ] Reply to substantive comments (technical questions, suggestions)
      with the same tone as the post body
- [ ] **Do not** reply to hostile comments in the first 6h.  If they
      get downvoted to bottom organically, leave alone.  If they're
      top-sorted at 6h, reply factually with citations only.

---

## Snapshot decision tree (mirror of r/Physics one)

| Snapshot at T+1h to T+24h | Action |
|---|---|
| Score > 30 + ratio > 0.85 | Cross-post to r/programming + r/scientific_computing; queue arXiv endorser emails |
| Score 10-30 | Wait full 24h; cross-post to r/scientific_computing only |
| Score 0-10 + post falling | Archive lesson; pause public launches; pivot to LinkedIn + personal blog |
| Removed by mod | Re-read removal reason; if rule violation, do not retry the same sub |

Higher thresholds than r/Physics because r/Python is bigger (~1.4M
vs ~2.4M actually — adjust if needed) and the engineering-first
framing should generate more upvotes if the project lands.
