"""Smoke tests for the v2.6 geodesics integration endpoint.

Cross-checks the FastAPI wrapper against:
  - the symplectic integrator's documented conservation properties
    (E and L_z exact to machine precision for Boyer-Lindquist Kerr,
    Carter Q to high precision)
  - the Schwarzschild limit (a → 0) which must remove Carter Q drift
  - validation: bad shapes, out-of-range params
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


# Reference Kerr geodesic — moderate prograde inclined orbit at r=10M
KERR_EXAMPLE = {
    "metric": "kerr",
    "params": {"mass": 1.0, "spin": 0.5},
    "initial_position": [0.0, 10.0, 1.5708, 0.0],
    "initial_momentum": [-0.94, 0.0, 1.5, 3.0],
    "step_size": 0.5,
    "n_steps": 200,
    "decimation": 5,
}


def test_kerr_integration_returns_well_formed_response() -> None:
    r = client.post("/api/geodesics/integrate", json=KERR_EXAMPLE)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "trajectory" in body
    assert "drift_residuals" in body
    assert "metadata" in body
    assert len(body["trajectory"]) > 0


def test_kerr_trajectory_length_respects_decimation() -> None:
    r = client.post("/api/geodesics/integrate", json=KERR_EXAMPLE)
    body = r.json()
    # n_steps=200 with decimation=5 → 40 + 1 (state0) + maybe final = ~41-42
    n = len(body["trajectory"])
    assert 40 <= n <= 45
    assert body["metadata"]["n_returned_points"] == n


def test_kerr_E_and_Lz_conserved_to_machine_precision() -> None:
    """For Boyer-Lindquist Kerr, t and φ are cyclic so E = -p_t and
    L_z = p_φ are conserved exactly by the implicit-midpoint integrator."""
    r = client.post("/api/geodesics/integrate", json=KERR_EXAMPLE)
    drift = r.json()["drift_residuals"]
    # Tighten the gate as the integrator improves; 1e-9 leaves room for
    # accumulated fsolve tolerance (rtol=1e-12, n=200 steps).
    assert drift["E_drift"] < 1e-9, f"E drift too large: {drift['E_drift']}"
    assert drift["L_z_drift"] < 1e-9, f"L_z drift: {drift['L_z_drift']}"


def test_kerr_returns_carter_constant() -> None:
    """Carter's Q is defined for Kerr; should be present and finite."""
    r = client.post("/api/geodesics/integrate", json=KERR_EXAMPLE)
    samples = r.json()["trajectory"]
    Qs = [s["Q_carter"] for s in samples]
    assert all(q is not None for q in Qs)
    # Q is NOT conserved exactly by the implicit-midpoint integrator (only
    # E and L_z are, because t and φ are cyclic in Boyer-Lindquist).
    # Per the module docstring, Q drifts at O(h²) per step.  With h=0.5,
    # n_steps=200, an absolute drift around 1e-4 is expected.  We gate at
    # 1e-3 so we'd notice a regression that broke the integrator quality
    # without false-positiving on legitimate 2nd-order accuracy.
    Q_drift = max(Qs) - min(Qs)
    assert Q_drift < 1e-3, f"Carter Q drift exceeds 2nd-order budget: {Q_drift}"


def test_schwarzschild_integration_works() -> None:
    """Schwarzschild has no Carter constant; the API returns Q_carter=null."""
    payload = {
        "metric": "schwarzschild",
        "params": {"mass": 1.0},
        "initial_position": [0.0, 10.0, 1.5708, 0.0],
        # E=-p_t, L=p_φ; mass-shell constraint is satisfied by p_r=0 here
        "initial_momentum": [-0.95, 0.0, 0.0, 4.0],
        "step_size": 0.5,
        "n_steps": 100,
        "decimation": 4,
    }
    r = client.post("/api/geodesics/integrate", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert all(s["Q_carter"] is None for s in body["trajectory"])
    assert body["drift_residuals"]["Q_carter_drift"] is None


# ──────────────────────────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────────────────────────

def test_rejects_unknown_metric() -> None:
    payload = dict(KERR_EXAMPLE, metric="reissner_nordstrom")
    r = client.post("/api/geodesics/integrate", json=payload)
    # FastAPI validates Literal at the Pydantic layer → 422
    assert r.status_code == 422


def test_rejects_wrong_position_shape() -> None:
    payload = dict(KERR_EXAMPLE, initial_position=[0.0, 10.0, 1.5708])
    r = client.post("/api/geodesics/integrate", json=payload)
    assert r.status_code == 422


def test_rejects_n_steps_above_cap() -> None:
    payload = dict(KERR_EXAMPLE, n_steps=999_999)
    r = client.post("/api/geodesics/integrate", json=payload)
    assert r.status_code == 422  # le=20_000 constraint


def test_rejects_zero_step_size() -> None:
    payload = dict(KERR_EXAMPLE, step_size=0.0)
    r = client.post("/api/geodesics/integrate", json=payload)
    assert r.status_code == 422  # gt=0


def test_rejects_too_many_returned_points() -> None:
    """Even within step cap, decimation=1 with large n_steps would
    return > MAX_RETURNED_POINTS — that should 400 (logical, not Pydantic)."""
    payload = dict(KERR_EXAMPLE, n_steps=20_000, decimation=1)
    r = client.post("/api/geodesics/integrate", json=payload)
    assert r.status_code == 400
    assert "decimation" in r.json()["detail"].lower()


# ──────────────────────────────────────────────────────────────────
# Convenience example endpoint
# ──────────────────────────────────────────────────────────────────

def test_example_endpoint_returns_valid_payload() -> None:
    r = client.get("/api/geodesics/example")
    assert r.status_code == 200
    payload = r.json()
    # The example must itself be a valid request body
    r2 = client.post("/api/geodesics/integrate", json=payload)
    assert r2.status_code == 200, r2.text
