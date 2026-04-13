r"""Replica wormhole on-shell actions and the island formula at n=1.

**v2.0 patch** — second of the three v2.0 modules.  Implements a
numerical version of the replica-wormhole calculation that derives
the island formula from a Euclidean path integral.

Background
==========

The Rényi entropy :math:`S_n = \tfrac{1}{1-n} \log Z_n` is computed
from a partition function :math:`Z_n` on an :math:`n`-fold replicated
manifold.  In Euclidean JT gravity + bath, :math:`Z_n` receives
contributions from two kinds of saddle:

- **Disconnected saddle**: :math:`n` copies of the single-replica
  disk, no topology change.  Contributes
  :math:`Z_n^{\text{disc}} = (Z_1)^n \cdot \langle \cdots \rangle`
  and gives the Hawking-like rising entropy when analytically
  continued to :math:`n = 1`.
- **Connected (replica-wormhole) saddle**: a handle attaches
  replica copies to each other, adding a new area term of size
  :math:`\text{Area}(\partial X)/(4 G_N)` per handle.  Gives the
  island-like *area-bounded* entropy when continued to :math:`n = 1`.

At :math:`n = 1`, the dominant saddle (smallest action) wins, and
the entropy is :math:`\min` over saddles — exactly the outer
``min`` in the island formula.

What this module provides (numerical, not analytical)
=====================================================

We do not re-derive the replica wormhole Euclidean path integral
in the code — that is analytical and belongs in a textbook.  What
we DO provide:

- :func:`disconnected_saddle_entropy` — the :math:`n=1` entropy
  of :math:`n` disconnected disks, equivalent to the no-island
  saddle of the island formula.  Grows linearly with time.
- :func:`connected_saddle_entropy` — the :math:`n=1` entropy of
  the replica wormhole, bounded by :math:`\text{Area}/(4 G_N)`.
  Time-independent for an eternal BH.
- :func:`replica_island_saddle` — takes ``min`` of both saddles
  and reports the winner, recovering the island formula.
- :func:`verify_replica_at_n_equals_1` — numerical check that the
  replica entropies reduce to the expected eternal-BH Page-curve
  limits (``S_disc = S_Hawking``, ``S_conn = 2 S_BH`` in the TFD
  convention).

The goal of this module is **not** to be a rigorous derivation; it
is to provide a numerical *cross-check* that the island formula
(Phase 9 and v2.0) and the replica-wormhole picture agree where
they overlap.

Honest scope
============

- **No full path integral computation** — we use closed-form on-shell
  actions where those are known (JT gravity), and schematic
  expressions elsewhere.
- **No fluctuations beyond the saddle** — we work at leading order
  in :math:`G_N`.
- **No island formula rederivation** — we *verify* consistency,
  assuming the island formula is correct (which it is,
  independently established by AEMM 2019 and Penington 2019).

References
==========
- Penington, Shenker, Stanford, Yang, *Replica wormholes and the
  black hole interior*, JHEP **03** 205 (2022), arXiv:1911.11977.
- Almheiri, Hartman, Maldacena, Shaghoulian, Tajdini, *Replica
  Wormholes and the Entropy of Hawking Radiation*, JHEP **05** 013
  (2020), arXiv:1911.12333.
"""

from __future__ import annotations

import math


# ─────────────────────────────────────────────────────────────────────
# Disconnected (Hawking-like) and connected (island-like) saddles
# ─────────────────────────────────────────────────────────────────────


def disconnected_saddle_entropy(
    t: float,
    beta: float,
    central_charge: float,
) -> float:
    r"""Entropy of the disconnected replica saddle (no-island, Hawking).

    At leading order in :math:`G_N` and the large-:math:`c` limit,
    the disconnected saddle produces a linearly growing Hawking
    entropy

    .. math::

        S_\text{disc}(t) \;=\; \frac{2\pi c}{3 \beta}\, t,

    matching the Hartman-Maldacena 2013 late-time slope of Phase 9's
    trivial saddle.  For :math:`t \ge 0`, never saturates.
    """
    if beta <= 0:
        raise ValueError(f"beta must be positive, got {beta}")
    if central_charge <= 0:
        raise ValueError(
            f"central_charge must be positive, got {central_charge}"
        )
    if t < 0:
        raise ValueError(f"t must be non-negative, got {t}")
    return 2.0 * math.pi * central_charge * t / (3.0 * beta)


def connected_saddle_entropy(
    horizon_radius: float,
    G_N: float = 1.0,
) -> float:
    r"""Entropy of the connected (replica-wormhole) saddle.

    The replica wormhole contributes :math:`2 S_{BH}` to the
    :math:`n=1` entropy — twice the horizon's Bekenstein-Hawking
    entropy, because the wormhole connects the two sides of the
    thermofield double through the bifurcation surface.

    .. math::

        S_\text{conn} \;=\; \frac{\pi r_+}{G_N}
                     \;=\; 2 \cdot \frac{\pi r_+}{2 G_N}
                     \;=\; 2 S_{BH}.

    This matches :func:`spacetime_lab.holography.island.island_saddle_entropy`
    from Phase 9 exactly; the replica-wormhole derivation provides
    the first-principles justification for that hand-identified
    value.
    """
    if horizon_radius <= 0:
        raise ValueError(
            f"horizon_radius must be positive, got {horizon_radius}"
        )
    if G_N <= 0:
        raise ValueError(f"G_N must be positive, got {G_N}")
    return math.pi * horizon_radius / G_N


def replica_island_saddle(
    t: float,
    horizon_radius: float,
    beta: float,
    central_charge: float,
    G_N: float = 1.0,
) -> dict:
    r"""Min over disconnected and connected saddles — the island formula.

    The outer ``min`` of the island formula comes out of the replica
    calculation as the competition between two topological sectors:
    disconnected (early times) versus connected (late times).  At
    the **Page time** the two saddles cross and the winner changes.

    Returns
    -------
    dict
        ``{s_disc, s_conn, winner, s_rad, page_time}`` where
        ``page_time = 3 beta r_+ / (2 G_N c)`` is the crossing
        :math:`S_\text{disc}(t_P) = S_\text{conn}`.
    """
    s_disc = disconnected_saddle_entropy(t, beta, central_charge)
    s_conn = connected_saddle_entropy(horizon_radius, G_N=G_N)
    if s_disc < s_conn:
        winner, total = "disconnected", s_disc
    else:
        winner, total = "connected", s_conn
    # Analytic Page time: 2 pi c t_P / (3 beta) = pi r_+ / G_N
    # => t_P = 3 beta r_+ / (2 c G_N)
    t_page = 3.0 * beta * horizon_radius / (2.0 * central_charge * G_N)
    return {
        "s_disc": s_disc,
        "s_conn": s_conn,
        "winner": winner,
        "s_rad": total,
        "page_time": t_page,
    }


# ─────────────────────────────────────────────────────────────────────
# Consistency with Phase 9 island formula
# ─────────────────────────────────────────────────────────────────────


def verify_replica_at_n_equals_1(
    horizon_radius: float = 1.0,
    beta: float = 2.0 * math.pi,
    central_charge: float = 6.0,
    G_N: float = 1.0,
) -> dict:
    r"""Verify that the replica n=1 entropies match Phase 9 island formula.

    Two bit-exact cross-checks:

    1. :func:`connected_saddle_entropy` == Phase 9's
       :func:`island_saddle_entropy`
       (both are :math:`2 S_{BH} = \pi r_+/G_N`).
    2. :func:`disconnected_saddle_entropy` late-time slope ==
       :func:`hartman_maldacena_growth_rate` from Phase 9
       (both are :math:`2 \pi c / (3 \beta)`).

    These two identities are the whole content of the replica
    derivation reducing to Phase 9's hand-identified saddles.
    """
    from spacetime_lab.holography.island import (
        hartman_maldacena_growth_rate,
        island_saddle_entropy,
    )

    # Check 1: connected saddle == Phase 9 island saddle
    s_conn = connected_saddle_entropy(horizon_radius, G_N=G_N)
    s_island_phase9 = island_saddle_entropy(
        horizon_radius, G_N=G_N
    )
    saddle_residual = abs(s_conn - s_island_phase9)

    # Check 2: disconnected late-time slope == HM growth rate
    # S_disc(t) = (2 pi c / 3 beta) * t, so dS/dt = 2 pi c / 3 beta
    dt = 1.0
    slope_disc = (
        disconnected_saddle_entropy(dt, beta, central_charge)
        - disconnected_saddle_entropy(0.0, beta, central_charge)
    ) / dt
    slope_phase9 = hartman_maldacena_growth_rate(
        central_charge=central_charge, beta=beta
    )
    slope_residual = abs(slope_disc - slope_phase9)

    return {
        "s_connected": s_conn,
        "s_island_phase9": s_island_phase9,
        "saddle_residual": saddle_residual,
        "slope_disconnected": slope_disc,
        "slope_phase9_hm": slope_phase9,
        "slope_residual": slope_residual,
    }
