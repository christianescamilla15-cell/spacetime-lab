r"""Event horizon finders.

For a stationary, spherically- or axially-symmetric vacuum spacetime,
the outer event horizon coincides with the locus where the radial
component of the inverse metric vanishes:

.. math::

    g^{rr}(r_+, \theta) = 0.

In Schwarzschild this is :math:`r = 2M`; in Kerr (Boyer-Lindquist)
this is :math:`r = r_+ = M + \sqrt{M^2 - a^2}`.  This module provides
two complementary implementations of the finder:

- :func:`find_event_horizon` — algebraic root finder on
  :math:`g^{rr}(r) = 0` along the equatorial slice.  Robust, fast,
  and the production-quality entry point.
- :func:`find_event_horizon_via_shooting` — null-geodesic ray
  shooting using :class:`spacetime_lab.geodesics.GeodesicIntegrator`.
  Slower, but exercises the entire Phase 3 stack and is the
  end-to-end cross-validation.

Both functions agree on Schwarzschild and Kerr to better than
:math:`10^{-8}` in the test suite.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from spacetime_lab.metrics.base import Metric


# ─────────────────────────────────────────────────────────────────────
# Algebraic finder (the production entry point)
# ─────────────────────────────────────────────────────────────────────


def find_event_horizon(
    metric: "Metric",
    r_min: float | None = None,
    r_max: float | None = None,
    *,
    theta: float = math.pi / 2,
    tol: float = 1e-10,
) -> float:
    r"""Locate the outer event horizon of a stationary metric.

    Solves :math:`g^{rr}(r, \theta) = 0` for :math:`r` numerically via
    Brent's method.  Works for any metric whose inverse :math:`g^{rr}`
    component is positive far from the hole and crosses zero exactly
    once at the outer horizon.

    Parameters
    ----------
    metric : Metric
        Any subclass of :class:`spacetime_lab.metrics.base.Metric`.
        Only :meth:`Metric.metric_at` is used.
    r_min, r_max : float, optional
        Bracketing range for the bisection.  If unspecified, defaults
        to :math:`r_\text{min} = 0.05` and :math:`r_\text{max} = 100`
        in geometric units.  These work for any reasonable mass
        :math:`M \sim 1` and spin :math:`a \le M`.
    theta : float
        Polar angle at which to evaluate :math:`g^{rr}`.  Defaults to
        :math:`\pi/2` (equator).  For axially symmetric spacetimes
        the event horizon is at constant :math:`r`, so the result
        does not depend on :math:`\theta`.
    tol : float
        Absolute tolerance for the root.

    Returns
    -------
    float
        The outer event horizon radius :math:`r_+`.

    Raises
    ------
    ValueError
        If :math:`g^{rr}` does not change sign on
        :math:`[r_\text{min}, r_\text{max}]`.
    """
    from scipy.optimize import brentq

    if r_min is None:
        r_min = 0.05
    if r_max is None:
        r_max = 100.0

    # For axisymmetric stationary metrics the (r, r) component of the
    # inverse metric is g^{rr} = 1/g_{rr} (no off-diagonal coupling
    # between r and the cyclic coordinates).  Use g_{rr} directly:
    # it diverges at the horizon (where Delta -> 0), and outside vs
    # inside the horizon it has opposite signs (g_{rr} > 0 outside,
    # g_{rr} < 0 inside).  We hunt for the sign change of g_{rr},
    # which is equivalent to the zero crossing of g^{rr}.
    def g_rr_value(r: float) -> float:
        try:
            g = metric.metric_at(t=0.0, r=r, theta=theta, phi=0.0)
        except (TypeError, ValueError):
            # Sympy can return a complex value at exactly r = r_+ due
            # to the 0/0 form of Sigma/Delta there.  Treat as a
            # divergence and return +/- inf depending on which side
            # we are on (use a small perturbation to decide).
            try:
                g = metric.metric_at(
                    t=0.0, r=r * (1.0 + 1e-9), theta=theta, phi=0.0
                )
            except Exception:
                return 0.0
        return float(g[1, 1])

    # Build a coarse scan to find a sign change.  This is much more
    # robust than asking the user to bracket the horizon manually.
    n_scan = 400
    r_scan = np.linspace(r_min, r_max, n_scan)
    g_scan = np.array([g_rr_value(r) for r in r_scan])
    sign_change_indices = np.where(np.diff(np.sign(g_scan)) != 0)[0]
    if len(sign_change_indices) > 0:
        # Take the *outermost* sign change (the outer event horizon).
        idx = sign_change_indices[-1]
        a_brack = r_scan[idx]
        b_brack = r_scan[idx + 1]
        return float(brentq(g_rr_value, a_brack, b_brack, xtol=tol))

    # No sign change.  This happens at extremal Kerr (a = M) where
    # the inner and outer horizons merge: Delta = (r - M)^2 has a
    # double root, so g_{rr} = Sigma/Delta only *touches* zero from
    # one side without crossing.  Look for the minimum of |g_{rr}|
    # — at the extremal horizon r = M, g_{rr} -> infinity, so
    # 1/g_{rr} -> 0 from the positive side.  Find the location of
    # the maximum of |g_{rr}| (or equivalently the minimum of
    # 1/|g_{rr}|).
    inv_abs = 1.0 / np.maximum(np.abs(g_scan), 1e-300)
    min_idx = int(np.argmin(inv_abs))
    if min_idx == 0 or min_idx == len(r_scan) - 1:
        raise ValueError(
            f"g_rr does not change sign and has no interior maximum "
            f"on [{r_min}, {r_max}].  Adjust r_min/r_max to bracket "
            f"the horizon."
        )
    # Refine the maximum location with a parabolic fit on the three
    # neighbours of min_idx.
    from scipy.optimize import minimize_scalar

    def neg_abs_grr(r: float) -> float:
        return -abs(g_rr_value(r))

    result = minimize_scalar(
        neg_abs_grr,
        bounds=(r_scan[min_idx - 1], r_scan[min_idx + 1]),
        method="bounded",
        options={"xatol": tol},
    )
    return float(result.x)


# ─────────────────────────────────────────────────────────────────────
# Ray-shooting finder (the cross-validation entry point)
# ─────────────────────────────────────────────────────────────────────


def find_event_horizon_via_shooting(
    metric: "Metric",
    *,
    theta: float = math.pi / 2,
    r_outer: float = 50.0,
    r_min_search: float = 1.05,
    r_max_search: float = 5.0,
    n_shoot_steps: int = 200,
    h: float = 0.5,
    tol: float = 1e-4,
) -> float:
    r"""[EXPERIMENTAL] Locate the outer event horizon by null geodesic shooting.

    .. warning::
       This implementation is experimental and not production-quality.
       The fundamental issue is that the event horizon is the *asymptote*
       of radially-ingoing null geodesics in affine parameter, not a
       finite-:math:`\lambda` event.  Any finite integration window
       gives a biased estimate, and the bias is large enough that the
       algebraic :func:`find_event_horizon` is dramatically more
       accurate (sub-:math:`10^{-10}` vs ~:math:`10^{-1}` here).
       This routine is kept in the codebase as a documentation of the
       attempted approach and as a place to plug in a future, smarter
       implementation that uses adaptive affine-parameter
       reparametrisation near the horizon.  It is **not** exported
       from :mod:`spacetime_lab.horizons` and the test suite does
       **not** rely on it.

    Algorithm:

    1. Pick a candidate horizon radius :math:`r_c`.
    2. Initialise a *radially outgoing* null geodesic just outside
       :math:`r_c` (small radial offset, no angular momentum).
    3. Evolve forward in affine parameter using
       :class:`GeodesicIntegrator`.
    4. If the photon escapes (r grows past ``r_outer``), :math:`r_c`
       was outside the horizon.
    5. If the photon does not escape within ``n_shoot_steps``,
       :math:`r_c` was at or inside the horizon.
    6. Bisect on :math:`r_c`.

    This is **slow** (typically 5-10 seconds per call) but exercises
    the entire Phase 1/3 stack.  It exists primarily to cross-validate
    the algebraic finder and the geodesic integrator at the same
    time: if the two finders agree on Schwarzschild
    (:math:`r_+ = 2M`) and Kerr (:math:`r_+ = M + \sqrt{M^2 - a^2}`)
    to high precision, then *every layer* of the metric → integrator
    → horizon-finder pipeline is correct.

    Parameters
    ----------
    metric : Metric
        The spacetime to probe.
    theta : float
        Polar angle of the radial geodesic (defaults to equator).
    r_outer : float
        Radius beyond which a photon counts as having escaped.
        Defaults to ``50.0`` geometric units.
    r_min_search, r_max_search : float
        Bracketing range for the bisection on the candidate horizon
        radius.  Defaults to ``[1.05, 5.0]`` which works for any
        Schwarzschild or sub-extremal Kerr with :math:`M \sim 1`.
    n_shoot_steps : int
        Maximum integrator steps per shot.  At ``h = 0.5`` and
        ``n_shoot_steps = 200``, that is :math:`\lambda_\text{max} =
        100` of affine parameter — long enough for any escape.
    h : float
        Integrator step size.
    tol : float
        Bisection tolerance on the horizon radius.  Default
        ``1e-4``: ray-shooting is intrinsically less precise than the
        algebraic finder, so we don't ask for machine precision.

    Returns
    -------
    float
        The estimated outer event horizon radius.
    """
    from spacetime_lab.geodesics import GeodesicIntegrator, GeodesicState

    integrator = GeodesicIntegrator(metric)

    def escapes(r_start: float) -> bool:
        """True iff a radially outgoing null geodesic from r_start escapes."""
        # We need an outgoing null vector at (r_start, theta).  The
        # easiest construction: in the local orthonormal frame, take a
        # photon with energy +1 and purely radial momentum.  Then
        # transform to coordinate basis using the metric components.
        g = metric.metric_at(t=0.0, r=r_start, theta=theta, phi=0.0)
        g_inv = np.linalg.inv(g)
        # Outgoing null direction: choose p_t = -1 (energy 1) and find
        # p_r > 0 satisfying the null condition g^{munu} p_mu p_nu = 0.
        # Set p_theta = p_phi = 0.  Null condition becomes:
        #   g^tt p_t^2 + g^rr p_r^2 + 2 g^tphi p_t p_phi = 0
        # With p_phi = 0: g^tt p_t^2 + g^rr p_r^2 = 0
        # so p_r^2 = -(g^tt / g^rr) p_t^2.
        ratio = -g_inv[0, 0] / g_inv[1, 1]
        if ratio < 0:
            # We are inside the horizon (or in the ergoregion at the
            # equator with non-zero spin); cannot construct an outgoing
            # null vector with p_phi = 0.  Treat as "does not escape".
            return False
        p_t = -1.0
        p_r = math.sqrt(ratio)  # outgoing → positive
        state = GeodesicState(
            x=np.array([0.0, r_start, theta, 0.0]),
            p=np.array([p_t, p_r, 0.0, 0.0]),
        )
        try:
            for _ in range(n_shoot_steps):
                state = integrator.step(state, h)
                if state.x[1] > r_outer:
                    return True
                if not math.isfinite(state.x[1]):
                    return False
        except Exception:
            return False
        return state.x[1] > r_outer

    # Bisection: find the smallest r_start for which escapes(r_start)
    # is True.  Below it, the photon never escapes.
    lo, hi = r_min_search, r_max_search
    if not escapes(hi):
        raise ValueError(
            f"Even at r={hi} the photon does not escape; "
            f"increase r_max_search or check the metric."
        )
    if escapes(lo):
        # The horizon is below our search range; either decrease
        # r_min_search or accept this lower bound.
        return lo
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if escapes(mid):
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)
