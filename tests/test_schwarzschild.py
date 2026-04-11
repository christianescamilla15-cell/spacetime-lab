"""Tests for the Schwarzschild metric."""

import numpy as np

from spacetime_lab.metrics import Schwarzschild


class TestSchwarzschild:
    """Verify Schwarzschild against known physics."""

    def test_event_horizon_unit_mass(self):
        """Event horizon of M=1 Schwarzschild BH is at r=2."""
        bh = Schwarzschild(mass=1.0)
        assert bh.event_horizon() == 2.0

    def test_event_horizon_arbitrary_mass(self):
        """Event horizon scales linearly with mass."""
        for m in [0.5, 1.0, 2.0, 10.0]:
            bh = Schwarzschild(mass=m)
            assert bh.event_horizon() == 2 * m

    def test_isco(self):
        """ISCO for Schwarzschild is at r=6M."""
        bh = Schwarzschild(mass=1.0)
        assert bh.isco() == 6.0

    def test_photon_sphere(self):
        """Photon sphere for Schwarzschild is at r=3M."""
        bh = Schwarzschild(mass=1.0)
        assert bh.photon_sphere() == 3.0

    def test_negative_mass_raises(self):
        """Negative mass should raise ValueError."""
        import pytest
        with pytest.raises(ValueError):
            Schwarzschild(mass=-1.0)

    def test_metric_tensor_shape(self):
        """Metric tensor is 4x4."""
        bh = Schwarzschild(mass=1.0)
        g = bh.metric_tensor
        assert g.shape == (4, 4)

    def test_metric_numerical_at_equator(self):
        """Evaluate metric at r=3, theta=pi/2."""
        bh = Schwarzschild(mass=1.0)
        g = bh.metric_at(t=0, r=3.0, theta=np.pi / 2, phi=0)

        # g_tt = -(1 - 2/3) = -1/3
        assert np.isclose(g[0, 0], -1/3)
        # g_rr = 1 / (1 - 2/3) = 3
        assert np.isclose(g[1, 1], 3.0)
        # g_theta_theta = r^2 = 9
        assert np.isclose(g[2, 2], 9.0)
        # g_phi_phi = r^2 sin^2(theta) = 9 * 1 = 9
        assert np.isclose(g[3, 3], 9.0)

    def test_metric_signature(self):
        """Schwarzschild has Lorentzian signature (-,+,+,+) at r > 2M."""
        bh = Schwarzschild(mass=1.0)
        g = bh.metric_at(t=0, r=5.0, theta=np.pi / 2, phi=0)
        eigenvalues = np.linalg.eigvalsh(g)
        # One negative (time), three positive (space)
        negative = sum(1 for e in eigenvalues if e < 0)
        positive = sum(1 for e in eigenvalues if e > 0)
        assert negative == 1
        assert positive == 3

    def test_surface_gravity(self):
        """Surface gravity kappa = 1/(4M)."""
        bh = Schwarzschild(mass=1.0)
        assert bh.surface_gravity() == 0.25

    def test_hawking_temperature_proportional_to_inverse_mass(self):
        """T_H scales as 1/M — smaller BHs are hotter."""
        bh1 = Schwarzschild(mass=1.0)
        bh2 = Schwarzschild(mass=2.0)
        T1 = float(bh1.hawking_temperature())
        T2 = float(bh2.hawking_temperature())
        assert np.isclose(T1, 2 * T2)

    def test_entropy_scales_as_mass_squared(self):
        """Bekenstein-Hawking entropy S = 4 pi M^2."""
        bh = Schwarzschild(mass=1.0)
        S = float(bh.bekenstein_hawking_entropy())
        expected = 4 * np.pi
        assert np.isclose(S, expected)

    def test_kretschmann_at_horizon_finite(self):
        """Kretschmann scalar is finite at horizon (confirms coord singularity)."""
        bh = Schwarzschild(mass=1.0)
        K = bh.kretschmann_scalar_at_horizon()
        assert K == 0.75  # 3/(4*1^4) = 0.75
        # And importantly, finite (not infinity)
        assert float(K) < float("inf")

    def test_repr(self):
        """String representation is informative."""
        bh = Schwarzschild(mass=1.0)
        assert "Schwarzschild" in repr(bh)
        assert "mass=1.0" in repr(bh)

    # ──────────────────────────────────────────────────────────────
    # Phase 1 additions: coordinates and geodesics
    # ──────────────────────────────────────────────────────────────

    def test_tortoise_coordinate_outside_horizon(self):
        """Tortoise coordinate is finite outside horizon."""
        bh = Schwarzschild(mass=1.0)
        # At r = 4M, r* = 4 + 2 ln(1) = 4
        r_star = bh.tortoise_coordinate(4.0)
        assert np.isclose(r_star, 4.0)  # 4 + 2*ln(1) = 4

    def test_tortoise_coordinate_diverges_at_horizon(self):
        """Tortoise r* → -∞ as r → 2M+."""
        bh = Schwarzschild(mass=1.0)
        r_star_3 = bh.tortoise_coordinate(3.0)
        r_star_close = bh.tortoise_coordinate(2.01)
        # Close to horizon should be very negative
        assert r_star_close < r_star_3
        assert r_star_close < -5

    def test_tortoise_coordinate_raises_inside_horizon(self):
        """Tortoise is undefined inside horizon."""
        import pytest
        bh = Schwarzschild(mass=1.0)
        with pytest.raises(ValueError):
            bh.tortoise_coordinate(1.0)  # r < 2M

    def test_effective_potential_massive_at_isco(self):
        """V_eff(r=6, L=sqrt(12)) is at max for massive particle — ISCO."""
        bh = Schwarzschild(mass=1.0)
        # Massive particle at ISCO
        L_isco = np.sqrt(12)  # Angular momentum for ISCO
        V = bh.effective_potential(6.0, L_isco, "massive")
        # V_eff = (1 - 1/3)(1 + 12/36) = (2/3)(4/3) = 8/9
        assert np.isclose(float(V), 8/9)

    def test_effective_potential_photon_sphere(self):
        """V_eff_photon has max at r=3M (photon sphere)."""
        bh = Schwarzschild(mass=1.0)
        # Photon at photon sphere
        L = 1.0  # Arbitrary, the max location doesn't depend on L
        V_at_3 = bh.effective_potential(3.0, L, "photon")
        V_at_2_5 = bh.effective_potential(2.5, L, "photon")
        V_at_4 = bh.effective_potential(4.0, L, "photon")
        # Maximum should be at r=3
        assert V_at_3 > V_at_2_5
        assert V_at_3 > V_at_4

    def test_kruskal_exterior_at_t_zero(self):
        """Kruskal coordinates in Region I at t=0: T=0."""
        bh = Schwarzschild(mass=1.0)
        T, X = bh.kruskal_coordinates(t=0, r=3.0, region=1)
        # At t=0, sinh(0)=0, so T=0
        assert np.isclose(T, 0.0)
        # X > 0 for exterior
        assert X > 0

    def test_kruskal_interior(self):
        """Kruskal coordinates in Region II (inside horizon)."""
        bh = Schwarzschild(mass=1.0)
        T, X = bh.kruskal_coordinates(t=0, r=1.0, region=2)
        # At t=0 in Region II, cosh(0)=1 so T > 0
        assert T > 0
        # X = factor * sinh(0) = 0
        assert np.isclose(X, 0.0)

    def test_kruskal_wrong_region_raises(self):
        """Using wrong region for r value raises error."""
        import pytest
        bh = Schwarzschild(mass=1.0)
        # r=3 (exterior) with region=2 should fail
        with pytest.raises(ValueError):
            bh.kruskal_coordinates(t=0, r=3.0, region=2)

    def test_kretschmann_scalar_scaling(self):
        """K(r) scales as r^-6."""
        bh = Schwarzschild(mass=1.0)
        K_at_2 = bh.kretschmann_scalar(2.0)
        K_at_4 = bh.kretschmann_scalar(4.0)
        # K(2)/K(4) should be 64 (2^6)
        assert np.isclose(float(K_at_2) / float(K_at_4), 64.0)

    def test_kretschmann_at_horizon_matches_cached(self):
        """kretschmann_scalar(2M) equals kretschmann_scalar_at_horizon()."""
        bh = Schwarzschild(mass=1.0)
        K_method = bh.kretschmann_scalar(2.0)
        K_cached = bh.kretschmann_scalar_at_horizon()
        assert np.isclose(float(K_method), float(K_cached))

    def test_kretschmann_divergence_at_singularity(self):
        """K(r) → ∞ as r → 0."""
        bh = Schwarzschild(mass=1.0)
        K_close_to_zero = bh.kretschmann_scalar(0.1)
        K_at_horizon = bh.kretschmann_scalar(2.0)
        # K(0.1) should be massively larger than K(2)
        assert K_close_to_zero > 10000 * K_at_horizon

    def test_christoffel_explicit_returns_13_components(self):
        """Should return exactly 13 non-zero components."""
        bh = Schwarzschild()
        explicit = bh.christoffel_symbols_explicit()
        # 13 non-zero components (with symmetries counted separately)
        assert len(explicit) == 13

    def test_christoffel_explicit_matches_computed(self):
        """The explicit formulas match the base class symbolic computation."""
        bh = Schwarzschild()
        # This verifies symbolic Christoffel calculation
        assert bh.verify_christoffel_symbols() is True
