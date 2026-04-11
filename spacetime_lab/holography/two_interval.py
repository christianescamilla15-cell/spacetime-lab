r"""Two-interval holographic entanglement entropy and the phase transition.

For two disjoint boundary intervals :math:`A_1 = [a, b]` and
:math:`A_2 = [c, d]` with :math:`a < b < c < d`, the bulk has *two*
candidate minimal-surface configurations:

**Disconnected (D)**: each interval has its own bulk geodesic.

.. math::

    \mathcal{L}^D = 2L \log\!\left(\frac{b-a}{\epsilon}\right)
                 + 2L \log\!\left(\frac{d-c}{\epsilon}\right).

**Connected (C)**: the four endpoints are joined by *two new*
geodesics linking the two intervals.

.. math::

    \mathcal{L}^C = 2L \log\!\left(\frac{d-a}{\epsilon}\right)
                 + 2L \log\!\left(\frac{c-b}{\epsilon}\right).

The Ryu-Takayanagi prescription picks the minimum:

.. math::

    S_{A_1 \cup A_2} = \frac{\min(\mathcal{L}^D, \mathcal{L}^C)}{4 G_N}.

The transition between the two phases is governed by the
**cross-ratio**

.. math::

    x = \frac{(b-a)(d-c)}{(c-a)(d-b)}.

The connected configuration wins when :math:`x > 1/2` (intervals
close to each other), and the disconnected configuration wins when
:math:`x < 1/2` (intervals far apart).  This is **the holographic
phase transition** of Headrick 2010 (arXiv:1006.0047).

The **mutual information** :math:`I(A_1 : A_2) = S(A_1) + S(A_2) -
S(A_1 \cup A_2)` is *exactly zero* in the disconnected phase and
positive in the connected phase.  It turns on continuously at the
transition, with a non-analytic kink at :math:`x = 1/2`.  This is
the cleanest holographic non-analyticity and is invisible from any
local CFT observable.

References
==========
- Headrick, *Entanglement Renyi entropies in holographic theories*,
  Phys. Rev. D **82** 126010 (2010), arXiv:1006.0047
- Headrick & Takayanagi, *Holographic proof of the strong
  subadditivity of entanglement entropy*, Phys. Rev. D **76**
  106013 (2007), arXiv:0704.3719
"""

from __future__ import annotations

import math


def cross_ratio(a: float, b: float, c: float, d: float) -> float:
    r"""Cross-ratio :math:`x = (b-a)(d-c)/((c-a)(d-b))`.

    The dimensionless control parameter for the two-interval phase
    transition.  The two intervals are :math:`[a, b]` and
    :math:`[c, d]` with :math:`a < b < c < d`.

    - :math:`x = 0`: intervals infinitely far apart (gap = infinity)
    - :math:`x = 1/2`: holographic phase transition
    - :math:`x = 1`: intervals touching, no gap

    Parameters
    ----------
    a, b, c, d : float
        The four boundary points, in order.

    Returns
    -------
    float

    Raises
    ------
    ValueError
        If the points are not strictly ordered :math:`a < b < c < d`.
    """
    if not (a < b < c < d):
        raise ValueError(
            f"points must satisfy a < b < c < d, got "
            f"a={a}, b={b}, c={c}, d={d}"
        )
    return (b - a) * (d - c) / ((c - a) * (d - b))


def two_interval_disconnected_length(
    a: float,
    b: float,
    c: float,
    d: float,
    ads_radius: float,
    epsilon: float,
) -> float:
    r"""Disconnected RT length :math:`\mathcal{L}^D = 2L\log\frac{b-a}{\epsilon} + 2L\log\frac{d-c}{\epsilon}`.

    Each interval has its own semicircular bulk geodesic.
    """
    if not (a < b < c < d):
        raise ValueError(
            f"points must satisfy a < b < c < d, got "
            f"a={a}, b={b}, c={c}, d={d}"
        )
    if ads_radius <= 0:
        raise ValueError(f"ads_radius must be positive, got {ads_radius}")
    if epsilon <= 0:
        raise ValueError(f"epsilon must be positive, got {epsilon}")
    return (
        2.0 * ads_radius * math.log((b - a) / epsilon)
        + 2.0 * ads_radius * math.log((d - c) / epsilon)
    )


def two_interval_connected_length(
    a: float,
    b: float,
    c: float,
    d: float,
    ads_radius: float,
    epsilon: float,
) -> float:
    r"""Connected RT length :math:`\mathcal{L}^C = 2L\log\frac{d-a}{\epsilon} + 2L\log\frac{c-b}{\epsilon}`.

    The "outer" geodesic links the outermost endpoints :math:`a` and
    :math:`d`; the "inner" geodesic links :math:`b` and :math:`c`
    across the gap.
    """
    if not (a < b < c < d):
        raise ValueError(
            f"points must satisfy a < b < c < d, got "
            f"a={a}, b={b}, c={c}, d={d}"
        )
    if ads_radius <= 0:
        raise ValueError(f"ads_radius must be positive, got {ads_radius}")
    if epsilon <= 0:
        raise ValueError(f"epsilon must be positive, got {epsilon}")
    return (
        2.0 * ads_radius * math.log((d - a) / epsilon)
        + 2.0 * ads_radius * math.log((c - b) / epsilon)
    )


def two_interval_entropy(
    a: float,
    b: float,
    c: float,
    d: float,
    ads_radius: float,
    epsilon: float,
    G_N: float = 1.0,
) -> dict:
    r"""Holographic entanglement entropy of the union of two intervals.

    Returns the RT entropy with the *minimum* of the connected and
    disconnected configurations, plus diagnostic information about
    which phase RT chose.

    Parameters
    ----------
    a, b, c, d : float
        The four boundary points, with :math:`a < b < c < d`.
        Intervals are :math:`A_1 = [a, b]` and :math:`A_2 = [c, d]`.
    ads_radius : float
        AdS\ :sub:`3` radius.
    epsilon : float
        UV cutoff.
    G_N : float
        Newton's constant.  Default ``1.0``.

    Returns
    -------
    dict
        With keys:

        - ``"entropy"`` (float): the RT entropy
        - ``"phase"`` (str): ``"connected"`` or ``"disconnected"``
        - ``"connected_length"`` (float): :math:`\mathcal{L}^C`
        - ``"disconnected_length"`` (float): :math:`\mathcal{L}^D`
        - ``"cross_ratio"`` (float): :math:`x`
        - ``"chosen_length"`` (float): the smaller of the two
    """
    if G_N <= 0:
        raise ValueError(f"G_N must be positive, got {G_N}")

    L_disc = two_interval_disconnected_length(
        a, b, c, d, ads_radius=ads_radius, epsilon=epsilon
    )
    L_conn = two_interval_connected_length(
        a, b, c, d, ads_radius=ads_radius, epsilon=epsilon
    )
    x = cross_ratio(a, b, c, d)

    if L_conn < L_disc:
        chosen = L_conn
        phase = "connected"
    else:
        chosen = L_disc
        phase = "disconnected"

    return {
        "entropy": chosen / (4.0 * G_N),
        "phase": phase,
        "connected_length": L_conn,
        "disconnected_length": L_disc,
        "cross_ratio": x,
        "chosen_length": chosen,
    }


def two_interval_mutual_information(
    a: float,
    b: float,
    c: float,
    d: float,
    ads_radius: float,
    epsilon: float,
    G_N: float = 1.0,
) -> float:
    r"""Holographic mutual information :math:`I(A_1 : A_2)`.

    .. math::

        I(A_1 : A_2) = S(A_1) + S(A_2) - S(A_1 \cup A_2).

    Exactly zero in the disconnected phase
    (:math:`L^D < L^C`, i.e. cross-ratio :math:`x < 1/2`); positive
    in the connected phase.  Equivalent to the difference of the
    two candidate RT lengths divided by :math:`4 G_N`:

    .. math::

        I = \frac{\mathcal{L}^D - \mathcal{L}^C}{4 G_N}
            \quad\text{if connected wins, else 0}.

    Parameters
    ----------
    a, b, c, d : float
        Boundary points :math:`a < b < c < d`.
    ads_radius : float
        AdS radius :math:`L`.
    epsilon : float
        UV cutoff.  Note: the mutual information is *cutoff-
        independent* — the :math:`\epsilon` dependence cancels
        between :math:`L^D` and :math:`L^C`.  Pass any positive
        value.
    G_N : float
        Newton's constant.

    Returns
    -------
    float
        :math:`I(A_1 : A_2) \ge 0`.
    """
    if G_N <= 0:
        raise ValueError(f"G_N must be positive, got {G_N}")

    L_disc = two_interval_disconnected_length(
        a, b, c, d, ads_radius=ads_radius, epsilon=epsilon
    )
    L_conn = two_interval_connected_length(
        a, b, c, d, ads_radius=ads_radius, epsilon=epsilon
    )
    diff = L_disc - L_conn  # > 0 iff connected wins
    if diff <= 0:
        return 0.0
    return diff / (4.0 * G_N)


def critical_separation_for_phase_transition(
    interval_length_1: float,
    interval_length_2: float,
) -> float:
    r"""Critical gap :math:`d_\text{crit}` between two equal intervals.

    For two intervals of length :math:`L_1` and :math:`L_2` separated
    by a gap :math:`d`, the holographic phase transition occurs when
    the cross-ratio crosses :math:`x = 1/2`.  Solving the cross-ratio
    equation explicitly for the gap with :math:`a = 0`,
    :math:`b = L_1`, :math:`c = L_1 + d`, :math:`d_\text{end} =
    L_1 + d + L_2`:

    .. math::

        x = \frac{L_1 \cdot L_2}{(L_1 + d)(d + L_2)} = \frac{1}{2}.

    Solving for :math:`d`:

    .. math::

        d_\text{crit} = \frac{-(L_1 + L_2) +
                              \sqrt{(L_1 - L_2)^2 + 8 L_1 L_2}}{2}.

    For equal intervals :math:`L_1 = L_2 = L_0` this reduces to
    :math:`d_\text{crit} = (\sqrt{8} - 2) L_0 / 2 = (\sqrt{2} - 1) L_0`.

    Parameters
    ----------
    interval_length_1, interval_length_2 : float
        The two interval lengths.

    Returns
    -------
    float
        The critical gap.
    """
    if interval_length_1 <= 0 or interval_length_2 <= 0:
        raise ValueError(
            f"interval lengths must be positive, got "
            f"{interval_length_1}, {interval_length_2}"
        )
    L1, L2 = float(interval_length_1), float(interval_length_2)
    discriminant = (L1 - L2) ** 2 + 8.0 * L1 * L2
    return (-(L1 + L2) + math.sqrt(discriminant)) / 2.0
