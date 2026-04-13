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

## Phase 8 — Holographic Depth (months 15-16)

**Status:** ✅ Done — shipped as v0.8.0 on 2026-04-11.

**Physics concepts:**
- BTZ black hole as a quotient of AdS_3
- BTZ thermodynamics (Hawking T, Bekenstein-Hawking entropy, first law)
- Strominger 1998: BTZ entropy from CFT Cardy formula
- Finite-temperature Calabrese-Cardy entanglement entropy
- Two-interval RT phase transition (Headrick 2010)
- Holographic mutual information kink at cross-ratio = 1/2

**Deliverables:**
- [x] `spacetime_lab.metrics.BTZ` (non-rotating, uncharged)
- [x] BTZ verified locally AdS_3 (Einstein-constant residual ~ 0)
- [x] `spacetime_lab.holography.btz` — `cardy_formula`,
      `thermal_calabrese_cardy`, `geodesic_length_btz`,
      `ryu_takayanagi_btz`, `verify_strominger_btz_cardy`,
      `verify_btz_against_thermal_calabrese_cardy`
- [x] `spacetime_lab.holography.two_interval` — `cross_ratio`,
      `two_interval_*`, `critical_separation_for_phase_transition`
- [x] **Bit-exact verification**:
      Strominger BTZ vs Cardy across 6 parameter combinations,
      finite-T RT vs CC across 6 parameter sets,
      critical gap = `sqrt(2) - 1` for unit equal intervals,
      cross-ratio at critical = exactly 1/2,
      mutual information = exactly 0 in disconnected phase
- [x] Notebook `08_holographic_phase_transitions.ipynb`
- [x] 63 unit tests
- [ ] Rotating BTZ (with inner horizon and ergoregion) — *deferred*
- [ ] Numerical bulk minimal-surface finder for higher-dimensional AdS
      — *deferred to v0.8.1 or v0.9.0 patch when needed*
- [ ] HRT (covariant Ryu-Takayanagi) for time-dependent backgrounds
      — *deferred*

**Release:** v0.8.0 — tagged 2026-04-11.

---

## Phase 9 — Island formula and the Page curve (months 17-18)

**Status:** ✅ Done — shipped as v1.0.0 on 2026-04-11.

**Physics concepts:**
- The Hawking information paradox
- Don Page's 1993 prediction for the unitary curve
- The island formula as a `min` over candidate quantum extremal surfaces
- Hartman-Maldacena 2013: linear-growth saddle in eternal BTZ
- Eternal-BH Page curve: rises linearly, saturates at `2 S_BH`
- Connection to the two-interval phase transition (same `min` structure)

**Deliverables:**
- [x] `spacetime_lab.holography.island` subpackage with the closed-form Hartman-Maldacena saddle and the island saddle
- [x] `page_curve` and `page_time` helpers (numerical root finding via `scipy.optimize.brentq`)
- [x] `verify_page_curve_unitarity` gate function with full diagnostics
- [x] Notebook `09_island_formula.ipynb` with the headline Page curve plot
- [x] 41 unit tests pinned to closed-form invariants
- [x] **Bit-exact verification**: continuity at the Page time, Page time independent of `G_N`, monotonicity of the Page curve, qualitative shape (trivial early, island late)
- [x] Evaporating-BH Page curve (toy model: Page 1976 + island saddle) — *shipped as v1.1.0 on 2026-04-11*
- [ ] Numerical quantum extremal surface finder — *deferred to v2.0*
- [ ] Replica wormhole derivation — *not implementable in code*

**Release:** **v1.0.0** 🚀 — tagged 2026-04-11.

**This is the v1.0 milestone.** The complete project arc from
Schwarzschild to the resolution of the Hawking information paradox
is now in one unified codebase.

---

## v1.1 patch — Evaporating Schwarzschild Page curve

**Status:** ✅ Done — shipped as v1.1.0 on 2026-04-11.

First post-v1.0 patch.  Extends the eternal-BH island formula module
to a real evaporating BH and ships the bell-shaped Page curve that
returns to zero at `t_evap` (toy-model unitarity).

**Physics concepts added:**
- Schwarzschild evaporation law (Page 1976): `t_evap = 5120 π G² M_0³`
- Cubic shrinking law `M(t) = M_0 (1 - t/t_evap)^(1/3)`
- No-island Hawking saddle `S_H(t) = S_BH(0) - S_BH(t)`
- QES saddle `S_island(t) = S_BH(t)` (the *current* horizon area)
- Closed-form Page time `t_P = (1 - √2/4) t_evap ≈ 0.6464 t_evap`
- Maximum entropy `S_rad,max = S_BH(0)/2 = 2π M_0²`

**Deliverables:**
- [x] `spacetime_lab.holography.evaporating` subpackage
- [x] Closed-form `page_time_evaporating` + numerical `brentq` cross-check
- [x] `verify_evaporating_unitarity` gate function
- [x] Notebook `10_evaporating_page_curve.ipynb` with bell-curve headline plot and side-by-side comparison vs Phase 9 eternal-BH curve
- [x] 37 new tests pinned to closed-form invariants (suite: 472 → **509 passing**)
- [x] **Bit-exact verification**: endpoint zeros, Page time closed form vs numerical, mass at Page time, saddle continuity, max entropy, bell-shape monotonicity

**Honest scope deferred to v2.0:** JT gravity + CFT bath, real QES finder, replica wormholes, backreaction, grey-body factors.

**Release:** **v1.1.0** 🚀 — tagged 2026-04-11.

---

## v1.2 patch — Kerr QNM wrapper

**Status:** ✅ Done — shipped as v1.2.0 on 2026-04-12.

Second v1.x patch.  Exposes Kerr QNMs through the Spacetime Lab
`waves` subpackage by wrapping Stein's `qnm` package's cache-based
Kerr front-end.

**Physics concepts added:**
- Kerr `m`-splitting: each `(l, n)` slot gives `2l + 1` frequencies
- Prograde (`m > 0`) modes are less damped than retrograde (`m < 0`)
- BH spectroscopy as a test of the no-hair theorem
- Schwarzschild `m`-degeneracy recovered at `a = 0`

**Deliverables:**
- [x] `kerr_qnm(l, m, n, a_over_M, s)` front-end in `spacetime_lab.waves`
- [x] `QNMResult` extended with optional `m` and `a_over_M` fields (backward-compatible)
- [x] Notebook `11_kerr_qnm_spectroscopy.ipynb` with Berti-Cardoso-Starinets Fig 2 reproduction + BH spectroscopy demo
- [x] 26 new tests (suite: 509 → **535 passing**)
- [x] **Bit-exact verification**: qnm-docs anchor pinned at 1e-10, Schwarzschild limit cross-check at ~6e-16 (bit-exact between two independent qnm code paths)

**Honest scope deferred:** Kerr-Newman (different solver), time-domain Kerr ringdown (trivially composable), Teukolsky `A` eigenvalue (not stored in `QNMResult`), superradiant bound states.

**Release:** **v1.2.0** 🚀 — tagged 2026-04-12.

---

## v1.3 patch — Rotating BTZ + ergoregion + rotating Strominger

**Status:** ✅ Done — shipped as v1.3.0 on 2026-04-12.

Third v1.x patch.  Extends the Phase 8 non-rotating BTZ module to
the full two-parameter `(M, J)` family.

**Physics concepts added:**
- Two horizons `r_±`, extremal limit `|J| ≤ ML`
- Hawking temperature `T_H` vanishing at extremality
- Horizon angular velocity `Ω_H` approaching `1/L` at extremal
- Ergoregion `r_+ < r < √(8 G_N L² M)` (frame-dragging forces observers to co-rotate)
- First law `dM = T_H dS + Ω_H dJ` and Smarr 2+1D `M = ½ T_H S + Ω_H J`
- Asymmetric chiral Virasoro towers `L_0 = (LM + |J|)/2 ≠ L̄_0 = (LM - |J|)/2`
- Rotating Strominger-Cardy match: `S_Cardy^L + S_Cardy^R = S_BH` with the `r_-` contributions cancelling bit-exactly

**Deliverables:**
- [x] `spacetime_lab.holography.btz_rotating` subpackage (13 new public functions)
- [x] Notebook `12_rotating_btz.ipynb` with `(M, J)` phase diagram, approach-to-extremality sweeps, ergoregion cartoon, rotating Strominger bar plot
- [x] 34 new tests (suite: 535 → **569 passing**)
- [x] **Bit-exact verification**: Smarr residual `0.0`, rotating Strominger-Cardy residual `0.0`, horizon round-trip `~1e-16`, first-law centered finite-difference `~1e-11`

**Honest scope deferred:** RT surfaces in rotating BTZ (v1.0 `btz.py` RT machinery is non-rotating only), superradiance, chiral CFT with `c_L ≠ c_R` (would need gravitational Chern-Simons), exact extremal limit (singular).

**Release:** **v1.3.0** 🚀 — tagged 2026-04-12.

---

## v1.5 patch — SVG and TikZ Penrose renderers

**Status:** ✅ Done — shipped as v1.5.0 on 2026-04-12.

Fourth v1.x patch.  Implements the SVG and TikZ backends that
Phase 2 (v0.2.0) left as `NotImplementedError` stubs.  Pure-string
output, no runtime deps, shared kind-to-style mapping with the
already-shipped matplotlib backend.

**Capabilities added:**
- Standalone `<svg>...</svg>` document with `kind-{kind}` CSS groups
- TikZ `tikzpicture` snippet with optional `standalone` document preamble for direct `pdflatex` compilation
- Browser-portable Unicode `ℐ` for `\mathscr{I}` in SVG; full LaTeX math in TikZ
- `PathStyle.stroke` and `width` override the kind default in both backends; hex colours translated to TikZ `rgb,255:` spec
- Empty scene tolerated (placeholder canvas, no crash)

**Deliverables:**
- [x] `render_svg` and `render_tikz` in `spacetime_lab.diagrams.render`
- [x] Notebook `13_penrose_renderers.ipynb` with Minkowski + Schwarzschild rendered to all three backends + live CSS theming demo
- [x] 29 new tests pinned to structural invariants (suite: 569 → **598 passing**)
- [x] **All gates pass exactly**: well-formed XML, kind grouping consistent across backends, infinity counts match, dasharray inheritance, override behaviour, hex → TikZ rgb conversion

**Honest scope deferred:** PNG/PDF rasterisers (downstream tools), interactive SVG (frontend concern), full LaTeX-in-SVG glyph fidelity, embedded Penrose backend.

**Release:** **v1.5.0** 🚀 — tagged 2026-04-12.

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
