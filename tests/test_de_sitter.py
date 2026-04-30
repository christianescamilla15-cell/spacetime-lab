"""Tests for the de Sitter metric (v3.2, partial).

All quantities are closed-form in dS, so every assertion is at machine
precision (rel 1e-12).
"""

from __future__ import annotations

import math

import pytest

from spacetime_lab.metrics import DeSitter


def test_default_radius_is_one() -> None:
    ds = DeSitter()
    assert ds.radius == 1.0


def test_rejects_non_positive_radius() -> None:
    with pytest.raises(ValueError, match="radius must be positive"):
        DeSitter(radius=0.0)
    with pytest.raises(ValueError, match="radius must be positive"):
        DeSitter(radius=-1.0)


def test_cosmological_horizon_equals_radius() -> None:
    """r_c = L by definition of static-patch coords."""
    for L in [0.5, 1.0, 2.5]:
        ds = DeSitter(radius=L)
        assert ds.cosmological_horizon() == L


def test_cosmological_constant_is_3_over_L_squared() -> None:
    for L in [0.5, 1.0, 2.5]:
        ds = DeSitter(radius=L)
        assert ds.cosmological_constant() == pytest.approx(3.0 / L ** 2, rel=1e-12)


def test_hubble_parameter_is_inverse_radius() -> None:
    for L in [0.5, 1.0, 2.5]:
        ds = DeSitter(radius=L)
        assert ds.hubble_parameter() == pytest.approx(1.0 / L, rel=1e-12)


def test_hubble_relates_to_lambda() -> None:
    """H = sqrt(Λ/3) — sanity check both formulas agree."""
    for L in [0.5, 1.0, 2.5]:
        ds = DeSitter(radius=L)
        assert ds.hubble_parameter() == pytest.approx(
            math.sqrt(ds.cosmological_constant() / 3.0), rel=1e-12,
        )


def test_gibbons_hawking_temperature() -> None:
    """T_GH = 1 / (2π L) — Gibbons & Hawking 1977."""
    for L in [0.5, 1.0, 2.5]:
        ds = DeSitter(radius=L)
        assert ds.hawking_temperature() == pytest.approx(
            1.0 / (2.0 * math.pi * L), rel=1e-12,
        )


def test_horizon_area_is_4_pi_L_squared() -> None:
    for L in [0.5, 1.0, 2.5]:
        ds = DeSitter(radius=L)
        assert ds.horizon_area() == pytest.approx(4.0 * math.pi * L ** 2, rel=1e-12)


def test_entropy_is_quarter_area() -> None:
    for L in [0.5, 1.0, 2.5]:
        ds = DeSitter(radius=L)
        assert ds.bekenstein_hawking_entropy() == pytest.approx(
            ds.horizon_area() / 4.0, rel=1e-12,
        )
        assert ds.bekenstein_hawking_entropy() == pytest.approx(
            math.pi * L ** 2, rel=1e-12,
        )


def test_ricci_scalar_is_4_lambda() -> None:
    """For 4D dS: R = 4Λ = 12/L²."""
    for L in [0.5, 1.0, 2.5]:
        ds = DeSitter(radius=L)
        assert ds.expected_ricci_scalar() == pytest.approx(
            4.0 * ds.cosmological_constant(), rel=1e-12,
        )


def test_metric_tensor_diagonal_4x4() -> None:
    ds = DeSitter(radius=1.0)
    g = ds.metric_tensor
    assert g.shape == (4, 4)
    for i in range(4):
        for j in range(4):
            if i != j:
                assert g[i, j] == 0


def test_line_element_latex_contains_L_and_no_M() -> None:
    """dS has NO mass parameter — the LaTeX should reference L only."""
    ds = DeSitter(radius=1.0)
    latex = ds.line_element_latex()
    assert "L^2" in latex
    assert "2M" not in latex
    assert "Q^2" not in latex
