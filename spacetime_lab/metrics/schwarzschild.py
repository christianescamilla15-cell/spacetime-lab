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
    # Geodesics and coordinate transformations
    # ──────────────────────────────────────────────────────────────

    def tortoise_coordinate(self, r: float | sp.Expr) -> float | sp.Expr:
        """Compute the tortoise coordinate r*.

        The tortoise coordinate is defined by:
            r* = r + 2M ln(r/2M - 1)

        It satisfies dr*/dr = 1 / f(r) where f(r) = 1 - 2M/r.

        Physical meaning: r* → -∞ as r → 2M+ (the horizon is pushed to
        infinity in the new coordinate). This is useful for studying
        wave propagation and ingoing/outgoing null coordinates.

        Args:
            r: Radial Schwarzschild coordinate (must be > 2M).

        Returns:
            The tortoise coordinate r*.

        Raises:
            ValueError: If r <= 2M (inside horizon).

        References:
            Wald, "General Relativity", eq. 6.4.25
        """
        M = self.mass
        if isinstance(r, (int, float)):
            if r <= 2 * M:
                raise ValueError(f"Tortoise coordinate undefined for r={r} <= 2M={2*M}")
            import math
            return r + 2 * M * math.log(r / (2 * M) - 1)
        # Symbolic case
        return r + 2 * M * sp.log(r / (2 * M) - 1)

    def effective_potential(
        self,
        r: float | sp.Expr,
        L: float | sp.Expr,
        particle_type: str = "massive",
    ) -> float | sp.Expr:
        """Compute the effective potential V_eff(r) for geodesic motion.

        For equatorial geodesics (theta = pi/2), the radial motion reduces
        to an effective one-dimensional problem:

            (dr/dtau)^2 = E^2 - V_eff(r)

        where V_eff depends on the particle type:

            Massive:  V_eff = (1 - 2M/r)(1 + L^2/r^2)
            Photon:   V_eff = (1 - 2M/r)(L^2/r^2)

        Args:
            r: Radial coordinate.
            L: Angular momentum per unit mass (or per unit energy for photons).
            particle_type: "massive" or "photon".

        Returns:
            The effective potential V_eff(r).

        References:
            Wald eq. 6.3.12, Carroll eq. 5.63
        """
        M = self.mass
        f = 1 - 2 * M / r

        if particle_type == "massive":
            return f * (1 + L**2 / r**2)
        elif particle_type == "photon":
            return f * (L**2 / r**2)
        else:
            raise ValueError(f"Unknown particle_type: {particle_type}")

    def kruskal_coordinates(
        self,
        t: float | sp.Expr,
        r: float | sp.Expr,
        region: int = 1,
    ) -> tuple[sp.Expr, sp.Expr] | tuple[float, float]:
        """Transform (t, r) to Kruskal-Szekeres coordinates (T, X).

        The Kruskal-Szekeres coordinates provide the maximal analytic
        extension of the Schwarzschild spacetime. They remove the
        coordinate singularity at r = 2M and reveal 4 distinct regions:

            Region I:   Exterior (our universe), r > 2M
            Region II:  Future interior (black hole), inside horizon
            Region III: Other exterior (parallel universe)
            Region IV:  Past interior (white hole)

        For Region I (r > 2M):
            T = sqrt(r/2M - 1) exp(r/4M) sinh(t/4M)
            X = sqrt(r/2M - 1) exp(r/4M) cosh(t/4M)

        For Region II (r < 2M):
            T = sqrt(1 - r/2M) exp(r/4M) cosh(t/4M)
            X = sqrt(1 - r/2M) exp(r/4M) sinh(t/4M)

        Args:
            t: Schwarzschild time coordinate.
            r: Schwarzschild radial coordinate.
            region: Which region (1=exterior, 2=interior).

        Returns:
            Tuple (T, X) in Kruskal-Szekeres coordinates.

        References:
            Wald eqs. 6.4.28-6.4.31, Carroll eqs. 5.86-5.87
        """
        M = self.mass
        is_numeric = isinstance(r, (int, float)) and isinstance(t, (int, float))

        if is_numeric:
            import math
            if region == 1:
                if r <= 2 * M:
                    raise ValueError(f"Region I requires r > 2M, got r={r}")
                factor = math.sqrt(r / (2 * M) - 1) * math.exp(r / (4 * M))
                T = factor * math.sinh(t / (4 * M))
                X = factor * math.cosh(t / (4 * M))
            elif region == 2:
                if r >= 2 * M:
                    raise ValueError(f"Region II requires r < 2M, got r={r}")
                factor = math.sqrt(1 - r / (2 * M)) * math.exp(r / (4 * M))
                T = factor * math.cosh(t / (4 * M))
                X = factor * math.sinh(t / (4 * M))
            else:
                raise ValueError(f"Unsupported region: {region}")
            return (T, X)

        # Symbolic case
        if region == 1:
            factor = sp.sqrt(r / (2 * M) - 1) * sp.exp(r / (4 * M))
            T = factor * sp.sinh(t / (4 * M))
            X = factor * sp.cosh(t / (4 * M))
        elif region == 2:
            factor = sp.sqrt(1 - r / (2 * M)) * sp.exp(r / (4 * M))
            T = factor * sp.cosh(t / (4 * M))
            X = factor * sp.sinh(t / (4 * M))
        else:
            raise ValueError(f"Unsupported region: {region}")

        return (T, X)

    def kretschmann_scalar(self, r: float | sp.Expr) -> float | sp.Expr:
        """Compute the Kretschmann scalar K = R_{abcd} R^{abcd} at radius r.

        For Schwarzschild:
            K(r) = 48 M^2 / r^6

        This scalar is finite at the horizon r = 2M (confirming it's a
        coordinate singularity) but diverges as r → 0 (the true curvature
        singularity).

        Args:
            r: Radial coordinate.

        Returns:
            The Kretschmann scalar K(r).

        References:
            MTW eq. 31.5
        """
        return 48 * self.mass**2 / r**6

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
