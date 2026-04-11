"""Geodesic motion in curved spacetime.

This subpackage provides numerical integration of timelike and null
geodesics in any :class:`~spacetime_lab.metrics.Metric` background.

The current Phase 3 deliverable is the implicit-midpoint
:class:`GeodesicIntegrator`, which is symplectic, time-reversible,
2nd-order accurate, and works for non-separable Hamiltonians like
geodesic motion in Kerr where the kinetic term :math:`g^{\\mu\\nu}(x)
p_\\mu p_\\nu` depends on position.

Typical usage::

    from spacetime_lab.metrics import Kerr
    from spacetime_lab.geodesics import GeodesicIntegrator, GeodesicState

    bh = Kerr(mass=1.0, spin=0.5)
    state0 = GeodesicState(
        x=[0.0, 10.0, 1.4, 0.0],            # (t, r, theta, phi)
        p=[-0.94, 0.0, 1.5, 3.0],           # (p_t, p_r, p_theta, p_phi)
    )
    integrator = GeodesicIntegrator(bh)
    states = integrator.integrate(state0, h=0.5, n_steps=2000)

Conservation diagnostics
========================

For Kerr, the four constants of motion are:

- :math:`E = -p_t` — Killing vector :math:`\\partial_t`
- :math:`L_z = +p_\\varphi` — Killing vector :math:`\\partial_\\varphi`
- :math:`\\mu^2 = -2H` — mass-shell (Hamiltonian itself)
- :math:`\\mathcal{Q}` — Carter's constant (irreducible Killing tensor)

The implicit-midpoint integrator conserves :math:`E` and :math:`L_z`
to **machine precision** because :math:`t` and :math:`\\varphi` are
cyclic in Boyer-Lindquist.  It conserves the mass-shell and Carter's
:math:`\\mathcal{Q}` to high precision (drift of order :math:`h^2` per
step) — small Q drift is the diagnostic that the integration is
following true geodesics rather than slowly diverging from them.
"""

from spacetime_lab.geodesics.symplectic import (
    GeodesicIntegrator,
    GeodesicState,
)

__all__ = [
    "GeodesicIntegrator",
    "GeodesicState",
]
