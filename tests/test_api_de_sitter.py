"""Smoke tests for /api/metrics/de-sitter (v3.2 partial)."""

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


def test_ds_returns_200() -> None:
    r = client.get("/api/metrics/de-sitter", params={"radius": 1.0})
    assert r.status_code == 200


def test_ds_canonical_at_unit_radius() -> None:
    """L = 1: r_c = 1, Λ = 3, H = 1, T = 1/(2π), A = 4π, S = π, R = 12."""
    body = client.get("/api/metrics/de-sitter", params={"radius": 1.0}).json()
    assert body["cosmological_horizon"] == pytest.approx(1.0, rel=1e-12)
    assert body["cosmological_constant"] == pytest.approx(3.0, rel=1e-12)
    assert body["hubble_parameter"] == pytest.approx(1.0, rel=1e-12)
    assert body["hawking_temperature"] == pytest.approx(1.0 / (2.0 * math.pi), rel=1e-12)
    assert body["horizon_area"] == pytest.approx(4.0 * math.pi, rel=1e-12)
    assert body["bekenstein_hawking_entropy"] == pytest.approx(math.pi, rel=1e-12)
    assert body["ricci_scalar"] == pytest.approx(12.0, rel=1e-12)


def test_ds_lambda_scales_as_inverse_L_squared() -> None:
    """Λ(L=2) / Λ(L=1) = 1/4."""
    a = client.get("/api/metrics/de-sitter", params={"radius": 1.0}).json()
    b = client.get("/api/metrics/de-sitter", params={"radius": 2.0}).json()
    assert b["cosmological_constant"] / a["cosmological_constant"] == \
        pytest.approx(0.25, rel=1e-12)


def test_ds_rejects_non_positive_radius() -> None:
    r = client.get("/api/metrics/de-sitter", params={"radius": -1.0})
    assert r.status_code == 422  # Query gt=0


def test_ds_listed_in_available_metrics() -> None:
    metrics = client.get("/api/metrics/available").json()["metrics"]
    ds = next((m for m in metrics if m["name"] == "de Sitter"), None)
    assert ds is not None
    assert ds["available"] is True
