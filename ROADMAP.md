# Spacetime Lab — Roadmap

18-month plan from bootstrap to v1.0 release, from Schwarzschild foundations to holographic entanglement entropy.

## Philosophy

Each phase delivers:
- ✅ **A physics concept mastered** (with understanding, not just code)
- ✅ **A working module in the platform** (visible in the web app)
- ✅ **A public release** (PyPI update, GitHub tag, blog post)

Ship every 2-4 weeks. Learn by building.

---

## Phase 0 — Bootstrap (current)

**Status:** 🏗️ In progress

- [x] Monorepo structure
- [x] README, LICENSE, CONTRIBUTING, SECURITY
- [x] `.gitignore`, CI stubs
- [ ] Python package skeleton (`pyproject.toml`, `__init__.py`)
- [ ] FastAPI backend skeleton
- [ ] React frontend skeleton
- [ ] Deploy to Vercel + Render
- [ ] Publish v0.0.1 to PyPI

**Deliverable:** Live deployment, empty but functional.

---

## Phase 1 — Schwarzschild Foundations (months 1-2)

**Physics concepts:**
- Lorentzian signature (-,+,+,+)
- Schwarzschild metric in different coordinates
- Event horizon, Kruskal-Szekeres extension
- Symbolic computation of Christoffel symbols and Riemann tensor

**Deliverables:**
- `spacetime_lab.metrics.Metric` abstract base class
- `spacetime_lab.metrics.Schwarzschild` full implementation
- Symbolic + numerical interfaces
- Web visualization: static embedding diagram of Schwarzschild
- Notebook: `01_schwarzschild_basics.ipynb`
- Contributions to Bilby (2-3 good-first-issue PRs)

**Release:** v0.1.0

---

## Phase 2 — Penrose Diagrams (months 3-4)

**Physics concepts:**
- Conformal compactification
- Causal structure
- Maximal extensions (Kruskal, Reissner-Nordström)
- Penrose diagram construction

**Deliverables:**
- `spacetime_lab.diagrams.penrose` module
- Penrose diagrams for Schwarzschild, RN, de Sitter, FLRW
- Export to SVG/TikZ for LaTeX papers
- Interactive web viewer
- Notebook: `02_penrose_diagrams.ipynb`

**Release:** v0.2.0

---

## Phase 3 — Kerr Geodesics (months 5-6)

**Physics concepts:**
- Kerr metric in Boyer-Lindquist
- Carter's constant (4th integral of motion)
- Separability of Kerr geodesic equation
- ISCO, photon sphere, ergosphere

**Deliverables:**
- `spacetime_lab.metrics.Kerr` full implementation
- `spacetime_lab.geodesics` symplectic integrator
- 3D interactive geodesic explorer (three.js)
- Notebook: `03_kerr_orbits.ipynb`
- Contributions to EinsteinPy revival

**Release:** v0.3.0

---

## Phase 4 — Horizon Finders (months 7-8)

**Physics concepts:**
- Event vs apparent horizon
- Trapped surfaces
- ISCO computation
- Photon sphere and its stability

**Deliverables:**
- `spacetime_lab.horizons` module
- Automatic horizon detection for arbitrary metrics
- Visualization of trapped regions
- Notebook: `04_horizon_topology.ipynb`

**Release:** v0.4.0

---

## Phase 5 — Gravitational Waves (months 9-10)

**Physics concepts:**
- Linear perturbations on Kerr
- Quasinormal modes (QNMs)
- Ringdown and BH spectroscopy
- Connection to LIGO observations

**Deliverables:**
- `spacetime_lab.waves` module
- QNM spectrum calculator for Kerr
- Integration with Bilby/PyCBC for real LIGO data
- Ringdown fitter for observed events
- Notebook: `05_ringdown_analysis.ipynb`

**Release:** v0.5.0

---

## Phase 6 — Quantum Information Basics (months 11-12)

**Physics concepts:**
- Density matrices, purity, von Neumann entropy
- Entanglement measures
- Quantum channels
- Replica trick for entropy

**Deliverables:**
- `spacetime_lab.entropy.quantum_info` helpers
- Integration with quimb for TN states
- Educational notebooks on entanglement
- Notebook: `06_entanglement_intro.ipynb`

**Release:** v0.6.0

---

## Phase 7 — AdS/CFT Foundations (months 13-14)

**Physics concepts:**
- Anti-de Sitter geometry
- BTZ black hole
- Conformal field theory basics
- GKP-Witten prescription

**Deliverables:**
- `spacetime_lab.metrics.AdS` and `spacetime_lab.metrics.BTZ`
- CFT boundary observables
- Notebook: `07_ads_cft_intro.ipynb`

**Release:** v0.7.0

---

## Phase 8 — Holographic Entanglement (months 15-16)

**Physics concepts:**
- Ryu-Takayanagi formula
- HRT surfaces (covariant extension)
- Subregion duality
- Entanglement wedge

**Deliverables:**
- `spacetime_lab.entropy.rt_surface` module
- `spacetime_lab.entropy.hrt_surface` module
- RT surface computation for simple geometries
- Comparison: holographic vs direct TN entropy
- Notebook: `08_holographic_entanglement.ipynb`

**Release:** v0.8.0 → v0.9.0

---

## Phase 9 — v1.0 Release (months 17-18)

- Polish all modules
- Complete documentation site
- Tutorial video series
- Paper draft (computational physics venue)
- Community outreach (Twitter, Reddit /r/Physics, /r/GeneralRelativity)
- Present at virtual seminar (if possible)

**Release:** v1.0.0 🚀

---

## Success Metrics

By v1.0:
- [ ] 100+ GitHub stars
- [ ] 20+ PyPI downloads/week
- [ ] 3+ external contributors
- [ ] 1 paper or arXiv preprint
- [ ] 5+ Jupyter tutorials
- [ ] 10+ exact metric solutions
- [ ] Featured in at least one physics blog or newsletter
