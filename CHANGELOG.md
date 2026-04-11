# Changelog

All notable changes to Spacetime Lab are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
