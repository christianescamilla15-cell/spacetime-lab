r"""Implicit-midpoint symplectic integrator for geodesic motion.

The geodesic equation in any Lorentzian metric :math:`g_{\mu\nu}` is
the Euler-Lagrange equation of the action :math:`S = \int g_{\mu\nu}
\dot x^\mu \dot x^\nu \, d\lambda`, which is equivalent to Hamilton's
equations for the Hamiltonian

.. math::

    H(x, p) = \tfrac{1}{2}\, g^{\mu\nu}(x)\, p_\mu p_\nu,

with conjugate momentum :math:`p_\mu = g_{\mu\nu}\, \dot x^\nu`.  The
4-velocity is recovered as :math:`u^\mu = \dot x^\mu = g^{\mu\nu}
p_\nu`.  Equations of motion:

.. math::

    \frac{dx^\mu}{d\lambda} = g^{\mu\nu}(x)\, p_\nu, \qquad
    \frac{dp_\mu}{d\lambda} = -\tfrac{1}{2}\,
        \partial_\mu g^{\alpha\beta}(x)\, p_\alpha p_\beta.

Why implicit midpoint
=====================

For Kerr the Hamiltonian is **non-separable**: the "kinetic" term
:math:`\tfrac{1}{2} g^{\mu\nu}(x) p_\mu p_\nu` depends on the
position :math:`x` through the inverse metric.  Standard leapfrog only
works for separable :math:`H = T(p) + V(x)`, so we use the implicit
midpoint method instead:

.. math::

    x_{n+1} &= x_n + h \cdot \dot x\!\left(\tfrac{x_n + x_{n+1}}{2},
        \tfrac{p_n + p_{n+1}}{2}\right), \\
    p_{n+1} &= p_n + h \cdot \dot p\!\left(\tfrac{x_n + x_{n+1}}{2},
        \tfrac{p_n + p_{n+1}}{2}\right).

This is a one-stage Gauss-Legendre Runge-Kutta scheme: it is
**symplectic**, **time-reversible**, **2nd-order accurate**, and
applies unchanged to non-separable Hamiltonians.  The system is solved
at each step by passing the residuals to :func:`scipy.optimize.fsolve`.

Cyclic-coordinate exact conservation
====================================

If the metric does not depend on a coordinate :math:`x^\alpha` (i.e.
:math:`\partial_\alpha g^{\mu\nu} = 0`), then :math:`\dot p_\alpha = 0`
identically — the conjugate momentum is exactly conserved by the
equations of motion.  The implicit midpoint method preserves this
exactly, so :math:`p_\alpha` is conserved to **machine precision**.

For Kerr in Boyer-Lindquist this means :math:`E = -p_t` and
:math:`L_z = +p_\varphi` are exactly conserved by the integrator.
The mass-shell :math:`H = -\mu^2/2` and Carter's constant
:math:`\mathcal{Q}` are conserved by the *true* geodesics, but the
integrator only achieves :math:`O(h^2)` per-step error on them.
Their drift is therefore the practical diagnostic that the
integration is faithful to the geodesic equation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
import sympy as sp

if TYPE_CHECKING:
    from spacetime_lab.metrics.base import Metric


@dataclass
class GeodesicState:
    r"""A point on the cotangent bundle: position + covariant momentum.

    Parameters
    ----------
    x : array_like, shape (4,)
        Spacetime coordinates :math:`x^\mu`.  For Boyer-Lindquist
        Kerr these are :math:`(t, r, \theta, \varphi)`.
    p : array_like, shape (4,)
        **Covariant** momentum components :math:`p_\mu`.  Note: this
        is not the contravariant 4-velocity.  The 4-velocity is
        recovered as :math:`u^\mu = g^{\mu\nu} p_\nu`.

    Notes
    -----
    The covariant convention is used because the cyclic-coordinate
    conservation laws are statements about :math:`p_\mu` (e.g.
    :math:`E = -p_t` is conserved iff :math:`\partial_t g^{\alpha\beta}
    = 0`), which makes the integrator's conservation properties more
    transparent.
    """

    x: np.ndarray
    p: np.ndarray

    def __post_init__(self) -> None:
        self.x = np.asarray(self.x, dtype=float).copy()
        self.p = np.asarray(self.p, dtype=float).copy()
        if self.x.shape != (4,):
            raise ValueError(f"x must have shape (4,), got {self.x.shape}")
        if self.p.shape != (4,):
            raise ValueError(f"p must have shape (4,), got {self.p.shape}")

    def copy(self) -> "GeodesicState":
        return GeodesicState(x=self.x.copy(), p=self.p.copy())


class GeodesicIntegrator:
    r"""Symplectic implicit-midpoint integrator for geodesic motion.

    Parameters
    ----------
    metric : Metric
        Any subclass of :class:`spacetime_lab.metrics.base.Metric`.
        The integrator will lambdify the inverse metric and its
        coordinate derivatives once at construction time, then use
        the resulting numerical functions at every step.
    rtol : float
        Relative tolerance passed to :func:`scipy.optimize.fsolve` for
        the implicit-midpoint root finding.  Default ``1e-12``.
    max_iter : int
        Maximum iteration count for the implicit solve.  Default 50.
    """

    def __init__(
        self,
        metric: "Metric",
        *,
        rtol: float = 1e-12,
        max_iter: int = 50,
    ) -> None:
        self.metric = metric
        self.rtol = rtol
        self.max_iter = max_iter
        self._build_numerical_functions()

    # ------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------

    def _build_numerical_functions(self) -> None:
        r"""Lambdify :math:`g^{\mu\nu}(x)` and :math:`\partial_\mu g^{\alpha\beta}(x)`.

        Done once at construction time so that every integration step
        only does numerical work.  Skips :class:`sympy.simplify`
        entirely (it is pathological for Kerr).
        """
        coords = self.metric.coordinates
        g = self.metric.metric_tensor
        g_inv = g.inv()

        # Lambdify the full 4x4 inverse metric.  Returns a numpy array
        # of shape (4, 4) given coordinate values.
        self._g_inv_func = sp.lambdify(coords, g_inv, modules="numpy")

        # Partial derivatives ∂_μ g^{αβ}.  One 4x4 matrix per coord.
        self._dg_inv_funcs: list[Any] = []
        for mu in range(4):
            dg = sp.Matrix(g_inv).diff(coords[mu])
            self._dg_inv_funcs.append(sp.lambdify(coords, dg, modules="numpy"))

    # ------------------------------------------------------------
    # Hamiltonian and equations of motion
    # ------------------------------------------------------------

    def _g_inv(self, x: np.ndarray) -> np.ndarray:
        out = np.asarray(self._g_inv_func(*x), dtype=float)
        if out.shape != (4, 4):
            out = out.reshape(4, 4)
        return out

    def _dg_inv(self, mu: int, x: np.ndarray) -> np.ndarray:
        out = np.asarray(self._dg_inv_funcs[mu](*x), dtype=float)
        # If the derivative is identically zero, lambdify may return a
        # scalar 0; promote to a 4x4 zero matrix.
        if out.ndim == 0:
            return np.zeros((4, 4))
        if out.shape != (4, 4):
            out = out.reshape(4, 4)
        return out

    def hamiltonian(self, state: GeodesicState) -> float:
        r"""Return :math:`H = \tfrac{1}{2} g^{\mu\nu}(x) p_\mu p_\nu`.

        For a particle of rest mass :math:`\mu` this equals
        :math:`-\mu^2/2`; for a photon it is zero.  Conserved along
        any geodesic.
        """
        g_inv = self._g_inv(state.x)
        return 0.5 * float(state.p @ g_inv @ state.p)

    def velocity(self, state: GeodesicState) -> np.ndarray:
        r"""Return :math:`u^\mu = dx^\mu/d\lambda = g^{\mu\nu} p_\nu`."""
        return self._g_inv(state.x) @ state.p

    def force(self, state: GeodesicState) -> np.ndarray:
        r"""Return :math:`dp_\mu / d\lambda = -\tfrac{1}{2}\,\partial_\mu g^{\alpha\beta}\, p_\alpha p_\beta`."""
        f = np.zeros(4)
        for mu in range(4):
            dg = self._dg_inv(mu, state.x)
            f[mu] = -0.5 * float(state.p @ dg @ state.p)
        return f

    # ------------------------------------------------------------
    # Implicit-midpoint step
    # ------------------------------------------------------------

    def step(self, state: GeodesicState, h: float) -> GeodesicState:
        r"""Take a single implicit-midpoint step of size ``h``.

        Solves the implicit system

        .. math::

            x_{n+1} &= x_n + h\, \dot x(\bar x, \bar p), \\
            p_{n+1} &= p_n + h\, \dot p(\bar x, \bar p),

        with :math:`\bar x = (x_n + x_{n+1})/2`,
        :math:`\bar p = (p_n + p_{n+1})/2` via
        :func:`scipy.optimize.fsolve`.
        """
        from scipy.optimize import fsolve

        def residual(z: np.ndarray) -> np.ndarray:
            x_new = z[:4]
            p_new = z[4:]
            mid = GeodesicState(
                x=0.5 * (state.x + x_new),
                p=0.5 * (state.p + p_new),
            )
            v = self.velocity(mid)
            f = self.force(mid)
            res_x = x_new - state.x - h * v
            res_p = p_new - state.p - h * f
            return np.concatenate([res_x, res_p])

        # Initial guess: explicit Euler.  This is only the *seed* for
        # the implicit solve; the symplectic property of the final
        # answer comes from the implicit-midpoint structure.
        v0 = self.velocity(state)
        f0 = self.force(state)
        z0 = np.concatenate([state.x + h * v0, state.p + h * f0])

        z_new = fsolve(residual, z0, xtol=self.rtol, maxfev=self.max_iter * 16)
        return GeodesicState(x=z_new[:4], p=z_new[4:])

    # ------------------------------------------------------------
    # Convenience: integrate many steps
    # ------------------------------------------------------------

    def integrate(
        self,
        state0: GeodesicState,
        h: float,
        n_steps: int,
    ) -> list[GeodesicState]:
        r"""Integrate from :math:`\lambda = 0` to :math:`\lambda = n h`.

        Returns the list of states ``[state0, state_1, ..., state_n]``
        of length ``n_steps + 1``.

        For long integrations or large state spaces, callers may
        prefer to drive :meth:`step` directly and accumulate only the
        observables they care about, to avoid storing every
        intermediate state in memory.
        """
        if n_steps < 0:
            raise ValueError(f"n_steps must be non-negative, got {n_steps}")
        states = [state0.copy()]
        current = state0.copy()
        for _ in range(n_steps):
            current = self.step(current, h)
            states.append(current)
        return states
