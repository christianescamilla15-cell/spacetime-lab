"""Abstract base class for Lorentzian metrics.

All metric solutions in Spacetime Lab inherit from `Metric`, which provides
a unified interface for symbolic and numerical computation.

Convention:
    - Signature: (-, +, +, +)
    - Geometric units: G = c = 1 unless otherwise specified
    - Coordinates are metric-specific (e.g., Boyer-Lindquist for Kerr)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

import numpy as np
import sympy as sp


class Metric(ABC):
    """Abstract base class for all Lorentzian metrics.

    Subclasses must implement:
        - `coordinates` — list of symbolic coordinates
        - `metric_tensor` — symbolic 4x4 metric tensor
        - `name` — human-readable name of the metric

    Provides automatically:
        - Inverse metric
        - Christoffel symbols
        - Riemann tensor
        - Ricci tensor and scalar
        - Kretschmann scalar
        - LaTeX rendering
        - Numerical evaluation at a point
    """

    def __init__(self) -> None:
        self._inverse: sp.Matrix | None = None
        self._christoffel: list[list[list[sp.Expr]]] | None = None
        self._riemann: list[list[list[list[sp.Expr]]]] | None = None
        self._ricci: sp.Matrix | None = None
        self._ricci_scalar: sp.Expr | None = None
        self._kretschmann: sp.Expr | None = None

    # ──────────────────────────────────────────────────────────────
    # Abstract properties (subclasses must provide)
    # ──────────────────────────────────────────────────────────────

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the metric (e.g., 'Schwarzschild')."""
        ...

    @property
    @abstractmethod
    def coordinates(self) -> list[sp.Symbol]:
        """List of symbolic coordinates, e.g., [t, r, theta, phi]."""
        ...

    @property
    @abstractmethod
    def metric_tensor(self) -> sp.Matrix:
        """Symbolic 4x4 metric tensor g_{mu nu}."""
        ...

    # ──────────────────────────────────────────────────────────────
    # Derived geometric quantities
    # ──────────────────────────────────────────────────────────────

    @property
    def dim(self) -> int:
        """Dimension of the manifold (usually 4)."""
        return len(self.coordinates)

    @property
    def inverse_metric(self) -> sp.Matrix:
        """Inverse metric g^{mu nu}."""
        if self._inverse is None:
            self._inverse = sp.simplify(self.metric_tensor.inv())
        return self._inverse

    def christoffel_symbols(self) -> list[list[list[sp.Expr]]]:
        """Christoffel symbols of the second kind Gamma^{mu}_{nu lambda}.

        Returns a 3D list: christoffel[mu][nu][lambda]

        Formula:
            Gamma^{mu}_{nu lambda} = (1/2) g^{mu sigma} (
                d_nu g_{lambda sigma} + d_lambda g_{nu sigma} - d_sigma g_{nu lambda}
            )
        """
        if self._christoffel is not None:
            return self._christoffel

        g = self.metric_tensor
        g_inv = self.inverse_metric
        coords = self.coordinates
        dim = self.dim

        gamma = [[[sp.S.Zero for _ in range(dim)] for _ in range(dim)] for _ in range(dim)]

        for mu in range(dim):
            for nu in range(dim):
                for lam in range(dim):
                    total = sp.S.Zero
                    for sigma in range(dim):
                        term = (
                            sp.diff(g[lam, sigma], coords[nu])
                            + sp.diff(g[nu, sigma], coords[lam])
                            - sp.diff(g[nu, lam], coords[sigma])
                        )
                        total += g_inv[mu, sigma] * term
                    gamma[mu][nu][lam] = sp.simplify(total / 2)

        self._christoffel = gamma
        return gamma

    def ricci_scalar(self) -> sp.Expr:
        """Ricci scalar R = g^{mu nu} R_{mu nu}.

        Cached for performance. Recomputing from scratch requires the
        Riemann tensor which is O(dim^4) in memory.
        """
        if self._ricci_scalar is not None:
            return self._ricci_scalar

        ricci = self._compute_ricci_tensor()
        g_inv = self.inverse_metric
        dim = self.dim

        scalar = sp.S.Zero
        for mu in range(dim):
            for nu in range(dim):
                scalar += g_inv[mu, nu] * ricci[mu, nu]

        self._ricci_scalar = sp.simplify(scalar)
        return self._ricci_scalar

    def _compute_ricci_tensor(self) -> sp.Matrix:
        """Compute the Ricci tensor R_{mu nu} = R^{lambda}_{mu lambda nu}."""
        if self._ricci is not None:
            return self._ricci

        riemann = self._compute_riemann()
        dim = self.dim
        ricci = sp.zeros(dim, dim)

        for mu in range(dim):
            for nu in range(dim):
                total = sp.S.Zero
                for lam in range(dim):
                    total += riemann[lam][mu][lam][nu]
                ricci[mu, nu] = sp.simplify(total)

        self._ricci = ricci
        return ricci

    def _compute_riemann(self) -> list[list[list[list[sp.Expr]]]]:
        """Compute the Riemann curvature tensor R^{rho}_{sigma mu nu}."""
        if self._riemann is not None:
            return self._riemann

        gamma = self.christoffel_symbols()
        coords = self.coordinates
        dim = self.dim

        riemann = [
            [
                [[sp.S.Zero for _ in range(dim)] for _ in range(dim)]
                for _ in range(dim)
            ]
            for _ in range(dim)
        ]

        for rho in range(dim):
            for sigma in range(dim):
                for mu in range(dim):
                    for nu in range(dim):
                        term = sp.diff(gamma[rho][nu][sigma], coords[mu]) - sp.diff(
                            gamma[rho][mu][sigma], coords[nu]
                        )
                        for lam in range(dim):
                            term += (
                                gamma[rho][mu][lam] * gamma[lam][nu][sigma]
                                - gamma[rho][nu][lam] * gamma[lam][mu][sigma]
                            )
                        riemann[rho][sigma][mu][nu] = sp.simplify(term)

        self._riemann = riemann
        return riemann

    # ──────────────────────────────────────────────────────────────
    # Numerical evaluation
    # ──────────────────────────────────────────────────────────────

    def metric_at(self, **coords: float) -> np.ndarray:
        """Evaluate the metric tensor numerically at a point.

        Args:
            **coords: Keyword arguments matching coordinate names.

        Returns:
            4x4 numpy array with the metric components.

        Example:
            >>> bh = Schwarzschild(mass=1.0)
            >>> g = bh.metric_at(r=3.0, theta=1.5708)
        """
        subs_dict = {}
        for coord in self.coordinates:
            name = str(coord)
            if name in coords:
                subs_dict[coord] = coords[name]

        numeric = self.metric_tensor.subs(subs_dict)
        return np.array(numeric.tolist(), dtype=np.float64)

    # ──────────────────────────────────────────────────────────────
    # Representation
    # ──────────────────────────────────────────────────────────────

    def line_element_latex(self) -> str:
        """Return the line element ds^2 as a LaTeX string."""
        coords = self.coordinates
        g = self.metric_tensor
        dim = self.dim

        terms: list[str] = []
        for mu in range(dim):
            for nu in range(dim):
                component = g[mu, nu]
                if component == 0:
                    continue
                dmu = sp.Symbol(f"d{coords[mu]}")
                dnu = sp.Symbol(f"d{coords[nu]}")
                terms.append(sp.latex(component * dmu * dnu))

        return "ds^2 = " + " + ".join(terms) if terms else "ds^2 = 0"

    def __repr__(self) -> str:
        return f"<{self.name} metric in {self.dim}D>"
