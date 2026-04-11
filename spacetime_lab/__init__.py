"""Spacetime Lab — Interactive platform for exploring black hole physics.

A Python package for general relativity, black hole physics, and holographic
entanglement entropy. Part of the Spacetime Lab unified platform.

Example:
    >>> from spacetime_lab.metrics import Schwarzschild
    >>> bh = Schwarzschild(mass=1.0)
    >>> print(bh.event_horizon())
    2.0

Modules:
    metrics: Exact solutions (Schwarzschild, Kerr, AdS, BTZ)
    diagrams: Penrose and embedding diagram generators
    geodesics: Geodesic integration in curved spacetime
    horizons: Horizon finders (event, apparent, ISCO, photon sphere)
    waves: Quasinormal modes and gravitational wave analysis
    entropy: Holographic entanglement entropy (RT/HRT surfaces)
    utils: Helpers, constants, plotting
"""

__version__ = "0.1.0"
__author__ = "Christian Hernández Escamilla"
__license__ = "MIT"

from spacetime_lab.metrics import Schwarzschild, Metric

__all__ = [
    "__version__",
    "Metric",
    "Schwarzschild",
]
