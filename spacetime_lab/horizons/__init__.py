"""Horizon and critical-orbit finders for stationary black hole spacetimes.

Phase 4 of the Spacetime Lab roadmap.  Provides numerical detection of
event horizons, innermost stable circular orbits, and the Bardeen
photon shadow boundary, all built on top of the Phase 3 geodesic
integrator (:class:`spacetime_lab.geodesics.GeodesicIntegrator`).

Public functions
================

- :func:`find_event_horizon` — locate the outer event horizon of a
  stationary metric by null-geodesic ray shooting + bisection.
  Generic: works for Schwarzschild, Kerr, and any future
  spherically- or axially-symmetric vacuum solution.
- :func:`find_isco_numerical` — locate the innermost stable circular
  orbit of an equatorial massive test particle by root-finding on
  :math:`V_\\text{eff}''(r) = 0`.  Generic: does not use the
  Bardeen-Press-Teukolsky closed form, so it works for metrics that
  do not have one.
- :func:`photon_shadow_kerr` — return the Bardeen 1973 parametric
  curve :math:`(\\alpha(r_p), \\beta(r_p))` of the Kerr photon shadow
  in the observer's image plane.

Cross-validation
================

The point of these finders is **not** to compute things we already
know.  It is to **rediscover** them numerically using only the metric
implementation, providing an end-to-end check that:

1. The Phase 1/3 metric tensors are correct
2. The Phase 3 geodesic integrator follows true null geodesics
3. The composition of the two reproduces textbook closed-form
   answers (Schwarzschild :math:`r_+ = 2M`, ISCO :math:`6M`,
   shadow radius :math:`3\\sqrt{3}\\,M`; Kerr :math:`r_+`, BPT 1972
   ISCO, photon shadow shape)

If any of those checks fail, we know exactly which layer of the stack
is broken.
"""

from spacetime_lab.horizons.event import find_event_horizon
from spacetime_lab.horizons.isco import find_isco_numerical
from spacetime_lab.horizons.shadow import (
    kerr_critical_curve_xi_eta,
    photon_shadow_kerr,
    spherical_photon_orbit_eta,
    spherical_photon_orbit_xi,
)

__all__ = [
    "find_event_horizon",
    "find_isco_numerical",
    "kerr_critical_curve_xi_eta",
    "photon_shadow_kerr",
    "spherical_photon_orbit_eta",
    "spherical_photon_orbit_xi",
]
