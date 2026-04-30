"""Smoke tests for the v3.1 Reissner-Nordström REST endpoint."""

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


def test_rn_returns_200_for_valid_inputs() -> None:
    r = client.get(
        "/api/metrics/reissner-nordstrom",
        params={"mass": 1.0, "charge": 0.5},
    )
    assert r.status_code == 200


def test_rn_response_schema_complete() -> None:
    r = client.get(
        "/api/metrics/reissner-nordstrom",
        params={"mass": 1.0, "charge": 0.6},
    )
    body = r.json()
    expected = {
        "mass", "charge", "q_over_m",
        "outer_horizon", "inner_horizon", "photon_sphere", "isco",
        "surface_gravity", "hawking_temperature", "horizon_area",
        "bekenstein_hawking_entropy", "is_extremal", "line_element_latex",
    }
    assert expected.issubset(body.keys())


def test_rn_at_q_zero_recovers_schwarzschild() -> None:
    """Q = 0 must give Schwarzschild values exactly."""
    r = client.get(
        "/api/metrics/reissner-nordstrom",
        params={"mass": 1.0, "charge": 0.0},
    )
    body = r.json()
    assert body["outer_horizon"] == pytest.approx(2.0, rel=1e-12)
    assert body["inner_horizon"] == pytest.approx(0.0, abs=1e-12)
    assert body["photon_sphere"] == pytest.approx(3.0, rel=1e-12)
    assert body["isco"] == pytest.approx(6.0, rel=1e-9)
    assert body["hawking_temperature"] == pytest.approx(
        1.0 / (8.0 * math.pi), rel=1e-12,
    )
    assert body["bekenstein_hawking_entropy"] == pytest.approx(
        4.0 * math.pi, rel=1e-12,
    )
    assert body["is_extremal"] is False


def test_rn_extremal_horizons_merge() -> None:
    r = client.get(
        "/api/metrics/reissner-nordstrom",
        params={"mass": 1.0, "charge": 1.0},
    )
    body = r.json()
    assert body["outer_horizon"] == pytest.approx(1.0, rel=1e-12)
    assert body["inner_horizon"] == pytest.approx(1.0, rel=1e-12)
    assert body["hawking_temperature"] == pytest.approx(0.0, abs=1e-12)
    assert body["is_extremal"] is True


def test_rn_vieta_root_relations() -> None:
    """r_+ + r_- = 2M and r_+ · r_- = Q² for any sub-extremal Q."""
    for M, Q in [(1.0, 0.3), (2.0, 1.5), (1.0, 0.999), (5.0, 2.5)]:
        body = client.get(
            "/api/metrics/reissner-nordstrom",
            params={"mass": M, "charge": Q},
        ).json()
        rp = body["outer_horizon"]
        rm = body["inner_horizon"]
        assert (rp + rm) == pytest.approx(2 * M, rel=1e-12)
        assert (rp * rm) == pytest.approx(Q * Q, rel=1e-12)


def test_rn_isco_decreases_monotonically_with_charge() -> None:
    """Spot-check: ISCO at Q=0 > ISCO at Q=0.5 > ISCO at Q=0.9."""
    iscos = []
    for Q in [0.0, 0.5, 0.9]:
        body = client.get(
            "/api/metrics/reissner-nordstrom",
            params={"mass": 1.0, "charge": Q},
        ).json()
        iscos.append(body["isco"])
    assert iscos[0] > iscos[1] > iscos[2]


def test_rn_rejects_supercritical_charge() -> None:
    """Cosmic censorship: |Q| > M is forbidden."""
    r = client.get(
        "/api/metrics/reissner-nordstrom",
        params={"mass": 1.0, "charge": 1.5},
    )
    assert r.status_code == 400
    assert "cosmic censorship" in r.json()["detail"].lower()


def test_rn_rejects_negative_mass() -> None:
    r = client.get(
        "/api/metrics/reissner-nordstrom",
        params={"mass": -1.0, "charge": 0.0},
    )
    assert r.status_code == 422


def test_available_metrics_lists_rn_as_available() -> None:
    r = client.get("/api/metrics/available")
    metrics = r.json()["metrics"]
    rn_entry = next(m for m in metrics if m["name"] == "Reissner-Nordström")
    assert rn_entry["available"] is True
    assert rn_entry["rest_endpoint"] == "/api/metrics/reissner-nordstrom"
