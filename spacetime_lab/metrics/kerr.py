r"""Kerr metric — the unique stationary, axisymmetric vacuum black hole.

References:
    Wald, "General Relativity", Chapter 12
    Misner, Thorne, Wheeler, "Gravitation", Chapter 33
    Carroll, "Spacetime and Geometry", Chapter 6
    Bardeen, Press & Teukolsky, ApJ 178 347 (1972) — ISCO formula
    Carter, Phys. Rev. 174 1559 (1968) — separability and Carter's constant

The Kerr metric describes the spacetime outside a rotating, uncharged
black hole.  In Boyer-Lindquist coordinates :math:`(t, r, \theta, \varphi)`
with the conventional abbreviations

.. math::

    \Sigma(r, \theta) = r^2 + a^2 \cos^2\theta, \qquad
    \Delta(r) = r^2 - 2Mr + a^2,

the line element is

.. math::

    ds^2 = -\left(1 - \frac{2Mr}{\Sigma}\right) dt^2
           - \frac{4Mar\sin^2\theta}{\Sigma}\, dt\, d\varphi
           + \frac{\Sigma}{\Delta}\, dr^2
           + \Sigma\, d\theta^2
           + \left(r^2 + a^2 + \frac{2Ma^2 r \sin^2\theta}{\Sigma}\right)
             \sin^2\theta\, d\varphi^2.

Convention pins (do not change without updating the tests):

- Signature ``(-, +, +, +)`` (Wald).
- Geometric units :math:`G = c = 1`.
- ``a`` is the *specific* angular momentum :math:`a = J / M`, with
  :math:`a \in [0, M]`.  ``a > M`` would give a naked singularity and
  is rejected by the constructor.
- "Prograde" means corotating with the hole; "retrograde" means
  counter-rotating.

Verified against:

- Wikipedia ``Kerr metric`` (line element, :math:`\Sigma`, :math:`\Delta`,
  :math:`r_\pm`, ergosphere).
- Bardeen, Press & Teukolsky 1972 (ISCO formula with :math:`Z_1`,
  :math:`Z_2`).
- Leo C. Stein's Kerr photon-orbit calculator (photon-sphere formula
  and the prograde/retrograde sign convention).
"""

from __future__ import annotations

import math

import sympy as sp

from spacetime_lab.metrics.base import Metric


class Kerr(Metric):
    """The Kerr metric for a rotating black hole.

    Args:
        mass: The mass parameter ``M`` of the black hole, in geometric
            units :math:`G = c = 1`.  Must be positive.
        spin: The specific angular momentum :math:`a = J / M`, in the
            same geometric units (so ``spin`` and ``mass`` have the same
            dimension — length).  Must satisfy ``0 <= spin <= mass``.
            ``spin = 0`` recovers the Schwarzschild metric;
            ``spin = mass`` is the extremal Kerr limit.

    Attributes:
        mass: Numerical mass parameter.
        spin: Numerical spin parameter ``a``.

    Example:
        >>> bh = Kerr(mass=1.0, spin=0.5)
        >>> round(bh.outer_horizon(), 6)
        1.866025
        >>> round(bh.inner_horizon(), 6)
        0.133975
        >>> bh.isco(prograde=True) < bh.isco(prograde=False)
        True
    """

    # ──────────────────────────────────────────────────────────────
    # Construction
    # ──────────────────────────────────────────────────────────────

    def __init__(self, mass: float, spin: float = 0.0) -> None:
        super().__init__()
        if not isinstance(mass, (int, float)):
            raise TypeError(f"mass must be a real number, got {type(mass).__name__}")
        if not isinstance(spin, (int, float)):
            raise TypeError(f"spin must be a real number, got {type(spin).__name__}")
        if mass <= 0:
            raise ValueError(f"mass must be positive, got {mass}")
        if spin < 0:
            raise ValueError(f"spin must be non-negative, got {spin}")
        if spin > mass:
            raise ValueError(
                f"spin must satisfy spin <= mass (cosmic censorship), "
                f"got spin={spin}, mass={mass}"
            )

        self.mass: float = float(mass)
        self.spin: float = float(spin)

        # Coordinates: (t, r, theta, phi)
        self._t = sp.Symbol("t", real=True)
        self._r = sp.Symbol("r", positive=True)
        self._theta = sp.Symbol("theta", positive=True)
        self._phi = sp.Symbol("phi", real=True)

        # Build metric tensor lazily (it's expensive symbolically).
        self._metric_cache: sp.Matrix | None = None

    # ──────────────────────────────────────────────────────────────
    # Abstract properties from base class
    # ──────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "Kerr"

    @property
    def coordinates(self) -> list[sp.Symbol]:
        return [self._t, self._r, self._theta, self._phi]

    @property
    def metric_tensor(self) -> sp.Matrix:
        """Boyer-Lindquist metric tensor :math:`g_{\\mu\\nu}`.

        Returns the symbolic 4x4 matrix; ``M`` and ``a`` are substituted
        with the constructor's numerical values, but ``r`` and
        ``theta`` remain symbolic so the tensor can be differentiated
        and evaluated.
        """
        if self._metric_cache is not None:
            return self._metric_cache

        M = sp.Float(self.mass)
        a = sp.Float(self.spin)
        r = self._r
        theta = self._theta

        Sigma = r**2 + a**2 * sp.cos(theta) ** 2
        Delta = r**2 - 2 * M * r + a**2
        sin2 = sp.sin(theta) ** 2

        g_tt = -(1 - 2 * M * r / Sigma)
        g_tphi = -(2 * M * a * r * sin2) / Sigma
        g_rr = Sigma / Delta
        g_thth = Sigma
        g_phiphi = (r**2 + a**2 + (2 * M * a**2 * r * sin2) / Sigma) * sin2

        g = sp.Matrix(
            [
                [g_tt,    0,    0,    g_tphi],
                [0,       g_rr, 0,    0],
                [0,       0,    g_thth, 0],
                [g_tphi,  0,    0,    g_phiphi],
            ]
        )

        self._metric_cache = g
        return g

    # ──────────────────────────────────────────────────────────────
    # Characteristic functions (helpers)
    # ──────────────────────────────────────────────────────────────

    @property
    def sigma_expr(self) -> sp.Expr:
        r"""Return :math:`\Sigma = r^2 + a^2 \cos^2\theta` symbolically."""
        return self._r**2 + sp.Float(self.spin) ** 2 * sp.cos(self._theta) ** 2

    @property
    def delta_expr(self) -> sp.Expr:
        r"""Return :math:`\Delta = r^2 - 2Mr + a^2` symbolically."""
        return (
            self._r**2
            - 2 * sp.Float(self.mass) * self._r
            + sp.Float(self.spin) ** 2
        )

    # ──────────────────────────────────────────────────────────────
    # Horizons and the ergosphere
    # ──────────────────────────────────────────────────────────────

    def outer_horizon(self) -> float:
        r"""Outer event horizon :math:`r_+ = M + \sqrt{M^2 - a^2}`.

        For ``spin == 0`` this is the Schwarzschild radius :math:`2M`.
        For extremal Kerr (``spin == mass``) :math:`r_+ = M` and the
        two horizons merge.
        """
        M = self.mass
        a = self.spin
        return M + math.sqrt(M * M - a * a)

    def inner_horizon(self) -> float:
        r"""Inner Cauchy horizon :math:`r_- = M - \sqrt{M^2 - a^2}`.

        Has no Schwarzschild analogue: as ``spin -> 0``,
        :math:`r_- \to 0` and the inner horizon collapses to the
        singularity.  For extremal Kerr (``spin == mass``)
        :math:`r_- = M = r_+`.
        """
        M = self.mass
        a = self.spin
        return M - math.sqrt(M * M - a * a)

    def ergosphere(self, theta: float) -> float:
        r"""Outer boundary of the ergoregion (static limit) at colatitude :math:`\theta`.

        Defined by :math:`g_{tt} = 0`:

        .. math::

            r_E(\theta) = M + \sqrt{M^2 - a^2 \cos^2\theta}.

        Coincides with :math:`r_+` at the poles and bulges outward at
        the equator (:math:`\theta = \pi/2`), where it equals
        :math:`r_E(\pi/2) = 2M` for any value of ``a``.

        Args:
            theta: Colatitude in radians.

        Returns:
            The static-limit radius at that colatitude.
        """
        M = self.mass
        a = self.spin
        c = math.cos(theta)
        return M + math.sqrt(M * M - a * a * c * c)

    # ──────────────────────────────────────────────────────────────
    # Equatorial circular orbits — prograde / retrograde split
    # ──────────────────────────────────────────────────────────────

    def isco(self, prograde: bool = True) -> float:
        r"""Innermost stable circular orbit radius for an equatorial massive test particle.

        Bardeen, Press and Teukolsky (1972) closed-form expression:

        .. math::

            r_{\text{ISCO}} = M\!\left[3 + Z_2 \mp
                \sqrt{(3 - Z_1)(3 + Z_1 + 2 Z_2)}\,\right],

        with the upper sign (minus) for **prograde** orbits and the
        lower sign (plus) for retrograde.  The auxiliary functions
        are

        .. math::

            Z_1 &= 1 + (1 - \chi^2)^{1/3}\!\left[
                (1 + \chi)^{1/3} + (1 - \chi)^{1/3}\right], \\
            Z_2 &= \sqrt{3 \chi^2 + Z_1^2},

        where :math:`\chi = a / M` is the dimensionless spin.

        Args:
            prograde: If True (default), return the corotating ISCO.
                If False, the counter-rotating ISCO.

        Returns:
            The ISCO radius in the same units as ``mass``.

        Notes:
            - Both branches collapse to :math:`6M` at :math:`\chi = 0`
              (Schwarzschild ISCO).
            - At extremal Kerr (:math:`\chi = 1`) the prograde branch
              gives :math:`r_{\text{ISCO}}^+ = M` and the retrograde
              branch gives :math:`r_{\text{ISCO}}^- = 9M`.
        """
        M = self.mass
        chi = self.spin / M
        one_minus_chi2 = 1.0 - chi * chi
        Z1 = 1.0 + (one_minus_chi2 ** (1.0 / 3.0)) * (
            (1.0 + chi) ** (1.0 / 3.0) + (1.0 - chi) ** (1.0 / 3.0)
        )
        Z2 = math.sqrt(3.0 * chi * chi + Z1 * Z1)
        sign = -1.0 if prograde else +1.0
        bracket = (3.0 - Z1) * (3.0 + Z1 + 2.0 * Z2)
        # bracket can be ~ -1e-15 at chi=1 due to floating-point cancellation
        if -1e-12 < bracket < 0.0:
            bracket = 0.0
        return M * (3.0 + Z2 + sign * math.sqrt(bracket))

    def photon_sphere_equatorial(self, prograde: bool = True) -> float:
        r"""Radius of the equatorial circular photon orbit.

        Closed-form expression (see e.g. Bardeen 1973 or
        https://duetosymmetry.com/tool/kerr-circular-photon-orbits/):

        .. math::

            r_{\text{ph}} = 2M\!\left[1 + \cos\!\left(
                \tfrac{2}{3}\arccos(\mp a / M)\right)\right],

        with the upper sign (minus) for **prograde** orbits and the
        lower sign (plus) for retrograde.

        Returns:
            The equatorial photon-orbit radius.

        Notes:
            - Both branches reduce to :math:`3M` at :math:`a = 0`.
            - At extremal Kerr the prograde orbit touches the
              horizon (:math:`r_{\text{ph}}^+ = M`) and the
              retrograde orbit sits at :math:`r_{\text{ph}}^- = 4M`.
            - For :math:`a > 0`, off-equatorial circular photon
              orbits also exist on a "photon region" rather than a
              single sphere.  This method only handles the equatorial
              ones.
        """
        M = self.mass
        a = self.spin
        sign = -1.0 if prograde else +1.0
        return 2.0 * M * (1.0 + math.cos((2.0 / 3.0) * math.acos(sign * a / M)))

    # ──────────────────────────────────────────────────────────────
    # Horizon thermodynamics
    # ──────────────────────────────────────────────────────────────

    def angular_velocity_horizon(self) -> float:
        r"""Angular velocity of the outer horizon, :math:`\Omega_H = a / (r_+^2 + a^2)`.

        Every observer at the horizon must rotate with this angular
        velocity (frame dragging is total).  For Schwarzschild
        (:math:`a = 0`) this vanishes; for extremal Kerr it equals
        :math:`1 / (2M)`.
        """
        rp = self.outer_horizon()
        a = self.spin
        return a / (rp * rp + a * a)

    def horizon_area(self) -> float:
        r"""Area of the outer event horizon, :math:`A = 4\pi(r_+^2 + a^2)`.

        Reduces to :math:`16\pi M^2` for Schwarzschild.
        """
        rp = self.outer_horizon()
        a = self.spin
        return 4.0 * math.pi * (rp * rp + a * a)

    def surface_gravity(self) -> float:
        r"""Surface gravity of the outer horizon.

        .. math::

            \kappa = \frac{r_+ - r_-}{2(r_+^2 + a^2)}.

        Reduces to :math:`1/(4M)` in the Schwarzschild limit.
        Vanishes at extremal Kerr (this is the "third law" of black
        hole thermodynamics: extremal holes are like absolute zero
        and cannot be reached by any finite physical process).
        """
        rp = self.outer_horizon()
        rm = self.inner_horizon()
        a = self.spin
        return (rp - rm) / (2.0 * (rp * rp + a * a))

    def hawking_temperature(self) -> float:
        r"""Hawking temperature :math:`T_H = \kappa / (2\pi)` in natural units.

        Reduces to :math:`1/(8\pi M)` for Schwarzschild and vanishes
        at extremal Kerr.
        """
        return self.surface_gravity() / (2.0 * math.pi)

    def bekenstein_hawking_entropy(self) -> float:
        r"""Bekenstein-Hawking entropy :math:`S = A / 4`.

        Reduces to :math:`4\pi M^2` for Schwarzschild.
        """
        return self.horizon_area() / 4.0

    # ──────────────────────────────────────────────────────────────
    # Carter's symmetry: the irreducible Killing tensor
    # ──────────────────────────────────────────────────────────────

    def killing_tensor(self) -> sp.Matrix:
        r"""Return the irreducible rank-2 Killing tensor of Kerr.

        Carter (1968) showed that, in addition to the obvious Killing
        vectors :math:`\partial_t` and :math:`\partial_\varphi`, the
        Kerr metric admits a Killing tensor :math:`K_{\mu\nu}` whose
        contraction with a geodesic 4-velocity gives a fourth
        conserved quantity:

        .. math::

            \mathcal{K} = K_{\mu\nu}\, u^\mu u^\nu = \mathrm{const}.

        Using the Walker-Penrose form (see e.g. Chandrasekhar,
        *The Mathematical Theory of Black Holes*, ch. 7),

        .. math::

            K^{\mu\nu} = \Delta\, k^{(\mu} l^{\nu)} + r^2\, g^{\mu\nu},

        where :math:`k^\mu` and :math:`l^\mu` are the principal null
        vectors of Kerr.  Equivalently, in Boyer-Lindquist
        components,

        .. math::

            K_{\mu\nu} = 2 \Sigma\, l_{(\mu} n_{\nu)}
                        + r^2 g_{\mu\nu},

        with :math:`l_\mu = (1, -\Sigma/\Delta, 0, -a\sin^2\theta)`
        and :math:`n_\mu = \tfrac{1}{2}((\Delta/\Sigma), 1, 0,
        -a\sin^2\theta(\Delta/\Sigma))` (up to overall normalisation).

        For a geodesic with energy :math:`E`, axial angular momentum
        :math:`L_z`, and rest mass :math:`\mu`, the relation between
        :math:`\mathcal{K}` and Carter's constant :math:`\mathcal{Q}`
        used in the separated geodesic equations is

        .. math::

            \mathcal{K} = \mathcal{Q} + (L_z - aE)^2.

        ``\mathcal{K}`` is always non-negative; ``\mathcal{Q}`` can
        change sign.  In the equatorial plane :math:`\theta = \pi/2`,
        :math:`\mathcal{Q} = 0` for any planar geodesic, so
        :math:`\mathcal{K} = (L_z - aE)^2` in that case.

        Returns:
            The 4x4 symbolic Killing tensor :math:`K_{\mu\nu}` with
            ``M`` and ``a`` substituted but ``r`` and ``theta``
            symbolic.

        Notes:
            This is currently a stub returning ``sp.Matrix.zeros(4)``
            for the trivial limit ``a == 0`` (where every Killing
            tensor of Schwarzschild is reducible).  The full Kerr
            implementation will land in Phase 3 alongside the
            symplectic integrator that uses :math:`\mathcal{K}` as a
            conservation diagnostic.
        """
        # Stub.  The explicit 4x4 Killing tensor matrix is not needed
        # by the integrator-conservation diagnostic, which uses the
        # equivalent polynomial form ``carter_constant(state)`` below.
        # The Walker-Penrose construction is left for a future
        # holography-driven extension where K_{munu} itself appears.
        raise NotImplementedError(
            "Kerr.killing_tensor (explicit 4x4 matrix) is not yet "
            "implemented.  Use carter_constant_from_state(state) for "
            "the conserved quantity along a geodesic — it is the "
            "polynomial form of K_{mu nu} u^mu u^nu and is what the "
            "symplectic integrator uses as its conservation diagnostic."
        )

    def carter_constant(
        self,
        E: float,
        L_z: float,
        p_theta: float,
        theta: float,
        mu_squared: float = 1.0,
    ) -> float:
        r"""Compute Carter's constant :math:`\mathcal{Q}` directly from physics inputs.

        .. math::

            \mathcal{Q} = p_\theta^2 + \cos^2\theta\!\left[
                a^2(\mu^2 - E^2) + \frac{L_z^2}{\sin^2\theta}\right].

        Parameters
        ----------
        E : float
            Conserved energy at infinity, :math:`E = -p_t`.
        L_z : float
            Conserved axial angular momentum, :math:`L_z = p_\varphi`.
        p_theta : float
            Polar momentum component.
        theta : float
            Polar angle (colatitude).
        mu_squared : float
            Rest mass squared :math:`\mu^2`.  Use ``1.0`` for a
            massive particle on a normalised geodesic
            (:math:`-2H = 1`), or ``0.0`` for a photon.  Default 1.0.

        Returns
        -------
        float
            The value of :math:`\mathcal{Q}`.

        Notes
        -----
        For an *equatorial* geodesic (:math:`\theta = \pi/2`,
        :math:`p_\theta = 0`) the formula gives :math:`\mathcal{Q} = 0`
        identically — equatorial orbits sit on the boundary
        :math:`\mathcal{Q} = 0`.  Non-trivial values of
        :math:`\mathcal{Q}` characterise off-equator orbits.
        """
        a = self.spin
        cos2 = math.cos(theta) ** 2
        sin2 = math.sin(theta) ** 2
        if sin2 < 1e-300:
            raise ValueError(
                f"theta = {theta} is on the symmetry axis (sin theta -> 0); "
                f"Carter's constant has a coordinate singularity there. "
                f"Use a value strictly inside (0, pi)."
            )
        return p_theta * p_theta + cos2 * (
            a * a * (mu_squared - E * E) + L_z * L_z / sin2
        )

    def carter_constant_from_state(self, state) -> float:  # type: ignore[no-untyped-def]
        r"""Compute Carter's :math:`\mathcal{Q}` for the given geodesic state.

        Reads :math:`E = -p_t`, :math:`L_z = p_\varphi`, :math:`p_\theta`
        and :math:`\theta` from the state, infers the rest mass via
        the mass-shell :math:`\mu^2 = -2H = -g^{\mu\nu} p_\mu p_\nu`,
        and returns

        .. math::

            \mathcal{Q} = p_\theta^2 + \cos^2\theta\!\left[
                a^2(\mu^2 - E^2) + \frac{L_z^2}{\sin^2\theta}\right].

        Used by the integrator-conservation diagnostic in
        :class:`spacetime_lab.geodesics.GeodesicIntegrator`: along an
        accurately-integrated geodesic this value should be constant
        to within the integrator's accumulated error.

        Parameters
        ----------
        state : GeodesicState
            A point on the cotangent bundle, with covariant momentum
            ``p`` ordered as :math:`(p_t, p_r, p_\theta, p_\varphi)`
            in Boyer-Lindquist coordinates.

        Returns
        -------
        float
            The value of Carter's constant for that state.
        """
        # Local import to avoid a circular dependency at package
        # initialisation time.
        from spacetime_lab.geodesics import GeodesicState  # noqa: F401

        x = state.x
        p = state.p
        theta = float(x[2])
        E = -float(p[0])
        L_z = float(p[3])
        p_theta = float(p[2])

        # Mass-shell: mu^2 = -2H = -g^{munu} p_mu p_nu, evaluated
        # numerically.  We avoid recomputing the inverse metric here
        # by reusing the cached metric_at and inverting numerically.
        g = self.metric_at(t=float(x[0]), r=float(x[1]), theta=theta, phi=float(x[3]))
        import numpy as np

        g_inv = np.linalg.inv(g)
        mu_squared = -float(p @ g_inv @ p)
        return self.carter_constant(E, L_z, p_theta, theta, mu_squared)

    def constants_of_motion(self, state) -> dict:  # type: ignore[no-untyped-def]
        r"""Return the four constants of motion for a Kerr geodesic.

        Returns a dictionary with keys:

        - ``"E"``         — energy at infinity, :math:`-p_t`
        - ``"L_z"``       — axial angular momentum, :math:`p_\varphi`
        - ``"mu_squared"``— rest mass squared, :math:`-2H`
        - ``"Q"``         — Carter's constant

        For an exact geodesic all four are conserved along the orbit.
        Used by the test suite as a one-shot diagnostic of the
        symplectic integrator.
        """
        E = -float(state.p[0])
        L_z = float(state.p[3])
        Q = self.carter_constant_from_state(state)

        x = state.x
        p = state.p
        g = self.metric_at(
            t=float(x[0]), r=float(x[1]), theta=float(x[2]), phi=float(x[3])
        )
        import numpy as np

        g_inv = np.linalg.inv(g)
        mu_squared = -float(p @ g_inv @ p)

        return {
            "E": E,
            "L_z": L_z,
            "mu_squared": mu_squared,
            "Q": Q,
        }

    # ──────────────────────────────────────────────────────────────
    # Sanity checks
    # ──────────────────────────────────────────────────────────────

    def verify_vacuum_numerical(
        self,
        sample_points: list[tuple[float, float]] | None = None,
        atol: float = 1e-10,
    ) -> float:
        r"""Verify the vacuum Einstein equations :math:`R_{\mu\nu} = 0` numerically.

        Computes every component of the Ricci tensor as a sympy
        expression *without* calling ``sp.simplify`` (which is
        pathologically slow for Kerr — it can take minutes per
        component), then ``lambdify``\ s each component into a fast
        numerical function and evaluates it at a handful of sample
        :math:`(r, \theta)` points.  Returns the maximum absolute value
        observed.

        For an exact vacuum solution this must be at floating-point
        noise level (~ ``1e-15``).  If any metric coefficient were
        miswritten, this would shoot up to :math:`O(1)` immediately.

        This is the *strong* sanity test for the line element.

        Parameters
        ----------
        sample_points : list of (float, float), optional
            ``(r, theta)`` pairs at which to evaluate :math:`R_{\mu\nu}`.
            Defaults to a spread of off-axis, off-equator points
            outside the outer horizon.
        atol : float
            If ``max_abs > atol`` an :class:`AssertionError` is raised.
            Pass ``float('inf')`` to skip the assertion and only return
            the value.

        Returns
        -------
        float
            The maximum absolute value of any Ricci component over all
            sample points.

        Raises
        ------
        AssertionError
            If the maximum exceeds ``atol``.
        """
        # Default sample points: a spread of (r, theta) outside r_+ and
        # away from the symmetry axes / equator.
        if sample_points is None:
            rp = self.outer_horizon()
            sample_points = [
                (rp + 1.0, 0.5),
                (rp + 2.0, 1.0),
                (rp + 5.0, 1.2),
                (rp + 0.5, 0.7),
                (rp + 10.0, 0.3),
            ]

        M_sym = sp.Float(self.mass)
        a_sym = sp.Float(self.spin)
        r = self._r
        theta = self._theta
        coords = self.coordinates
        dim = 4

        # Build the metric directly here (not via metric_tensor) so we
        # control the symbolic form and skip every cache.
        Sigma = r**2 + a_sym**2 * sp.cos(theta) ** 2
        Delta = r**2 - 2 * M_sym * r + a_sym**2
        sin2 = sp.sin(theta) ** 2
        g_tt = -(1 - 2 * M_sym * r / Sigma)
        g_tphi = -(2 * M_sym * a_sym * r * sin2) / Sigma
        g_rr = Sigma / Delta
        g_thth = Sigma
        g_phiphi = (
            r**2 + a_sym**2 + (2 * M_sym * a_sym**2 * r * sin2) / Sigma
        ) * sin2
        g = sp.Matrix(
            [
                [g_tt, 0, 0, g_tphi],
                [0, g_rr, 0, 0],
                [0, 0, g_thth, 0],
                [g_tphi, 0, 0, g_phiphi],
            ]
        )

        # Inverse metric (no simplify — Kerr's inverse is fast on its own).
        g_inv = g.inv()

        # Christoffel symbols (no simplify, no caching).
        gamma = [
            [[sp.S.Zero for _ in range(dim)] for _ in range(dim)]
            for _ in range(dim)
        ]
        for mu in range(dim):
            for nu in range(dim):
                for lam in range(dim):
                    total = sp.S.Zero
                    for sigma_idx in range(dim):
                        term = (
                            sp.diff(g[lam, sigma_idx], coords[nu])
                            + sp.diff(g[nu, sigma_idx], coords[lam])
                            - sp.diff(g[nu, lam], coords[sigma_idx])
                        )
                        total += g_inv[mu, sigma_idx] * term
                    gamma[mu][nu][lam] = total / 2

        # Riemann tensor (no simplify).
        riemann = [
            [
                [[sp.S.Zero for _ in range(dim)] for _ in range(dim)]
                for _ in range(dim)
            ]
            for _ in range(dim)
        ]
        for rho in range(dim):
            for sigma_idx in range(dim):
                for mu in range(dim):
                    for nu in range(dim):
                        term = sp.diff(
                            gamma[rho][nu][sigma_idx], coords[mu]
                        ) - sp.diff(gamma[rho][mu][sigma_idx], coords[nu])
                        for lam in range(dim):
                            term += (
                                gamma[rho][mu][lam] * gamma[lam][nu][sigma_idx]
                                - gamma[rho][nu][lam] * gamma[lam][mu][sigma_idx]
                            )
                        riemann[rho][sigma_idx][mu][nu] = term

        # Contract to Ricci.
        ricci_funcs = []
        for mu in range(dim):
            for nu in range(dim):
                total = sp.S.Zero
                for lam in range(dim):
                    total += riemann[lam][mu][lam][nu]
                ricci_funcs.append(sp.lambdify((r, theta), total, "math"))

        max_abs = 0.0
        for f in ricci_funcs:
            for r_val, theta_val in sample_points:
                val = f(r_val, theta_val)
                if abs(val) > max_abs:
                    max_abs = abs(val)

        if max_abs > atol:
            raise AssertionError(
                f"Kerr is not vacuum: max |R_munu| = {max_abs} > atol = {atol}"
            )
        return max_abs

    def reduces_to_schwarzschild_at_zero_spin(self) -> bool:
        """Verify that ``Kerr(M, 0).metric_at`` matches Schwarzschild numerically.

        Compares the metric tensor at a fixed off-axis point against
        the closed-form Schwarzschild components.  This is a structural
        check on the line element: if the off-diagonal Kerr piece
        does not vanish at ``a = 0``, or the radial coefficient does
        not collapse to ``1/(1 - 2M/r)``, this returns False.

        Only meaningful when ``self.spin == 0``.

        Raises:
            ValueError: If called on a non-zero spin instance.
        """
        if self.spin != 0:
            raise ValueError(
                "reduces_to_schwarzschild_at_zero_spin only makes sense "
                "for spin=0; got spin={}".format(self.spin)
            )

        import numpy as np

        M = self.mass
        r_test = 5.0
        theta_test = 0.7  # generic, not on the axis or equator
        g = self.metric_at(t=0.0, r=r_test, theta=theta_test, phi=0.0)

        f = 1.0 - 2.0 * M / r_test
        expected = np.diag(
            [
                -f,
                1.0 / f,
                r_test * r_test,
                r_test * r_test * math.sin(theta_test) ** 2,
            ]
        ).astype(float)

        return bool(np.allclose(g, expected, atol=1e-12))

    # ──────────────────────────────────────────────────────────────
    # Representation
    # ──────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"Kerr(mass={self.mass}, spin={self.spin})"

    def line_element_latex(self) -> str:
        """Return the canonical Boyer-Lindquist line element as LaTeX."""
        return (
            r"ds^2 = -\left(1 - \frac{2Mr}{\Sigma}\right) dt^2"
            r"- \frac{4Mar\sin^2\theta}{\Sigma}\, dt\, d\varphi"
            r"+ \frac{\Sigma}{\Delta}\, dr^2 + \Sigma\, d\theta^2"
            r"+ \left(r^2 + a^2 + \frac{2Ma^2 r\sin^2\theta}{\Sigma}\right)"
            r"\sin^2\theta\, d\varphi^2"
        )
