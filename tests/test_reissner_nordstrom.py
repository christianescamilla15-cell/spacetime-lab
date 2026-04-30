"""Tests for the Reissner-Nordström metric (v3.1).

Verification strategy: every result is gated against either
  (a) the canonical closed-form expression, or
  (b) the Schwarzschild limit Q → 0, which must reproduce
      the existing test_schwarzschild values to ≤ 1e-9.

References:
    Wald §6.4 ; MTW §31.5 ; Carroll §5.7.
    Pradhan & Iyer 2010 (ISCO closed form).
"""

from __future__ import annotations

import math

import pytest

from spacetime_lab.metrics import ReissnerNordstrom, Schwarzschild


# ──────────────────────────────────────────────────────────────────
# Construction & validation
# ──────────────────────────────────────────────────────────────────

def test_default_charge_is_zero() -> None:
    bh = ReissnerNordstrom(mass=1.0)
    assert bh.charge == 0.0
    assert bh.mass == 1.0


def test_construction_stores_absolute_charge() -> None:
    """The metric depends only on Q²; we normalise to |Q| for clarity."""
    bh = ReissnerNordstrom(mass=1.0, charge=-0.5)
    assert bh.charge == 0.5


def test_rejects_non_positive_mass() -> None:
    with pytest.raises(ValueError, match="mass must be positive"):
        ReissnerNordstrom(mass=0.0)
    with pytest.raises(ValueError, match="mass must be positive"):
        ReissnerNordstrom(mass=-1.0)


def test_rejects_supercritical_charge_cosmic_censorship() -> None:
    """|Q| > M would be a naked singularity — forbidden."""
    with pytest.raises(ValueError, match="cosmic censorship"):
        ReissnerNordstrom(mass=1.0, charge=1.5)


def test_extremal_flag_at_Q_equals_M() -> None:
    bh_extremal = ReissnerNordstrom(mass=1.0, charge=1.0)
    bh_subextremal = ReissnerNordstrom(mass=1.0, charge=0.5)
    assert bh_extremal.is_extremal is True
    assert bh_subextremal.is_extremal is False


# ──────────────────────────────────────────────────────────────────
# Schwarzschild limit (Q = 0) — must reproduce ALL Schwarzschild values
# ──────────────────────────────────────────────────────────────────

def test_schwarzschild_limit_outer_horizon() -> None:
    bh = ReissnerNordstrom(mass=1.0, charge=0.0)
    assert bh.outer_horizon() == pytest.approx(2.0, rel=1e-12)


def test_schwarzschild_limit_inner_horizon() -> None:
    bh = ReissnerNordstrom(mass=1.0, charge=0.0)
    assert bh.inner_horizon() == pytest.approx(0.0, abs=1e-12)


def test_schwarzschild_limit_photon_sphere() -> None:
    bh = ReissnerNordstrom(mass=1.0, charge=0.0)
    assert bh.photon_sphere() == pytest.approx(3.0, rel=1e-12)


def test_schwarzschild_limit_isco_recovers_6M() -> None:
    """Numerical ISCO must hit 6M to high precision when Q = 0."""
    bh = ReissnerNordstrom(mass=1.0, charge=0.0)
    assert bh.isco() == pytest.approx(6.0, rel=1e-9)


def test_schwarzschild_limit_hawking_temperature() -> None:
    bh = ReissnerNordstrom(mass=1.0, charge=0.0)
    expected = 1.0 / (8.0 * math.pi)
    assert bh.hawking_temperature() == pytest.approx(expected, rel=1e-12)


def test_schwarzschild_limit_entropy() -> None:
    bh = ReissnerNordstrom(mass=1.0, charge=0.0)
    expected = 4.0 * math.pi  # 4πM² with M=1
    assert bh.bekenstein_hawking_entropy() == pytest.approx(expected, rel=1e-12)


def test_schwarzschild_limit_matches_schwarzschild_class() -> None:
    """End-to-end: RN with Q=0 should agree with Schwarzschild on every
    invariant we both expose.  We wrap each Schwarzschild result in
    float() because the Schwarzschild class returns SymPy expressions
    (e.g. 1/(8πM)) that pytest.approx can't compare against a Python
    float directly."""
    rn = ReissnerNordstrom(mass=2.0, charge=0.0)
    sw = Schwarzschild(mass=2.0)
    assert rn.outer_horizon() == pytest.approx(float(sw.event_horizon()), rel=1e-12)
    assert rn.photon_sphere() == pytest.approx(float(sw.photon_sphere()), rel=1e-12)
    assert rn.isco() == pytest.approx(float(sw.isco()), rel=1e-9)
    assert rn.hawking_temperature() == pytest.approx(
        float(sw.hawking_temperature()), rel=1e-12)
    assert rn.bekenstein_hawking_entropy() == pytest.approx(
        float(sw.bekenstein_hawking_entropy()), rel=1e-12)


# ──────────────────────────────────────────────────────────────────
# Extremal limit Q = M
# ──────────────────────────────────────────────────────────────────

def test_extremal_horizons_merge_at_M() -> None:
    """At extremality both horizons sit at r = M."""
    bh = ReissnerNordstrom(mass=1.0, charge=1.0)
    assert bh.outer_horizon() == pytest.approx(1.0, rel=1e-12)
    assert bh.inner_horizon() == pytest.approx(1.0, rel=1e-12)


def test_extremal_hawking_temperature_zero() -> None:
    """Third law: T_H → 0 at extremality (zero-temperature BH)."""
    bh = ReissnerNordstrom(mass=1.0, charge=1.0)
    assert bh.hawking_temperature() == pytest.approx(0.0, abs=1e-12)


def test_extremal_photon_sphere_at_2M() -> None:
    """At Q = M: r_γ = (3M + sqrt(9M² - 8M²))/2 = (3+1)M/2 = 2M.
    Note 2M = 2·1 = 2, NOT r_+ = M.  Photon sphere stays OUTSIDE r_+
    even at extremality."""
    bh = ReissnerNordstrom(mass=1.0, charge=1.0)
    assert bh.photon_sphere() == pytest.approx(2.0, rel=1e-12)


# ──────────────────────────────────────────────────────────────────
# Sub-extremal closed-form sanity checks
# ──────────────────────────────────────────────────────────────────

def test_horizons_at_Q_equals_06() -> None:
    """M=1, Q=0.6 → r_± = 1 ± sqrt(1 - 0.36) = 1 ± 0.8."""
    bh = ReissnerNordstrom(mass=1.0, charge=0.6)
    assert bh.outer_horizon() == pytest.approx(1.8, rel=1e-12)
    assert bh.inner_horizon() == pytest.approx(0.2, rel=1e-12)


def test_horizons_satisfy_quadratic_root_relations() -> None:
    """For all valid Q, by Vieta's: r_+ + r_- = 2M and r_+ · r_- = Q²."""
    for M, Q in [(1.0, 0.3), (2.0, 1.5), (1.0, 0.999), (5.0, 2.5)]:
        bh = ReissnerNordstrom(mass=M, charge=Q)
        rp = bh.outer_horizon()
        rm = bh.inner_horizon()
        assert (rp + rm) == pytest.approx(2 * M, rel=1e-12)
        assert (rp * rm) == pytest.approx(Q * Q, rel=1e-12)


def test_isco_decreases_with_charge() -> None:
    """ISCO should monotonically decrease as Q grows from 0 toward M.
    Spot-check at three values."""
    M = 1.0
    isco_0 = ReissnerNordstrom(mass=M, charge=0.0).isco()
    isco_05 = ReissnerNordstrom(mass=M, charge=0.5).isco()
    isco_09 = ReissnerNordstrom(mass=M, charge=0.9).isco()
    assert isco_0 > isco_05 > isco_09
    assert isco_0 == pytest.approx(6.0, rel=1e-9)


def test_hawking_temperature_positive_subextremal() -> None:
    """T_H > 0 for any |Q| < M, vanishing only at extremality."""
    for Q in [0.0, 0.3, 0.5, 0.9]:
        bh = ReissnerNordstrom(mass=1.0, charge=Q)
        assert bh.hawking_temperature() > 0


def test_metric_tensor_is_4x4_diagonal() -> None:
    bh = ReissnerNordstrom(mass=1.0, charge=0.5)
    g = bh.metric_tensor
    assert g.shape == (4, 4)
    # Diagonal: off-diagonal entries identically zero
    for i in range(4):
        for j in range(4):
            if i != j:
                assert g[i, j] == 0


def test_line_element_latex_contains_charge_term() -> None:
    bh = ReissnerNordstrom(mass=1.0, charge=0.5)
    latex = bh.line_element_latex()
    assert "Q^2" in latex
    assert "2M" in latex
    assert "r^2" in latex
