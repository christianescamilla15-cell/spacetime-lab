"""Smoke tests for the v2.5 AdS metric and Holography (Page curve) routes.

Same pattern as test_api_kerr.py: physics is already covered by the
test_phase8/9/v1_1 suites; here we verify HTTP wrappers.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


# ──────────────────────────────────────────────────────────────────
# AdS endpoint
# ──────────────────────────────────────────────────────────────────

def test_ads_d3_canonical_values() -> None:
    """AdS_3 with L=1, G=1: Λ=-1, R=-6, R_μν proportionality=-2,
    Brown-Henneaux c = 3L/(2G) = 1.5."""
    r = client.get("/api/metrics/ads", params={"dimension": 3, "radius": 1.0, "G_N": 1.0})
    assert r.status_code == 200
    body = r.json()
    assert body["cosmological_constant"] == pytest.approx(-1.0, rel=1e-12)
    assert body["ricci_scalar"] == pytest.approx(-6.0, rel=1e-12)
    assert body["ricci_proportionality"] == pytest.approx(-2.0, rel=1e-12)
    assert body["brown_henneaux_central_charge"] == pytest.approx(1.5, rel=1e-12)


def test_ads_d4_no_central_charge() -> None:
    """Brown-Henneaux only defined for d=3.  Higher dims must return null."""
    r = client.get("/api/metrics/ads", params={"dimension": 4, "radius": 2.0})
    body = r.json()
    assert body["brown_henneaux_central_charge"] is None


def test_ads_curvature_scaling_with_L() -> None:
    """R = -n(n-1)/L² scales as 1/L² so R(L=2)/R(L=1) = 1/4."""
    r1 = client.get("/api/metrics/ads", params={"dimension": 3, "radius": 1.0}).json()
    r2 = client.get("/api/metrics/ads", params={"dimension": 3, "radius": 2.0}).json()
    ratio = r2["ricci_scalar"] / r1["ricci_scalar"]
    assert ratio == pytest.approx(0.25, rel=1e-12)


def test_ads_rejects_dim_below_2() -> None:
    r = client.get("/api/metrics/ads", params={"dimension": 1, "radius": 1.0})
    assert r.status_code == 422


def test_ads_rejects_negative_radius() -> None:
    r = client.get("/api/metrics/ads", params={"dimension": 3, "radius": -1.0})
    assert r.status_code == 422


# ──────────────────────────────────────────────────────────────────
# Page curve — eternal BTZ
# ──────────────────────────────────────────────────────────────────

def test_page_curve_eternal_returns_well_formed() -> None:
    r = client.get(
        "/api/holography/page_curve/eternal",
        params={"horizon_radius": 1.0, "ads_radius": 1.0, "epsilon": 0.01,
                "t_max": 10.0, "n_samples": 50},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "eternal"
    assert len(body["t_values"]) == 50
    assert len(body["s_values"]) == 50
    assert len(body["phase_labels"]) == 50


def test_page_curve_eternal_phase_transitions() -> None:
    """Early times trivial (HM saddle wins); late times island wins.
    Both labels must appear in the output."""
    r = client.get(
        "/api/holography/page_curve/eternal",
        params={"horizon_radius": 1.0, "ads_radius": 1.0, "epsilon": 0.01,
                "t_max": 20.0, "n_samples": 100},
    )
    phases = r.json()["phase_labels"]
    assert "trivial" in phases
    assert "island" in phases
    # Phase must transition exactly once (monotone): all 'trivial' then all 'island'
    first_island = phases.index("island")
    assert all(p == "trivial" for p in phases[:first_island])
    assert all(p == "island" for p in phases[first_island:])


def test_page_curve_eternal_saturates() -> None:
    """At late times the curve must plateau at the island saddle value
    (= 2 S_BH for the eternal case)."""
    r = client.get(
        "/api/holography/page_curve/eternal",
        params={"horizon_radius": 1.0, "ads_radius": 1.0, "epsilon": 0.01,
                "t_max": 20.0, "n_samples": 100},
    )
    body = r.json()
    last_few = body["s_values"][-5:]
    sat = body["saturation_entropy"]
    for s in last_few:
        assert s == pytest.approx(sat, rel=1e-9)


# ──────────────────────────────────────────────────────────────────
# Page curve — evaporating Schwarzschild
# ──────────────────────────────────────────────────────────────────

def test_page_curve_evaporating_returns_bell_shape() -> None:
    """Evaporating Page curve must be bell-shaped: ~0 at endpoints,
    peak somewhere in the middle."""
    r = client.get(
        "/api/holography/page_curve/evaporating",
        params={"initial_mass": 1.0, "n_samples": 100},
    )
    body = r.json()
    s_values = body["s_values"]
    # Endpoints near zero
    assert abs(s_values[0]) < 1e-6
    assert abs(s_values[-1]) < 1e-3
    # Peak strictly between endpoints
    peak_idx = s_values.index(max(s_values))
    assert 0 < peak_idx < len(s_values) - 1


def test_page_curve_evaporating_phase_transition() -> None:
    """hawking phase early, island phase late, exactly one crossing."""
    r = client.get(
        "/api/holography/page_curve/evaporating",
        params={"initial_mass": 1.0, "n_samples": 200},
    )
    phases = r.json()["phase_labels"]
    assert "hawking" in phases
    assert "island" in phases
    first_island = phases.index("island")
    assert all(p == "hawking" for p in phases[:first_island])
    assert all(p == "island" for p in phases[first_island:])


def test_page_curve_evaporating_page_time_known() -> None:
    """Closed-form: t_P = (1 - sqrt(2)/4) * t_evap ≈ 0.6464 t_evap."""
    r = client.get(
        "/api/holography/page_curve/evaporating",
        params={"initial_mass": 1.0, "n_samples": 50},
    )
    body = r.json()
    t_evap = body["parameters"]["t_evap"]
    expected_tp = (1 - math.sqrt(2) / 4) * t_evap
    assert body["page_time"] == pytest.approx(expected_tp, rel=1e-9)


# ──────────────────────────────────────────────────────────────────
# Available metrics list reflects v2.5 truth (AdS now available)
# ──────────────────────────────────────────────────────────────────

def test_available_metrics_lists_ads_as_available() -> None:
    r = client.get("/api/metrics/available")
    metrics = r.json()["metrics"]
    ads_entry = next(m for m in metrics if m["name"].startswith("AdS"))
    assert ads_entry["available"] is True
    assert ads_entry["rest_endpoint"] == "/api/metrics/ads"
