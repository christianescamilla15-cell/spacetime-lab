r"""Geodesics in AdS and the Brown-Henneaux relation.

Phase 7 only needs the closed-form regularised length of a Poincaré
AdS\ :sub:`3` geodesic anchored to two points on the conformal
boundary.  A general bulk minimal-surface finder for higher
dimensions is Phase 8 territory and is not implemented here.

The Poincaré AdS\\ :sub:`3` metric is

.. math::

    ds^2 = \frac{L^2}{z^2}\,(-dt^2 + dx^2 + dz^2),

with :math:`z > 0` and the conformal boundary at :math:`z \to 0^+`.
A constant-time slice :math:`t = 0` is the upper half-plane model
of 2D hyperbolic space :math:`\mathbb{H}^2` of curvature
:math:`-1/L^2`.

The geodesics of :math:`\mathbb{H}^2` are vertical half-lines and
**semicircles whose centre lies on the boundary** :math:`z = 0`.
For two boundary anchor points :math:`(x_A, 0)` and :math:`(x_B, 0)`
the geodesic is the semicircle of centre :math:`(x_A + x_B)/2` and
radius :math:`R = |x_B - x_A| / 2`.

The actual geodesic is infinite (it asymptotes to the boundary at
each end) so we **regularise** by stopping at :math:`z = \epsilon`.
The closed-form regularised length is

.. math::

    \mathcal{L}(x_A, x_B; \epsilon) = 2 L \log\!\left(
        \frac{|x_B - x_A|}{\epsilon}\right).

This formula is the bulk-side input to the Ryu-Takayanagi
verification in :mod:`spacetime_lab.holography.ryu_takayanagi`.

The **Brown-Henneaux relation**
:math:`c = 3 L / (2 G_N)` ties the AdS radius and Newton's constant
to the central charge of the dual 2D CFT.  This is the deepest single
formula tying bulk gravity to boundary CFT and is verified by every
test of holography.
"""

from __future__ import annotations

import math


def geodesic_length_ads3(
    x_A: float,
    x_B: float,
    radius: float,
    epsilon: float,
) -> float:
    r"""Regularised length of a Poincaré AdS\ :sub:`3` boundary geodesic.

    For two boundary anchor points :math:`(x_A, 0)` and :math:`(x_B, 0)`
    on a constant-time slice of Poincaré AdS\\ :sub:`3`, returns

    .. math::

        \mathcal{L}(\epsilon) = 2 L \log\!\left(
            \frac{|x_B - x_A|}{\epsilon}\right),

    where :math:`\epsilon` is the UV cutoff (the geodesic is stopped at
    :math:`z = \epsilon` near each endpoint).

    Parameters
    ----------
    x_A, x_B : float
        Boundary positions of the two anchor points (in geometric units
        of the AdS radius).  May be in any order; the function uses
        :math:`|x_B - x_A|`.
    radius : float
        AdS radius :math:`L > 0`.
    epsilon : float
        UV cutoff :math:`\epsilon > 0`.  Must be much smaller than the
        interval length :math:`|x_B - x_A|`.

    Returns
    -------
    float
        The regularised geodesic length.  Note: this *can* be negative
        when ``epsilon > |x_B - x_A|``, in which case the geodesic
        does not actually exist (the cutoff is larger than the
        interval) — caller beware.

    Raises
    ------
    ValueError
        If ``radius <= 0``, ``epsilon <= 0``, or the two anchor
        points coincide.

    Examples
    --------
    >>> import math
    >>> L = geodesic_length_ads3(x_A=0.0, x_B=2.0, radius=1.0, epsilon=0.01)
    >>> abs(L - 2.0 * math.log(200.0)) < 1e-12
    True

    Notes
    -----
    The factor of 2 inside the log
    (:math:`\log(2 R / \epsilon)` rather than :math:`\log(R/\epsilon)`)
    has been absorbed into a redefinition of :math:`\epsilon` to match
    the standard Calabrese-Cardy convention.  The two conventions
    differ by an additive constant proportional to :math:`\log 2`,
    which is non-universal and drops out of any subtraction of two
    entropies at the same UV cutoff.
    """
    if radius <= 0:
        raise ValueError(f"radius must be positive, got {radius}")
    if epsilon <= 0:
        raise ValueError(f"epsilon must be positive, got {epsilon}")
    interval_length = abs(x_B - x_A)
    if interval_length == 0:
        raise ValueError(
            "geodesic length is undefined when x_A == x_B"
        )
    return 2.0 * radius * math.log(interval_length / epsilon)


def brown_henneaux_central_charge(
    radius: float,
    G_N: float = 1.0,
) -> float:
    r"""Brown-Henneaux central charge of the boundary CFT\ :sub:`2`.

    .. math::

        c = \frac{3 L}{2 G_N}.

    Derived in 1986 by Brown and Henneaux from the asymptotic
    symmetry algebra of asymptotically AdS\ :sub:`3` spacetimes.  The
    boundary CFT central charge is determined entirely by the bulk
    gravitational scale (the AdS radius :math:`L` and Newton's
    constant :math:`G_N`).  This is one of the deepest hints that
    AdS\ :sub:`3` is dual to a 2D CFT.

    Parameters
    ----------
    radius : float
        AdS radius :math:`L > 0`.
    G_N : float
        Newton's constant in the same units as :math:`L`.  Default
        ``1.0`` (geometric units).

    Returns
    -------
    float
        The central charge :math:`c`.

    Raises
    ------
    ValueError
        If ``radius <= 0`` or ``G_N <= 0``.

    Examples
    --------
    >>> abs(brown_henneaux_central_charge(radius=2.0) - 3.0) < 1e-12
    True

    For the canonical free-boson CFT (:math:`c = 1`), set
    ``radius = 2/3``::

        >>> abs(brown_henneaux_central_charge(radius=2.0/3.0) - 1.0) < 1e-12
        True

    References
    ----------
    Brown & Henneaux, *Central charges in the canonical realization
    of asymptotic symmetries*, Comm. Math. Phys. **104** 207 (1986).
    """
    if radius <= 0:
        raise ValueError(f"radius must be positive, got {radius}")
    if G_N <= 0:
        raise ValueError(f"G_N must be positive, got {G_N}")
    return 3.0 * radius / (2.0 * G_N)
