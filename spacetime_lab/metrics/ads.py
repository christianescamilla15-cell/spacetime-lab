r"""Anti-de Sitter spacetime in Poincaré coordinates.

Anti-de Sitter space :math:`\mathrm{AdS}_n` is the maximally symmetric
Lorentzian manifold with constant negative scalar curvature.  It is
the unique solution of the vacuum Einstein equations with a negative
cosmological constant:

.. math::

    R_{\mu\nu} - \tfrac{1}{2} R g_{\mu\nu} + \Lambda g_{\mu\nu} = 0,
    \qquad \Lambda = -\frac{(n-1)(n-2)}{2 L^2}.

Here we use Poincaré coordinates :math:`(t, x_1, \ldots, x_{n-2}, z)`
with :math:`z > 0`:

.. math::

    ds^2 = \frac{L^2}{z^2}\left(-dt^2 + dx_1^2 + \cdots + dx_{n-2}^2
                                + dz^2\right).

The conformal boundary is at :math:`z \to 0^+`.

In our notation, ``dimension`` refers to the dimension :math:`n` of
the bulk spacetime, so ``dimension = 3`` is :math:`\mathrm{AdS}_3`
(2+1 dimensional), with a 2D conformal boundary on which the dual
CFT lives.

Verified analytic identities (used in the test suite)
=====================================================

For :math:`\mathrm{AdS}_n` with radius :math:`L`:

- Ricci tensor:        :math:`R_{\mu\nu} = -\frac{n-1}{L^2}\,g_{\mu\nu}`
- Ricci scalar:        :math:`R = -\frac{n(n-1)}{L^2}`
- Cosmological const.: :math:`\Lambda = -\frac{(n-1)(n-2)}{2 L^2}`

Source: Wikipedia, *Anti-de Sitter space*; standard textbook material.
"""

from __future__ import annotations

import math

import numpy as np
import sympy as sp

from spacetime_lab.metrics.base import Metric


class AdS(Metric):
    r"""Pure anti-de Sitter spacetime in Poincaré coordinates.

    Args:
        dimension: Number of bulk spacetime dimensions :math:`n`.
            Must be at least 2.  ``dimension = 3`` is the most useful
            case (AdS\ :sub:`3` / CFT\ :sub:`2`); higher dimensions
            are also supported.
        radius: AdS radius :math:`L > 0`.

    Coordinates:
        For ``dimension = n``, the coordinates are
        :math:`(t, x_1, \ldots, x_{n-2}, z)` with :math:`z > 0`.
        The conformal boundary is at :math:`z \to 0^+`.

    Example:
        >>> ads = AdS(dimension=3, radius=2.0)
        >>> ads.cosmological_constant()  # -1/L^2 in 3d
        -0.25
        >>> abs(ads.expected_ricci_scalar() - (-1.5)) < 1e-12  # -6/L^2 = -6/4
        True
    """

    def __init__(self, dimension: int = 3, radius: float = 1.0) -> None:
        super().__init__()
        if not isinstance(dimension, int) or dimension < 2:
            raise ValueError(f"dimension must be int >= 2, got {dimension}")
        if not isinstance(radius, (int, float)) or radius <= 0:
            raise ValueError(f"radius must be positive, got {radius}")

        self.dimension: int = int(dimension)
        self.radius: float = float(radius)

        # Coordinates: (t, x_1, ..., x_{n-2}, z)
        n = self.dimension
        self._t = sp.Symbol("t", real=True)
        self._spatial = [
            sp.Symbol(f"x{i}", real=True) for i in range(1, n - 1)
        ]
        self._z = sp.Symbol("z", positive=True)

        self._metric_cache: sp.Matrix | None = None

    # ──────────────────────────────────────────────────────────────
    # Abstract properties from Metric base
    # ──────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return f"AdS_{self.dimension} (Poincare coords)"

    @property
    def coordinates(self) -> list[sp.Symbol]:
        return [self._t, *self._spatial, self._z]

    @property
    def metric_tensor(self) -> sp.Matrix:
        r"""Poincaré-coordinate metric tensor.

        .. math::

            g_{\mu\nu} = \frac{L^2}{z^2}\,\eta_{\mu\nu}

        where :math:`\eta = \mathrm{diag}(-1, +1, \ldots, +1)` and
        the last coordinate is :math:`z`.
        """
        if self._metric_cache is not None:
            return self._metric_cache

        n = self.dimension
        L = sp.Float(self.radius)
        z = self._z
        prefactor = L**2 / z**2

        # Build the diag(-1, 1, ..., 1) Minkowski form, with the last
        # coordinate (z) carrying a +1 (it's spacelike).
        signature = [-1] + [1] * (n - 1)
        g = sp.zeros(n, n)
        for i, s in enumerate(signature):
            g[i, i] = prefactor * s

        self._metric_cache = g
        return g

    # ──────────────────────────────────────────────────────────────
    # Analytic invariants
    # ──────────────────────────────────────────────────────────────

    def cosmological_constant(self) -> float:
        r"""Cosmological constant :math:`\Lambda = -(n-1)(n-2)/(2 L^2)`.

        For :math:`n = 3`: :math:`\Lambda = -1/L^2`.  For :math:`n = 4`:
        :math:`\Lambda = -3/L^2`.
        """
        n = self.dimension
        L = self.radius
        return -(n - 1) * (n - 2) / (2 * L * L)

    def expected_ricci_scalar(self) -> float:
        r"""Analytic Ricci scalar :math:`R = -n(n-1)/L^2`.

        Verified against the symbolic computation by
        :meth:`verify_einstein_constant_curvature`.
        """
        n = self.dimension
        L = self.radius
        return -n * (n - 1) / (L * L)

    def expected_ricci_proportionality(self) -> float:
        r"""Analytic constant :math:`-(n-1)/L^2` such that
        :math:`R_{\mu\nu} = c \cdot g_{\mu\nu}`.
        """
        n = self.dimension
        L = self.radius
        return -(n - 1) / (L * L)

    # ──────────────────────────────────────────────────────────────
    # Numerical vacuum-Einstein verification
    # ──────────────────────────────────────────────────────────────

    def verify_einstein_constant_curvature(
        self,
        sample_points: list[dict[str, float]] | None = None,
        atol: float = 1e-10,
    ) -> float:
        r"""Verify :math:`R_{\mu\nu} - c \cdot g_{\mu\nu} = 0` numerically.

        Following the Phase 3 lesson (sympy ``simplify`` is
        pathologically slow on non-trivial metrics), we lambdify the
        Ricci tensor and the metric tensor as numerical functions and
        evaluate :math:`|R_{\mu\nu} - c \cdot g_{\mu\nu}|` at sample
        points, where :math:`c = -(n-1)/L^2` is the expected
        proportionality constant.

        Returns the maximum absolute deviation observed (should be at
        floating-point noise level for a correct AdS line element).

        Parameters
        ----------
        sample_points : list of dict, optional
            Each dict assigns floats to the coordinate symbols.
            Defaults to a small spread of off-axis points away from
            :math:`z = 0`.
        atol : float
            Asserts the maximum deviation does not exceed this.

        Returns
        -------
        float
            The max absolute deviation across all sampled points and
            tensor components.

        Raises
        ------
        AssertionError
            If the deviation exceeds ``atol``.
        """
        n = self.dimension
        coords = self.coordinates
        if sample_points is None:
            # Off-axis points safely away from the boundary z = 0.
            sample_points = []
            for z_val in (0.5, 1.0, 2.0):
                pt = {"t": 0.3, "z": z_val}
                for i, sym in enumerate(self._spatial, start=1):
                    pt[str(sym)] = 0.4 * i
                sample_points.append(pt)

        # Build the metric (no simplify) and its inverse.
        L = sp.Float(self.radius)
        z = self._z
        prefactor = L**2 / z**2
        signature = [-1] + [1] * (n - 1)
        g = sp.zeros(n, n)
        for i, s in enumerate(signature):
            g[i, i] = prefactor * s
        g_inv = g.inv()

        # Christoffel symbols (no simplify).
        gamma = [
            [[sp.S.Zero for _ in range(n)] for _ in range(n)]
            for _ in range(n)
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

        # Riemann tensor.
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

        # Ricci tensor.
        ricci_funcs = []
        for mu in range(n):
            for nu in range(n):
                total = sp.S.Zero
                for lam in range(n):
                    total += riemann[lam][mu][lam][nu]
                # The expected proportionality: R_{mu nu} = c * g_{mu nu}
                # with c = -(n-1)/L^2.  Form the residual symbolically
                # but skip simplify; lambdify and evaluate numerically.
                expected_c = -sp.Float(n - 1) / (L * L)
                residual = total - expected_c * g[mu, nu]
                ricci_funcs.append(
                    (mu, nu, sp.lambdify(coords, residual, "math"))
                )

        max_abs = 0.0
        for _, _, f in ricci_funcs:
            for pt in sample_points:
                args = [pt[str(c)] for c in coords]
                val = f(*args)
                if abs(val) > max_abs:
                    max_abs = abs(val)

        if max_abs > atol:
            raise AssertionError(
                f"AdS_{n} (radius={self.radius}) is not Einstein-constant: "
                f"max |R_munu - c g_munu| = {max_abs} > atol = {atol}"
            )
        return max_abs

    # ──────────────────────────────────────────────────────────────
    # Representation
    # ──────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"AdS(dimension={self.dimension}, radius={self.radius})"

    def line_element_latex(self) -> str:
        n = self.dimension
        spatial = " + ".join(f"dx_{i}^2" for i in range(1, n - 1))
        spatial_part = f"+ {spatial} " if spatial else ""
        return (
            r"ds^2 = \frac{L^2}{z^2}\left(-dt^2 "
            f"{spatial_part}"
            r"+ dz^2\right)"
        )
