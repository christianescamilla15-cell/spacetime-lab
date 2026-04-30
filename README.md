# Spacetime Lab

A Python + web toolkit for exploring exact solutions of General Relativity in the browser, from Schwarzschild geodesics to the Page curve.

Live: https://spacetime-lab.vercel.app
API: https://spacetime-lab-api.onrender.com (Render free tier, first hit cold-starts in 30-60 s)
Code: MIT licensed, this repo.

```
790 tests passing
7 metric classes (Schwarzschild, Kerr, BTZ, AdS, Reissner-Nordström, Kerr-Newman, de Sitter)
9 frontend pages, all with EN/ES toggle
15 tutorial notebooks
```

## Why this exists

I'm Christian. About six months ago I started reading Wald cover-to-cover and got stuck on Kerr at chapter 12. The textbook plots horizons and ergospheres in the abstract, my brain wanted sliders. I couldn't find an interactive thing that wasn't either (a) a 2003-era Java applet or (b) a closed Mathematica notebook behind a paywall, so I started building one. Six months in I have something that works and I figured I'd put it online.

The project is an excuse to learn three things at once: actual GR (the physics), production scientific Python (FastAPI + Pydantic v2 + a real test suite), and React with Three.js (the frontend was the part I knew least about).

## How it was built (honest version)

I use Claude as a pair programmer. That doesn't mean Claude wrote the project: every formula has a test that checks it against a published reference value (Brown-Henneaux 1986 central charge, Bardeen-Press-Teukolsky 1972 ISCO closed form, Strominger 1998 Cardy match, Carter constant drift bounds). When the test fails the code is wrong, full stop. I've had Claude produce sign errors and incorrect Kerr Δ definitions that the tests caught immediately.

I'm flagging this upfront because some readers see a polished open-source project from an unknown author and assume "vibe coded slop". The defense is the test suite, not the README prose. If you find a physics bug, open an issue with the reference and I'll fix it.

What I personally wrote vs. what Claude assisted with: the architecture, the test gates, the choice of which references to pin against, the commit messages, this README. Claude helped a lot with React/Three.js boilerplate (which I'd never used before) and with the more tedious Pydantic models. Both of us made mistakes; the tests caught them.

## What works right now

Seven black-hole / cosmological metrics, each with a REST endpoint, a frontend page, and bit-exact verification tests:

- **Schwarzschild** (Phase 1). Sliders for M, live readouts of horizon, ISCO, photon sphere, Hawking T. Most basic page.
- **Kerr** (Phase 3). Two-parameter (M, a/M), ergosphere splits from horizon, ISCO bifurcates into prograde/retrograde, ISCO via Bardeen-Press-Teukolsky 1972 closed form.
- **BTZ** (Phase 8). 3D AdS black hole. Strominger-Cardy match recomputed client-side and gated.
- **AdS** (Phase 7). Mostly used by the holography page.
- **Reissner-Nordström** (v3.1). Charged static. Cosmic censorship enforced; ISCO solved numerically from dL²/dr=0.
- **Kerr-Newman** (v3.2). Three-parameter (M, a, Q). All three limits cross-checked. ISCO via numerical R=R'=R''=0 system.
- **de Sitter** (v3.2). Λ-only static patch, Gibbons-Hawking radiation. The easy half of the FLRW family.

Plus:

- **Geodesic explorer**. Three.js Kerr scene with multiple simultaneous trajectories, click-pick on the equatorial disk to launch a new geodesic. Implicit-midpoint symplectic integrator: E and L_z (cyclic coordinates) drift exactly zero, Carter Q drifts at O(h²) per step. There's a conservation panel that shows the drift in real time. Watching that work is the prettiest debug session I had this whole project.
- **Penrose diagrams**. Minkowski + Schwarzschild four-region. Pan/zoom. Optional bound-orbit overlay projected via (t,r) → (U,V).
- **Holography**. Page curves for both eternal BTZ (Hartman-Maldacena vs. island saddle) and evaporating Schwarzschild (bell shape returning to zero). The Page time vertical line moves with you.

Everything is bilingual (English / Spanish) via a toggle in the top-right.

## What's broken or missing

Things I wanted to ship but didn't, with honest reasons:

- **LIGO ringdown fitting**. Designed it, wrote a 4-page spec (`docs/v3.1-ligo-ringdown-spec.md`), realised it's 4 weeks of work and needs Bilby + GWOSC integration, and parked it. The Bilby team won't review my contributions seriously without a published preprint first.
- **Full FLRW cosmology**. Have de Sitter (the closed-form Λ-only case). The general case needs the Friedmann ODE solver and a unit-system decision (Mpc vs. geometric vs. natural). Spec at `docs/v3.2-flrw-de-sitter-spec.md`.
- **HRT covariant entropy**. Time-dependent backgrounds. Spec at `docs/v3.3-hrt-covariant-spec.md`. Needs a careful Wall 2014 reread.
- **Penrose region tracking through horizons**. The bound-orbit overlay only renders region I; tracking through II/III/IV needs a Kruskal-coords integrator. Multi-day job.
- **Kerr-Newman ISCO closed form** (Aliev-Galtsov 1981). The polynomial is genuinely gnarly. The numerical version matches the closed Kerr/RN limits to fsolve tolerance, so this is marginal.

The pattern: I'd rather have 7 metrics that work bit-exactly than 12 half-finished ones that lie about their precision.

## Quick start

```bash
git clone https://github.com/christianescamilla15-cell/spacetime-lab.git
cd spacetime-lab

# Backend
cd backend
pip install -r requirements.txt
pip install ..          # install the spacetime_lab package itself
uvicorn app.main:app --reload   # http://localhost:8000

# Frontend (in another terminal)
cd frontend
npm install
npm run dev             # http://localhost:5173
```

If you only want the Python package, `pip install -e .` from the repo root works (PyPI release pending, see issue if you need it sooner).

## Example usage

```python
from spacetime_lab.metrics import Schwarzschild

bh = Schwarzschild(mass=1.0)
print(bh.event_horizon())              # 2.0
print(bh.isco())                       # 6.0
print(bh.hawking_temperature())        # ~0.0199 (= 1/(8π))
print(bh.line_element_latex())
```

```python
from spacetime_lab.metrics import KerrNewman

kn = KerrNewman(mass=1.0, spin=0.6, charge=0.7)
# Kerr-Newman raises ValueError if a²+Q² > M² (cosmic censorship).
print(kn.outer_horizon(), kn.inner_horizon())
print(kn.ergosphere(theta=1.5708))
```

## Layout

```
spacetime_lab/      # Python package
  metrics/          # 7 metric classes
  diagrams/         # Penrose renderers
  geodesics/        # symplectic integrator
  horizons/         # closed-form solvers
  holography/       # AdS/CFT + Page curve
  waves/            # qnm wrapper
  entropy/          # quantum information primitives
backend/            # FastAPI REST + WebSocket API
frontend/           # React 18 + Vite + Three.js
notebooks/          # 15 tutorial notebooks
docs/               # specs for deferred features + arXiv draft
tests/              # 790 pytest tests
```

## Notebooks

The `notebooks/` folder pairs the physics narrative with executable checks against the package. Read in order if you want to follow the same path I took.

| #  | Notebook                              | What you get out of it |
|----|---------------------------------------|------------------------|
| 01 | `01_schwarzschild_basics.ipynb`       | Line element, vacuum Einstein, Kretschmann, tortoise/Kruskal, V_eff, horizon thermodynamics |
| 02 | `02_penrose_diagrams.ipynb`           | Conformal compactification, Minkowski diamond, Schwarzschild four regions |
| 03 | `03_kerr_geodesics.ipynb`             | Boyer-Lindquist, ISCO bifurcation, Hamilton's equations, symplectic integrator, Carter Q |
| 04 | `04_horizon_topology.ipynb`           | Event vs. apparent, MOTS, Bardeen 1973 photon shadow (the EHT geometry) |
| 05 | `05_quasinormal_modes.ipynb`          | Regge-Wheeler, Leaver continued fractions, dominant Mω ~ 0.37 - 0.09i |
| 06 | `06_entanglement_entropy.ipynb`       | Density matrices, Schmidt, Bell pair = log 2, bridge to holographic entropy |
| 07 | `07_ads_cft_foundations.ipynb`        | AdS in Poincaré, Brown-Henneaux c, RT vs Calabrese-Cardy bit-exact |
| 08 | `08_holographic_phase_transitions.ipynb` | BTZ, Strominger 1998, two-interval mutual information kink at cross-ratio = 1/2 |
| 09 | `09_island_formula.ipynb`             | The Hawking paradox + Page curve in eternal BTZ |
| 10 | `10_evaporating_page_curve.ipynb`     | Page 1976 cubic, bell-shaped curve returning to zero, t_P = (1 - √2/4) t_evap |
| 11 | `11_kerr_qnm_spectroscopy.ipynb`      | Berti-Cardoso-Starinets 2009 Fig 2 reproduced, BH spectroscopy as no-hair test |
| 12 | `12_rotating_btz.ipynb`               | Outer + inner horizons, ergoregion, rotating Strominger-Cardy with L_0 ≠ L̄_0 |
| 13 | `13_penrose_renderers.ipynb`          | SVG / TikZ / matplotlib backends from a single Scene |
| 14 | `14_quantum_extremal_surfaces.ipynb`  | Real QES finder, replica wormholes, higher-d RT |
| 15 | `15_v2_1_dynamics.ipynb`              | Dynamical Page curve, three-path cross-check, Schwarzschild-AdS RT |

## Contributing back

I've been trying to ship small fixes to the libraries I depend on. Phase 5 produced eight PRs to [bilby-dev/bilby](https://github.com/bilby-dev/bilby) (gravitational-wave inference framework):

| #     | PR        | Topic |
|-------|-----------|-------|
| 1069  | merged-ish | `matched_filter_snr` docstring (complex vs squared) |
| 1070  | open      | Document `conversion.py` spin / mass-ratio parameters |
| 1071  | open      | `.devcontainer/` (core + gw) |
| 1072  | open      | Logger uses `NullHandler` by default |
| 1073  | open      | `Emcee.get_expected_outputs` classmethod for HTCondor |
| 1074  | open      | `plot_exclude_keys` for bilby_mcmc trace plots |
| 1075  | open      | Nested-sampling weights in `plot_corner` |
| 1076  | open      | Wire docstring doctests into the unittest suite |

Realistic note: most are open. The Bilby team rightly prioritises contributions from people they recognise. Part of why I'm publishing Spacetime Lab is to build that recognition.

## Contributing to this repo

Issues and PRs welcome. The two things I'd love help with:

1. **Physics bug reports**. If you find a number that disagrees with a literature value, open an issue with the reference (paper + equation number). I'll fix and add a regression test.
2. **More test gates**. The pattern in `tests/` is "pin every closed-form invariant against its canonical reference value at machine precision". Adding more of these (especially in places where I currently only have the obvious ones) is high-value.

Avoid:

- Refactoring for refactoring's sake. The architecture is intentional.
- Adding new dependencies without discussion.
- "I rewrote your prose to flow better". The writing voice is mine, intentional warts and all.

## Reading list

The papers I actually used while building this. Not exhaustive — just the ones I returned to.

- Wald, *General Relativity* (1984). The textbook. Ch. 6 (Schwarzschild), 11 (Penrose), 12 (Kerr).
- Bardeen, Press, Teukolsky, *Astrophys. J.* 178 (1972). Kerr ISCO closed form, used in `tests/test_kerr.py`.
- Brown & Henneaux, *Commun. Math. Phys.* 104 (1986). Central charge of AdS_3 boundary CFT.
- Strominger, *JHEP* 02 (1998). The Cardy → Bekenstein-Hawking match for BTZ.
- Page, *Phys. Rev. Lett.* 71 (1993). Page time, Page curve.
- Hartman & Maldacena, *JHEP* 05 (2013). Eternal-BH entropy growth.
- Penington, Shenker, Stanford, Yang, *JHEP* 03 (2022). Replica wormholes.
- Berti, Cardoso, Starinets, *Class. Quantum Grav.* 26 (2009). QNM review.

## Acknowledgments

- The [`qnm`](https://github.com/duetosymmetry/qnm) package by Leo C. Stein, used in the QNM module via direct wrapper.
- [EinsteinPy](https://github.com/einsteinpy/einsteinpy) for showing it's possible to build a serious GR package in Python.
- The [Bilby](https://github.com/bilby-dev/bilby) maintainers for being patient with my early PRs.

## License

MIT. See [LICENSE](./LICENSE).

---

Built by Christian Hernández. Issues and "your physics is wrong here" reports both welcome.
