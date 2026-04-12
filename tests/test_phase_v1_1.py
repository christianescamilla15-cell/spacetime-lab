"""Tests for v1.1 patch: the evaporating Schwarzschild Page curve.

The v1.0 (Phase 9) island formula module shipped the **eternal** BTZ
Page curve (rises and saturates).  v1.1 extends it to the
**evaporating** Schwarzschild case where the BH actually shrinks and
the radiation entropy returns to zero — the bell-shaped Page curve
that visually demonstrates unitarity.

Every test in this file is pinned to a closed-form invariant from
``spacetime_lab/holography/evaporating.py``:

1. **Schwarzschild evaporation time** (Page 1976): in geometric
   units :math:`G = c = \\hbar = 1`,
   :math:`t_\\text{evap} = 5120\\pi M_0^3`.
2. **Cubic shrinking law**: :math:`M(t) = M_0(1 - t/t_\\text{evap})^{1/3}`,
   with :math:`M(0) = M_0` and :math:`M(t_\\text{evap}) = 0`.
3. **Bekenstein-Hawking entropy**: :math:`S_{BH} = 4\\pi M^2/G_N`.
4. **No-island Hawking saddle**: :math:`S_H(t) = S_{BH}(0) - S_{BH}(t)`,
   monotone increasing from 0 to :math:`S_{BH}(0)`.
5. **Island/QES saddle**: :math:`S_\\text{island}(t) = S_{BH}(t)`,
   monotone decreasing from :math:`S_{BH}(0)` to 0.
6. **Page curve**: :math:`S_\\text{rad} = \\min(S_H, S_\\text{island})`.
7. **Page time** (closed form, no logs): :math:`t_P = (1 -
   \\sqrt{2}/4)\\,t_\\text{evap} \\approx 0.6464\\,t_\\text{evap}`.
8. **Mass at the Page time**: :math:`M(t_P) = M_0/\\sqrt{2}`.
9. **Maximum radiation entropy**: :math:`S_\\text{rad,max} = S_{BH}(0)/2
   = 2\\pi M_0^2/G_N`.
10. **Closed form vs numerical**: ``page_time_evaporating`` and
    ``page_time_evaporating_numerical`` agree to :math:`10^{-10}`.

All tolerances are machine-precision (``abs_tol=1e-12``) unless an
upstream numerical solver introduces broader noise (``brentq``
returns to :math:`10^{-12}`).
"""

import math

import pytest

from spacetime_lab.holography import (
    bekenstein_hawking_entropy,
    hawking_saddle_entropy,
    island_saddle_entropy_evaporating,
    page_curve_evaporating,
    page_time_evaporating,
    page_time_evaporating_numerical,
    schwarzschild_evaporation_time,
    schwarzschild_mass,
    verify_evaporating_unitarity,
)


# ─────────────────────────────────────────────────────────────────────
# Schwarzschild evaporation law (Page 1976)
# ─────────────────────────────────────────────────────────────────────


class TestSchwarzschildEvaporationTime:
    def test_unit_mass_geometric_units(self):
        t = schwarzschild_evaporation_time(1.0)
        assert math.isclose(t, 5120.0 * math.pi, abs_tol=1e-12)

    def test_cubic_scaling_in_initial_mass(self):
        # t_evap ∝ M_0^3 — Page 1976 cubic scaling.
        t1 = schwarzschild_evaporation_time(1.0)
        t2 = schwarzschild_evaporation_time(2.0)
        t3 = schwarzschild_evaporation_time(3.5)
        assert math.isclose(t2, 8.0 * t1, abs_tol=1e-12)
        assert math.isclose(t3, (3.5 ** 3) * t1, abs_tol=1e-12)

    def test_quadratic_scaling_in_G_N(self):
        # In SI form t_evap ∝ G_N^2 M_0^3.
        t_a = schwarzschild_evaporation_time(1.0, G_N=1.0)
        t_b = schwarzschild_evaporation_time(1.0, G_N=2.0)
        assert math.isclose(t_b, 4.0 * t_a, abs_tol=1e-12)

    def test_negative_mass_raises(self):
        with pytest.raises(ValueError):
            schwarzschild_evaporation_time(-1.0)

    def test_zero_mass_raises(self):
        with pytest.raises(ValueError):
            schwarzschild_evaporation_time(0.0)


class TestSchwarzschildMass:
    def test_initial_value(self):
        assert math.isclose(
            schwarzschild_mass(0.0, 1.0), 1.0, abs_tol=1e-12
        )

    def test_evaporated_endpoint_clamped_to_zero(self):
        t_evap = schwarzschild_evaporation_time(1.0)
        assert schwarzschild_mass(t_evap, 1.0) == 0.0

    def test_after_evaporation_returns_zero(self):
        t_evap = schwarzschild_evaporation_time(1.0)
        assert schwarzschild_mass(2.0 * t_evap, 1.0) == 0.0

    def test_cubic_law_at_known_fractions(self):
        # M(t)^3 = M_0^3 (1 - t/t_evap)
        M0 = 1.0
        t_evap = schwarzschild_evaporation_time(M0)
        for f in [0.1, 0.25, 0.5, 0.75, 0.9, 0.99]:
            M = schwarzschild_mass(f * t_evap, M0)
            expected = M0 * (1.0 - f) ** (1.0 / 3.0)
            assert math.isclose(M, expected, abs_tol=1e-12)

    def test_monotonically_decreasing(self):
        M0 = 1.0
        t_evap = schwarzschild_evaporation_time(M0)
        N = 200
        prev = M0 + 1.0
        for i in range(N):
            t = i * t_evap / (N - 1)
            M = schwarzschild_mass(t, M0)
            assert M <= prev + 1e-15
            prev = M

    def test_negative_time_raises(self):
        with pytest.raises(ValueError):
            schwarzschild_mass(-0.1, 1.0)


# ─────────────────────────────────────────────────────────────────────
# Bekenstein-Hawking entropy
# ─────────────────────────────────────────────────────────────────────


class TestBekensteinHawkingEntropy:
    def test_unit_mass(self):
        S = bekenstein_hawking_entropy(1.0)
        assert math.isclose(S, 4.0 * math.pi, abs_tol=1e-12)

    def test_zero_mass_clean(self):
        assert bekenstein_hawking_entropy(0.0) == 0.0

    def test_quadratic_in_mass(self):
        S1 = bekenstein_hawking_entropy(1.0)
        S3 = bekenstein_hawking_entropy(3.0)
        assert math.isclose(S3, 9.0 * S1, abs_tol=1e-12)

    def test_inverse_in_G_N(self):
        S_a = bekenstein_hawking_entropy(1.0, G_N=1.0)
        S_b = bekenstein_hawking_entropy(1.0, G_N=2.0)
        assert math.isclose(S_b, S_a / 2.0, abs_tol=1e-12)


# ─────────────────────────────────────────────────────────────────────
# Hawking and island saddles
# ─────────────────────────────────────────────────────────────────────


class TestHawkingSaddle:
    def test_zero_at_t0(self):
        assert hawking_saddle_entropy(0.0, 1.0) == 0.0

    def test_full_at_t_evap(self):
        M0 = 1.0
        t_evap = schwarzschild_evaporation_time(M0)
        S = hawking_saddle_entropy(t_evap, M0)
        S_BH_0 = bekenstein_hawking_entropy(M0)
        assert math.isclose(S, S_BH_0, abs_tol=1e-12)

    def test_monotonically_increasing(self):
        M0 = 1.0
        t_evap = schwarzschild_evaporation_time(M0)
        N = 500
        prev = -1.0
        for i in range(N):
            t = i * t_evap / (N - 1)
            S = hawking_saddle_entropy(t, M0)
            assert S >= prev - 1e-12
            prev = S

    def test_complementary_to_island_saddle(self):
        # S_H(t) + S_island(t) = S_BH(0) (entropy conservation in
        # the toy model: every bit of BH entropy lost is in the
        # complementary saddle).
        M0 = 1.5
        t_evap = schwarzschild_evaporation_time(M0)
        S_BH_0 = bekenstein_hawking_entropy(M0)
        for f in [0.1, 0.3, 0.5, 0.7, 0.9]:
            t = f * t_evap
            S_H = hawking_saddle_entropy(t, M0)
            S_I = island_saddle_entropy_evaporating(t, M0)
            assert math.isclose(S_H + S_I, S_BH_0, abs_tol=1e-12)


class TestIslandSaddle:
    def test_initial_value_equals_S_BH_0(self):
        M0 = 1.0
        S = island_saddle_entropy_evaporating(0.0, M0)
        assert math.isclose(
            S, bekenstein_hawking_entropy(M0), abs_tol=1e-12
        )

    def test_zero_at_t_evap(self):
        M0 = 1.0
        t_evap = schwarzschild_evaporation_time(M0)
        assert island_saddle_entropy_evaporating(t_evap, M0) == 0.0

    def test_monotonically_decreasing(self):
        M0 = 1.0
        t_evap = schwarzschild_evaporation_time(M0)
        N = 500
        prev = float("inf")
        for i in range(N):
            t = i * t_evap / (N - 1)
            S = island_saddle_entropy_evaporating(t, M0)
            assert S <= prev + 1e-12
            prev = S


# ─────────────────────────────────────────────────────────────────────
# Page curve and Page time
# ─────────────────────────────────────────────────────────────────────


class TestPageCurveEvaporating:
    def test_endpoints_are_zero(self):
        M0 = 1.0
        t_evap = schwarzschild_evaporation_time(M0)
        s0, _ = page_curve_evaporating(0.0, M0)
        sE, _ = page_curve_evaporating(t_evap, M0)
        assert s0 == 0.0
        assert sE == 0.0

    def test_early_phase_is_hawking(self):
        M0 = 1.0
        t_P = page_time_evaporating(M0)
        _, phase = page_curve_evaporating(0.5 * t_P, M0)
        assert phase == "hawking"

    def test_late_phase_is_island(self):
        M0 = 1.0
        t_evap = schwarzschild_evaporation_time(M0)
        t_P = page_time_evaporating(M0)
        # Pick a sample strictly past t_P but well before t_evap.
        t_late = 0.5 * (t_P + t_evap)
        _, phase = page_curve_evaporating(t_late, M0)
        assert phase == "island"

    def test_max_at_page_time_equals_S_BH_0_over_2(self):
        M0 = 1.0
        t_P = page_time_evaporating(M0)
        S_max, _ = page_curve_evaporating(t_P, M0)
        S_BH_0 = bekenstein_hawking_entropy(M0)
        assert math.isclose(S_max, S_BH_0 / 2.0, abs_tol=1e-12)

    def test_max_equals_2_pi_M0_squared(self):
        # Closed-form: S_rad,max = 2 pi M_0^2 in G_N=1 units.
        M0 = 1.5
        t_P = page_time_evaporating(M0)
        S_max, _ = page_curve_evaporating(t_P, M0)
        assert math.isclose(S_max, 2.0 * math.pi * M0 ** 2, abs_tol=1e-12)


class TestPageTimeEvaporating:
    def test_closed_form_value(self):
        # t_P / t_evap = 1 - sqrt(2)/4 ≈ 0.6464
        M0 = 1.0
        t_evap = schwarzschild_evaporation_time(M0)
        t_P = page_time_evaporating(M0)
        ratio = t_P / t_evap
        expected = 1.0 - math.sqrt(2.0) / 4.0
        assert math.isclose(ratio, expected, abs_tol=1e-12)

    def test_after_temporal_midpoint(self):
        # The Page time is *not* at t_evap/2; it sits past it
        # because S_BH ∝ M^2 falls faster than linearly.
        M0 = 1.0
        t_evap = schwarzschild_evaporation_time(M0)
        t_P = page_time_evaporating(M0)
        assert t_P > 0.5 * t_evap
        assert t_P < t_evap

    def test_mass_at_page_time(self):
        M0 = 2.5
        t_P = page_time_evaporating(M0)
        M_at_tP = schwarzschild_mass(t_P, M0)
        assert math.isclose(M_at_tP, M0 / math.sqrt(2.0), abs_tol=1e-12)

    def test_closed_form_matches_numerical(self):
        # Independent verification: brentq on the residual must
        # agree with the closed-form value to 1e-10.
        M0 = 1.0
        t_P_cf = page_time_evaporating(M0)
        t_P_num = page_time_evaporating_numerical(M0)
        assert math.isclose(t_P_cf, t_P_num, abs_tol=1e-10)

    def test_closed_form_matches_numerical_varied_mass(self):
        for M0 in [0.5, 1.0, 1.5, 3.0, 10.0]:
            t_P_cf = page_time_evaporating(M0)
            t_P_num = page_time_evaporating_numerical(M0)
            # brentq xtol=1e-12 on a t_evap ∝ M0^3, so the
            # absolute residual scales with M0^3.  Use a relative
            # tolerance to compare.
            assert math.isclose(t_P_cf, t_P_num, rel_tol=1e-10)

    def test_saddles_equal_at_page_time(self):
        # Continuity: S_H(t_P) = S_island(t_P) bit-exactly.
        M0 = 1.0
        t_P = page_time_evaporating(M0)
        S_H = hawking_saddle_entropy(t_P, M0)
        S_I = island_saddle_entropy_evaporating(t_P, M0)
        assert math.isclose(S_H, S_I, abs_tol=1e-12)


# ─────────────────────────────────────────────────────────────────────
# End-to-end gate: verify_evaporating_unitarity
# ─────────────────────────────────────────────────────────────────────


class TestVerifyEvaporatingUnitarity:
    def test_diagnostics_pass_for_unit_mass(self):
        diag = verify_evaporating_unitarity(1.0, n_samples=2000)
        assert diag["page_time_residual"] < 1e-10
        assert diag["mass_residual"] < 1e-12
        assert diag["continuity_residual"] < 1e-12
        assert diag["max_entropy_residual"] < 1e-12
        assert diag["endpoint_zero_t0"] == 0.0
        assert diag["endpoint_zero_tevap"] == 0.0
        assert diag["phase_ordering_correct"]
        assert diag["bell_shape_monotone"]

    def test_diagnostics_pass_for_varied_mass(self):
        for M0 in [0.5, 1.0, 2.0, 5.0]:
            diag = verify_evaporating_unitarity(M0, n_samples=1000)
            assert diag["continuity_residual"] < 1e-10, M0
            assert diag["max_entropy_residual"] < 1e-10, M0
            assert diag["endpoint_zero_t0"] == 0.0
            assert diag["endpoint_zero_tevap"] == 0.0
            assert diag["phase_ordering_correct"], M0
            assert diag["bell_shape_monotone"], M0

    def test_diagnostics_pass_with_custom_t_evap(self):
        # The shape of the curve must be independent of the t_evap
        # normalisation — only the timescale changes.
        M0 = 1.0
        diag = verify_evaporating_unitarity(
            M0, t_evap=1.0, n_samples=1000
        )
        assert diag["continuity_residual"] < 1e-12
        assert diag["max_entropy_residual"] < 1e-12
        assert diag["bell_shape_monotone"]
        # Page time ratio is independent of t_evap.
        assert math.isclose(
            diag["page_time_closed_form"],
            1.0 - math.sqrt(2.0) / 4.0,
            abs_tol=1e-12,
        )

    def test_max_entropy_equals_half_initial_S_BH(self):
        for M0 in [0.5, 1.0, 1.5, 3.0]:
            diag = verify_evaporating_unitarity(M0, n_samples=500)
            S_BH_0 = bekenstein_hawking_entropy(M0)
            assert math.isclose(
                diag["max_entropy_expected"], S_BH_0 / 2.0,
                abs_tol=1e-12,
            ), M0
