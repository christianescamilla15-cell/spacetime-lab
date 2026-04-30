# Spacetime Lab — interactive black-hole physics in your browser

> **TL;DR**  Open-source Python + web platform that takes you from
> the Schwarzschild horizon to the resolution of the Hawking
> information paradox via the Page curve. Six live interactive
> pages, 700+ tests, 15 Jupyter notebook tutorials. MIT license.
>
> **Try it**: https://spacetime-lab.vercel.app
> **Code**: https://github.com/christianescamilla15-cell/spacetime-lab

---

I started Spacetime Lab six months ago as an excuse to learn General
Relativity by building tools for it. Six months later, the project
sits at v2.7 and covers an arc that I genuinely did not expect to
finish: every major piece of the holographic information-paradox
program is in there, with bit-exact tests pinning the canonical
results to their literature values.

This post is the launch announcement — what's in v2.7, what's
deliberately not, and how to play with it without installing
anything.

## What you can actually do, today

Open the live site and you get six pages, all functional. Move a
slider, get a result. No installation, no signup.

### `/schwarzschild`
The simplest exact black hole. Slide the mass parameter; watch the
event horizon, ISCO, photon sphere, Hawking temperature, and BH
entropy update. Below the readout, an interactive *effective
potential* plot $V_\text{eff}(r)$ for circular orbits at given
angular momentum, with stable/unstable critical points marked
automatically.

### `/kerr`
Two sliders: $M$ and $a/M$. Watch the inner and outer horizons
approach as you push $a/M$ toward extremality, the ISCO split into
prograde and retrograde branches (the prograde one collapses toward
$M$; the retrograde one grows toward $9M$), and the Hawking
temperature drop to zero. The 2D equatorial visualizer shades the
ergoregion.

### `/btz`
The 3D AdS black hole. Sliders for $r_+$ and $L$. The page does the
**Strominger 1998 calculation in real time**: it shows you the
boundary CFT central charge $c = 3L/(2 G_N)$ from Brown-Henneaux,
re-derives the Cardy entropy client-side, and ratios it against the
API's Bekenstein-Hawking value. The "Cardy check" card reads exactly
1.000000 every time.

### `/geodesics` ← **the new one in v2.6/v2.7**
Pick an initial $(r, p_t, p_\varphi, p_\theta)$, hit *Integrate*,
watch a Boyer-Lindquist Kerr trajectory animate around a Three.js
scene of horizons and ergosphere. You can stack up to five
trajectories at once with different presets (stable orbit, plunge,
Schwarzschild bound orbit, highly inclined Kerr) to compare. The
conservation diagnostics panel shows that energy and $z$-angular-
momentum drift is **zero** to machine precision (the integrator is
symplectic and $t, \varphi$ are cyclic) while Carter's $\mathcal{Q}$
drifts only at $O(h^2)$ per step.

You can also click on the equatorial disk to set the initial
position with the mouse.

### `/penrose`
Pan-and-zoom Penrose diagrams for Minkowski and Schwarzschild,
rendered server-side from `spacetime_lab.diagrams.render` (the
v1.5 SVG backend), embedded with `react-zoom-pan-pinch`.

### `/holography`
The money plot. Two side-by-side Page curves — one for eternal BTZ,
one for evaporating Schwarzschild. Slide horizon radius / AdS radius
/ initial mass and watch the Hartman-Maldacena vs. island saddle
crossover, color-coded by phase. The Page time vertical line moves
with you.

## What's underneath

The frontend is the visible layer; underneath, three more layers do
the actual work.

```
React + Three.js + KaTeX             ← what you click
            ↓ HTTP
FastAPI REST endpoints (17)          ← what serves the data
            ↓ Python imports
spacetime_lab/ Python package (8 modules) ← what does the physics
            ↓ pytest
700+ tests with bit-exact gates       ← what keeps it honest
```

The Python package is `pip install`able and used directly in the
fifteen Jupyter notebooks that ship with the repository. The
tutorials run end-to-end on a fresh clone with `jupyter nbconvert
--execute notebooks/*.ipynb`.

## The honest bits

Six months in, here's what is **not** in v2.7:

- No Reissner-Nordström, FLRW, or de Sitter (they're written down,
  just not implemented)
- No Kerr-Newman (the Teukolsky equation needs a different solver)
- No real LIGO ringdown fitter (the Bilby wrapper exists, the
  binding to a specific catalog event does not)
- No two-parameter QES for two-sided TFD geometries
- No replica-wormhole *Euclidean path integral* — we ship the
  on-shell actions only
- No HRT (covariant Ryu-Takayanagi) for time-dependent backgrounds

These are tracked in `ROADMAP-v3.md` and prioritized for v2.7.x and
v2.8.

## Why I'm sharing this

I write Python + AI infrastructure for a living. I am not a
relativist. I built Spacetime Lab to learn the field by reproducing
its canonical results, and to give other people a way to interact
with these objects without committing to a Mathematica license or a
PhD program.

If you find it useful — if you use a screenshot in a slide, or fork
it for an undergraduate course, or use the API in a paper — please
let me know. Open an issue, send a PR, or email. I want to see this
become a community resource.

## Try it

- **Live**: https://spacetime-lab.vercel.app
- **Code**: https://github.com/christianescamilla15-cell/spacetime-lab
- **Notebooks**: clone and `jupyter notebook notebooks/`
- **Embed in your own site**: every page has an `/embed/{name}`
  variant (no nav chrome) suitable for direct `<iframe src="…">`
- **Cite**: a draft arXiv preprint is in `docs/arxiv-draft.md`
- **License**: MIT

— Christian Hernández Escamilla, April 2026
