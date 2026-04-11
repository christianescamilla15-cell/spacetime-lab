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


_INFINITY_LATEX = {
    "i+": r"$i^{+}$",
    "i-": r"$i^{-}$",
    "i0": r"$i^{0}$",
    "scri+": r"$\mathscr{I}^{+}$",
    "scri-": r"$\mathscr{I}^{-}$",
}


def render_matplotlib(
    scene: "Scene",
    ax: "matplotlib.axes.Axes | None" = None,
    *,
    show_labels: bool = True,
    label_offset: float = 0.08,
    **plot_kwargs: Any,
) -> "matplotlib.axes.Axes":
    r"""Render a :class:`Scene` onto a matplotlib Axes.

    Parameters
    ----------
    scene : Scene
        The scene produced by a :meth:`PenroseChart.to_scene` call.
    ax : matplotlib.axes.Axes, optional
        An existing Axes to draw onto.  If ``None`` a new figure and
        Axes are created at a reasonable default size.
    show_labels : bool
        If ``True`` (default) place a LaTeX label at each named
        infinity.  Set to ``False`` to get a bare diagram.
    label_offset : float
        Radial push applied to infinity labels so they do not
        overlap the boundary lines.  In :math:`(T, X)` units.
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
    intended for Jupyter notebooks.  It rotates every scene point from
    :math:`(U, V)` null coordinates into the conventional
    :math:`(T, X)` orientation so light cones render at 45 degrees.
    """
    import matplotlib.pyplot as plt  # lazy import

    from spacetime_lab.diagrams.penrose import Path as _Path  # for isinstance

    if ax is None:
        _, ax = plt.subplots(figsize=(6, 6))

    def _to_tx(path: _Path) -> tuple[list[float], list[float]]:
        Ts: list[float] = []
        Xs: list[float] = []
        for pt in path.points:
            T, X = _rotate_uv_to_tx(pt.U, pt.V)
            Ts.append(T)
            Xs.append(X)
        return Ts, Xs

    # Group paths by kind so we can impose a consistent default style
    # per kind while still letting individual path styles override.
    kind_defaults = {
        "boundary":    dict(color="#000000", linewidth=1.6, linestyle="-"),
        "horizon":     dict(color="#444444", linewidth=1.1, linestyle="--"),
        "singularity": dict(color="#b30000", linewidth=1.8, linestyle=(0, (2, 2))),
        "lightcone":   dict(color="#1a9a4a", linewidth=1.2, linestyle="-"),
        "world_line":  dict(color="#c64a0b", linewidth=1.6, linestyle="-"),
        "guide":       dict(color="#888888", linewidth=1.0, linestyle=":"),
    }

    # Stable draw order: boundaries first (under everything), then
    # horizons, singularities, world lines, and finally light cones.
    draw_order = ["boundary", "horizon", "singularity", "world_line", "lightcone", "guide"]
    paths_by_kind: dict[str, list[_Path]] = {k: [] for k in draw_order}
    for p in scene.paths:
        paths_by_kind.setdefault(p.kind, []).append(p)

    for kind in draw_order:
        for path in paths_by_kind.get(kind, []):
            Ts, Xs = _to_tx(path)
            base = dict(kind_defaults.get(kind, dict(color="#333333", linewidth=1.0)))
            # The PathStyle can refine stroke/width; leave linestyle alone
            # so the kind-level default wins for dashes.
            base.update({"color": path.style.stroke})
            if path.style.width:
                base["linewidth"] = path.style.width
            base.update(plot_kwargs)
            ax.plot(Xs, Ts, **base)

    if show_labels:
        for inf in scene.infinities:
            T, X = _rotate_uv_to_tx(inf.position.U, inf.position.V)
            # Push the label radially outward from the diagram centre
            # so it does not overlap the boundary.
            import math as _math

            r = _math.hypot(T, X)
            if r > 1e-9:
                dx = X / r * label_offset
                dy = T / r * label_offset
            else:
                dx = dy = 0.0
            ax.annotate(
                _INFINITY_LATEX.get(inf.symbol, inf.symbol),
                xy=(X, T),
                xytext=(X + dx, T + dy),
                fontsize=13,
                ha="center",
                va="center",
            )

    ax.set_aspect("equal")
    ax.set_xlabel("X")
    ax.set_ylabel("T")
    ax.set_title(scene.name)
    # Let the data drive the limits, with a modest padding.
    all_T = []
    all_X = []
    for path in scene.paths:
        for pt in path.points:
            T, X = _rotate_uv_to_tx(pt.U, pt.V)
            all_T.append(T)
            all_X.append(X)
    if all_T:
        from math import pi

        pad = 0.2
        ax.set_xlim(min(all_X) - pad, max(all_X) + pad)
        ax.set_ylim(min(all_T) - pad, max(all_T) + pad)
        # Reduce visual clutter
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
    return ax
