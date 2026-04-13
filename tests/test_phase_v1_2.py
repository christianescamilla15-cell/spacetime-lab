"""Tests for v1.2 patch: Kerr quasinormal mode wrapper.

The v1.2 patch adds :func:`kerr_qnm` to ``spacetime_lab.waves``.
It wraps Stein's ``qnm`` package's Kerr front-end
(``qnm.modes_cache``) so that :class:`QNMResult` objects carry the
azimuthal number ``m`` and the dimensionless spin ``a_over_M`` in
addition to ``l``, ``n``, ``s`` and the complex frequency.

Tests are pinned to the following invariants:

1. **qnm-docs anchor**: the canonical example in the ``qnm`` package
   docs, ``kerr_qnm(l=2, m=2, n=0, a_over_M=0.68)``, returns
   ``0.5239751042900845 - 0.08151262363119974 i`` (bit-exact up to
   the double-precision noise between qnm versions).
2. **Schwarzschild limit**: at ``a_over_M = 0.0`` the Kerr path
   returns the same omega as the independent Schwarzschild path
   (:func:`leaver_qnm_schwarzschild`), for every ``m`` in
   ``{-l, ..., l}``.  The residual is at machine precision (the
   two solvers reduce to the same computation at a = 0).
3. **m-degeneracy at a=0**: modes with different ``m`` but same
   ``(l, n)`` are equal at ``a = 0`` (Schwarzschild is spherically
   symmetric).
4. **Prograde less damped than retrograde**: for any ``a > 0``,
   ``|Im(omega_prograde)| < |Im(omega_retrograde)|`` for ``l=2``,
   ``m = ±2``, ``n = 0``.
5. **Monotonic frequency with spin**: ``Re(omega_{l=m=2, n=0}(a))``
   is monotonically increasing in ``a`` (the BH "rigidifies" as it
   spins up).
6. **All modes decay**: every returned omega has
   ``Im(omega) < 0``.
7. **Input validation**: ``|m| > l``, ``l < |s|``, ``n < 0``, and
   ``a_over_M`` outside ``[0, 1)`` raise ``ValueError``.
"""

import math

import pytest

from spacetime_lab.waves import (
    QNMResult,
    kerr_qnm,
    leaver_qnm_schwarzschild,
)


# ─────────────────────────────────────────────────────────────────────
# qnm-docs canonical anchor
# ─────────────────────────────────────────────────────────────────────


class TestKerrQNMAnchor:
    """The canonical example from the qnm package's own documentation."""

    def test_kerr_220_at_a_0p68(self):
        # From qnm docs: grav_220(a=0.68) = 0.5239751042900845 - 0.08151262363119974j
        r = kerr_qnm(l=2, m=2, n=0, a_over_M=0.68)
        assert math.isclose(r.omega.real, 0.5239751042900845, abs_tol=1e-10)
        assert math.isclose(r.omega.imag, -0.08151262363119974, abs_tol=1e-10)

    def test_returns_qnmresult(self):
        r = kerr_qnm(l=2, m=2, n=0, a_over_M=0.5)
        assert isinstance(r, QNMResult)
        assert r.l == 2
        assert r.m == 2
        assert r.n == 0
        assert r.s == -2
        assert r.a_over_M == 0.5

    def test_fields_for_kerr_are_populated(self):
        r = kerr_qnm(l=2, m=2, n=0, a_over_M=0.5)
        assert r.m is not None
        assert r.a_over_M is not None


# ─────────────────────────────────────────────────────────────────────
# Schwarzschild limit: a -> 0
# ─────────────────────────────────────────────────────────────────────


class TestSchwarzschildLimit:
    """At a=0 the Kerr path must agree with the Schwarzschild path."""

    def test_matches_leaver_schwarzschild_m0(self):
        rK = kerr_qnm(l=2, m=0, n=0, a_over_M=0.0)
        rS = leaver_qnm_schwarzschild(l=2, n=0)
        assert abs(rK.omega - rS.omega) < 1e-10

    def test_matches_leaver_schwarzschild_all_m(self):
        # At a=0, m-degeneracy: every m gives the Schwarzschild value.
        rS = leaver_qnm_schwarzschild(l=2, n=0)
        for m in [-2, -1, 0, 1, 2]:
            rK = kerr_qnm(l=2, m=m, n=0, a_over_M=0.0)
            assert abs(rK.omega - rS.omega) < 1e-10, m

    def test_m_degeneracy_at_a_zero(self):
        # All (l=2, m, n=0) modes are equal at a=0.
        omegas = [
            kerr_qnm(l=2, m=m, n=0, a_over_M=0.0).omega
            for m in [-2, -1, 0, 1, 2]
        ]
        for o in omegas[1:]:
            assert abs(o - omegas[0]) < 1e-10

    def test_matches_leaver_higher_l(self):
        rK = kerr_qnm(l=3, m=3, n=0, a_over_M=0.0)
        rS = leaver_qnm_schwarzschild(l=3, n=0)
        assert abs(rK.omega - rS.omega) < 1e-10


# ─────────────────────────────────────────────────────────────────────
# Prograde vs retrograde
# ─────────────────────────────────────────────────────────────────────


class TestProgradeVsRetrograde:
    """Prograde modes (m > 0) are less damped than retrograde (m < 0)."""

    def test_at_high_spin(self):
        pro = kerr_qnm(l=2, m=2, n=0, a_over_M=0.9)
        retro = kerr_qnm(l=2, m=-2, n=0, a_over_M=0.9)
        assert abs(pro.omega.imag) < abs(retro.omega.imag)

    def test_at_mid_spin(self):
        pro = kerr_qnm(l=2, m=2, n=0, a_over_M=0.5)
        retro = kerr_qnm(l=2, m=-2, n=0, a_over_M=0.5)
        assert abs(pro.omega.imag) < abs(retro.omega.imag)

    def test_prograde_frequency_higher_than_retrograde(self):
        # At a > 0, prograde modes have higher real frequency (BH
        # drags perturbations in the co-rotating direction).
        pro = kerr_qnm(l=2, m=2, n=0, a_over_M=0.7)
        retro = kerr_qnm(l=2, m=-2, n=0, a_over_M=0.7)
        assert pro.omega.real > retro.omega.real

    def test_degeneracy_broken_at_any_nonzero_spin(self):
        for a in [0.1, 0.3, 0.5, 0.7]:
            pro = kerr_qnm(l=2, m=2, n=0, a_over_M=a)
            retro = kerr_qnm(l=2, m=-2, n=0, a_over_M=a)
            assert abs(pro.omega - retro.omega) > 1e-4, a


# ─────────────────────────────────────────────────────────────────────
# Monotonicity with spin
# ─────────────────────────────────────────────────────────────────────


class TestSpinMonotonicity:
    """Re(omega_{l=m=2, n=0}(a)) monotonically increases with a."""

    def test_real_part_monotone_prograde(self):
        spins = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 0.98]
        prev = -1.0
        for a in spins:
            r = kerr_qnm(l=2, m=2, n=0, a_over_M=a)
            assert r.omega.real > prev - 1e-12, (a, r.omega.real, prev)
            prev = r.omega.real

    def test_damping_decreases_with_spin_prograde(self):
        # Prograde mode becomes less damped as spin increases —
        # in the extremal limit |Im(omega)| approaches zero.
        spins = [0.0, 0.3, 0.6, 0.9, 0.98]
        prev_imag_abs = float("inf")
        for a in spins:
            r = kerr_qnm(l=2, m=2, n=0, a_over_M=a)
            assert abs(r.omega.imag) < prev_imag_abs + 1e-12, (a, r.omega)
            prev_imag_abs = abs(r.omega.imag)

    def test_damping_at_near_extremal(self):
        # At a = 0.98, the prograde l=m=2 n=0 mode has much
        # smaller |Im(omega)| than the Schwarzschild value ~0.089.
        r = kerr_qnm(l=2, m=2, n=0, a_over_M=0.98)
        assert abs(r.omega.imag) < 0.08


# ─────────────────────────────────────────────────────────────────────
# Physical sanity
# ─────────────────────────────────────────────────────────────────────


class TestPhysicalSanity:
    """All returned modes must decay (no superradiance)."""

    def test_all_modes_decay(self):
        spins = [0.0, 0.2, 0.5, 0.8, 0.95]
        for a in spins:
            for m in [-2, -1, 0, 1, 2]:
                r = kerr_qnm(l=2, m=m, n=0, a_over_M=a)
                assert r.omega.imag < 0, (a, m, r.omega)

    def test_frequency_positive_for_prograde_large_spin(self):
        # At high spin, the prograde (l=m=2, n=0) mode has Re(omega)
        # approaching m * Omega_H with Omega_H = a / (2 M r_+) ~ O(0.5).
        # So we expect it to grow well past the Schwarzschild value.
        r = kerr_qnm(l=2, m=2, n=0, a_over_M=0.9)
        assert r.omega.real > 0.5  # well above Schwarzschild ~0.37


# ─────────────────────────────────────────────────────────────────────
# Input validation
# ─────────────────────────────────────────────────────────────────────


class TestInputValidation:
    def test_m_greater_than_l_raises(self):
        with pytest.raises(ValueError, match="|m|"):
            kerr_qnm(l=2, m=3, n=0)

    def test_m_less_than_minus_l_raises(self):
        with pytest.raises(ValueError, match="|m|"):
            kerr_qnm(l=2, m=-3, n=0)

    def test_l_less_than_abs_s_raises(self):
        with pytest.raises(ValueError, match=r"l must be >= \|s\|"):
            kerr_qnm(l=1, m=0, n=0, s=-2)

    def test_negative_n_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            kerr_qnm(l=2, m=0, n=-1)

    def test_a_over_M_equal_one_raises(self):
        with pytest.raises(ValueError, match=r"\[0, 1\)"):
            kerr_qnm(l=2, m=2, n=0, a_over_M=1.0)

    def test_a_over_M_negative_raises(self):
        with pytest.raises(ValueError, match=r"\[0, 1\)"):
            kerr_qnm(l=2, m=2, n=0, a_over_M=-0.1)

    def test_a_over_M_above_one_raises(self):
        with pytest.raises(ValueError, match=r"\[0, 1\)"):
            kerr_qnm(l=2, m=2, n=0, a_over_M=1.5)


# ─────────────────────────────────────────────────────────────────────
# QNMResult backward compatibility
# ─────────────────────────────────────────────────────────────────────


class TestQNMResultBackCompat:
    """Schwarzschild QNMResult must remain unchanged by the Kerr extension."""

    def test_schwarzschild_has_none_m_and_a(self):
        r = leaver_qnm_schwarzschild(l=2, n=0)
        assert r.m is None
        assert r.a_over_M is None

    def test_schwarzschild_still_has_cf_metadata(self):
        r = leaver_qnm_schwarzschild(l=2, n=0)
        assert not math.isnan(r.cf_truncation_error)
        assert r.n_cf_terms >= 0

    def test_kerr_has_nan_cf_metadata(self):
        # qnm's cache API does not expose cf_truncation_error / n_cf_terms
        r = kerr_qnm(l=2, m=2, n=0, a_over_M=0.5)
        assert math.isnan(r.cf_truncation_error)
        assert r.n_cf_terms == -1
