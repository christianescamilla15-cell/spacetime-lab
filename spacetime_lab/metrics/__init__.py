"""Exact metric solutions for black hole spacetimes.

Provides a unified interface for computing metric tensors, Christoffel symbols,
curvature invariants, and physical quantities (horizons, ISCO, etc.) for a
library of exact solutions to the Einstein field equations.

Available metrics:
    Schwarzschild — static, spherically symmetric vacuum black hole
    Kerr          — stationary, axisymmetric, rotating vacuum black hole

Example:
    >>> from spacetime_lab.metrics import Schwarzschild, Kerr
    >>> bh = Schwarzschild(mass=1.0)
    >>> bh.event_horizon()
    2.0
    >>> kerr = Kerr(mass=1.0, spin=0.5)
    >>> round(kerr.outer_horizon(), 6)
    1.866025
"""

from spacetime_lab.metrics.base import Metric
from spacetime_lab.metrics.kerr import Kerr
from spacetime_lab.metrics.schwarzschild import Schwarzschild

__all__ = [
    "Kerr",
    "Metric",
    "Schwarzschild",
]
