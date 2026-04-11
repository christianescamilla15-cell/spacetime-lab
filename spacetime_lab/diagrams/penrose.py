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
        vertex = self.physical_to_compact(region, **coords)
        # Future light cone: half-length along +U and +V respectively.
        future = Path(
            points=(
                Vec2(vertex.U + length, vertex.V),
                vertex,
                Vec2(vertex.U, vertex.V + length),
            ),
            style=PathStyle(stroke="#1a9a4a", width=1.2),
            kind="lightcone",
        )
        past = Path(
            points=(
                Vec2(vertex.U - length, vertex.V),
                vertex,
                Vec2(vertex.U, vertex.V - length),
            ),
            style=PathStyle(stroke="#1a9a4a", width=1.2, dash=(3.0, 2.0)),
            kind="lightcone",
        )
        return future, past

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
        if len(samples) < 2:
            raise ValueError("map_curve needs at least two samples")
        points = tuple(
            self.physical_to_compact(region, **sample) for sample in samples
        )
        return Path(
            points=points,
            style=PathStyle(stroke="#c64a0b", width=1.5),
            kind="world_line",
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
        scene = Scene(name=self.name)
        for path in self.boundary_paths():
            scene.add(path)
        for infinity in self.infinities():
            scene.add_infinity(infinity)
        for region, samples in world_lines:
            scene.add(self.map_curve(region, samples))
        for region, coords in light_cones:
            future, past = self.light_cone_at(region, **coords)
            scene.add(future)
            scene.add(past)
        scene.metadata["regions"] = list(self.regions)
        return scene


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

        Parameters
        ----------
        region : int
            Must equal 1 (Minkowski has a single region).
        **coords : float
            ``t`` and ``x`` — any finite real numbers.
        """
        import math

        if region != 1:
            raise ValueError(
                f"MinkowskiPenrose has only region 1, got region={region}"
            )
        missing = {"t", "x"} - coords.keys()
        if missing:
            raise ValueError(f"Missing physical coordinates: {sorted(missing)}")
        t = float(coords["t"])
        x = float(coords["x"])
        return Vec2(U=math.atan(t - x), V=math.atan(t + x))

    def compact_to_physical(self, region: int, point: Vec2) -> dict[str, float]:
        r"""Inverse map: :math:`t = (\tan V + \tan U)/2`, :math:`x = (\tan V - \tan U)/2`.

        Parameters
        ----------
        region : int
            Must equal 1.
        point : Vec2
            A point strictly inside :math:`(-\pi/2, \pi/2)^2` — the
            boundary maps to infinity and cannot be inverted.
        """
        import math

        if region != 1:
            raise ValueError(
                f"MinkowskiPenrose has only region 1, got region={region}"
            )
        half_pi = math.pi / 2
        if abs(point.U) >= half_pi or abs(point.V) >= half_pi:
            raise ValueError(
                "compact_to_physical is undefined on the boundary "
                f"(|U| or |V| >= pi/2). Got U={point.U}, V={point.V}"
            )
        u = math.tan(point.U)
        v = math.tan(point.V)
        return {"t": 0.5 * (v + u), "x": 0.5 * (v - u)}

    def boundary_paths(self) -> list[Path]:
        r"""Return the four edges of the Minkowski diamond.

        In compactified null coordinates :math:`(U, V)` the diamond is
        simply the square :math:`[-\pi/2, +\pi/2]^2`.  The four edges
        correspond, in order, to:

        - upper: :math:`V = +\pi/2` (future-null asymptote, hosts
          :math:`\mathscr{I}^+` when oriented in ``(T, X)``)
        - right: :math:`U = +\pi/2` (the other future-null asymptote)
        - lower: :math:`V = -\pi/2` (past-null asymptote)
        - left: :math:`U = -\pi/2` (past-null asymptote)

        Each edge is tagged ``kind='boundary'`` so renderers style
        them with the asymptotic boundary palette.
        """
        import math

        h = math.pi / 2
        style = PathStyle(stroke="#000000", width=1.5)
        return [
            Path(points=(Vec2(-h, h), Vec2(h, h)), style=style, kind="boundary"),
            Path(points=(Vec2(h, -h), Vec2(h, h)), style=style, kind="boundary"),
            Path(points=(Vec2(-h, -h), Vec2(h, -h)), style=style, kind="boundary"),
            Path(points=(Vec2(-h, -h), Vec2(-h, h)), style=style, kind="boundary"),
        ]

    def infinities(self) -> list[Infinity]:
        r"""Return the eight named infinities of the Minkowski diamond.

        A 1+1 Minkowski spacetime has ``x`` running over
        :math:`\mathbb{R}`, so spatial infinity splits into two
        distinct points (left and right), and each of :math:`\mathscr{I}^\pm`
        is a pair of disjoint null edges (one for right-moving, one for
        left-moving rays).  The four corners of the :math:`(U, V)`
        square and the midpoints of the four edges give:

        - :math:`i^+` at :math:`(+\pi/2, +\pi/2)` (top vertex of diamond)
        - :math:`i^-` at :math:`(-\pi/2, -\pi/2)` (bottom vertex)
        - :math:`i^0` (right) at :math:`(-\pi/2, +\pi/2)`
        - :math:`i^0` (left)  at :math:`(+\pi/2, -\pi/2)`
        - :math:`\mathscr{I}^+` upper-right midpoint at :math:`(-\pi/4, +\pi/2)`
        - :math:`\mathscr{I}^+` upper-left midpoint at :math:`(+\pi/2, +\pi/4)`
        - :math:`\mathscr{I}^-` lower-right midpoint at :math:`(-\pi/2, -\pi/4)`
        - :math:`\mathscr{I}^-` lower-left midpoint at :math:`(+\pi/4, -\pi/2)`

        All eight entries share ``region=1`` since Minkowski has a
        single region.
        """
        import math

        h = math.pi / 2
        q = math.pi / 4
        return [
            Infinity("i+", Vec2(h, h)),
            Infinity("i-", Vec2(-h, -h)),
            Infinity("i0", Vec2(-h, h)),    # right
            Infinity("i0", Vec2(h, -h)),    # left
            Infinity("scri+", Vec2(-q, h)),  # upper right
            Infinity("scri+", Vec2(h, q)),   # upper left
            Infinity("scri-", Vec2(-h, -q)), # lower right
            Infinity("scri-", Vec2(q, -h)),  # lower left
        ]


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

    # --- internal helpers ----------------------------------------

    def _radial_prefactor(self, region: int, r: float) -> float:
        r"""Return :math:`\sqrt{|r/(2M) - 1|}` with region-domain validation.

        Raises :class:`ValueError` if ``r`` is not strictly inside the
        admissible range for the given region (the horizon itself is
        not included).
        """
        import math

        M = self.mass
        if region in (1, 3):
            if r <= 2 * M:
                raise ValueError(
                    f"Region {region} requires r > 2M ({2 * M}), got r={r}"
                )
            return math.sqrt(r / (2 * M) - 1.0)
        if region in (2, 4):
            if not (0.0 < r < 2 * M):
                raise ValueError(
                    f"Region {region} requires 0 < r < 2M ({2 * M}), got r={r}"
                )
            return math.sqrt(1.0 - r / (2 * M))
        raise ValueError(
            f"SchwarzschildPenrose has regions 1-4, got region={region}"
        )

    # --- forward / inverse maps ----------------------------------

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

        Parameters
        ----------
        region : int
            One of 1 (exterior), 2 (BH interior), 3 (mirror exterior),
            4 (WH interior).
        **coords : float
            Must contain ``t`` and ``r``.  ``r`` must respect the
            strict inequality for its region (``r > 2M`` for I/III,
            ``0 < r < 2M`` for II/IV).

        Raises
        ------
        ValueError
            If ``region`` is not 1-4, if ``r`` is not in the allowed
            range for that region, or if required coordinates are
            missing.
        """
        import math

        missing = {"t", "r"} - coords.keys()
        if missing:
            raise ValueError(f"Missing physical coordinates: {sorted(missing)}")
        t = float(coords["t"])
        r = float(coords["r"])

        radial = self._radial_prefactor(region, r)
        # Signs of (U_K, V_K) by region (Carroll convention):
        #   Region I   (-,+)   Region II  (+,+)
        #   Region III (+,-)   Region IV  (-,-)
        signs = {1: (-1, +1), 2: (+1, +1), 3: (+1, -1), 4: (-1, -1)}
        sU, sV = signs[region]

        M = self.mass
        # Combined exponents: exp((r - t)/(4M)) for U_K, exp((r + t)/(4M))
        # for V_K.  This avoids the factor * exp overflow dance.
        inf = float("inf")

        def _safe_exp(arg: float) -> float:
            # math.exp overflows near 709.  Saturate explicitly.
            if arg > 700.0:
                return inf
            if arg < -700.0:
                return 0.0
            return math.exp(arg)

        expU = _safe_exp((r - t) / (4.0 * M))
        expV = _safe_exp((r + t) / (4.0 * M))
        # If radial == 0 (we never admit it here; strict inequalities) and
        # exp is inf, we'd get NaN — but that path is closed by the domain
        # checks in _radial_prefactor.  Plain multiplication suffices.
        U_K = sU * radial * expU
        V_K = sV * radial * expV
        return Vec2(U=math.atan(U_K), V=math.atan(V_K))

    def compact_to_physical(self, region: int, point: Vec2) -> dict[str, float]:
        r"""Invert the Penrose compactification back to Schwarzschild :math:`(t, r)`.

        Recover :math:`(U_K, V_K)` via :math:`\tan`, then use
        :math:`U_K V_K = (1 - r/(2M)) e^{r/(2M)}` to solve for :math:`r`
        via the principal branch :math:`W_0` of the Lambert function:

        .. math::

            \frac{r}{2M} = 1 + W_0\!\left(-\frac{U_K V_K}{e}\right).

        The coordinate :math:`t` is then :math:`t = 2M \ln|V_K / U_K|`
        (valid in every region up to an overall sign that is fixed by
        ``region``).

        Parameters
        ----------
        region : int
            Which region of the chart the point belongs to (1-4).
        point : Vec2
            Strictly inside its region (not on a horizon or at
            infinity) — :math:`|U|, |V| < \pi/2` and the region sign
            constraints must hold.
        """
        import cmath
        import math

        from scipy.special import lambertw

        half_pi = math.pi / 2
        if abs(point.U) >= half_pi or abs(point.V) >= half_pi:
            raise ValueError(
                "compact_to_physical undefined on the boundary "
                f"(|U|, |V| < pi/2 required). Got U={point.U}, V={point.V}"
            )

        U_K = math.tan(point.U)
        V_K = math.tan(point.V)

        # Check the region sign constraints before inverting.
        signs = {1: (-1, +1), 2: (+1, +1), 3: (+1, -1), 4: (-1, -1)}
        if region not in signs:
            raise ValueError(f"region must be 1-4, got {region}")
        sU, sV = signs[region]
        if (sU * U_K < 0) or (sV * V_K < 0):
            raise ValueError(
                f"point is outside region {region}: (U_K={U_K}, V_K={V_K}) "
                f"does not match required signs {(sU, sV)}"
            )

        # Avoid the degenerate case U_K=V_K=0 (bifurcation sphere).
        if U_K == 0 and V_K == 0:
            return {"t": 0.0, "r": 2.0 * self.mass}

        # r comes from U_K * V_K = (1 - r/(2M)) exp(r/(2M)).
        prod = U_K * V_K
        w = lambertw(-prod / math.e, k=0)
        # w should be real for admissible inputs; guard just in case.
        if abs(w.imag) > 1e-9:
            raise ValueError(
                f"Lambert W returned complex value ({w}) for prod={prod}; "
                "point may be outside the physical domain."
            )
        x = 1.0 + float(w.real)  # x = r / (2M)
        r = 2.0 * self.mass * x

        # t from |V_K / U_K| = exp(t/(2M)); the overall sign is fixed by
        # which region we are in via the signs tuple above.  Within a
        # region, the ratio is positive so the log is well-defined.
        if U_K == 0:
            # On a horizon — t is undefined (it runs to +/- infinity).
            raise ValueError(
                "point lies on a horizon (U_K=0); t is infinite there."
            )
        ratio = V_K / U_K
        # In regions 1,3 the ratio is negative; in 2,4 it is positive.
        # |ratio| is what we need.
        t = 2.0 * self.mass * math.log(abs(ratio))

        return {"t": t, "r": r}

    # --- global structure (Phase 2 coding pass) -------------------

    def boundary_paths(self) -> list[Path]:
        r"""Return the outer asymptotic edges, horizons, and singularities.

        In :math:`(U, V)` compactified null coordinates the four-region
        Schwarzschild diagram has a beautifully simple structure:

        - **Four asymptotic edges** at :math:`U = \pm\pi/2` or
          :math:`V = \pm\pi/2` — the :math:`\mathscr{I}^\pm` of
          regions I and III.
        - **Two singularity edges** on the straight lines
          :math:`U + V = \pm\pi/2` (the future and past singularities).
          The straightness is not an approximation: the equation
          :math:`U_K V_K = 1` is equivalent to :math:`\tan U\,\tan V = 1`,
          which for :math:`U, V \in (0, \pi/2)` simplifies to
          :math:`U + V = \pi/2`.
        - **Four horizon null lines** meeting at the bifurcation
          sphere :math:`(U, V) = (0, 0)`.

        Total: 10 paths, tagged ``kind='boundary'``, ``'singularity'``,
        or ``'horizon'`` respectively.
        """
        import math

        h = math.pi / 2
        boundary_style = PathStyle(stroke="#000000", width=1.5)
        horizon_style = PathStyle(stroke="#444444", width=1.0, dash=(4.0, 3.0))
        singularity_style = PathStyle(stroke="#b30000", width=1.8, dash=(2.0, 2.0))

        def line(a: Vec2, b: Vec2, *, style: PathStyle, kind: str) -> Path:
            return Path(points=(a, b), style=style, kind=kind)

        paths: list[Path] = [
            # --- scri of region I (right-side exterior) ---------------
            # scri+(I): V = pi/2, U in [-pi/2, 0]
            line(Vec2(-h, h), Vec2(0.0, h), style=boundary_style, kind="boundary"),
            # scri-(I): U = -pi/2, V in [0, pi/2]
            line(Vec2(-h, 0.0), Vec2(-h, h), style=boundary_style, kind="boundary"),

            # --- scri of region III (left-side exterior) --------------
            # scri+(III): U = pi/2, V in [-pi/2, 0]
            line(Vec2(h, -h), Vec2(h, 0.0), style=boundary_style, kind="boundary"),
            # scri-(III): V = -pi/2, U in [0, pi/2]
            line(Vec2(0.0, -h), Vec2(h, -h), style=boundary_style, kind="boundary"),

            # --- singularities -----------------------------------------
            # Future singularity: straight line U + V = pi/2
            # from i+(I)=(0, pi/2) to i+(III)=(pi/2, 0)
            line(
                Vec2(0.0, h), Vec2(h, 0.0),
                style=singularity_style, kind="singularity",
            ),
            # Past singularity: straight line U + V = -pi/2
            # from i-(I)=(-pi/2, 0) to i-(III)=(0, -pi/2)
            line(
                Vec2(-h, 0.0), Vec2(0.0, -h),
                style=singularity_style, kind="singularity",
            ),

            # --- horizons ----------------------------------------------
            # Future horizon of I (between I and II): U = 0, V in [0, pi/2]
            line(Vec2(0.0, 0.0), Vec2(0.0, h), style=horizon_style, kind="horizon"),
            # Past horizon of I (between I and IV): V = 0, U in [-pi/2, 0]
            line(Vec2(-h, 0.0), Vec2(0.0, 0.0), style=horizon_style, kind="horizon"),
            # Future horizon of III (between III and II): V = 0, U in [0, pi/2]
            line(Vec2(0.0, 0.0), Vec2(h, 0.0), style=horizon_style, kind="horizon"),
            # Past horizon of III (between III and IV): U = 0, V in [-pi/2, 0]
            line(Vec2(0.0, -h), Vec2(0.0, 0.0), style=horizon_style, kind="horizon"),
        ]
        return paths

    def infinities(self) -> list[Infinity]:
        r"""Return the 10 named infinities of the eternal Schwarzschild diagram.

        Region I and region III each host a full set :math:`(i^+, i^-,
        i^0, \mathscr{I}^+, \mathscr{I}^-)`; regions II and IV have no
        infinities of their own (their future / past ends in the
        spacelike singularity).  The point / edge positions are:

        - Region I  (right exterior):
          :math:`i^+ = (0, \pi/2)`, :math:`i^- = (-\pi/2, 0)`,
          :math:`i^0 = (-\pi/2, \pi/2)`, with
          :math:`\mathscr{I}^+` midpoint :math:`(-\pi/4, \pi/2)` and
          :math:`\mathscr{I}^-` midpoint :math:`(-\pi/2, \pi/4)`.
        - Region III (left exterior): mirror of region I under
          :math:`(U, V) \to (V, U)` then :math:`(U, V) \to (-U, -V)`
          — concretely, :math:`i^+ = (\pi/2, 0)`,
          :math:`i^- = (0, -\pi/2)`, :math:`i^0 = (\pi/2, -\pi/2)`,
          with scri midpoints at :math:`(\pi/4, -\pi/2)` and
          :math:`(\pi/2, -\pi/4)`.
        """
        import math

        h = math.pi / 2
        q = math.pi / 4
        return [
            # Region I
            Infinity("i+", Vec2(0.0, h), region=1),
            Infinity("i-", Vec2(-h, 0.0), region=1),
            Infinity("i0", Vec2(-h, h), region=1),
            Infinity("scri+", Vec2(-q, h), region=1),
            Infinity("scri-", Vec2(-h, q), region=1),
            # Region III (mirror exterior).  The global time arrow of
            # the eternal diagram points up in (T, X), so scri+(III) is
            # the upper-left null edge (U = pi/2, V in (-pi/2, 0)) and
            # scri-(III) is the lower-left edge (V = -pi/2, U in (0, pi/2)).
            Infinity("i+", Vec2(h, 0.0), region=3),
            Infinity("i-", Vec2(0.0, -h), region=3),
            Infinity("i0", Vec2(h, -h), region=3),
            Infinity("scri+", Vec2(h, -q), region=3),   # upper-left edge
            Infinity("scri-", Vec2(q, -h), region=3),   # lower-left edge
        ]
