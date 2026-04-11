"""Tests for the Schwarzschild metric."""

import numpy as np
import sympy as sp

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
