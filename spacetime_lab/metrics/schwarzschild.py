"""Schwarzschild metric — the unique static, spherically symmetric vacuum solution.

References:
    Wald, "General Relativity", Chapter 6
    Misner, Thorne, Wheeler, "Gravitation", Chapter 31
    Carroll, "Spacetime and Geometry", Chapter 5

The Schwarzschild metric describes the spacetime outside a non-rotating,
uncharged spherical mass. It is the simplest exact black hole solution to
the Einstein field equations in vacuum (T_{mu nu} = 0).

Line element in Schwarzschild coordinates (t, r, theta, phi):

    ds^2 = -(1 - 2M/r) dt^2 + (1 - 2M/r)^{-1} dr^2 + r^2 dOmega^2

where dOmega^2 = dtheta^2 + sin^2(theta) dphi^2 is the metric on the unit
2-sphere. The coordinate singularity at r = 2M is the event horizon; the
true curvature singularity is at r = 0.
"""

from __future__ import annotations

import sympy as sp

from spacetime_lab.metrics.base import Metric


class Schwarzschild(Metric):
    """The Schwarzschild metric for a non-rotating black hole.

    Args:
        mass: The mass parameter M of the black hole (in geometric units G=c=1).
              Must be positive. Default is a symbolic variable.

    Attributes:
        mass: The numerical or symbolic mass parameter.

    Example:
        >>> bh = Schwarzschild(mass=1.0)
        >>> bh.event_horizon()
        2.0
        >>> bh.isco()
        6.0
        >>> bh.photon_sphere()
        3.0
    """

    def __init__(self, mass: float | sp.Symbol | None = None) -> None:
        super().__init__()
        if mass is None:
            self.mass: sp.Symbol | float = sp.Symbol("M", positive=True)
        else:
            if isinstance(mass, (int, float)) and mass <= 0:
                raise ValueError(f"Mass must be positive, got {mass}")
            self.mass = mass

        # Coordinates: (t, r, theta, phi)
        self._t = sp.Symbol("t", real=True)
        self._r = sp.Symbol("r", positive=True)
        self._theta = sp.Symbol("theta", positive=True)
        self._phi = sp.Symbol("phi", real=True)

        # Build metric tensor lazily
        self._metric_cache: sp.Matrix | None = None

    # ──────────────────────────────────────────────────────────────
    # Abstract methods from base class
    # ──────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "Schwarzschild"

    @property
    def coordinates(self) -> list[sp.Symbol]:
        return [self._t, self._r, self._theta, self._phi]

    @property
    def metric_tensor(self) -> sp.Matrix:
        """Schwarzschild metric in Schwarzschild coordinates."""
        if self._metric_cache is not None:
            return self._metric_cache

        M = self.mass
        r = self._r
        theta = self._theta

        f = 1 - 2 * M / r  # The Schwarzschild factor

        g = sp.Matrix([
            [-f, 0, 0, 0],
            [0, 1 / f, 0, 0],
            [0, 0, r**2, 0],
            [0, 0, 0, r**2 * sp.sin(theta) ** 2],
        ])

        self._metric_cache = g
        return g

    # ──────────────────────────────────────────────────────────────
    # Physics
    # ──────────────────────────────────────────────────────────────

    def event_horizon(self) -> float | sp.Expr:
        """Return the Schwarzschild radius r_s = 2M.

        This is the location of the event horizon — the null surface beyond
        which even light cannot escape to infinity.

        Returns:
            The Schwarzschild radius in geometric units (length = M).
        """
        return 2 * self.mass

    def isco(self) -> float | sp.Expr:
        """Return the ISCO (Innermost Stable Circular Orbit) radius.

        For Schwarzschild, r_ISCO = 6M. This is the smallest radius at which
        a test particle can maintain a stable circular orbit.

        Returns:
            The ISCO radius in geometric units.
        """
        return 6 * self.mass

    def photon_sphere(self) -> float | sp.Expr:
        """Return the photon sphere radius.

        For Schwarzschild, r_ph = 3M. This is the radius of the unstable
        circular null geodesic — the orbit of a photon around the black hole.

        Returns:
            The photon sphere radius in geometric units.
        """
        return 3 * self.mass

    def kretschmann_scalar_at_horizon(self) -> float | sp.Expr:
        """Compute K = R_{abcd} R^{abcd} at the event horizon.

        For Schwarzschild, K(r) = 48 M^2 / r^6. At the horizon r = 2M,
        K = 48 / (16 M^4 * 4) = 3 / (4 M^4). This quantity is finite at
        the horizon but diverges as r -> 0, confirming that r = 2M is
        only a coordinate singularity while r = 0 is a true curvature
        singularity.

        Returns:
            The Kretschmann scalar evaluated at r = 2M.
        """
        return 3 / (4 * self.mass**4)

    def surface_gravity(self) -> float | sp.Expr:
        """Return the surface gravity kappa = 1/(4M).

        The surface gravity relates to the Hawking temperature via
        T_H = kappa / (2 pi) (in natural units with k_B = hbar = 1).

        Returns:
            The surface gravity at the event horizon.
        """
        return 1 / (4 * self.mass)

    def hawking_temperature(self) -> float | sp.Expr:
        """Return the Hawking temperature T_H = 1/(8 pi M).

        In natural units (G = c = hbar = k_B = 1):
            T_H = kappa / (2 pi) = 1 / (8 pi M)

        Returns:
            The Hawking temperature.
        """
        return 1 / (8 * sp.pi * self.mass)

    def bekenstein_hawking_entropy(self) -> float | sp.Expr:
        """Return the Bekenstein-Hawking entropy S = A/4 = 4 pi M^2.

        The area of the event horizon is A = 4 pi r_s^2 = 16 pi M^2,
        and the entropy is one quarter of the area in natural units.

        Returns:
            The Bekenstein-Hawking entropy.
        """
        return 4 * sp.pi * self.mass**2

    # ──────────────────────────────────────────────────────────────
    # Representation
    # ──────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"Schwarzschild(mass={self.mass})"

    def line_element_latex(self) -> str:
        """Return the canonical line element as LaTeX."""
        M = self.mass
        if isinstance(M, sp.Symbol):
            M_str = "M"
        else:
            M_str = str(M)
        return (
            rf"ds^2 = -\left(1 - \frac{{2{M_str}}}{{r}}\right) dt^2 "
            rf"+ \left(1 - \frac{{2{M_str}}}{{r}}\right)^{{-1}} dr^2 "
            rf"+ r^2 d\theta^2 + r^2 \sin^2\theta \, d\varphi^2"
        )
