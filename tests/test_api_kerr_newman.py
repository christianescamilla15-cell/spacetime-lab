"""Smoke tests for /api/metrics/kerr-newman (v3.2)."""

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


def test_kn_returns_200() -> None:
    r = client.get("/api/metrics/kerr-newman",
                   params={"mass": 1.0, "spin": 0.5, "charge": 0.3})
    assert r.status_code == 200


def test_kn_schwarzschild_limit() -> None:
    """a=0, Q=0 → standard Schwarzschild values."""
    body = client.get("/api/metrics/kerr-newman",
                      params={"mass": 1.0, "spin": 0.0, "charge": 0.0}).json()
    assert body["outer_horizon"] == pytest.approx(2.0, rel=1e-12)
    assert body["inner_horizon"] == pytest.approx(0.0, abs=1e-12)
    assert body["hawking_temperature"] == pytest.approx(
        1.0 / (8.0 * math.pi), rel=1e-12)
    assert body["bekenstein_hawking_entropy"] == pytest.approx(4.0 * math.pi, rel=1e-12)
    assert body["angular_velocity_horizon"] == pytest.approx(0.0, abs=1e-12)


def test_kn_kerr_limit_matches_kerr_endpoint() -> None:
    """Q = 0 → must match /api/metrics/kerr at same (M, a)."""
    kn = client.get("/api/metrics/kerr-newman",
                    params={"mass": 1.0, "spin": 0.5, "charge": 0.0}).json()
    kerr = client.get("/api/metrics/kerr",
                      params={"mass": 1.0, "spin": 0.5}).json()
    assert kn["outer_horizon"] == pytest.approx(kerr["outer_horizon"], rel=1e-12)
    assert kn["inner_horizon"] == pytest.approx(kerr["inner_horizon"], rel=1e-12)
    assert kn["angular_velocity_horizon"] == pytest.approx(
        kerr["angular_velocity_horizon"], rel=1e-12)
    assert kn["hawking_temperature"] == pytest.approx(
        kerr["hawking_temperature"], rel=1e-12)


def test_kn_rn_limit_matches_rn_endpoint() -> None:
    """a = 0 → must match /api/metrics/reissner-nordstrom."""
    kn = client.get("/api/metrics/kerr-newman",
                    params={"mass": 1.0, "spin": 0.0, "charge": 0.5}).json()
    rn = client.get("/api/metrics/reissner-nordstrom",
                    params={"mass": 1.0, "charge": 0.5}).json()
    assert kn["outer_horizon"] == pytest.approx(rn["outer_horizon"], rel=1e-12)
    assert kn["inner_horizon"] == pytest.approx(rn["inner_horizon"], rel=1e-12)
    assert kn["hawking_temperature"] == pytest.approx(
        rn["hawking_temperature"], rel=1e-12)
    assert kn["bekenstein_hawking_entropy"] == pytest.approx(
        rn["bekenstein_hawking_entropy"], rel=1e-12)


def test_kn_extremal() -> None:
    """a² + Q² = M² → r_± = M, T_H = 0."""
    body = client.get("/api/metrics/kerr-newman",
                      params={"mass": 1.0, "spin": 0.6, "charge": 0.8}).json()
    assert body["outer_horizon"] == pytest.approx(1.0, rel=1e-12)
    assert body["inner_horizon"] == pytest.approx(1.0, rel=1e-12)
    assert body["hawking_temperature"] == pytest.approx(0.0, abs=1e-12)
    assert body["is_extremal"] is True


def test_kn_horizon_root_relations() -> None:
    """Vieta's: r_+ + r_- = 2M, r_+ · r_- = a² + Q²."""
    for M, a, Q in [(1.0, 0.3, 0.4), (2.0, 1.0, 1.0), (1.0, 0.5, 0.5)]:
        body = client.get("/api/metrics/kerr-newman",
                          params={"mass": M, "spin": a, "charge": Q}).json()
        rp = body["outer_horizon"]
        rm = body["inner_horizon"]
        assert (rp + rm) == pytest.approx(2 * M, rel=1e-12)
        assert (rp * rm) == pytest.approx(a * a + Q * Q, rel=1e-12)


def test_kn_rejects_supercritical_a_squared_plus_q_squared() -> None:
    """Cosmic censorship at the API layer."""
    r = client.get("/api/metrics/kerr-newman",
                   params={"mass": 1.0, "spin": 0.7, "charge": 0.8})
    assert r.status_code == 400
    assert "cosmic censorship" in r.json()["detail"].lower()


def test_kn_listed_in_available_metrics() -> None:
    metrics = client.get("/api/metrics/available").json()["metrics"]
    kn = next((m for m in metrics if m["name"] == "Kerr-Newman"), None)
    assert kn is not None
    assert kn["available"] is True
