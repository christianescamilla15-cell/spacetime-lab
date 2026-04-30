"""Smoke tests for v2.5 BTZ + Penrose endpoints."""

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
# BTZ endpoint
# ──────────────────────────────────────────────────────────────────

def test_btz_canonical_values_at_unit_params() -> None:
    """At r_+ = L = G_N = 1: T_H = 1/(2π), S_BH = π/2, β = 2π,
    Brown-Henneaux c = 1.5, mass parameter M = 1/8."""
    r = client.get("/api/metrics/btz", params={
        "horizon_radius": 1.0, "ads_radius": 1.0, "G_N": 1.0,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["hawking_temperature"] == pytest.approx(1 / (2 * math.pi), rel=1e-12)
    assert body["bekenstein_hawking_entropy"] == pytest.approx(math.pi / 2, rel=1e-12)
    assert body["thermal_beta"] == pytest.approx(2 * math.pi, rel=1e-12)
    assert body["central_charge_brown_henneaux"] == pytest.approx(1.5, rel=1e-12)
    assert body["mass_parameter"] == pytest.approx(1 / 8, rel=1e-12)


def test_btz_strominger_cardy_match() -> None:
    """Cardy formula reproduces BH entropy: S = π r_+ / (2 G_N).
    Verify the Cardy ratio is exactly 1 for a few parameter combos."""
    for r_plus, L in [(1.0, 1.0), (2.0, 1.0), (1.0, 2.0), (0.5, 0.7)]:
        r = client.get("/api/metrics/btz", params={
            "horizon_radius": r_plus, "ads_radius": L, "G_N": 1.0,
        })
        body = r.json()
        s_cardy_expected = math.pi * r_plus / (2.0 * 1.0)
        assert body["bekenstein_hawking_entropy"] == pytest.approx(
            s_cardy_expected, rel=1e-12
        )


def test_btz_temperature_scales_with_horizon() -> None:
    """T_H = r_+ / (2π L²): doubling r_+ doubles T."""
    r1 = client.get("/api/metrics/btz", params={
        "horizon_radius": 1.0, "ads_radius": 1.0,
    }).json()
    r2 = client.get("/api/metrics/btz", params={
        "horizon_radius": 2.0, "ads_radius": 1.0,
    }).json()
    assert r2["hawking_temperature"] == pytest.approx(
        2.0 * r1["hawking_temperature"], rel=1e-12
    )


def test_btz_rejects_non_positive_horizon() -> None:
    r = client.get("/api/metrics/btz", params={
        "horizon_radius": 0.0, "ads_radius": 1.0,
    })
    assert r.status_code == 422  # gt=0 constraint


def test_available_metrics_lists_btz_as_available() -> None:
    r = client.get("/api/metrics/available")
    metrics = r.json()["metrics"]
    btz = next(m for m in metrics if m["name"] == "BTZ")
    assert btz["available"] is True
    assert btz["rest_endpoint"] == "/api/metrics/btz"


# ──────────────────────────────────────────────────────────────────
# Penrose SVG endpoint
# ──────────────────────────────────────────────────────────────────

def test_penrose_minkowski_svg_returns_valid_xml() -> None:
    r = client.get("/api/diagrams/penrose/minkowski/svg")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    body = r.text
    assert body.lstrip().startswith("<svg") or body.lstrip().startswith("<?xml")
    assert "</svg>" in body


def test_penrose_schwarzschild_svg_includes_path_groups() -> None:
    """v1.5 renderer groups paths into <g class="kind-..."> tags."""
    r = client.get(
        "/api/diagrams/penrose/schwarzschild/svg",
        params={"mass": 1.0, "width": 400, "height": 400},
    )
    body = r.text
    assert r.status_code == 200
    # at least one kind group should be present
    assert 'class="kind-' in body or "kind-" in body


def test_penrose_unknown_kind_400() -> None:
    r = client.get("/api/diagrams/penrose/de_sitter/svg")
    assert r.status_code == 400
    assert "supported" in r.json()["detail"].lower()


def test_penrose_manifest_minkowski() -> None:
    r = client.get("/api/diagrams/penrose/minkowski/manifest")
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "minkowski"
    assert isinstance(body["regions"], list)
    assert isinstance(body["physical_coordinates"], list)
    assert isinstance(body["infinities"], list)


def test_penrose_manifest_schwarzschild_has_4_regions() -> None:
    """Maximally extended Schwarzschild has regions I, II, III, IV."""
    r = client.get(
        "/api/diagrams/penrose/schwarzschild/manifest",
        params={"mass": 1.0},
    )
    body = r.json()
    assert len(body["regions"]) == 4


def test_penrose_available_lists_two_kinds() -> None:
    r = client.get("/api/diagrams/penrose/available")
    body = r.json()
    assert set(body["kinds"]) == {"minkowski", "schwarzschild"}
    assert "reissner_nordstrom" in body["deferred"]


def test_penrose_svg_width_height_constraints() -> None:
    """Width must be in [200, 1200]."""
    too_small = client.get("/api/diagrams/penrose/minkowski/svg",
                            params={"width": 50})
    assert too_small.status_code == 422
    too_big = client.get("/api/diagrams/penrose/minkowski/svg",
                          params={"width": 5000})
    assert too_big.status_code == 422
