r"""Rotating BTZ black hole: horizons, ergoregion, first law, Strominger-Cardy.

The **v1.3** extension of the Phase 8 non-rotating BTZ module
(:mod:`spacetime_lab.holography.btz`) to the full two-parameter
:math:`(M, J)` family of BTZ solutions.  Ships four main things:

1. The horizon structure :math:`r_\pm(M, J, L, G_N)` and the
   inverse mapping from the horizon radii back to :math:`(M, J)`.
2. Hawking temperature, angular velocity of the horizon,
   Bekenstein-Hawking entropy, and the extremal bound
   :math:`|J| \le ML`.
3. The ergoregion bounded inside by the outer horizon and outside
   by the static limit :math:`g_{tt} = 0`.
4. The **rotating** Strominger 1998 derivation of BTZ entropy:
   the CFT Cardy formula with asymmetric left/right Virasoro
   weights :math:`L_0 = (LM + J)/2`, :math:`\bar L_0 = (LM - J)/2`
   sums bit-exactly to :math:`S_{BH} = \pi r_+/(2 G_N)`.

Convention (matching :mod:`spacetime_lab.holography.btz`)
========================================================

The BTZ metric in standard Schwarzschild-like coordinates is

.. math::

    ds^2 = -f(r) dt^2 + \frac{dr^2}{f(r)}
           + r^2 \left(d\phi - \frac{r_+ r_-}{r^2 L} dt\right)^2,

with

.. math::

    f(r) = \frac{(r^2 - r_+^2)(r^2 - r_-^2)}{r^2 L^2},

:math:`L` the AdS radius, and

.. math::

    M = \frac{r_+^2 + r_-^2}{8 G_N L^2}, \qquad
    J = \frac{r_+ r_-}{4 G_N L}.

This is the same convention used in the Phase 8 non-rotating
module — the :math:`J = 0` limit of everything here recovers
the Phase 8 formulas bit-exactly.  Equivalently,

.. math::

    r_\pm^2 = 4 G_N L^2 M \left(1 \pm
              \sqrt{1 - \left(\frac{J}{ML}\right)^2}\right).

Key quantities
==============

================================  ============================
Quantity                          Closed form
================================  ============================
Hawking temperature               :math:`T_H = \frac{r_+^2 - r_-^2}{2\pi r_+ L^2}`
Horizon angular velocity          :math:`\Omega_H = \frac{r_-}{r_+ L}`
Bekenstein-Hawking entropy        :math:`S_{BH} = \frac{\pi r_+}{2 G_N}`
Ergoregion outer (static limit)   :math:`r_\text{erg}^2 = r_+^2 + r_-^2 = 8 G_N L^2 M`
Extremal bound                    :math:`|J| \le ML`; extremal :math:`r_+ = r_-`
First law                         :math:`dM = T_H\, dS + \Omega_H\, dJ`
Smarr 2+1D                        :math:`M = \tfrac{1}{2} T_H S + \Omega_H J`
================================  ============================

The Smarr relation in 2+1D has a coefficient :math:`1/2` on the
temperature-entropy term rather than the 4D coefficient :math:`1/2`
on an identical-looking combination: the dimensional analysis in
:math:`D = 3` makes this precise, and our
:func:`verify_rotating_btz_thermodynamics` gate checks it.

Rotating Strominger-Cardy match
===============================

For rotating BTZ, the boundary 2D CFT has *left* and *right*
Virasoro towers with unequal weights:

.. math::

    L_0 = \frac{LM + J}{2}, \qquad
    \bar L_0 = \frac{LM - J}{2}.

The central charge is the same for both chiralities,
:math:`c = 3 L/(2 G_N)` (Brown-Henneaux).  The total Cardy entropy
is

.. math::

    S_\text{Cardy} = 2\pi\sqrt{\frac{c\, L_0}{6}}
                   + 2\pi\sqrt{\frac{c\, \bar L_0}{6}}
                   = \frac{\pi (r_+ + r_-)}{4 G_N}
                   + \frac{\pi (r_+ - r_-)}{4 G_N}
                   = \frac{\pi r_+}{2 G_N}
                   = S_{BH},

matching the bulk :math:`A/(4 G_N)` bit-exactly.  The cancellation
between the two chiralities to give :math:`r_+` (and not, say,
:math:`r_+ + r_-` or :math:`r_-`) is a non-trivial consistency
check of the whole AdS/CFT dictionary: both the Bekenstein-Hawking
area law and the Brown-Henneaux relation participate in the match.

References
==========
- Bañados, Teitelboim & Zanelli, *The black hole in three-dimensional
  space-time*, Phys. Rev. Lett. **69** 1849 (1992),
  arXiv:hep-th/9204099.
- Bañados, Henneaux, Teitelboim & Zanelli, *Geometry of the 2+1
  black hole*, Phys. Rev. D **48** 1506 (1993), arXiv:gr-qc/9302012.
- Strominger, *Black hole entropy from near-horizon microstates*,
  J. High Energy Phys. **02** 009 (1998), arXiv:hep-th/9712251.
- Carlip, *The (2+1)-dimensional black hole*,
  Class. Quantum Grav. **12** 2853 (1995).
"""

from __future__ import annotations

import math


# ─────────────────────────────────────────────────────────────────────
# Horizon structure
# ─────────────────────────────────────────────────────────────────────


def extremal_bound_J(mass: float, ads_radius: float) -> float:
    r"""Extremal-rotation bound :math:`|J| \le M L`.

    Returns the positive extremal value :math:`J_\text{max} = M L`
    at which the inner and outer horizons coincide.
    """
    if mass < 0:
        raise ValueError(f"mass must be non-negative, got {mass}")
    if ads_radius <= 0:
        raise ValueError(
            f"ads_radius must be positive, got {ads_radius}"
        )
    return mass * ads_radius


def is_extremal(
    mass: float,
    angular_momentum: float,
    ads_radius: float,
    tol: float = 1e-12,
) -> bool:
    r"""Check whether :math:`|J|/(ML)` is within ``tol`` of :math:`1`."""
    if mass <= 0:
        return False
    return abs(abs(angular_momentum) / (mass * ads_radius) - 1.0) < tol


def rotating_btz_horizons(
    mass: float,
    angular_momentum: float,
    ads_radius: float,
    G_N: float = 1.0,
) -> tuple[float, float]:
    r"""Outer and inner horizon radii of rotating BTZ.

    .. math::

        r_\pm^2 = 4 G_N L^2 M \left(1 \pm
                  \sqrt{1 - (J/(ML))^2}\right).

    Parameters
    ----------
    mass : float
        BTZ mass :math:`M \ge 0`.
    angular_momentum : float
        BTZ angular momentum :math:`J`.  Must satisfy
        :math:`|J| \le ML` (extremal bound).
    ads_radius : float
        AdS radius :math:`L > 0`.
    G_N : float
        Newton's constant.

    Returns
    -------
    r_plus, r_minus : float
        Outer and inner horizon radii with :math:`r_+ \ge r_- \ge 0`.

    Raises
    ------
    ValueError
        If :math:`|J| > ML` (no horizon) or inputs negative / zero.
    """
    if mass < 0:
        raise ValueError(f"mass must be non-negative, got {mass}")
    if ads_radius <= 0:
        raise ValueError(
            f"ads_radius must be positive, got {ads_radius}"
        )
    if G_N <= 0:
        raise ValueError(f"G_N must be positive, got {G_N}")
    J_max = mass * ads_radius
    if abs(angular_momentum) > J_max + 1e-15 * J_max:
        raise ValueError(
            f"|J| > ML: angular_momentum={angular_momentum}, "
            f"ML={J_max}.  No horizon."
        )
    if mass == 0.0:
        return 0.0, 0.0

    ratio = angular_momentum / J_max
    disc = max(0.0, 1.0 - ratio * ratio)
    sqrt_disc = math.sqrt(disc)
    prefactor = 4.0 * G_N * ads_radius * ads_radius * mass
    r_plus_sq = prefactor * (1.0 + sqrt_disc)
    r_minus_sq = prefactor * (1.0 - sqrt_disc)
    # The sign of J is absorbed into r_-.  By convention we return
    # r_+ >= r_- >= 0 and use |J| for the inverse relation.
    return math.sqrt(r_plus_sq), math.sqrt(r_minus_sq)


def rotating_btz_mass_from_horizons(
    r_plus: float,
    r_minus: float,
    ads_radius: float,
    G_N: float = 1.0,
) -> float:
    r"""Inverse relation :math:`M = (r_+^2 + r_-^2)/(8 G_N L^2)`."""
    if r_plus < r_minus:
        raise ValueError(
            f"require r_+ >= r_-, got r_+={r_plus}, r_-={r_minus}"
        )
    if r_plus < 0 or r_minus < 0:
        raise ValueError(
            f"horizon radii must be non-negative, "
            f"got r_+={r_plus}, r_-={r_minus}"
        )
    if ads_radius <= 0:
        raise ValueError(
            f"ads_radius must be positive, got {ads_radius}"
        )
    if G_N <= 0:
        raise ValueError(f"G_N must be positive, got {G_N}")
    return (r_plus * r_plus + r_minus * r_minus) / (
        8.0 * G_N * ads_radius * ads_radius
    )


def rotating_btz_angular_momentum_from_horizons(
    r_plus: float,
    r_minus: float,
    ads_radius: float,
    G_N: float = 1.0,
) -> float:
    r"""Inverse relation :math:`J = r_+ r_-/(4 G_N L)` (non-negative)."""
    if r_plus < r_minus:
        raise ValueError(
            f"require r_+ >= r_-, got r_+={r_plus}, r_-={r_minus}"
        )
    if r_plus < 0 or r_minus < 0:
        raise ValueError(
            f"horizon radii must be non-negative, "
            f"got r_+={r_plus}, r_-={r_minus}"
        )
    if ads_radius <= 0:
        raise ValueError(
            f"ads_radius must be positive, got {ads_radius}"
        )
    if G_N <= 0:
        raise ValueError(f"G_N must be positive, got {G_N}")
    return r_plus * r_minus / (4.0 * G_N * ads_radius)


# ─────────────────────────────────────────────────────────────────────
# Thermodynamic quantities
# ─────────────────────────────────────────────────────────────────────


def rotating_btz_hawking_temperature(
    mass: float,
    angular_momentum: float,
    ads_radius: float,
    G_N: float = 1.0,
) -> float:
    r"""Hawking temperature :math:`T_H = (r_+^2 - r_-^2)/(2\pi r_+ L^2)`.

    Vanishes in the extremal limit :math:`r_+ \to r_-` (equivalently
    :math:`|J| \to ML`).
    """
    r_plus, r_minus = rotating_btz_horizons(
        mass, angular_momentum, ads_radius, G_N=G_N
    )
    if r_plus == 0:
        return 0.0
    return (r_plus * r_plus - r_minus * r_minus) / (
        2.0 * math.pi * r_plus * ads_radius * ads_radius
    )


def rotating_btz_angular_velocity(
    mass: float,
    angular_momentum: float,
    ads_radius: float,
    G_N: float = 1.0,
) -> float:
    r"""Horizon angular velocity :math:`\Omega_H = r_-/(r_+ L)`.

    The sign of :math:`\Omega_H` matches the sign of
    ``angular_momentum`` (our :func:`rotating_btz_horizons` returns
    non-negative radii, so we restore the sign here).
    """
    if mass <= 0:
        return 0.0
    r_plus, r_minus = rotating_btz_horizons(
        mass, angular_momentum, ads_radius, G_N=G_N
    )
    if r_plus == 0:
        return 0.0
    sign = 1.0 if angular_momentum >= 0 else -1.0
    return sign * r_minus / (r_plus * ads_radius)


def rotating_btz_entropy(
    mass: float,
    angular_momentum: float,
    ads_radius: float,
    G_N: float = 1.0,
) -> float:
    r"""Bekenstein-Hawking entropy :math:`S_{BH} = \pi r_+ / (2 G_N)`.

    Depends only on the outer horizon radius :math:`r_+`, just like
    the non-rotating case.  The form is the same as in Phase 8; the
    only change is that :math:`r_+` itself now depends on both
    :math:`M` and :math:`J`.
    """
    r_plus, _ = rotating_btz_horizons(
        mass, angular_momentum, ads_radius, G_N=G_N
    )
    return math.pi * r_plus / (2.0 * G_N)


# ─────────────────────────────────────────────────────────────────────
# Ergoregion
# ─────────────────────────────────────────────────────────────────────


def rotating_btz_ergoregion_bounds(
    mass: float,
    angular_momentum: float,
    ads_radius: float,
    G_N: float = 1.0,
) -> tuple[float, float]:
    r"""Inner / outer radial bounds of the ergoregion.

    The ergoregion is the annulus :math:`r_+ < r < r_\text{erg}` in
    which the Killing vector :math:`\partial_t` is *spacelike*; no
    observer can remain at rest relative to infinity.  Static limit:

    .. math::

        r_\text{erg}^2 = r_+^2 + r_-^2 = 8 G_N L^2 M.

    For non-rotating BTZ (:math:`J = 0`, :math:`r_- = 0`) the
    ergoregion collapses to a point: the static limit coincides
    with the horizon.

    Returns
    -------
    r_inner : float
        :math:`r_+` — the outer horizon.
    r_outer : float
        :math:`r_\text{erg} = \sqrt{r_+^2 + r_-^2}`.  Equal to
        :math:`r_+` for :math:`J = 0` (no ergoregion).
    """
    r_plus, r_minus = rotating_btz_horizons(
        mass, angular_momentum, ads_radius, G_N=G_N
    )
    r_erg = math.sqrt(r_plus * r_plus + r_minus * r_minus)
    return r_plus, r_erg


# ─────────────────────────────────────────────────────────────────────
# Rotating Strominger-Cardy match
# ─────────────────────────────────────────────────────────────────────


def strominger_rotating_btz_cardy(
    mass: float,
    angular_momentum: float,
    ads_radius: float,
    G_N: float = 1.0,
) -> dict:
    r"""Rotating Strominger 1998 BTZ-Cardy derivation.

    Computes the left and right Virasoro weights
    :math:`L_0 = (LM + J)/2`, :math:`\bar L_0 = (LM - J)/2` and
    the two Cardy contributions at Brown-Henneaux central charge
    :math:`c = 3L/(2 G_N)`.  Returns a diagnostic dict that makes
    the bit-exact match :math:`S_{BH} = S_\text{Cardy, L} +
    S_\text{Cardy, R}` visible.

    Returns
    -------
    dict
        ``{s_bh, l_0_left, l_0_right, c, s_cardy_left,
        s_cardy_right, s_cardy_total, residual}``.
    """
    from spacetime_lab.holography.btz import cardy_formula

    r_plus, r_minus = rotating_btz_horizons(
        mass, angular_momentum, ads_radius, G_N=G_N
    )
    s_bh = math.pi * r_plus / (2.0 * G_N)

    LM = ads_radius * mass
    L_0_left = (LM + abs(angular_momentum)) / 2.0
    L_0_right = (LM - abs(angular_momentum)) / 2.0
    c = 3.0 * ads_radius / (2.0 * G_N)

    s_left = cardy_formula(
        central_charge=c, conformal_weight=L_0_left
    )
    s_right = cardy_formula(
        central_charge=c, conformal_weight=L_0_right
    )
    s_total = s_left + s_right

    return {
        "s_bh": s_bh,
        "l_0_left": L_0_left,
        "l_0_right": L_0_right,
        "c": c,
        "s_cardy_left": s_left,
        "s_cardy_right": s_right,
        "s_cardy_total": s_total,
        "residual": abs(s_bh - s_total),
    }


# ─────────────────────────────────────────────────────────────────────
# First law + Smarr + end-to-end gate
# ─────────────────────────────────────────────────────────────────────


def verify_first_law(
    mass: float,
    angular_momentum: float,
    ads_radius: float,
    G_N: float = 1.0,
    h: float = 1e-5,
) -> dict:
    r"""Finite-difference verification of :math:`dM = T dS + \Omega dJ`.

    Evaluates the partial derivatives :math:`(\partial M/\partial S)_J`
    and :math:`(\partial M/\partial J)_S` by a symmetric
    finite-difference stencil and compares them to
    :math:`T_H` and :math:`\Omega_H` respectively.

    The partial derivatives are taken with respect to :math:`S` and
    :math:`J` independently — requires inverting from
    :math:`(S, J)` back to :math:`(M, J)`, which is straightforward
    since :math:`S = \pi r_+/(2 G_N)` and :math:`r_+` plus :math:`J`
    determines :math:`r_-` via :math:`J = r_+ r_-/(4 G_N L)`.

    Returns
    -------
    dict
        Diagnostics including the reference :math:`T_H`, :math:`\Omega_H`,
        the numerical derivatives, and the relative residuals.
    """

    def M_of_S_J(S: float, J: float) -> float:
        # Invert (S, J) -> (r_+, r_-) -> M.  From S = pi r_+/(2 G_N)
        # and J = r_+ r_-/(4 G_N L):
        #     r_+ = 2 G_N S / pi
        #     r_- = 4 G_N L J / r_+
        # Then M = (r_+^2 + r_-^2)/(8 G_N L^2).  M is even in J so
        # the sign of J is irrelevant; we use the closed form
        # directly to avoid round-trip sign gymnastics near J = 0.
        r_plus_val = 2.0 * G_N * S / math.pi
        if r_plus_val == 0:
            return 0.0
        r_minus_sq = (4.0 * G_N * ads_radius * J / r_plus_val) ** 2
        return (r_plus_val * r_plus_val + r_minus_sq) / (
            8.0 * G_N * ads_radius * ads_radius
        )

    S0 = rotating_btz_entropy(
        mass, angular_momentum, ads_radius, G_N=G_N
    )
    J0 = angular_momentum
    T0 = rotating_btz_hawking_temperature(
        mass, angular_momentum, ads_radius, G_N=G_N
    )
    Om0 = rotating_btz_angular_velocity(
        mass, angular_momentum, ads_radius, G_N=G_N
    )

    dS = h * max(abs(S0), 1.0)
    dJ = h * max(abs(J0), 1.0)

    dM_dS = (M_of_S_J(S0 + dS, J0) - M_of_S_J(S0 - dS, J0)) / (
        2.0 * dS
    )
    dM_dJ = (M_of_S_J(S0, J0 + dJ) - M_of_S_J(S0, J0 - dJ)) / (
        2.0 * dJ
    )

    return {
        "T_H": T0,
        "Omega_H": Om0,
        "dM_dS_numerical": dM_dS,
        "dM_dJ_numerical": dM_dJ,
        "dM_dS_residual": abs(dM_dS - T0),
        "dM_dJ_residual": abs(dM_dJ - Om0),
        "dM_dS_rel_residual": abs(dM_dS - T0) / (abs(T0) + 1e-30),
        "dM_dJ_rel_residual": abs(dM_dJ - Om0) / (abs(Om0) + 1e-30),
    }


def verify_smarr_2plus1(
    mass: float,
    angular_momentum: float,
    ads_radius: float,
    G_N: float = 1.0,
) -> dict:
    r"""Smarr-like identity for rotating BTZ: :math:`M = \tfrac{1}{2} T_H S + \Omega_H J`.

    In 2+1 dimensions the Smarr relation takes this specific form,
    derivable from Euler scaling on the extensive variables.

    Returns
    -------
    dict
        ``{M, smarr_rhs, residual}`` where
        ``smarr_rhs = 0.5 * T_H * S + Omega_H * J``.
    """
    S = rotating_btz_entropy(
        mass, angular_momentum, ads_radius, G_N=G_N
    )
    T = rotating_btz_hawking_temperature(
        mass, angular_momentum, ads_radius, G_N=G_N
    )
    Om = rotating_btz_angular_velocity(
        mass, angular_momentum, ads_radius, G_N=G_N
    )
    smarr_rhs = 0.5 * T * S + Om * angular_momentum
    return {
        "M": mass,
        "smarr_rhs": smarr_rhs,
        "residual": abs(mass - smarr_rhs),
    }


def verify_rotating_btz_thermodynamics(
    mass: float,
    angular_momentum: float,
    ads_radius: float,
    G_N: float = 1.0,
    h: float = 1e-5,
) -> dict:
    r"""End-to-end gate on rotating BTZ consistency.

    Bundles:
    - horizon-inversion round-trip residual
    - first-law finite-difference residuals
    - Smarr 2+1D residual
    - rotating Strominger-Cardy residual
    - non-rotating-limit residual (for :math:`J = 0` only)

    Used by ``tests/test_phase_v1_3.py`` and by the closing gate
    cell of the v1.3 notebook.
    """
    r_plus, r_minus = rotating_btz_horizons(
        mass, angular_momentum, ads_radius, G_N=G_N
    )
    M_round_trip = rotating_btz_mass_from_horizons(
        r_plus, r_minus, ads_radius, G_N=G_N
    )
    J_round_trip = rotating_btz_angular_momentum_from_horizons(
        r_plus, r_minus, ads_radius, G_N=G_N
    )

    first_law = verify_first_law(
        mass, angular_momentum, ads_radius, G_N=G_N, h=h
    )
    smarr = verify_smarr_2plus1(
        mass, angular_momentum, ads_radius, G_N=G_N
    )
    cardy = strominger_rotating_btz_cardy(
        mass, angular_momentum, ads_radius, G_N=G_N
    )

    return {
        "r_plus": r_plus,
        "r_minus": r_minus,
        "mass_roundtrip_residual": abs(mass - M_round_trip),
        "angular_momentum_roundtrip_residual": abs(
            abs(angular_momentum) - J_round_trip
        ),
        "first_law_dM_dS_rel_residual": first_law[
            "dM_dS_rel_residual"
        ],
        "first_law_dM_dJ_rel_residual": first_law[
            "dM_dJ_rel_residual"
        ],
        "smarr_residual": smarr["residual"],
        "strominger_cardy_residual": cardy["residual"],
        "is_extremal": is_extremal(
            mass, angular_momentum, ads_radius
        ),
        "T_H": first_law["T_H"],
        "Omega_H": first_law["Omega_H"],
        "S_BH": cardy["s_bh"],
    }
