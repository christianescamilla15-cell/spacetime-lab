"""Tests for v1.3 patch: rotating BTZ + extremal + ergoregion.

The v1.3 patch adds ``spacetime_lab.holography.btz_rotating`` with
the full two-parameter ``(M, J)`` family of BTZ solutions.  Tests
pinned to closed-form invariants:

1. **Horizon formulas**: ``r_±² = 4 G_N L² M (1 ± √(1 - (J/ML)²))``.
2. **Convention match**: ``r_+² + r_-² = 8 G_N L² M`` and
   ``r_+ r_- = 4 G_N L J``.
3. **Non-rotating limit**: ``J = 0`` ⟹ ``r_- = 0`` and ``r_+ = √(8 G_N L² M)``.
4. **Extremal limit**: ``|J| = ML`` ⟹ ``r_+ = r_-`` and ``T_H = 0``.
5. **Extremal bound**: ``|J| > ML`` raises ``ValueError`` (no horizon).
6. **Horizon inversion**: ``(r_+, r_-) → (M, J) → (r_+, r_-)`` is bit-exact.
7. **Thermodynamics**: ``T_H = (r_+² - r_-²)/(2π r_+ L²)``,
   ``Ω_H = r_-/(r_+ L)``, ``S_BH = π r_+/(2 G_N)``.
8. **First law**: finite differences of ``M(S, J)`` match ``T_H``
   and ``Ω_H`` to ``rel_tol=1e-6``.
9. **Smarr 2+1D**: ``M = ½ T_H S + Ω_H J`` bit-exactly.
10. **Rotating Strominger-Cardy**: ``S_BH = 2π√(c L_0/6) + 2π√(c L̄_0/6)``
    with ``L_0 = (LM+J)/2``, ``L̄_0 = (LM-J)/2``, bit-exactly.
11. **Ergoregion**: outer bound = ``√(r_+² + r_-²)`` = ``√(8 G_N L² M)``.
"""

import math

import pytest

from spacetime_lab.holography import (
    extremal_bound_J,
    is_extremal,
    rotating_btz_angular_momentum_from_horizons,
    rotating_btz_angular_velocity,
    rotating_btz_entropy,
    rotating_btz_ergoregion_bounds,
    rotating_btz_hawking_temperature,
    rotating_btz_horizons,
    rotating_btz_mass_from_horizons,
    strominger_rotating_btz_cardy,
    verify_first_law,
    verify_rotating_btz_thermodynamics,
    verify_smarr_2plus1,
)
from spacetime_lab.holography.btz import (
    verify_strominger_btz_cardy,
)


# ─────────────────────────────────────────────────────────────────────
# Horizon formulas + convention match
# ─────────────────────────────────────────────────────────────────────


class TestHorizonFormulas:
    def test_non_rotating_reduces_to_sqrt_8_G_N_L2_M(self):
        r_plus, r_minus = rotating_btz_horizons(
            mass=1.0, angular_momentum=0.0, ads_radius=1.0, G_N=1.0
        )
        assert math.isclose(r_plus, math.sqrt(8.0), abs_tol=1e-12)
        assert r_minus == 0.0

    def test_sum_of_squares_equals_8_G_N_L2_M(self):
        for M in [0.5, 1.0, 2.5, 10.0]:
            for J_frac in [0.0, 0.1, 0.5, 0.9]:
                L = 1.0
                G_N = 1.0
                J = J_frac * extremal_bound_J(M, L)
                r_p, r_m = rotating_btz_horizons(
                    M, J, L, G_N=G_N
                )
                lhs = r_p * r_p + r_m * r_m
                rhs = 8.0 * G_N * L * L * M
                assert math.isclose(lhs, rhs, abs_tol=1e-12), (M, J)

    def test_product_of_horizons_equals_4_G_N_L_J(self):
        for M in [0.5, 1.0, 2.5]:
            for J_frac in [0.1, 0.5, 0.9]:
                L, G_N = 1.0, 1.0
                J = J_frac * extremal_bound_J(M, L)
                r_p, r_m = rotating_btz_horizons(M, J, L, G_N=G_N)
                lhs = r_p * r_m
                rhs = 4.0 * G_N * L * abs(J)
                assert math.isclose(lhs, rhs, abs_tol=1e-12), (M, J)

    def test_r_plus_greater_equal_r_minus(self):
        for J_frac in [0.0, 0.3, 0.7, 0.99]:
            J = J_frac * extremal_bound_J(1.0, 1.0)
            r_p, r_m = rotating_btz_horizons(1.0, J, 1.0)
            assert r_p >= r_m

    def test_G_N_scaling(self):
        # r_+^2 ∝ G_N, so r_+(2 G_N) = sqrt(2) * r_+(G_N)
        r_p1, _ = rotating_btz_horizons(1.0, 0.3, 1.0, G_N=1.0)
        r_p2, _ = rotating_btz_horizons(1.0, 0.3, 1.0, G_N=2.0)
        assert math.isclose(r_p2, math.sqrt(2.0) * r_p1, abs_tol=1e-12)


# ─────────────────────────────────────────────────────────────────────
# Extremal limit
# ─────────────────────────────────────────────────────────────────────


class TestExtremal:
    def test_extremal_bound_equals_ML(self):
        for M in [0.5, 1.0, 3.0]:
            for L in [0.5, 1.0, 2.0]:
                assert math.isclose(
                    extremal_bound_J(M, L), M * L, abs_tol=1e-12
                )

    def test_horizons_coincide_at_extremal(self):
        M, L = 2.0, 1.0
        J = extremal_bound_J(M, L)  # J = ML
        r_p, r_m = rotating_btz_horizons(M, J, L)
        assert math.isclose(r_p, r_m, abs_tol=1e-12)

    def test_temperature_zero_at_extremal(self):
        M, L = 2.0, 1.0
        J = extremal_bound_J(M, L)
        T = rotating_btz_hawking_temperature(M, J, L)
        assert abs(T) < 1e-12

    def test_over_extremal_raises(self):
        M, L = 1.0, 1.0
        J_over = 1.001 * extremal_bound_J(M, L)
        with pytest.raises(ValueError, match=r"\|J\|"):
            rotating_btz_horizons(M, J_over, L)

    def test_is_extremal_detects(self):
        M, L = 1.5, 1.0
        J_ext = extremal_bound_J(M, L)
        assert is_extremal(M, J_ext, L)
        assert is_extremal(M, -J_ext, L)
        assert not is_extremal(M, 0.5 * J_ext, L)


# ─────────────────────────────────────────────────────────────────────
# Inversion: (r_+, r_-) ↔ (M, J) round-trip
# ─────────────────────────────────────────────────────────────────────


class TestHorizonInversion:
    def test_mass_from_horizons_roundtrip(self):
        for M in [0.1, 1.0, 5.0]:
            for J_frac in [0.0, 0.2, 0.8]:
                L, G_N = 1.0, 1.0
                J = J_frac * extremal_bound_J(M, L)
                r_p, r_m = rotating_btz_horizons(M, J, L, G_N=G_N)
                M_rt = rotating_btz_mass_from_horizons(
                    r_p, r_m, L, G_N=G_N
                )
                assert math.isclose(M_rt, M, abs_tol=1e-12), (M, J)

    def test_angular_momentum_from_horizons_roundtrip(self):
        for J_frac in [0.0, 0.2, 0.8]:
            L, G_N, M = 1.0, 1.0, 1.5
            J = J_frac * extremal_bound_J(M, L)
            r_p, r_m = rotating_btz_horizons(M, J, L, G_N=G_N)
            J_rt = rotating_btz_angular_momentum_from_horizons(
                r_p, r_m, L, G_N=G_N
            )
            # J is non-negative in the inverse relation; compare absolute value.
            assert math.isclose(J_rt, abs(J), abs_tol=1e-12)


# ─────────────────────────────────────────────────────────────────────
# Thermodynamic quantities
# ─────────────────────────────────────────────────────────────────────


class TestThermodynamicQuantities:
    def test_T_H_non_rotating_matches_non_rotating_btz(self):
        # T_H for rotating BTZ with J=0 should equal r_+/(2 π L²)
        M, L = 2.0, 1.0
        r_p, r_m = rotating_btz_horizons(M, 0.0, L)
        T_expected = r_p / (2.0 * math.pi * L * L)
        T_actual = rotating_btz_hawking_temperature(M, 0.0, L)
        assert math.isclose(T_actual, T_expected, abs_tol=1e-12)

    def test_Omega_H_non_rotating_is_zero(self):
        Om = rotating_btz_angular_velocity(
            mass=1.0, angular_momentum=0.0, ads_radius=1.0
        )
        assert Om == 0.0

    def test_Omega_H_sign_matches_J_sign(self):
        M, L = 1.0, 1.0
        Om_pos = rotating_btz_angular_velocity(M, 0.5, L)
        Om_neg = rotating_btz_angular_velocity(M, -0.5, L)
        assert Om_pos > 0
        assert Om_neg < 0
        assert math.isclose(Om_pos, -Om_neg, abs_tol=1e-12)

    def test_Omega_H_formula(self):
        # Ω_H = r_-/(r_+ L)
        M, J, L = 1.5, 1.0, 1.0
        r_p, r_m = rotating_btz_horizons(M, J, L)
        Om_expected = r_m / (r_p * L)
        Om_actual = rotating_btz_angular_velocity(M, J, L)
        assert math.isclose(Om_actual, Om_expected, abs_tol=1e-12)

    def test_entropy_matches_non_rotating(self):
        # S_BH depends only on r_+, so for the same r_+, different J
        # settings should give the same entropy.  Equivalently, for
        # non-rotating BTZ it must match pi r_+ / (2 G_N).
        M, L = 2.0, 1.0
        r_p, _ = rotating_btz_horizons(M, 0.0, L)
        S_expected = math.pi * r_p / 2.0
        S_actual = rotating_btz_entropy(M, 0.0, L)
        assert math.isclose(S_actual, S_expected, abs_tol=1e-12)

    def test_all_quantities_finite_away_from_extremal(self):
        M, J, L = 1.0, 0.5, 1.0
        T = rotating_btz_hawking_temperature(M, J, L)
        Om = rotating_btz_angular_velocity(M, J, L)
        S = rotating_btz_entropy(M, J, L)
        for v in (T, Om, S):
            assert math.isfinite(v)


# ─────────────────────────────────────────────────────────────────────
# First law: dM = T dS + Ω dJ
# ─────────────────────────────────────────────────────────────────────


class TestFirstLaw:
    def test_first_law_at_mid_J(self):
        diag = verify_first_law(
            mass=1.0, angular_momentum=0.5, ads_radius=1.0, G_N=1.0
        )
        assert diag["dM_dS_rel_residual"] < 1e-6
        assert diag["dM_dJ_rel_residual"] < 1e-6

    def test_first_law_many_points(self):
        for M in [0.5, 1.0, 2.0]:
            for J_frac in [0.1, 0.4, 0.8]:
                J = J_frac * extremal_bound_J(M, 1.0)
                diag = verify_first_law(M, J, 1.0)
                assert diag["dM_dS_rel_residual"] < 1e-6, (M, J)
                assert diag["dM_dJ_rel_residual"] < 1e-6, (M, J)


# ─────────────────────────────────────────────────────────────────────
# Smarr 2+1D: M = ½ T S + Ω J
# ─────────────────────────────────────────────────────────────────────


class TestSmarr:
    def test_smarr_exact_away_from_extremal(self):
        for M in [0.5, 1.0, 2.5]:
            for J_frac in [0.0, 0.3, 0.7]:
                J = J_frac * extremal_bound_J(M, 1.0)
                diag = verify_smarr_2plus1(M, J, 1.0)
                assert diag["residual"] < 1e-12, (M, J)

    def test_smarr_exact_at_negative_J(self):
        diag = verify_smarr_2plus1(1.0, -0.3, 1.0)
        assert diag["residual"] < 1e-12

    def test_smarr_exact_near_extremal(self):
        M, L = 1.0, 1.0
        J = 0.9999 * extremal_bound_J(M, L)
        diag = verify_smarr_2plus1(M, J, L)
        assert diag["residual"] < 1e-12


# ─────────────────────────────────────────────────────────────────────
# Rotating Strominger-Cardy
# ─────────────────────────────────────────────────────────────────────


class TestRotatingStromingerCardy:
    def test_exact_match_various(self):
        for M in [0.5, 1.0, 2.0, 5.0]:
            for J_frac in [0.0, 0.3, 0.7, 0.95]:
                L, G_N = 1.0, 1.0
                J = J_frac * extremal_bound_J(M, L)
                diag = strominger_rotating_btz_cardy(
                    M, J, L, G_N=G_N
                )
                assert diag["residual"] < 1e-12, (M, J)

    def test_left_right_weights(self):
        # L_0 = (LM + |J|)/2, L̄_0 = (LM - |J|)/2
        M, J, L = 2.0, 0.5, 1.0
        diag = strominger_rotating_btz_cardy(M, J, L)
        assert math.isclose(
            diag["l_0_left"], (L * M + abs(J)) / 2.0, abs_tol=1e-12
        )
        assert math.isclose(
            diag["l_0_right"], (L * M - abs(J)) / 2.0, abs_tol=1e-12
        )

    def test_central_charge_is_brown_henneaux(self):
        L, G_N = 1.0, 1.0
        diag = strominger_rotating_btz_cardy(1.0, 0.2, L, G_N=G_N)
        assert math.isclose(
            diag["c"], 3.0 * L / (2.0 * G_N), abs_tol=1e-12
        )

    def test_reduces_to_non_rotating_at_J_zero(self):
        # At J=0, L_0 = bar L_0 = ML/2 and the sum of two identical
        # Cardy terms must equal the Phase 8 non-rotating formula.
        M, L, G_N = 1.0, 1.0, 1.0
        rotating = strominger_rotating_btz_cardy(M, 0.0, L, G_N=G_N)
        # Phase 8 path
        r_plus, _ = rotating_btz_horizons(M, 0.0, L, G_N=G_N)
        s_bh_ph8, s_cardy_ph8, residual_ph8 = (
            verify_strominger_btz_cardy(
                r_plus, L, G_N=G_N
            )
        )
        assert math.isclose(
            rotating["s_bh"], s_bh_ph8, abs_tol=1e-12
        )
        assert math.isclose(
            rotating["s_cardy_total"], s_cardy_ph8, abs_tol=1e-12
        )


# ─────────────────────────────────────────────────────────────────────
# Ergoregion
# ─────────────────────────────────────────────────────────────────────


class TestErgoregion:
    def test_ergoregion_inner_is_outer_horizon(self):
        M, J, L = 1.0, 0.3, 1.0
        r_in, r_out = rotating_btz_ergoregion_bounds(M, J, L)
        r_p, _ = rotating_btz_horizons(M, J, L)
        assert math.isclose(r_in, r_p, abs_tol=1e-12)

    def test_ergoregion_outer_is_static_limit(self):
        # r_erg^2 = r_+^2 + r_-^2 = 8 G_N L^2 M
        M, J, L, G_N = 1.0, 0.3, 1.0, 1.0
        _, r_out = rotating_btz_ergoregion_bounds(M, J, L, G_N=G_N)
        expected = math.sqrt(8.0 * G_N * L * L * M)
        assert math.isclose(r_out, expected, abs_tol=1e-12)

    def test_ergoregion_collapses_at_zero_J(self):
        # Non-rotating: r_+ = r_erg (no ergoregion)
        M, L = 1.0, 1.0
        r_in, r_out = rotating_btz_ergoregion_bounds(M, 0.0, L)
        assert math.isclose(r_in, r_out, abs_tol=1e-12)

    def test_ergoregion_is_nontrivial_at_nonzero_J(self):
        M, J, L = 1.0, 0.5, 1.0
        r_in, r_out = rotating_btz_ergoregion_bounds(M, J, L)
        assert r_out > r_in


# ─────────────────────────────────────────────────────────────────────
# End-to-end gate
# ─────────────────────────────────────────────────────────────────────


class TestEndToEndGate:
    def test_gate_passes_at_typical_point(self):
        diag = verify_rotating_btz_thermodynamics(
            mass=1.0, angular_momentum=0.5, ads_radius=1.0, G_N=1.0
        )
        assert diag["mass_roundtrip_residual"] < 1e-12
        assert diag["angular_momentum_roundtrip_residual"] < 1e-12
        assert diag["first_law_dM_dS_rel_residual"] < 1e-6
        assert diag["first_law_dM_dJ_rel_residual"] < 1e-6
        assert diag["smarr_residual"] < 1e-12
        assert diag["strominger_cardy_residual"] < 1e-12

    def test_gate_passes_for_varied_M_and_J(self):
        for M in [0.3, 1.0, 5.0]:
            for J_frac in [0.0, 0.4, 0.9]:
                J = J_frac * extremal_bound_J(M, 1.0)
                diag = verify_rotating_btz_thermodynamics(
                    M, J, 1.0
                )
                assert diag["smarr_residual"] < 1e-10, (M, J)
                assert diag["strominger_cardy_residual"] < 1e-10, (
                    M,
                    J,
                )

    def test_gate_varied_G_N_and_L(self):
        # The physics should be independent of the choice of units
        for G_N in [0.5, 1.0, 3.0]:
            for L in [0.5, 1.0, 2.0]:
                diag = verify_rotating_btz_thermodynamics(
                    mass=1.0,
                    angular_momentum=0.3,
                    ads_radius=L,
                    G_N=G_N,
                )
                assert diag["smarr_residual"] < 1e-10
                assert diag["strominger_cardy_residual"] < 1e-10
