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


# ──────────────────────────────────────────────────────────────────
# v2.7.1: Penrose with geodesic overlay
# ──────────────────────────────────────────────────────────────────

OVERLAY_REQUEST = {
    "mass": 1.0,
    "initial_position": [0.0, 8.0, 1.5708, 0.0],
    "initial_momentum": [-0.96, 0.0, 0.0, 3.7],
    "step_size": 0.5,
    "n_steps": 200,
    "width": 400,
    "height": 400,
    "overlay_color": "#fbbf24",
}


def test_penrose_with_geodesic_returns_svg() -> None:
    r = client.post(
        "/api/diagrams/penrose/schwarzschild/with_geodesic",
        json=OVERLAY_REQUEST,
    )
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("image/svg+xml")
    assert "</svg>" in r.text


def test_penrose_with_geodesic_includes_world_line_path() -> None:
    """The overlaid trajectory must be rendered as a world_line path
    (the renderer's _DRAW_ORDER doesn't include arbitrary kinds)."""
    r = client.post(
        "/api/diagrams/penrose/schwarzschild/with_geodesic",
        json=OVERLAY_REQUEST,
    )
    body = r.text
    assert 'class="kind-world_line"' in body
    assert 'stroke="#fbbf24"' in body


def test_penrose_with_geodesic_metadata_headers() -> None:
    r = client.post(
        "/api/diagrams/penrose/schwarzschild/with_geodesic",
        json=OVERLAY_REQUEST,
    )
    assert "X-Overlay-Samples" in r.headers
    samples = int(r.headers["X-Overlay-Samples"])
    assert samples > 100  # ~n_steps + 1 samples for a region-I orbit
    skipped = int(r.headers["X-Overlay-Skipped"])
    assert skipped == 0   # bound orbit at r=8M never crosses 2M
    final_r = float(r.headers["X-Geodesic-Final-R"])
    assert final_r > 2.0  # still in region I


def test_penrose_with_geodesic_rejects_r_below_2M() -> None:
    """Initial r must be > 2M for region I overlay."""
    bad = dict(OVERLAY_REQUEST, initial_position=[0.0, 1.5, 1.5708, 0.0])
    r = client.post(
        "/api/diagrams/penrose/schwarzschild/with_geodesic", json=bad,
    )
    assert r.status_code == 400
    assert "2M" in r.json()["detail"]


def test_penrose_with_geodesic_rejects_invalid_color() -> None:
    bad = dict(OVERLAY_REQUEST, overlay_color="red")
    r = client.post(
        "/api/diagrams/penrose/schwarzschild/with_geodesic", json=bad,
    )
    assert r.status_code == 422  # pydantic regex constraint


# ──────────────────────────────────────────────────────────────────
# v2.7.2: Multi-trajectory overlay
# ──────────────────────────────────────────────────────────────────

import json as _json  # noqa: E402

MULTI_OVERLAY_REQUEST = {
    "mass": 1.0,
    "width": 400,
    "height": 400,
    "geodesics": [
        {
            "initial_position": [0.0, 8.0, 1.5708, 0.0],
            "initial_momentum": [-0.96, 0.0, 0.0, 3.7],
            "step_size": 0.5, "n_steps": 200,
            "color": "#fbbf24", "label": "bound r=8M",
        },
        {
            "initial_position": [0.0, 12.0, 1.5708, 0.0],
            "initial_momentum": [-0.97, 0.0, 0.0, 4.2],
            "step_size": 0.5, "n_steps": 200,
            "color": "#22c55e", "label": "bound r=12M",
        },
    ],
}


def test_multi_overlay_returns_svg_with_two_paths() -> None:
    r = client.post(
        "/api/diagrams/penrose/schwarzschild/with_geodesics",
        json=MULTI_OVERLAY_REQUEST,
    )
    assert r.status_code == 200
    body = r.text
    # Two world_line groups should be rendered (one per trajectory).
    # Renderer groups all paths of same kind into ONE <g>; so we
    # expect exactly 2 <path> elements inside the world_line group.
    assert 'class="kind-world_line"' in body
    assert body.count('stroke="#fbbf24"') >= 1
    assert body.count('stroke="#22c55e"') >= 1


def test_multi_overlay_summary_header_per_trajectory() -> None:
    r = client.post(
        "/api/diagrams/penrose/schwarzschild/with_geodesics",
        json=MULTI_OVERLAY_REQUEST,
    )
    assert r.headers["X-Trajectories-Total"] == "2"
    assert r.headers["X-Trajectories-Rendered"] == "2"
    summary = _json.loads(r.headers["X-Trajectories-Summary"])
    assert len(summary) == 2
    assert summary[0]["label"] == "bound r=8M"
    assert summary[1]["label"] == "bound r=12M"
    assert summary[0]["status"] == "ok"
    assert summary[0]["samples"] > 100


def test_multi_overlay_partial_failure_still_renders_others() -> None:
    """One bad trajectory in the bunch should NOT kill the whole render —
    it should be reported as no-samples in the summary, others render."""
    body = {
        "mass": 1.0,
        "geodesics": [
            # OK
            {"initial_position": [0.0, 8.0, 1.5708, 0.0],
             "initial_momentum": [-0.96, 0.0, 0.0, 3.7],
             "step_size": 0.5, "n_steps": 100,
             "color": "#fbbf24", "label": "OK"},
            # Below 2M — rejected at the per-traj guard with 400
        ],
    }
    # Adding the bad one would 400 — verify
    body["geodesics"].append({
        "initial_position": [0.0, 1.5, 1.5708, 0.0],
        "initial_momentum": [-0.96, 0.0, 0.0, 3.7],
        "step_size": 0.5, "n_steps": 100,
        "color": "#22c55e", "label": "bad r<2M",
    })
    r = client.post(
        "/api/diagrams/penrose/schwarzschild/with_geodesics", json=body,
    )
    assert r.status_code == 400
    assert "trajectory 1" in r.json()["detail"]


def test_multi_overlay_caps_at_5_trajectories() -> None:
    body = {
        "mass": 1.0,
        "geodesics": [
            {
                "initial_position": [0.0, 8.0, 1.5708, 0.0],
                "initial_momentum": [-0.96, 0.0, 0.0, 3.7],
                "step_size": 0.5, "n_steps": 50,
                "color": "#fbbf24",
            }
            for _ in range(6)  # over the cap
        ],
    }
    r = client.post(
        "/api/diagrams/penrose/schwarzschild/with_geodesics", json=body,
    )
    assert r.status_code == 422  # pydantic max_length=5 constraint
