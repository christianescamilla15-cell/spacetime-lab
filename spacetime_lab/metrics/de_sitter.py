"""de Sitter spacetime in static-patch coordinates.

The unique maximally symmetric solution of vacuum Einstein with
positive cosmological constant Λ > 0.  Structurally analogous to
Schwarzschild but with the BH replaced by a *cosmological* event
horizon at r = L = sqrt(3/Λ).

References:
    Wald, "General Relativity", §5.2 ("Cosmological Models")
    Hawking & Ellis, "The Large Scale Structure of Space-Time", §5.2
    Gibbons & Hawking 1977 ("Cosmological event horizons,
        thermodynamics, and particle creation")

Static patch line element:
    ds² = -(1 - r²/L²) dt² + dr²/(1 - r²/L²) + r² dΩ²

Key facts:
    - r = L is the cosmological event horizon (g_tt = 0).  No
      singularity inside; the static patch covers only one observer's
      causal diamond.
    - Hubble rate H = 1/L (constant).
    - Λ = 3/L² = 3 H².
    - Hawking T = H/(2π) = 1/(2πL).
    - Bekenstein-Hawking entropy of the cosmological horizon:
        S = A/4 = π L².

Structurally the simplest cosmological metric — closed form for
everything.  More general FLRW (with matter content) lives in the
deferred docs/v3.2-flrw-de-sitter-spec.md (needs the Friedmann
ODE solver).

This module is the "easy half" of v3.2.
"""

from __future__ import annotations

import math

import sympy as sp

from spacetime_lab.metrics.base import Metric


class DeSitter(Metric):
    """de Sitter spacetime in static-patch (or "Hubble") coordinates.

    Args:
        radius: de Sitter radius L = sqrt(3/Λ) in geometric units.
                Equivalently L = 1/H where H is the Hubble rate.
                Must be positive.

    Attributes:
        radius: Numerical L.

    Example:
        >>> ds = DeSitter(radius=1.0)
        >>> ds.cosmological_horizon()
        1.0
        >>> round(ds.cosmological_constant(), 6)
        3.0
        >>> round(ds.hubble_parameter(), 6)
        1.0
    """

    def __init__(self, radius: float = 1.0) -> None:
        super().__init__()
        if not isinstance(radius, (int, float)):
            raise TypeError(f"radius must be a real number, got {type(radius).__name__}")
        if radius <= 0:
            raise ValueError(f"radius must be positive, got {radius}")
        self.radius: float = float(radius)

        self._t = sp.Symbol("t", real=True)
        self._r = sp.Symbol("r", positive=True)
        self._theta = sp.Symbol("theta", positive=True)
        self._phi = sp.Symbol("phi", real=True)

        self._metric_cache: sp.Matrix | None = None

    # ──────────────────────────────────────────────────────────────
    # Abstract interface
    # ──────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "de Sitter"

    @property
    def coordinates(self) -> list[sp.Symbol]:
        return [self._t, self._r, self._theta, self._phi]

    @property
    def metric_tensor(self) -> sp.Matrix:
        """Static-patch metric tensor."""
        if self._metric_cache is not None:
            return self._metric_cache
        L = sp.Float(self.radius)
        r = self._r
        theta = self._theta
        f = 1 - r ** 2 / L ** 2
        g = sp.Matrix([
            [-f, 0, 0, 0],
            [0, 1 / f, 0, 0],
            [0, 0, r ** 2, 0],
            [0, 0, 0, r ** 2 * sp.sin(theta) ** 2],
        ])
        self._metric_cache = g
        return g

    # ──────────────────────────────────────────────────────────────
    # Cosmological invariants — all closed form
    # ──────────────────────────────────────────────────────────────

    def cosmological_horizon(self) -> float:
        """The static-patch cosmological event horizon, r_c = L."""
        return self.radius

    def cosmological_constant(self) -> float:
        """Λ = 3 / L²."""
        return 3.0 / (self.radius ** 2)

    def hubble_parameter(self) -> float:
        """H = 1 / L = sqrt(Λ/3) (constant in dS)."""
        return 1.0 / self.radius

    def hawking_temperature(self) -> float:
        """Gibbons-Hawking temperature of the cosmological horizon:
            T = H / (2π) = 1 / (2π L).
        """
        return 1.0 / (2.0 * math.pi * self.radius)

    def horizon_area(self) -> float:
        """A = 4π L² (area of the cosmological 2-sphere)."""
        return 4.0 * math.pi * self.radius ** 2

    def bekenstein_hawking_entropy(self) -> float:
        """Cosmological-horizon entropy S = A/4 = π L²."""
        return math.pi * self.radius ** 2

    def expected_ricci_scalar(self) -> float:
        """For 4D dS: R = 12/L² = 4Λ.  Useful as a self-consistency
        check against any numerical Ricci computed from metric_tensor."""
        return 12.0 / (self.radius ** 2)

    # ──────────────────────────────────────────────────────────────
    # Output
    # ──────────────────────────────────────────────────────────────

    def line_element_latex(self) -> str:
        return (
            r"ds^2 = -\left(1 - \frac{r^2}{L^2}\right) dt^2 "
            r"+ \left(1 - \frac{r^2}{L^2}\right)^{-1} dr^2 "
            r"+ r^2 \, d\Omega^2"
        )

    def __repr__(self) -> str:
        return f"DeSitter(radius={self.radius})"
