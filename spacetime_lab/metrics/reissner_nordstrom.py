"""Reissner-Nordström metric — static, spherically symmetric, electrically charged.

References:
    Wald, "General Relativity", §6.4 ("The Reissner-Nordström solution")
    Misner, Thorne, Wheeler, "Gravitation", §31.5
    Carroll, "Spacetime and Geometry", §5.7
    Reissner 1916; Nordström 1918 (originals)

The Reissner-Nordström metric is the unique static, spherically symmetric,
asymptotically-flat solution of the Einstein-Maxwell equations sourced by a
point charge Q sitting at the origin.  It generalizes Schwarzschild to
include a stress-energy contribution from the electromagnetic field of the
charge:

    ds^2 = -f(r) dt^2 + f(r)^{-1} dr^2 + r^2 dOmega^2,
    f(r) = 1 - 2M/r + Q^2/r^2.

The two roots f(r_±) = 0 give the **outer (event) horizon** r_+ and the
**inner (Cauchy) horizon** r_- :

    r_± = M ± sqrt(M^2 - Q^2).

Cosmic censorship (the analogue of |a| ≤ M for Kerr) requires |Q| ≤ M.
At Q = M the two horizons coincide at r = M — the **extremal** limit, with
zero Hawking temperature.  At Q > M the metric is a naked singularity and is
forbidden by the cosmic censorship hypothesis.

Schwarzschild limit: Q = 0 reduces to f = 1 - 2M/r exactly, so r_+ = 2M,
r_- = 0, ISCO = 6M, photon sphere = 3M, T_H = 1/(8πM), S = 4πM².

Phase 4-deferred-since-forever module, finally landed in v3.1.
"""

from __future__ import annotations

import math

import numpy as np
import sympy as sp

from spacetime_lab.metrics.base import Metric


class ReissnerNordstrom(Metric):
    """The Reissner-Nordström metric for a static, charged BH.

    Args:
        mass: BH mass parameter M, in geometric units G = c = 1. Must be > 0.
        charge: Electric charge Q, same dimensions as M (length).  Must
                satisfy |Q| ≤ M (cosmic censorship).  Default 0 — recovers
                Schwarzschild.

    Attributes:
        mass: Numerical mass parameter.
        charge: Numerical charge parameter (always stored as float ≥ 0;
                magnitude is what matters geometrically since Q only enters
                squared).

    Example:
        >>> bh = ReissnerNordstrom(mass=1.0, charge=0.6)
        >>> round(bh.outer_horizon(), 6)
        1.8
        >>> round(bh.inner_horizon(), 6)
        0.2
        >>> bh = ReissnerNordstrom(mass=1.0, charge=0.0)
        >>> bh.outer_horizon()  # Schwarzschild limit
        2.0
    """

    # ──────────────────────────────────────────────────────────────
    # Construction
    # ──────────────────────────────────────────────────────────────

    def __init__(self, mass: float, charge: float = 0.0) -> None:
        super().__init__()
        if not isinstance(mass, (int, float)):
            raise TypeError(f"mass must be a real number, got {type(mass).__name__}")
        if not isinstance(charge, (int, float)):
            raise TypeError(f"charge must be a real number, got {type(charge).__name__}")
        if mass <= 0:
            raise ValueError(f"mass must be positive, got {mass}")
        # Store |Q|; the metric only ever depends on Q²
        if abs(charge) > mass:
            raise ValueError(
                f"|charge| must satisfy |Q| <= M (cosmic censorship), "
                f"got |Q|={abs(charge)}, M={mass}"
            )

        self.mass: float = float(mass)
        self.charge: float = float(abs(charge))

        self._t = sp.Symbol("t", real=True)
        self._r = sp.Symbol("r", positive=True)
        self._theta = sp.Symbol("theta", positive=True)
        self._phi = sp.Symbol("phi", real=True)

        self._metric_cache: sp.Matrix | None = None

    # ──────────────────────────────────────────────────────────────
    # Abstract methods from Metric base class
    # ──────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "Reissner-Nordström"

    @property
    def coordinates(self) -> list[sp.Symbol]:
        return [self._t, self._r, self._theta, self._phi]

    @property
    def metric_tensor(self) -> sp.Matrix:
        """Reissner-Nordström metric in Schwarzschild-like coordinates."""
        if self._metric_cache is not None:
            return self._metric_cache

        M = self.mass
        Q = self.charge
        r = self._r
        theta = self._theta

        f = 1 - 2 * M / r + Q ** 2 / r ** 2

        g = sp.Matrix([
            [-f, 0, 0, 0],
            [0, 1 / f, 0, 0],
            [0, 0, r ** 2, 0],
            [0, 0, 0, r ** 2 * sp.sin(theta) ** 2],
        ])

        self._metric_cache = g
        return g

    # ──────────────────────────────────────────────────────────────
    # Horizons (closed form)
    # ──────────────────────────────────────────────────────────────

    def outer_horizon(self) -> float:
        """Outer (event) horizon r_+ = M + sqrt(M² - Q²)."""
        return self.mass + math.sqrt(self.mass ** 2 - self.charge ** 2)

    def inner_horizon(self) -> float:
        """Inner (Cauchy) horizon r_- = M - sqrt(M² - Q²).

        For Q = 0 this returns 0 (Schwarzschild has no inner horizon)."""
        return self.mass - math.sqrt(self.mass ** 2 - self.charge ** 2)

    @property
    def is_extremal(self) -> bool:
        """True iff |Q| == M (within float tolerance)."""
        return abs(self.charge - self.mass) < 1e-12

    # ──────────────────────────────────────────────────────────────
    # Photon sphere (closed form)
    # ──────────────────────────────────────────────────────────────

    def photon_sphere(self) -> float:
        """Outer photon sphere r_γ.

        Solving the circular null geodesic condition gives a quadratic
        in r whose two roots are the *outer* and *inner* photon spheres.
        The outer one (the only one outside the event horizon for
        |Q| < M) is

            r_γ = (3M + sqrt(9M² - 8Q²)) / 2.

        At Q = 0 this collapses to 3M.  At extremal Q = M the outer
        photon sphere sits at r_γ = (3 + 1)/2·M = 2M = r_+ — it merges
        with the horizon.
        """
        return 0.5 * (3 * self.mass + math.sqrt(9 * self.mass ** 2 - 8 * self.charge ** 2))

    # ──────────────────────────────────────────────────────────────
    # ISCO (numerical via the effective potential)
    # ──────────────────────────────────────────────────────────────

    def isco(self) -> float:
        """Innermost Stable Circular Orbit (ISCO) for massive timelike
        geodesics in RN.

        Standard ISCO condition (Wald §6.3 generalised; equivalent to
        Sundman's stability criterion ``dL_circ²/dr = 0``):

            For a circular orbit at radius r, the angular-momentum
            squared is
                L²_circ(r) = (M r³ - Q² r²) / (r² - 3Mr + 2Q²).
            ISCO is the smallest r > r_+ where dL²_circ/dr = 0.

        We compute the derivative *analytically* and root-find with
        scipy.optimize.brentq on a tight bracket.  This gives
        machine-precision accuracy (≤ 1e-12) instead of the ~1e-6
        floor that finite-differencing V'' would impose.

        Schwarzschild limit (Q=0): the condition collapses to
        r² - 6Mr = 0 → r = 6M (or r = 0), so ISCO = 6M exactly.
        """
        from scipy.optimize import brentq

        M = self.mass
        Q = self.charge

        # u(r) = M r³ - Q² r²,   v(r) = r² - 3Mr + 2Q²
        # L²_circ = u/v;  d(L²)/dr = (u' v - u v') / v²
        #
        # We only need the numerator's sign for root-finding because v² > 0
        # outside the photon sphere (where v changes sign).  So define
        #     dL2_num(r) = u'(r) v(r) - u(r) v'(r)
        # which is a polynomial in r and machine-precision evaluable.
        def dL2_num(r: float) -> float:
            u = M * r ** 3 - Q ** 2 * r ** 2
            up = 3 * M * r ** 2 - 2 * Q ** 2 * r
            v = r ** 2 - 3 * M * r + 2 * Q ** 2
            vp = 2 * r - 3 * M
            return up * v - u * vp

        # Bracket: just outside the photon sphere (where v → 0+) up to
        # 12M (more than enough — Schwarzschild ISCO is 6M; ISCO
        # decreases with Q).
        r_lo = self.photon_sphere() * 1.0001
        r_hi = 12.0 * M

        f_lo = dL2_num(r_lo)
        f_hi = dL2_num(r_hi)

        # If we don't bracket directly, scan for a sign change.
        if not (math.isfinite(f_lo) and math.isfinite(f_hi)) or f_lo * f_hi > 0:
            rs = np.linspace(r_lo, r_hi, 400)
            for i in range(len(rs) - 1):
                a, b = float(rs[i]), float(rs[i + 1])
                fa, fb = dL2_num(a), dL2_num(b)
                if math.isfinite(fa) and math.isfinite(fb) and fa * fb < 0:
                    return float(brentq(dL2_num, a, b, xtol=1e-12, rtol=1e-12))
            raise RuntimeError(
                f"ISCO bracket failed for M={M}, Q={Q}: "
                f"dL²/dr({r_lo})={f_lo}, dL²/dr({r_hi})={f_hi}"
            )
        return float(brentq(dL2_num, r_lo, r_hi, xtol=1e-12, rtol=1e-12))

    # ──────────────────────────────────────────────────────────────
    # Thermodynamics
    # ──────────────────────────────────────────────────────────────

    def surface_gravity(self) -> float:
        """Surface gravity at the outer horizon.

            κ = (r_+ - r_-) / (2 r_+²).
        """
        rp = self.outer_horizon()
        rm = self.inner_horizon()
        return (rp - rm) / (2.0 * rp ** 2)

    def hawking_temperature(self) -> float:
        """Hawking temperature T_H = κ / (2π)."""
        return self.surface_gravity() / (2.0 * math.pi)

    def bekenstein_hawking_entropy(self) -> float:
        """Bekenstein-Hawking entropy S = A/4 = π r_+²."""
        return math.pi * self.outer_horizon() ** 2

    def horizon_area(self) -> float:
        """Outer horizon area A = 4π r_+²."""
        return 4.0 * math.pi * self.outer_horizon() ** 2

    # ──────────────────────────────────────────────────────────────
    # Output
    # ──────────────────────────────────────────────────────────────

    def line_element_latex(self) -> str:
        return (
            r"ds^2 = -\left(1 - \frac{2M}{r} + \frac{Q^2}{r^2}\right) dt^2 "
            r"+ \left(1 - \frac{2M}{r} + \frac{Q^2}{r^2}\right)^{-1} dr^2 "
            r"+ r^2 \, d\Omega^2"
        )

    def __repr__(self) -> str:
        return f"ReissnerNordstrom(mass={self.mass}, charge={self.charge})"
