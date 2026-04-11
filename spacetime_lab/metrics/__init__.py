"""Exact metric solutions for black hole spacetimes.

Provides a unified interface for computing metric tensors, Christoffel symbols,
curvature invariants, and physical quantities (horizons, ISCO, etc.) for a
library of exact solutions to the Einstein field equations.

Available metrics:
    Schwarzschild — static, spherically symmetric vacuum black hole
    (more coming in future phases)

Example:
    >>> from spacetime_lab.metrics import Schwarzschild
    >>> bh = Schwarzschild(mass=1.0)
    >>> bh.event_horizon()
    2.0
"""

from spacetime_lab.metrics.base import Metric
from spacetime_lab.metrics.schwarzschild import Schwarzschild

__all__ = [
    "Metric",
    "Schwarzschild",
]
