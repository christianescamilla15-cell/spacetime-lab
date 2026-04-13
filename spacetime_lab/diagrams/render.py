r"""Renderers for :class:`~spacetime_lab.diagrams.Scene` objects.

Three backends:

- :func:`render_svg` — pure-string SVG renderer with no runtime
  dependency.  Intended for the web frontend and for embedding in
  README / blog posts.  **Implemented in v1.5.**
- :func:`render_tikz` — pure-string TikZ / pgf source generator for
  inclusion in LaTeX papers.  No runtime dependency.
  **Implemented in v1.5.**
- :func:`render_matplotlib` — matplotlib backend for the Jupyter
  notebooks and for Python users who want to compose diagrams with
  other plots.  Shipped in Phase 2.

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

Style mapping (shared across renderers)
=======================================

Every backend uses the same kind-to-style defaults so the three
renderers produce visually consistent diagrams from the same Scene:

==============  =============  =============  ========
``kind``        Stroke         Width (pt)     Dash
==============  =============  =============  ========
boundary        ``#000000``    1.6            solid
horizon         ``#444444``    1.1            ``--``
singularity     ``#b30000``    1.8            short ``--``
lightcone       ``#1a9a4a``    1.2            solid
world_line      ``#c64a0b``    1.6            solid
guide           ``#888888``    1.0            ``..``
==============  =============  =============  ========

A path's :class:`~spacetime_lab.diagrams.PathStyle` overrides the
stroke and width but not the dash pattern; the dash is determined
by ``kind`` so that horizons stay dashed regardless of colour
choice.

The five canonical infinity symbols
:math:`\{i^{+}, i^{-}, i^{0}, \mathscr{I}^{+}, \mathscr{I}^{-}\}`
are rendered as LaTeX math by all backends (SVG uses the literal
glyphs ``ℐ`` since arbitrary LaTeX is not portable to SVG; TikZ and
matplotlib use ``\mathscr{I}``).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # Only imported at type-check time to avoid a matplotlib dependency
    # for SVG / TikZ consumers.
    import matplotlib.axes

    from spacetime_lab.diagrams.penrose import (
        Infinity,
        Path,
        Scene,
    )


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


# ----------------------------------------------------------------------
# Style mapping shared between the SVG and TikZ backends
# ----------------------------------------------------------------------


# (stroke, width-points, dasharray-svg-string-or-None, tikz-style-keyword)
_KIND_STYLE_SVG: dict[str, tuple[str, float, str | None]] = {
    "boundary":    ("#000000", 1.6, None),
    "horizon":     ("#444444", 1.1, "6 4"),
    "singularity": ("#b30000", 1.8, "3 3"),
    "lightcone":   ("#1a9a4a", 1.2, None),
    "world_line":  ("#c64a0b", 1.6, None),
    "guide":       ("#888888", 1.0, "1 3"),
}

_KIND_STYLE_TIKZ: dict[str, tuple[str, float, str]] = {
    "boundary":    ("black",        1.6, "solid"),
    "horizon":     ("black!70",     1.1, "dashed"),
    "singularity": ("red!75!black", 1.8, "densely dashed"),
    "lightcone":   ("green!50!black", 1.2, "solid"),
    "world_line":  ("orange!85!black", 1.6, "solid"),
    "guide":       ("black!50",     1.0, "dotted"),
}

# z-order for grouping output: boundaries first (under), light cones last (over)
_DRAW_ORDER: tuple[str, ...] = (
    "boundary",
    "horizon",
    "singularity",
    "world_line",
    "lightcone",
    "guide",
)

# SVG-portable infinity glyphs.  SVG cannot render arbitrary LaTeX, so we
# use the Unicode script-I (U+2110) for scri and a plus/minus/zero
# superscript, plus a plain "i" with sup for the timelike/spatial
# infinities.  Browsers render these in the document font.
_INFINITY_SVG: dict[str, str] = {
    "i+":   "<tspan font-style='italic'>i</tspan><tspan baseline-shift='super' font-size='0.75em'>+</tspan>",
    "i-":   "<tspan font-style='italic'>i</tspan><tspan baseline-shift='super' font-size='0.75em'>-</tspan>",
    "i0":   "<tspan font-style='italic'>i</tspan><tspan baseline-shift='super' font-size='0.75em'>0</tspan>",
    "scri+": "<tspan font-style='italic'>&#x2110;</tspan><tspan baseline-shift='super' font-size='0.75em'>+</tspan>",
    "scri-": "<tspan font-style='italic'>&#x2110;</tspan><tspan baseline-shift='super' font-size='0.75em'>-</tspan>",
}

_INFINITY_TIKZ: dict[str, str] = {
    "i+":    r"$i^{+}$",
    "i-":    r"$i^{-}$",
    "i0":    r"$i^{0}$",
    "scri+": r"$\mathscr{I}^{+}$",
    "scri-": r"$\mathscr{I}^{-}$",
}


def render_svg(
    scene: "Scene",
    *,
    width: int = 480,
    height: int = 480,
    padding: int = 24,
    show_labels: bool = True,
    label_offset: float = 0.10,
) -> str:
    r"""Render a :class:`Scene` as a standalone SVG string.

    Pure-string renderer with no runtime dependency.  Output is a
    complete ``<svg>...</svg>`` document suitable for writing to a
    ``.svg`` file or embedding directly in HTML or Markdown.

    Parameters
    ----------
    scene : Scene
        The scene produced by a :meth:`PenroseChart.to_scene` call.
    width, height : int
        Canvas size in pixels.  Default ``480 x 480``.
    padding : int
        Empty margin around the diagram content in pixels.
    show_labels : bool
        If ``True`` (default), render an SVG ``<text>`` for each
        named infinity using the styled glyph map.
    label_offset : float
        Radial push applied to infinity labels in :math:`(T, X)` units
        so they do not overlap the boundary lines.

    Returns
    -------
    str
        A complete ``<svg>...</svg>`` document.

    Notes
    -----
    Paths are grouped into ``<g class="kind-{kind}">`` elements so the
    consumer (frontend CSS, downstream HTML) can restyle entire
    categories without parsing individual ``<path>`` attributes.
    """
    from math import isfinite

    if width <= 0 or height <= 0:
        raise ValueError(
            f"width and height must be positive, got {width}x{height}"
        )
    if padding < 0:
        raise ValueError(f"padding must be non-negative, got {padding}")

    # 1. Compute rotated (T, X) for every scene point.
    rotated_paths: list[tuple[str, list[tuple[float, float]], "Path"]] = []
    all_T: list[float] = []
    all_X: list[float] = []
    for path in scene.paths:
        pts: list[tuple[float, float]] = []
        for vec in path.points:
            T, X = _rotate_uv_to_tx(vec.U, vec.V)
            pts.append((T, X))
            all_T.append(T)
            all_X.append(X)
        rotated_paths.append((path.kind, pts, path))

    rotated_infinities: list[tuple["Infinity", float, float]] = []
    for inf in scene.infinities:
        T, X = _rotate_uv_to_tx(inf.position.U, inf.position.V)
        rotated_infinities.append((inf, T, X))
        all_T.append(T)
        all_X.append(X)

    # 2. Bounding box and world-to-pixel transform.
    if not all_T:
        # Empty scene: emit a placeholder canvas, do not error.
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
            f"<title>{_xml_escape(scene.name)}</title></svg>"
        )

    T_min, T_max = min(all_T), max(all_T)
    X_min, X_max = min(all_X), max(all_X)
    pad_world = 0.05 * max(T_max - T_min, X_max - X_min, 1e-9)
    T_min -= pad_world
    T_max += pad_world
    X_min -= pad_world
    X_max += pad_world

    inner_w = max(1, width - 2 * padding)
    inner_h = max(1, height - 2 * padding)
    span_X = max(X_max - X_min, 1e-9)
    span_T = max(T_max - T_min, 1e-9)
    scale = min(inner_w / span_X, inner_h / span_T)
    # Centre the diagram in the canvas.
    plot_w = scale * span_X
    plot_h = scale * span_T
    x_off = padding + (inner_w - plot_w) / 2.0
    y_off = padding + (inner_h - plot_h) / 2.0

    def to_px(T: float, X: float) -> tuple[float, float]:
        # SVG y axis points downward; physical T runs upward.
        px_x = x_off + (X - X_min) * scale
        px_y = y_off + (T_max - T) * scale
        return px_x, px_y

    # 3. Build SVG body.
    body: list[str] = []
    body.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )
    body.append(f"  <title>{_xml_escape(scene.name)}</title>")
    body.append('  <rect width="100%" height="100%" fill="white" />')

    # Group paths by kind in z-order.
    paths_by_kind: dict[str, list[tuple[str, list[tuple[float, float]], "Path"]]] = {
        k: [] for k in _DRAW_ORDER
    }
    for entry in rotated_paths:
        paths_by_kind.setdefault(entry[0], []).append(entry)

    for kind in _DRAW_ORDER:
        entries = paths_by_kind.get(kind, [])
        if not entries:
            continue
        default_stroke, default_width, dasharray = _KIND_STYLE_SVG.get(
            kind, ("#333333", 1.0, None)
        )
        body.append(f'  <g class="kind-{_xml_escape(kind)}" fill="none">')
        for _, pts, path in entries:
            pts_px = [to_px(T, X) for (T, X) in pts]
            if not all(isfinite(x) and isfinite(y) for (x, y) in pts_px):
                continue
            d_attr = " ".join(
                f"{cmd}{px:.3f},{py:.3f}"
                for (cmd, (px, py)) in zip(
                    ["M "] + ["L "] * (len(pts_px) - 1), pts_px
                )
            )
            stroke = path.style.stroke if path.style.stroke else default_stroke
            stroke_w = path.style.width if path.style.width else default_width
            attrs = [f'd="{d_attr}"', f'stroke="{stroke}"',
                     f'stroke-width="{stroke_w:g}"',
                     'stroke-linecap="round"', 'stroke-linejoin="round"']
            if dasharray:
                attrs.append(f'stroke-dasharray="{dasharray}"')
            body.append("    <path " + " ".join(attrs) + " />")
        body.append("  </g>")

    # 4. Infinity labels.
    if show_labels and rotated_infinities:
        body.append('  <g class="infinities" font-family="serif" font-size="14">')
        for inf, T, X in rotated_infinities:
            r = (T * T + X * X) ** 0.5
            if r > 1e-9:
                dT = T / r * label_offset
                dX = X / r * label_offset
            else:
                dT = dX = 0.0
            tx, ty = to_px(T + dT, X + dX)
            glyph = _INFINITY_SVG.get(
                inf.symbol, _xml_escape(inf.symbol)
            )
            body.append(
                f'    <text x="{tx:.2f}" y="{ty:.2f}" '
                f'text-anchor="middle" dominant-baseline="middle">'
                f"{glyph}</text>"
            )
        body.append("  </g>")

    body.append("</svg>")
    return "\n".join(body)


def _xml_escape(text: str) -> str:
    """Escape ``& < > " '`` for safe inclusion in SVG attributes/text."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


# ----------------------------------------------------------------------
# TikZ renderer
# ----------------------------------------------------------------------


def render_tikz(
    scene: "Scene",
    *,
    scale: float = 3.0,
    show_labels: bool = True,
    label_offset: float = 0.10,
    standalone: bool = False,
) -> str:
    r"""Render a :class:`Scene` as a TikZ / pgf LaTeX source snippet.

    Pure-string renderer with no runtime dependency.  Output is
    ready to paste into a LaTeX document that loads
    ``\usepackage{tikz}`` (and ``\usepackage{mathrsfs}`` if the
    ``\mathscr{I}`` glyph is desired with the standard formatting).

    Parameters
    ----------
    scene : Scene
        The scene produced by a :meth:`PenroseChart.to_scene` call.
    scale : float
        TikZ ``scale`` option applied to the whole picture.  The
        diagram content is in compactified null coordinates living in
        :math:`[-\pi/2, \pi/2]^2`, so a ``scale`` of about 3 gives
        a diagram roughly the width of a textbook column.
    show_labels : bool
        If ``True`` (default), emit a ``\node`` per named infinity
        with the LaTeX symbol.
    label_offset : float
        Radial push applied to infinity labels in :math:`(T, X)` units
        so they do not overlap the boundary lines.
    standalone : bool
        If ``True``, wrap the ``tikzpicture`` in a ``standalone``
        document preamble so the output can be compiled directly with
        ``pdflatex``.  Default ``False``.

    Returns
    -------
    str
        A LaTeX source snippet (or full standalone document when
        ``standalone=True``).

    Notes
    -----
    Infinity tags map as
    ``"scri+" -> \mathscr{I}^{+}``,
    ``"scri-" -> \mathscr{I}^{-}``,
    ``"i+"    -> i^{+}``,
    ``"i-"    -> i^{-}``,
    ``"i0"    -> i^{0}``.
    """
    if scale <= 0:
        raise ValueError(f"scale must be positive, got {scale}")

    body: list[str] = []
    if standalone:
        body.append(r"\documentclass[tikz,border=4pt]{standalone}")
        body.append(r"\usepackage{mathrsfs}")
        body.append(r"\usepackage{tikz}")
        body.append(r"\begin{document}")

    body.append(rf"\begin{{tikzpicture}}[scale={scale:g}, "
                r"line cap=round, line join=round]")
    body.append(rf"  % {scene.name}")

    # Group paths by kind in z-order.
    paths_by_kind: dict[str, list["Path"]] = {k: [] for k in _DRAW_ORDER}
    for p in scene.paths:
        paths_by_kind.setdefault(p.kind, []).append(p)

    for kind in _DRAW_ORDER:
        entries = paths_by_kind.get(kind, [])
        if not entries:
            continue
        default_color, default_width, default_dash = _KIND_STYLE_TIKZ.get(
            kind, ("black", 1.0, "solid")
        )
        body.append(f"  % --- {kind} ---")
        for path in entries:
            color = path.style.stroke if path.style.stroke else default_color
            # Convert hex colours from PathStyle to a TikZ-compatible form.
            color_tikz = _hex_to_tikz(color, default_color)
            width = path.style.width if path.style.width else default_width
            # TikZ line widths are usually given as named (thin/thick)
            # but we use explicit pt values to match the SVG/matplotlib
            # backends bit-for-bit.
            opts = [color_tikz, default_dash, f"line width={width:.2f}pt"]
            opts_str = ", ".join(opts)
            tx_pts = [_rotate_uv_to_tx(v.U, v.V) for v in path.points]
            # TikZ expects (X, T) order so X is horizontal and T vertical.
            coord_str = " -- ".join(
                f"({X:.4f},{T:.4f})" for (T, X) in tx_pts
            )
            body.append(f"  \\draw[{opts_str}] {coord_str};")

    if show_labels and scene.infinities:
        body.append("  % --- infinities ---")
        for inf in scene.infinities:
            T, X = _rotate_uv_to_tx(inf.position.U, inf.position.V)
            r = (T * T + X * X) ** 0.5
            if r > 1e-9:
                dT = T / r * label_offset
                dX = X / r * label_offset
            else:
                dT = dX = 0.0
            label = _INFINITY_TIKZ.get(inf.symbol, inf.symbol)
            body.append(
                f"  \\node at ({X + dX:.4f},{T + dT:.4f}) {{{label}}};"
            )

    body.append(r"\end{tikzpicture}")
    if standalone:
        body.append(r"\end{document}")

    return "\n".join(body)


def _hex_to_tikz(color: str, default: str) -> str:
    """Translate a hex / named colour into a TikZ-friendly token.

    TikZ understands named colours from the ``xcolor`` package
    (``black``, ``red!75!black``, ...) and also a literal HTML hex
    via ``color={HTML}{RRGGBB}``.  We use that latter form when the
    input is a hex string, and fall back to ``default`` (already
    expressed as an xcolor token) otherwise.
    """
    if isinstance(color, str) and color.startswith("#") and len(color) == 7:
        return "color={rgb,255:" + (
            f"red,{int(color[1:3], 16)};"
            f"green,{int(color[3:5], 16)};"
            f"blue,{int(color[5:7], 16)}"
        ) + "}"
    if not color:
        return default
    return color


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
