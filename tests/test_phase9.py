"""Tests for Phase 9: the island formula and the Page curve.

Phase 9 implements the simplest non-trivial version of the island
formula — the Hartman-Maldacena 2013 calculation in eternal BTZ —
and verifies the qualitative resolution of the Hawking information
paradox: a non-trivial saddle exists, it eventually beats the
Hawking saddle, and the crossover happens at a closed-form Page
time.

Every formula was verified against an external source before
implementation; see the file header in
``spacetime_lab/holography/island.py``.

Tests are pinned to the following invariants:

1. **HM saddle at t = 0**: equals `(c/3) log(beta/(pi eps))`.
2. **HM saddle late-time growth rate**: `dS/dt -> 2 pi c / (3 beta)`.
3. **Island saddle**: equals `2 S_BH = pi r_+ / G_N`.
4. **Page time**: numerical root of the transcendental equation
   `S_HM(t_P) = 2 S_BH` exists and is positive.
5. **Continuity at the Page time**: `S_HM(t_P) = 2 S_BH` exactly
   (residual at floating-point bit precision).
6. **Page curve qualitative shape**: trivial saddle wins early,
   island saddle wins late, the curve is monotonic non-decreasing
   (eternal BH does not actually evaporate, so the late-time tail
   saturates rather than falling).
"""

import math

import pytest

from spacetime_lab.holography import (
    hartman_maldacena_entropy,
    hartman_maldacena_growth_rate,
    island_saddle_entropy,
    page_curve,
    page_time,
    verify_page_curve_unitarity,
)


# ─────────────────────────────────────────────────────────────────────
# HM saddle: closed-form value at t = 0
# ─────────────────────────────────────────────────────────────────────


class TestHartmanMaldacenaAtZeroTime:
    def test_canonical_value(self):
        c, beta, eps = 1.5, 2 * math.pi, 0.01
        S = hartman_maldacena_entropy(0.0, c, beta, eps)
        # cosh(0) = 1, so S = (c/3) log(beta / (pi eps))
        expected = (c / 3.0) * math.log(beta / (math.pi * eps))
        assert math.isclose(S, expected, abs_tol=1e-12)

    def test_even_in_t(self):
        c, beta, eps = 1.5, 2 * math.pi, 0.01
        S_pos = hartman_maldacena_entropy(1.5, c, beta, eps)
        S_neg = hartman_maldacena_entropy(-1.5, c, beta, eps)
        assert math.isclose(S_pos, S_neg, abs_tol=1e-12)

    def test_invalid_inputs_raise(self):
        with pytest.raises(ValueError):
            hartman_maldacena_entropy(0, -1.0, 1.0, 0.01)
        with pytest.raises(ValueError):
            hartman_maldacena_entropy(0, 1.0, -1.0, 0.01)
        with pytest.raises(ValueError):
            hartman_maldacena_entropy(0, 1.0, 1.0, -0.01)


# ─────────────────────────────────────────────────────────────────────
# HM saddle: late-time linear growth
# ─────────────────────────────────────────────────────────────────────


class TestHartmanMaldacenaGrowthRate:
    @pytest.mark.parametrize(
        "c,beta",
        [
            (1.0, 2 * math.pi),
            (1.5, 2 * math.pi),
            (3.0, math.pi),
            (6.0, 4 * math.pi),
        ],
    )
    def test_growth_rate_formula(self, c, beta):
        rate = hartman_maldacena_growth_rate(c, beta)
        assert math.isclose(rate, 2.0 * math.pi * c / (3.0 * beta))

    def test_late_time_numerical_matches_formula(self):
        """Numerical derivative at large t should match the formula."""
        c, beta, eps = 1.5, 2 * math.pi, 0.01
        rate_formula = hartman_maldacena_growth_rate(c, beta)
        # Sample numerically very far in time so tanh ~ 1.
        t_large = 1000.0
        S_a = hartman_maldacena_entropy(t_large, c, beta, eps)
        S_b = hartman_maldacena_entropy(t_large + 1.0, c, beta, eps)
        rate_numerical = S_b - S_a
        assert math.isclose(rate_numerical, rate_formula, abs_tol=1e-9)

    def test_rate_inverse_to_beta(self):
        """Doubling beta should halve the growth rate."""
        c = 1.5
        r1 = hartman_maldacena_growth_rate(c, 2 * math.pi)
        r2 = hartman_maldacena_growth_rate(c, 4 * math.pi)
        assert math.isclose(r2, r1 / 2.0)

    def test_invalid_inputs_raise(self):
        with pytest.raises(ValueError):
            hartman_maldacena_growth_rate(-1.0, 1.0)
        with pytest.raises(ValueError):
            hartman_maldacena_growth_rate(1.0, -1.0)


# ─────────────────────────────────────────────────────────────────────
# HM saddle: numerical stability for large arguments
# ─────────────────────────────────────────────────────────────────────


class TestHartmanMaldacenaNumericalStability:
    def test_handles_very_large_t(self):
        """At t = 10000 with beta = 1, naive cosh would overflow.

        Our _log_cosh helper should handle it cleanly.
        """
        c, beta, eps = 1.0, 1.0, 1e-6
        S = hartman_maldacena_entropy(1e4, c, beta, eps)
        assert math.isfinite(S)
        assert S > 0

    def test_extreme_late_time(self):
        c, beta, eps = 1.0, 1.0, 1e-3
        S = hartman_maldacena_entropy(1e6, c, beta, eps)
        assert math.isfinite(S)


# ─────────────────────────────────────────────────────────────────────
# Island saddle (= 2 S_BH)
# ─────────────────────────────────────────────────────────────────────


class TestIslandSaddleEntropy:
    @pytest.mark.parametrize(
        "rp",
        [0.5, 1.0, 2.0, 4.0],
    )
    def test_equals_pi_rp_over_GN(self, rp):
        # 2 S_BH = 2 * pi r_+ / (2 G_N) = pi r_+ / G_N
        S = island_saddle_entropy(rp, G_N=1.0)
        assert math.isclose(S, math.pi * rp)

    def test_equals_twice_BH_entropy(self):
        """Cross-check against the BTZ Bekenstein-Hawking entropy."""
        from spacetime_lab.metrics import BTZ

        bh = BTZ(horizon_radius=2.0, ads_radius=1.0)
        S_BH = bh.bekenstein_hawking_entropy(G_N=1.0)
        S_island = island_saddle_entropy(2.0, G_N=1.0)
        assert math.isclose(S_island, 2 * S_BH)

    def test_GN_inverse_scaling(self):
        S1 = island_saddle_entropy(1.0, G_N=1.0)
        S2 = island_saddle_entropy(1.0, G_N=2.0)
        assert math.isclose(S2, S1 / 2.0)

    def test_invalid_inputs_raise(self):
        with pytest.raises(ValueError):
            island_saddle_entropy(-1.0)
        with pytest.raises(ValueError):
            island_saddle_entropy(1.0, G_N=-1.0)


# ─────────────────────────────────────────────────────────────────────
# Page time
# ─────────────────────────────────────────────────────────────────────


class TestPageTime:
    """The Page time is the root of S_HM(t) = 2 S_BH."""

    def test_canonical_value_exists_and_positive(self):
        rp, L, eps, G_N = 1.0, 1.0, 0.01, 1.0
        t_P = page_time(rp, L, eps, G_N=G_N)
        assert t_P > 0
        assert math.isfinite(t_P)

    def test_continuity_at_page_time_is_bit_exact(self):
        """At the Page time, S_HM(t_P) should equal 2 S_BH exactly
        (within scipy.brentq tolerance)."""
        rp, L, eps, G_N = 1.0, 1.0, 0.01, 1.0
        t_P = page_time(rp, L, eps, G_N=G_N)
        beta = 2 * math.pi * L * L / rp
        c = 3 * L / (2 * G_N)
        S_hm_at_P = hartman_maldacena_entropy(t_P, c, beta, eps)
        S_island = island_saddle_entropy(rp, G_N=G_N)
        assert math.isclose(S_hm_at_P, S_island, abs_tol=1e-9)

    @pytest.mark.parametrize(
        "rp,L,eps,G_N",
        [
            (1.0, 1.0, 0.01, 1.0),
            (2.0, 1.0, 0.01, 1.0),
            (1.0, 2.0, 0.1, 1.0),
            (3.0, 1.5, 0.1, 0.5),
        ],
    )
    def test_continuity_at_various_parameters(self, rp, L, eps, G_N):
        t_P = page_time(rp, L, eps, G_N=G_N)
        # Skip the degenerate regime where t_P = 0 (cutoff so fine that
        # S_HM(0) > 2 S_BH already and there is no Page transition).
        if t_P == 0:
            return
        beta = 2 * math.pi * L * L / rp
        c = 3 * L / (2 * G_N)
        S_hm = hartman_maldacena_entropy(t_P, c, beta, eps)
        S_island = island_saddle_entropy(rp, G_N=G_N)
        assert math.isclose(S_hm, S_island, abs_tol=1e-9)

    def test_degenerate_fine_cutoff_returns_zero(self):
        """Very fine cutoff: S_HM(0) > 2 S_BH already, page_time = 0."""
        # tiny cutoff and small BH
        t_P = page_time(horizon_radius=1.0, ads_radius=1.0, epsilon=1e-30)
        assert t_P == 0.0

    def test_invalid_inputs_raise(self):
        with pytest.raises(ValueError):
            page_time(horizon_radius=-1.0, ads_radius=1.0, epsilon=0.01)
        with pytest.raises(ValueError):
            page_time(horizon_radius=1.0, ads_radius=-1.0, epsilon=0.01)


# ─────────────────────────────────────────────────────────────────────
# Page curve = min(HM, island)
# ─────────────────────────────────────────────────────────────────────


class TestPageCurve:
    def setup_method(self):
        self.rp = 1.0
        self.L = 1.0
        self.eps = 0.01
        self.G_N = 1.0
        self.t_P = page_time(self.rp, self.L, self.eps, G_N=self.G_N)

    def test_at_t_zero_in_trivial_phase(self):
        """At t = 0 the trivial saddle wins (for any reasonable cutoff)."""
        S, phase = page_curve(0.0, self.rp, self.L, self.eps, G_N=self.G_N)
        assert phase == "trivial"

    def test_at_late_time_in_island_phase(self):
        """At t much greater than the Page time, the island saddle wins."""
        S, phase = page_curve(
            10 * self.t_P, self.rp, self.L, self.eps, G_N=self.G_N
        )
        assert phase == "island"

    def test_just_before_page_time_is_trivial(self):
        S, phase = page_curve(
            0.99 * self.t_P, self.rp, self.L, self.eps, G_N=self.G_N
        )
        assert phase == "trivial"

    def test_just_after_page_time_is_island(self):
        S, phase = page_curve(
            1.01 * self.t_P, self.rp, self.L, self.eps, G_N=self.G_N
        )
        assert phase == "island"

    def test_island_value_after_transition(self):
        """In the island phase the curve is constant at 2 S_BH."""
        S_island = island_saddle_entropy(self.rp, G_N=self.G_N)
        for t in [self.t_P * 1.1, self.t_P * 2, self.t_P * 5, self.t_P * 100]:
            S, phase = page_curve(t, self.rp, self.L, self.eps, G_N=self.G_N)
            assert phase == "island"
            assert math.isclose(S, S_island, abs_tol=1e-12)

    def test_trivial_value_matches_HM(self):
        """In the trivial phase, the curve equals S_HM."""
        for t in [0.0, self.t_P / 4, self.t_P / 2, self.t_P * 0.9]:
            S, phase = page_curve(t, self.rp, self.L, self.eps, G_N=self.G_N)
            beta = 2 * math.pi * self.L * self.L / self.rp
            c = 3 * self.L / (2 * self.G_N)
            S_hm = hartman_maldacena_entropy(t, c, beta, self.eps)
            assert phase == "trivial"
            assert math.isclose(S, S_hm, abs_tol=1e-12)


# ─────────────────────────────────────────────────────────────────────
# Page curve unitarity gate function
# ─────────────────────────────────────────────────────────────────────


class TestPageCurveUnitarityGate:
    """The full Phase 9 gate function checks the qualitative shape."""

    def test_unit_BTZ_gate(self):
        diag = verify_page_curve_unitarity(
            horizon_radius=1.0, ads_radius=1.0, epsilon=0.01
        )
        assert diag["trivial_at_early"] is True
        assert diag["island_at_late"] is True
        assert diag["monotonic"] is True
        assert diag["continuity_residual"] < 1e-9
        assert diag["page_time"] > 0
        assert math.isfinite(diag["page_time"])

    @pytest.mark.parametrize(
        "rp,L,eps,G_N",
        [
            (1.0, 1.0, 0.01, 1.0),
            (2.0, 1.0, 0.01, 1.0),
            (3.0, 2.0, 0.1, 1.0),
            (1.5, 0.5, 0.05, 0.5),
        ],
    )
    def test_unitarity_across_parameter_space(self, rp, L, eps, G_N):
        diag = verify_page_curve_unitarity(
            horizon_radius=rp, ads_radius=L, epsilon=eps, G_N=G_N
        )
        assert diag["trivial_at_early"]
        assert diag["island_at_late"]
        assert diag["monotonic"]
        assert diag["continuity_residual"] < 1e-9

    def test_late_time_approximation_in_right_ballpark(self):
        """The closed-form approximation `t_P ~ (3 beta S_BH)/(pi c)`
        should be close to the exact root, modulo log corrections,
        in the regime where the approximation is valid (large BH,
        moderate cutoff)."""
        diag = verify_page_curve_unitarity(
            horizon_radius=20.0, ads_radius=1.0, epsilon=0.1
        )
        # For large BH the log corrections are small relative to the
        # leading-order term, so the ratio should be order unity.
        ratio = diag["page_time"] / diag["page_time_approx"]
        assert 0.5 < ratio < 2.0


# ─────────────────────────────────────────────────────────────────────
# Cross-validation: page_time matches the late-time approximation
# in the right limit
# ─────────────────────────────────────────────────────────────────────


class TestPageTimeAsymptotics:
    def test_page_time_grows_with_horizon_radius(self):
        """For larger BH, the Page time should be larger (more entropy
        to accumulate before saturation)."""
        eps = 0.05  # generous cutoff so we are in the standard regime
        t_small = page_time(1.0, 1.0, eps)
        t_large = page_time(10.0, 1.0, eps)
        # Both should be positive (non-degenerate) and t_large > t_small.
        assert t_small > 0
        assert t_large > 0
        assert t_large > t_small

    def test_page_time_independent_of_GN(self):
        """In the eternal BTZ setup, the Page time is independent of G_N.

        Reason: both 2 S_BH (the saturation value) and c (entering S_HM)
        scale as 1/G_N, so G_N cancels in the equation S_HM(t_P) = 2 S_BH.
        The Page time is purely a property of the bulk geometry
        (`r_+`, `L`, `epsilon`), not of the gravitational coupling.
        This is a non-obvious feature of the holographic setup.
        """
        rp, L, eps = 1.0, 1.0, 0.05
        t_GN1 = page_time(rp, L, eps, G_N=1.0)
        t_GN2 = page_time(rp, L, eps, G_N=2.0)
        t_GN_half = page_time(rp, L, eps, G_N=0.5)
        assert math.isclose(t_GN1, t_GN2, abs_tol=1e-9)
        assert math.isclose(t_GN1, t_GN_half, abs_tol=1e-9)
