"""Penrose and embedding diagrams for Lorentzian spacetimes.

This submodule is the Phase 2 deliverable of the Spacetime Lab roadmap.
It provides:

- :class:`PenroseChart`: abstract base class for a conformally compactified
  2D "chart" of a spacetime.  Subclasses implement the forward and inverse
  maps between physical coordinates and compactified null coordinates
  ``(U, V)`` in the diamond ``[-pi/2, pi/2] x [-pi/2, pi/2]``, plus metadata
  (positions of infinities, singularity and horizon paths, etc.).
- :class:`MinkowskiPenrose`: the reference implementation — 2D Minkowski,
  trivial diamond, no horizons.  Serves as the canonical test target.
- :class:`SchwarzschildPenrose`: the first non-trivial case.  Four regions
  (exterior, interior, mirror exterior, white-hole interior) obtained via
  Eddington-Finkelstein -> Kruskal -> ``arctan`` of null Kruskal variables.

Rendering lives in :mod:`spacetime_lab.diagrams.render` and consumes
the chart-agnostic :class:`Scene` intermediate representation built by
:meth:`PenroseChart.to_scene`.

Typical usage (once implemented)::

    from spacetime_lab.diagrams import SchwarzschildPenrose
    from spacetime_lab.diagrams.render import render_svg

    chart = SchwarzschildPenrose(mass=1.0)
    scene = chart.to_scene()
    svg = render_svg(scene)
    open("schwarzschild_penrose.svg", "w").write(svg)

References
----------
- Hawking & Ellis, *The Large Scale Structure of Space-Time*, ch. 5
- Wald, *General Relativity*, ch. 11 and Appendix D
- Carroll, *Spacetime and Geometry*, ch. 5 (Schwarzschild Penrose
  diagram) and Appendix H (conformal diagrams)
"""
from __future__ import annotations

from spacetime_lab.diagrams.penrose import (
    Infinity,
    MinkowskiPenrose,
    Path,
    PathStyle,
    PenroseChart,
    SchwarzschildPenrose,
    Scene,
    Vec2,
)

__all__ = [
    "Infinity",
    "MinkowskiPenrose",
    "Path",
    "PathStyle",
    "PenroseChart",
    "SchwarzschildPenrose",
    "Scene",
    "Vec2",
]
