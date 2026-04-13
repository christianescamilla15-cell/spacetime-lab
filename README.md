# Spacetime Lab

**Interactive platform for exploring black hole physics.**

From Schwarzschild geodesics to holographic entanglement entropy — a modern, open-source toolkit for general relativity, black hole thermodynamics, and the frontier of quantum gravity.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Version 1.2.0](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/christianescamilla15-cell/spacetime-lab/releases/tag/v1.2.0)
[![Tests](https://img.shields.io/badge/tests-535%20passing-brightgreen.svg)](https://github.com/christianescamilla15-cell/spacetime-lab)

---

## What is Spacetime Lab?

Spacetime Lab is an interactive web platform and Python SDK for exploring black hole physics. It bridges the gap between reading papers and running code — you get a canonical toolkit for computing, visualizing, and understanding spacetime geometry.

**Built for:**
- 🎓 Graduate students learning general relativity
- 👩‍🏫 Instructors teaching black hole physics
- 🔬 Computational physicists and GR researchers
- 🧠 Anyone curious about what's really inside a black hole

## Planned Modules

| Module | What it does | Status |
|--------|-------------|--------|
| `metrics/` | Exact solutions (Schwarzschild, Kerr, AdS, BTZ) | ✅ Schwarzschild + Kerr + AdS + BTZ (v0.8) |
| `diagrams/` | Penrose and embedding diagram generators | ✅ Minkowski + Schwarzschild (v0.2) |
| `geodesics/` | Symplectic geodesic integration in curved spacetime | ✅ implicit-midpoint (v0.3) |
| `horizons/` | Event horizon, ISCO, photon shadow finders | ✅ algebraic + Bardeen 1973 shadow (v0.4) |
| `waves/` | Quasinormal modes + ringdown waveforms | ✅ Schwarzschild QNM + ringdown (v0.5) |
| `entropy/` | Quantum information primitives (von Neumann, Schmidt, partial trace) | ✅ pure-numpy implementation (v0.6) |
| `holography/` | Holographic entanglement entropy: AdS geodesics, RT, Brown-Henneaux, **island formula** | ✅ AdS_3/CFT_2 RT (v0.7) + BTZ + Strominger + two-interval phase transition (v0.8) + **Page curve from island formula (v1.0)** |
| `waves/` | Quasinormal modes, ringdown, LIGO integration | 📅 Phase 5 |
| (RT/HRT surfaces) | Holographic entanglement entropy via geodesic / minimal surface integration | 📅 Phase 7-8 |
| `edu/` | Interactive tutorials and educational notebooks | 🔄 Continuous |

## Quick Start

```bash
# Install the Python package
pip install spacetime-lab

# Or clone and run the full platform locally
git clone https://github.com/christianescamilla15-cell/spacetime-lab.git
cd spacetime-lab

# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Example Usage

```python
from spacetime_lab.metrics import Schwarzschild

# Create a Schwarzschild black hole with mass M = 1
bh = Schwarzschild(mass=1.0)

# Get the metric tensor at a point
g = bh.metric_at(r=3.0, theta=1.5708)

# Find the event horizon
r_h = bh.event_horizon()  # Returns 2.0 (in geometric units)

# Print the line element
print(bh.line_element_latex())
```

## Architecture

```
spacetime-lab/
├── spacetime_lab/    # Core Python package (pip installable)
├── backend/          # FastAPI REST + WebSocket API
├── frontend/         # React + Three.js interactive viewer
├── docs/             # MkDocs Material documentation
└── notebooks/        # Jupyter playgrounds and tutorials
```

## Roadmap

**18-month plan — from Schwarzschild to holography.** See [ROADMAP.md](./ROADMAP.md) for the full phase-by-phase breakdown.

- ✅ Phase 0 — Bootstrap
- ✅ Phase 1 — Schwarzschild foundations (v0.1.0)
- ✅ Phase 2 — Penrose diagrams (v0.2.0)
- ✅ Phase 3 — Kerr geodesics (v0.3.0)
- ✅ Phase 4 — Horizon finders + photon shadow (v0.4.0)
- ✅ Phase 5 — Quasinormal modes + ringdown (v0.5.0)
- ✅ Phase 6 — Quantum information primitives (v0.6.0)
- ✅ Phase 7 — AdS/CFT foundations + Ryu-Takayanagi (v0.7.0)
- ✅ Phase 8 — Holographic depth: BTZ, Strominger, two-interval phase transition (v0.8.0)
- ✅ **Phase 9 — Island formula and the Page curve (v1.0.0)** ★ ROADMAP COMPLETE ★
- ✅ **v1.1 patch — Evaporating Schwarzschild Page curve (bell-shaped, returns to zero)** (v1.1.0)
- ✅ **v1.2 patch — Kerr QNM wrapper (m-splitting, prograde vs retrograde, BH spectroscopy)** (v1.2.0)

## Tutorial notebooks

Concept notebooks live under [`notebooks/`](./notebooks) and pair the physics narrative with executable checks against the `spacetime_lab` API.

| # | Notebook | Phase | What you learn |
|---|----------|-------|----------------|
| 01 | [`01_schwarzschild_basics.ipynb`](./notebooks/01_schwarzschild_basics.ipynb) | 1 | Line element, vacuum Einstein equations, Kretschmann scalar, tortoise and Kruskal coordinates, effective potential, horizon thermodynamics |
| 02 | [`02_penrose_diagrams.ipynb`](./notebooks/02_penrose_diagrams.ipynb) | 2 | Conformal compactification, the five infinities, Minkowski diamond, Schwarzschild four-region Penrose diagram, the straight-line singularity identity |
| 03 | [`03_kerr_geodesics.ipynb`](./notebooks/03_kerr_geodesics.ipynb) | 3 | Boyer–Lindquist Kerr, horizons + ergoregion, prograde/retrograde ISCO and photon sphere, Hamilton's equations, implicit-midpoint symplectic integrator, Carter's constant, 2nd-order convergence |
| 04 | [`04_horizon_topology.ipynb`](./notebooks/04_horizon_topology.ipynb) | 4 | Event vs apparent horizon, MOTS, numerical horizon and ISCO finders, Schwarzschild critical impact parameter, Bardeen 1973 photon shadow with frame-dragging asymmetries (the EHT geometry) |
| 05 | [`05_quasinormal_modes.ipynb`](./notebooks/05_quasinormal_modes.ipynb) | 5 | Linear perturbations of Schwarzschild, Regge-Wheeler equation, Leaver continued fraction, dominant gravitational mode `M*omega ~ 0.37 - 0.09 i`, ringdown waveform generator, no-hair theorem test |
| 06 | [`06_entanglement_entropy.ipynb`](./notebooks/06_entanglement_entropy.ipynb) | 6 | Density matrices, partial traces, von Neumann entropy, Schmidt decomposition, Bell pair = log 2, GHZ bipartitions, mutual information, the bridge to holographic entanglement entropy |
| 07 | [`07_ads_cft_foundations.ipynb`](./notebooks/07_ads_cft_foundations.ipynb) | 7 | Pure AdS in Poincare coordinates, R = -n(n-1)/L^2 verified, Brown-Henneaux c = 3L/(2G_N), AdS_3 boundary geodesics, Ryu-Takayanagi formula bit-exactly equal to Calabrese-Cardy 2D CFT entropy across 5 orders of magnitude |
| 08 | [`08_holographic_phase_transitions.ipynb`](./notebooks/08_holographic_phase_transitions.ipynb) | 8 | BTZ black hole as a quotient of AdS_3, Strominger 1998 microscopic derivation S_BH from CFT Cardy, finite-T Calabrese-Cardy with limit checks, two-interval phase transition with mutual information kink at cross-ratio = 1/2 |
| 09 | [`09_island_formula.ipynb`](./notebooks/09_island_formula.ipynb) | 9 | The Hawking information paradox, Page's 1993 prediction, the island formula, Hartman-Maldacena 2013 closed form in eternal BTZ, **the Page curve plotted** — rises linearly until the Page time then saturates at 2 S_BH (the resolution of a 49-year-old paradox in one notebook) |
| 10 | [`10_evaporating_page_curve.ipynb`](./notebooks/10_evaporating_page_curve.ipynb) | v1.1 | Page 1976 Schwarzschild evaporation law, the cubic shrinking `M(t) = M_0(1-t/t_evap)^(1/3)`, no-island vs QES saddles for an evaporating BH, the **bell-shaped Page curve that returns to zero at t_evap** (toy-model unitarity), closed-form Page time `t_P = (1 - √2/4) t_evap` (not at the midpoint!) |
| 11 | [`11_kerr_qnm_spectroscopy.ipynb`](./notebooks/11_kerr_qnm_spectroscopy.ipynb) | v1.2 | Kerr QNM wrapper via `qnm.modes_cache`, breaking the Schwarzschild m-degeneracy into 2l+1 frequencies, prograde vs retrograde splitting (Berti-Cardoso-Starinets Fig 2 reproduced numerically), BH spectroscopy as a no-hair test — two measured QNMs must pin a single (M, a) |

## Upstream contributions

Part of Spacetime Lab's philosophy is *learn by shipping to real projects*. Phase 1 produced the following pull requests to [`bilby-dev/bilby`](https://github.com/bilby-dev/bilby):

| # | PR | Topic |
|---|-----|-------|
| 1 | [bilby-dev/bilby#1069](https://github.com/bilby-dev/bilby/pull/1069) | Fix `matched_filter_snr` docstring (complex vs squared) |
| 2 | [bilby-dev/bilby#1070](https://github.com/bilby-dev/bilby/pull/1070) | Document `conversion.py` spin / mass-ratio parameters |
| 3 | [bilby-dev/bilby#1071](https://github.com/bilby-dev/bilby/pull/1071) | Add `.devcontainer/` (core + gw) |
| 4 | [bilby-dev/bilby#1072](https://github.com/bilby-dev/bilby/pull/1072) | Logger uses `NullHandler` by default |
| 5 | [bilby-dev/bilby#1073](https://github.com/bilby-dev/bilby/pull/1073) | `Emcee.get_expected_outputs` classmethod for HTCondor transfer |
| 6 | [bilby-dev/bilby#1074](https://github.com/bilby-dev/bilby/pull/1074) | `plot_exclude_keys` for bilby_mcmc trace plots |
| 7 | [bilby-dev/bilby#1075](https://github.com/bilby-dev/bilby/pull/1075) | Use nested-sampling weights in `plot_corner` + weighted quantiles |
| 8 | [bilby-dev/bilby#1076](https://github.com/bilby-dev/bilby/pull/1076) | Wire docstring doctests into the unittest suite |

## Contributing

Contributions welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

**Good first issues:**
- Adding new exact metric solutions
- Writing tutorial notebooks
- Improving documentation
- Performance optimization

## License

MIT — see [LICENSE](./LICENSE).

## Acknowledgments

Standing on the shoulders of:
- [Wald's *General Relativity*](https://press.uchicago.edu/ucp/books/book/chicago/G/bo5952261.html)
- [EinsteinPy](https://github.com/einsteinpy/einsteinpy)
- [quimb](https://github.com/jcmgray/quimb)
- [PyCBC](https://github.com/gwastro/pycbc) and [Bilby](https://github.com/bilby-dev/bilby)
- The holography community (Maldacena, Susskind, Harlow, Penington, and many others)

---

**Built by [Christian Hernández](https://github.com/christianescamilla15-cell)** — an AI engineer learning general relativity by building tools for it.
