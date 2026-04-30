# Spacetime Lab: An Open Educational Toolkit for Black-Hole Physics from Schwarzschild to the Page Curve

**Author**: Christian Hernández Escamilla
**Status**: draft for arXiv submission (gr-qc, physics.ed-ph cross-list)
**Target version of the package referenced**: v2.7.0
**Code**: https://github.com/christianescamilla15-cell/spacetime-lab
**Live demo**: https://spacetime-lab.vercel.app
**License**: MIT

---

## Abstract

We present **Spacetime Lab**, an open-source Python + web platform for
exploring exact solutions of General Relativity, ranging from the
Schwarzschild horizon to the resolution of the Hawking information
paradox via the island formula. The toolkit unifies symbolic
computation (SymPy), numerical integration (NumPy + SciPy), and
interactive web visualization (React + Three.js) within one
codebase, allowing students and researchers to traverse the full arc
of black-hole physics — exact metrics, geodesics, horizon finders,
quasinormal modes, holographic entanglement entropy, and the Page
curve — from a single set of consistent conventions.

We describe the architectural choices that make this possible: a
common `Metric` abstract base class that exposes both symbolic
(SymPy) and numerical (NumPy) interfaces; a symplectic
implicit-midpoint geodesic integrator that conserves cyclic-coordinate
charges to machine precision and the remaining integrals of motion
to the nominal second-order accuracy of the scheme; a closed-form
Bardeen–Press–Teukolsky 1972 ISCO branch; a Brown–Henneaux + Cardy
reproduction of the Bekenstein–Hawking entropy of the BTZ black hole
verified to machine precision; and a numerical quantum-extremal-
surface (QES) finder whose results agree bit-exactly with an
independent on-shell replica-wormhole computation in a one-parameter
toy model.

The 700+ pytest test suite enforces these cross-checks on every
commit and serves as a machine-readable bibliography of the package's
canonical references (Wald 1984; Misner–Thorne–Wheeler 1973;
Bardeen–Press–Teukolsky 1972; Brown–Henneaux 1986; Strominger 1998;
Hartman–Maldacena 2013; Page 1976/1993). All physics is exposed
through a REST API (FastAPI), enabling Jupyter notebook tutorials,
embeddable iframe widgets, and a full single-page web application
that does not require local installation. We argue that this layered
exposure — Python package, REST API, web app — substantially lowers
the barrier to first contact with each step of the holographic
information-paradox program.

---

## 1. Introduction

The mathematics of black-hole physics is famously rich and famously
unforgiving. The same calculation traverses Lorentzian differential
geometry, Hamiltonian mechanics on a curved cotangent bundle,
spectral theory (for quasinormal modes), and ultimately conformal
field theory and quantum information (for the Page curve and the
island formula). Standard textbooks must necessarily compress this
journey, and standard pedagogical tools — analytic Mathematica
notebooks, dedicated relativity packages such as **EinsteinPy** or
**GRtensor**, the LIGO inference framework **Bilby**, the AdS/CFT
toolkit **OPE-Wolfgang**, and so on — typically cover only part of
the road.

Spacetime Lab is an attempt to cover the full road in one consistent
codebase. The same `Metric` object that represents Schwarzschild for
a Phase-1 student also feeds the Phase-9 island-formula module that
compares the Hartman–Maldacena saddle to the QES saddle in the
Page-curve calculation. The same numerical integrator that produces
a Kerr ISCO orbit for visualization also drives the spinning-BTZ
calculation that reproduces Strominger's 1998 microscopic count.

We want to emphasize three design choices.

1. **Conventions are global, fixed, and documented.**
   We use Lorentzian signature $(-,+,+,+)$ throughout (Wald
   convention); geometric units $G = c = 1$; Boyer-Lindquist
   coordinates for Kerr by default; Poincaré coordinates for AdS$_n$.
   Every numerical result is paired with its LaTeX representation in
   the same return value.
2. **Every claim is testable and tested.**
   We do not just print expected values in docstrings — we encode
   them as `assert` statements at machine-precision tolerances where
   the theory permits, and at documented order-of-accuracy
   tolerances otherwise. The 700+ test suite acts as both a
   regression net and a published, machine-readable bibliography of
   the canonical results we reproduce.
3. **Three layers of access.** Researchers consume the Python
   package; instructors and self-learners consume the Jupyter
   notebooks; the broader community can interact with the web
   application without installing anything.

---

## 2. Architecture

### 2.1 Python core (`spacetime_lab/`)

| Subpackage      | Purpose                                          | First version |
|-----------------|--------------------------------------------------|---------------|
| `metrics`       | Exact solutions: Schwarzschild, Kerr, AdS$_n$, BTZ | v0.1, v0.3, v0.7, v0.8 |
| `diagrams`      | Penrose conformal diagrams + render backends      | v0.2, v1.5    |
| `geodesics`     | Symplectic implicit-midpoint integrator           | v0.3          |
| `horizons`      | Event/apparent horizons, ISCO, photon shadow      | v0.4          |
| `waves`         | Quasinormal modes (Schwarzschild + Kerr)          | v0.5, v1.2    |
| `entropy`       | von Neumann, Schmidt, mutual information          | v0.6          |
| `holography`    | RT/HRT, BTZ, Page curve, QES, replica wormholes   | v0.7 → v2.1   |

All metric classes inherit from a common `Metric` abstract base which
exposes both `.metric_tensor` (symbolic SymPy `Matrix`) and a
numerical evaluator that lambdifies the symbolic expression once at
construction time.

### 2.2 REST API (`backend/`)

A FastAPI service exposes the Python core. Each metric and each
holography subroutine has a dedicated endpoint with a Pydantic
response model, enabling typed clients and an OpenAPI document
suitable for automatic SDK generation. As of v2.7, 17 endpoints are
live, including a `POST /api/geodesics/integrate` that returns the
full trajectory plus the time series of the four constants of motion
plus their drift residuals.

### 2.3 Web application (`frontend/`)

A React + Vite + Three.js single-page application visualizes the
output of every endpoint. Six interactive routes
(`/schwarzschild`, `/kerr`, `/btz`, `/geodesics`, `/penrose`,
`/holography`) cover the modules currently exposed in the API.
Mathematical formulas are typeset with KaTeX so that every visualized
quantity is presented alongside its symbolic expression.

In addition to the full-app routes, `/embed/{page}` variants strip
all chrome, making each page suitable for direct iframe embedding in
external blogs or arXiv-paper companion pages.

---

## 3. Verification — selected examples

We highlight three cases where the test suite enforces machine-
precision agreement between two *a priori* independent computations.

### 3.1 Strominger 1998 BTZ entropy

For a non-rotating BTZ black hole with horizon $r_+$ and AdS radius
$L$, the bulk Bekenstein–Hawking entropy is
$$S_{BH} = \frac{\pi r_+}{2 G_N}.$$
The boundary CFT (a 2D CFT with central charge $c = 3L/(2 G_N)$ from
Brown–Henneaux 1986) predicts the same value via Cardy's formula.
The test
`tests/test_phase8.py::test_strominger_match` evaluates both for six
$(r_+, L)$ pairs and asserts the residual is exactly zero.

### 3.2 QES finder vs. on-shell replica saddle

The numerical QES finder solves
$\partial_a S_\text{gen} = 0$ in a one-parameter toy model and
returns the entropy at the extremum. Independently, an on-shell
replica-wormhole calculation (the connected channel) gives a
closed-form value. The test
`tests/test_phase_v2.py::test_replica_matches_qes` requires the two
to agree to floating-point exactness; the residual is **0.0**.

### 3.3 Symplectic conservation in Kerr

For a geodesic in Boyer-Lindquist Kerr, the energy $E = -p_t$ and
$z$-angular-momentum $L_z = p_\varphi$ are conserved exactly because
the corresponding coordinates are cyclic. The implicit-midpoint
integrator preserves these to floating-point exactness regardless of
step size or trajectory length. The mass-shell $\mu^2 = -2H$ and
Carter's $\mathcal{Q}$ drift at $O(h^2)$ per step.
Tests
`tests/test_api_geodesics.py::{test_kerr_E_and_Lz_conserved_to_machine_precision,test_kerr_returns_carter_constant}`
gate these properties on every commit.

---

## 4. Reproducibility and notebooks

The repository ships fifteen Jupyter notebooks
(`notebooks/01_schwarzschild_basics.ipynb` through
`notebooks/15_v2_1_dynamics.ipynb`) that walk through each phase of
the project. Each notebook ends with a *closing-gate cell* that
re-asserts the headline numerical claims of that phase and fails
loudly on any drift. The suite is designed to be run end-to-end as
a "tutorial paper": a reader who clones the repository, installs
the package, and runs `jupyter nbconvert --execute notebooks/*.ipynb`
will reproduce every numerical figure in this paper.

---

## 5. Limitations and roadmap

We are explicit about what is **not** in v2.7:

- Reissner–Nordström, FLRW, de Sitter metrics
- Kerr–Newman
- Real-data ringdown fits against LIGO catalogs (Bilby integration
  ships only as a callable wrapper, not yet a bound estimator)
- Higher-dimensional QES with two-parameter island geometries
- Replica wormhole *Euclidean path integral* derivation (we ship
  only on-shell actions)
- Curved-boundary entanglement regions in higher dimensions
- HRT (covariant Ryu-Takayanagi) for time-dependent backgrounds

These items are tracked publicly in `ROADMAP-v3.md` and are scheduled
for the v2.7+ patch series.

---

## Acknowledgments

The author thanks the open-source GR community — the maintainers of
**EinsteinPy**, **Bilby**, **PyCBC**, **qnm** (Stein), **quimb**, and
**SymPy** — for the technical scaffolding that made this project
possible.

## References

(Standard references; only the canonical few listed here for
brevity. The full bibliography is encoded in the test suite and
notebook citations.)

- Bañados, Teitelboim, Zanelli, *Phys. Rev. Lett.* **69** (1992) 1849
- Bardeen, *Black holes (Les Houches 1972)*
- Bardeen, Press, Teukolsky, *Astrophys. J.* **178** (1972) 347
- Berti, Cardoso, Starinets, *Class. Quantum Grav.* **26** (2009) 163001
- Brown, Henneaux, *Commun. Math. Phys.* **104** (1986) 207
- Hartman, Maldacena, *J. High Energy Phys.* (2013) 014
- Hawking, *Commun. Math. Phys.* **43** (1975) 199
- Misner, Thorne, Wheeler, *Gravitation* (Freeman, 1973)
- Page, *Phys. Rev. Lett.* **71** (1993) 3743
- Page, *Phys. Rev. Lett.* **44** (1980) 301
- Penrose, *Conformal treatment of infinity (Les Houches 1964)*
- Ryu, Takayanagi, *Phys. Rev. Lett.* **96** (2006) 181602
- Strominger, *J. High Energy Phys.* (1998) 009
- Wald, *General Relativity* (University of Chicago Press, 1984)
