"""Tests for the Kerr metric.

Every assertion is pinned to a closed-form value verified against an
external source (Wikipedia ``Kerr metric``, Bardeen-Press-Teukolsky 1972,
or Leo C. Stein's photon-orbit calculator).  See the file header of
``spacetime_lab/metrics/kerr.py`` for the verification trail.

Conventions used throughout: signature ``(-, +, +, +)``, geometric units
``G = c = 1``, ``a`` is the specific angular momentum ``J / M`` with
``a in [0, M]``.
"""

import math

import numpy as np
import pytest

from spacetime_lab.metrics import Kerr, Schwarzschild


# ─────────────────────────────────────────────────────────────────────
# Construction and validation
# ─────────────────────────────────────────────────────────────────────


class TestConstruction:
    def test_default_spin_is_zero(self):
        k = Kerr(mass=1.0)
        assert k.spin == 0.0

    def test_negative_mass_raises(self):
        with pytest.raises(ValueError):
            Kerr(mass=-1.0, spin=0.0)

    def test_zero_mass_raises(self):
        with pytest.raises(ValueError):
            Kerr(mass=0.0, spin=0.0)

    def test_negative_spin_raises(self):
        with pytest.raises(ValueError):
            Kerr(mass=1.0, spin=-0.1)

    def test_spin_above_mass_raises(self):
        """Cosmic censorship: a > M would give a naked singularity."""
        with pytest.raises(ValueError):
            Kerr(mass=1.0, spin=1.1)

    def test_extremal_spin_allowed(self):
        """spin = mass is the extremal limit and is admissible."""
        k = Kerr(mass=1.0, spin=1.0)
        assert k.spin == 1.0

    def test_repr(self):
        k = Kerr(mass=2.0, spin=0.7)
        s = repr(k)
        assert "Kerr" in s
        assert "mass=2.0" in s
        assert "spin=0.7" in s


# ─────────────────────────────────────────────────────────────────────
# Schwarzschild limit (a = 0)
# ─────────────────────────────────────────────────────────────────────


class TestSchwarzschildLimit:
    """At a = 0 every Kerr quantity must reduce to the Schwarzschild value."""

    def setup_method(self):
        self.k = Kerr(mass=1.0, spin=0.0)
        self.s = Schwarzschild(mass=1.0)

    def test_outer_horizon_is_2M(self):
        assert math.isclose(self.k.outer_horizon(), 2.0)

    def test_inner_horizon_collapses_to_singularity(self):
        assert math.isclose(self.k.inner_horizon(), 0.0)

    def test_isco_prograde_is_6M(self):
        assert math.isclose(self.k.isco(prograde=True), 6.0)

    def test_isco_retrograde_is_6M(self):
        """At a=0 the two ISCO branches must coincide."""
        assert math.isclose(self.k.isco(prograde=False), 6.0)

    def test_photon_sphere_is_3M(self):
        assert math.isclose(self.k.photon_sphere_equatorial(True), 3.0)
        assert math.isclose(self.k.photon_sphere_equatorial(False), 3.0)

    def test_horizon_area_is_16pi_M2(self):
        assert math.isclose(self.k.horizon_area(), 16.0 * math.pi)

    def test_surface_gravity_is_quarter_M(self):
        assert math.isclose(self.k.surface_gravity(), 0.25)

    def test_hawking_temperature_recovers_schwarzschild(self):
        assert math.isclose(self.k.hawking_temperature(), 1.0 / (8.0 * math.pi))

    def test_entropy_recovers_schwarzschild(self):
        assert math.isclose(self.k.bekenstein_hawking_entropy(), 4.0 * math.pi)

    def test_angular_velocity_horizon_is_zero(self):
        assert math.isclose(self.k.angular_velocity_horizon(), 0.0)

    def test_metric_components_match_schwarzschild(self):
        """The whole 4x4 tensor must collapse to diag Schwarzschild form."""
        assert self.k.reduces_to_schwarzschild_at_zero_spin() is True

    def test_metric_at_random_point_matches_schwarzschild(self):
        """Direct numerical comparison at an off-axis, off-equator point."""
        for theta in [0.3, math.pi / 4, math.pi / 3, 1.2]:
            for r in [3.0, 5.0, 10.0]:
                gk = self.k.metric_at(t=0.0, r=r, theta=theta, phi=0.0)
                gs = self.s.metric_at(t=0.0, r=r, theta=theta, phi=0.0)
                assert np.allclose(gk, gs, atol=1e-12)


# ─────────────────────────────────────────────────────────────────────
# Horizons
# ─────────────────────────────────────────────────────────────────────


class TestHorizons:
    @pytest.mark.parametrize(
        "spin,r_plus_expected,r_minus_expected",
        [
            (0.0, 2.0, 0.0),
            (0.5, 1.0 + math.sqrt(0.75), 1.0 - math.sqrt(0.75)),
            (0.8, 1.0 + math.sqrt(0.36), 1.0 - math.sqrt(0.36)),
            (1.0, 1.0, 1.0),
        ],
    )
    def test_horizon_formula(self, spin, r_plus_expected, r_minus_expected):
        k = Kerr(mass=1.0, spin=spin)
        assert math.isclose(k.outer_horizon(), r_plus_expected, abs_tol=1e-12)
        assert math.isclose(k.inner_horizon(), r_minus_expected, abs_tol=1e-12)

    def test_horizons_merge_at_extremal(self):
        k = Kerr(mass=1.0, spin=1.0)
        assert math.isclose(k.outer_horizon(), k.inner_horizon())

    def test_outer_above_inner_in_subextremal(self):
        for a in [0.1, 0.3, 0.5, 0.7, 0.9, 0.99]:
            k = Kerr(mass=1.0, spin=a)
            assert k.outer_horizon() > k.inner_horizon()

    def test_horizon_scales_linearly_with_mass(self):
        for M in [0.5, 1.0, 2.0, 10.0]:
            k = Kerr(mass=M, spin=0.5 * M)  # same dimensionless spin
            k1 = Kerr(mass=1.0, spin=0.5)
            assert math.isclose(k.outer_horizon() / M, k1.outer_horizon())
            assert math.isclose(k.inner_horizon() / M, k1.inner_horizon())


# ─────────────────────────────────────────────────────────────────────
# Ergosphere
# ─────────────────────────────────────────────────────────────────────


class TestErgosphere:
    def test_equator_value_is_2M(self):
        """At theta = pi/2, the ergosphere boundary equals 2M for any spin."""
        for a in [0.0, 0.1, 0.5, 0.9, 1.0]:
            k = Kerr(mass=1.0, spin=a)
            assert math.isclose(k.ergosphere(math.pi / 2), 2.0, abs_tol=1e-12)

    def test_pole_value_equals_outer_horizon(self):
        """At theta = 0 or pi, the static limit coincides with r_+."""
        k = Kerr(mass=1.0, spin=0.6)
        assert math.isclose(k.ergosphere(0.0), k.outer_horizon())
        assert math.isclose(k.ergosphere(math.pi), k.outer_horizon())

    def test_ergosphere_above_outer_horizon_in_between(self):
        """Off the poles, the static limit lies strictly outside r_+."""
        k = Kerr(mass=1.0, spin=0.7)
        for theta in [0.3, math.pi / 4, math.pi / 3, math.pi / 2]:
            assert k.ergosphere(theta) > k.outer_horizon()

    def test_ergosphere_collapses_to_horizon_when_spin_zero(self):
        """In Schwarzschild the ergoregion has zero thickness everywhere."""
        k = Kerr(mass=1.0, spin=0.0)
        for theta in [0.0, 0.4, math.pi / 2, math.pi]:
            assert math.isclose(k.ergosphere(theta), 2.0)


# ─────────────────────────────────────────────────────────────────────
# ISCO — Bardeen, Press & Teukolsky 1972
# ─────────────────────────────────────────────────────────────────────


class TestISCO:
    def test_extremal_prograde_isco_is_M(self):
        k = Kerr(mass=1.0, spin=1.0)
        assert math.isclose(k.isco(prograde=True), 1.0, abs_tol=1e-9)

    def test_extremal_retrograde_isco_is_9M(self):
        k = Kerr(mass=1.0, spin=1.0)
        assert math.isclose(k.isco(prograde=False), 9.0, abs_tol=1e-9)

    def test_prograde_smaller_than_retrograde(self):
        for a in [0.1, 0.3, 0.5, 0.7, 0.9, 0.99]:
            k = Kerr(mass=1.0, spin=a)
            assert k.isco(prograde=True) < k.isco(prograde=False)

    def test_prograde_isco_above_outer_horizon(self):
        for a in [0.0, 0.3, 0.5, 0.9, 0.99]:
            k = Kerr(mass=1.0, spin=a)
            assert k.isco(prograde=True) >= k.outer_horizon()

    def test_prograde_isco_decreases_with_spin(self):
        radii = [Kerr(mass=1.0, spin=a).isco(True) for a in [0.0, 0.2, 0.5, 0.8, 0.99]]
        assert all(r2 < r1 for r1, r2 in zip(radii, radii[1:]))

    def test_retrograde_isco_increases_with_spin(self):
        radii = [
            Kerr(mass=1.0, spin=a).isco(False) for a in [0.0, 0.2, 0.5, 0.8, 0.99]
        ]
        assert all(r2 > r1 for r1, r2 in zip(radii, radii[1:]))

    def test_isco_known_value_a_half(self):
        """Cross-checked with kerr ISCO calculator for a = 0.5 M."""
        k = Kerr(mass=1.0, spin=0.5)
        # Bardeen-Press-Teukolsky direct evaluation:
        chi = 0.5
        Z1 = 1.0 + (1.0 - chi**2) ** (1.0 / 3.0) * (
            (1.0 + chi) ** (1.0 / 3.0) + (1.0 - chi) ** (1.0 / 3.0)
        )
        Z2 = math.sqrt(3.0 * chi**2 + Z1**2)
        expected_pro = 3.0 + Z2 - math.sqrt((3.0 - Z1) * (3.0 + Z1 + 2.0 * Z2))
        expected_retro = 3.0 + Z2 + math.sqrt((3.0 - Z1) * (3.0 + Z1 + 2.0 * Z2))
        assert math.isclose(k.isco(True), expected_pro, abs_tol=1e-12)
        assert math.isclose(k.isco(False), expected_retro, abs_tol=1e-12)


# ─────────────────────────────────────────────────────────────────────
# Equatorial photon sphere
# ─────────────────────────────────────────────────────────────────────


class TestPhotonSphere:
    def test_extremal_prograde_is_M(self):
        k = Kerr(mass=1.0, spin=1.0)
        assert math.isclose(
            k.photon_sphere_equatorial(prograde=True), 1.0, abs_tol=1e-12
        )

    def test_extremal_retrograde_is_4M(self):
        k = Kerr(mass=1.0, spin=1.0)
        assert math.isclose(
            k.photon_sphere_equatorial(prograde=False), 4.0, abs_tol=1e-12
        )

    def test_prograde_smaller_than_retrograde(self):
        for a in [0.1, 0.3, 0.5, 0.7, 0.9]:
            k = Kerr(mass=1.0, spin=a)
            assert k.photon_sphere_equatorial(True) < k.photon_sphere_equatorial(False)

    def test_prograde_above_horizon(self):
        for a in [0.0, 0.3, 0.5, 0.9, 0.99]:
            k = Kerr(mass=1.0, spin=a)
            assert k.photon_sphere_equatorial(True) >= k.outer_horizon()

    def test_below_isco(self):
        """Photon sphere lives strictly inside the ISCO."""
        for a in [0.0, 0.3, 0.5, 0.9]:
            k = Kerr(mass=1.0, spin=a)
            assert k.photon_sphere_equatorial(True) < k.isco(True)
            assert k.photon_sphere_equatorial(False) < k.isco(False)


# ─────────────────────────────────────────────────────────────────────
# Horizon thermodynamics
# ─────────────────────────────────────────────────────────────────────


class TestThermodynamics:
    def test_omega_h_extremal(self):
        """At extremal Kerr, Omega_H = 1 / (2 M)."""
        k = Kerr(mass=1.0, spin=1.0)
        assert math.isclose(k.angular_velocity_horizon(), 0.5)

    def test_surface_gravity_vanishes_at_extremal(self):
        """Third law of BH thermo: kappa -> 0 at extremality."""
        k = Kerr(mass=1.0, spin=1.0)
        assert math.isclose(k.surface_gravity(), 0.0, abs_tol=1e-12)

    def test_temperature_vanishes_at_extremal(self):
        k = Kerr(mass=1.0, spin=1.0)
        assert math.isclose(k.hawking_temperature(), 0.0, abs_tol=1e-12)

    def test_entropy_equals_area_over_4(self):
        for a in [0.0, 0.3, 0.7, 1.0]:
            k = Kerr(mass=1.0, spin=a)
            assert math.isclose(
                k.bekenstein_hawking_entropy(), k.horizon_area() / 4.0
            )

    def test_horizon_area_decreases_with_spin(self):
        """At fixed M, increasing |a| shrinks the outer horizon area."""
        radii = [Kerr(mass=1.0, spin=a).horizon_area() for a in [0.0, 0.5, 0.9]]
        assert radii[0] > radii[1] > radii[2]

    def test_entropy_drops_smoothly_to_extremal(self):
        for a in [0.0, 0.5, 0.9, 1.0]:
            k = Kerr(mass=1.0, spin=a)
            # 4 pi (r_+^2 + a^2)/4 = pi (r_+^2 + a^2)
            expected = math.pi * (k.outer_horizon() ** 2 + a**2)
            assert math.isclose(k.bekenstein_hawking_entropy(), expected)


# ─────────────────────────────────────────────────────────────────────
# Metric tensor structure
# ─────────────────────────────────────────────────────────────────────


class TestMetricTensor:
    def test_shape(self):
        k = Kerr(mass=1.0, spin=0.5)
        g = k.metric_tensor
        assert g.shape == (4, 4)

    def test_symmetric(self):
        k = Kerr(mass=1.0, spin=0.5)
        g = k.metric_tensor
        for i in range(4):
            for j in range(4):
                assert g[i, j] == g[j, i]

    def test_off_diagonal_t_phi_present_for_spin(self):
        """The g_{t phi} term must be non-zero whenever a != 0."""
        k = Kerr(mass=1.0, spin=0.5)
        g_num = k.metric_at(t=0.0, r=4.0, theta=math.pi / 2, phi=0.0)
        # indices: 0=t, 3=phi
        assert abs(g_num[0, 3]) > 1e-6

    def test_off_diagonal_t_phi_absent_when_spin_zero(self):
        k = Kerr(mass=1.0, spin=0.0)
        g_num = k.metric_at(t=0.0, r=4.0, theta=math.pi / 2, phi=0.0)
        assert math.isclose(g_num[0, 3], 0.0, abs_tol=1e-12)

    def test_signature_far_from_horizon(self):
        """Far from the hole the metric must have signature (-,+,+,+)."""
        k = Kerr(mass=1.0, spin=0.5)
        g = k.metric_at(t=0.0, r=20.0, theta=math.pi / 4, phi=0.0)
        eigvals = np.linalg.eigvalsh(g)
        n_neg = sum(1 for e in eigvals if e < 0)
        n_pos = sum(1 for e in eigvals if e > 0)
        assert n_neg == 1
        assert n_pos == 3


# ─────────────────────────────────────────────────────────────────────
# Carter's Killing tensor stub
# ─────────────────────────────────────────────────────────────────────


class TestKillingTensor:
    def test_killing_tensor_is_stub(self):
        """The Killing tensor implementation is deferred to the integrator pass."""
        k = Kerr(mass=1.0, spin=0.5)
        with pytest.raises(NotImplementedError):
            k.killing_tensor()


# ─────────────────────────────────────────────────────────────────────
# Vacuum Einstein equations
# ─────────────────────────────────────────────────────────────────────


class TestVacuum:
    """Strong test of the line element via R_{mu nu} = 0 numerically.

    If any g_{mu nu} component were miswritten, the Ricci tensor would
    not vanish — these tests would explode immediately.  Done
    numerically rather than symbolically because sympy.simplify on Kerr
    expressions is pathologically slow (minutes per component).
    """

    def test_vacuum_at_zero_spin(self):
        k = Kerr(mass=1.0, spin=0.0)
        max_abs = k.verify_vacuum_numerical(atol=1e-10)
        assert max_abs < 1e-10

    def test_vacuum_at_half_spin(self):
        k = Kerr(mass=1.0, spin=0.5)
        max_abs = k.verify_vacuum_numerical(atol=1e-10)
        assert max_abs < 1e-10

    def test_vacuum_at_high_spin(self):
        k = Kerr(mass=1.0, spin=0.9)
        max_abs = k.verify_vacuum_numerical(atol=1e-10)
        assert max_abs < 1e-10

    def test_vacuum_at_extremal(self):
        """Even at extremal Kerr the vacuum equations must hold."""
        k = Kerr(mass=1.0, spin=1.0)
        # At extremal, points right on the horizon (r = M = 1) are
        # singular for the metric but the Ricci tensor outside r_+ is
        # still zero. Use the default sample points which sit outside.
        max_abs = k.verify_vacuum_numerical(atol=1e-10)
        assert max_abs < 1e-10

    def test_vacuum_at_different_mass(self):
        """The vacuum check must be invariant under the choice of M."""
        for M in [0.5, 2.0, 5.0]:
            k = Kerr(mass=M, spin=0.3 * M)
            max_abs = k.verify_vacuum_numerical(atol=1e-10)
            assert max_abs < 1e-10
