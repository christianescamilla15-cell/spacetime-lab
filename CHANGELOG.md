# Changelog

All notable changes to Spacetime Lab are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] — 2026-04-11 — Phase 5: Quasinormal modes + ringdown

Fifth substantive release. Closes Phase 5 of the 18-month
[ROADMAP](./ROADMAP.md). Spacetime Lab now has Schwarzschild
quasinormal mode finders and a time-domain ringdown waveform
generator — the canonical 'ringtone' of a perturbed black hole and
the basis for the no-hair theorem test that LIGO/Virgo runs on
every binary merger.

### Added

- `spacetime_lab.waves` — new subpackage:
  - `leaver_qnm_schwarzschild(l, n, s=-2)` — returns the complex
    QNM frequency `M*omega` for a Schwarzschild black hole.  Thin
    wrapper over Stein's `qnm` package
    (`pip install qnm`, JOSS 4 1683, arXiv:1908.10377), which is
    the canonical Python implementation of Leaver's 1985
    continued-fraction method via the Cook-Zalutskiy 2014 form.
  - `QNMResult` dataclass holding the complex frequency, the CF
    truncation error (typically ~1e-16) and the number of CF
    terms used.
  - `RingdownMode` dataclass for a single damped sinusoid
    (frequency, amplitude, phase).
  - `RingdownWaveform(mass, modes)` — pure-Python time-domain
    waveform generator: sum of damped sinusoids
    `h(t) = sum_i A_i cos(omega_R^i (t - t_0) + phi_i)
                    exp(-omega_I^i (t - t_0))`.
    Includes diagnostics `fundamental_period()` and
    `longest_damping_time()`.
- `notebooks/05_quasinormal_modes.ipynb` — Phase 5 concept + demo
  notebook.  Walks through linear perturbations, Regge-Wheeler,
  the radiating boundary conditions that make QNMs complex,
  Leaver's continued-fraction method, verification against
  Berti et al 2009 Table 1, the QNM tower (4 overtones), higher
  multipoles, ringdown waveform generation with single and
  multi-mode superposition, and the no-hair theorem test.
  Closing gate cell hard-asserts every claim including all three
  Berti et al reference values.
- Optional dependency `qnm>=0.4` via the new `[waves]` extra in
  `pyproject.toml`.  Install with `pip install spacetime-lab[waves]`.

### Tests

- `tests/test_waves.py` — 25 new tests:
  - `QNMResult` dataclass construction
  - Argument validation (`l < |s|`, `n < 0`)
  - **Hard-pinned to Berti, Cardoso & Starinets 2009 Table 1**:
    `(l=2, n=0)`, `(l=2, n=1)`, `(l=3, n=0)` to ~1e-4 (limited by
    the 5-decimal precision of the published table)
  - Sign convention: `Im(omega) < 0` for damped modes
  - Higher overtones damp faster
  - Higher multipoles oscillate faster
  - Internal CF convergence to ~1e-12 or better
  - `RingdownMode` and `RingdownWaveform` validation
  - Strain at `t = 0` matches `sum of amplitudes`
  - Strain after one period matches `A * exp(-omega_I * T)` to 1e-6
  - Mass scaling: doubling `M` doubles the period
  - Phase offset: `cos(pi/2)` gives `h(0) = 0`
  - Multi-mode superposition
  - End-to-end pipeline: `leaver_qnm_schwarzschild` ->
    `RingdownMode` -> `RingdownWaveform.evaluate`
- Total project test suite: **255 tests** passing (up from 230 in
  v0.4.0; +25 waves).

### Honest scope notes

- **The QNM finder is a wrapper, not a from-scratch implementation.**
  The Leaver recurrence coefficients have at least three
  different sign / spin-weight conventions floating around the
  literature, and our first attempt to write them from memory
  failed verification at the canonical Berti et al value
  `M*omega = 0.37367 - 0.08896 i` (off by ~20%).  Rather than
  blindly tune signs we chose to wrap Stein's `qnm` package,
  which is verified against published tables to ~1e-16 and is
  the canonical reference implementation.  This is the same
  honest-scope decision pattern used in Phase 4 (the experimental
  ray-shooting horizon finder) and Phase 3 (the Killing-tensor
  matrix stub).  A from-scratch implementation may land in a
  future patch when we are willing to invest the time to derive
  the coefficients via a sympy reduction of Regge-Wheeler.
- **Kerr QNMs are not yet exposed.** `qnm` provides them and a
  Spacetime Lab wrapper will land in a future patch.  The
  Schwarzschild case verifies the entire pipeline against
  published tables and demonstrates every concept needed for
  the Phase 5 deliverables.
- **`RingdownWaveform` is pure Spacetime Lab code.**  No
  dependency on `qnm`; users can supply any list of
  `RingdownMode` objects (e.g. hardcoded literature values, or
  Kerr modes from another solver).

## [0.4.0] — 2026-04-11 — Phase 4: Horizon finders + photon shadow

Fourth substantive release. Closes Phase 4 of the 18-month
[ROADMAP](./ROADMAP.md). Spacetime Lab now has numerical horizon
finders and the Bardeen 1973 photon shadow generator — the same
shadow geometry that EHT measured for M87* in 2019 and Sgr A* in 2022.

### Added

- `spacetime_lab.horizons` — new subpackage with three production
  finders, all pinned to closed-form values from Phases 1-3:
  - `find_event_horizon(metric, ...)` — locates the outer event
    horizon by sign-change scan + Brent's method on `g_rr` along
    the equatorial slice. Falls back to a parabolic-touch
    detection for the extremal Kerr case where the two horizons
    merge. Generic over any axisymmetric stationary metric in
    `spacetime_lab.metrics`. Verified to ~`1e-9` against
    Schwarzschild (`r = 2M`) and Kerr (`r_+ = M + sqrt(M^2 - a^2)`)
    over a wide range of masses and spins.
  - `find_isco_numerical(metric, ...)` — locates the equatorial
    ISCO by simultaneously root-finding on
    `V_eff'(r; L) = V_eff''(r; L) = 0`. Uses sympy to differentiate
    the metric's `effective_potential` and `scipy.optimize.fsolve`
    to solve the 2x2 system. Currently only Schwarzschild
    implements `effective_potential`; for Kerr the closed-form
    `Kerr.isco()` from v0.3.0 should be used. Verified to ~`1e-7`
    against `r = 6M` for Schwarzschild over multiple masses.
  - `photon_shadow_kerr(spin, mass, ...)` — returns the closed
    Bardeen 1973 shadow boundary `(alpha, beta)` in the observer's
    image plane. Uses the parametric form via the spherical photon
    orbits' conserved quantities `xi(r_p)` and `eta(r_p)`. The
    full `csc theta_o` / `cot theta_o` formulas are implemented,
    but the test suite only pins the equatorial-observer case
    (the EHT geometry). Verified to ~`1e-2` against the
    Schwarzschild limit `b_crit = 3 sqrt(3) M`.
- `spherical_photon_orbit_xi(r_p, M, a)` and
  `spherical_photon_orbit_eta(r_p, M, a)` — closed-form helpers
  for the conserved impact parameters of a Kerr spherical photon
  orbit at radius `r_p`. Used internally by `photon_shadow_kerr`
  but exported for direct access.
- `kerr_critical_curve_xi_eta(M, a, n_points)` — sample the
  `(r_p, xi, eta)` curve over the photon-region range
  `[r_p^prograde, r_p^retrograde]`.
- `find_event_horizon_via_shooting` — experimental ray-shooting
  finder using `GeodesicIntegrator`. Documented but **not exported**
  from the package and **not relied on by tests**, because the
  event horizon is the asymptote of geodesic motion in affine
  parameter and any finite integration window gives a biased
  estimate. Kept in the codebase as a starting point for a future
  smarter implementation with adaptive affine reparametrisation.
- `notebooks/04_horizon_topology.ipynb` — Phase 4 concept + demo
  notebook. Walks through the three notions of horizon, the
  rediscovery cross-validation against Schwarzschild and Kerr
  closed forms, the Schwarzschild critical impact parameter, and
  the Bardeen 1973 photon shadow with the headline near-extremal
  Kerr image. Closing gate cell hard-asserts every claim.

### Tests

- `tests/test_horizons.py` — 36 new tests:
  - `find_event_horizon` against Schwarzschild `r = 2M` (5 masses),
    Kerr `r_+` (7 spins), extremal `r_+ = M`, multi-mass + multi-spin
    combinations, and bracket-failure error path
  - `find_isco_numerical` against Schwarzschild `r = 6M` (4 masses),
    plus the AttributeError raised when called on Kerr (which has
    no `effective_potential`)
  - `spherical_photon_orbit_xi/eta` zero-spin error path and the
    `eta = 0` boundary at the equatorial photon-sphere endpoints
  - `photon_shadow_kerr` zero-spin and `spin > mass` error paths,
    closed-curve property, Schwarzschild limit (`b -> 3 sqrt 3`),
    centred at origin for tiny spin, asymmetric for extremal,
    frame-drag shift, linear scaling with mass
- Total project test suite: **230 tests** passing (up from 194 in
  v0.3.0; +36 horizons).

### Cross-validation

The point of Phase 4 is end-to-end **rediscovery**: every textbook
closed-form value should pop out of the numerical finder applied to
only the metric implementation. The test suite verifies:

- Schwarzschild outer horizon at `r = 2M` to ~`1e-9`
- Kerr outer horizon at `r_+ = M + sqrt(M^2 - a^2)` to ~`1e-9` for
  6 sub-extremal spins, ~`1e-6` at extremal
- Schwarzschild ISCO at `r = 6M` to ~`1e-7`
- Schwarzschild critical impact parameter `b_crit = 3 sqrt(3) M`
  to ~`1e-2` (this last one limited by the parametric formula
  becoming singular as `a -> 0`)

If any of these had failed, we would know exactly which layer of
the stack was broken: the metric tensor (Phase 1/3), the inverse
metric, or the finder itself.

### Notes

- The general-inclination Bardeen formulas are implemented but the
  test suite only pins the equatorial observer case `theta_o = pi/2`
  to known closed-form values. The EHT geometry for both M87* and
  Sgr A* is nearly equatorial.
- A general apparent-horizon finder for dynamical spacetimes
  requires solving a nonlinear elliptic PDE on a 2-sphere — not
  in scope for v0.4.0. For stationary spacetimes the apparent and
  event horizons coincide and `find_event_horizon` returns both.
- The ray-shooting finder is documented but not production-quality.
  See `find_event_horizon_via_shooting` for the explanation.

## [0.3.0] — 2026-04-11 — Phase 3: Kerr geodesics

Third substantive release.  Closes Phase 3 of the 18-month
[ROADMAP](./ROADMAP.md).  Spacetime Lab now has a working Kerr metric
and a symplectic geodesic integrator that experimentally verifies the
existence of Carter's irreducible Killing tensor by conserving its
constant along integrated trajectories.

### Added

- `spacetime_lab.metrics.Kerr` — full Boyer-Lindquist Kerr metric
  parametrised by `(mass, spin)` with cosmic-censorship validation
  `0 <= spin <= mass`.  Symbolic line element with the off-diagonal
  `g_{t phi}` frame-dragging term, plus all the physical observables:
  - `outer_horizon` (`r_+`) and `inner_horizon` (`r_-`) — both real
    iff `a <= M`; the inner Cauchy horizon is the new feature with
    no Schwarzschild analogue
  - `ergosphere(theta)` — the static-limit surface, bulging out to
    `2M` at the equator
  - `isco(prograde)` — Bardeen-Press-Teukolsky 1972 closed form with
    the `Z_1`, `Z_2` helpers, prograde (smaller) and retrograde
    branches
  - `photon_sphere_equatorial(prograde)` —
    `2M[1 + cos(2/3 arccos(-+ a/M))]`
  - `angular_velocity_horizon`, `horizon_area`, `surface_gravity`,
    `hawking_temperature`, `bekenstein_hawking_entropy`
  - `verify_vacuum_numerical()` — strong test of the line element
    via `R_{munu} = 0`, computed numerically (max ~1e-15) so it
    finishes in seconds rather than minutes
- `spacetime_lab.geodesics` — new subpackage:
  - `GeodesicState` dataclass holding 4-position `x` and covariant
    4-momentum `p` (in that order, since cyclic-coordinate
    conservation laws are statements about `p_mu`)
  - `GeodesicIntegrator` — implicit-midpoint symplectic integrator
    for Hamilton's equations on `H = (1/2) g^{munu}(x) p_mu p_nu`.
    Symplectic, time-reversible, 2nd-order accurate, and works for
    non-separable Hamiltonians (which Kerr's is).  Lambdifies the
    inverse metric and its derivatives once at construction.
- `Kerr.carter_constant(E, L_z, p_theta, theta, mu_squared)` and
  `Kerr.carter_constant_from_state(state)` — the irreducible
  Killing-tensor invariant in its polynomial form
  `Q = p_theta^2 + cos^2(theta) [a^2(mu^2 - E^2) + L_z^2/sin^2(theta)]`.
  This is the *practical* form of Carter's constant — it is what
  the integrator's conservation diagnostic uses.
- `Kerr.constants_of_motion(state)` — convenience method that
  returns `{E, L_z, mu_squared, Q}` for any geodesic state, so test
  suites and notebooks can compare drift across all four conserved
  quantities at once.
- `notebooks/03_kerr_geodesics.ipynb` — Phase 3 concept + demo
  notebook.  Walks through Kerr line element, three surfaces
  (horizons + static limit), prograde/retrograde ISCO and photon
  sphere, vacuum verification, Hamilton's equations, the implicit
  midpoint method, conservation diagnostics, and a quadratic
  convergence test in `h`.  Closing "Phase 3 gate" cell hard-asserts
  every claim.

### Tests

- `tests/test_kerr.py` — 59 unit tests for the Kerr metric class.
  See v0.2.0 changelog entry; this set was actually committed with
  v0.2.x but ships as part of v0.3.0.
- `tests/test_geodesics_kerr.py` — 26 new tests covering:
  - `GeodesicState` dataclass shape, validation, copy semantics,
    array independence
  - `GeodesicIntegrator` construction, step, integrate API
  - **Killing-vector exact conservation**: `E` and `L_z` drift by
    less than `1e-12` over 200 steps
  - **Symplectic mass-shell conservation**: `H` drift bounded
    over 200 steps
  - **Quadratic convergence in step size**: halving `h` reduces
    drift by a factor of 4 in both `H` and Carter's `Q`
  - **Carter's constant closed-form**: `Q = 0` for equatorial
    orbits, axis singularity raises, Schwarzschild limit reduces
    to `L_perp^2`
  - **Carter's constant conservation along geodesics** at the same
    order as the Hamiltonian
- Total project test suite: **194 tests** passing (up from 109 in
  v0.2.0; +59 Kerr metric and +26 geodesic integrator).

### Notes

- The integrator uses **implicit midpoint** rather than leapfrog
  because Kerr's Hamiltonian is non-separable
  (`g^{munu}(x) p_mu p_nu` depends on `x` through the inverse
  metric).  Implicit midpoint is symplectic for non-separable
  Hamiltonians and exactly conserves cyclic-coordinate momenta.
- `verify_vacuum_numerical()` was forced to be numerical rather
  than symbolic because `sympy.simplify` is pathologically slow on
  Kerr expressions (>5 minutes per Ricci component).  The
  numerical version evaluates `R_{munu}` at sample points via
  `lambdify` and runs in ~2 seconds.  This is the same trick that
  any future Kerr-Newman / RN extension will need.
- The explicit 4x4 Killing tensor matrix `K_{munu}` is left as a
  documented stub.  The integrator-conservation diagnostic only
  needs the polynomial form, and the matrix form is more book-
  keeping than physics.

## [0.2.0] — 2026-04-10 — Phase 2: Penrose diagrams

Second substantive release. Closes Phase 2 of the 18-month
[ROADMAP](./ROADMAP.md). Spacetime Lab now has a working Penrose
diagram pipeline: chart -> Scene -> matplotlib renderer, with
Minkowski and Schwarzschild as concrete charts.

### Added

- `spacetime_lab.diagrams` submodule with:
  - `PenroseChart` — abstract base class. Subclasses define a
    two-way map between physical coordinates and compactified null
    coordinates `(U, V)` in the diamond `[-pi/2, pi/2]^2`, plus the
    boundary path and infinity metadata. The base class supplies
    `light_cone_at`, `map_curve`, and `to_scene` concrete methods
    built on top of the abstract primitives.
  - `MinkowskiPenrose` — 1+1 Minkowski spacetime.
    `(t, x) -> (arctan(t - x), arctan(t + x))`. Four boundary edges
    (the square) and eight infinities: `i+`, `i-`, two `i0` (left
    and right), and four disjoint `scri+/-` midpoints.
  - `SchwarzschildPenrose(mass)` — full four-region maximally
    extended Schwarzschild spacetime. Forward map via
    Eddington-Finkelstein -> Kruskal -> `arctan` with region-
    dependent sign conventions (Carroll). Inverse map via the
    Lambert `W_0` function. Returns 10 boundary paths (4 `scri`
    edges, 4 horizon null lines meeting at the bifurcation sphere,
    2 singularity segments) and 10 infinities (5 per exterior
    region). The singularity segments are genuinely straight lines
    in compactified coordinates because `tan(U) tan(V) = 1` is
    equivalent to `U + V = pi/2` on the admissible domain.
  - Small chart-agnostic dataclasses (`Vec2`, `PathStyle`, `Path`,
    `Infinity`, `Scene`) that form the wire format between charts
    and renderers.
- `spacetime_lab.diagrams.render.render_matplotlib` — matplotlib
  backend that renders any `Scene` onto an `Axes`. Rotates `(U, V)`
  into the conventional `(T, X)` orientation (time up, space
  right), groups paths by `kind` with per-kind default styles
  (solid boundaries, dashed horizons, dashed red singularities,
  green light cones, orange world lines), and places LaTeX-
  formatted infinity labels (`i^+`, `\mathscr{I}^-`, etc.) via
  `ax.annotate` with a radial outward nudge.
- `spacetime_lab.diagrams.render.render_svg` and
  `spacetime_lab.diagrams.render.render_tikz` — stubs, to be
  implemented when the web frontend and LaTeX paper workflow need
  them.
- `notebooks/02_penrose_diagrams.ipynb` — Phase 2 concept + demo
  notebook. Walks through conformal compactification, the Minkowski
  diamond, the Schwarzschild four-region construction (with a
  direct numerical verification that the singularity is straight),
  and overlays static observers at several `r` values. Closing
  "Phase 2 gate" cell hard-asserts every physical claim.

### Tests

- `tests/test_diagrams_minkowski.py` — 33 tests covering metadata,
  forward and inverse maps, asymptotic limits (`i+`, `i-`, `i0`),
  round trips, boundary and infinity structure, and all derived
  methods (`light_cone_at`, `map_curve`, `to_scene`).
- `tests/test_diagrams_schwarzschild.py` — 50 tests covering
  metadata and per-region domain validation, sign quadrants for
  the four regions, asymptotic limits of `i+/-/0`, singularity
  approach (`U + V -> +/- pi/2`), horizon approach, round trips in
  every region, boundary and infinity structure, and geometric-
  units mass scale invariance.
- Total suite: **109 tests** passing (up from 26 in v0.1.0).

### Notes

- Convention for Schwarzschild `scri+/-` labels in Region III: the
  *global* arrow of time runs upward in `(T, X)`, so `scri+(III)`
  is the upper-left null edge and `scri-(III)` is the lower-left
  edge, not the reverse. Region III's local Schwarzschild `t`
  coordinate runs in the opposite sense but this is purely a
  coordinate artefact.
- 1+1 Minkowski has **two** spatial infinities (left and right),
  contrary to the usual 3+1 convention where `i0` is a single
  point. This is because `x` runs over `R`, not over a half-line.

## [0.1.0] — 2026-04-10 — Phase 1: Schwarzschild foundations

First substantive release. Closes Phase 1 of the 18-month
[ROADMAP](./ROADMAP.md).

### Added

- `spacetime_lab.metrics.base.Metric` — abstract base class for Lorentzian
  metrics. Provides cached symbolic machinery for the inverse metric,
  Christoffel symbols, Riemann / Ricci tensors, Ricci scalar and
  Kretschmann scalar, plus numerical evaluation via `metric_at(**coords)`.
- `spacetime_lab.metrics.schwarzschild.Schwarzschild` — full implementation
  of the Schwarzschild solution in Schwarzschild coordinates
  `(t, r, theta, phi)` with signature `(-,+,+,+)` and geometric units
  `G = c = 1`. Includes:
  - `event_horizon()`, `isco()`, `photon_sphere()` (the three canonical radii)
  - `kretschmann_scalar(r)` and `kretschmann_scalar_at_horizon()`
  - `tortoise_coordinate(r)` with `r* -> -infty` at the horizon
  - `effective_potential(r, L, particle_type)` for massive and null geodesics
  - `kruskal_coordinates(t, r, region)` for Regions I and II of the
    maximally extended spacetime
  - `christoffel_symbols_explicit()` — the 13 non-zero components in
    closed form
  - `verify_christoffel_symbols()` — sanity check of the explicit
    formulas against the base-class symbolic computation
  - `surface_gravity()`, `hawking_temperature()`,
    `bekenstein_hawking_entropy()` (horizon thermodynamics preview)
  - `line_element_latex()` — canonical LaTeX rendering
- 26 pytest tests in `tests/test_schwarzschild.py` covering every
  method above.
- `notebooks/01_schwarzschild_basics.ipynb` — Phase 1 concept notebook
  interleaving narrative, LaTeX, and direct calls into the API, with a
  closing "Phase 1 gate" cell that asserts every physics claim. Runs
  end-to-end against the current implementation.

### Upstream contributions

Eight pull requests opened against
[`bilby-dev/bilby`](https://github.com/bilby-dev/bilby) as part of the
Phase 1 "learn by shipping" track. See the
[Upstream contributions section of the README](./README.md#upstream-contributions)
for the full list with links.

### Notes

- Signature convention: `(-,+,+,+)` (Wald).
- Units: `G = c = 1` throughout. Mass, time and length all have the same
  dimension in this system.
- All claims in the Phase 1 notebook are verified by the accompanying
  assert block; if anything regresses the notebook will fail loudly.
