"""Tests for the Schwarzschild Penrose chart.

Covers the four-region maximally extended spacetime.  Most
assertions are pinned to closed-form limits (i+, i-, i0, scri+, scri-,
singularity locus) that are independent of the particular numerical
representation.
"""

import math

import pytest

from spacetime_lab.diagrams import (
    Path,
    PenroseChart,
    SchwarzschildPenrose,
    Vec2,
)


HALF_PI = math.pi / 2
QUARTER_PI = math.pi / 4


class TestSchwarzschildMetadata:
    def setup_method(self):
        self.chart = SchwarzschildPenrose(mass=1.0)

    def test_is_penrose_chart(self):
        assert isinstance(self.chart, PenroseChart)

    def test_name_includes_mass(self):
        assert "M=1.0" in self.chart.name

    def test_four_regions(self):
        assert self.chart.regions == (1, 2, 3, 4)

    def test_physical_coordinates(self):
        assert self.chart.physical_coordinate_names == ("t", "r")

    def test_negative_mass_raises(self):
        with pytest.raises(ValueError):
            SchwarzschildPenrose(mass=-1.0)

    def test_zero_mass_raises(self):
        with pytest.raises(ValueError):
            SchwarzschildPenrose(mass=0.0)


class TestRegionDomains:
    """Each region has a strict r-range; the horizon is not included."""

    def setup_method(self):
        self.chart = SchwarzschildPenrose(mass=1.0)

    def test_region_1_requires_r_above_horizon(self):
        with pytest.raises(ValueError):
            self.chart.physical_to_compact(1, t=0, r=1.5)
        with pytest.raises(ValueError):
            self.chart.physical_to_compact(1, t=0, r=2.0)  # exactly on horizon

    def test_region_2_requires_r_inside_horizon(self):
        with pytest.raises(ValueError):
            self.chart.physical_to_compact(2, t=0, r=3.0)
        with pytest.raises(ValueError):
            self.chart.physical_to_compact(2, t=0, r=0.0)

    def test_region_3_requires_r_above_horizon(self):
        with pytest.raises(ValueError):
            self.chart.physical_to_compact(3, t=0, r=1.0)

    def test_region_4_requires_r_inside_horizon(self):
        with pytest.raises(ValueError):
            self.chart.physical_to_compact(4, t=0, r=5.0)

    def test_unknown_region_raises(self):
        with pytest.raises(ValueError):
            self.chart.physical_to_compact(5, t=0, r=3)

    def test_missing_coordinate_raises(self):
        with pytest.raises(ValueError):
            self.chart.physical_to_compact(1, t=0)


class TestRegionSigns:
    """Each region lives in a specific quadrant of (U, V)."""

    def setup_method(self):
        self.chart = SchwarzschildPenrose(mass=1.0)

    def test_region_1_is_negative_positive(self):
        v = self.chart.physical_to_compact(1, t=0.5, r=4.0)
        assert v.U < 0
        assert v.V > 0

    def test_region_2_is_positive_positive(self):
        v = self.chart.physical_to_compact(2, t=0.3, r=1.2)
        assert v.U > 0
        assert v.V > 0

    def test_region_3_is_positive_negative(self):
        v = self.chart.physical_to_compact(3, t=-0.2, r=5.0)
        assert v.U > 0
        assert v.V < 0

    def test_region_4_is_negative_negative(self):
        v = self.chart.physical_to_compact(4, t=0.1, r=0.7)
        assert v.U < 0
        assert v.V < 0


class TestInfinityLimits:
    """Timelike/spatial/null infinities of Region I approach known points."""

    def setup_method(self):
        self.chart = SchwarzschildPenrose(mass=1.0)

    def test_future_timelike_infinity(self):
        """Large +t with any r > 2M approaches (0, pi/2) = i+."""
        v = self.chart.physical_to_compact(1, t=1e6, r=5.0)
        assert math.isclose(v.U, 0.0, abs_tol=1e-3)
        assert math.isclose(v.V, HALF_PI, abs_tol=1e-3)

    def test_past_timelike_infinity(self):
        v = self.chart.physical_to_compact(1, t=-1e6, r=5.0)
        assert math.isclose(v.U, -HALF_PI, abs_tol=1e-3)
        assert math.isclose(v.V, 0.0, abs_tol=1e-3)

    def test_spatial_infinity(self):
        """r -> infinity at fixed t approaches (-pi/2, pi/2) = i0."""
        v = self.chart.physical_to_compact(1, t=0.0, r=1e5)
        assert math.isclose(v.U, -HALF_PI, abs_tol=1e-3)
        assert math.isclose(v.V, HALF_PI, abs_tol=1e-3)


class TestSingularityLocus:
    """The singularity sits on U + V = +/- pi/2 to high precision."""

    def setup_method(self):
        self.chart = SchwarzschildPenrose(mass=1.0)

    def test_future_singularity_in_region_2(self):
        for r in [0.5, 0.1, 0.01, 1e-6]:
            v = self.chart.physical_to_compact(2, t=0, r=r)
            assert v.U + v.V < HALF_PI
        # r -> 0 approaches U + V = pi/2
        v_close = self.chart.physical_to_compact(2, t=0, r=1e-8)
        assert math.isclose(v_close.U + v_close.V, HALF_PI, abs_tol=1e-6)

    def test_past_singularity_in_region_4(self):
        v_close = self.chart.physical_to_compact(4, t=0, r=1e-8)
        assert math.isclose(v_close.U + v_close.V, -HALF_PI, abs_tol=1e-6)


class TestHorizonLimits:
    """Approaching r = 2M from above/below collapses to the bifurcation axis."""

    def setup_method(self):
        self.chart = SchwarzschildPenrose(mass=1.0)

    def test_region_1_horizon_approach(self):
        """r -> 2M+ at t = 0 approaches U = V -> 0-,0+."""
        v = self.chart.physical_to_compact(1, t=0, r=2.0 + 1e-8)
        assert abs(v.U) < 1e-3
        assert abs(v.V) < 1e-3

    def test_region_2_horizon_approach(self):
        v = self.chart.physical_to_compact(2, t=0, r=2.0 - 1e-8)
        assert abs(v.U) < 1e-3
        assert abs(v.V) < 1e-3


class TestRoundTrips:
    """Forward then inverse recovers the original coordinates."""

    CASES = [
        (1, 1.5, 4.0),
        (1, -0.5, 2.5),
        (1, 0.0, 10.0),
        (1, 3.0, 6.0),
        (2, 0.3, 1.2),
        (2, -0.2, 0.5),
        (2, 1.0, 1.7),
        (3, 1.0, 3.0),
        (3, -2.0, 5.0),
        (4, 0.5, 0.8),
        (4, 0.0, 1.5),
    ]

    @pytest.mark.parametrize("region,t,r", CASES)
    def test_round_trip(self, region, t, r):
        chart = SchwarzschildPenrose(mass=1.0)
        p = chart.physical_to_compact(region, t=t, r=r)
        back = chart.compact_to_physical(region, p)
        assert math.isclose(back["t"], t, abs_tol=1e-8)
        assert math.isclose(back["r"], r, abs_tol=1e-8)

    def test_inverse_wrong_region_raises(self):
        chart = SchwarzschildPenrose(mass=1.0)
        # Take a point clearly in region II and ask for region I.
        p_ii = chart.physical_to_compact(2, t=0, r=1.0)
        with pytest.raises(ValueError):
            chart.compact_to_physical(1, p_ii)

    def test_inverse_on_boundary_raises(self):
        chart = SchwarzschildPenrose(mass=1.0)
        with pytest.raises(ValueError):
            chart.compact_to_physical(1, Vec2(HALF_PI, 0))

    def test_inverse_on_horizon_raises(self):
        chart = SchwarzschildPenrose(mass=1.0)
        # U = 0, V > 0 is the future horizon of region I; t is infinite there.
        with pytest.raises(ValueError):
            chart.compact_to_physical(1, Vec2(0.0, 0.5))


class TestBoundaryStructure:
    """The chart's boundary paths form the expected 10-edge decomposition."""

    def setup_method(self):
        self.chart = SchwarzschildPenrose(mass=1.0)

    def test_ten_boundary_paths(self):
        paths = self.chart.boundary_paths()
        assert len(paths) == 10
        assert all(isinstance(p, Path) for p in paths)

    def test_path_kinds_partition(self):
        kinds = [p.kind for p in self.chart.boundary_paths()]
        assert kinds.count("boundary") == 4     # 4 scri edges (2 per exterior)
        assert kinds.count("horizon") == 4      # 4 horizon null lines
        assert kinds.count("singularity") == 2  # future + past singularity

    def test_future_singularity_endpoints(self):
        """Future singularity connects i+(I)=(0, pi/2) to i+(III)=(pi/2, 0)."""
        sings = [p for p in self.chart.boundary_paths() if p.kind == "singularity"]
        future = next(s for s in sings if s.points[0].V > 0 or s.points[1].V > 0)
        pts = sorted(((p.U, p.V) for p in future.points))
        assert math.isclose(pts[0][0], 0.0) and math.isclose(pts[0][1], HALF_PI)
        assert math.isclose(pts[1][0], HALF_PI) and math.isclose(pts[1][1], 0.0)

    def test_horizons_pass_through_bifurcation(self):
        """At least one endpoint of every horizon path is the bifurcation (0,0)."""
        horizons = [p for p in self.chart.boundary_paths() if p.kind == "horizon"]
        for h in horizons:
            has_bif = any(
                math.isclose(pt.U, 0.0) and math.isclose(pt.V, 0.0)
                for pt in h.points
            )
            assert has_bif, f"horizon path does not touch the bifurcation: {h}"


class TestInfinitiesOfSchwarzschild:
    def setup_method(self):
        self.chart = SchwarzschildPenrose(mass=1.0)

    def test_ten_infinities(self):
        assert len(self.chart.infinities()) == 10

    def test_both_exterior_regions_represented(self):
        regions = {inf.region for inf in self.chart.infinities()}
        assert regions == {1, 3}

    def test_all_five_symbols_per_exterior(self):
        infs = self.chart.infinities()
        for region in (1, 3):
            symbols_in_region = {
                i.symbol for i in infs if i.region == region
            }
            assert symbols_in_region == {"i+", "i-", "i0", "scri+", "scri-"}

    def test_region_1_i_plus_at_origin_upper(self):
        by_symbol = {
            (i.symbol, i.region): i.position for i in self.chart.infinities()
        }
        assert by_symbol[("i+", 1)] == Vec2(0.0, HALF_PI)
        assert by_symbol[("i-", 1)] == Vec2(-HALF_PI, 0.0)
        assert by_symbol[("i0", 1)] == Vec2(-HALF_PI, HALF_PI)


class TestSchwarzschildToScene:
    def setup_method(self):
        self.chart = SchwarzschildPenrose(mass=1.0)

    def test_scene_populated(self):
        scene = self.chart.to_scene()
        assert scene.name == "Schwarzschild Penrose (M=1.0)"
        assert len(scene.paths) == 10  # 4 boundary + 4 horizon + 2 singularity
        assert len(scene.infinities) == 10
        assert scene.metadata["regions"] == [1, 2, 3, 4]

    def test_scene_with_worldline_and_lightcone(self):
        scene = self.chart.to_scene(
            world_lines=[
                (
                    1,
                    [
                        {"t": -1.0, "r": 6.0},
                        {"t": 0.0, "r": 6.0},
                        {"t": 1.0, "r": 6.0},
                    ],
                )
            ],
            light_cones=[(1, {"t": 0.0, "r": 6.0})],
        )
        kinds = [p.kind for p in scene.paths]
        assert kinds.count("world_line") == 1
        assert kinds.count("lightcone") == 2


class TestMassScaling:
    """Scaling M rescales t and r by the same factor but preserves (U, V) shape.

    Concretely, if (t, r) -> (U, V) under mass M, then (alpha*t, alpha*r)
    should give the *same* (U, V) under mass alpha*M.  This is the standard
    geometric-units scaling.
    """

    @pytest.mark.parametrize("alpha", [0.5, 2.0, 3.7])
    def test_mass_scale_invariance(self, alpha):
        ch1 = SchwarzschildPenrose(mass=1.0)
        ch_alpha = SchwarzschildPenrose(mass=alpha)
        v1 = ch1.physical_to_compact(1, t=0.4, r=3.0)
        v_alpha = ch_alpha.physical_to_compact(1, t=0.4 * alpha, r=3.0 * alpha)
        assert math.isclose(v1.U, v_alpha.U, abs_tol=1e-12)
        assert math.isclose(v1.V, v_alpha.V, abs_tol=1e-12)
