# Changelog

All notable changes to Spacetime Lab are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.5.0] — 2026-04-12 — v1.5 patch: SVG and TikZ Penrose renderers

Fourth v1.x patch.  Phase 2 (v0.2.0) shipped the matplotlib backend
for Penrose diagrams but left `render_svg` and `render_tikz` as
stubs raising `NotImplementedError`.  v1.5 implements both as pure
strings with no runtime dependency, sharing a kind-to-style table
with the matplotlib backend so all three produce visually
consistent diagrams from the same `Scene`.

### Added

- `spacetime_lab.diagrams.render.render_svg(scene, width, height,
  padding, show_labels, label_offset)` — pure-string SVG renderer:
  - Standalone `<svg>...</svg>` document, ready to write to file
    or embed in HTML
  - Paths grouped into `<g class="kind-{kind}">` so frontend CSS
    can re-skin entire categories without parsing `<path>` attrs
  - Configurable canvas + padding; auto-fitted bounding box with
    margin
  - Infinities rendered as `<text>` with Unicode `ℐ` for
    `\mathscr{I}` (browser-portable, no LaTeX engine required)
  - Empty scene yields a valid placeholder, not a crash
- `spacetime_lab.diagrams.render.render_tikz(scene, scale,
  show_labels, label_offset, standalone)` — pure-string TikZ
  renderer:
  - LaTeX `tikzpicture` snippet, ready to paste into a document
    that loads `\usepackage{tikz}`
  - `standalone=True` wraps in a `\documentclass{standalone}`
    preamble for `pdflatex` direct compilation
  - Infinities mapped to `\mathscr{I}^{\pm}` / `i^{\pm,0}` LaTeX
    math
  - Hex colours from `PathStyle` translated to TikZ `rgb,255:`
    spec; default kind colours use named `xcolor` tokens
- `notebooks/13_penrose_renderers.ipynb` — concept + Minkowski and
  Schwarzschild rendered to all three backends + CSS theming demo
  (paper-white and dark mode skinning the same SVG via stylesheets)
  + closing structural-invariants gate cell
- `tests/test_phase_v1_5.py` — 29 new tests pinned to structural
  invariants (envelope shape, well-formed XML, kind grouping,
  infinity count, dasharray inheritance, override behaviour,
  cross-backend consistency).  Suite: **569 → 598 passing**.

### Verified

| Invariant | Tolerance |
|---|---|
| SVG output is well-formed XML (parseable by `xml.etree`) | exact |
| Each `Path.kind` produces one `<g class="kind-{kind}">` group / `% --- {kind} ---` TikZ comment | exact |
| Each `Infinity` produces exactly one `<text>` / `\node` | exact |
| Horizons emit `stroke-dasharray` (SVG) and `dashed` (TikZ) | exact |
| Boundaries emit no dasharray | exact |
| `PathStyle.stroke` overrides the kind default in both backends | exact |
| Hex colour `#abcdef` → SVG literal + TikZ `rgb,255:red,171;green,205;blue,239` | exact |
| `standalone=True` wraps the TikZ in `\documentclass{standalone}` ... `\end{document}` | exact |
| Empty scene does not crash | exact |
| Cross-backend: `svg.count('<path ') == tz.count(r'\\draw[') == len(scene.paths)` | exact |

### Implementation notes

The shared kind-to-style table now lives in `render.py` as two
constants `_KIND_STYLE_SVG` and `_KIND_STYLE_TIKZ`, ensuring all
three backends agree on stroke colour and dash behaviour per kind.
The matplotlib backend's `kind_defaults` dict was already aligned
with these values from Phase 2; the v1.5 patch did not need to
modify it.

The SVG dasharray uses simple two-number patterns (`6 4` for
horizons, `3 3` for singularities, `1 3` for guides) so they
render consistently across browsers without depending on
`stroke-dashoffset` defaults.

### Honest scope deferred

- **PNG / JPEG / PDF rasterisers** — these belong downstream
  (browser SVG renderer, `rsvg-convert`, `pdflatex`)
- **Interactive SVG** — clicks, hovers, animation hooks belong
  to the frontend, not this Python package
- **Full LaTeX glyph fidelity in SVG** — SVG cannot embed
  arbitrary LaTeX; we use Unicode `ℐ` for `\mathscr{I}`, which is
  browser-portable and visually clean
- **Embedded Penrose backend** (penrose.cs.cmu.edu) — different
  ecosystem, different goals; out of scope

### Methodology

This was the most interface-heavy patch of the v1.x sprint, but
followed the same verify-before-code → bit-exact gate →
honest-scope-keeping pattern.  The "verify" step here was reading
the existing `render_matplotlib` for the kind-to-style mapping and
the `Scene` / `Path` / `Infinity` dataclasses in `penrose.py` to
pin the wire format before writing any of the new code.

## [1.3.0] — 2026-04-12 — v1.3 patch: Rotating BTZ + ergoregion + rotating Strominger

Third v1.x patch.  Extends the Phase 8 non-rotating BTZ module to
the full two-parameter `(M, J)` family: both horizons, Hawking
temperature and angular velocity, ergoregion between the outer
horizon and the static limit, first law and Smarr in 2+1D, and
the **rotating** Strominger 1998 derivation with asymmetric
left/right Virasoro weights.

### Added

- `spacetime_lab.holography.btz_rotating` — new module:
  - `rotating_btz_horizons(M, J, L, G_N)` — outer + inner
    radii `r_± = L√(4 G_N M (1 ± √(1-(J/ML)²)))`
  - `rotating_btz_mass_from_horizons(r_+, r_-, L, G_N)` and
    `rotating_btz_angular_momentum_from_horizons(...)` — the
    inverse mappings
  - `rotating_btz_hawking_temperature(M, J, L, G_N)` —
    `T_H = (r_+²−r_-²)/(2π r_+ L²)`.  Vanishes at extremality.
  - `rotating_btz_angular_velocity(M, J, L, G_N)` —
    `Ω_H = sign(J)·r_-/(r_+ L)`
  - `rotating_btz_entropy(M, J, L, G_N)` — `S_BH = π r_+/(2 G_N)`
  - `rotating_btz_ergoregion_bounds(M, J, L, G_N)` — inner
    bound `r_+`, outer bound `√(r_+² + r_-²) = √(8 G_N L² M)`
  - `extremal_bound_J(M, L)` → `ML`
  - `is_extremal(M, J, L, tol)` → bool
  - `strominger_rotating_btz_cardy(M, J, L, G_N)` — asymmetric
    chiral match, `L_0 = (LM+|J|)/2`, `L̄_0 = (LM-|J|)/2`,
    `c = 3L/(2 G_N)`, sum equals `S_BH` bit-exactly
  - `verify_first_law(M, J, L, G_N, h)` — finite-difference
    `(∂M/∂S)_J` vs `T_H` and `(∂M/∂J)_S` vs `Ω_H`
  - `verify_smarr_2plus1(M, J, L, G_N)` — `M = ½ T_H S + Ω_H J`
  - `verify_rotating_btz_thermodynamics(M, J, L, G_N, h)` —
    end-to-end gate bundling all of the above
- `notebooks/12_rotating_btz.ipynb` — concept + phase diagram `(M, J)`
  + approach-to-extremality curves for `T_H`, `Ω_H`, `S_BH` + ergoregion
  cartoon + first-law / Smarr verification + rotating Strominger
  bar plot + closing gate cell
- `tests/test_phase_v1_3.py` — 34 new tests.  Suite: **535 → 569
  passing**.

### Verified

| Invariant | Residual |
|---|---|
| `r_+² + r_-² = 8 G_N L² M` across `(M, J)` grid | `~1e-15` |
| `r_+ r_- = 4 G_N L \|J\|` across grid | `~1e-15` |
| Horizon ↔ `(M, J)` round-trip | `0.0` / `~1e-16` |
| `T_H = 0` at extremal `J = ML` | exact |
| `\|J\| > ML` raises `ValueError` | exact |
| `r_erg = √(8 G_N L² M)` (static limit) | exact |
| **First law** `dM = T_H dS + Ω_H dJ` (centered finite diff) | `~1e-11` rel |
| **Smarr 2+1D** `M = ½ T_H S + Ω_H J` | `0.0` |
| **Rotating Strominger-Cardy** `S_BH = S_L + S_R` across `(M, J)` grid | `0.0` |
| `J=0` limit matches Phase 8 non-rotating `verify_strominger_btz_cardy` | `0.0` |

### Physics highlights

- **Ergoregion exists only when `J ≠ 0`**: the static limit
  `r_erg = √(r_+² + r_-²)` is outside the outer horizon iff
  `r_- > 0`.  Non-rotating BTZ has no ergoregion.
- **`Ω_H → 1/L` at extremality**: the horizon angular velocity
  saturates at the AdS scale as `J → ML`.
- **Smarr identity in 2+1D has `1/2` coefficient** on the `T S`
  term (different from the 4D Smarr-Bardeen with `2`).  Derivable
  from Euler scaling; we check it bit-exactly.
- **The `r_-` cancellation in rotating Strominger** is the most
  physically satisfying part: `S_Cardy^L = π(r_+ + r_-)/(4 G_N)`
  and `S_Cardy^R = π(r_+ - r_-)/(4 G_N)`.  The sum is
  `π r_+/(2 G_N) = S_BH`; the `r_-` contributions cancel between
  the two chiralities to leave the area of the *outer* horizon
  alone as the total entropy.

### Honest scope deferred

- **Geodesics and RT surfaces in rotating BTZ** — the existing
  `btz.py` Phase 8 RT machinery only handles the non-rotating
  limit; rotating RT requires treating the inner horizon and
  handling complex geodesics
- **Superradiance** — we do not study scalar / gravitational
  perturbations in rotating BTZ
- **Chiral CFT with `c_L ≠ c_R`** — Einstein gravity keeps them
  equal; gravitational Chern-Simons would split them
- **Exact extremal limit `J = ML`** — handled as "near-extremal"
  with the bound check; the exact `r_+ = r_-` state is analytically
  subtle and can give `0/0` forms

### Methodology

Same verify-before-code → bit-exact gate → honest-scope-keeping
discipline.  Strominger 1998 was pinned via WebFetch to arXiv
hep-th/9712251: confirmed `M = (L_0 + L̄_0)/L`, `J = L_0 - L̄_0`,
single central charge `c = 3L/(2 G_N)` applies to both chiralities,
and the closed-form Cardy sum `π√[L(LM+J)/(2G_N)] + π√[L(LM-J)/(2G_N)]`
algebraically equals `π r_+/(2 G_N)` under the convention
`M = (r_+² + r_-²)/(8 G_N L²)`, `J = r_+ r_-/(4 G_N L)` (the same
convention as the existing Phase 8 `btz.py`).

**Bug caught during smoke test**: first cut of
`rotating_btz_horizons` divided by 2 incorrectly, giving
`r_+² = 4 G_N L² M` instead of `8 G_N L² M` in the non-rotating
limit.  Caught immediately by the simple J=0 check against
`√(8 G_N L² M)`.  Second-cut `verify_first_law` sent negative
`r_-` into `mass_from_horizons` at finite-difference points
straddling `J = 0`; fix was to use the closed-form
`M(S, J) = r_+²/(8 G_N L²) + 2 G_N J²/r_+²` directly (even in
`J`), avoiding the round-trip sign handling entirely.

## [1.2.0] — 2026-04-12 — v1.2 patch: Kerr QNM wrapper

Second v1.x patch.  Extends the Phase 5 QNM wrapper from
Schwarzschild-only to full Kerr: the 2D spheroidal-harmonic +
5-term radial recurrence that Stein's `qnm` package solves is now
exposed through Spacetime Lab's `waves` subpackage.  Breaks the
Schwarzschild `m`-degeneracy into `2l + 1` distinct frequencies
and enables the canonical BH spectroscopy test of the no-hair
theorem.

### Added

- `spacetime_lab.waves.kerr_qnm(l, m, n, a_over_M, s)` — Kerr QNM
  front-end at dimensionless spin `a/M ∈ [0, 1)`.  Thin wrapper
  around `qnm.modes_cache` (Stein 2019, JOSS 4 1683).
- `QNMResult` extended with optional `m: int | None` and
  `a_over_M: float | None` fields (backward-compatible — existing
  Schwarzschild code paths continue to set them to `None`).  For
  Kerr modes the cache-based `qnm` API does not expose
  `cf_truncation_error` / `n_cf_terms`, which are reported as
  `nan` / `-1` respectively.
- `notebooks/11_kerr_qnm_spectroscopy.ipynb` — the full Kerr QNM
  concept + Berti-Cardoso-Starinets Figure 2 reproduction (Re and
  Im of `Mω` vs `a/M` for `(l, m, n) = (2, ±2, 0)` and `(2, 0, 0)`)
  + BH spectroscopy no-hair-test demonstration + closing gate cell.
- `tests/test_phase_v1_2.py` — 26 new tests pinned to closed-form
  invariants.  Total project suite grows from **509 to 535 passing
  tests**.

### Verified

| Invariant | Tolerance |
|---|---|
| `qnm` docs anchor: `kerr_qnm(l=m=2, n=0, a=0.68)` = `0.52397510429 − 0.08151262363 i` | `abs_tol = 1e-10` |
| Schwarzschild limit: Kerr path at `a=0` ≡ Schwarzschild path, for all `m ∈ {-l,...,l}` | `~1e-16` (bit-exact) |
| `m`-degeneracy at `a = 0` (all `m` give the same ω) | `< 1e-10` |
| Prograde less damped than retrograde: `|Im ω(m=2)| < |Im ω(m=-2)|` for `a > 0` | exact |
| Prograde `Re(ω)` monotone increasing in `a` | exact |
| Prograde damping decreases monotonically with `a` | exact |
| All modes decay (`Im(ω) < 0`) | exact |

### Physics highlights

- The **Schwarzschild `m`-degeneracy** is broken at any non-zero
  spin.  At `a = 0.9`, the `(l=2, m=+2, n=0)` prograde mode is
  `0.6716 − 0.0649 i`, while the retrograde `(l=2, m=-2, n=0)` mode
  is `0.2972 − 0.0883 i`.  Prograde is both *higher frequency* and
  *longer-lived*.
- **BH spectroscopy** (notebook §3): a true Kerr BH remnant with
  `(M, a/M) = (1, 0.7)` produces `(2, 2, 0)` and `(3, 3, 0)` mode
  frequencies that, when interpreted as observational data,
  uniquely pin `(M, a)` at the intersection of two contours in
  parameter space.  Any inconsistency would be a violation of the
  no-hair theorem.

### Honest scope deferred

- **Kerr-Newman** (charged rotating BH) QNMs — different solver,
  out of scope for Spacetime Lab v1.x
- **Time-domain Kerr ringdown** — trivially composable from
  `kerr_qnm` + existing `RingdownWaveform`; not scoped as a
  separate deliverable
- **Teukolsky angular eigenvalue** `A` — exposed by `qnm` but not
  currently stored in `QNMResult`
- **Superradiant bound states** — `kerr_qnm` returns decaying modes
  only

### Methodology

Same verify-before-code → bit-exact gate → honest-scope-keeping
discipline.  The qnm package's own docs provided the numerical
anchor value `kerr_qnm(l=m=2, n=0, a=0.68) = 0.5239751042900845 −
0.08151262363119974 i`, which was pinned at `abs_tol=1e-10` before
writing any of the v1.2 implementation.  The Schwarzschild limit
gate is the *cross-check*: the Kerr path at `a=0` goes through
`qnm.modes_cache`, a completely different code path in `qnm` than
`SchwOvertoneSeq`, and the two paths agree to machine precision
(`~6e-16`).

## [1.1.0] — 2026-04-11 — v1.1 patch: the evaporating Page curve

First post-v1.0 patch.  Extends the Phase 9 island formula module
from the **eternal BTZ** Page curve (rises and saturates) to the
**evaporating Schwarzschild** Page curve (rises, peaks, **falls back
to zero**).  The bell-shaped curve is the visual demonstration of
toy-model unitarity: every bit of entropy radiated comes back at the
end of evaporation.

### Added

- `spacetime_lab.holography.evaporating` — new module:
  - `schwarzschild_evaporation_time(M0, G_N)` — Page 1976 lifetime
    `t_evap = 5120 π G_N² M_0³` in geometric units.
  - `schwarzschild_mass(t, M0, G_N, t_evap)` — cubic shrinking law
    `M(t) = M_0 (1 - t/t_evap)^(1/3)`, clamped to zero for
    `t ≥ t_evap`.
  - `bekenstein_hawking_entropy(M, G_N)` — `S = 4π M² / G_N` (the
    universal `1/(4 G_N)` factor that ties every Spacetime Lab
    phase together).
  - `hawking_saddle_entropy(t, M0, G_N, t_evap)` — no-island
    Penington 2019 saddle, `S_BH(0) - S_BH(t)`.
  - `island_saddle_entropy_evaporating(t, M0, G_N, t_evap)` —
    quantum extremal surface saddle, `S_BH(t)` (the *current*
    horizon area entropy of the shrinking BH).
  - `page_curve_evaporating(t, M0, G_N, t_evap)` — returns
    `(entropy, phase)` where the entropy is `min(S_H, S_island)`
    and the phase is `"hawking"` or `"island"`.
  - `page_time_evaporating(M0, G_N, t_evap)` — **closed-form** Page
    time `t_P = (1 - √2/4) t_evap ≈ 0.6464 t_evap`.  No transcendental
    equation, no log corrections.
  - `page_time_evaporating_numerical(M0, G_N, t_evap)` — independent
    `brentq` cross-check; agrees with the closed form to 1e-12.
  - `verify_evaporating_unitarity(M0, G_N, t_evap, n_samples)` —
    end-to-end gate function returning bit-exact diagnostics on
    every closed-form invariant.
- `notebooks/10_evaporating_page_curve.ipynb` — concept + headline
  bell-curve plot + side-by-side comparison with the Phase 9 eternal
  BH curve + closing gate cell.
- `tests/test_phase_v1_1.py` — 37 new tests pinned to closed-form
  invariants.  Total project suite grows from **472 to 509 passing
  tests**.

### Verified

| Closed-form invariant | Bit-exact |
|---|---|
| `t_evap = 5120 π M_0³` | `abs_tol=1e-12` |
| `M(t_evap) = 0` exactly | exact |
| `M(t_P) = M_0/√2` | `abs_tol=1e-12` |
| `t_P / t_evap = 1 - √2/4` | `abs_tol=1e-12` |
| `S_rad,max = S_BH(0)/2 = 2π M_0²` | `abs_tol=1e-12` |
| `S_rad(0) = S_rad(t_evap) = 0` | exact (unitarity) |
| `S_H(t_P) = S_island(t_P)` | `~1e-15` (continuity) |
| Closed-form Page time vs `brentq` | `~1e-12` |
| Bell-shape monotonicity | `n=2000` samples |

### Surprise found and documented

The Page time is **not at** `t_evap/2`.  Because `S_BH ∝ M²` falls
faster than linearly in time, half the BH entropy is lost at
`t_P = (1 - √2/4) t_evap ≈ 0.6464 t_evap`, well past the temporal
midpoint of evaporation.  This is testable bit-exactly and is one
of the visually striking features of the bell curve.

### Honest scope notes (deferred to v2.0)

- **JT gravity + CFT bath** setup of Penington / AEMM — analytical
  rigour upgrade.
- **Quantum extremal surface finder** — currently the island is
  identified by hand at the bifurcation surface.
- **Replica wormhole** Euclidean path integral derivation —
  analytical, not coded.
- **Backreaction** of radiation on the geometry — assumes
  quasi-static evaporation throughout.
- **Grey-body factors** and species multiplicity — folded into the
  `t_evap` parameter; not modelled separately.
- **Higher-dimensional BHs** — the cubic law is specific to D=4.

These are the same honest-scope decisions that shipped Phases 3-9
without ever shipping a broken-but-deferred feature.  Each is
documented with the *reason* and the *trigger condition*.

### Methodology

This patch followed the same verify-before-code → bit-exact gate →
honest-scope-keeping discipline that produced Phases 1-9.  Formulas
were pinned against Page 1976, Penington 2019 (arXiv:1905.08255),
AEMM 2019 (arXiv:1905.08762), and the AHMST 2020 review
(arXiv:2006.06872) **before** writing any code.

## [1.0.0] — 2026-04-11 — Phase 9: Island formula and the Page curve (v1.0 MILESTONE)

**The v1.0 milestone of Spacetime Lab.**  Closes Phase 9 of the
18-month roadmap and completes the entire arc from Schwarzschild to
the resolution of the Hawking information paradox.  Eight phases of
preparatory work, plus this one, constitute the complete project:

| Phase | Concept | Headline |
|---|---|---|
| 1 | Schwarzschild | Bekenstein-Hawking `S = A/(4 G_N)` |
| 2 | Penrose diagrams | Causal structure |
| 3 | Kerr + symplectic integrator | Carter's irreducible Killing tensor |
| 4 | Horizon finders + photon shadow | Bardeen 1973 EHT geometry |
| 5 | Quasinormal modes | Schwarzschild QNM verified vs Berti et al |
| 6 | Quantum information | von Neumann entropy + Schmidt decomposition |
| 7 | AdS/CFT foundations | Ryu-Takayanagi bit-exact vs Calabrese-Cardy |
| 8 | BTZ + holographic phase transition | Strominger 1998 BTZ-Cardy match |
| **9** | **Island formula** | **Page curve from the trivial-vs-island saddle transition** |

The factor of `1/(4 G_N)` appears in every single phase: as
Bekenstein-Hawking in Phases 1, 3, 4; as Brown-Henneaux
`c = 3L/(2 G_N)` in Phase 7; as the Cardy-Strominger derivation in
Phase 8; as the area term in the island formula in Phase 9.  The
same number ties classical horizon area to quantum entanglement
entropy across every level of the holographic dictionary.

### Added (Phase 9)

- `spacetime_lab.holography.island` — new module with the simplest
  non-trivial implementation of the island formula:
  - `hartman_maldacena_entropy(t, c, beta, eps)` — the trivial /
    connected saddle in eternal BTZ thermofield double, closed-form
    `(c/3) log[(beta/(pi eps)) cosh(2 pi t / beta)]`.  Uses an
    overflow-safe `_log_cosh` helper for arbitrarily late times.
  - `hartman_maldacena_growth_rate(c, beta)` — the late-time linear
    growth rate `2 pi c / (3 beta)`.
  - `island_saddle_entropy(r_+, G_N=1.0)` — the disconnected /
    island saddle, equal to `2 S_BH = pi r_+ / G_N` (constant in
    time for the eternal BH).
  - `page_curve(t, r_+, L, eps, G_N=1.0)` — returns
    `(entropy, phase)` where the entropy is `min(S_HM, 2 S_BH)`
    and the phase is `"trivial"` or `"island"`.
  - `page_time(r_+, L, eps, G_N=1.0)` — numerical root of
    `S_HM(t_P) = 2 S_BH` via `scipy.optimize.brentq`.  Returns
    `0.0` cleanly in the degenerate fine-cutoff regime where the
    trivial saddle is already above the island saddle at `t = 0`.
  - `verify_page_curve_unitarity(r_+, L, eps, G_N=1.0)` — gate
    function returning a diagnostic dict with the Page time,
    continuity residual, monotonicity check, and phase
    identification at early/late times.
- `notebooks/09_island_formula.ipynb` — concept + demo + closing
  gate cell.  Walks through the Hawking paradox, Page's 1993
  prediction, the island formula, the Hartman-Maldacena 2013
  setup, the headline Page curve plot, the comparison plot for
  multiple BH sizes, and the connection to the Phase 8
  two-interval phase transition (same `min` structure, different
  physics).

### Tests

- `tests/test_phase9.py` — 41 new tests:
  - HM saddle at `t = 0` (closed form), even-in-`t` symmetry
  - Late-time linear growth rate `2 pi c / (3 beta)` matches the
    formula and the numerical derivative at large `t`
  - Numerical stability for arbitrarily large arguments (`t = 1e6`)
  - Island saddle equals `pi r_+ / G_N` and `2 * BTZ.bekenstein_hawking_entropy()`
  - Page time exists, is positive, and the continuity residual
    `|S_HM(t_P) - 2 S_BH| < 1e-9` across multiple parameter sets
  - Page curve is in the trivial phase before `t_P`, in the
    island phase after, and exactly equal to `2 S_BH` after the
    transition
  - Trivial phase value matches `S_HM(t)` exactly
  - Page curve is monotonically non-decreasing
  - **The Page time is independent of `G_N`** (a non-obvious
    feature: both `c` and `2 S_BH` scale as `1/G_N` so the
    coupling cancels in the equation determining `t_P`)
  - Page time grows monotonically with horizon radius
  - Degenerate fine-cutoff regime returns `t_P = 0` cleanly
  - Verification gate function passes across the parameter space
- Total project test suite: **472 tests** passing (up from 431 in
  v0.8.0; +41 Phase 9).

### Verification trail (every formula pinned before implementation)

| Formula | Source |
|---|---|
| HM closed form `(c/3) log(cosh(2 pi t/beta) ...)` | Hartman-Maldacena 2013 §3.5, [arXiv:1303.1080](https://arxiv.org/abs/1303.1080) |
| HM late-time growth rate `2 pi c / (3 beta)` | derivative of the closed form, HM 2013 §3.5 |
| Island saddle = `2 S_BH` for eternal BTZ | Penington 2019, AEMM 2019 |
| Page curve = `min(trivial, island)` | island formula prescription |
| Resolution of the Hawking paradox | Penington 2019 ([arXiv:1905.08255](https://arxiv.org/abs/1905.08255)), AEMM 2019 ([arXiv:1905.08762](https://arxiv.org/abs/1905.08762)) |
| Canonical review | Almheiri-Hartman-Maldacena-Shaghoulian-Tajdini 2020, [arXiv:2006.06872](https://arxiv.org/abs/2006.06872) |

### Bug found and fixed during implementation

The first cut of `hartman_maldacena_growth_rate` returned
`pi c / (3 beta)`, which is the *single-sided* convention often
quoted in reviews.  The HM 2013 formula uses the *two-sided* time
convention with `cosh(2 pi t / beta)` in the argument, which
gives a derivative `dS/dt = (c/3) * (2 pi / beta) * tanh(2 pi t/beta)`
saturating to `2 pi c / (3 beta)` at late times — a factor of 2
larger.  Caught immediately by the smoke test (numerical derivative
at large `t` was double the formula prediction).  Fix: insert the
factor of 2 in `hartman_maldacena_growth_rate` and document the
sign convention in the docstring.  Bit-exact agreement after the
fix.

### Honest scope notes

This release implements the **simplest** non-trivial version of
the island formula:

- **Eternal BTZ**, not an evaporating BH.  The eternal-BH Page
  curve rises and **saturates** at `2 S_BH` rather than falling
  back to zero, because the BH does not actually shrink.  The
  full evaporating Page curve (Penington 2019, AEMM 2019)
  requires coupling to a non-gravitational reservoir and would
  be a v1.1 patch.
- **Hartman-Maldacena 2013 closed form**, not a numerical
  extremal-surface finder.  The closed form makes the
  verification bit-exact.
- **No quantum extremal surface formalism**.  The island here is
  identified by hand (it lives at the bifurcation surface).
- **No replica wormhole derivation**.  The 2019-2020 papers
  derive the island formula from a Euclidean gravitational path
  integral via the replica trick on multiple disconnected
  gravitational saddles.  That is *the proof*, but it is an
  analytical argument that does not become more illuminating by
  being coded up.

These are honest scope decisions.  The qualitative resolution of
the paradox — *there is a non-trivial saddle that prevents the
radiation entropy from growing forever* — is fully present in
this release.  That is the v1.0 milestone.

### Project status at v1.0

- **9 phases shipped, 9 tags, 9 GitHub releases, 9 notebooks** —
  in two calendar days
- **472 tests passing** project-wide
- **8 upstream PRs to bilby-dev/bilby** from Phase 1
- The complete project arc from Schwarzschild to the resolution
  of the Hawking information paradox in one unified codebase

## [0.8.0] — 2026-04-11 — Phase 8: Holographic depth (BTZ + Strominger + two-interval phase transition)

Eighth substantive release. Closes Phase 8 of the 18-month
[ROADMAP](./ROADMAP.md). Where Phase 7 verified the simplest
non-trivial check of the holographic dictionary, Phase 8 extends
to **non-trivial situations**: black holes (BTZ), finite temperature,
microscopic Bekenstein-Hawking from boundary CFT (Strominger 1998),
and the holographic phase transition between connected and
disconnected bulk minimal-surface configurations (Headrick 2010).

Every quantitative result is verified to **bit-exact agreement**:

- BTZ Bekenstein-Hawking entropy = sum of two CFT Cardy contributions
- Bulk RT in BTZ = boundary thermal Calabrese-Cardy
- Two-interval critical gap = `sqrt(2) - 1` for equal unit intervals
- Cross-ratio at the holographic phase transition = exactly `1/2`
- Mutual information = exactly `0` in the disconnected phase

### Added

- `spacetime_lab.metrics.BTZ(horizon_radius, ads_radius)` — the
  non-rotating, uncharged BTZ black hole as a `Metric` subclass.
  Coordinates `(t, r, phi)` with `phi in [0, 2 pi)` periodic; bulk
  at `r > r_+`; conformal boundary at `r -> infinity`.
  - `hawking_temperature()` returns `T_H = r_+ / (2 pi L^2)`.
  - `bekenstein_hawking_entropy(G_N=1.0)` returns
    `S_BH = pi r_+ / (2 G_N)` (the 2D area law: horizon "area" =
    circumference).
  - `mass_parameter(G_N=1.0)` returns `M = r_+^2 / (8 G_N L^2)`.
  - `thermal_beta()` returns `beta = 2 pi L^2 / r_+`.
  - `verify_einstein_constant_curvature()` confirms BTZ is locally
    AdS_3 (`R_munu = -2/L^2 g_munu`) numerically. Verified to
    machine precision (1 ULP at most).
- `spacetime_lab.holography.btz` module:
  - `cardy_formula(c, Delta)` — `S = 2 pi sqrt(c Delta / 6)`
  - `thermal_calabrese_cardy(L_A, c, beta, eps)` — finite-T 2D CFT
    formula `(c/3) log[(beta/(pi eps)) sinh(pi L_A / beta)]`. Uses
    a numerically stable `_log_sinh` helper that handles arbitrarily
    large arguments without overflow.
  - `thermal_entropy_density_high_T(L_A, c, beta)` — the extensive
    piece `pi c L_A / (3 beta)` for the high-T limit.
  - `geodesic_length_btz(L_A, r_+, L, eps)` — closed-form
    regularised length of a BTZ boundary geodesic.
  - `ryu_takayanagi_btz(...)` — apply RT formula in BTZ background.
  - `verify_btz_against_thermal_calabrese_cardy(...)` — gate
    function returning `(rt, cc, residual)`. Residual is bit-exact
    zero for consistent inputs.
  - `verify_strominger_btz_cardy(r_+, L, G_N=1.0)` — Strominger's
    1998 microscopic derivation. BTZ Bekenstein-Hawking entropy
    equals sum of two Cardy contributions (left + right Virasoro
    towers). Bit-exact agreement.
- `spacetime_lab.holography.two_interval` module:
  - `cross_ratio(a, b, c, d)` — `(b-a)(d-c) / ((c-a)(d-b))`
  - `two_interval_disconnected_length(...)` — `L^D`
  - `two_interval_connected_length(...)` — `L^C`
  - `two_interval_entropy(...)` — RT picks the minimum of `L^D`
    and `L^C`. Returns a dict with the chosen entropy, the phase
    name, both candidate lengths, and the cross ratio.
  - `two_interval_mutual_information(...)` — exactly zero in the
    disconnected phase, positive in the connected phase, with a
    sharp non-analyticity at the transition.
  - `critical_separation_for_phase_transition(L1, L2)` —
    closed-form critical gap from solving `x = 1/2`. For equal
    unit intervals this is exactly `sqrt(2) - 1`.
- `notebooks/08_holographic_phase_transitions.ipynb` — concept +
  demo + closing gate cell. Walks through BTZ thermodynamics, the
  Strominger derivation, finite-T Calabrese-Cardy with limit
  checks, the bulk-vs-boundary table at finite temperature, the
  two-interval phase transition with the mutual information plot,
  and the Phase 9 (island formula) teaser.

### Tests

- `tests/test_phase8.py` — 63 new tests:
  - `BTZ` construction, validation, repr
  - BTZ thermodynamics: closed-form `T_H`, `S_BH`, `M`, `beta`,
    first-law consistency
  - BTZ is locally AdS_3 (`R_munu = -2/L^2 g_munu`) at multiple
    parameter combinations
  - `cardy_formula` canonical value, error paths
  - **Strominger 1998**: `verify_strominger_btz_cardy` for 6
    parameter combinations, all residuals < 1e-12
  - `thermal_calabrese_cardy` canonical value, low-T limit reduces
    to zero-T, high-T limit gives the extensive thermal entropy
    plus a cutoff-dependent constant, overflow safety for large
    `L_A / beta`
  - `geodesic_length_btz` canonical value
  - **Bulk RT in BTZ vs thermal CC** for 6 parameter sets, all
    residuals < 1e-12, bit-exact zero for unit inputs
  - `cross_ratio` canonical value, ordering validation
  - Two-interval lengths (connected and disconnected) canonical
    values
  - Phase identification: connected when intervals close,
    disconnected when far
  - **Critical gap = `sqrt(2) - 1`** for equal unit intervals,
    closed form for unequal intervals
  - **Cross-ratio at critical = exactly `1/2`**
  - Mutual information: exactly zero in disconnected phase,
    positive in connected, exactly zero at the critical gap,
    cutoff-independent (the `epsilon` cancels), non-negative,
    continuous across the transition (`L^D = L^C` at critical)
- Total project test suite: **431 tests** passing (up from 368 in
  v0.7.0; +63 Phase 8).

### Verification trail

Following the pattern from Phases 5-7, every formula was pinned to
an external source before implementation:

| Formula | Source |
|---|---|
| BTZ metric | Bañados, Teitelboim & Zanelli 1992 (Phys. Rev. Lett. 69 1849); Wikipedia *BTZ black hole* |
| BTZ T_H = r_+ / (2 pi L^2), S_BH = pi r_+ / (2 G_N) | standard, BTZ 1992 |
| BTZ M = r_+^2 / (8 G_N L^2) | Wikipedia |
| Cardy formula `S = 2 pi sqrt(c Delta / 6)` | Cardy 1986 |
| Strominger BTZ-Cardy match (sum of L_0 + bar L_0) | Strominger 1998 (hep-th/9712251) |
| Thermal Calabrese-Cardy `(c/3) log[(beta/(pi eps)) sinh(pi L_A/beta)]` | Calabrese-Cardy 2004 |
| Two-interval RT phase transition | Headrick 2010 (arXiv:1006.0047) |
| Critical cross-ratio `x = 1/2` | Headrick 2010 |

### Bug found and fixed during implementation

The first cut of `verify_strominger_btz_cardy` returned the
single-Virasoro-tower Cardy formula `S = 2 pi sqrt(c Delta / 6)`
with `Delta = M L`, which gave a residual of `~1/sqrt(2)` from the
target. The fix is the **two-Virasoro-tower formula** of the
Strominger derivation: for non-rotating BTZ, the left and right
Virasoro modes are symmetric with `L_0 = bar L_0 = M L / 2`, and
the Cardy entropy is the *sum* of the two contributions:
`S = 2 * (2 pi sqrt(c L_0 / 6))`. After this fix the agreement is
bit-exact at all parameter values.

A second issue was numerical: the naive
`math.sinh(pi * L_A / beta)` overflows when `L_A / beta` is large
(the high-temperature regime, which is precisely the regime where
the holographic dictionary becomes most interesting because
thermal entropy starts to dominate). Fixed by adding a
`_log_sinh(x)` helper that uses the asymptotic expansion
`log sinh(x) ~ x - log 2 + log(1 - exp(-2x))` for `x > 20`,
combined into the formula in log-space arithmetic. Now handles
arbitrarily extreme parameter combinations.

### Honest scope notes

- Only **non-rotating, uncharged BTZ**. Rotating BTZ has inner and
  outer horizons and richer thermodynamics; deferred to a future
  patch.
- Only the **equatorial-observer two-interval RT** (no time-
  dependent / HRT generalisation). Deferred.
- **No numerical bulk minimal-surface finder** for higher-dimensional
  AdS. The closed-form AdS_3 / BTZ cases give us bit-exact
  verification of every Phase 8 deliverable, which is plenty. A
  general numerical surface finder will land in v0.8.1 when there
  is a higher-dimensional case that genuinely requires it.
- **No Lewkowycz-Maldacena 2013 derivation of RT.** That is a
  beautiful entirely analytical argument that does not become more
  illuminating by being coded up. Mentioned in the notebook prose.

## [0.7.0] — 2026-04-11 — Phase 7: AdS/CFT foundations + Ryu-Takayanagi

Seventh substantive release. Closes Phase 7 of the 18-month
[ROADMAP](./ROADMAP.md). **The simplest non-trivial test of the
holographic entanglement entropy correspondence is now numerically
verified, end-to-end, to bit-exact agreement.**

This is the release where general relativity (Phases 1-5) and
quantum information theory (Phase 6) finally meet via holography.
The bulk-side Ryu-Takayanagi computation (geodesic length in AdS_3)
and the boundary-side Calabrese-Cardy computation (entanglement
entropy of a 2D CFT interval) give *exactly* the same number when
the central charge is determined from the AdS radius via Brown-
Henneaux. The factor of 1/(4 G_N) — the same factor that appears in
the Bekenstein-Hawking formula S = A/(4 G_N) for a black hole — is
universal.

### Added

- `spacetime_lab.metrics.AdS(dimension, radius)` — pure anti-de
  Sitter spacetime in Poincare coordinates as a `Metric` subclass.
  - Coordinates `(t, x_1, ..., x_{n-2}, z)` with `z > 0`; conformal
    boundary at `z -> 0`.
  - Symbolic line element `ds^2 = (L^2 / z^2)(-dt^2 + sum dx_i^2 + dz^2)`.
  - `cosmological_constant()` returns `Lambda = -(n-1)(n-2)/(2 L^2)`.
  - `expected_ricci_scalar()` returns `R = -n(n-1)/L^2`.
  - `verify_einstein_constant_curvature()` confirms
    `R_munu - c g_munu = 0` numerically (lambdified, not symbolic),
    where `c = -(n-1)/L^2`. Verified to exact zero residual for
    AdS_3, AdS_4, AdS_5 at multiple radii.
- `spacetime_lab.holography` — new subpackage:
  - `geodesic_length_ads3(x_A, x_B, radius, epsilon)` — closed-form
    regularised length of a Poincare AdS_3 boundary geodesic. The
    spatial slice is the upper half-plane model of 2D hyperbolic
    space; the geodesic is a semicircle anchored to the two
    boundary points; the length is `2 L log(|x_B - x_A| / epsilon)`.
  - `brown_henneaux_central_charge(radius, G_N=1.0)` — the relation
    `c = 3 L / (2 G_N)`. Returns the central charge of the boundary
    CFT in AdS_3/CFT_2.
  - `ryu_takayanagi_ads3(interval_length, radius, epsilon, G_N=1.0)` —
    apply the RT formula `S = Length / (4 G_N)` for a single
    boundary interval.
  - `calabrese_cardy_2d(interval_length, central_charge, epsilon)` —
    the boundary CFT formula `S = (c/3) log(L_A / epsilon)`, derived
    by Calabrese & Cardy 2004 from a CFT replica trick.
  - `verify_rt_against_calabrese_cardy(...)` — the gate function: it
    computes both sides of the holographic dictionary and returns
    `(rt_value, cc_value, residual)`. The residual is *exactly zero*
    for all consistent inputs — the two code paths reduce to the
    same floating-point computation.
- `notebooks/07_ads_cft_foundations.ipynb` — concept + demo + closing
  gate cell. Walks through pure AdS in Poincare coordinates,
  numerical verification of Einstein-constant curvature, the Brown-
  Henneaux relation, semicircular geodesics in the upper half-plane,
  the closed-form regularised length, the RT formula, the
  bit-exact agreement with Calabrese-Cardy across 5 parameter sets,
  and a wide-range comparison plot showing the two formulas
  overlapping across 5 orders of magnitude in interval length.

### Tests

- `tests/test_holography.py` — 55 new tests:
  - `AdS` construction, validation, repr, dimension and coordinate
    counts
  - **Pinned to closed-form invariants** for the Ricci scalar,
    cosmological constant, Ricci-proportionality constant, in
    multiple dimensions and at multiple radii
  - `verify_einstein_constant_curvature` for AdS_3, AdS_4, AdS_5
    (residual < 1e-10)
  - `geodesic_length_ads3` against the closed form, swap symmetry,
    translation invariance, radius scaling, log-scaling in interval
    length, error paths
  - `brown_henneaux_central_charge` for the unit case, the
    free-boson `c=1` (radius `2/3`), large radius, `1/G_N` scaling
  - `calabrese_cardy_2d` against canonical values, central-charge
    scaling, log-scaling
  - `ryu_takayanagi_ads3` against canonical values, scaling
  - **THE Phase 7 gate**: `verify_rt_against_calabrese_cardy` for 7
    different parameter combinations, all with residual < 1e-12
  - Bit-exact equality for unit inputs (residual is *literally*
    zero, not just below tolerance)
  - Pipeline cross-validation: building RT manually from primitives
    matches the helper exactly
- Total project test suite: **368 tests** passing (up from 313 in
  v0.6.0; +55 holography).

### Verification trail

All formulas pinned to external sources before implementation,
following the verification pattern from Phase 5 onward:

| Formula | Source |
|---|---|
| AdS_n Ricci tensor `R_munu = -(n-1)/L^2 g_munu` | Wikipedia *Anti-de Sitter space* |
| AdS_n Ricci scalar `R = -n(n-1)/L^2` | same |
| Brown-Henneaux `c = 3 L / (2 G_N)` | Brown & Henneaux 1986 (CMP 104 207) |
| Poincare AdS_3 geodesic length `2 L log(L_A/eps)` | arxiv 1708.02958, direct derivation |
| Calabrese-Cardy `S = (c/3) log(L_A/eps)` | Calabrese & Cardy 2004 (J. Stat. Mech. 0406:P06002) |
| Ryu-Takayanagi `S = Length(geodesic) / (4 G_N)` | Ryu & Takayanagi 2006 (PRL 96 181602) |

### Key technical decisions

1. **`AdS` is a `Metric` subclass** consistent with `Schwarzschild`
   and `Kerr`, exposing the same `metric_tensor` / `coordinates`
   API. The `verify_einstein_constant_curvature` method follows
   the Phase 3 lambdified-numerical pattern (sympy `simplify` is
   pathologically slow).
2. **`spacetime_lab.holography` is a new top-level subpackage**
   rather than living in `entropy/` or `metrics/`. Holographic
   entropy is a cross-cutting concern: it relates bulk geometry to
   boundary entropy, so it needs its own home. Phase 8-9 will add
   minimal-surface finders, BTZ thermodynamics, and the island
   formula here.
3. **Closed-form first, ODE solver later.** Phase 7 uses the
   explicit Poincare AdS_3 geodesic formula because it makes the
   verification *bit-exact*. A general numerical bulk minimal-
   surface finder is Phase 8 territory.
4. **`G_N` defaults to 1** consistent with the geometric units used
   throughout Phases 1-5.

### Honest scope notes

This release implements the **simplest non-trivial test** of
holographic entanglement entropy. We deliberately deferred:

- **Two-interval entanglement** (mutual information phase
  transition) — Phase 8.
- **BTZ black hole** and finite-temperature RT — Phase 8.
- **Numerical bulk minimal-surface finder** for higher dimensions
  — Phase 8.
- **Quantum corrections / island formula** — Phase 9.

These are real, hard problems that justify their own phases. Phase
7 establishes that the bulk and boundary computations agree
exactly in the simplest case, which is the existence proof that
the rest of the program is well-posed.

## [0.6.0] — 2026-04-11 — Phase 6: Quantum information primitives

Sixth substantive release. Closes Phase 6 of the 18-month
[ROADMAP](./ROADMAP.md). Spacetime Lab now has the quantum
information building blocks needed for the holographic entanglement
entropy machinery in Phases 7-9: density matrices, partial traces,
von Neumann entropy, Schmidt decomposition, and quantum mutual
information.

This is the **conceptual pivot** of the roadmap.  For five phases
we have been doing classical general relativity.  Phase 6 enters
quantum information theory.  Phase 7+ will weld the two together
(that is the holography programme), and the bridge is already
visible from previous phases: the Bekenstein-Hawking entropy
:math:`S_{BH} = A/4` that we computed for Schwarzschild and Kerr is
literally an entanglement entropy in the holographic dictionary.

### Added

- `spacetime_lab.entropy` — new subpackage:
  - `density_matrix(state)` — promote a pure state vector to its
    rank-1 density matrix :math:`|\\psi\\rangle\\langle\\psi|`.
  - `partial_trace(rho, dims, traced_subsystems)` — generic partial
    trace for arbitrary subsystem dimensions and arbitrary subsets
    of subsystems to trace out.  Uses ``numpy.einsum`` with
    explicit index labels for clarity and supports up to 13
    subsystems.
  - `is_pure(rho)`, `is_density_matrix(rho)` — predicates with
    explicit Hermiticity, trace-1, and PSD checks.
  - `von_neumann_entropy(rho, base)` — the canonical
    :math:`S(\\rho) = -\\text{tr}(\\rho \\log \\rho)`.  Selectable log
    base (``"e"``, ``"2"``, ``"10"``).  Handles the
    :math:`0 \\log 0 = 0` convention via an eigenvalue cutoff.
  - `mutual_information(rho_AB, dims, A, B, base)` — quantum
    mutual information :math:`I(A:B) = S_A + S_B - S_{AB}`.
  - `schmidt_decomposition(state, dims)` — return Schmidt
    coefficients and the two sets of Schmidt vectors via SVD on
    the reshaped state.
  - `schmidt_rank(state, dims)` — number of non-zero Schmidt
    coefficients (= rank of the reduced density matrix).
  - `entanglement_entropy(state, dims, base)` — convenience
    wrapper that goes state → SVD → entropy in one call without
    materialising the reduced density matrix.
- `notebooks/06_entanglement_entropy.ipynb` — Phase 6 concept +
  demo notebook.  Walks through pure vs mixed states, the partial
  trace and the Bell pair, von Neumann entropy and its bounds,
  Schmidt decomposition, a smooth interpolation between product
  and Bell states (with the bell-curve plot of $S(\\theta)$), the
  3-qubit GHZ state and its bipartitions, quantum mutual
  information, and the bridge to holography.  Closing gate cell
  hard-asserts every canonical value.

### Tests

- `tests/test_entropy.py` — 58 new tests:
  - `density_matrix` and predicates (`is_pure`,
    `is_density_matrix`)
  - `partial_trace` against the Bell pair (→ maximally mixed),
    product states, and GHZ; trace-preservation; error paths for
    bad dimensions, out-of-range indices, duplicate indices
  - `von_neumann_entropy` against pure states (= 0), the
    maximally mixed state in dimensions 2-16 (= log d in nats,
    log_2 d in bits, log_10 d in dits), unitary invariance,
    additivity, the :math:`0 \\log 0 = 0` convention
  - `schmidt_decomposition` against the Bell pair, product states,
    state reconstruction (using fixed `Vh.T` instead of
    `Vh.conj().T`), normalisation, error paths
  - `schmidt_rank` for product (=1), Bell (=2), and maximally
    entangled states in $d \\times d$ for $d = 2, 3, 4$
  - `entanglement_entropy` against Bell pair (= log 2), Bell in
    bits (= 1), product (= 0), maximally entangled $d \\times d$
    (= log d), and round-trip agreement with the
    `partial_trace` + `von_neumann_entropy` route
  - GHZ state: every 1-vs-2 bipartition gives log 2, and the
    qubit-pair marginal has zero off-diagonal entries (separable)
  - `mutual_information` for Bell pair (= 2 log 2), product
    states (= 0), and a non-negativity smoke test
- Total project test suite: **313 tests** passing (up from 255 in
  v0.5.0; +58 entropy).

### Bug found and fixed during implementation

- The first cut of `schmidt_decomposition` returned
  `V = Vh.conj().T` rather than `Vh.T`.  The conjugation made the
  reconstruction `sum_i lambda_i kron(U[:, i], V[:, i])` come out
  as the complex conjugate of the original state for non-real
  states.  Fixed by removing the `.conj()` (the SVD relation
  $C = U\\Sigma V^\\dagger$ already accounts for it).  The
  reconstruction round-trip test caught this immediately.

### Notes

- This release has no new external dependencies.  The entire
  module is pure numpy with optional `scipy.linalg` calls.  No
  `quimb`, no `qutip`.  This was a deliberate scope choice to
  keep the install simple and the code self-contained.
- The bridge to Phase 7+ is the verification that Bell pair
  entanglement = exactly $\\log 2$.  That number is the simplest
  case of the Ryu-Takayanagi formula on its smallest possible
  geometry — and Phase 7 will reproduce the more general
  $S = (c/3) \\log(L/\\epsilon)$ formula for a 1D CFT interval
  using AdS$_3$ geodesic lengths.

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
