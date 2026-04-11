r"""Penrose diagram chart abstraction.

This module defines the core data types and abstract interface for
Penrose diagrams in Spacetime Lab.  See the package docstring of
:mod:`spacetime_lab.diagrams` for context.

Design notes
============

1. **Two coordinate systems per chart.**

   Every chart has a notion of *physical* coordinates (e.g. Schwarzschild
   :math:`(t, r)` on the equatorial slice, Minkowski :math:`(t, x)`, etc.)
   and *compactified null* coordinates :math:`(U, V)` which live in the
   finite diamond :math:`U, V \in [-\pi/2, \pi/2]`.

   The chart's fundamental responsibility is to provide the bijective
   map between the two, together with the information about which
   subset of the diamond is actually the image of the physical spacetime
   (the 'region' data).

2. **Null coordinates are the common currency.**

   Light cones in the Penrose diagram must be 45 degrees everywhere.
   The simplest way to guarantee this is to treat the compactified
   coordinates as null coordinates :math:`(U, V)`, so that ingoing rays
   are lines :math:`V = \text{const}` and outgoing rays are
   :math:`U = \text{const}`.  When rendering, we rotate to the 'usual'
   orientation via

   .. math::

       T = (U + V) / \sqrt{2}, \qquad X = (V - U) / \sqrt{2},

   so that :math:`T` points up and :math:`X` points right.  This rotation
   is done once, inside the renderers.

3. **Charts produce a :class:`Scene`, not pixels.**

   The chart assembles a chart-agnostic :class:`Scene` object (paths,
   markers, labels) in :math:`(U, V)` coordinates.  The renderers in
   :mod:`spacetime_lab.diagrams.render` consume that scene and emit
   SVG / TikZ / matplotlib output.  This keeps the physics and the
   graphics concerns fully separate and makes it cheap to add new
   output targets.

4. **Regions are tracked explicitly for multi-region spacetimes.**

   For Schwarzschild the diamond is carved into four regions by the two
   horizon null lines.  Rather than have a single monolithic
   ``physical_to_compact`` that 'knows' about all four, we require the
   caller to pass a ``region`` argument (an integer 1..4 following the
   standard Penrose numbering).  The chart exposes :attr:`regions` so
   the renderer can iterate over them.  Minkowski has a single region
   numbered 1.

5. **Stub status.**

   This module currently contains:

   - Fully implemented small dataclasses
     (:class:`Vec2`, :class:`PathStyle`, :class:`Path`, :class:`Infinity`,
     :class:`Scene`).
   - The abstract :class:`PenroseChart` interface.
   - Stub subclasses :class:`MinkowskiPenrose` and
     :class:`SchwarzschildPenrose` with docstrings but no numerical
     implementation yet.  Every non-trivial method raises
     :class:`NotImplementedError`.

   Implementation is the next coding task of Phase 2.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Sequence


# ======================================================================
# Small dataclasses — the wire format between charts and renderers
# ======================================================================


@dataclass(frozen=True)
class Vec2:
    """A 2D point in compactified null coordinates :math:`(U, V)`.

    Attributes
    ----------
    U, V : float
        Compactified null coordinates, both in :math:`[-\\pi/2, \\pi/2]`.
        :math:`U` is retarded, :math:`V` is advanced.
    """

    U: float
    V: float


@dataclass(frozen=True)
class PathStyle:
    """Visual style applied to a :class:`Path` by renderers.

    Purely cosmetic; renderers map these fields to backend-specific
    attributes (e.g. SVG ``stroke``, TikZ ``draw``).

    Attributes
    ----------
    stroke : str
        Any CSS / matplotlib / TikZ compatible colour string.
    width : float
        Stroke width in points.
    dash : tuple[float, ...] | None
        Optional dash pattern (on, off, on, off, ...).  ``None`` means solid.
    label : str | None
        Optional in-line label rendered near the midpoint of the path.
        LaTeX math-mode strings are allowed (the renderers wrap them
        in ``$...$`` where appropriate).
    """

    stroke: str = "#000000"
    width: float = 1.0
    dash: tuple[float, ...] | None = None
    label: str | None = None


@dataclass(frozen=True)
class Path:
    """An ordered polyline in compactified null coordinates.

    Paths are the basic drawable object.  Straight-line segments, jagged
    singularities, and mapped physical curves are all represented the
    same way: a sequence of :class:`Vec2` vertices plus style metadata.

    Attributes
    ----------
    points : tuple[Vec2, ...]
        Vertices of the polyline in order.  Must contain at least two
        points.
    style : PathStyle
        Visual style hints for the renderers.
    kind : str
        A semantic tag used by renderers to decide grouping and
        z-ordering.  Recognised values:

        - ``"boundary"`` — outer edge of the diamond
        - ``"horizon"`` — a null line separating regions
        - ``"singularity"`` — a spacelike or timelike curvature singularity
        - ``"lightcone"`` — one leg of a light cone at an event
        - ``"world_line"`` — a user-supplied physical curve (geodesic,
          observer, etc.)
        - ``"guide"`` — a reference helper (e.g. a constant-r hyperbola)
    """

    points: tuple[Vec2, ...]
    style: PathStyle = field(default_factory=PathStyle)
    kind: str = "world_line"

    def __post_init__(self) -> None:
        if len(self.points) < 2:
            raise ValueError("Path must contain at least two points")


@dataclass(frozen=True)
class Infinity:
    """A named boundary point / segment of the Penrose diagram.

    Attributes
    ----------
    symbol : str
        Canonical symbol, one of ``"i+"``, ``"i-"``, ``"i0"``,
        ``"scri+"``, ``"scri-"``.  Renderers translate these to LaTeX.
    position : Vec2
        Anchor position in :math:`(U, V)`.  For point infinities
        (:math:`i^\\pm, i^0`) this is the point itself.  For
        :math:`\\mathscr{I}^\\pm` it is a representative point on the edge
        where the label should attach; the geometry of the edge itself
        lives in the ``boundary`` paths of the scene.
    region : int
        Which region this infinity belongs to (1 for single-region
        charts like Minkowski; 1-4 for Schwarzschild).
    """

    symbol: str
    position: Vec2
    region: int = 1


@dataclass
class Scene:
    """Chart-agnostic intermediate representation of a Penrose diagram.

    A :class:`Scene` is produced by :meth:`PenroseChart.to_scene` and
    consumed by the renderers in :mod:`spacetime_lab.diagrams.render`.
    It has no dependency on any graphics library.

    Attributes
    ----------
    name : str
        Human-readable name of the chart (e.g. ``"Schwarzschild (M=1)"``).
    paths : list[Path]
        Every drawable polyline in the diagram.  The caller is expected
        to sort and group by :attr:`Path.kind` at render time.
    infinities : list[Infinity]
        Named boundary points / segments.
    metadata : dict[str, object]
        Free-form bag for chart-specific extras (number of regions,
        black hole mass, ...).  Renderers may ignore anything they do
        not understand.
    """

    name: str
    paths: list[Path] = field(default_factory=list)
    infinities: list[Infinity] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

    def add(self, path: Path) -> None:
        """Append a path to the scene.  Convenience for building code."""
        self.paths.append(path)

    def add_infinity(self, infinity: Infinity) -> None:
        """Append a named infinity to the scene."""
        self.infinities.append(infinity)


# ======================================================================
# Abstract chart
# ======================================================================


class PenroseChart(ABC):
    r"""Abstract base class for a conformally compactified 2D diagram.

    Concrete subclasses must implement the forward and inverse maps
    between physical coordinates and compactified null coordinates
    :math:`(U, V)`, and must supply the region data, infinities, and
    boundary paths that describe the global structure of the diagram.

    All charts share the same rendering pipeline via :meth:`to_scene`.
    """

    # ------------------------------------------------------------
    # Required metadata
    # ------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name (e.g. ``'Minkowski (1+1)'``)."""

    @property
    @abstractmethod
    def regions(self) -> tuple[int, ...]:
        """Tuple of region indices present in this chart.

        Minkowski: ``(1,)``.  Eternal Schwarzschild: ``(1, 2, 3, 4)``.
        Used by renderers to iterate over the pieces of the diagram.
        """

    @property
    @abstractmethod
    def physical_coordinate_names(self) -> tuple[str, ...]:
        """Names of the physical coordinates this chart accepts.

        For 2D diagrams these are typically ``('t', 'x')`` or
        ``('t', 'r')``.  Used for nicer error messages when a caller
        passes the wrong kwargs to :meth:`physical_to_compact`.
        """

    # ------------------------------------------------------------
    # Forward and inverse coordinate maps
    # ------------------------------------------------------------

    @abstractmethod
    def physical_to_compact(self, region: int, **coords: float) -> Vec2:
        r"""Map a physical event to compactified null coordinates.

        Parameters
        ----------
        region : int
            Which region of the chart this event lives in.  Must be
            one of :attr:`regions`.  For single-region charts simply
            pass ``region=1``.
        **coords : float
            Physical coordinates of the event, matching
            :attr:`physical_coordinate_names`.

        Returns
        -------
        Vec2
            The corresponding compactified null coordinates
            :math:`(U, V)` in :math:`[-\pi/2, \pi/2]^2`.

        Raises
        ------
        ValueError
            If ``region`` is not in :attr:`regions`, or the physical
            coordinates are outside the valid domain for that region
            (e.g. :math:`r \le 2M` with ``region=1`` in Schwarzschild).
        """

    @abstractmethod
    def compact_to_physical(self, region: int, point: Vec2) -> dict[str, float]:
        """Inverse of :meth:`physical_to_compact`.

        Parameters
        ----------
        region : int
            Which region of the chart the point belongs to.
        point : Vec2
            A point in compactified null coordinates.

        Returns
        -------
        dict[str, float]
            Physical coordinates keyed by name, matching
            :attr:`physical_coordinate_names`.

        Notes
        -----
        This inverse is primarily used for interactive diagrams where
        the user clicks a point on the rendered diagram and wants to
        know what physical event it represents.
        """

    # ------------------------------------------------------------
    # Global structure
    # ------------------------------------------------------------

    @abstractmethod
    def boundary_paths(self) -> list[Path]:
        """Return the boundary paths of the diagram.

        Includes every edge of every region: outer asymptotic edges
        (where :math:`\\mathscr{I}^\\pm` live), horizon null lines that
        separate regions, and singularity curves.  Each path is tagged
        via :attr:`Path.kind` so the renderer can style them
        differently.
        """

    @abstractmethod
    def infinities(self) -> list[Infinity]:
        """Return the named infinities of the diagram.

        For 2D Minkowski this is 5 entries (:math:`i^\\pm`, :math:`i^0`,
        :math:`\\mathscr{I}^\\pm`).  For eternal Schwarzschild it is more
        (each exterior region has its own set).
        """

    # ------------------------------------------------------------
    # Derived operations (concrete, built on the abstract primitives)
    # ------------------------------------------------------------

    def light_cone_at(
        self,
        region: int,
        length: float = 0.15,
        **coords: float,
    ) -> tuple[Path, Path]:
        r"""Return the two null rays forming the light cone at an event.

        In :math:`(U, V)` null coordinates, the future light cone is the
        union of the two rays :math:`U = U_0` and :math:`V = V_0`
        emanating in the ``+V`` and ``+U`` directions respectively.
        We return two short segments (length ``length`` in each
        coordinate) so the rendered light cone is a finite tick.

        Parameters
        ----------
        region : int
            The region in which the event lives.
        length : float
            How far (in :math:`(U, V)` units) to extend each ray.
            Default ``0.15``.
        **coords : float
            Physical coordinates of the event.

        Returns
        -------
        tuple[Path, Path]
            ``(future, past)`` light cone as two Path objects.  Each
            Path contains three vertices (past endpoint, vertex,
            future endpoint) so it renders as an ``X``.

        Notes
        -----
        This default implementation delegates to
        :meth:`physical_to_compact` and then constructs the rays
        directly.  Subclasses usually do not need to override it.
        """
        raise NotImplementedError(
            "PenroseChart.light_cone_at will be implemented in the "
            "Phase 2 coding pass — requires physical_to_compact to "
            "return a valid Vec2 first."
        )

    def map_curve(
        self,
        region: int,
        samples: Sequence[dict[str, float]],
    ) -> Path:
        """Map a physical world-line to the compactified diagram.

        Parameters
        ----------
        region : int
            The region in which the whole curve lives.  Curves that
            cross a horizon must be split by the caller and mapped
            piece by piece with the appropriate regions.
        samples : sequence of dict
            Each element is a dict of physical coordinates (keys match
            :attr:`physical_coordinate_names`).  They are mapped to
            :math:`(U, V)` in order and joined into a single polyline.

        Returns
        -------
        Path
            A ``kind='world_line'`` path suitable for adding to a
            :class:`Scene`.

        Notes
        -----
        This default implementation is a thin wrapper over
        :meth:`physical_to_compact` and does no resampling or clipping.
        """
        raise NotImplementedError(
            "PenroseChart.map_curve will be implemented alongside "
            "physical_to_compact in the Phase 2 coding pass."
        )

    # ------------------------------------------------------------
    # Scene assembly
    # ------------------------------------------------------------

    def to_scene(
        self,
        *,
        world_lines: Iterable[tuple[int, Sequence[dict[str, float]]]] = (),
        light_cones: Iterable[tuple[int, dict[str, float]]] = (),
    ) -> Scene:
        """Build a :class:`Scene` ready for rendering.

        Parameters
        ----------
        world_lines : iterable of (region, samples)
            Optional physical world-lines to overlay on the diagram.
            Each entry is ``(region, samples)`` with the same semantics
            as :meth:`map_curve`.
        light_cones : iterable of (region, coords)
            Optional light cones to draw at specific events.  Each
            entry is ``(region, coords_dict)``.

        Returns
        -------
        Scene
            A fully populated :class:`Scene` containing the boundary
            paths, infinities, user-supplied world lines, and light
            cones.  The scene is independent of any graphics backend.

        Notes
        -----
        Subclasses usually do not override this; the default
        implementation calls the abstract primitives in the right
        order.
        """
        raise NotImplementedError(
            "PenroseChart.to_scene will be implemented once the "
            "boundary_paths / infinities / physical_to_compact "
            "primitives have concrete implementations."
        )


# ======================================================================
# Concrete charts — STUBS ONLY (Phase 2 coding pass will implement)
# ======================================================================


class MinkowskiPenrose(PenroseChart):
    r"""Penrose diagram of 1+1 Minkowski spacetime.

    The canonical textbook example.  Flat metric
    :math:`ds^2 = -dt^2 + dx^2` in null coordinates :math:`u = t - x`,
    :math:`v = t + x` becomes :math:`-du\, dv`; compactifying with
    :math:`U = \arctan u`, :math:`V = \arctan v` and rescaling by
    :math:`\Omega = \cos U \cos V` gives the flat diamond
    :math:`U, V \in (-\pi/2, \pi/2)`.

    This chart has a single region, five named infinities
    (:math:`i^\pm`, :math:`i^0`, :math:`\mathscr{I}^\pm`), no
    horizons, and no singularities.  It serves as the simplest
    possible sanity check for the chart + renderer pipeline.

    Notes
    -----
    This is currently a stub.  The Phase 2 coding pass will implement:

    - ``physical_to_compact``: ``U = arctan(t - x)``, ``V = arctan(t + x)``.
    - ``compact_to_physical``: ``t = (tan V + tan U) / 2``,
      ``x = (tan V - tan U) / 2``.
    - ``boundary_paths``: the four edges of the diamond, tagged as
      ``kind='boundary'``.
    - ``infinities``: 5 entries at the 4 vertices + 2 edge midpoints
      (``scri+`` label attached to the upper-left edge,
      ``scri-`` to the lower-left edge in null-coordinate layout).
    """

    @property
    def name(self) -> str:
        return "Minkowski (1+1)"

    @property
    def regions(self) -> tuple[int, ...]:
        return (1,)

    @property
    def physical_coordinate_names(self) -> tuple[str, ...]:
        return ("t", "x")

    def physical_to_compact(self, region: int, **coords: float) -> Vec2:
        r"""Map ``(t, x)`` to ``(U, V) = (arctan(t - x), arctan(t + x))``.

        Raises
        ------
        NotImplementedError
            Stub — not yet implemented.
        """
        raise NotImplementedError("MinkowskiPenrose.physical_to_compact (stub)")

    def compact_to_physical(self, region: int, point: Vec2) -> dict[str, float]:
        """Inverse map for Minkowski.  Stub."""
        raise NotImplementedError("MinkowskiPenrose.compact_to_physical (stub)")

    def boundary_paths(self) -> list[Path]:
        """Four edges of the diamond.  Stub."""
        raise NotImplementedError("MinkowskiPenrose.boundary_paths (stub)")

    def infinities(self) -> list[Infinity]:
        """Five named infinities (i+, i-, i0, scri+, scri-).  Stub."""
        raise NotImplementedError("MinkowskiPenrose.infinities (stub)")


class SchwarzschildPenrose(PenroseChart):
    r"""Penrose diagram of the maximally extended Schwarzschild spacetime.

    Four regions separated by the future / past horizons :math:`T = \pm X`:

    - **Region I**: exterior universe, :math:`r > 2M`.  Hosts
      :math:`\mathscr{I}^\pm`, :math:`i^\pm`, :math:`i^0`.
    - **Region II**: black-hole interior, :math:`r < 2M`, bounded
      above by the **spacelike** future singularity :math:`r = 0`.
    - **Region III**: mirror exterior (a second asymptotically flat
      universe, causally disconnected from region I).
    - **Region IV**: white-hole interior, bounded below by the
      spacelike past singularity.

    Construction (to be implemented in the Phase 2 coding pass):

    1. Start from Schwarzschild :math:`(t, r)` and compute the tortoise
       coordinate ``r_star = r + 2M ln|r/(2M) - 1|`` via
       :meth:`spacetime_lab.metrics.Schwarzschild.tortoise_coordinate`.
    2. Form the Eddington-Finkelstein null coordinates
       :math:`u = t - r^*`, :math:`v = t + r^*`.
    3. Exponentiate to Kruskal null coordinates:
       :math:`U_K = -\exp(-u/4M)` in region I (sign flips in II/III/IV),
       :math:`V_K = +\exp(v/4M)`.
    4. Apply ``arctan`` to compactify:
       :math:`U = \arctan U_K`, :math:`V = \arctan V_K`.

    Singularity locus :math:`r = 0` corresponds to
    :math:`U V = +1` in Kruskal coordinates (pre-compactification),
    which maps to two spacelike curves
    :math:`\tan U \cdot \tan V = 1` in :math:`(U, V)` after ``arctan``.
    These are the jagged lines at the top and bottom of the diagram.

    Parameters
    ----------
    mass : float
        Black hole mass :math:`M` in geometric units.  Must be positive.
    """

    def __init__(self, mass: float) -> None:
        if mass <= 0:
            raise ValueError(f"mass must be positive, got {mass}")
        self.mass = mass

    @property
    def name(self) -> str:
        return f"Schwarzschild Penrose (M={self.mass})"

    @property
    def regions(self) -> tuple[int, ...]:
        return (1, 2, 3, 4)

    @property
    def physical_coordinate_names(self) -> tuple[str, ...]:
        return ("t", "r")

    # --- forward / inverse maps (Phase 2 coding pass) -------------

    def physical_to_compact(self, region: int, **coords: float) -> Vec2:
        r"""Map Schwarzschild :math:`(t, r)` to compactified :math:`(U, V)`.

        The implementation depends on which region the event lives in:

        - Region I (:math:`r > 2M`):
          :math:`U_K = -e^{-(t - r^*)/4M}, V_K = e^{(t + r^*)/4M}`.
        - Region II (:math:`0 < r < 2M`, future of horizon):
          :math:`U_K = +e^{-(t - r^*)/4M}, V_K = e^{(t + r^*)/4M}`.
        - Region III: mirror of region I under :math:`(U_K, V_K) \to (-U_K, -V_K)`.
        - Region IV: mirror of region II.

        Then :math:`U = \arctan U_K`, :math:`V = \arctan V_K`.

        Raises
        ------
        NotImplementedError
            Stub — not yet implemented.  The Phase 2 coding pass will
            use :meth:`spacetime_lab.metrics.Schwarzschild.tortoise_coordinate`
            to compute :math:`r^*`.
        """
        raise NotImplementedError(
            "SchwarzschildPenrose.physical_to_compact (stub)"
        )

    def compact_to_physical(self, region: int, point: Vec2) -> dict[str, float]:
        r"""Invert the Penrose compactification back to Schwarzschild :math:`(t, r)`.

        Recover :math:`(U_K, V_K)` via ``tan``, then use
        :math:`U_K V_K = (1 - r/(2M)) e^{r/(2M)}` to solve for
        :math:`r` (this is transcendental — use the Lambert :math:`W`
        function or a 1D root solver), and
        :math:`V_K / U_K = -\exp(t/(2M))` (sign depends on region) for
        :math:`t`.

        Raises
        ------
        NotImplementedError
            Stub.
        """
        raise NotImplementedError(
            "SchwarzschildPenrose.compact_to_physical (stub)"
        )

    # --- global structure (Phase 2 coding pass) -------------------

    def boundary_paths(self) -> list[Path]:
        """Return the outer boundary, horizons, and both singularities.

        Expected contents (after implementation):

        - Two asymptotic edges for region I (``scri+`` upper-right,
          ``scri-`` lower-right), ``kind='boundary'``.
        - Two asymptotic edges for region III (mirror on the left),
          ``kind='boundary'``.
        - Four horizon null lines separating the four regions,
          ``kind='horizon'``.
        - Two singularity curves (top and bottom), sampled from
          :math:`\\tan U \\cdot \\tan V = \\pm 1`, ``kind='singularity'``,
          with a dashed / jagged style to distinguish them from
          boundaries.

        Raises
        ------
        NotImplementedError
            Stub.
        """
        raise NotImplementedError("SchwarzschildPenrose.boundary_paths (stub)")

    def infinities(self) -> list[Infinity]:
        """Return the named infinities of the Schwarzschild diagram.

        Region I hosts :math:`i^+`, :math:`i^-`, :math:`i^0`,
        :math:`\\mathscr{I}^+`, :math:`\\mathscr{I}^-`.
        Region III hosts a mirror set.  Regions II and IV host none
        (they end at the spacelike singularity).

        Raises
        ------
        NotImplementedError
            Stub.
        """
        raise NotImplementedError("SchwarzschildPenrose.infinities (stub)")
