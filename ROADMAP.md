# Spacetime Lab — Roadmap

18-month plan from bootstrap to v1.0 release, from Schwarzschild foundations to holographic entanglement entropy.

## Philosophy

Each phase delivers:
- ✅ **A physics concept mastered** (with understanding, not just code)
- ✅ **A working module in the platform** (visible in the web app)
- ✅ **A public release** (PyPI update, GitHub tag, blog post)

Ship every 2-4 weeks. Learn by building.

---

## Phase 0 — Bootstrap

**Status:** ✅ Done

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

**Status:** ✅ Done — shipped as v0.1.0 on 2026-04-10.

**Physics concepts:**
- Lorentzian signature (-,+,+,+)
- Schwarzschild metric in different coordinates
- Event horizon, Kruskal-Szekeres extension
- Symbolic computation of Christoffel symbols and Riemann tensor

**Deliverables:**
- [x] `spacetime_lab.metrics.Metric` abstract base class
- [x] `spacetime_lab.metrics.Schwarzschild` full implementation (26 tests)
- [x] Symbolic + numerical interfaces
- [ ] Web visualization: static embedding diagram of Schwarzschild *(deferred to Phase 2 — will be rolled into the diagrams module)*
- [x] Notebook: `01_schwarzschild_basics.ipynb`
- [x] Contributions to Bilby — **8 PRs opened** (target was 2-3): #1069, #1070, #1071, #1072, #1073, #1074, #1075, #1076

**Release:** v0.1.0 — tagged 2026-04-10.

---

## Phase 2 — Penrose Diagrams (months 3-4)

**Status:** ✅ Done — shipped as v0.2.0 on 2026-04-10.

**Physics concepts:**
- Conformal compactification
- Causal structure
- Maximal extensions (Kruskal, Reissner-Nordström)
- Penrose diagram construction

**Deliverables:**
- [x] `spacetime_lab.diagrams.penrose` module — `PenroseChart` ABC + `MinkowskiPenrose` + `SchwarzschildPenrose`
- [x] Penrose diagram for Schwarzschild (full four-region maximally extended)
- [ ] Reissner-Nordström, de Sitter, FLRW — *deferred to a Phase 2.5 / Phase 7 extension*
- [ ] Export to SVG/TikZ for LaTeX papers — *stubs in place, implementation deferred to a follow-up pass*
- [ ] Interactive web viewer — *deferred to the frontend sprint*
- [x] Notebook: `02_penrose_diagrams.ipynb`
- [x] `render_matplotlib` backend (unlocks the notebook)
- [x] 83 new tests (33 Minkowski + 50 Schwarzschild) — total suite 109 tests

**Release:** v0.2.0 — tagged 2026-04-10.

---

## Phase 3 — Kerr Geodesics (months 5-6)

**Status:** ✅ Done — shipped as v0.3.0 on 2026-04-11.

**Physics concepts:**
- Kerr metric in Boyer-Lindquist
- Carter's constant (4th integral of motion)
- Separability of Kerr geodesic equation
- ISCO, photon sphere, ergosphere

**Deliverables:**
- [x] `spacetime_lab.metrics.Kerr` full implementation (59 tests, vacuum Einstein verified numerically to ~1e-15)
- [x] `spacetime_lab.geodesics` symplectic integrator — implicit-midpoint, works for Kerr's non-separable Hamiltonian
- [x] Carter's constant (`carter_constant_from_state`) and `constants_of_motion`
- [x] Notebook: `03_kerr_geodesics.ipynb` with concept session, integrator demo, conservation diagnostics, and 2nd-order convergence test
- [ ] 3D interactive geodesic explorer (three.js) — *deferred to the frontend sprint*
- [ ] Contributions to EinsteinPy revival — *deferred*

**Release:** v0.3.0 — tagged 2026-04-11.

---

## Phase 4 — Horizon Finders (months 7-8)

**Status:** ✅ Done — shipped as v0.4.0 on 2026-04-11.

**Physics concepts:**
- Event vs apparent horizon
- Trapped surfaces (MOTS / outermost expansion zero)
- ISCO computation via the effective potential
- Photon sphere and its stability
- Bardeen 1973 photon shadow

**Deliverables:**
- [x] `spacetime_lab.horizons` module (event finder + ISCO finder + Bardeen shadow)
- [x] Automatic horizon detection for arbitrary axisymmetric stationary metrics — verified against Schwarzschild and Kerr to ~`1e-9`
- [x] Numerical ISCO via the effective potential — Schwarzschild verified to ~`1e-7`
- [x] Bardeen 1973 photon shadow generator — verified Schwarzschild limit to ~`1e-2`
- [x] Notebook: `04_horizon_topology.ipynb` with the headline near-extremal Kerr shadow plot
- [ ] General apparent horizon finder for dynamical spacetimes — *deferred (would require a 2D nonlinear PDE solver)*
- [ ] Production-quality ray-shooting finder — *experimental version exists but is not exported; deferred until needed*

**Release:** v0.4.0 — tagged 2026-04-11.

---

## Phase 5 — Gravitational Waves (months 9-10)

**Status:** ✅ Done — shipped as v0.5.0 on 2026-04-11.

**Physics concepts:**
- Linear perturbations of Schwarzschild (Regge-Wheeler equation)
- Quasinormal modes (QNMs) and the radiating boundary conditions
- Leaver's 1985 continued-fraction method
- Ringdown waveforms and BH spectroscopy
- The no-hair theorem test

**Deliverables:**
- [x] `spacetime_lab.waves` module
- [x] QNM spectrum calculator for Schwarzschild — verified to ~1e-6 against Berti-Cardoso-Starinets 2009 Table 1
- [x] Time-domain ringdown waveform generator (`RingdownWaveform`)
- [x] Notebook: `05_quasinormal_modes.ipynb`
- [ ] Kerr QNMs — *deferred to a future patch (the underlying `qnm` package supports them; only the Spacetime Lab wrapper is missing)*
- [ ] Integration with Bilby/PyCBC for real LIGO data — *deferred*
- [ ] Ringdown fitter for observed events — *deferred*

**Release:** v0.5.0 — tagged 2026-04-11.

---

## Phase 6 — Quantum Information Basics (months 11-12)

**Status:** ✅ Done — shipped as v0.6.0 on 2026-04-11.

**Physics concepts:**
- Density matrices and the partial trace
- Von Neumann entropy and its bounds
- Schmidt decomposition via SVD
- Entanglement entropy of bipartite pure states
- Quantum mutual information

**Deliverables:**
- [x] `spacetime_lab.entropy` subpackage (pure numpy, no quimb dep)
- [x] `density_matrix`, `partial_trace`, `is_pure`, `is_density_matrix`
- [x] `von_neumann_entropy`, `mutual_information`
- [x] `schmidt_decomposition`, `schmidt_rank`, `entanglement_entropy`
- [x] Notebook `06_entanglement_entropy.ipynb` with closing gate
- [x] All canonical examples verified to machine precision: Bell pair = log 2, GHZ bipartitions = log 2, max mixed I_d/d = log d, product = 0, additivity, mutual info
- [x] 58 unit tests
- [ ] Integration with quimb for tensor-network states — *deferred until Phase 7+ when DMRG/MERA become physically motivated*
- [ ] Replica-trick entropy computation — *deferred (relevant for Phase 8 holographic computations)*

**Release:** v0.6.0 — tagged 2026-04-11.

---

## Phase 7 — AdS/CFT Foundations (months 13-14)

**Status:** ✅ Done — shipped as v0.7.0 on 2026-04-11.

**Physics concepts:**
- Anti-de Sitter geometry in Poincaré coordinates
- Constant negative curvature: `R_munu = -(n-1)/L^2 g_munu`
- Brown-Henneaux relation `c = 3 L / (2 G_N)`
- AdS_3 boundary geodesics as semicircles in the upper half-plane
- Ryu-Takayanagi formula `S = Length(geodesic) / (4 G_N)`
- Calabrese-Cardy 2D CFT entanglement entropy `S = (c/3) log(L_A/eps)`
- The simplest non-trivial check of holographic entanglement entropy

**Deliverables:**
- [x] `spacetime_lab.metrics.AdS` (Poincaré coordinates, multi-dimensional)
- [x] Numerical verification of Einstein constant curvature `R_munu = -(n-1)/L^2 g_munu` for AdS_3, AdS_4, AdS_5 (residual exactly zero)
- [x] `spacetime_lab.holography` subpackage: `geodesic_length_ads3`, `brown_henneaux_central_charge`, `ryu_takayanagi_ads3`, `calabrese_cardy_2d`
- [x] **Bit-exact verification** that `RT == CC` via Brown-Henneaux across 5+ parameter combinations
- [x] Notebook `07_ads_cft_foundations.ipynb` with closing gate cell
- [x] 55 unit tests pinned to closed-form invariants
- [ ] `spacetime_lab.metrics.BTZ` — *deferred to Phase 8 (BTZ thermodynamics + Hawking-Page)*
- [ ] CFT boundary observables (operator dimensions, OPE coefficients) — *deferred*
- [ ] GKP-Witten prescription for boundary correlators — *deferred*

**Release:** v0.7.0 — tagged 2026-04-11.

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
