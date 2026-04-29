"""Smoke tests for the v2.5 Kerr REST endpoint.

These do NOT re-test the underlying physics — that's already covered by
``test_kerr.py``.  Their job is to verify the FastAPI wrapper:
parameter validation, response schema, error handling.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

# The backend uses ``from app.routes import kerr`` which expects the
# backend directory on sys.path.  pytest runs from repo root, so add it.
BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


# ──────────────────────────────────────────────────────────────────
# Happy path
# ──────────────────────────────────────────────────────────────────

def test_kerr_endpoint_returns_200_for_valid_inputs() -> None:
    response = client.get("/api/metrics/kerr", params={"mass": 1.0, "spin": 0.5})
    assert response.status_code == 200


def test_kerr_response_includes_all_documented_fields() -> None:
    response = client.get("/api/metrics/kerr", params={"mass": 1.0, "spin": 0.5})
    body = response.json()
    expected = {
        "mass", "spin", "a_over_m",
        "outer_horizon", "inner_horizon",
        "ergo_equator", "ergo_pole",
        "isco_prograde", "isco_retrograde",
        "photon_sphere_prograde", "photon_sphere_retrograde",
        "angular_velocity_horizon", "horizon_area",
        "surface_gravity", "hawking_temperature", "bekenstein_hawking_entropy",
        "line_element_latex", "is_extremal",
    }
    assert expected.issubset(body.keys())


# ──────────────────────────────────────────────────────────────────
# Schwarzschild limit (a = 0): closed-form invariants
# ──────────────────────────────────────────────────────────────────

def test_kerr_at_zero_spin_recovers_schwarzschild() -> None:
    """At a=0, Kerr collapses to Schwarzschild: r_+ = 2M, r_- = 0,
    ISCO_+ = ISCO_- = 6M, photon = 3M.  Numerical tolerances kept loose
    on photon_sphere because the prograde/retrograde Bardeen formula
    has a removable indeterminacy at a=0."""
    M = 1.0
    response = client.get("/api/metrics/kerr", params={"mass": M, "spin": 0.0})
    body = response.json()
    assert body["outer_horizon"] == pytest.approx(2.0 * M, rel=1e-12)
    assert body["inner_horizon"] == pytest.approx(0.0, abs=1e-12)
    assert body["isco_prograde"] == pytest.approx(6.0 * M, rel=1e-9)
    assert body["isco_retrograde"] == pytest.approx(6.0 * M, rel=1e-9)
    assert body["photon_sphere_prograde"] == pytest.approx(3.0 * M, rel=1e-6)
    assert body["photon_sphere_retrograde"] == pytest.approx(3.0 * M, rel=1e-6)
    assert body["ergo_equator"] == pytest.approx(2.0 * M, rel=1e-12)
    assert body["is_extremal"] is False


# ──────────────────────────────────────────────────────────────────
# Extremal limit (a → M): horizons merge, T_H → 0, prograde ISCO → M
# ──────────────────────────────────────────────────────────────────

def test_kerr_extremal_limit_horizons_merge() -> None:
    """At a = M (extremal), r_+ = r_- = M.  Hawking T → 0."""
    M = 1.0
    response = client.get("/api/metrics/kerr", params={"mass": M, "spin": M})
    body = response.json()
    assert body["outer_horizon"] == pytest.approx(M, rel=1e-12)
    assert body["inner_horizon"] == pytest.approx(M, rel=1e-12)
    assert body["hawking_temperature"] == pytest.approx(0.0, abs=1e-12)
    assert body["is_extremal"] is True


def test_kerr_high_spin_isco_prograde_goes_below_6M() -> None:
    """For a > 0, prograde ISCO < 6M (BH "drags" the orbit closer)."""
    response = client.get("/api/metrics/kerr", params={"mass": 1.0, "spin": 0.9})
    isco_pro = response.json()["isco_prograde"]
    assert isco_pro < 6.0


def test_kerr_high_spin_isco_retrograde_goes_above_6M() -> None:
    """For a > 0, retrograde ISCO > 6M (BH "fights" the orbit)."""
    response = client.get("/api/metrics/kerr", params={"mass": 1.0, "spin": 0.9})
    isco_retro = response.json()["isco_retrograde"]
    assert isco_retro > 6.0


# ──────────────────────────────────────────────────────────────────
# Validation errors
# ──────────────────────────────────────────────────────────────────

def test_kerr_rejects_negative_mass() -> None:
    response = client.get("/api/metrics/kerr", params={"mass": -1.0, "spin": 0.0})
    assert response.status_code == 422  # FastAPI Query(gt=0) constraint


def test_kerr_rejects_spin_greater_than_mass() -> None:
    """Cosmic censorship: a > M is unphysical (naked singularity)."""
    response = client.get("/api/metrics/kerr", params={"mass": 1.0, "spin": 1.5})
    assert response.status_code == 400
    assert "spin" in response.json()["detail"].lower()


def test_kerr_rejects_negative_spin() -> None:
    response = client.get("/api/metrics/kerr", params={"mass": 1.0, "spin": -0.1})
    assert response.status_code == 422  # ge=0 constraint


# ──────────────────────────────────────────────────────────────────
# Available metrics list reflects the v2.5 truth
# ──────────────────────────────────────────────────────────────────

def test_available_metrics_lists_kerr_as_available() -> None:
    response = client.get("/api/metrics/available")
    metrics = response.json()["metrics"]
    kerr_entry = next(m for m in metrics if m["name"] == "Kerr")
    assert kerr_entry["available"] is True
    assert kerr_entry["rest_endpoint"] == "/api/metrics/kerr"


def test_available_metrics_lists_schwarzschild_as_available() -> None:
    response = client.get("/api/metrics/available")
    metrics = response.json()["metrics"]
    sch_entry = next(m for m in metrics if m["name"] == "Schwarzschild")
    assert sch_entry["available"] is True
