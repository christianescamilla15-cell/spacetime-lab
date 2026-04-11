r"""BTZ black hole — the simplest known black hole.

Discovered by Bañados, Teitelboim & Zanelli in 1992
(*Phys. Rev. Lett.* **69** 1849), the BTZ black hole is the AdS\
:sub:`3` analogue of Schwarzschild.  It is a genuine black hole with
a horizon, a Hawking temperature, and a Bekenstein-Hawking entropy
— but it lives in 2+1 dimensions in an asymptotically AdS\ :sub:`3`
background, not asymptotically flat space.

Profoundly: BTZ has **zero local curvature beyond what AdS\ :sub:`3`
already has**.  It is a quotient of AdS\ :sub:`3` by a discrete
subgroup of its isometry group, with the angular coordinate made
periodic.  The horizon, the entropy, and the Hawking temperature are
consequences of this *global* identification, not of any new local
curvature.  This is why BTZ is "the simplest black hole".

The non-rotating, uncharged BTZ metric in Schwarzschild-like
coordinates :math:`(t, r, \varphi)` with :math:`\varphi \in [0, 2\pi)`:

.. math::

    ds^2 = -\frac{r^2 - r_+^2}{L^2}\,dt^2
           + \frac{L^2}{r^2 - r_+^2}\,dr^2
           + r^2\,d\varphi^2,

where :math:`r_+` is the horizon radius and :math:`L` is the AdS
radius.  The bulk has :math:`r > r_+`; the boundary is at
:math:`r \to \infty`.

Verified analytic identities (used in the test suite)
=====================================================

For non-rotating BTZ at horizon radius :math:`r_+` and AdS radius
:math:`L`:

- Hawking temperature:    :math:`T_H = \dfrac{r_+}{2\pi L^2}`
- Mass parameter:         :math:`M = \dfrac{r_+^2}{8 G_N L^2}`
  (in standard normalisation)
- Bekenstein-Hawking entropy: :math:`S_{BH} = \dfrac{2\pi r_+}{4 G_N}
  = \dfrac{\pi r_+}{2 G_N}`
- The metric satisfies Einstein with negative cosmological constant:
  :math:`R_{\mu\nu} = -\dfrac{2}{L^2}\,g_{\mu\nu}`

Sources: Bañados-Teitelboim-Zanelli 1992 (Phys. Rev. Lett. **69** 1849);
Wikipedia *BTZ black hole*; standard textbook material.

Strominger 1998 (hep-th/9712251) showed that this entropy is exactly
reproduced by the Cardy formula on the boundary 2D CFT at the
matching temperature, with the central charge given by the
Brown-Henneaux relation :math:`c = 3 L / (2 G_N)`.  We verify this
match numerically in
:func:`spacetime_lab.holography.btz.verify_strominger_btz_cardy`.
"""

from __future__ import annotations

import math

import numpy as np
import sympy as sp

from spacetime_lab.metrics.base import Metric


class BTZ(Metric):
    r"""Non-rotating, uncharged BTZ black hole in 2+1 dimensions.

    Args:
        horizon_radius: Outer horizon radius :math:`r_+ > 0`.  In
            geometric units this has dimensions of length.
        ads_radius: AdS radius :math:`L > 0`.  Default ``1.0``.

    Coordinates:
        :math:`(t, r, \varphi)` with :math:`r > r_+` (the bulk
        outside the horizon) and :math:`\varphi \in [0, 2\pi)`.

    Example:
        >>> bh = BTZ(horizon_radius=1.0, ads_radius=1.0)
        >>> abs(bh.hawking_temperature() - 1.0/(2*3.141592653589793)) < 1e-12
        True
        >>> bh.bekenstein_hawking_entropy()  # pi r_+ / (2 G_N) with G_N=1
        1.5707963267948966

    Notes
    -----
    Phase 8 implements only the non-rotating, uncharged BTZ.  The
    rotating case (with angular momentum :math:`J \neq 0`) and the
    charged case have richer thermodynamic structure (inner horizon,
    extremal limit) and are deferred to a future patch.
    """

    def __init__(
        self,
        horizon_radius: float,
        ads_radius: float = 1.0,
    ) -> None:
        super().__init__()
        if not isinstance(horizon_radius, (int, float)) or horizon_radius <= 0:
            raise ValueError(
                f"horizon_radius must be positive, got {horizon_radius}"
            )
        if not isinstance(ads_radius, (int, float)) or ads_radius <= 0:
            raise ValueError(f"ads_radius must be positive, got {ads_radius}")

        self.horizon_radius: float = float(horizon_radius)
        self.ads_radius: float = float(ads_radius)

        self._t = sp.Symbol("t", real=True)
        self._r = sp.Symbol("r", positive=True)
        self._phi = sp.Symbol("phi", real=True)

        self._metric_cache: sp.Matrix | None = None

    # ──────────────────────────────────────────────────────────────
    # Metric base interface
    # ──────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return f"BTZ (r_+={self.horizon_radius}, L={self.ads_radius})"

    @property
    def coordinates(self) -> list[sp.Symbol]:
        return [self._t, self._r, self._phi]

    @property
    def metric_tensor(self) -> sp.Matrix:
        r"""Symbolic 3x3 BTZ metric tensor.

        .. math::

            g_{\mu\nu} = \mathrm{diag}\!\left(
                -\frac{r^2 - r_+^2}{L^2},\;
                \frac{L^2}{r^2 - r_+^2},\;
                r^2\right).
        """
        if self._metric_cache is not None:
            return self._metric_cache

        rp = sp.Float(self.horizon_radius)
        L = sp.Float(self.ads_radius)
        r = self._r

        f = (r * r - rp * rp) / (L * L)
        g = sp.Matrix(
            [
                [-f, 0, 0],
                [0, 1 / f, 0],
                [0, 0, r * r],
            ]
        )

        self._metric_cache = g
        return g

    # ──────────────────────────────────────────────────────────────
    # Thermodynamic invariants — analytic
    # ──────────────────────────────────────────────────────────────

    def hawking_temperature(self) -> float:
        r"""Return :math:`T_H = r_+ / (2 \pi L^2)`.

        Standard non-rotating BTZ result.  In the Schwarzschild limit
        :math:`L \to \infty` this collapses (the BTZ horizon
        decompactifies into a Rindler-like surface), but for finite
        :math:`L` the temperature scales linearly with the horizon
        radius.
        """
        rp = self.horizon_radius
        L = self.ads_radius
        return rp / (2.0 * math.pi * L * L)

    def bekenstein_hawking_entropy(self, G_N: float = 1.0) -> float:
        r"""Return :math:`S_{BH} = 2 \pi r_+ / (4 G_N) = \pi r_+ / (2 G_N)`.

        The 2-dimensional analogue of the area law: in 2+1 dimensions
        the "area" of the horizon is the *circumference* of the
        horizon circle, :math:`2 \pi r_+`.  Divided by :math:`4 G_N`
        gives the standard Bekenstein-Hawking entropy.

        Verified by Strominger 1998 against the Cardy formula on the
        boundary CFT.
        """
        if G_N <= 0:
            raise ValueError(f"G_N must be positive, got {G_N}")
        rp = self.horizon_radius
        return math.pi * rp / (2.0 * G_N)

    def mass_parameter(self, G_N: float = 1.0) -> float:
        r"""Return the BTZ mass parameter :math:`M = r_+^2 / (8 G_N L^2)`.

        Standard convention from Bañados-Teitelboim-Zanelli 1992.
        Different references absorb factors of :math:`8 G_N` into
        slightly different conventions; this implementation uses
        :math:`M = r_+^2 / (8 G_N L^2)`, consistent with the rotating
        formula :math:`M = (r_+^2 + r_-^2) / (8 G_N L^2)`.
        """
        if G_N <= 0:
            raise ValueError(f"G_N must be positive, got {G_N}")
        rp = self.horizon_radius
        L = self.ads_radius
        return rp * rp / (8.0 * G_N * L * L)

    def thermal_beta(self) -> float:
        r"""Inverse Hawking temperature, :math:`\beta = 2 \pi L^2 / r_+`."""
        return 1.0 / self.hawking_temperature()

    # ──────────────────────────────────────────────────────────────
    # Numerical Einstein-constant verification
    # ──────────────────────────────────────────────────────────────

    def verify_einstein_constant_curvature(
        self,
        sample_points: list[dict[str, float]] | None = None,
        atol: float = 1e-10,
    ) -> float:
        r"""Verify :math:`R_{\mu\nu} = -2/L^2 \cdot g_{\mu\nu}` numerically.

        BTZ is locally AdS\ :sub:`3` (it is a quotient of AdS\
        :sub:`3` by a discrete isometry), so it must satisfy the
        same Einstein-constant equation:

        .. math::

            R_{\mu\nu} = -\frac{2}{L^2}\,g_{\mu\nu}.

        We compute the residual numerically using the same
        lambdified-not-simplified pattern as
        :class:`spacetime_lab.metrics.ads.AdS`.

        Parameters
        ----------
        sample_points : list of dict, optional
            Each dict assigns floats to ``t``, ``r``, ``phi``.
            Defaults to a small spread of points safely outside the
            horizon.
        atol : float
            Tolerance for the residual.

        Returns
        -------
        float
            The maximum absolute residual.

        Raises
        ------
        AssertionError
            If the residual exceeds ``atol``.
        """
        if sample_points is None:
            rp = self.horizon_radius
            sample_points = [
                {"t": 0.3, "r": rp + 1.0, "phi": 0.5},
                {"t": 0.0, "r": rp + 2.0, "phi": 1.0},
                {"t": -0.5, "r": rp + 5.0, "phi": 2.0},
                {"t": 1.0, "r": rp + 0.5, "phi": 0.0},
            ]

        n = 3
        coords = self.coordinates
        rp_sym = sp.Float(self.horizon_radius)
        L_sym = sp.Float(self.ads_radius)
        r = self._r

        f = (r * r - rp_sym * rp_sym) / (L_sym * L_sym)
        g = sp.Matrix(
            [
                [-f, 0, 0],
                [0, 1 / f, 0],
                [0, 0, r * r],
            ]
        )
        g_inv = g.inv()

        # Christoffel
        gamma = [
            [[sp.S.Zero for _ in range(n)] for _ in range(n)] for _ in range(n)
        ]
        for mu in range(n):
            for nu in range(n):
                for lam in range(n):
                    total = sp.S.Zero
                    for sigma_idx in range(n):
                        term = (
                            sp.diff(g[lam, sigma_idx], coords[nu])
                            + sp.diff(g[nu, sigma_idx], coords[lam])
                            - sp.diff(g[nu, lam], coords[sigma_idx])
                        )
                        total += g_inv[mu, sigma_idx] * term
                    gamma[mu][nu][lam] = total / 2

        # Riemann tensor
        riemann = [
            [
                [[sp.S.Zero for _ in range(n)] for _ in range(n)]
                for _ in range(n)
            ]
            for _ in range(n)
        ]
        for rho in range(n):
            for sigma_idx in range(n):
                for mu in range(n):
                    for nu in range(n):
                        term = sp.diff(
                            gamma[rho][nu][sigma_idx], coords[mu]
                        ) - sp.diff(gamma[rho][mu][sigma_idx], coords[nu])
                        for lam in range(n):
                            term += (
                                gamma[rho][mu][lam] * gamma[lam][nu][sigma_idx]
                                - gamma[rho][nu][lam] * gamma[lam][mu][sigma_idx]
                            )
                        riemann[rho][sigma_idx][mu][nu] = term

        # Ricci tensor and residual
        expected_c = -sp.Float(2) / (L_sym * L_sym)
        ricci_funcs = []
        for mu in range(n):
            for nu in range(n):
                total = sp.S.Zero
                for lam in range(n):
                    total += riemann[lam][mu][lam][nu]
                residual = total - expected_c * g[mu, nu]
                ricci_funcs.append(
                    sp.lambdify(coords, residual, "math")
                )

        max_abs = 0.0
        for f_lam in ricci_funcs:
            for pt in sample_points:
                args = [pt[str(c)] for c in coords]
                val = f_lam(*args)
                if abs(val) > max_abs:
                    max_abs = abs(val)

        if max_abs > atol:
            raise AssertionError(
                f"BTZ (r_+={self.horizon_radius}, L={self.ads_radius}) "
                f"is not Einstein-constant: max residual = {max_abs}"
            )
        return max_abs

    # ──────────────────────────────────────────────────────────────
    # Representation
    # ──────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"BTZ(horizon_radius={self.horizon_radius}, "
            f"ads_radius={self.ads_radius})"
        )

    def line_element_latex(self) -> str:
        return (
            r"ds^2 = -\frac{r^2 - r_+^2}{L^2} dt^2 "
            r"+ \frac{L^2}{r^2 - r_+^2} dr^2 + r^2 d\varphi^2"
        )
