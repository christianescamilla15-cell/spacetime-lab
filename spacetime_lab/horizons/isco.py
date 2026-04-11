r"""Numerical ISCO finder.

The innermost stable circular orbit (ISCO) is the smallest radius at
which a massive test particle can maintain a stable circular geodesic.
For a 1D effective potential :math:`V_\text{eff}(r; L)` parametrised
by the angular momentum :math:`L`, a circular orbit at radius
:math:`r` requires

.. math::

    V_\text{eff}'(r; L) = 0,

and stability requires :math:`V_\text{eff}''(r; L) \ge 0` (we use the
sign convention where the radial equation is :math:`\dot r^2 = E^2 -
V_\text{eff}`, so a *minimum* of :math:`V_\text{eff}` is stable).

The ISCO is the marginal case where the minimum becomes an inflection:

.. math::

    V_\text{eff}'(r_\text{ISCO}; L_\text{ISCO}) = 0, \qquad
    V_\text{eff}''(r_\text{ISCO}; L_\text{ISCO}) = 0.

These two equations in two unknowns :math:`(r, L)` are solved by
:func:`scipy.optimize.fsolve`.

Verified against the closed-form Schwarzschild ISCO :math:`r = 6M`
to ~``1e-9`` precision in the test suite.

Scope
-----

This finder currently only handles **Schwarzschild** because that is
the only metric in :mod:`spacetime_lab.metrics` that exposes a
``effective_potential(r, L, particle_type)`` method.  Kerr's ISCO is
already provided in closed form via :meth:`Kerr.isco`, which was
verified in v0.3.0 against the Bardeen-Press-Teukolsky 1972 paper.

When we add Kerr-Newman or another non-trivial metric in a future
phase, the obvious extension is to add an ``effective_potential``
method to it as well, at which point this finder will work without
modification.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from spacetime_lab.metrics.base import Metric


def find_isco_numerical(
    metric: "Metric",
    *,
    r_guess: float = 6.0,
    L_guess: float = 3.5,
    tol: float = 1e-10,
) -> float:
    r"""Locate the equatorial ISCO of a massive test particle by root-finding.

    Solves the simultaneous equations

    .. math::

        V_\text{eff}'(r; L) = 0, \qquad V_\text{eff}''(r; L) = 0,

    where :math:`V_\text{eff}` is supplied by the metric's
    ``effective_potential(r, L, "massive")`` method.

    Parameters
    ----------
    metric : Metric
        Must expose ``effective_potential(r, L, particle_type)``
        returning a sympy expression in ``r`` (the symbolic radial
        coordinate).  Currently only :class:`Schwarzschild` qualifies.
    r_guess : float
        Initial guess for the ISCO radius.  Default ``6.0`` (the
        Schwarzschild value).
    L_guess : float
        Initial guess for the angular momentum at the ISCO.  Default
        ``3.5`` (close to the Schwarzschild value :math:`\sqrt{12}
        \approx 3.464`).
    tol : float
        Tolerance for the root finder.

    Returns
    -------
    float
        The ISCO radius in the same units as the metric's mass.

    Raises
    ------
    AttributeError
        If ``metric.effective_potential`` is not implemented.
    RuntimeError
        If the root finder fails to converge.

    Notes
    -----
    The two equations are solved jointly with :func:`scipy.optimize.fsolve`,
    which uses a hybrid Newton method.  For metrics with a
    well-behaved effective potential (Schwarzschild, planned Kerr,
    Reissner-Nordstrom) this converges quadratically from any
    reasonable initial guess.
    """
    import sympy as sp
    from scipy.optimize import fsolve

    if not hasattr(metric, "effective_potential"):
        raise AttributeError(
            f"{type(metric).__name__} does not implement "
            f"effective_potential(r, L, particle_type); cannot find "
            f"ISCO numerically.  Use the metric's analytical isco() "
            f"method instead if available."
        )

    # Build a symbolic effective potential and its derivatives once.
    r_sym = sp.Symbol("r", positive=True)
    L_sym = sp.Symbol("L", positive=True)
    V = metric.effective_potential(r_sym, L_sym, "massive")
    dV_dr = sp.diff(V, r_sym)
    d2V_dr2 = sp.diff(dV_dr, r_sym)

    f1 = sp.lambdify((r_sym, L_sym), dV_dr, "math")
    f2 = sp.lambdify((r_sym, L_sym), d2V_dr2, "math")

    def residuals(z: np.ndarray) -> np.ndarray:
        r_val, L_val = z[0], z[1]
        return np.array([f1(r_val, L_val), f2(r_val, L_val)])

    z0 = np.array([float(r_guess), float(L_guess)])
    sol, info, ier, msg = fsolve(residuals, z0, xtol=tol, full_output=True)
    if ier != 1:
        raise RuntimeError(f"ISCO root finder failed to converge: {msg}")
    return float(sol[0])
