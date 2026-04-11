"""Tests for the Phase 7 holography module + AdS metric.

The point of these tests is the **end-to-end verification of
holographic entanglement entropy** for the simplest possible case:
a single interval in a 2D CFT, dual to a Poincaré AdS_3 boundary
geodesic.  Bulk-side Ryu-Takayanagi and boundary-side Calabrese-Cardy
must agree to machine precision when the central charge is determined
from the AdS radius via Brown-Henneaux.

Every formula was verified against an external source before
implementation; see the file headers in
``spacetime_lab/holography/`` for the verification trail
(Brown-Henneaux 1986, Calabrese-Cardy 2004, Ryu-Takayanagi 2006,
Wikipedia AdS).

Most tests pin to the exact closed forms:

- AdS_n Ricci scalar = -n(n-1)/L^2
- AdS_n cosmological constant = -(n-1)(n-2)/(2 L^2)
- AdS_n Einstein-constant: R_munu = -(n-1)/L^2 g_munu
- Poincaré AdS_3 boundary geodesic length = 2 L log(|x_B - x_A|/eps)
- Brown-Henneaux: c = 3 L / (2 G_N)
- Ryu-Takayanagi: S = Length(geodesic) / (4 G_N)
- Calabrese-Cardy: S = (c/3) log(L_A/eps)
"""

import math

import pytest

from spacetime_lab.holography import (
    brown_henneaux_central_charge,
    calabrese_cardy_2d,
    geodesic_length_ads3,
    ryu_takayanagi_ads3,
    verify_rt_against_calabrese_cardy,
)
from spacetime_lab.metrics import AdS


# ─────────────────────────────────────────────────────────────────────
# AdS metric class
# ─────────────────────────────────────────────────────────────────────


class TestAdSConstruction:
    def test_default_is_ads3_unit_radius(self):
        ads = AdS()
        assert ads.dimension == 3
        assert ads.radius == 1.0

    def test_dimension_below_2_raises(self):
        with pytest.raises(ValueError):
            AdS(dimension=1)

    def test_dimension_zero_raises(self):
        with pytest.raises(ValueError):
            AdS(dimension=0)

    def test_negative_radius_raises(self):
        with pytest.raises(ValueError):
            AdS(radius=-1.0)

    def test_zero_radius_raises(self):
        with pytest.raises(ValueError):
            AdS(radius=0.0)

    def test_repr(self):
        ads = AdS(dimension=4, radius=2.0)
        s = repr(ads)
        assert "dimension=4" in s
        assert "radius=2.0" in s

    def test_name(self):
        assert "AdS_3" in AdS(dimension=3).name
        assert "AdS_4" in AdS(dimension=4).name

    def test_coordinates_count(self):
        for d in [2, 3, 4, 5]:
            ads = AdS(dimension=d)
            assert len(ads.coordinates) == d


class TestAdSAnalyticInvariants:
    """Pin closed-form Ricci scalar, cosmological constant."""

    @pytest.mark.parametrize(
        "dim,radius,expected_R",
        [
            (3, 1.0, -6.0),       # -3*2/1
            (3, 2.0, -1.5),       # -3*2/4
            (3, 0.5, -24.0),      # -3*2/0.25
            (4, 1.0, -12.0),      # -4*3/1
            (5, 1.0, -20.0),      # -5*4/1
        ],
    )
    def test_ricci_scalar_formula(self, dim, radius, expected_R):
        ads = AdS(dimension=dim, radius=radius)
        assert math.isclose(ads.expected_ricci_scalar(), expected_R)

    @pytest.mark.parametrize(
        "dim,radius,expected_Lambda",
        [
            (3, 1.0, -1.0),       # -2*1/(2*1)
            (3, 2.0, -0.25),      # -2*1/(2*4)
            (4, 1.0, -3.0),       # -3*2/(2*1)
            (4, 2.0, -0.75),      # -3*2/(2*4)
            (5, 1.0, -6.0),       # -4*3/(2*1)
        ],
    )
    def test_cosmological_constant_formula(self, dim, radius, expected_Lambda):
        ads = AdS(dimension=dim, radius=radius)
        assert math.isclose(ads.cosmological_constant(), expected_Lambda)

    def test_ricci_proportionality_constant(self):
        for dim in [3, 4, 5]:
            for radius in [0.5, 1.0, 2.0, 3.7]:
                ads = AdS(dimension=dim, radius=radius)
                expected = -(dim - 1) / (radius * radius)
                assert math.isclose(
                    ads.expected_ricci_proportionality(), expected
                )


class TestAdSEinsteinConstantCurvature:
    """Verify R_munu = -(n-1)/L^2 g_munu numerically (the strong test)."""

    def test_ads3_unit_radius(self):
        ads = AdS(dimension=3, radius=1.0)
        residual = ads.verify_einstein_constant_curvature()
        assert residual < 1e-10

    def test_ads3_radius_2(self):
        ads = AdS(dimension=3, radius=2.0)
        residual = ads.verify_einstein_constant_curvature()
        assert residual < 1e-10

    def test_ads4(self):
        ads = AdS(dimension=4, radius=1.0)
        residual = ads.verify_einstein_constant_curvature()
        assert residual < 1e-10

    def test_ads5(self):
        ads = AdS(dimension=5, radius=1.5)
        residual = ads.verify_einstein_constant_curvature()
        assert residual < 1e-10


# ─────────────────────────────────────────────────────────────────────
# geodesic_length_ads3
# ─────────────────────────────────────────────────────────────────────


class TestGeodesicLengthAdS3:
    def test_canonical_value(self):
        L = geodesic_length_ads3(x_A=0.0, x_B=2.0, radius=1.0, epsilon=0.01)
        # 2 * 1 * log(200)
        expected = 2.0 * math.log(200.0)
        assert math.isclose(L, expected, abs_tol=1e-12)

    def test_swap_endpoints_gives_same_length(self):
        L1 = geodesic_length_ads3(x_A=0.0, x_B=3.0, radius=1.0, epsilon=0.01)
        L2 = geodesic_length_ads3(x_A=3.0, x_B=0.0, radius=1.0, epsilon=0.01)
        assert math.isclose(L1, L2, abs_tol=1e-12)

    def test_translation_invariance(self):
        """The length depends only on |x_B - x_A|."""
        L1 = geodesic_length_ads3(x_A=0.0, x_B=2.0, radius=1.0, epsilon=0.01)
        L2 = geodesic_length_ads3(x_A=10.0, x_B=12.0, radius=1.0, epsilon=0.01)
        L3 = geodesic_length_ads3(x_A=-5.0, x_B=-3.0, radius=1.0, epsilon=0.01)
        assert math.isclose(L1, L2, abs_tol=1e-12)
        assert math.isclose(L1, L3, abs_tol=1e-12)

    def test_radius_scaling(self):
        """Doubling L doubles the length."""
        L1 = geodesic_length_ads3(x_A=0.0, x_B=2.0, radius=1.0, epsilon=0.01)
        L2 = geodesic_length_ads3(x_A=0.0, x_B=2.0, radius=2.0, epsilon=0.01)
        assert math.isclose(L2, 2 * L1, abs_tol=1e-12)

    def test_logarithmic_in_interval(self):
        """log(2 * L_A) - log(L_A) = log 2."""
        L1 = geodesic_length_ads3(x_A=0.0, x_B=1.0, radius=1.0, epsilon=0.001)
        L2 = geodesic_length_ads3(x_A=0.0, x_B=2.0, radius=1.0, epsilon=0.001)
        # L2 - L1 = 2 L log(2)
        assert math.isclose(L2 - L1, 2.0 * math.log(2.0), abs_tol=1e-12)

    def test_zero_radius_raises(self):
        with pytest.raises(ValueError):
            geodesic_length_ads3(x_A=0, x_B=1, radius=0, epsilon=0.01)

    def test_negative_radius_raises(self):
        with pytest.raises(ValueError):
            geodesic_length_ads3(x_A=0, x_B=1, radius=-1, epsilon=0.01)

    def test_zero_epsilon_raises(self):
        with pytest.raises(ValueError):
            geodesic_length_ads3(x_A=0, x_B=1, radius=1, epsilon=0)

    def test_coincident_endpoints_raises(self):
        with pytest.raises(ValueError):
            geodesic_length_ads3(x_A=2, x_B=2, radius=1, epsilon=0.01)


# ─────────────────────────────────────────────────────────────────────
# brown_henneaux_central_charge
# ─────────────────────────────────────────────────────────────────────


class TestBrownHenneaux:
    def test_unit_radius_unit_GN(self):
        c = brown_henneaux_central_charge(radius=1.0, G_N=1.0)
        assert math.isclose(c, 1.5)  # 3 * 1 / (2 * 1)

    def test_free_boson_central_charge(self):
        """For c = 1 (free boson) we need L = 2 G_N / 3."""
        c = brown_henneaux_central_charge(radius=2.0 / 3.0, G_N=1.0)
        assert math.isclose(c, 1.0, abs_tol=1e-12)

    def test_radius_4(self):
        c = brown_henneaux_central_charge(radius=4.0, G_N=1.0)
        assert math.isclose(c, 6.0)

    def test_GN_dependence(self):
        """c is inversely proportional to G_N."""
        c1 = brown_henneaux_central_charge(radius=1.0, G_N=1.0)
        c2 = brown_henneaux_central_charge(radius=1.0, G_N=2.0)
        assert math.isclose(c2, c1 / 2.0)

    def test_negative_radius_raises(self):
        with pytest.raises(ValueError):
            brown_henneaux_central_charge(radius=-1.0)

    def test_zero_GN_raises(self):
        with pytest.raises(ValueError):
            brown_henneaux_central_charge(radius=1.0, G_N=0.0)


# ─────────────────────────────────────────────────────────────────────
# calabrese_cardy_2d
# ─────────────────────────────────────────────────────────────────────


class TestCalabreseCardy:
    def test_canonical(self):
        S = calabrese_cardy_2d(interval_length=2.0, central_charge=1.0, epsilon=0.01)
        expected = (1.0 / 3.0) * math.log(200.0)
        assert math.isclose(S, expected, abs_tol=1e-12)

    def test_central_charge_scaling(self):
        S1 = calabrese_cardy_2d(2.0, central_charge=1.0, epsilon=0.01)
        S2 = calabrese_cardy_2d(2.0, central_charge=2.0, epsilon=0.01)
        assert math.isclose(S2, 2 * S1)

    def test_log_of_interval(self):
        """S(L_A=4) - S(L_A=2) = (c/3) log 2."""
        S1 = calabrese_cardy_2d(2.0, central_charge=1.5, epsilon=0.01)
        S2 = calabrese_cardy_2d(4.0, central_charge=1.5, epsilon=0.01)
        assert math.isclose(S2 - S1, (1.5 / 3.0) * math.log(2.0), abs_tol=1e-12)

    def test_negative_central_charge_raises(self):
        with pytest.raises(ValueError):
            calabrese_cardy_2d(2.0, central_charge=-1.0, epsilon=0.01)


# ─────────────────────────────────────────────────────────────────────
# ryu_takayanagi_ads3 — bulk side
# ─────────────────────────────────────────────────────────────────────


class TestRyuTakayanagiAdS3:
    def test_canonical(self):
        S = ryu_takayanagi_ads3(interval_length=2.0, radius=1.0, epsilon=0.01)
        expected = (1.0 / (2.0 * 1.0)) * math.log(200.0)
        assert math.isclose(S, expected, abs_tol=1e-12)

    def test_radius_scaling(self):
        """S_RT scales linearly with L (at fixed G_N)."""
        S1 = ryu_takayanagi_ads3(2.0, radius=1.0, epsilon=0.01)
        S2 = ryu_takayanagi_ads3(2.0, radius=2.0, epsilon=0.01)
        assert math.isclose(S2, 2 * S1)

    def test_GN_inverse_scaling(self):
        S1 = ryu_takayanagi_ads3(2.0, radius=1.0, epsilon=0.01, G_N=1.0)
        S2 = ryu_takayanagi_ads3(2.0, radius=1.0, epsilon=0.01, G_N=2.0)
        assert math.isclose(S2, S1 / 2)


# ─────────────────────────────────────────────────────────────────────
# THE Phase 7 gate: RT == Calabrese-Cardy via Brown-Henneaux
# ─────────────────────────────────────────────────────────────────────


class TestRTCalabreseCardyConsistency:
    """The simplest non-trivial check of holographic entanglement entropy.

    Bulk Ryu-Takayanagi and boundary Calabrese-Cardy must give the
    *exactly* the same number when the central charge is determined
    from the AdS radius via Brown-Henneaux.  This is the entire
    content of holographic entanglement entropy in the simplest
    possible case.
    """

    @pytest.mark.parametrize(
        "L_A,L_ads,eps,G",
        [
            (1.0, 1.0, 0.01, 1.0),
            (2.0, 1.0, 0.001, 1.0),
            (5.0, 2.0, 0.001, 1.0),
            (10.0, 4.0, 1e-5, 1.0),
            (3.7, 2.5, 1e-4, 0.5),
            (0.5, 0.6, 1e-3, 1.5),
            (100.0, 1.0, 1e-6, 1.0),
        ],
    )
    def test_RT_equals_CC(self, L_A, L_ads, eps, G):
        rt, cc, residual = verify_rt_against_calabrese_cardy(
            interval_length=L_A,
            radius=L_ads,
            epsilon=eps,
            G_N=G,
        )
        # Both code paths reduce to L/(2G) log(L_A/eps), so the
        # residual should be at *floating-point bit precision*, not
        # just "machine precision" — typically 0.0 exactly.
        assert residual < 1e-12

    def test_residual_is_zero_for_unit_inputs(self):
        rt, cc, residual = verify_rt_against_calabrese_cardy(
            interval_length=1.0, radius=1.0, epsilon=0.01
        )
        # The two code paths reduce to the same expression algebraically,
        # so the residual should be exactly zero.
        assert residual == 0.0


# ─────────────────────────────────────────────────────────────────────
# Cross-validation: RT manually constructed from primitives
# ─────────────────────────────────────────────────────────────────────


class TestPipelineConsistency:
    """Build RT from primitives and check the result matches the helper."""

    def test_RT_from_primitives(self):
        L_A = 2.0
        L_ads = 1.0
        eps = 0.01
        G_N = 1.0
        # Bulk geodesic length
        bulk_L = geodesic_length_ads3(0.0, L_A, radius=L_ads, epsilon=eps)
        # Apply 1/(4 G_N)
        S_manual = bulk_L / (4 * G_N)
        # Compare to the helper
        S_helper = ryu_takayanagi_ads3(L_A, radius=L_ads, epsilon=eps, G_N=G_N)
        assert math.isclose(S_manual, S_helper, abs_tol=1e-12)

    def test_CC_from_brown_henneaux(self):
        L_ads = 1.0
        G_N = 1.0
        L_A = 2.0
        eps = 0.01
        c = brown_henneaux_central_charge(radius=L_ads, G_N=G_N)
        S_manual = (c / 3.0) * math.log(L_A / eps)
        S_helper = calabrese_cardy_2d(L_A, central_charge=c, epsilon=eps)
        assert math.isclose(S_manual, S_helper, abs_tol=1e-12)
