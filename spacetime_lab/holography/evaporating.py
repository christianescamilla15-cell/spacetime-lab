r"""The evaporating-BH Page curve (v1.1 patch).

Phase 9 (the v1.0 milestone) shipped the Page curve for an **eternal**
BTZ thermofield double, where the disconnected/island saddle is the
constant :math:`2 S_{BH}` and the curve *rises and saturates* rather
than rises and falls.  This module is the **v1.1** extension: the
**evaporating** Schwarzschild Page curve, where the BH actually
shrinks and the radiation entropy returns to zero at the end of
evaporation.

The full Page curve, qualitatively
==================================

For an evaporating BH there are two competing saddles:

- **Hawking / no-island saddle**:  the radiation, treated thermally,
  carries away the entropy lost by the BH.  Monotonically increasing
  from :math:`0` to :math:`S_{BH}(0)` as the BH evaporates.
- **Island / quantum-extremal-surface saddle**:  the bulk QES contributes
  :math:`A(t)/(4 G_N) = S_{BH}(t)`, the *current* horizon area entropy.
  This *decreases* with time as the BH shrinks.

The Page curve (Penington 2019, AEMM 2019) is the minimum:

.. math::

    S_\text{rad}(t) = \min\!\left(S_\text{H}(t),\, S_\text{island}(t)\right).

The two saddles cross at the **Page time** :math:`t_P`, where the BH
has lost half its initial entropy.  Before :math:`t_P` the Hawking
saddle wins (entropy rises like the radiation count).  After
:math:`t_P` the island saddle wins (entropy falls with the shrinking
BH area).  The curve is shaped like a **bell** that closes back to
zero at :math:`t = t_\text{evap}`, recovering unitarity.

This is the qualitative resolution of the 49-year-old Hawking
information paradox in its simplest possible form.

The Schwarzschild evaporation law (Page 1976)
=============================================

A 4D Schwarzschild BH radiates with Hawking temperature
:math:`T_H = 1/(8\pi M)` (in :math:`G = c = \hbar = 1`).  The
Stefan-Boltzmann power emitted is :math:`P \propto T^4 A \propto
1/M^2`, so :math:`dM/dt \propto -1/M^2`.  Integrating with
:math:`M(0) = M_0` and :math:`M(t_\text{evap}) = 0` gives the
**cubic shrinking law**

.. math::

    M(t) = M_0\,(1 - t/t_\text{evap})^{1/3},

with the closed-form lifetime (Page 1976, including only photons in
the simplest count)

.. math::

    t_\text{evap} = \frac{5120\,\pi\,G^2 M_0^3}{\hbar c^4}
                  \;\xrightarrow{G=c=\hbar=1}\;
                  5120\,\pi\,M_0^3.

We use the canonical Page 1976 prefactor as the default, but it can
be overridden via the ``t_evap`` argument: the **shape** of the Page
curve is independent of this normalisation, only the timescale is
set by it.

Closed-form invariants pinned by the gates
==========================================

For the toy model :math:`M(t) = M_0 (1 - t/t_\text{evap})^{1/3}` and
:math:`S_{BH} = 4\pi M^2`, every gate has an exact closed-form
prediction:

============================  =====================================
Quantity                      Closed form
============================  =====================================
:math:`S_\text{rad}(0)`       :math:`0`
:math:`S_\text{rad}(t_evap)`  :math:`0`
:math:`M(t_P)`                :math:`M_0/\sqrt{2}`
:math:`S_{BH}(t_P)`           :math:`S_{BH}(0)/2 = 2\pi M_0^2`
:math:`S_\text{rad,max}`      :math:`S_{BH}(0)/2 = 2\pi M_0^2`
:math:`t_P / t_\text{evap}`   :math:`1 - \sqrt{2}/4 \approx 0.6464`
============================  =====================================

The Page time is **not** at the midpoint of evaporation: because
:math:`S_{BH} \propto M^2` falls faster than linearly in :math:`M`,
the crossover happens at :math:`t_P = (1 - \sqrt{2}/4)\,t_\text{evap}
\approx 0.6464\,t_\text{evap}`, not at :math:`t_\text{evap}/2`.
This is one of the visually striking features of the bell-shaped
curve and is testable bit-exactly.

Honest scope notes
==================

This is the **simplest** non-trivial evaporating Page curve, not the
state of the art.  The following are explicitly out of scope and
deferred to later patches:

- **JT gravity + CFT bath setup** (Penington / AEMM original 2D
  models) — deferred to v2.0 along with the QES finder.
- **Replica wormhole derivation** — analytical, not coded.
- **Backreaction of the radiation on the geometry** — we assume
  quasi-static evaporation throughout.
- **Grey-body factors** — Page 1976 includes them; they shift the
  prefactor of :math:`t_\text{evap}` by an :math:`O(1)` factor but
  do not change the cubic shape or the bell-curve qualitative
  result.
- **Higher-dimensional BHs** — the cubic law :math:`M^3 \propto t`
  is specific to :math:`D = 4`.
- **Effective number of radiating species** — folded into the
  ``t_evap`` parameter; not modelled separately.

What this module **does** establish, bit-exactly:

1. Two saddles compete throughout the evaporation.
2. The Page curve is the minimum of the two.
3. The curve is bell-shaped, peaking at the closed-form
   :math:`t_P = (1 - \sqrt{2}/4)\,t_\text{evap}`.
4. The maximum entropy is exactly :math:`S_{BH}(0)/2`.
5. The curve closes to zero at :math:`t_\text{evap}`, proving
   unitarity in the toy model.

References
==========
- Page, *Particle emission rates from a black hole: massless particles
  from an uncharged, nonrotating hole*, Phys. Rev. D **13** 198 (1976).
- Penington, *Entanglement wedge reconstruction and the information
  paradox*, J. High Energy Phys. **09** 002 (2020), arXiv:1905.08255.
- Almheiri, Engelhardt, Marolf, Maxfield, *The entropy of bulk quantum
  fields and the entanglement wedge of an evaporating black hole*,
  J. High Energy Phys. **12** 063 (2019), arXiv:1905.08762.
- Almheiri, Hartman, Maldacena, Shaghoulian, Tajdini, *The entropy of
  Hawking radiation*, Rev. Mod. Phys. **93** 035002 (2021),
  arXiv:2006.06872 (the canonical review).
- Hawking radiation, Wikipedia article — convenient reference for the
  Page 1976 :math:`t_\text{evap}` numerical prefactor used as our
  default.
"""

from __future__ import annotations

import math


# Page 1976 numerical prefactor for the Schwarzschild evaporation
# time in geometric units (G = c = hbar = 1).  The full formula in SI
# units is t_evap = (5120 pi G^2 M^3) / (hbar c^4); the dimensionful
# constants drop out under our convention.
PAGE_1976_PREFACTOR: float = 5120.0 * math.pi


# ─────────────────────────────────────────────────────────────────────
# Schwarzschild evaporation law (Page 1976)
# ─────────────────────────────────────────────────────────────────────


def schwarzschild_evaporation_time(
    initial_mass: float,
    G_N: float = 1.0,
) -> float:
    r"""Closed-form Schwarzschild evaporation lifetime (Page 1976).

    In geometric units :math:`G = c = \hbar = 1`,

    .. math::

        t_\text{evap} = 5120\,\pi\, G_N^{2}\, M_0^{3}.

    The :math:`G_N^2` factor is kept explicit so the user can vary
    Newton's constant for cross-checks; the SI prefactor is
    :math:`5120 \pi / (\hbar c^4)` and reduces to
    :math:`5120 \pi` in our units when :math:`G_N = 1`.

    Parameters
    ----------
    initial_mass : float
        Initial BH mass :math:`M_0` in geometric units.
    G_N : float, optional
        Newton's constant.  Default ``1.0``.

    Returns
    -------
    float
        :math:`t_\text{evap}` in geometric units.

    Examples
    --------
    >>> import math
    >>> t = schwarzschild_evaporation_time(1.0)
    >>> math.isclose(t, 5120.0 * math.pi)
    True
    """
    if initial_mass <= 0:
        raise ValueError(
            f"initial_mass must be positive, got {initial_mass}"
        )
    if G_N <= 0:
        raise ValueError(f"G_N must be positive, got {G_N}")
    return PAGE_1976_PREFACTOR * G_N * G_N * initial_mass**3


def schwarzschild_mass(
    t: float,
    initial_mass: float,
    G_N: float = 1.0,
    t_evap: float | None = None,
) -> float:
    r"""Mass of a Schwarzschild BH at time :math:`t` during evaporation.

    The cubic shrinking law follows from integrating
    :math:`dM/dt \propto -1/M^2` with :math:`M(0) = M_0` and
    :math:`M(t_\text{evap}) = 0`:

    .. math::

        M(t) = M_0\,(1 - t/t_\text{evap})^{1/3}.

    Outside :math:`[0, t_\text{evap}]` the mass is clamped to zero
    (the BH has fully evaporated).  Negative :math:`t` raises a
    ``ValueError``.

    Parameters
    ----------
    t : float
        Time :math:`\ge 0` in geometric units.
    initial_mass : float
        Initial mass :math:`M_0`.
    G_N : float, optional
        Newton's constant, used only if ``t_evap`` is not supplied.
    t_evap : float, optional
        Override the Page 1976 default lifetime.  Useful for studying
        the shape of the curve at a different timescale, or for
        accounting for grey-body factors / multiple radiation species
        without rescaling :math:`G_N`.

    Returns
    -------
    float
        :math:`M(t)`.  Returns ``0.0`` cleanly for
        :math:`t \ge t_\text{evap}`.
    """
    if initial_mass <= 0:
        raise ValueError(
            f"initial_mass must be positive, got {initial_mass}"
        )
    if t < 0:
        raise ValueError(f"t must be non-negative, got {t}")
    if t_evap is None:
        t_evap = schwarzschild_evaporation_time(initial_mass, G_N=G_N)
    if t_evap <= 0:
        raise ValueError(f"t_evap must be positive, got {t_evap}")
    if t >= t_evap:
        return 0.0
    return initial_mass * (1.0 - t / t_evap) ** (1.0 / 3.0)


def bekenstein_hawking_entropy(
    mass: float,
    G_N: float = 1.0,
) -> float:
    r"""Bekenstein-Hawking entropy of a Schwarzschild BH.

    .. math::

        S_{BH} = \frac{A}{4 G_N}
               = \frac{4\pi r_s^2}{4 G_N}
               = \frac{4\pi M^2}{G_N},

    where :math:`r_s = 2 G_N M` is the Schwarzschild radius.  At
    :math:`G_N = 1`, :math:`S_{BH} = 4\pi M^2`.  Returns ``0.0`` at
    :math:`M = 0` (fully evaporated BH).

    This is the *universal factor of* :math:`1/(4 G_N)` that ties
    every phase of Spacetime Lab together — Bekenstein-Hawking,
    Brown-Henneaux, Cardy-Strominger, Ryu-Takayanagi, and the area
    term in the island formula all share this normalisation.
    """
    if mass < 0:
        raise ValueError(f"mass must be non-negative, got {mass}")
    if G_N <= 0:
        raise ValueError(f"G_N must be positive, got {G_N}")
    return 4.0 * math.pi * mass * mass / G_N


# ─────────────────────────────────────────────────────────────────────
# The two saddles for the evaporating BH
# ─────────────────────────────────────────────────────────────────────


def hawking_saddle_entropy(
    t: float,
    initial_mass: float,
    G_N: float = 1.0,
    t_evap: float | None = None,
) -> float:
    r"""No-island (Hawking) saddle for the evaporating BH.

    Treating the radiation as thermal, the radiation entropy in the
    absence of any island contribution is the entropy *lost* by the
    BH so far:

    .. math::

        S_\text{H}(t) = S_{BH}(0) - S_{BH}(t)
                      = \frac{4\pi}{G_N}\,(M_0^2 - M(t)^2).

    This is the Penington 2019 "no-island" saddle.  It rises
    monotonically from :math:`0` at :math:`t = 0` to
    :math:`S_{BH}(0)` at :math:`t = t_\text{evap}`, and is the
    quantity that *would* keep growing forever in Hawking's original
    semi-classical calculation.

    Parameters
    ----------
    t : float
        Time :math:`\ge 0`.
    initial_mass : float
        Initial mass :math:`M_0`.
    G_N : float, optional
        Newton's constant.
    t_evap : float, optional
        Override the Page 1976 default lifetime.
    """
    if t_evap is None:
        t_evap = schwarzschild_evaporation_time(initial_mass, G_N=G_N)
    M_t = schwarzschild_mass(t, initial_mass, G_N=G_N, t_evap=t_evap)
    s_bh_0 = bekenstein_hawking_entropy(initial_mass, G_N=G_N)
    s_bh_t = bekenstein_hawking_entropy(M_t, G_N=G_N)
    return s_bh_0 - s_bh_t


def island_saddle_entropy_evaporating(
    t: float,
    initial_mass: float,
    G_N: float = 1.0,
    t_evap: float | None = None,
) -> float:
    r"""Island / QES saddle for the evaporating BH.

    The quantum extremal surface contribution to the radiation
    entropy in the simplest model is the area term

    .. math::

        S_\text{island}(t) = \frac{A(t)}{4 G_N} = S_{BH}(t)
                           = \frac{4\pi M(t)^2}{G_N},

    i.e. the *current* Bekenstein-Hawking entropy of the shrinking
    BH (Penington 2019 §2-3, AEMM 2019).  We drop the bulk
    semi-classical entropy :math:`S_\text{bulk}(\partial X)` of the
    QES boundary, which is sub-leading in the toy model.

    This decreases monotonically from :math:`S_{BH}(0)` at
    :math:`t = 0` to :math:`0` at :math:`t = t_\text{evap}`, and
    eventually wins the :math:`\min` competition against the
    Hawking saddle.

    Note the contrast with the eternal-BH version (the v1.0 island
    formula in :mod:`spacetime_lab.holography.island`), where the
    horizon area is constant and the island saddle is the constant
    :math:`2 S_{BH}` instead of a shrinking single :math:`S_{BH}`.
    The factor-of-2 difference comes from the eternal BH's two-sided
    thermofield double doubling the bifurcation surface area; for an
    evaporating one-sided BH there is only one horizon contribution.
    """
    if t_evap is None:
        t_evap = schwarzschild_evaporation_time(initial_mass, G_N=G_N)
    M_t = schwarzschild_mass(t, initial_mass, G_N=G_N, t_evap=t_evap)
    return bekenstein_hawking_entropy(M_t, G_N=G_N)


# ─────────────────────────────────────────────────────────────────────
# The Page curve (bell-shaped) and the Page time
# ─────────────────────────────────────────────────────────────────────


def page_curve_evaporating(
    t: float,
    initial_mass: float,
    G_N: float = 1.0,
    t_evap: float | None = None,
) -> tuple[float, str]:
    r"""Bell-shaped Page curve for the evaporating Schwarzschild BH.

    .. math::

        S_\text{rad}(t) = \min\!\left(S_\text{H}(t),\,
                                       S_\text{island}(t)\right).

    Returns the entropy and the label of the winning saddle.  Early
    times (:math:`t < t_P`) are in the ``"hawking"`` phase: the
    rising no-island saddle is below the falling island saddle.
    Late times (:math:`t > t_P`) are in the ``"island"`` phase: the
    falling island saddle is below the rising Hawking saddle.

    The curve is bell-shaped: zero at the endpoints, peak at the
    closed-form Page time :math:`t_P = (1 - \sqrt{2}/4)\,t_\text{evap}`.

    Parameters
    ----------
    t : float
        Time :math:`\ge 0`.
    initial_mass : float
        Initial mass :math:`M_0`.
    G_N : float, optional
        Newton's constant.
    t_evap : float, optional
        Override the Page 1976 default lifetime.

    Returns
    -------
    entropy : float
        :math:`S_\text{rad}(t)`.
    phase : str
        ``"hawking"`` if the no-island saddle wins, ``"island"`` if
        the QES saddle wins.
    """
    if t_evap is None:
        t_evap = schwarzschild_evaporation_time(initial_mass, G_N=G_N)
    s_h = hawking_saddle_entropy(t, initial_mass, G_N=G_N, t_evap=t_evap)
    s_i = island_saddle_entropy_evaporating(
        t, initial_mass, G_N=G_N, t_evap=t_evap
    )
    if s_h < s_i:
        return s_h, "hawking"
    return s_i, "island"


def page_time_evaporating(
    initial_mass: float,
    G_N: float = 1.0,
    t_evap: float | None = None,
) -> float:
    r"""Closed-form Page time for the evaporating Schwarzschild BH.

    The two saddles cross when the BH has lost half its initial
    entropy, i.e. when :math:`M(t_P)^2 = M_0^2/2`, equivalently
    :math:`M(t_P) = M_0/\sqrt{2}`.  Substituting into the cubic
    shrinking law :math:`M(t) = M_0(1 - t/t_\text{evap})^{1/3}`:

    .. math::

        \frac{1}{\sqrt{2}}
            = \left(1 - \frac{t_P}{t_\text{evap}}\right)^{1/3}
        \;\Longrightarrow\;
        \frac{t_P}{t_\text{evap}}
            = 1 - \frac{1}{2\sqrt{2}}
            = 1 - \frac{\sqrt{2}}{4}
            \approx 0.6464.

    The Page time is *not* at the midpoint of evaporation: because
    :math:`S_{BH} \propto M^2` decreases faster than linearly in
    :math:`M`, the crossover happens after the temporal midpoint.

    This function returns the closed-form value directly — no
    numerical root-finder is needed for this toy model.

    Returns
    -------
    float
        :math:`t_P > 0`.
    """
    if t_evap is None:
        t_evap = schwarzschild_evaporation_time(initial_mass, G_N=G_N)
    if t_evap <= 0:
        raise ValueError(f"t_evap must be positive, got {t_evap}")
    return t_evap * (1.0 - math.sqrt(2.0) / 4.0)


def page_time_evaporating_numerical(
    initial_mass: float,
    G_N: float = 1.0,
    t_evap: float | None = None,
) -> float:
    r"""Numerical Page time via :func:`scipy.optimize.brentq`.

    Independent cross-check on :func:`page_time_evaporating`: solves
    the transcendental equation :math:`S_\text{H}(t_P) =
    S_\text{island}(t_P)` directly.  The closed-form value and the
    numerical value must agree to ``1e-10`` — that is the bit-exact
    gate.

    This is the same verify-by-two-paths discipline used throughout
    Spacetime Lab (e.g., RT length vs Calabrese-Cardy in Phase 7,
    BTZ-Cardy match in Phase 8, HM-island crossing in Phase 9).
    """
    from scipy.optimize import brentq

    if t_evap is None:
        t_evap = schwarzschild_evaporation_time(initial_mass, G_N=G_N)

    def residual(t: float) -> float:
        s_h = hawking_saddle_entropy(
            t, initial_mass, G_N=G_N, t_evap=t_evap
        )
        s_i = island_saddle_entropy_evaporating(
            t, initial_mass, G_N=G_N, t_evap=t_evap
        )
        return s_h - s_i

    # The two saddles cross strictly inside (0, t_evap): at t=0 the
    # Hawking saddle is 0 and the island saddle is S_BH(0) > 0; at
    # t=t_evap the island saddle is 0 and the Hawking saddle is
    # S_BH(0) > 0.  By continuity there is a unique crossing.
    return float(brentq(residual, 1e-12 * t_evap, t_evap * (1 - 1e-12),
                        xtol=1e-12))


# ─────────────────────────────────────────────────────────────────────
# v1.1 gate verification
# ─────────────────────────────────────────────────────────────────────


def verify_evaporating_unitarity(
    initial_mass: float,
    G_N: float = 1.0,
    t_evap: float | None = None,
    n_samples: int = 1000,
) -> dict:
    r"""End-to-end gate test: verify the bell-shaped Page curve.

    Returns a dict of diagnostics with bit-exact closed-form
    predictions for every quantity.  Used by ``test_phase_v1_1.py``
    and by the closing cell of ``notebooks/10_evaporating_page_curve``.

    Verified invariants
    -------------------

    1. **Endpoint zeros**: :math:`S_\text{rad}(0) = 0` and
       :math:`S_\text{rad}(t_\text{evap}) = 0` (unitarity).
    2. **Page time**: closed-form value
       :math:`t_P = (1 - \sqrt{2}/4)\,t_\text{evap}`, and the
       numerical brentq result agrees to :math:`10^{-10}`.
    3. **Saddle continuity at** :math:`t_P`:
       :math:`S_\text{H}(t_P) = S_\text{island}(t_P)` to
       :math:`10^{-12}`.
    4. **Maximum entropy**: equals :math:`S_{BH}(0)/2 = 2\pi M_0^2`,
       attained at :math:`t_P`.
    5. **Mass at the Page time**: :math:`M(t_P) = M_0/\sqrt{2}` to
       :math:`10^{-12}`.
    6. **Phase ordering**: the curve is in the ``"hawking"`` phase
       for :math:`t < t_P` and in the ``"island"`` phase for
       :math:`t > t_P`.
    7. **Bell shape**: monotone non-decreasing on :math:`[0, t_P]`
       and monotone non-increasing on :math:`[t_P, t_\text{evap}]`.

    Parameters
    ----------
    initial_mass, G_N, t_evap
        See :func:`page_curve_evaporating`.
    n_samples : int
        Number of time samples for the shape diagnostics.  Default
        ``1000``.

    Returns
    -------
    dict
        Keys: ``"t_evap"``, ``"page_time_closed_form"``,
        ``"page_time_numerical"``, ``"page_time_residual"``,
        ``"mass_at_page_time"``, ``"mass_at_page_time_expected"``,
        ``"mass_residual"``, ``"hawking_at_page_time"``,
        ``"island_at_page_time"``, ``"continuity_residual"``,
        ``"max_entropy"``, ``"max_entropy_expected"``,
        ``"max_entropy_residual"``, ``"endpoint_zero_t0"``,
        ``"endpoint_zero_tevap"``, ``"phase_ordering_correct"``,
        ``"bell_shape_monotone"``.
    """
    if t_evap is None:
        t_evap = schwarzschild_evaporation_time(initial_mass, G_N=G_N)

    # 1. Page time, closed form vs numerical
    t_P_cf = page_time_evaporating(initial_mass, G_N=G_N, t_evap=t_evap)
    t_P_num = page_time_evaporating_numerical(
        initial_mass, G_N=G_N, t_evap=t_evap
    )
    page_time_residual = abs(t_P_cf - t_P_num)

    # 2. Mass at the Page time
    M_at_tP = schwarzschild_mass(
        t_P_cf, initial_mass, G_N=G_N, t_evap=t_evap
    )
    M_at_tP_expected = initial_mass / math.sqrt(2.0)
    mass_residual = abs(M_at_tP - M_at_tP_expected)

    # 3. Saddle continuity at t_P
    s_h_at_tP = hawking_saddle_entropy(
        t_P_cf, initial_mass, G_N=G_N, t_evap=t_evap
    )
    s_i_at_tP = island_saddle_entropy_evaporating(
        t_P_cf, initial_mass, G_N=G_N, t_evap=t_evap
    )
    continuity_residual = abs(s_h_at_tP - s_i_at_tP)

    # 4. Maximum entropy = S_BH(0)/2
    s_bh_0 = bekenstein_hawking_entropy(initial_mass, G_N=G_N)
    max_entropy_expected = s_bh_0 / 2.0
    s_max, _ = page_curve_evaporating(
        t_P_cf, initial_mass, G_N=G_N, t_evap=t_evap
    )
    max_entropy_residual = abs(s_max - max_entropy_expected)

    # 5. Endpoint zeros (unitarity)
    s_at_0, _ = page_curve_evaporating(
        0.0, initial_mass, G_N=G_N, t_evap=t_evap
    )
    s_at_evap, _ = page_curve_evaporating(
        t_evap, initial_mass, G_N=G_N, t_evap=t_evap
    )
    endpoint_zero_t0 = abs(s_at_0)
    endpoint_zero_tevap = abs(s_at_evap)

    # 6. Sample the curve and check phase ordering + bell shape
    times = [t_evap * i / (n_samples - 1) for i in range(n_samples)]
    entropies = []
    phases = []
    for t in times:
        s, phase = page_curve_evaporating(
            t, initial_mass, G_N=G_N, t_evap=t_evap
        )
        entropies.append(s)
        phases.append(phase)

    # Phase ordering: every sample at t < t_P should be hawking, every
    # sample at t > t_P should be island.  Allow exact-equality samples
    # at t_P itself to be either label (the min picks one of the two).
    phase_ordering_correct = True
    for i, t in enumerate(times):
        if t < t_P_cf - 1e-9 * t_evap and phases[i] != "hawking":
            phase_ordering_correct = False
            break
        if t > t_P_cf + 1e-9 * t_evap and phases[i] != "island":
            phase_ordering_correct = False
            break

    # Bell shape: monotone non-decreasing then non-increasing.  Use
    # the argmax of the *sampled* curve as the split index — the true
    # peak at t_P sits between two grid samples and the discrete
    # maximum can land on either side, so splitting on the closed-form
    # t_P alone gives a one-sample off-by-one false positive.
    i_argmax = max(range(len(entropies)), key=lambda i: entropies[i])
    rising = all(
        entropies[i + 1] >= entropies[i] - 1e-12
        for i in range(i_argmax)
    )
    falling = all(
        entropies[i + 1] <= entropies[i] + 1e-12
        for i in range(i_argmax, len(entropies) - 1)
    )
    bell_shape_monotone = rising and falling

    return {
        "t_evap": t_evap,
        "page_time_closed_form": t_P_cf,
        "page_time_numerical": t_P_num,
        "page_time_residual": page_time_residual,
        "mass_at_page_time": M_at_tP,
        "mass_at_page_time_expected": M_at_tP_expected,
        "mass_residual": mass_residual,
        "hawking_at_page_time": s_h_at_tP,
        "island_at_page_time": s_i_at_tP,
        "continuity_residual": continuity_residual,
        "max_entropy": s_max,
        "max_entropy_expected": max_entropy_expected,
        "max_entropy_residual": max_entropy_residual,
        "endpoint_zero_t0": endpoint_zero_t0,
        "endpoint_zero_tevap": endpoint_zero_tevap,
        "phase_ordering_correct": phase_ordering_correct,
        "bell_shape_monotone": bell_shape_monotone,
    }
