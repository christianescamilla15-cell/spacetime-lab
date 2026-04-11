r"""Ryu-Takayanagi 2006 holographic entanglement entropy formula.

The simplest case of the RT formula: a single spatial interval in a
2D CFT, dual to a Poincaré AdS\ :sub:`3` boundary geodesic.  The
formula is

.. math::

    S_A = \frac{\mathrm{Length}(\gamma_A)}{4 G_N},

where :math:`\gamma_A` is the (unique) bulk geodesic anchored to the
two endpoints of the interval :math:`A` on the boundary.  Combining
with :func:`spacetime_lab.holography.geodesics.geodesic_length_ads3`
and the Brown-Henneaux relation, this becomes

.. math::

    S_A
    = \frac{2 L \log(L_A / \epsilon)}{4 G_N}
    = \frac{L}{2 G_N} \log(L_A / \epsilon)
    = \frac{c}{3} \log(L_A / \epsilon),

where :math:`c = 3 L / (2 G_N)` is the Brown-Henneaux central charge.
**This is exactly the Calabrese-Cardy 2004 formula** for the
entanglement entropy of an interval in a 2D CFT, computed entirely
from the boundary side via a CFT replica-trick argument.

The agreement of these two computations — bulk geodesic length on
one side, CFT entanglement entropy on the other — is the simplest
non-trivial test of the holographic entanglement entropy
correspondence.  This module provides:

- :func:`ryu_takayanagi_ads3` — apply RT to a single interval
- :func:`calabrese_cardy_2d` — the boundary CFT formula
- :func:`verify_rt_against_calabrese_cardy` — compute both and
  return the residual (must be at machine precision for consistent
  inputs)

References
==========
- Calabrese & Cardy, *Entanglement entropy and quantum field theory*,
  J. Stat. Mech. 0406:P06002 (2004), arXiv:hep-th/0405152.
- Ryu & Takayanagi, *Holographic derivation of entanglement entropy
  from AdS/CFT*, Phys. Rev. Lett. **96** 181602 (2006),
  arXiv:hep-th/0603001.
"""

from __future__ import annotations

import math


def ryu_takayanagi_ads3(
    interval_length: float,
    radius: float,
    epsilon: float,
    G_N: float = 1.0,
) -> float:
    r"""Apply the Ryu-Takayanagi formula in AdS\ :sub:`3` / CFT\ :sub:`2`.

    For a single boundary interval of length :math:`L_A`, returns

    .. math::

        S_A = \frac{\mathrm{Length}(\gamma_A)}{4 G_N}
            = \frac{2 L \log(L_A/\epsilon)}{4 G_N}
            = \frac{L}{2 G_N} \log(L_A/\epsilon).

    Parameters
    ----------
    interval_length : float
        Length :math:`L_A > 0` of the boundary interval.
    radius : float
        AdS radius :math:`L > 0`.
    epsilon : float
        UV cutoff :math:`\epsilon > 0`.  Should be much smaller than
        ``interval_length``.
    G_N : float
        Newton's constant.  Default ``1.0``.

    Returns
    -------
    float
        The bulk-side holographic entanglement entropy :math:`S_A`
        in nats.

    Raises
    ------
    ValueError
        If any input is non-positive.

    Examples
    --------
    With a unit AdS radius and unit Newton's constant::

        >>> import math
        >>> S = ryu_takayanagi_ads3(interval_length=2.0, radius=1.0, epsilon=0.01)
        >>> abs(S - 0.5 * math.log(200.0)) < 1e-12
        True
    """
    from spacetime_lab.holography.geodesics import geodesic_length_ads3

    if interval_length <= 0:
        raise ValueError(
            f"interval_length must be positive, got {interval_length}"
        )
    if G_N <= 0:
        raise ValueError(f"G_N must be positive, got {G_N}")
    L_geo = geodesic_length_ads3(
        x_A=0.0, x_B=interval_length, radius=radius, epsilon=epsilon
    )
    return L_geo / (4.0 * G_N)


def calabrese_cardy_2d(
    interval_length: float,
    central_charge: float,
    epsilon: float,
) -> float:
    r"""Calabrese-Cardy 2004 entanglement entropy of a 2D CFT interval.

    .. math::

        S_A = \frac{c}{3} \log\!\left(\frac{L_A}{\epsilon}\right).

    This is the boundary-side formula, derived from a replica-trick
    computation in the 2D CFT and *independent* of any reference to
    bulk gravity.  The Phase 7 verification is that this number
    equals :func:`ryu_takayanagi_ads3` evaluated with the same
    interval, when the bulk parameters are tied to the boundary
    central charge via Brown-Henneaux.

    Parameters
    ----------
    interval_length : float
        Length :math:`L_A > 0` of the interval.
    central_charge : float
        Central charge :math:`c > 0` of the CFT.
    epsilon : float
        UV cutoff :math:`\epsilon > 0`.

    Returns
    -------
    float
        :math:`(c/3) \log(L_A / \epsilon)` in nats.

    Raises
    ------
    ValueError
        If any input is non-positive.

    Examples
    --------
    For a free boson (:math:`c = 1`), interval of length 2, cutoff 0.01::

        >>> import math
        >>> S = calabrese_cardy_2d(interval_length=2.0, central_charge=1.0, epsilon=0.01)
        >>> abs(S - (1.0 / 3.0) * math.log(200.0)) < 1e-12
        True

    References
    ----------
    Calabrese & Cardy, J. Stat. Mech. 0406:P06002 (2004),
    arXiv:hep-th/0405152.
    """
    if interval_length <= 0:
        raise ValueError(
            f"interval_length must be positive, got {interval_length}"
        )
    if central_charge <= 0:
        raise ValueError(
            f"central_charge must be positive, got {central_charge}"
        )
    if epsilon <= 0:
        raise ValueError(f"epsilon must be positive, got {epsilon}")
    return (central_charge / 3.0) * math.log(interval_length / epsilon)


def verify_rt_against_calabrese_cardy(
    interval_length: float,
    radius: float,
    epsilon: float,
    G_N: float = 1.0,
) -> tuple[float, float, float]:
    r"""End-to-end Phase 7 verification of holographic entanglement entropy.

    Computes both sides of the holographic dictionary for a single
    boundary interval and returns the bulk RT result, the boundary
    Calabrese-Cardy result, and their absolute residual.  The two
    must agree to machine precision when the central charge is taken
    from Brown-Henneaux:

    .. math::

        \frac{2 L \log(L_A/\epsilon)}{4 G_N}
        \;=\;
        \frac{c}{3}\log(L_A/\epsilon)
        \quad\text{with}\quad
        c = \frac{3 L}{2 G_N}.

    Parameters
    ----------
    interval_length : float
    radius : float
        AdS radius :math:`L`.
    epsilon : float
    G_N : float
        Newton's constant.  Default ``1.0``.

    Returns
    -------
    rt_value : float
        Bulk RT entropy :math:`S_A^{\text{RT}}`.
    cc_value : float
        Boundary Calabrese-Cardy entropy :math:`S_A^{\text{CC}}` with
        :math:`c` determined from ``radius`` and ``G_N`` via
        Brown-Henneaux.
    residual : float
        :math:`|S_A^{\text{RT}} - S_A^{\text{CC}}|`.  Should be at
        floating-point noise (~1e-15).

    Examples
    --------
    >>> rt, cc, res = verify_rt_against_calabrese_cardy(
    ...     interval_length=2.0, radius=1.0, epsilon=0.01
    ... )
    >>> res < 1e-12
    True
    """
    from spacetime_lab.holography.geodesics import (
        brown_henneaux_central_charge,
    )

    rt = ryu_takayanagi_ads3(
        interval_length=interval_length,
        radius=radius,
        epsilon=epsilon,
        G_N=G_N,
    )
    c = brown_henneaux_central_charge(radius=radius, G_N=G_N)
    cc = calabrese_cardy_2d(
        interval_length=interval_length,
        central_charge=c,
        epsilon=epsilon,
    )
    return rt, cc, abs(rt - cc)
