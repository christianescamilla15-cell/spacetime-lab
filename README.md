# Spacetime Lab

**Interactive platform for exploring black hole physics.**

From Schwarzschild geodesics to holographic entanglement entropy — a modern, open-source toolkit for general relativity, black hole thermodynamics, and the frontier of quantum gravity.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/christianescamilla15-cell/spacetime-lab)

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
| `metrics/` | Exact solutions (Schwarzschild, Kerr, AdS, BTZ) | ✅ Schwarzschild + Kerr (v0.3) |
| `diagrams/` | Penrose and embedding diagram generators | ✅ Minkowski + Schwarzschild (v0.2) |
| `geodesics/` | Symplectic geodesic integration in curved spacetime | ✅ implicit-midpoint (v0.3) |
| `horizons/` | Event horizon, ISCO, photon shadow finders | ✅ algebraic + Bardeen 1973 shadow (v0.4) |
| `waves/` | Quasinormal modes + ringdown waveforms | ✅ Schwarzschild QNM + ringdown (v0.5) |
| `waves/` | Quasinormal modes, ringdown, LIGO integration | 📅 Phase 5 |
| `entropy/` | Holographic entanglement entropy (RT/HRT surfaces) | 📅 Phase 7 |
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
- 🏗️ Phase 6 — Quantum information basics
- 📅 Phase 7 — AdS/CFT foundations
- 📅 Phase 8 — Holographic entanglement (RT/HRT)
- 📅 Phase 9 — v1.0 release

## Tutorial notebooks

Concept notebooks live under [`notebooks/`](./notebooks) and pair the physics narrative with executable checks against the `spacetime_lab` API.

| # | Notebook | Phase | What you learn |
|---|----------|-------|----------------|
| 01 | [`01_schwarzschild_basics.ipynb`](./notebooks/01_schwarzschild_basics.ipynb) | 1 | Line element, vacuum Einstein equations, Kretschmann scalar, tortoise and Kruskal coordinates, effective potential, horizon thermodynamics |
| 02 | [`02_penrose_diagrams.ipynb`](./notebooks/02_penrose_diagrams.ipynb) | 2 | Conformal compactification, the five infinities, Minkowski diamond, Schwarzschild four-region Penrose diagram, the straight-line singularity identity |
| 03 | [`03_kerr_geodesics.ipynb`](./notebooks/03_kerr_geodesics.ipynb) | 3 | Boyer–Lindquist Kerr, horizons + ergoregion, prograde/retrograde ISCO and photon sphere, Hamilton's equations, implicit-midpoint symplectic integrator, Carter's constant, 2nd-order convergence |
| 04 | [`04_horizon_topology.ipynb`](./notebooks/04_horizon_topology.ipynb) | 4 | Event vs apparent horizon, MOTS, numerical horizon and ISCO finders, Schwarzschild critical impact parameter, Bardeen 1973 photon shadow with frame-dragging asymmetries (the EHT geometry) |
| 05 | [`05_quasinormal_modes.ipynb`](./notebooks/05_quasinormal_modes.ipynb) | 5 | Linear perturbations of Schwarzschild, Regge-Wheeler equation, Leaver continued fraction, dominant gravitational mode `M*omega ~ 0.37 - 0.09 i`, ringdown waveform generator, no-hair theorem test |

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
