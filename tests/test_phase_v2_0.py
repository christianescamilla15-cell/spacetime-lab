"""Tests for v2.0 patch: real QES formalism + replica wormholes + higher-d RT.

v2.0 is the most ambitious of the five-patch sprint.  Adds three
new modules to ``spacetime_lab.holography``:

1. ``qes.py`` — generic 1-parameter QES finder, JT dilaton + matter
   CFT toy, island formula min.
2. ``replica.py`` — disconnected + connected replica saddles,
   verification that they reproduce Phase 9 saddles bit-exactly.
3. ``minimal_surfaces.py`` — higher-d RT strip area, closed form +
   numerical integration, verified against each other across
   dimensions 2–6.

Tests pinned to closed-form invariants where possible, to
machine-precision residuals where those invariants reduce to the
same numerical computation.
"""

import math

import pytest

from spacetime_lab.holography import (
    # QES module
    QESResult,
    connected_saddle_entropy,
    # Replica module
    disconnected_saddle_entropy,
    extremize_generalized_entropy,
    find_qes,
    island_formula_min,
    jt_dilaton,
    jt_dilaton_derivative,
    jt_generalized_entropy,
    jt_generalized_entropy_derivative,
    no_island_saddle_entropy,
    replica_island_saddle,
    # Minimal surfaces module
    rt_strip_area_numerical,
    rt_strip_area_pure_ads,
    thermal_cft_interval_entropy,
    verify_qes_formalism,
    verify_replica_at_n_equals_1,
    verify_rt_strip_against_closed_form,
)
from spacetime_lab.holography.island import (
    hartman_maldacena_growth_rate,
    island_saddle_entropy,
)


# ─────────────────────────────────────────────────────────────────────
# qes.py
# ─────────────────────────────────────────────────────────────────────


class TestJTDilaton:
    def test_value_at_horizon(self):
        # phi(0) = phi_0
        assert math.isclose(
            jt_dilaton(0.0, phi_0=2.5, phi_r=7.0, beta=1.0),
            2.5,
            abs_tol=1e-12,
        )

    def test_saturates_at_infinity(self):
        # phi(a → ∞) → phi_0 + phi_r
        v = jt_dilaton(100.0, phi_0=2.5, phi_r=7.0, beta=1.0)
        assert math.isclose(v, 2.5 + 7.0, abs_tol=1e-6)

    def test_monotone_increasing(self):
        prev = -math.inf
        for a in [0.0, 0.1, 0.5, 1.0, 2.0, 5.0]:
            v = jt_dilaton(a, phi_0=1.0, phi_r=3.0, beta=1.0)
            assert v > prev - 1e-12
            prev = v

    def test_derivative_closed_form(self):
        # dphi/da = phi_r π/β · sech²(πa/β); compare to centered FD
        phi_r, beta = 3.0, 1.0
        for a in [0.1, 0.5, 1.0]:
            h = 1e-6
            fd = (
                jt_dilaton(a + h, 0.0, phi_r, beta)
                - jt_dilaton(a - h, 0.0, phi_r, beta)
            ) / (2 * h)
            cl = jt_dilaton_derivative(a, phi_r, beta)
            assert math.isclose(fd, cl, rel_tol=1e-6)


class TestThermalCFTInterval:
    def test_interval_positive_at_large_length(self):
        # At large L = b - a, sinh^2 → very large, so S is dominated
        # by the positive log term and is positive.
        S = thermal_cft_interval_entropy(
            a=0.0, b=5.0, beta=1.0, central_charge=1.0, epsilon=0.01
        )
        assert S > 0

    def test_invalid_ordering_raises(self):
        with pytest.raises(ValueError, match="b > a"):
            thermal_cft_interval_entropy(
                a=1.0, b=0.5, beta=1.0, central_charge=1.0,
                epsilon=0.01,
            )


class TestFindQES:
    def test_qes_exists_with_balanced_defaults(self):
        qes = find_qes(
            phi_0=1.0, phi_r=10.0, beta=1.0, central_charge=1.0,
            b=2.0, epsilon=0.01,
        )
        assert isinstance(qes, QESResult)
        assert 0.0 < qes.a_qes < 2.0
        assert qes.residual < 1e-10

    def test_residual_exactly_zero_at_qes(self):
        qes = find_qes(
            phi_0=1.0, phi_r=10.0, beta=1.0, central_charge=1.0,
            b=2.0, epsilon=0.01,
        )
        # dS_gen/da at a_qes must vanish to brentq tolerance
        d = jt_generalized_entropy_derivative(
            qes.a_qes, phi_r=10.0, beta=1.0, central_charge=1.0,
            b=2.0,
        )
        assert abs(d) < 1e-10

    def test_increasing_phi_r_pushes_qes_outward(self):
        # Larger dilaton coupling (stronger area penalty) moves the
        # QES further from the horizon toward the bath boundary.
        a_small = find_qes(
            phi_0=0.0, phi_r=5.0, beta=1.0, central_charge=1.0,
            b=2.0, epsilon=0.01,
        ).a_qes
        a_large = find_qes(
            phi_0=0.0, phi_r=50.0, beta=1.0, central_charge=1.0,
            b=2.0, epsilon=0.01,
        ).a_qes
        assert a_large > a_small

    def test_no_qes_in_bracket_raises(self):
        # With tiny phi_r the derivative is negative everywhere →
        # no zero on the default bracket, finder raises.
        with pytest.raises(ValueError, match="does not change sign"):
            find_qes(
                phi_0=0.0, phi_r=0.01, beta=1.0, central_charge=6.0,
                b=2.0, epsilon=0.01,
            )


class TestExtremizeGenericAPI:
    def test_finds_zero_of_arbitrary_function(self):
        # User-supplied S_gen = (a - 1)^2, derivative = 2(a - 1), zero at 1
        r = extremize_generalized_entropy(
            s_gen=lambda a: (a - 1.0) ** 2,
            ds_gen_da=lambda a: 2.0 * (a - 1.0),
            bracket=(0.1, 5.0),
        )
        assert math.isclose(r.a_qes, 1.0, abs_tol=1e-10)
        assert math.isclose(r.s_gen_at_qes, 0.0, abs_tol=1e-20)


class TestIslandFormulaMin:
    def test_returns_dict_with_winner(self):
        d = island_formula_min(
            phi_0=1.0, phi_r=10.0, beta=1.0, central_charge=1.0,
            b=2.0, epsilon=0.01,
        )
        assert d["winner"] in {"no-island", "island"}
        assert d["s_rad"] == min(d["s_no_island"], d["s_island"])


class TestVerifyQESFormalism:
    def test_default_gate_passes(self):
        diag = verify_qes_formalism()
        assert diag["a_qes_in_bounds"]
        assert diag["second_derivative_nonzero"]
        assert diag["qes_residual"] < 1e-10
        assert diag["winner"] in {"no-island", "island"}


# ─────────────────────────────────────────────────────────────────────
# replica.py
# ─────────────────────────────────────────────────────────────────────


class TestDisconnectedSaddle:
    def test_zero_at_t0(self):
        assert disconnected_saddle_entropy(
            0.0, beta=2 * math.pi, central_charge=6.0
        ) == 0.0

    def test_linear_growth_slope(self):
        # dS_disc/dt = 2 π c / (3 β)
        beta, c = 2 * math.pi, 6.0
        slope = (
            disconnected_saddle_entropy(1.0, beta, c)
            - disconnected_saddle_entropy(0.0, beta, c)
        )
        expected = 2 * math.pi * c / (3 * beta)
        assert math.isclose(slope, expected, abs_tol=1e-12)

    def test_matches_phase9_HM_late_time(self):
        # Must match Phase 9's hartman_maldacena_growth_rate exactly
        beta, c = 3.0, 4.0
        slope = (
            disconnected_saddle_entropy(1.0, beta, c)
            - disconnected_saddle_entropy(0.0, beta, c)
        )
        phase9 = hartman_maldacena_growth_rate(
            central_charge=c, beta=beta
        )
        assert math.isclose(slope, phase9, abs_tol=1e-12)

    def test_negative_t_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            disconnected_saddle_entropy(-0.1, 1.0, 1.0)


class TestConnectedSaddle:
    def test_matches_phase9_island_saddle(self):
        # 2 S_BH = π r_+ / G_N matches island_saddle_entropy exactly
        r_plus = 2.5
        s_conn = connected_saddle_entropy(r_plus)
        s_phase9 = island_saddle_entropy(r_plus)
        assert math.isclose(s_conn, s_phase9, abs_tol=1e-12)

    def test_scales_linearly_with_horizon_radius(self):
        s1 = connected_saddle_entropy(1.0)
        s3 = connected_saddle_entropy(3.0)
        assert math.isclose(s3, 3.0 * s1, abs_tol=1e-12)

    def test_inverse_in_G_N(self):
        s1 = connected_saddle_entropy(1.0, G_N=1.0)
        s2 = connected_saddle_entropy(1.0, G_N=2.0)
        assert math.isclose(s2, s1 / 2.0, abs_tol=1e-12)


class TestReplicaIslandSaddle:
    def test_disconnected_wins_early(self):
        d = replica_island_saddle(
            t=0.1, horizon_radius=1.0, beta=2 * math.pi,
            central_charge=6.0,
        )
        assert d["winner"] == "disconnected"

    def test_connected_wins_late(self):
        d = replica_island_saddle(
            t=10.0, horizon_radius=1.0, beta=2 * math.pi,
            central_charge=6.0,
        )
        assert d["winner"] == "connected"

    def test_page_time_closed_form(self):
        # t_P = 3 β r_+ / (2 c G_N)
        beta, r_plus, c, G_N = 2 * math.pi, 1.0, 6.0, 1.0
        d = replica_island_saddle(1.0, r_plus, beta, c, G_N=G_N)
        expected = 3.0 * beta * r_plus / (2.0 * c * G_N)
        assert math.isclose(d["page_time"], expected, abs_tol=1e-12)

    def test_saddles_equal_at_page_time(self):
        beta, r_plus, c = 2 * math.pi, 1.0, 6.0
        t_P = 3 * beta * r_plus / (2 * c * 1.0)
        d = replica_island_saddle(t_P, r_plus, beta, c)
        assert math.isclose(d["s_disc"], d["s_conn"], abs_tol=1e-12)


class TestVerifyReplicaAtN1:
    def test_all_residuals_zero(self):
        diag = verify_replica_at_n_equals_1()
        assert diag["saddle_residual"] == 0.0
        assert diag["slope_residual"] == 0.0

    def test_varied_params(self):
        for r_plus in [0.5, 1.0, 2.5]:
            for beta in [math.pi, 2 * math.pi, 4 * math.pi]:
                diag = verify_replica_at_n_equals_1(
                    horizon_radius=r_plus,
                    beta=beta,
                    central_charge=3.0,
                )
                assert diag["saddle_residual"] < 1e-12
                assert diag["slope_residual"] < 1e-12


# ─────────────────────────────────────────────────────────────────────
# minimal_surfaces.py
# ─────────────────────────────────────────────────────────────────────


class TestRTStripClosedForm:
    def test_d2_matches_ads3_geodesic(self):
        # For d=2: A = 2 L_AdS log(L/ε)
        L, eps = 3.0, 0.01
        A = rt_strip_area_pure_ads(L, eps, d=2)
        assert math.isclose(A, 2.0 * math.log(L / eps), abs_tol=1e-12)

    def test_d3_uv_divergence_scaling(self):
        # For d=3: A_UV ~ 2 L_AdS² / (d-2) · 1/ε^(d-2) = 2 / ε
        # Specifically, the 1/ε piece should have coefficient 2.
        L, eps_small = 2.0, 0.001
        L_finite = rt_strip_area_pure_ads(L, eps_small, d=3)
        L_smaller_eps = rt_strip_area_pure_ads(L, eps_small / 2, d=3)
        # Delta A should ~ 2 · (1/(eps/2) - 1/eps) = 2/eps
        delta = L_smaller_eps - L_finite
        expected = 2.0 * (1.0 / (eps_small / 2) - 1.0 / eps_small)
        assert math.isclose(delta, expected, rel_tol=1e-6)

    def test_invalid_epsilon_raises(self):
        with pytest.raises(ValueError):
            rt_strip_area_pure_ads(1.0, 1.0, d=3)  # eps >= L/2


class TestRTStripNumerical:
    def test_matches_closed_form_d2(self):
        L, eps = 2.0, 0.01
        cl = rt_strip_area_pure_ads(L, eps, d=2)
        nm = rt_strip_area_numerical(L, eps, d=2)
        assert math.isclose(cl, nm, rel_tol=1e-4)

    def test_matches_closed_form_d3(self):
        L, eps = 2.0, 0.01
        cl = rt_strip_area_pure_ads(L, eps, d=3)
        nm = rt_strip_area_numerical(L, eps, d=3)
        assert math.isclose(cl, nm, rel_tol=1e-8)

    def test_matches_closed_form_d4(self):
        L, eps = 2.0, 0.01
        cl = rt_strip_area_pure_ads(L, eps, d=4)
        nm = rt_strip_area_numerical(L, eps, d=4)
        assert math.isclose(cl, nm, rel_tol=1e-4)

    def test_matches_closed_form_d5(self):
        L, eps = 2.0, 0.01
        cl = rt_strip_area_pure_ads(L, eps, d=5)
        nm = rt_strip_area_numerical(L, eps, d=5)
        assert math.isclose(cl, nm, rel_tol=1e-6)


class TestVerifyRTStrip:
    def test_all_dimensions_under_tolerance(self):
        diag = verify_rt_strip_against_closed_form(
            L=2.0, epsilon=0.01, dimensions_to_check=(2, 3, 4, 5, 6)
        )
        for d, r in diag.items():
            assert r["rel_residual"] < 1e-3, (d, r)


# ─────────────────────────────────────────────────────────────────────
# Cross-module sanity
# ─────────────────────────────────────────────────────────────────────


class TestCrossModuleConsistency:
    def test_replica_connected_matches_island_saddle_phase9(self):
        # The entire point of the replica derivation is to reproduce
        # Phase 9's island saddle bit-exactly.
        for r_plus in [0.7, 1.0, 2.0]:
            assert math.isclose(
                connected_saddle_entropy(r_plus),
                island_saddle_entropy(r_plus),
                abs_tol=1e-12,
            )

    def test_rt_strip_d2_recovers_calabrese_cardy(self):
        # In d=2, RT strip area = 2 log(L/ε).
        # Calabrese-Cardy entropy: (c/3) log(L/ε) = A/(4 G_N) with
        # c = 3 L_AdS / (2 G_N) and L_AdS = 1, G_N arbitrary.
        # So 2 log(L/ε) = (2 c G_N / 3) · log(L/ε) / G_N means
        # the RT area divided by 4 G_N equals (1/(2 G_N)) · log(L/ε),
        # matching (c/3) log(L/ε) at c = 3 / (2 G_N).  Consistency
        # check: the explicit formula 2 log(L/ε) is exactly what
        # Phase 7 uses.
        for L in [0.5, 2.0, 10.0]:
            A = rt_strip_area_pure_ads(L=L, epsilon=0.01, d=2)
            assert math.isclose(
                A, 2.0 * math.log(L / 0.01), abs_tol=1e-12
            )


# ─────────────────────────────────────────────────────────────────────
# Silence unused-import warnings for re-exports we don't call directly
# ─────────────────────────────────────────────────────────────────────


_ = (no_island_saddle_entropy, jt_generalized_entropy)
