"""Holographic entanglement entropy machinery (Phase 7+).

This subpackage implements the bulk-side computations of the AdS/CFT
correspondence:

- Geodesics and minimal surfaces in AdS metrics (Phase 7: closed-form
  AdS\\ :sub:`3` boundary geodesics; Phase 8: numerical minimal-surface
  finder for higher dimensions)
- The Brown-Henneaux relation tying the bulk gravitational scale to
  the boundary CFT central charge
- The Ryu-Takayanagi formula
  :math:`S_A = \\mathrm{Area}(\\gamma_A) / (4 G_N)`
- The 2D CFT entanglement entropy formula of Calabrese & Cardy 2004,
  used as the boundary-side check on the bulk RT computation

The Phase 7 deliverable is the **end-to-end verification** that the
two sides of the holographic dictionary agree:

.. math::

    \\frac{\\mathrm{Length}(\\gamma_A^{\\text{bulk}})}{4 G_N}
    \\;\\stackrel{\\text{Brown-Henneaux}}{=}\\;
    \\frac{c}{3} \\log\\!\\left(\\frac{L_A}{\\epsilon}\\right)
    \\;=\\;
    S_A^{\\text{boundary CFT}}.

This module exists to make that verification numerical, exact, and
testable.

Public API
==========

- :func:`geodesic_length_ads3` — closed-form regularised length of a
  Poincaré-AdS\\ :sub:`3` geodesic anchored to two boundary points.
- :func:`brown_henneaux_central_charge` — convert AdS radius and
  Newton's constant to the boundary CFT central charge.
- :func:`ryu_takayanagi_ads3` — apply the RT formula directly: take a
  bulk geodesic length, divide by :math:`4 G_N`.
- :func:`calabrese_cardy_2d` — the boundary CFT formula
  :math:`S = (c/3) \\log(L_A / \\epsilon)`.
- :func:`verify_rt_against_calabrese_cardy` — compute both sides of
  the holographic dictionary and return the residual (which should
  be at machine precision for consistent inputs).

References
==========
- Brown & Henneaux, *Central charges in the canonical realization of
  asymptotic symmetries*, Comm. Math. Phys. **104** 207 (1986).
- Calabrese & Cardy, *Entanglement entropy and quantum field theory*,
  J. Stat. Mech. 0406:P06002 (2004), arXiv:hep-th/0405152.
- Ryu & Takayanagi, *Holographic derivation of entanglement entropy
  from AdS/CFT*, Phys. Rev. Lett. **96** 181602 (2006),
  arXiv:hep-th/0603001.
- Maldacena, *The large N limit of superconformal field theories
  and supergravity*, Adv. Theor. Math. Phys. **2** 231 (1998).
"""

from spacetime_lab.holography.btz import (
    cardy_formula,
    geodesic_length_btz,
    ryu_takayanagi_btz,
    thermal_calabrese_cardy,
    thermal_entropy_density_high_T,
    verify_btz_against_thermal_calabrese_cardy,
    verify_strominger_btz_cardy,
)
from spacetime_lab.holography.geodesics import (
    brown_henneaux_central_charge,
    geodesic_length_ads3,
)
from spacetime_lab.holography.evaporating import (
    bekenstein_hawking_entropy,
    hawking_saddle_entropy,
    island_saddle_entropy_evaporating,
    page_curve_evaporating,
    page_time_evaporating,
    page_time_evaporating_numerical,
    schwarzschild_evaporation_time,
    schwarzschild_mass,
    verify_evaporating_unitarity,
)
from spacetime_lab.holography.island import (
    hartman_maldacena_entropy,
    hartman_maldacena_growth_rate,
    island_saddle_entropy,
    page_curve,
    page_time,
    verify_page_curve_unitarity,
)
from spacetime_lab.holography.ryu_takayanagi import (
    calabrese_cardy_2d,
    ryu_takayanagi_ads3,
    verify_rt_against_calabrese_cardy,
)
from spacetime_lab.holography.two_interval import (
    critical_separation_for_phase_transition,
    cross_ratio,
    two_interval_connected_length,
    two_interval_disconnected_length,
    two_interval_entropy,
    two_interval_mutual_information,
)

__all__ = [
    "bekenstein_hawking_entropy",
    "brown_henneaux_central_charge",
    "calabrese_cardy_2d",
    "cardy_formula",
    "critical_separation_for_phase_transition",
    "cross_ratio",
    "geodesic_length_ads3",
    "geodesic_length_btz",
    "hartman_maldacena_entropy",
    "hartman_maldacena_growth_rate",
    "hawking_saddle_entropy",
    "island_saddle_entropy",
    "island_saddle_entropy_evaporating",
    "page_curve",
    "page_curve_evaporating",
    "page_time",
    "page_time_evaporating",
    "page_time_evaporating_numerical",
    "ryu_takayanagi_ads3",
    "ryu_takayanagi_btz",
    "schwarzschild_evaporation_time",
    "schwarzschild_mass",
    "thermal_calabrese_cardy",
    "thermal_entropy_density_high_T",
    "two_interval_connected_length",
    "two_interval_disconnected_length",
    "two_interval_entropy",
    "two_interval_mutual_information",
    "verify_btz_against_thermal_calabrese_cardy",
    "verify_evaporating_unitarity",
    "verify_page_curve_unitarity",
    "verify_rt_against_calabrese_cardy",
    "verify_strominger_btz_cardy",
]
