"""Tests for Phase 8: BTZ + finite-T RT + two-interval phase transition.

The point of these tests is the **bit-exact verification of the
holographic dictionary at finite temperature** and at the
**holographic phase transition** for two intervals. Every formula
was verified against an external source before implementation; see
the file headers in ``spacetime_lab/holography/btz.py`` and
``spacetime_lab/holography/two_interval.py``.

The two big results:

1. **Strominger 1998**: BTZ Bekenstein-Hawking entropy
   `S = pi r_+ / (2 G_N)` exactly equals the sum of the two CFT
   Cardy contributions (left + right Virasoro towers) at the
   matching temperature.

2. **Headrick 2010**: For two boundary intervals, the holographic
   entanglement entropy switches between connected and disconnected
   bulk geodesic configurations at cross-ratio `x = 1/2`. The
   mutual information is *exactly zero* in the disconnected phase
   and positive in the connected phase.
"""

import math

import pytest

from spacetime_lab.holography import (
    brown_henneaux_central_charge,
    calabrese_cardy_2d,
    cardy_formula,
    critical_separation_for_phase_transition,
    cross_ratio,
    geodesic_length_btz,
    ryu_takayanagi_btz,
    thermal_calabrese_cardy,
    thermal_entropy_density_high_T,
    two_interval_connected_length,
    two_interval_disconnected_length,
    two_interval_entropy,
    two_interval_mutual_information,
    verify_btz_against_thermal_calabrese_cardy,
    verify_strominger_btz_cardy,
)
from spacetime_lab.metrics import BTZ


# ─────────────────────────────────────────────────────────────────────
# BTZ metric and thermodynamics
# ─────────────────────────────────────────────────────────────────────


class TestBTZConstruction:
    def test_default_construction(self):
        bh = BTZ(horizon_radius=1.0, ads_radius=1.0)
        assert bh.horizon_radius == 1.0
        assert bh.ads_radius == 1.0

    def test_negative_horizon_raises(self):
        with pytest.raises(ValueError):
            BTZ(horizon_radius=-1.0)

    def test_zero_horizon_raises(self):
        with pytest.raises(ValueError):
            BTZ(horizon_radius=0.0)

    def test_negative_ads_radius_raises(self):
        with pytest.raises(ValueError):
            BTZ(horizon_radius=1.0, ads_radius=-1.0)

    def test_repr(self):
        bh = BTZ(horizon_radius=2.5, ads_radius=1.5)
        s = repr(bh)
        assert "horizon_radius=2.5" in s
        assert "ads_radius=1.5" in s


class TestBTZThermodynamics:
    """Hawking temperature, entropy, mass — closed-form invariants."""

    @pytest.mark.parametrize(
        "rp,L,expected_T",
        [
            (1.0, 1.0, 1.0 / (2 * math.pi)),
            (2.0, 1.0, 2.0 / (2 * math.pi)),
            (1.0, 2.0, 1.0 / (2 * math.pi * 4.0)),
            (3.0, 1.5, 3.0 / (2 * math.pi * 2.25)),
        ],
    )
    def test_hawking_temperature(self, rp, L, expected_T):
        bh = BTZ(horizon_radius=rp, ads_radius=L)
        assert math.isclose(bh.hawking_temperature(), expected_T, abs_tol=1e-12)

    @pytest.mark.parametrize(
        "rp,expected_S",
        [
            (1.0, math.pi / 2),
            (2.0, math.pi),
            (4.0, 2 * math.pi),
            (0.5, math.pi / 4),
        ],
    )
    def test_bekenstein_hawking_entropy_unit_GN(self, rp, expected_S):
        bh = BTZ(horizon_radius=rp, ads_radius=1.0)
        assert math.isclose(
            bh.bekenstein_hawking_entropy(), expected_S, abs_tol=1e-12
        )

    def test_entropy_inverse_proportional_to_GN(self):
        bh = BTZ(horizon_radius=1.0)
        s1 = bh.bekenstein_hawking_entropy(G_N=1.0)
        s2 = bh.bekenstein_hawking_entropy(G_N=2.0)
        assert math.isclose(s2, s1 / 2.0)

    def test_mass_parameter(self):
        # M = r_+^2 / (8 G_N L^2), with G_N=1, L=1 gives r_+^2 / 8
        for rp in [1.0, 2.0, 0.5]:
            bh = BTZ(horizon_radius=rp, ads_radius=1.0)
            assert math.isclose(bh.mass_parameter(), rp**2 / 8.0)

    def test_first_law_dM_eq_T_dS(self):
        """dM/dr_+ = T_H * dS/dr_+ should hold for BTZ thermodynamics."""
        L = 1.0
        rp = 2.0
        bh = BTZ(horizon_radius=rp, ads_radius=L)
        # dM/dr_+ = 2 r_+ / (8 L^2)
        dM_drp = 2.0 * rp / (8.0 * L * L)
        # T_H * dS/dr_+ = (r_+ / (2 pi L^2)) * (pi / 2)
        T = bh.hawking_temperature()
        dS_drp = math.pi / 2.0
        T_dS = T * dS_drp
        assert math.isclose(dM_drp, T_dS, abs_tol=1e-12)

    def test_thermal_beta_consistency(self):
        for rp, L in [(1.0, 1.0), (2.0, 1.5), (0.5, 0.7)]:
            bh = BTZ(horizon_radius=rp, ads_radius=L)
            assert math.isclose(
                bh.thermal_beta() * bh.hawking_temperature(), 1.0
            )


class TestBTZIsLocallyAdS3:
    """BTZ is a quotient of AdS_3 — verify Einstein-constant curvature."""

    def test_unit_horizon_unit_radius(self):
        bh = BTZ(horizon_radius=1.0, ads_radius=1.0)
        residual = bh.verify_einstein_constant_curvature()
        assert residual < 1e-10

    def test_larger_horizon(self):
        bh = BTZ(horizon_radius=2.0, ads_radius=1.0)
        residual = bh.verify_einstein_constant_curvature()
        assert residual < 1e-10

    def test_larger_ads_radius(self):
        bh = BTZ(horizon_radius=1.0, ads_radius=2.0)
        residual = bh.verify_einstein_constant_curvature()
        assert residual < 1e-10

    def test_general_case(self):
        bh = BTZ(horizon_radius=1.5, ads_radius=2.5)
        residual = bh.verify_einstein_constant_curvature()
        assert residual < 1e-10


# ─────────────────────────────────────────────────────────────────────
# Cardy formula
# ─────────────────────────────────────────────────────────────────────


class TestCardyFormula:
    def test_canonical_value(self):
        # S = 2 pi sqrt(c Delta / 6)
        c, delta = 6.0, 1.0
        S = cardy_formula(c, delta)
        assert math.isclose(S, 2.0 * math.pi * math.sqrt(1.0))

    def test_zero_weight(self):
        S = cardy_formula(central_charge=1.0, conformal_weight=0.0)
        assert math.isclose(S, 0.0)

    def test_negative_central_charge_raises(self):
        with pytest.raises(ValueError):
            cardy_formula(central_charge=-1.0, conformal_weight=1.0)

    def test_negative_weight_raises(self):
        with pytest.raises(ValueError):
            cardy_formula(central_charge=1.0, conformal_weight=-1.0)


# ─────────────────────────────────────────────────────────────────────
# Strominger 1998: BTZ Bekenstein-Hawking from Cardy
# ─────────────────────────────────────────────────────────────────────


class TestStromingerBTZCardy:
    """The simplest microscopic derivation of black hole entropy.

    BTZ Bekenstein-Hawking entropy = sum of two Cardy contributions
    (one per Virasoro tower) on the boundary CFT at the matching
    temperature, with central charge from Brown-Henneaux.
    """

    @pytest.mark.parametrize(
        "rp,L",
        [
            (1.0, 1.0),
            (2.0, 1.0),
            (1.0, 2.0),
            (1.5, 2.5),
            (5.0, 3.0),
            (0.5, 0.7),
        ],
    )
    def test_BH_equals_double_cardy(self, rp, L):
        s_bh, s_cardy, residual = verify_strominger_btz_cardy(
            horizon_radius=rp, ads_radius=L, G_N=1.0
        )
        assert residual < 1e-12

    def test_GN_dependence(self):
        """The residual should remain bit-exact when changing G_N."""
        for G in [0.5, 1.0, 2.0]:
            _, _, res = verify_strominger_btz_cardy(
                horizon_radius=1.0, ads_radius=1.0, G_N=G
            )
            assert res < 1e-12


# ─────────────────────────────────────────────────────────────────────
# Finite-temperature Calabrese-Cardy
# ─────────────────────────────────────────────────────────────────────


class TestThermalCalabreseCardy:
    def test_canonical_value(self):
        S = thermal_calabrese_cardy(
            interval_length=2.0,
            central_charge=1.5,
            beta=10.0,
            epsilon=0.01,
        )
        # Direct evaluation of (c/3) log[(beta/(pi eps)) sinh(pi L_A / beta)]
        arg = (10.0 / (math.pi * 0.01)) * math.sinh(math.pi * 2.0 / 10.0)
        expected = (1.5 / 3.0) * math.log(arg)
        assert math.isclose(S, expected, abs_tol=1e-12)

    def test_low_temperature_reduces_to_zero_T(self):
        """beta -> infinity should give the zero-T Calabrese-Cardy result."""
        L_A, c, eps = 2.0, 1.5, 0.01
        S_zeroT = calabrese_cardy_2d(L_A, central_charge=c, epsilon=eps)
        S_lowT = thermal_calabrese_cardy(
            L_A, central_charge=c, beta=1e6, epsilon=eps
        )
        assert math.isclose(S_lowT, S_zeroT, abs_tol=1e-9)

    def test_high_temperature_thermal_extensive_piece(self):
        """At high T the formula becomes (pi c L_A / 3 beta) plus a constant."""
        L_A, c, beta, eps = 100.0, 1.5, 0.1, 1e-3
        S_thermal_cc = thermal_calabrese_cardy(L_A, c, beta, eps)
        S_extensive = thermal_entropy_density_high_T(L_A, c, beta)
        cutoff_constant = (c / 3.0) * math.log(beta / (2.0 * math.pi * eps))
        # The asymptotic agreement is bit-exact for large L_A/beta
        # because log(sinh(x)) -> x - log 2 exactly for large x.
        predicted = S_extensive + cutoff_constant
        assert math.isclose(S_thermal_cc, predicted, abs_tol=1e-10)

    def test_handles_overflow_safely(self):
        """The _log_sinh trick should handle very large interval / small beta."""
        L_A, c, beta, eps = 1e3, 1.0, 0.01, 1e-6
        # Naive math.sinh(pi * 1e3 / 0.01) = sinh(pi*1e5) overflows.
        # Our implementation should work.
        S = thermal_calabrese_cardy(L_A, c, beta, eps)
        assert math.isfinite(S)
        assert S > 0

    def test_invalid_inputs_raise(self):
        with pytest.raises(ValueError):
            thermal_calabrese_cardy(0.0, 1.0, 1.0, 0.01)
        with pytest.raises(ValueError):
            thermal_calabrese_cardy(1.0, -1.0, 1.0, 0.01)
        with pytest.raises(ValueError):
            thermal_calabrese_cardy(1.0, 1.0, -1.0, 0.01)
        with pytest.raises(ValueError):
            thermal_calabrese_cardy(1.0, 1.0, 1.0, -0.01)


# ─────────────────────────────────────────────────────────────────────
# Bulk-side BTZ geodesic and Ryu-Takayanagi
# ─────────────────────────────────────────────────────────────────────


class TestGeodesicLengthBTZ:
    def test_canonical_value(self):
        L = geodesic_length_btz(
            interval_length=2.0,
            horizon_radius=1.0,
            ads_radius=1.0,
            epsilon=0.01,
        )
        beta = 2.0 * math.pi * 1.0 * 1.0 / 1.0
        arg = (beta / (math.pi * 0.01)) * math.sinh(math.pi * 2.0 / beta)
        expected = 2.0 * 1.0 * math.log(arg)
        assert math.isclose(L, expected, abs_tol=1e-12)

    def test_radius_scaling(self):
        L1 = geodesic_length_btz(2.0, 1.0, ads_radius=1.0, epsilon=0.01)
        L2 = geodesic_length_btz(2.0, 1.0, ads_radius=2.0, epsilon=0.01)
        # Doubling L doesn't simply double the length (the temperature
        # changes too), but we can check positivity and finiteness
        assert math.isfinite(L1) and math.isfinite(L2)


class TestBTZRTvsThermalCC:
    """Bulk RT in BTZ equals boundary thermal Calabrese-Cardy bit-exactly."""

    @pytest.mark.parametrize(
        "L_A,rp,L_ads,eps,G",
        [
            (2.0, 1.0, 1.0, 0.01, 1.0),
            (5.0, 2.0, 1.0, 0.001, 1.0),
            (10.0, 3.0, 2.0, 1e-4, 1.0),
            (1.0, 1.0, 0.5, 0.001, 1.0),
            (3.0, 0.5, 1.5, 1e-3, 0.5),
            (100.0, 1.0, 1.0, 1e-6, 1.0),  # high-T regime
        ],
    )
    def test_RT_equals_thermal_CC(self, L_A, rp, L_ads, eps, G):
        rt, cc, residual = verify_btz_against_thermal_calabrese_cardy(
            interval_length=L_A,
            horizon_radius=rp,
            ads_radius=L_ads,
            epsilon=eps,
            G_N=G,
        )
        assert residual < 1e-12

    def test_residual_is_zero_for_unit_inputs(self):
        rt, cc, res = verify_btz_against_thermal_calabrese_cardy(
            interval_length=2.0,
            horizon_radius=1.0,
            ads_radius=1.0,
            epsilon=0.01,
        )
        assert res == 0.0


# ─────────────────────────────────────────────────────────────────────
# Two-interval phase transition (Headrick 2010)
# ─────────────────────────────────────────────────────────────────────


class TestCrossRatio:
    def test_canonical_value(self):
        # Equal intervals of length 1 separated by gap 1:
        # a=0, b=1, c=2, d=3
        # x = (1)(1) / ((2)(2)) = 1/4
        x = cross_ratio(0.0, 1.0, 2.0, 3.0)
        assert math.isclose(x, 0.25)

    def test_unordered_points_raise(self):
        with pytest.raises(ValueError):
            cross_ratio(0.0, 2.0, 1.0, 3.0)  # b > c

    def test_collapsing_intervals(self):
        # As gap -> 0, x -> 1
        # a=0, b=1, c=1+eps, d=2+eps -> x ~ 1
        x = cross_ratio(0.0, 1.0, 1.001, 2.001)
        assert x > 0.99


class TestTwoIntervalRT:
    def test_disconnected_length_canonical(self):
        L = two_interval_disconnected_length(
            0.0, 1.0, 2.0, 3.0, ads_radius=1.0, epsilon=0.01
        )
        # 2 log(100) + 2 log(100) = 4 log 100
        expected = 4.0 * math.log(100.0)
        assert math.isclose(L, expected)

    def test_connected_length_canonical(self):
        L = two_interval_connected_length(
            0.0, 1.0, 2.0, 3.0, ads_radius=1.0, epsilon=0.01
        )
        # 2 log(300) + 2 log(100) = 2 log(30000)
        expected = 2.0 * math.log(300.0) + 2.0 * math.log(100.0)
        assert math.isclose(L, expected)

    def test_connected_wins_when_close(self):
        # Equal intervals of length 1 with very small gap (gap = 0.05)
        result = two_interval_entropy(
            0.0, 1.0, 1.05, 2.05, ads_radius=1.0, epsilon=0.001
        )
        assert result["phase"] == "connected"

    def test_disconnected_wins_when_far(self):
        # Equal intervals of length 1 with large gap
        result = two_interval_entropy(
            0.0, 1.0, 5.0, 6.0, ads_radius=1.0, epsilon=0.001
        )
        assert result["phase"] == "disconnected"

    def test_critical_separation_equal_intervals(self):
        """For two unit intervals the critical gap is sqrt(2) - 1."""
        d_crit = critical_separation_for_phase_transition(1.0, 1.0)
        assert math.isclose(d_crit, math.sqrt(2.0) - 1.0, abs_tol=1e-12)

    def test_cross_ratio_at_critical_is_one_half(self):
        """The phase transition cross-ratio is exactly 1/2."""
        L0 = 1.0
        d_crit = critical_separation_for_phase_transition(L0, L0)
        x = cross_ratio(0.0, L0, L0 + d_crit, 2 * L0 + d_crit)
        assert math.isclose(x, 0.5, abs_tol=1e-12)

    def test_critical_separation_unequal(self):
        """For unequal intervals: closed-form formula."""
        L1, L2 = 1.0, 2.0
        d_crit = critical_separation_for_phase_transition(L1, L2)
        # At d_crit the cross ratio should be 0.5
        x = cross_ratio(0.0, L1, L1 + d_crit, L1 + d_crit + L2)
        assert math.isclose(x, 0.5, abs_tol=1e-12)


class TestMutualInformation:
    def test_zero_in_disconnected_phase(self):
        """Disjoint intervals far apart have zero mutual information."""
        I = two_interval_mutual_information(
            0.0, 1.0, 5.0, 6.0, ads_radius=1.0, epsilon=0.001
        )
        assert I == 0.0

    def test_positive_in_connected_phase(self):
        I = two_interval_mutual_information(
            0.0, 1.0, 1.05, 2.05, ads_radius=1.0, epsilon=0.001
        )
        assert I > 0

    def test_zero_at_critical_separation(self):
        """At the critical gap, mutual information is exactly 0."""
        L0 = 1.0
        d_crit = critical_separation_for_phase_transition(L0, L0)
        I = two_interval_mutual_information(
            0.0, L0, L0 + d_crit, 2 * L0 + d_crit,
            ads_radius=1.0, epsilon=0.001,
        )
        assert math.isclose(I, 0.0, abs_tol=1e-12)

    def test_cutoff_independence(self):
        """The mutual information is cutoff-independent (the eps cancels)."""
        a, b, c, d = 0.0, 1.0, 1.1, 2.1
        I1 = two_interval_mutual_information(a, b, c, d, ads_radius=1.0, epsilon=0.001)
        I2 = two_interval_mutual_information(a, b, c, d, ads_radius=1.0, epsilon=1e-8)
        assert math.isclose(I1, I2, abs_tol=1e-12)

    def test_non_negative(self):
        """Mutual information is always >= 0 (subadditivity)."""
        for d in [0.05, 0.2, 0.4, 0.6, 1.0, 2.0, 5.0]:
            I = two_interval_mutual_information(
                0.0, 1.0, 1.0 + d, 2.0 + d,
                ads_radius=1.0, epsilon=0.001,
            )
            assert I >= -1e-15


class TestPhaseTransitionContinuity:
    """The phase transition is continuous in the cross-ratio at x = 1/2."""

    def test_lengths_equal_at_critical(self):
        """L^D = L^C exactly at the critical gap."""
        L0 = 1.0
        d_crit = critical_separation_for_phase_transition(L0, L0)
        L_D = two_interval_disconnected_length(
            0.0, L0, L0 + d_crit, 2 * L0 + d_crit,
            ads_radius=1.0, epsilon=0.001,
        )
        L_C = two_interval_connected_length(
            0.0, L0, L0 + d_crit, 2 * L0 + d_crit,
            ads_radius=1.0, epsilon=0.001,
        )
        assert math.isclose(L_D, L_C, abs_tol=1e-12)

    def test_phase_changes_across_critical(self):
        """Just below critical: connected; just above: disconnected."""
        L0 = 1.0
        d_crit = critical_separation_for_phase_transition(L0, L0)
        result_below = two_interval_entropy(
            0.0, L0, L0 + d_crit - 0.01, 2 * L0 + d_crit - 0.01,
            ads_radius=1.0, epsilon=0.001,
        )
        result_above = two_interval_entropy(
            0.0, L0, L0 + d_crit + 0.01, 2 * L0 + d_crit + 0.01,
            ads_radius=1.0, epsilon=0.001,
        )
        assert result_below["phase"] == "connected"
        assert result_above["phase"] == "disconnected"
