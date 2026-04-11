r"""Finite-temperature holographic entanglement entropy via BTZ.

This module implements the BTZ-side and CFT-side computations for
holographic entanglement entropy at finite temperature.  The BTZ
black hole is dual to a *thermal state* of the boundary CFT at
inverse temperature :math:`\beta`.  The CFT entanglement entropy of
an interval is given by the Calabrese-Cardy 2004 finite-temperature
formula

.. math::

    S_A^{T>0} = \frac{c}{3} \log\!\left[
        \frac{\beta}{\pi\epsilon}\,
        \sinh\!\left(\frac{\pi L_A}{\beta}\right)\right],

and the bulk dual is the regularised length of a geodesic in the
BTZ background ending on two boundary points, divided by
:math:`4 G_N`.  The two computations agree exactly when the central
charge is determined from the AdS radius via Brown-Henneaux
:math:`c = 3 L / (2 G_N)` and the BTZ temperature
:math:`T_H = r_+ / (2 \pi L^2)` matches the CFT temperature
:math:`T = 1/\beta`.

Two important limits of the finite-T formula:

- **Low temperature** :math:`\beta \gg L_A`:
  :math:`\sinh(\pi L_A/\beta) \approx \pi L_A/\beta`, and the formula
  collapses to :math:`(c/3)\log(L_A/\epsilon)` — the Phase 7
  zero-temperature result.
- **High temperature** :math:`\beta \ll L_A`:
  :math:`\sinh(\pi L_A/\beta) \approx \tfrac{1}{2} e^{\pi L_A/\beta}`,
  so :math:`S \approx (c/3)[\log(\beta/(2\pi\epsilon)) + \pi L_A/\beta]`.
  The second term is the *thermal entropy* of a 1+1 CFT,
  :math:`S_\text{thermal} = (\pi c L_A) / (3\beta)`.

The Strominger 1998 derivation shows that the BTZ Bekenstein-Hawking
entropy itself equals the Cardy formula on the boundary CFT at the
matching temperature:

.. math::

    S_{BH}^{\text{BTZ}} = \frac{\pi r_+}{2 G_N}
    \;\stackrel{?}{=}\;
    S^\text{Cardy}\!\left(c, \Delta = M L\right),

where :math:`M = r_+^2 / (8 G_N L^2)` is the BTZ mass parameter.
We verify this match in :func:`verify_strominger_btz_cardy`.

References
==========
- Bañados, Teitelboim & Zanelli, Phys. Rev. Lett. **69** 1849 (1992)
- Strominger, *Black hole entropy from near-horizon microstates*,
  J. High Energy Phys. **02** 009 (1998), arXiv:hep-th/9712251
- Calabrese & Cardy, *Entanglement entropy and quantum field
  theory*, J. Stat. Mech. 0406:P06002 (2004), arXiv:hep-th/0405152
- Cardy, *Operator content of two-dimensional conformally invariant
  theories*, Nucl. Phys. B **270** 186 (1986)
"""

from __future__ import annotations

import math


def _log_sinh(x: float) -> float:
    r"""Numerically stable :math:`\log\sinh(x)` for arbitrary :math:`x > 0`.

    For small :math:`x` we use the standard :math:`\log\sinh(x)`.  For
    large :math:`x` (where :math:`\sinh(x)` overflows ``math.sinh``)
    we use the asymptotic expansion

    .. math::

        \log\sinh(x) = x - \log 2 + \log(1 - e^{-2x}),

    which is exact and well-behaved for any :math:`x > 0`.
    """
    if x <= 0:
        raise ValueError(f"_log_sinh requires x > 0, got {x}")
    if x > 20.0:
        # log(sinh(x)) = log((e^x - e^-x)/2)
        #              = x + log((1 - e^{-2x})/2)
        #              = x - log 2 + log(1 - e^{-2x})
        # For x > 20, e^{-2x} < 4e-18 so log(1 - e^{-2x}) ~ -e^{-2x} ~ 0.
        return x - math.log(2.0) + math.log1p(-math.exp(-2.0 * x))
    return math.log(math.sinh(x))


# ─────────────────────────────────────────────────────────────────────
# Cardy formula for the density of states
# ─────────────────────────────────────────────────────────────────────


def cardy_formula(central_charge: float, conformal_weight: float) -> float:
    r"""Asymptotic density of states of a 2D CFT — Cardy 1986.

    .. math::

        S = 2\pi\sqrt{\frac{c \, \Delta}{6}}.

    Used by Strominger 1998 to derive the BTZ Bekenstein-Hawking
    entropy from the boundary CFT.

    Parameters
    ----------
    central_charge : float
        Central charge :math:`c > 0`.
    conformal_weight : float
        Conformal weight :math:`\Delta \ge 0` of the state (eigenvalue
        of the Hamiltonian, modulo zero-point shifts).

    Returns
    -------
    float
        The Cardy entropy.

    Examples
    --------
    >>> import math
    >>> S = cardy_formula(central_charge=6.0, conformal_weight=1.0)
    >>> abs(S - 2 * math.pi * math.sqrt(1.0)) < 1e-12
    True
    """
    if central_charge <= 0:
        raise ValueError(
            f"central_charge must be positive, got {central_charge}"
        )
    if conformal_weight < 0:
        raise ValueError(
            f"conformal_weight must be non-negative, got {conformal_weight}"
        )
    return 2.0 * math.pi * math.sqrt(central_charge * conformal_weight / 6.0)


# ─────────────────────────────────────────────────────────────────────
# Finite-temperature Calabrese-Cardy
# ─────────────────────────────────────────────────────────────────────


def thermal_calabrese_cardy(
    interval_length: float,
    central_charge: float,
    beta: float,
    epsilon: float,
) -> float:
    r"""Calabrese-Cardy 2004 entanglement entropy at finite temperature.

    .. math::

        S_A = \frac{c}{3}
              \log\!\left[\frac{\beta}{\pi\epsilon}
                          \sinh\!\left(\frac{\pi L_A}{\beta}\right)\right].

    The boundary-side input to the BTZ holographic verification.

    Parameters
    ----------
    interval_length : float
        Length :math:`L_A` of the boundary interval.
    central_charge : float
        Central charge :math:`c` of the CFT.
    beta : float
        Inverse temperature :math:`\beta = 1/T`.
    epsilon : float
        UV cutoff.

    Returns
    -------
    float
        :math:`S_A^{T>0}` in nats.

    Examples
    --------
    Low-temperature limit reduces to Phase 7 result::

        >>> import math
        >>> S_lowT = thermal_calabrese_cardy(2.0, 1.0, beta=1e6, epsilon=0.01)
        >>> S_zeroT = (1.0/3.0) * math.log(2.0/0.01)
        >>> abs(S_lowT - S_zeroT) < 1e-4
        True
    """
    if interval_length <= 0:
        raise ValueError(
            f"interval_length must be positive, got {interval_length}"
        )
    if central_charge <= 0:
        raise ValueError(
            f"central_charge must be positive, got {central_charge}"
        )
    if beta <= 0:
        raise ValueError(f"beta must be positive, got {beta}")
    if epsilon <= 0:
        raise ValueError(f"epsilon must be positive, got {epsilon}")

    # log[(beta/(pi eps)) * sinh(pi L_A / beta)]
    #   = log(beta/(pi eps)) + log sinh(pi L_A / beta)
    # The log_sinh helper is numerically stable for all positive args.
    log_arg = (
        math.log(beta / (math.pi * epsilon))
        + _log_sinh(math.pi * interval_length / beta)
    )
    return (central_charge / 3.0) * log_arg


def thermal_entropy_density_high_T(
    interval_length: float,
    central_charge: float,
    beta: float,
) -> float:
    r"""High-temperature thermal-entropy contribution :math:`(\pi c L_A)/(3\beta)`.

    The leading "extensive" piece of the finite-temperature
    entanglement entropy in the limit :math:`\beta \ll L_A`.  This
    is just the standard 1+1 CFT thermal entropy density times the
    interval length, with no UV-cutoff dependence.

    Used to verify that
    :func:`thermal_calabrese_cardy` reproduces this density at high
    temperature, modulo a sub-extensive cutoff-dependent constant.
    """
    return math.pi * central_charge * interval_length / (3.0 * beta)


# ─────────────────────────────────────────────────────────────────────
# Bulk side: BTZ geodesic length
# ─────────────────────────────────────────────────────────────────────


def geodesic_length_btz(
    interval_length: float,
    horizon_radius: float,
    ads_radius: float,
    epsilon: float,
) -> float:
    r"""Closed-form regularised length of a BTZ boundary geodesic.

    For a boundary interval of length :math:`L_A` on the asymptotic
    boundary of a non-rotating BTZ black hole with horizon radius
    :math:`r_+` and AdS radius :math:`L`, the regularised length of
    the bulk geodesic is

    .. math::

        \mathcal{L}(\epsilon) = 2 L \log\!\left[
            \frac{\beta}{\pi\epsilon}\,
            \sinh\!\left(\frac{\pi L_A}{\beta}\right)\right],

    with inverse temperature :math:`\beta = 2\pi L^2 / r_+`.

    Substituting Brown-Henneaux :math:`c = 3L/(2 G_N)`, this is
    *exactly* :math:`4 G_N` times the boundary-CFT formula
    :func:`thermal_calabrese_cardy`.  The Phase 8 gate test pins this
    agreement to bit-exact precision.

    Parameters
    ----------
    interval_length : float
        Boundary interval length :math:`L_A`.
    horizon_radius : float
        BTZ horizon radius :math:`r_+ > 0`.
    ads_radius : float
        AdS radius :math:`L > 0`.
    epsilon : float
        UV cutoff.

    Returns
    -------
    float
        The bulk geodesic length.
    """
    if interval_length <= 0:
        raise ValueError(
            f"interval_length must be positive, got {interval_length}"
        )
    if horizon_radius <= 0:
        raise ValueError(
            f"horizon_radius must be positive, got {horizon_radius}"
        )
    if ads_radius <= 0:
        raise ValueError(f"ads_radius must be positive, got {ads_radius}")
    if epsilon <= 0:
        raise ValueError(f"epsilon must be positive, got {epsilon}")

    beta = 2.0 * math.pi * ads_radius * ads_radius / horizon_radius
    log_arg = (
        math.log(beta / (math.pi * epsilon))
        + _log_sinh(math.pi * interval_length / beta)
    )
    return 2.0 * ads_radius * log_arg


def ryu_takayanagi_btz(
    interval_length: float,
    horizon_radius: float,
    ads_radius: float,
    epsilon: float,
    G_N: float = 1.0,
) -> float:
    r"""Apply the Ryu-Takayanagi formula in BTZ / thermal CFT_2.

    .. math::

        S_A = \frac{\mathrm{Length}_\text{BTZ}(L_A; r_+, L, \epsilon)}{4 G_N}.

    Returns the bulk-side holographic entanglement entropy of a
    boundary interval at finite temperature.
    """
    if G_N <= 0:
        raise ValueError(f"G_N must be positive, got {G_N}")
    L_geo = geodesic_length_btz(
        interval_length=interval_length,
        horizon_radius=horizon_radius,
        ads_radius=ads_radius,
        epsilon=epsilon,
    )
    return L_geo / (4.0 * G_N)


def verify_btz_against_thermal_calabrese_cardy(
    interval_length: float,
    horizon_radius: float,
    ads_radius: float,
    epsilon: float,
    G_N: float = 1.0,
) -> tuple[float, float, float]:
    r"""End-to-end verification: bulk RT in BTZ vs boundary thermal CC.

    Computes both sides of the holographic dictionary at finite
    temperature and returns ``(rt_value, cc_value, residual)``.  The
    residual is *exactly zero* for consistent inputs (the two code
    paths reduce to the same floating-point computation when the
    central charge is determined from the AdS radius via Brown-
    Henneaux and :math:`\beta = 2\pi L^2 / r_+`).
    """
    from spacetime_lab.holography.geodesics import (
        brown_henneaux_central_charge,
    )

    rt = ryu_takayanagi_btz(
        interval_length=interval_length,
        horizon_radius=horizon_radius,
        ads_radius=ads_radius,
        epsilon=epsilon,
        G_N=G_N,
    )
    c = brown_henneaux_central_charge(radius=ads_radius, G_N=G_N)
    beta = 2.0 * math.pi * ads_radius * ads_radius / horizon_radius
    cc = thermal_calabrese_cardy(
        interval_length=interval_length,
        central_charge=c,
        beta=beta,
        epsilon=epsilon,
    )
    return rt, cc, abs(rt - cc)


# ─────────────────────────────────────────────────────────────────────
# Strominger 1998 derivation: BTZ entropy from Cardy
# ─────────────────────────────────────────────────────────────────────


def verify_strominger_btz_cardy(
    horizon_radius: float,
    ads_radius: float,
    G_N: float = 1.0,
) -> tuple[float, float, float]:
    r"""Strominger 1998 derivation of BTZ entropy from CFT Cardy formula.

    The BTZ Bekenstein-Hawking entropy
    :math:`S_{BH} = \pi r_+ / (2 G_N)` should equal the **sum of two
    Cardy contributions** — one for each chirality of the boundary
    2D CFT (left-movers and right-movers).  This is the original
    Strominger 1998 observation.

    For non-rotating BTZ the two chiralities are symmetric, so
    :math:`L_0 = \bar L_0 = M L / 2` and

    .. math::

        S_\text{Cardy} = 2\pi\sqrt{\frac{c L_0}{6}}
                       + 2\pi\sqrt{\frac{c \bar L_0}{6}}
                       = 2 \cdot 2\pi\sqrt{\frac{c\,M L / 2}{6}}.

    Substituting :math:`c = 3 L / (2 G_N)` and
    :math:`M = r_+^2/(8 G_N L^2)`:

    .. math::

        \frac{c \cdot M L / 2}{6}
        = \frac{1}{2} \cdot \frac{3 L}{2 G_N}
                      \cdot \frac{r_+^2}{8 G_N L^2}
                      \cdot \frac{L}{6}
        = \frac{r_+^2}{64 G_N^2},

    so :math:`\sqrt{\cdots} = r_+/(8 G_N)` and

    .. math::

        S_\text{Cardy} = 4\pi \cdot \frac{r_+}{8 G_N}
                       = \frac{\pi r_+}{2 G_N}
                       = S_{BH}.

    This is the simplest microscopic derivation of black-hole
    entropy, and it predates Maldacena's AdS/CFT statement by months.
    Our implementation reproduces it bit-exactly.

    Returns
    -------
    s_bh : float
        :math:`S_{BH} = \pi r_+ / (2 G_N)` from the bulk metric.
    s_cardy : float
        Sum of left-mover and right-mover Cardy contributions at
        the matching CFT state.
    residual : float
        :math:`|S_{BH} - S_\text{Cardy}|`.  Exactly zero for the
        canonical convention.
    """
    from spacetime_lab.holography.geodesics import (
        brown_henneaux_central_charge,
    )
    from spacetime_lab.metrics.btz import BTZ

    btz = BTZ(horizon_radius=horizon_radius, ads_radius=ads_radius)
    s_bh = btz.bekenstein_hawking_entropy(G_N=G_N)

    c = brown_henneaux_central_charge(radius=ads_radius, G_N=G_N)
    M = btz.mass_parameter(G_N=G_N)
    # Non-rotating BTZ: left and right Virasoro towers are symmetric.
    # L_0 = bar L_0 = M L / 2.
    L0 = M * ads_radius / 2.0
    s_left = cardy_formula(central_charge=c, conformal_weight=L0)
    s_right = cardy_formula(central_charge=c, conformal_weight=L0)
    s_cardy = s_left + s_right

    return s_bh, s_cardy, abs(s_bh - s_cardy)
