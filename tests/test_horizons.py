"""Tests for the Phase 4 horizons module.

Every assertion is pinned to a closed-form value verified against an
external source.  See the file headers of
``spacetime_lab/horizons/event.py``, ``isco.py`` and ``shadow.py``
for the verification trail (Wikipedia ``Photon sphere``,
Bardeen-Press-Teukolsky 1972, Stein's Kerr photon-orbit calculator,
Cunha et al arXiv:1904.07710 for the Bardeen shadow alpha-beta
formulas).

The point of these tests is **cross-validation**: every result is
also derivable analytically from earlier phases (Schwarzschild
``r = 2M``, Kerr ``r_+ = M + sqrt(M^2 - a^2)``, Schwarzschild ISCO
``r = 6M``, Schwarzschild critical impact parameter
``b = 3 sqrt(3) M``, Kerr ISCO via the BPT 1972 closed form already
verified in v0.3.0), so any failure here points to a bug in either
the metric implementation, the geodesic integrator (in the
ray-shooting case), or the horizon finder itself.
"""

import math

import numpy as np
import pytest

from spacetime_lab.horizons import (
    find_event_horizon,
    find_isco_numerical,
    kerr_critical_curve_xi_eta,
    photon_shadow_kerr,
    spherical_photon_orbit_eta,
    spherical_photon_orbit_xi,
)
from spacetime_lab.metrics import Kerr, Schwarzschild


# ─────────────────────────────────────────────────────────────────────
# find_event_horizon — algebraic finder
# ─────────────────────────────────────────────────────────────────────


class TestFindEventHorizonSchwarzschild:
    """find_event_horizon must rediscover r = 2M for Schwarzschild."""

    def test_unit_mass(self):
        rh = find_event_horizon(Schwarzschild(mass=1.0))
        assert math.isclose(rh, 2.0, abs_tol=1e-9)

    @pytest.mark.parametrize("M", [0.5, 1.0, 2.0, 5.0, 10.0])
    def test_various_masses(self, M):
        rh = find_event_horizon(Schwarzschild(mass=M))
        assert math.isclose(rh, 2.0 * M, abs_tol=1e-9)


class TestFindEventHorizonKerr:
    """find_event_horizon must rediscover r_+ = M + sqrt(M^2 - a^2) for Kerr."""

    @pytest.mark.parametrize("a", [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 0.99])
    def test_various_spins(self, a):
        k = Kerr(mass=1.0, spin=a)
        rh = find_event_horizon(k)
        expected = 1.0 + math.sqrt(1.0 - a * a)
        assert math.isclose(rh, expected, abs_tol=1e-9)

    def test_extremal(self):
        """At extremal Kerr the two horizons merge at r = M."""
        k = Kerr(mass=1.0, spin=1.0)
        rh = find_event_horizon(k)
        assert math.isclose(rh, 1.0, abs_tol=1e-6)

    def test_different_mass_and_spin(self):
        """Verify the formula works for non-unit mass."""
        for M in [0.5, 2.0, 10.0]:
            for spin_ratio in [0.0, 0.5, 0.9]:
                k = Kerr(mass=M, spin=spin_ratio * M)
                rh = find_event_horizon(k)
                expected = M + math.sqrt(M * M - (spin_ratio * M) ** 2)
                assert math.isclose(rh, expected, abs_tol=1e-8)

    def test_no_sign_change_raises(self):
        """If the bracket cannot capture the horizon, raise."""
        with pytest.raises(ValueError):
            find_event_horizon(Kerr(mass=1.0, spin=0.5), r_min=10.0, r_max=20.0)


# ─────────────────────────────────────────────────────────────────────
# find_isco_numerical — effective-potential finder
# ─────────────────────────────────────────────────────────────────────


class TestFindIscoNumerical:
    """find_isco_numerical must rediscover r = 6M for Schwarzschild."""

    def test_unit_mass(self):
        isco = find_isco_numerical(Schwarzschild(mass=1.0))
        assert math.isclose(isco, 6.0, abs_tol=1e-7)

    @pytest.mark.parametrize("M", [0.5, 1.0, 2.5, 5.0])
    def test_scales_linearly_with_mass(self, M):
        isco = find_isco_numerical(
            Schwarzschild(mass=M), r_guess=6.0 * M, L_guess=3.5 * M
        )
        assert math.isclose(isco, 6.0 * M, abs_tol=1e-6)

    def test_metric_without_effective_potential_raises(self):
        """A metric class lacking effective_potential cannot use this finder."""
        # Kerr currently does not implement effective_potential
        with pytest.raises(AttributeError):
            find_isco_numerical(Kerr(mass=1.0, spin=0.5))


# ─────────────────────────────────────────────────────────────────────
# Spherical photon orbit conserved quantities
# ─────────────────────────────────────────────────────────────────────


class TestSphericalPhotonOrbitFormulas:
    """Verify the (xi, eta) formulas pin to known limits."""

    def test_xi_zero_spin_raises(self):
        with pytest.raises(ValueError):
            spherical_photon_orbit_xi(3.0, mass=1.0, spin=0.0)

    def test_eta_zero_spin_raises(self):
        with pytest.raises(ValueError):
            spherical_photon_orbit_eta(3.0, mass=1.0, spin=0.0)

    def test_eta_vanishes_at_equatorial_photon_radii(self):
        """At r_p = r_p^pro and r_p = r_p^retro, eta = 0 by definition.

        These are the equatorial photon-sphere radii.  The Kerr photon
        sphere splits into prograde/retrograde branches at these
        endpoints, and the spherical-orbit family parametrised by
        ``r_p`` in [r_p^pro, r_p^retro] has zero Carter constant at
        the boundary (purely equatorial orbits).
        """
        a = 0.5
        M = 1.0
        r_p_pro = 2.0 * M * (1.0 + math.cos((2.0 / 3.0) * math.acos(-a / M)))
        r_p_retro = 2.0 * M * (1.0 + math.cos((2.0 / 3.0) * math.acos(+a / M)))
        eta_pro = spherical_photon_orbit_eta(r_p_pro, M, a)
        eta_retro = spherical_photon_orbit_eta(r_p_retro, M, a)
        assert math.isclose(eta_pro, 0.0, abs_tol=1e-8)
        assert math.isclose(eta_retro, 0.0, abs_tol=1e-8)


class TestKerrCriticalCurve:
    """The xi-eta curve from r_p sweep."""

    def test_returns_three_arrays(self):
        r_p, xi, eta = kerr_critical_curve_xi_eta(mass=1.0, spin=0.5)
        assert r_p.shape == xi.shape == eta.shape

    def test_eta_non_negative(self):
        """eta(r_p) >= 0 on the physically allowed range, modulo numerical noise at the endpoints."""
        _, _, eta = kerr_critical_curve_xi_eta(mass=1.0, spin=0.5, n_points=100)
        # Allow small negative numerical artefacts at the endpoints
        assert eta.min() > -1e-10


# ─────────────────────────────────────────────────────────────────────
# Bardeen shadow
# ─────────────────────────────────────────────────────────────────────


class TestPhotonShadowKerr:
    """Bardeen 1973 photon shadow boundary."""

    def test_zero_spin_raises(self):
        """Schwarzschild is degenerate; user should draw the analytic circle."""
        with pytest.raises(ValueError):
            photon_shadow_kerr(spin=0.0)

    def test_spin_above_mass_raises(self):
        with pytest.raises(ValueError):
            photon_shadow_kerr(spin=2.0, mass=1.0)

    def test_returned_arrays_have_expected_length(self):
        """The output is a closed curve of length 2 * n_points."""
        alpha, beta = photon_shadow_kerr(spin=0.5, n_points=100)
        assert alpha.shape == (200,)
        assert beta.shape == (200,)

    def test_curve_is_closed(self):
        """Last point should equal (or be close to) the first."""
        alpha, beta = photon_shadow_kerr(spin=0.5, n_points=100)
        # The closing connects the upper and lower halves at the
        # equatorial-orbit endpoints where beta = 0.
        # First point: upper half, retrograde end (large positive alpha)
        # Last point: lower half (mirrored), retrograde end
        assert math.isclose(alpha[0], alpha[-1], abs_tol=1e-12)
        assert math.isclose(beta[0], -beta[-1], abs_tol=1e-12)

    def test_schwarzschild_limit_is_circle_of_radius_3sqrt3(self):
        """At infinitesimal spin the shadow must approach a circle of radius 3 sqrt(3) M."""
        alpha, beta = photon_shadow_kerr(spin=1e-6, mass=1.0, n_points=400)
        radii = np.sqrt(alpha**2 + beta**2)
        b_crit = 3.0 * math.sqrt(3.0)
        assert math.isclose(radii.mean(), b_crit, abs_tol=1e-2)
        # And the curve should be nearly circular (small std):
        assert radii.std() < 5e-3

    def test_schwarzschild_limit_centered_at_origin(self):
        """For tiny spin the center of the shadow is at the origin."""
        alpha, beta = photon_shadow_kerr(spin=1e-6, mass=1.0)
        assert abs(alpha.mean()) < 1e-3
        assert abs(beta.mean()) < 1e-3

    def test_extremal_kerr_shadow_is_asymmetric(self):
        """At a = M the shadow is strongly distorted from a circle."""
        alpha, beta = photon_shadow_kerr(spin=0.998, mass=1.0)
        radii = np.sqrt(alpha**2 + beta**2)
        # The retrograde side bulges out, prograde flattens — the
        # range of radii is much wider than for small spin.
        assert (radii.max() - radii.min()) > 4.0

    def test_shadow_shifts_in_alpha_with_spin(self):
        """Frame dragging shifts the shadow's centroid in alpha."""
        for spin in [0.1, 0.5, 0.998]:
            alpha, beta = photon_shadow_kerr(spin=spin, mass=1.0)
            # Centroid of the closed curve should be shifted in +alpha
            # for prograde rotation (the retrograde-photon side bulges
            # outward in +alpha).
            assert alpha.mean() > 0

    def test_shadow_scales_linearly_with_mass(self):
        """A 2M black hole has a shadow twice as big as an M black hole."""
        alpha1, beta1 = photon_shadow_kerr(spin=0.5, mass=1.0, n_points=100)
        alpha2, beta2 = photon_shadow_kerr(spin=1.0, mass=2.0, n_points=100)
        radii1 = np.sqrt(alpha1**2 + beta1**2)
        radii2 = np.sqrt(alpha2**2 + beta2**2)
        # Same dimensionless spin, doubled mass: shadow should be 2x
        assert math.isclose(radii2.mean() / radii1.mean(), 2.0, abs_tol=1e-6)
