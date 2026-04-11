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
| `metrics/` | Exact solutions (Schwarzschild, Kerr, AdS, BTZ) | 🏗️ Building |
| `diagrams/` | Penrose and embedding diagram generators | 📅 Phase 2 |
| `geodesics/` | Symplectic geodesic integration in curved spacetime | 📅 Phase 3 |
| `horizons/` | Event horizon, ISCO, photon sphere finders | 📅 Phase 4 |
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

- ✅ Phase 0 — Bootstrap (you are here)
- 🏗️ Phase 1 — Schwarzschild foundations
- 📅 Phase 2 — Penrose diagrams
- 📅 Phase 3 — Kerr geodesics
- 📅 Phase 4 — Horizon finders
- 📅 Phase 5 — Gravitational waves
- 📅 Phase 6 — Quantum information basics
- 📅 Phase 7 — AdS/CFT foundations
- 📅 Phase 8 — Holographic entanglement (RT/HRT)
- 📅 Phase 9 — v1.0 release

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
