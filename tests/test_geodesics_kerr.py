"""Tests for the Kerr geodesic integrator and Carter's constant.

The defining property of the Kerr geodesic system is that it is
**Liouville-integrable**: in addition to the obvious conserved
quantities (E, L_z, mass-shell), there is a fourth one — Carter's
constant — that comes from an *irreducible* Killing tensor, not from
any continuous symmetry.

These tests pin down two things:

1. The :class:`spacetime_lab.geodesics.GeodesicIntegrator`
   (implicit-midpoint) is symplectic and 2nd-order.
2. Carter's constant, computed via the polynomial form
   :meth:`Kerr.carter_constant_from_state`, is conserved along
   integrated geodesics — to the same precision as the
   Hamiltonian itself.

Together they constitute the experimental verification that Kerr is
genuinely Liouville-integrable.
"""

import math

import numpy as np
import pytest

from spacetime_lab.geodesics import GeodesicIntegrator, GeodesicState
from spacetime_lab.metrics import Kerr


# ─────────────────────────────────────────────────────────────────────
# GeodesicState dataclass
# ─────────────────────────────────────────────────────────────────────


class TestGeodesicState:
    def test_construction(self):
        s = GeodesicState(x=[0.0, 10.0, 1.4, 0.0], p=[-1.0, 0.0, 1.5, 3.0])
        assert s.x.shape == (4,)
        assert s.p.shape == (4,)
        assert s.x[1] == 10.0
        assert s.p[3] == 3.0

    def test_wrong_shape_raises(self):
        with pytest.raises(ValueError):
            GeodesicState(x=[0, 1, 2], p=[0, 0, 0, 0])
        with pytest.raises(ValueError):
            GeodesicState(x=[0, 1, 2, 3], p=[0, 0])

    def test_copy_is_independent(self):
        s = GeodesicState(x=[0, 10, 1.5, 0], p=[-1, 0, 0, 3])
        c = s.copy()
        c.x[0] = 999.0
        assert s.x[0] == 0.0  # original unchanged

    def test_arrays_are_copied_not_aliased(self):
        x = np.array([0.0, 10.0, 1.4, 0.0])
        p = np.array([-1.0, 0.0, 1.5, 3.0])
        s = GeodesicState(x=x, p=p)
        x[0] = 999.0  # mutate the input
        assert s.x[0] == 0.0  # state should not be affected


# ─────────────────────────────────────────────────────────────────────
# GeodesicIntegrator construction and basic operations
# ─────────────────────────────────────────────────────────────────────


def _generic_kerr_state() -> tuple[Kerr, GeodesicState]:
    """A generic timelike-ish initial state for an a=0.5 Kerr BH."""
    bh = Kerr(mass=1.0, spin=0.5)
    state = GeodesicState(
        x=np.array([0.0, 10.0, 1.4, 0.0]),
        p=np.array([-0.97, 0.0, 1.5, 3.0]),
    )
    return bh, state


class TestIntegratorBasics:
    def test_construction(self):
        bh = Kerr(mass=1.0, spin=0.5)
        integrator = GeodesicIntegrator(bh)
        assert integrator.metric is bh

    def test_hamiltonian_returns_float(self):
        bh, state = _generic_kerr_state()
        integrator = GeodesicIntegrator(bh)
        H = integrator.hamiltonian(state)
        assert isinstance(H, float)

    def test_velocity_shape(self):
        bh, state = _generic_kerr_state()
        integrator = GeodesicIntegrator(bh)
        v = integrator.velocity(state)
        assert v.shape == (4,)

    def test_force_shape(self):
        bh, state = _generic_kerr_state()
        integrator = GeodesicIntegrator(bh)
        f = integrator.force(state)
        assert f.shape == (4,)

    def test_step_returns_new_state(self):
        bh, state = _generic_kerr_state()
        integrator = GeodesicIntegrator(bh)
        new = integrator.step(state, h=0.1)
        assert isinstance(new, GeodesicState)
        # Time should advance
        assert new.x[0] != state.x[0]

    def test_integrate_returns_n_plus_1_states(self):
        bh, state = _generic_kerr_state()
        integrator = GeodesicIntegrator(bh)
        states = integrator.integrate(state, h=0.5, n_steps=10)
        assert len(states) == 11

    def test_negative_n_steps_raises(self):
        bh, state = _generic_kerr_state()
        integrator = GeodesicIntegrator(bh)
        with pytest.raises(ValueError):
            integrator.integrate(state, h=0.1, n_steps=-1)


# ─────────────────────────────────────────────────────────────────────
# Cyclic-coordinate exact conservation: E and L_z
# ─────────────────────────────────────────────────────────────────────


class TestKillingVectorConservation:
    """E = -p_t and L_z = p_phi must be conserved to machine precision.

    Boyer-Lindquist Kerr does not depend on t or phi, so the conjugate
    momenta p_t and p_phi are exactly preserved by the equations of
    motion.  The implicit-midpoint method preserves this exactly.
    """

    def setup_method(self):
        self.bh, self.state = _generic_kerr_state()
        self.integrator = GeodesicIntegrator(self.bh)
        self.states = self.integrator.integrate(self.state, h=0.5, n_steps=200)

    def test_E_conserved_to_machine_precision(self):
        Es = np.array([-s.p[0] for s in self.states])
        max_dev = np.max(np.abs(Es - Es[0]))
        assert max_dev < 1e-12, f"E drifted by {max_dev}"

    def test_Lz_conserved_to_machine_precision(self):
        Lzs = np.array([s.p[3] for s in self.states])
        max_dev = np.max(np.abs(Lzs - Lzs[0]))
        assert max_dev < 1e-12, f"L_z drifted by {max_dev}"


# ─────────────────────────────────────────────────────────────────────
# Mass-shell preservation (Hamiltonian)
# ─────────────────────────────────────────────────────────────────────


class TestMassShellConservation:
    """The Hamiltonian H = -mu^2/2 should drift only by O(h^2) per step.

    This is the standard symplectic-integrator property: H is not
    exactly conserved, but a "modified" H is, and the true H stays
    close to it for exponentially long times.
    """

    def setup_method(self):
        self.bh, self.state = _generic_kerr_state()
        self.integrator = GeodesicIntegrator(self.bh)

    def test_drift_is_small(self):
        states = self.integrator.integrate(self.state, h=0.5, n_steps=200)
        H_vals = np.array([self.integrator.hamiltonian(s) for s in states])
        max_rel_drift = np.max(np.abs(H_vals - H_vals[0])) / abs(H_vals[0])
        assert max_rel_drift < 1e-3, f"H drifted by {max_rel_drift}"

    def test_drift_scales_quadratically_with_step_size(self):
        """Halving h should reduce H drift by a factor of about 4."""
        drifts = []
        for h in [1.0, 0.5, 0.25]:
            n_steps = int(round(50.0 / h))  # same total lambda
            states = self.integrator.integrate(self.state, h=h, n_steps=n_steps)
            H_vals = np.array([self.integrator.hamiltonian(s) for s in states])
            drifts.append(np.max(np.abs(H_vals - H_vals[0])) / abs(H_vals[0]))
        # Each drift should be roughly 1/4 of the previous one
        ratio_1 = drifts[0] / drifts[1]
        ratio_2 = drifts[1] / drifts[2]
        # 2nd order means ratio of 4; allow generous tolerance
        assert 2.0 < ratio_1 < 8.0, f"first ratio = {ratio_1}"
        assert 2.0 < ratio_2 < 8.0, f"second ratio = {ratio_2}"


# ─────────────────────────────────────────────────────────────────────
# Carter's constant — the irreducible Killing tensor
# ─────────────────────────────────────────────────────────────────────


class TestCarterConstantFormula:
    """Pin down the closed-form values of Carter's Q at known points."""

    def test_equatorial_orbit_has_Q_zero(self):
        """For theta = pi/2, p_theta = 0, the formula gives Q = 0 identically."""
        bh = Kerr(mass=1.0, spin=0.5)
        Q = bh.carter_constant(E=0.95, L_z=3.0, p_theta=0.0, theta=math.pi / 2)
        assert math.isclose(Q, 0.0, abs_tol=1e-12)

    def test_equatorial_orbit_with_p_theta(self):
        """If p_theta != 0, Q = p_theta^2 even on the equator."""
        bh = Kerr(mass=1.0, spin=0.5)
        Q = bh.carter_constant(E=0.95, L_z=3.0, p_theta=1.5, theta=math.pi / 2)
        assert math.isclose(Q, 1.5 * 1.5, abs_tol=1e-12)

    def test_axis_raises(self):
        """Carter's formula has a coordinate singularity at sin theta = 0."""
        bh = Kerr(mass=1.0, spin=0.5)
        with pytest.raises(ValueError):
            bh.carter_constant(E=0.95, L_z=3.0, p_theta=0.0, theta=0.0)

    def test_schwarzschild_limit(self):
        """At a=0, Q reduces to L^2 - L_z^2 = L_perp^2."""
        bh = Kerr(mass=1.0, spin=0.0)
        # Generic angle, p_theta corresponds to part of L
        theta = 1.2
        L_z = 2.5
        p_theta = 1.7
        # In Schwarzschild Q = p_theta^2 + cos^2 theta * L_z^2/sin^2 theta
        # = L_perp^2 (the non-axial angular momentum squared component)
        Q = bh.carter_constant(E=1.0, L_z=L_z, p_theta=p_theta, theta=theta)
        expected = p_theta**2 + (math.cos(theta) ** 2) * (L_z**2) / (
            math.sin(theta) ** 2
        )
        assert math.isclose(Q, expected, abs_tol=1e-12)


class TestCarterConservation:
    """Carter's Q must be conserved along integrated Kerr geodesics.

    This is the experimental verification of the irreducible Killing
    tensor: Q has *no* continuous-symmetry origin, yet it is exactly
    conserved by true geodesics.  After 200 implicit-midpoint steps
    its drift should be at the same order as the Hamiltonian's drift.
    """

    def setup_method(self):
        self.bh, self.state = _generic_kerr_state()
        self.integrator = GeodesicIntegrator(self.bh)
        self.states = self.integrator.integrate(self.state, h=0.5, n_steps=200)

    def test_Q_drift_is_small(self):
        Qs = np.array([self.bh.carter_constant_from_state(s) for s in self.states])
        rel_drift = np.max(np.abs(Qs - Qs[0])) / abs(Qs[0])
        assert rel_drift < 1e-3, f"Q drifted by {rel_drift}"

    def test_Q_drift_matches_hamiltonian_drift_order(self):
        """Q and the Hamiltonian should drift to the same order of magnitude.

        Both are quadratic-in-momenta conserved quantities, so under
        a symplectic 2nd-order method they should accumulate error
        at the same rate.
        """
        Qs = np.array([self.bh.carter_constant_from_state(s) for s in self.states])
        Hs = np.array([self.integrator.hamiltonian(s) for s in self.states])
        rel_drift_Q = np.max(np.abs(Qs - Qs[0])) / abs(Qs[0])
        rel_drift_H = np.max(np.abs(Hs - Hs[0])) / abs(Hs[0])
        # Same order of magnitude (within a factor of 100 either way)
        assert 0.01 < rel_drift_Q / rel_drift_H < 100.0

    def test_Q_drift_scales_quadratically_with_step_size(self):
        """Halving h should reduce Q drift by a factor of about 4."""
        drifts = []
        for h in [1.0, 0.5, 0.25]:
            n_steps = int(round(50.0 / h))
            states = self.integrator.integrate(self.state, h=h, n_steps=n_steps)
            Qs = np.array([self.bh.carter_constant_from_state(s) for s in states])
            drifts.append(np.max(np.abs(Qs - Qs[0])) / abs(Qs[0]))
        ratio_1 = drifts[0] / drifts[1]
        ratio_2 = drifts[1] / drifts[2]
        assert 2.0 < ratio_1 < 8.0, f"first ratio = {ratio_1}"
        assert 2.0 < ratio_2 < 8.0, f"second ratio = {ratio_2}"


# ─────────────────────────────────────────────────────────────────────
# constants_of_motion convenience method
# ─────────────────────────────────────────────────────────────────────


class TestConstantsOfMotion:
    def test_returns_dict_with_four_keys(self):
        bh, state = _generic_kerr_state()
        c = bh.constants_of_motion(state)
        assert set(c.keys()) == {"E", "L_z", "mu_squared", "Q"}

    def test_E_matches_minus_p_t(self):
        bh, state = _generic_kerr_state()
        c = bh.constants_of_motion(state)
        assert math.isclose(c["E"], -state.p[0])

    def test_Lz_matches_p_phi(self):
        bh, state = _generic_kerr_state()
        c = bh.constants_of_motion(state)
        assert math.isclose(c["L_z"], state.p[3])

    def test_all_four_constants_conserved_along_integration(self):
        bh, state = _generic_kerr_state()
        integrator = GeodesicIntegrator(bh)
        states = integrator.integrate(state, h=0.5, n_steps=100)
        init = bh.constants_of_motion(states[0])
        for s in states[::10]:  # subsample
            c = bh.constants_of_motion(s)
            for key in ("E", "L_z"):
                assert math.isclose(c[key], init[key], abs_tol=1e-12)
            for key in ("mu_squared", "Q"):
                rel = abs(c[key] - init[key]) / abs(init[key])
                assert rel < 1e-3
