# Launch submission texts — copy/paste ready

**Live URLs (verified 2026-04-30):**
- Frontend: https://spacetime-lab.vercel.app
- Backend:  https://spacetime-lab-api.onrender.com
- Repo:     https://github.com/christianescamilla15-cell/spacetime-lab

> Render free tier spins down after 15 min idle.  First request after a
> cold start takes 30-60 s.  Heads-up if a HN comment says "site looks
> broken" — it's likely just the cold start.  Reply: "Render free tier
> cold start, give it 30 s and refresh."

---

## Hacker News — "Show HN"

**URL:** https://news.ycombinator.com/submit
**Login required:** yes (your HN account)

### Title (under 80 chars — HN limit)

```
Show HN: Spacetime Lab – Interactive black-hole physics in your browser
```

### URL field

```
https://spacetime-lab.vercel.app
```

### Text field — leave EMPTY

(For Show HN, you submit either URL or text, not both. URL gives the
demo first impression; the comment thread is where you add context.
Once submitted, immediately add a top-level comment with the body
below.)

### First comment to post yourself (immediately after submitting)

```
Author here.  Six months ago I started this as an excuse to learn
General Relativity by building tools for it.  Six months later it's
a Python package + REST API + interactive web app covering the full
arc from Schwarzschild to the Page curve / island formula.

The seven pages on the site each correspond to a Python module that's
pip-installable, with the same numbers, same conventions, and same
test gates.  690+ tests pin every closed-form result to its canonical
reference (Wald, MTW, Brown-Henneaux 1986, Strominger 1998,
Bardeen-Press-Teukolsky 1972, Page 1976, Hartman-Maldacena 2013).

What's actually live:
- Schwarzschild, Kerr, BTZ, AdS, Reissner-Nordström, Kerr-Newman,
  de Sitter — each with sliders, closed-form readouts, KaTeX
- Geodesic explorer with a Three.js Kerr scene + symplectic
  implicit-midpoint integrator (E and L_z conserved to machine
  precision because t and φ are cyclic in Boyer-Lindquist)
- Penrose diagrams (Minkowski + Schwarzschild four-region) with
  optional bound-orbit overlay
- Page curve (eternal BTZ + evaporating Schwarzschild) — the
  resolution of the Hawking information paradox in two animated plots

What's deferred (specs in docs/ explaining why and how):
- Real LIGO ringdown fitter (Bilby + GWOSC + posterior precompute)
- Full FLRW with mixed Ωm + Ωr + ΩΛ (needs Friedmann ODE)
- HRT covariant for time-dependent backgrounds
- A few polish items in the Penrose region tracking

Backend is on Render free tier so first hit after idle takes 30-60 s
to cold-start; if it looks broken, refresh.

MIT license, contributions welcome.  Issues, PRs, and "your physics
is wrong here" all read.

Code: https://github.com/christianescamilla15-cell/spacetime-lab
```

### Best time to submit

Tuesday-Thursday, 8-10 AM Pacific (US daytime gets the most HN
traffic).  Avoid Friday afternoon / weekend mornings.

---

## r/Physics

**URL:** https://www.reddit.com/r/Physics/submit
**Subreddit rules to check first:**
- r/Physics requires `[Project]` or `[Education]` flair for
  self-promotion-adjacent posts (mark this as Project)
- No URL-only posts; need a body
- One self-promo post per 30 days

### Flair

```
Project
```

### Title (under 300 chars but keep ≤ 100 for visibility)

```
[Project] Spacetime Lab — open-source interactive GR/holography toolkit (Schwarzschild → Page curve)
```

### Body (markdown)

```
I built **Spacetime Lab**, an open-source platform for exploring
exact solutions of General Relativity in the browser, ranging from
the Schwarzschild horizon to the modern resolution of the Hawking
information paradox via the island formula.

**Live:** https://spacetime-lab.vercel.app
**Code (MIT):** https://github.com/christianescamilla15-cell/spacetime-lab

Each of the seven physics pages corresponds to a pip-installable
Python module, with shared conventions (Lorentzian (-,+,+,+), Wald;
geometric units; LaTeX paired with every numerical result).  The
canonical results are pinned by a 690+ pytest suite at machine
precision against literature values (Wald, MTW, Brown-Henneaux 1986,
Strominger 1998, Bardeen-Press-Teukolsky 1972, Page 1976,
Hartman-Maldacena 2013).

**Pages currently live:**

* Schwarzschild — sliders for M, V_eff for circular orbits, ISCO,
  photon sphere, Hawking T
* Kerr — (M, a/M); ergosphere splits from horizon, ISCO into
  prograde/retrograde branches, third-law T → 0 at extremality
* Reissner-Nordström — (M, |Q|/M); cosmic censorship enforced;
  closed-form horizons + photon sphere; numerical ISCO
* Kerr-Newman — three-parameter (M, a, Q); all three limits cross-
  checked bit-exactly; ISCO via numerical R = R' = R'' = 0
* BTZ — Strominger-Cardy match recomputed client-side and gated
* AdS — implicit (used by holography page)
* de Sitter — Λ-only, static patch, Gibbons-Hawking T
* Geodesic explorer — Three.js Kerr scene, multiple simultaneous
  trajectories, click-pick on equatorial disk, conservation panel
  (E and L_z drift exactly zero by construction; Carter Q drifts
  at O(h²) per step as expected from the symplectic integrator)
* Penrose diagrams — Minkowski + Schwarzschild four-region; pan/zoom
* Holography — Page curves (eternal BTZ + evaporating Schwarzschild)
  side by side; Page time vertical line moves with you

**What's explicitly NOT in v3.2** (specs in `docs/` for each):

* Real LIGO ringdown inference (Bilby + GWOSC; deferred — 4 weeks +
  endorser)
* Full FLRW with arbitrary equation of state (deferred — needs the
  Friedmann ODE solver)
* HRT (covariant Ryu-Takayanagi) for time-dependent backgrounds
* Region-tracking through horizons in Penrose overlays (needs a
  Kruskal-coords integrator)

The arXiv preprint draft is in `docs/arxiv-draft.md` if you want to
read the formal write-up.

Feedback, "your physics is wrong here" reports, and PRs all welcome.

(Backend is on Render free tier so the first request after idle
takes 30-60 s to spin up.)
```

### Posting rules

- DO read r/Physics' submission rules before posting (auto-modded
  community)
- DO NOT post and immediately upvote yourself / from alt accounts
  (Reddit shadowbans for this)
- DO respond to comments — even rude ones — kindly and with citations

---

## Other targets (lower priority but worth doing)

### r/PhysicsStudents
URL: https://www.reddit.com/r/PhysicsStudents/submit
Same body, slightly less formal tone.  Higher engagement-per-view but
smaller subreddit.

### LinkedIn
URL: write a post on your profile
Best for non-physics audience — pitch the engineering side
(React + Three.js + FastAPI + 690 tests + 24 commits in 5 days).

### Twitter / X (if you use it)
4-tweet thread:
  1. The TL;DR + URL + one screenshot
  2. The "what's underneath" architecture diagram
  3. A specific physics result with a screenshot (suggest the Page
     curve — it's the "wow" plot)
  4. "MIT license, contributions welcome" + GitHub URL

### Physics blogs / newsletters worth emailing
- Sean Carroll's blog (sean@preposterousuniverse.com)
- Quanta Magazine "What's Up in the Universe" newsletter
- Ars Technica (john.timmer@arstechnica.com handles physics)

These are gigantic asks; only worth doing if HN/r/Physics get traction
first.
```
