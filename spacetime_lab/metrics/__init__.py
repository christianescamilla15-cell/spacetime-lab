"""Exact metric solutions for black hole and AdS spacetimes.

Provides a unified interface for computing metric tensors, Christoffel symbols,
curvature invariants, and physical quantities (horizons, ISCO, etc.) for a
library of exact solutions to the Einstein field equations.

Available metrics:
    Schwarzschild — static, spherically symmetric vacuum black hole
    Kerr          — stationary, axisymmetric, rotating vacuum black hole
    AdS           — anti-de Sitter spacetime in Poincare coordinates
                    (the bulk geometry of holographic AdS/CFT)
    BTZ           — non-rotating BTZ black hole in 2+1 dimensions
                    (the simplest known black hole; quotient of AdS_3)

Example:
    >>> from spacetime_lab.metrics import Schwarzschild, Kerr, AdS
    >>> bh = Schwarzschild(mass=1.0)
    >>> bh.event_horizon()
    2.0
    >>> kerr = Kerr(mass=1.0, spin=0.5)
    >>> round(kerr.outer_horizon(), 6)
    1.866025
    >>> ads = AdS(dimension=3, radius=1.0)
    >>> ads.expected_ricci_scalar()
    -6.0
"""

from spacetime_lab.metrics.ads import AdS
from spacetime_lab.metrics.base import Metric
from spacetime_lab.metrics.btz import BTZ
from spacetime_lab.metrics.kerr import Kerr
from spacetime_lab.metrics.kerr_newman import KerrNewman
from spacetime_lab.metrics.reissner_nordstrom import ReissnerNordstrom
from spacetime_lab.metrics.schwarzschild import Schwarzschild

__all__ = [
    "AdS",
    "BTZ",
    "Kerr",
    "KerrNewman",
    "Metric",
    "ReissnerNordstrom",
    "Schwarzschild",
]
