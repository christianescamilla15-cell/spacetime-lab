"""Tests for Kerr-Newman metric (v3.2).

Verification: every result is gated by either
  (a) the canonical closed-form expression, or
  (b) a layered limit:
        Q = 0  → must match the Kerr class at same (M, a)
        a = 0  → must match the ReissnerNordstrom class at same (M, Q)
        a = 0, Q = 0 → must match Schwarzschild at same M

References: Newman et al. 1965; Wald §12.3; Misner-Thorne-Wheeler §33.
"""

from __future__ import annotations

import math

import pytest

from spacetime_lab.metrics import (
    Kerr,
    KerrNewman,
    ReissnerNordstrom,
    Schwarzschild,
)


# ──────────────────────────────────────────────────────────────────
# Construction & validation
# ──────────────────────────────────────────────────────────────────

def test_default_args_no_spin_no_charge() -> None:
    bh = KerrNewman(mass=1.0)
    assert bh.spin == 0.0
    assert bh.charge == 0.0


def test_charge_stored_as_absolute_value() -> None:
    bh = KerrNewman(mass=1.0, spin=0.0, charge=-0.5)
    assert bh.charge == 0.5


def test_rejects_non_positive_mass() -> None:
    with pytest.raises(ValueError, match="mass must be positive"):
        KerrNewman(mass=0.0)


def test_rejects_negative_spin() -> None:
    with pytest.raises(ValueError, match="spin must be non-negative"):
        KerrNewman(mass=1.0, spin=-0.1)


def test_rejects_supercritical_a_squared_plus_q_squared() -> None:
    """Cosmic censorship: a² + Q² > M² is forbidden."""
    with pytest.raises(ValueError, match="cosmic censorship"):
        KerrNewman(mass=1.0, spin=0.7, charge=0.8)  # 0.49 + 0.64 = 1.13 > 1


def test_extremal_at_boundary_of_cosmic_censorship() -> None:
    """a² + Q² = M² is allowed (extremal); just barely."""
    bh = KerrNewman(mass=1.0, spin=0.6, charge=0.8)  # 0.36 + 0.64 = 1.00
    assert bh.is_extremal is True


# ──────────────────────────────────────────────────────────────────
# Schwarzschild limit (a = 0, Q = 0)
# ──────────────────────────────────────────────────────────────────

def test_schwarzschild_limit_horizon() -> None:
    bh = KerrNewman(mass=1.0, spin=0.0, charge=0.0)
    assert bh.outer_horizon() == pytest.approx(2.0, rel=1e-12)
    assert bh.inner_horizon() == pytest.approx(0.0, abs=1e-12)


def test_schwarzschild_limit_thermo() -> None:
    bh = KerrNewman(mass=1.0, spin=0.0, charge=0.0)
    sw = Schwarzschild(mass=1.0)
    assert bh.hawking_temperature() == pytest.approx(
        float(sw.hawking_temperature()), rel=1e-12,
    )
    assert bh.bekenstein_hawking_entropy() == pytest.approx(
        float(sw.bekenstein_hawking_entropy()), rel=1e-12,
    )


# ──────────────────────────────────────────────────────────────────
# Kerr limit (Q = 0) — must match Kerr at same (M, a)
# ──────────────────────────────────────────────────────────────────

def test_kerr_limit_horizons_match_kerr_class() -> None:
    for M, a in [(1.0, 0.5), (2.0, 1.5), (1.0, 0.999)]:
        kn = KerrNewman(mass=M, spin=a, charge=0.0)
        kerr = Kerr(mass=M, spin=a)
        assert kn.outer_horizon() == pytest.approx(kerr.outer_horizon(), rel=1e-12)
        assert kn.inner_horizon() == pytest.approx(kerr.inner_horizon(), rel=1e-12)


def test_kerr_limit_thermo_matches_kerr_class() -> None:
    kn = KerrNewman(mass=1.0, spin=0.6, charge=0.0)
    kerr = Kerr(mass=1.0, spin=0.6)
    assert kn.angular_velocity_horizon() == pytest.approx(
        kerr.angular_velocity_horizon(), rel=1e-12,
    )
    assert kn.horizon_area() == pytest.approx(kerr.horizon_area(), rel=1e-12)
    assert kn.surface_gravity() == pytest.approx(kerr.surface_gravity(), rel=1e-12)
    assert kn.hawking_temperature() == pytest.approx(
        kerr.hawking_temperature(), rel=1e-12,
    )
    assert kn.bekenstein_hawking_entropy() == pytest.approx(
        kerr.bekenstein_hawking_entropy(), rel=1e-12,
    )


def test_kerr_limit_ergosphere_matches_kerr_class() -> None:
    """Ergosphere at equator: r_E(π/2) = M + sqrt(M² - a²·0) = 2M for both."""
    kn = KerrNewman(mass=1.0, spin=0.5, charge=0.0)
    kerr = Kerr(mass=1.0, spin=0.5)
    for theta in [math.pi / 2, math.pi / 4, 0.1]:
        assert kn.ergosphere(theta) == pytest.approx(
            kerr.ergosphere(theta), rel=1e-12,
        )


# ──────────────────────────────────────────────────────────────────
# RN limit (a = 0) — must match ReissnerNordstrom at same (M, Q)
# ──────────────────────────────────────────────────────────────────

def test_rn_limit_horizons_match_rn_class() -> None:
    for M, Q in [(1.0, 0.5), (2.0, 1.5), (1.0, 0.999)]:
        kn = KerrNewman(mass=M, spin=0.0, charge=Q)
        rn = ReissnerNordstrom(mass=M, charge=Q)
        assert kn.outer_horizon() == pytest.approx(rn.outer_horizon(), rel=1e-12)
        assert kn.inner_horizon() == pytest.approx(rn.inner_horizon(), rel=1e-12)


def test_rn_limit_thermo_matches_rn_class() -> None:
    kn = KerrNewman(mass=1.0, spin=0.0, charge=0.6)
    rn = ReissnerNordstrom(mass=1.0, charge=0.6)
    assert kn.surface_gravity() == pytest.approx(rn.surface_gravity(), rel=1e-12)
    assert kn.hawking_temperature() == pytest.approx(
        rn.hawking_temperature(), rel=1e-12,
    )
    assert kn.bekenstein_hawking_entropy() == pytest.approx(
        rn.bekenstein_hawking_entropy(), rel=1e-12,
    )


def test_rn_limit_no_frame_dragging() -> None:
    """At a = 0, Ω_H = 0 (no frame-dragging in non-rotating BH)."""
    kn = KerrNewman(mass=1.0, spin=0.0, charge=0.6)
    assert kn.angular_velocity_horizon() == pytest.approx(0.0, abs=1e-12)


# ──────────────────────────────────────────────────────────────────
# Sub-extremal closed-form sanity (genuine 3-parameter checks)
# ──────────────────────────────────────────────────────────────────

def test_horizon_root_relations() -> None:
    """For all (M, a, Q): r_+ + r_- = 2M and r_+ · r_- = a² + Q².
    This is the 3-parameter generalization of RN's Vieta relations."""
    for M, a, Q in [(1.0, 0.3, 0.4), (2.0, 1.0, 1.0), (1.0, 0.5, 0.5)]:
        bh = KerrNewman(mass=M, spin=a, charge=Q)
        rp = bh.outer_horizon()
        rm = bh.inner_horizon()
        assert (rp + rm) == pytest.approx(2 * M, rel=1e-12)
        assert (rp * rm) == pytest.approx(a * a + Q * Q, rel=1e-12)


def test_extremal_horizons_merge() -> None:
    """At a² + Q² = M²: r_+ = r_- = M; T_H = 0."""
    bh = KerrNewman(mass=1.0, spin=0.6, charge=0.8)  # 0.36 + 0.64 = 1
    assert bh.outer_horizon() == pytest.approx(1.0, rel=1e-12)
    assert bh.inner_horizon() == pytest.approx(1.0, rel=1e-12)
    assert bh.hawking_temperature() == pytest.approx(0.0, abs=1e-12)


def test_metric_tensor_shape() -> None:
    """4×4 with one off-diagonal pair (g_tφ, g_φt)."""
    bh = KerrNewman(mass=1.0, spin=0.5, charge=0.3)
    g = bh.metric_tensor
    assert g.shape == (4, 4)
    # Symmetric in t,φ; zero everywhere else off-diagonal
    assert g[0, 3] == g[3, 0]
    for i in range(4):
        for j in range(4):
            if i != j and not ((i, j) == (0, 3) or (i, j) == (3, 0)):
                assert g[i, j] == 0


def test_line_element_latex_contains_Q_and_a() -> None:
    bh = KerrNewman(mass=1.0, spin=0.5, charge=0.3)
    latex = bh.line_element_latex()
    assert "Q^2" in latex
    assert "a^" in latex or "a " in latex
    assert "Sigma" in latex or "\\Sigma" in latex


def test_ergosphere_at_equator_independent_of_spin() -> None:
    """At θ=π/2 (cos²θ=0), r_E = M + sqrt(M² - Q²) — only depends on Q.
    At a=0 this reduces to the RN outer horizon r_+."""
    bh = KerrNewman(mass=1.0, spin=0.5, charge=0.4)
    bh_no_spin = KerrNewman(mass=1.0, spin=0.0, charge=0.4)
    assert bh.ergosphere(math.pi / 2) == pytest.approx(
        bh_no_spin.ergosphere(math.pi / 2), rel=1e-12,
    )
    # Numerical sanity: 1 + sqrt(1 - 0.16) = 1 + sqrt(0.84) ≈ 1.9165
    assert bh.ergosphere(math.pi / 2) == pytest.approx(
        1.0 + math.sqrt(0.84), rel=1e-12,
    )
