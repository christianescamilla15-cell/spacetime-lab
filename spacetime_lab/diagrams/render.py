r"""Renderers for :class:`~spacetime_lab.diagrams.Scene` objects.

Three backends are planned for Phase 2:

- :func:`render_svg` — a pure-string SVG renderer with no runtime
  dependency.  Intended for the web frontend and for embedding in
  README / blog posts.
- :func:`render_tikz` — a pure-string TikZ / pgf source generator for
  inclusion in LaTeX papers.  No runtime dependency.
- :func:`render_matplotlib` — a matplotlib backend for the Jupyter
  notebooks and for Python users who want to compose diagrams with
  other plots.

All three consume the same chart-agnostic
:class:`~spacetime_lab.diagrams.Scene` data structure produced by
:meth:`~spacetime_lab.diagrams.PenroseChart.to_scene`.

Coordinate convention
=====================

Scenes store paths in compactified **null** coordinates :math:`(U, V)`.
The renderers rotate them into the more familiar :math:`(T, X)` frame
via

.. math::

    T = (U + V) / \sqrt{2}, \qquad X = (V - U) / \sqrt{2},

so that the final image has time running upwards and space running to
the right, with light cones at 45 degrees.  Individual renderers may
additionally clip, pad or rescale to fit the output canvas.

Stub status
===========

This module is a stub.  Every renderer currently raises
:class:`NotImplementedError` with a clear TODO message.  The Phase 2
coding pass will implement them one at a time, each with its own unit
tests verifying that the output contains the expected number of paths,
labels, and infinities.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # Only imported at type-check time to avoid a matplotlib dependency
    # for SVG / TikZ consumers.
    import matplotlib.axes

    from spacetime_lab.diagrams.penrose import Scene


# ----------------------------------------------------------------------
# Helper used by all three renderers once they exist
# ----------------------------------------------------------------------


def _rotate_uv_to_tx(U: float, V: float) -> tuple[float, float]:
    r"""Rotate a single :math:`(U, V)` point into :math:`(T, X)` frame.

    Applies

    .. math::

        T = \frac{U + V}{\sqrt{2}}, \qquad X = \frac{V - U}{\sqrt{2}},

    so that the resulting :math:`T` axis runs vertically and :math:`X`
    horizontally, matching the conventional orientation of textbook
    Penrose diagrams.

    Parameters
    ----------
    U, V : float
        Compactified null coordinates.

    Returns
    -------
    tuple[float, float]
        The rotated ``(T, X)`` coordinates.
    """
    from math import sqrt

    inv_sqrt2 = 1.0 / sqrt(2.0)
    T = (U + V) * inv_sqrt2
    X = (V - U) * inv_sqrt2
    return T, X


# ----------------------------------------------------------------------
# SVG renderer
# ----------------------------------------------------------------------


def render_svg(
    scene: "Scene",
    *,
    width: int = 480,
    height: int = 480,
    padding: int = 24,
) -> str:
    """Render a :class:`Scene` as an SVG string.

    Parameters
    ----------
    scene : Scene
        The scene produced by a :meth:`PenroseChart.to_scene` call.
    width, height : int
        Canvas size in pixels.  Default ``480 x 480``.
    padding : int
        Empty margin around the diagram content in pixels.

    Returns
    -------
    str
        A complete, standalone ``<svg>...</svg>`` document that can be
        written to a file or embedded directly in HTML.

    Notes
    -----
    The implementation will:

    1. Rotate every :class:`Vec2` in the scene from :math:`(U, V)` to
       :math:`(T, X)` using :func:`_rotate_uv_to_tx`.
    2. Compute a bounding box of the rotated points and derive a
       world-to-pixel transform with the requested padding.
    3. Emit ``<path>`` elements for every :class:`~spacetime_lab.diagrams.Path`
       in the scene, grouping by :attr:`Path.kind` so the CSS in the
       frontend can restyle them cleanly.
    4. Emit ``<text>`` elements for each :class:`Infinity`.

    Raises
    ------
    NotImplementedError
        Stub.
    """
    raise NotImplementedError(
        "render_svg: Phase 2 coding pass will implement. "
        "Start from the boundary paths, then add horizons, "
        "singularities, light cones, and finally infinity labels."
    )


# ----------------------------------------------------------------------
# TikZ renderer
# ----------------------------------------------------------------------


def render_tikz(
    scene: "Scene",
    *,
    scale: float = 3.0,
) -> str:
    r"""Render a :class:`Scene` as a TikZ / pgf LaTeX source snippet.

    Parameters
    ----------
    scene : Scene
        The scene produced by a :meth:`PenroseChart.to_scene` call.
    scale : float
        TikZ ``scale`` option applied to the whole picture.  The
        diagram content is in compactified null coordinates which live
        in :math:`[-\pi/2, \pi/2]^2`, so a ``scale`` of about 3 gives
        a diagram roughly the width of a textbook column.

    Returns
    -------
    str
        A LaTeX source snippet starting with ``\begin{tikzpicture}`` and
        ending with ``\end{tikzpicture}``, ready to paste into a
        document that has ``\usepackage{tikz}``.

    Notes
    -----
    Infinity symbols are emitted as LaTeX math, mapping the scene's
    ``"scri+"``/``"scri-"``/``"i+"``/``"i-"``/``"i0"`` tags to
    ``\mathscr{I}^{+}``, ``\mathscr{I}^{-}``, ``i^{+}``, ``i^{-}``,
    ``i^{0}`` respectively.

    Raises
    ------
    NotImplementedError
        Stub.
    """
    raise NotImplementedError(
        "render_tikz: Phase 2 coding pass will implement. "
        "Map Path.kind to standard TikZ styles (boundary, horizon=dashed, "
        "singularity=decorate/snake, world_line=thick), then emit a "
        "tikzpicture environment."
    )


# ----------------------------------------------------------------------
# Matplotlib renderer
# ----------------------------------------------------------------------


def render_matplotlib(
    scene: "Scene",
    ax: "matplotlib.axes.Axes | None" = None,
    **plot_kwargs: Any,
) -> "matplotlib.axes.Axes":
    """Render a :class:`Scene` onto a matplotlib Axes.

    Parameters
    ----------
    scene : Scene
        The scene produced by a :meth:`PenroseChart.to_scene` call.
    ax : matplotlib.axes.Axes, optional
        An existing Axes to draw onto.  If ``None`` a new figure and
        Axes are created.
    **plot_kwargs
        Extra keyword arguments forwarded to every ``ax.plot`` call
        (e.g. ``alpha=0.8``).  Individual paths override these with
        their own :class:`PathStyle` settings when appropriate.

    Returns
    -------
    matplotlib.axes.Axes
        The Axes onto which the diagram was drawn.

    Notes
    -----
    The matplotlib renderer is the most forgiving of the three and is
    intended for Jupyter notebooks.  The Phase 2 coding pass will:

    1. Import matplotlib lazily (only when this function is called).
    2. Create or reuse an Axes.
    3. Rotate every scene point into :math:`(T, X)` via
       :func:`_rotate_uv_to_tx`.
    4. Group paths by :attr:`Path.kind` and draw them with a sensible
       default style per kind (solid for boundaries, dashed for
       horizons, zig-zag for singularities, thick for world lines).
    5. Place infinity labels using ``ax.annotate``.

    Raises
    ------
    NotImplementedError
        Stub.
    """
    raise NotImplementedError(
        "render_matplotlib: Phase 2 coding pass will implement. "
        "Keep the matplotlib import inside the function body so the "
        "module remains importable in environments without matplotlib."
    )
