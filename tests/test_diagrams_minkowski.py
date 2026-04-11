"""Tests for the 1+1 Minkowski Penrose chart.

These pin down the reference implementation that every other chart is
checked against.  If these fail, nothing else in `spacetime_lab.diagrams`
can be trusted.
"""

import math

import pytest

from spacetime_lab.diagrams import (
    Infinity,
    MinkowskiPenrose,
    Path,
    PenroseChart,
    Scene,
    Vec2,
)


HALF_PI = math.pi / 2


class TestMinkowskiMetadata:
    def setup_method(self):
        self.chart = MinkowskiPenrose()

    def test_is_penrose_chart(self):
        assert isinstance(self.chart, PenroseChart)

    def test_name(self):
        assert self.chart.name == "Minkowski (1+1)"

    def test_single_region(self):
        assert self.chart.regions == (1,)

    def test_physical_coordinates(self):
        assert self.chart.physical_coordinate_names == ("t", "x")


class TestMinkowskiForwardMap:
    def setup_method(self):
        self.chart = MinkowskiPenrose()

    def test_origin_maps_to_origin(self):
        """(t=0, x=0) -> (U=0, V=0)."""
        v = self.chart.physical_to_compact(region=1, t=0.0, x=0.0)
        assert v == Vec2(0.0, 0.0)

    def test_future_timelike_infinity_limit(self):
        """Large future t with x=0 should approach (pi/2, pi/2)."""
        v = self.chart.physical_to_compact(region=1, t=1e12, x=0.0)
        assert math.isclose(v.U, HALF_PI, abs_tol=1e-6)
        assert math.isclose(v.V, HALF_PI, abs_tol=1e-6)

    def test_past_timelike_infinity_limit(self):
        v = self.chart.physical_to_compact(region=1, t=-1e12, x=0.0)
        assert math.isclose(v.U, -HALF_PI, abs_tol=1e-6)
        assert math.isclose(v.V, -HALF_PI, abs_tol=1e-6)

    def test_right_spatial_infinity_limit(self):
        """Large positive x with t=0 -> U=-pi/2, V=+pi/2."""
        v = self.chart.physical_to_compact(region=1, t=0.0, x=1e12)
        assert math.isclose(v.U, -HALF_PI, abs_tol=1e-6)
        assert math.isclose(v.V, HALF_PI, abs_tol=1e-6)

    def test_formula_matches_arctan(self):
        """U = arctan(t-x), V = arctan(t+x) exactly."""
        for t, x in [(1, 2), (-3, 4), (0.5, -0.7), (5, 5)]:
            v = self.chart.physical_to_compact(region=1, t=t, x=x)
            assert math.isclose(v.U, math.atan(t - x))
            assert math.isclose(v.V, math.atan(t + x))


class TestMinkowskiRoundTrip:
    def setup_method(self):
        self.chart = MinkowskiPenrose()

    @pytest.mark.parametrize(
        "t,x",
        [
            (0.0, 0.0),
            (1.0, 0.0),
            (0.0, 1.0),
            (-2.0, 3.0),
            (5.0, -4.0),
            (0.3, 0.7),
            (-0.1, -0.9),
        ],
    )
    def test_forward_then_inverse_recovers_input(self, t, x):
        v = self.chart.physical_to_compact(region=1, t=t, x=x)
        back = self.chart.compact_to_physical(region=1, point=v)
        assert math.isclose(back["t"], t, abs_tol=1e-10)
        assert math.isclose(back["x"], x, abs_tol=1e-10)

    def test_inverse_raises_on_boundary(self):
        with pytest.raises(ValueError):
            self.chart.compact_to_physical(1, Vec2(HALF_PI, 0.0))
        with pytest.raises(ValueError):
            self.chart.compact_to_physical(1, Vec2(0.0, HALF_PI))


class TestMinkowskiValidation:
    def setup_method(self):
        self.chart = MinkowskiPenrose()

    def test_wrong_region_raises(self):
        with pytest.raises(ValueError):
            self.chart.physical_to_compact(region=2, t=0, x=0)

    def test_missing_coordinate_raises(self):
        with pytest.raises(ValueError):
            self.chart.physical_to_compact(region=1, t=0)

    def test_inverse_wrong_region_raises(self):
        with pytest.raises(ValueError):
            self.chart.compact_to_physical(2, Vec2(0.0, 0.0))


class TestMinkowskiStructure:
    def setup_method(self):
        self.chart = MinkowskiPenrose()

    def test_four_boundary_paths(self):
        paths = self.chart.boundary_paths()
        assert len(paths) == 4
        assert all(isinstance(p, Path) for p in paths)
        assert all(p.kind == "boundary" for p in paths)

    def test_boundary_paths_are_the_four_edges(self):
        """Check each edge uses the expected U/V values."""
        edge_coords = {
            frozenset({(p.U, p.V) for p in path.points})
            for path in self.chart.boundary_paths()
        }
        expected = {
            frozenset({(-HALF_PI, HALF_PI), (HALF_PI, HALF_PI)}),   # top
            frozenset({(HALF_PI, -HALF_PI), (HALF_PI, HALF_PI)}),   # right
            frozenset({(-HALF_PI, -HALF_PI), (HALF_PI, -HALF_PI)}), # bottom
            frozenset({(-HALF_PI, -HALF_PI), (-HALF_PI, HALF_PI)}), # left
        }
        assert edge_coords == expected

    def test_eight_infinities(self):
        """1+1 Minkowski has two i0 points (left/right) and two disjoint
        pieces of each scri, hence 8 entries total."""
        infs = self.chart.infinities()
        assert len(infs) == 8
        assert all(isinstance(i, Infinity) for i in infs)

    def test_infinity_symbols_counts(self):
        infs = self.chart.infinities()
        symbols = [i.symbol for i in infs]
        assert symbols.count("i+") == 1
        assert symbols.count("i-") == 1
        assert symbols.count("i0") == 2   # left + right
        assert symbols.count("scri+") == 2  # upper-left + upper-right
        assert symbols.count("scri-") == 2  # lower-left + lower-right

    def test_timelike_infinity_positions(self):
        positions = {i.symbol: [] for i in self.chart.infinities()}
        for i in self.chart.infinities():
            positions[i.symbol].append(i.position)
        assert Vec2(HALF_PI, HALF_PI) in positions["i+"]
        assert Vec2(-HALF_PI, -HALF_PI) in positions["i-"]

    def test_both_spatial_infinities_present(self):
        i0_positions = [
            i.position for i in self.chart.infinities() if i.symbol == "i0"
        ]
        assert Vec2(-HALF_PI, HALF_PI) in i0_positions  # right
        assert Vec2(HALF_PI, -HALF_PI) in i0_positions  # left


class TestMinkowskiDerivedMethods:
    def setup_method(self):
        self.chart = MinkowskiPenrose()

    def test_light_cone_returns_two_paths(self):
        future, past = self.chart.light_cone_at(1, length=0.1, t=0.0, x=0.0)
        assert future.kind == "lightcone"
        assert past.kind == "lightcone"
        # 3 vertices each (past endpoint / vertex / future endpoint)
        assert len(future.points) == 3
        assert len(past.points) == 3

    def test_light_cone_45_degrees(self):
        """Each leg is along +U or +V only (null direction)."""
        future, past = self.chart.light_cone_at(1, length=0.25, t=0.5, x=0.2)
        # For both paths the vertex is points[1], legs are points[0] and points[2].
        for cone in (future, past):
            v = cone.points[1]
            leg_a = cone.points[0]
            leg_b = cone.points[2]
            # One leg varies only in U, the other only in V.
            du_a, dv_a = leg_a.U - v.U, leg_a.V - v.V
            du_b, dv_b = leg_b.U - v.U, leg_b.V - v.V
            assert math.isclose(du_a, 0.0) or math.isclose(dv_a, 0.0)
            assert math.isclose(du_b, 0.0) or math.isclose(dv_b, 0.0)

    def test_map_curve_preserves_length(self):
        samples = [
            {"t": -2.0, "x": 0.0},
            {"t": -1.0, "x": 0.0},
            {"t": 0.0, "x": 0.0},
            {"t": 1.0, "x": 0.0},
            {"t": 2.0, "x": 0.0},
        ]
        path = self.chart.map_curve(1, samples)
        assert path.kind == "world_line"
        assert len(path.points) == len(samples)

    def test_map_curve_rejects_short_input(self):
        with pytest.raises(ValueError):
            self.chart.map_curve(1, [{"t": 0, "x": 0}])

    def test_static_observer_is_a_vertical_line_segment(self):
        """A timelike observer at x=0 stays on the U+V=0 diagonal in null coords.

        For u = t - x = t, v = t + x = t at x=0, so U=V=arctan(t). The
        path (in null coords) lives on U == V.
        """
        samples = [{"t": tt, "x": 0.0} for tt in [-3, -1, 0, 1, 3]]
        path = self.chart.map_curve(1, samples)
        for p in path.points:
            assert math.isclose(p.U, p.V)


class TestMinkowskiToScene:
    def setup_method(self):
        self.chart = MinkowskiPenrose()

    def test_empty_scene_has_only_boundary_and_infinities(self):
        scene = self.chart.to_scene()
        assert isinstance(scene, Scene)
        assert scene.name == "Minkowski (1+1)"
        assert len(scene.paths) == 4  # four boundary edges
        assert len(scene.infinities) == 8
        assert all(p.kind == "boundary" for p in scene.paths)
        assert scene.metadata["regions"] == [1]

    def test_scene_includes_world_lines_and_light_cones(self):
        scene = self.chart.to_scene(
            world_lines=[
                (1, [{"t": -1, "x": 0}, {"t": 0, "x": 0}, {"t": 1, "x": 0}])
            ],
            light_cones=[(1, {"t": 0, "x": 0})],
        )
        kinds = [p.kind for p in scene.paths]
        assert kinds.count("boundary") == 4
        assert kinds.count("world_line") == 1
        assert kinds.count("lightcone") == 2
