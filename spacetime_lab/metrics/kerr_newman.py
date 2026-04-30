"""Kerr-Newman metric — rotating + electrically charged BH.

The unique stationary, axisymmetric, asymptotically-flat solution of the
Einstein-Maxwell equations sourced by a point mass with both spin and
electric charge.  Combines Kerr's two-parameter (M, a) family with
Reissner-Nordström's charge Q.

References:
    Newman et al. 1965 (the original — "Metric of a rotating, charged mass")
    Wald, "General Relativity", §12.3
    Misner, Thorne, Wheeler, "Gravitation", §33
    Aliev & Galtsov 1981 (KN ISCO closed form)

Line element in Boyer-Lindquist coordinates (t, r, θ, φ):
    ds² = -(Δ - a² sin²θ)/Σ · dt² - (4 M a r - 2 Q² a)/Σ · sin²θ dt dφ
          + Σ/Δ · dr² + Σ · dθ² + ((r²+a²)² - Δ a² sin²θ)/Σ · sin²θ dφ²

where:
    Σ = r² + a² cos²θ                     (same as Kerr)
    Δ = r² - 2 M r + a² + Q²              (Kerr's Δ + Q²)

Limits:
    Q = 0          → recovers Kerr exactly
    a = 0          → recovers Reissner-Nordström exactly
    a = 0, Q = 0   → recovers Schwarzschild

Cosmic censorship: a² + Q² ≤ M².  Extremal at equality.

Horizons (closed form):
    r_± = M ± sqrt(M² - a² - Q²)

Hawking T = (r_+ - r_-) / (4π (r_+² + a²))
Bekenstein-Hawking entropy S = π (r_+² + a²)   (same form as Kerr)

ISCO is genuinely non-trivial in KN (no clean closed form except for
the Aliev-Galtsov 1981 polynomial expression).  Deferred to v3.2.1.
"""

from __future__ import annotations

import math

import sympy as sp

from spacetime_lab.metrics.base import Metric


class KerrNewman(Metric):
    """Kerr-Newman metric for a rotating, electrically charged BH.

    Args:
        mass: Mass parameter M (geometric units G = c = 1).  Must be > 0.
        spin: Specific angular momentum a = J/M (length).  Must be ≥ 0.
        charge: Electric charge |Q| (length).  Must be ≥ 0.

        Constraint: a² + Q² ≤ M² (cosmic censorship).

    Attributes:
        mass, spin, charge: float numerical parameters.

    Example:
        >>> bh = KerrNewman(mass=1.0, spin=0.5, charge=0.3)
        >>> round(bh.outer_horizon(), 6)
        1.812458
        >>> # Kerr limit: same as Kerr(1.0, 0.5)
        >>> kn = KerrNewman(mass=1.0, spin=0.5, charge=0.0)
        >>> round(kn.outer_horizon(), 6)
        1.866025
    """

    def __init__(self, mass: float, spin: float = 0.0, charge: float = 0.0) -> None:
        super().__init__()
        for name, val in [("mass", mass), ("spin", spin), ("charge", charge)]:
            if not isinstance(val, (int, float)):
                raise TypeError(f"{name} must be a real number, got {type(val).__name__}")
        if mass <= 0:
            raise ValueError(f"mass must be positive, got {mass}")
        if spin < 0:
            raise ValueError(f"spin must be non-negative, got {spin}")
        # Store |Q|
        Q = abs(charge)
        # Cosmic-censorship check with a small absolute tolerance.  Without
        # it, "exactly extremal" choices like (a=0.6, Q=0.8, M=1) fail
        # because 0.6² + 0.8² = 1.0000000000000002 > 1.0 in IEEE 754.
        # Tolerance matches `is_extremal` (1e-12).
        if spin * spin + Q * Q > mass * mass + 1e-12:
            raise ValueError(
                f"a² + Q² must satisfy a² + Q² <= M² (cosmic censorship), "
                f"got a²+Q²={spin**2 + Q**2}, M²={mass**2}"
            )

        self.mass: float = float(mass)
        self.spin: float = float(spin)
        self.charge: float = float(Q)

        self._t = sp.Symbol("t", real=True)
        self._r = sp.Symbol("r", positive=True)
        self._theta = sp.Symbol("theta", positive=True)
        self._phi = sp.Symbol("phi", real=True)

        self._metric_cache: sp.Matrix | None = None

    # ──────────────────────────────────────────────────────────────
    # Abstract methods
    # ──────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "Kerr-Newman"

    @property
    def coordinates(self) -> list[sp.Symbol]:
        return [self._t, self._r, self._theta, self._phi]

    @property
    def metric_tensor(self) -> sp.Matrix:
        """Boyer-Lindquist Kerr-Newman metric (4×4 SymPy Matrix)."""
        if self._metric_cache is not None:
            return self._metric_cache

        M = sp.Float(self.mass)
        a = sp.Float(self.spin)
        Q = sp.Float(self.charge)
        r = self._r
        theta = self._theta

        Sigma = r ** 2 + a ** 2 * sp.cos(theta) ** 2
        Delta = r ** 2 - 2 * M * r + a ** 2 + Q ** 2  # Kerr's Δ + Q²
        sin2 = sp.sin(theta) ** 2

        # Following Wald §12.3 — Q² enters only through Δ.  The g_{tt},
        # g_{tφ}, g_{φφ} terms keep the Kerr structural form.  This is
        # easy to verify: Newman et al. 1965 derived KN by Newman-Janis
        # algorithm = complex-coordinate trick on RN, which only modifies
        # Δ.
        g_tt     = -(1 - (2 * M * r - Q ** 2) / Sigma)
        g_tphi   = -((2 * M * a * r - Q ** 2 * a) * sin2) / Sigma
        g_rr     = Sigma / Delta
        g_thth   = Sigma
        g_phiphi = (
            r ** 2 + a ** 2 + ((2 * M * a ** 2 * r - Q ** 2 * a ** 2) * sin2) / Sigma
        ) * sin2

        g = sp.Matrix([
            [g_tt,   0,    0,      g_tphi],
            [0,      g_rr, 0,      0],
            [0,      0,    g_thth, 0],
            [g_tphi, 0,    0,      g_phiphi],
        ])

        self._metric_cache = g
        return g

    # ──────────────────────────────────────────────────────────────
    # Horizons (closed form)
    # ──────────────────────────────────────────────────────────────

    def _disc(self) -> float:
        """M² - a² - Q², clamped at 0 to absorb sub-eps roundoff at extremality."""
        return max(self.mass ** 2 - self.spin ** 2 - self.charge ** 2, 0.0)

    def outer_horizon(self) -> float:
        """r_+ = M + sqrt(M² - a² - Q²)."""
        return self.mass + math.sqrt(self._disc())

    def inner_horizon(self) -> float:
        """r_- = M - sqrt(M² - a² - Q²)."""
        return self.mass - math.sqrt(self._disc())

    @property
    def is_extremal(self) -> bool:
        """True iff a² + Q² == M² within tolerance."""
        return abs(self.spin ** 2 + self.charge ** 2 - self.mass ** 2) < 1e-12

    # ──────────────────────────────────────────────────────────────
    # Ergosphere
    # ──────────────────────────────────────────────────────────────

    def ergosphere(self, theta: float) -> float:
        """Outer boundary of the ergoregion (where g_tt = 0).

        Solving g_tt = -(1 - (2Mr - Q²)/Σ) = 0 with Σ = r² + a² cos²θ:
            r² - 2Mr + Q² + a² cos²θ = 0
            r_E(θ) = M + sqrt(M² - Q² - a² cos²θ).

        At equator (θ = π/2): r_E = M + sqrt(M² - Q²) — same as RN's r_+
        in the no-spin limit, but here it's the *ergosphere*, not the
        horizon.  At pole (θ = 0): r_E = M + sqrt(M² - Q² - a²) = r_+
        (ergosphere collapses onto horizon at the poles).
        """
        M = self.mass
        a = self.spin
        Q = self.charge
        disc = M ** 2 - Q ** 2 - a ** 2 * math.cos(theta) ** 2
        # Same tolerance treatment as _disc(): negative due to roundoff at
        # extremality is clamped to 0; truly negative (theoretically
        # impossible inside cosmic-censorship) raises.
        if disc < -1e-12:
            raise ValueError(f"ergosphere undefined at θ={theta}: M²-Q²-a²cos²θ={disc}<0")
        return M + math.sqrt(max(disc, 0.0))

    # ──────────────────────────────────────────────────────────────
    # Thermodynamics
    # ──────────────────────────────────────────────────────────────

    def angular_velocity_horizon(self) -> float:
        """Ω_H = a / (r_+² + a²) — same form as Kerr (Q-independent)."""
        rp = self.outer_horizon()
        return self.spin / (rp ** 2 + self.spin ** 2)

    def horizon_area(self) -> float:
        """A = 4π (r_+² + a²)."""
        rp = self.outer_horizon()
        return 4.0 * math.pi * (rp ** 2 + self.spin ** 2)

    def surface_gravity(self) -> float:
        """κ = (r_+ - r_-) / (2(r_+² + a²))."""
        rp = self.outer_horizon()
        rm = self.inner_horizon()
        return (rp - rm) / (2.0 * (rp ** 2 + self.spin ** 2))

    def hawking_temperature(self) -> float:
        """T_H = κ / (2π)."""
        return self.surface_gravity() / (2.0 * math.pi)

    def bekenstein_hawking_entropy(self) -> float:
        """S = A/4 = π(r_+² + a²)."""
        return math.pi * (self.outer_horizon() ** 2 + self.spin ** 2)

    # ──────────────────────────────────────────────────────────────
    # Output
    # ──────────────────────────────────────────────────────────────

    def line_element_latex(self) -> str:
        return (
            r"ds^2 = -\frac{\Delta - a^2 \sin^2\theta}{\Sigma} dt^2 "
            r"- \frac{2(2Mar - Q^2 a) \sin^2\theta}{\Sigma} dt\, d\phi "
            r"+ \frac{\Sigma}{\Delta} dr^2 + \Sigma\, d\theta^2 "
            r"+ \frac{(r^2+a^2)^2 - \Delta a^2 \sin^2\theta}{\Sigma} \sin^2\theta\, d\phi^2"
            r",\quad \Sigma = r^2 + a^2\cos^2\theta,\ \Delta = r^2 - 2Mr + a^2 + Q^2"
        )

    def __repr__(self) -> str:
        return (
            f"KerrNewman(mass={self.mass}, spin={self.spin}, "
            f"charge={self.charge})"
        )
