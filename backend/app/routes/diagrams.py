"""Penrose diagram SVG endpoints.

v2.5: GET endpoints for the two supported chart kinds.
v2.7.1: POST endpoint that overlays a Schwarzschild geodesic onto the
maximally-extended diagram by injecting a new Path into the Scene
before rendering.

Why server-side overlay (not frontend SVG injection):
The render_svg bounding box is auto-computed from the Scene contents.
If the frontend tried to draw an overlay using its own coords, those
would not align with the existing diagram's pixel mapping.  The only
clean way is to add the geodesic-as-a-Path to the Scene and let the
existing renderer place everything in a single coordinate system.
"""

from __future__ import annotations

import numpy as np
from fastapi import APIRouter, HTTPException, Path as FastApiPath, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from spacetime_lab.diagrams.penrose import (
    MinkowskiPenrose,
    Path as DiagramPath,
    PathStyle,
    SchwarzschildPenrose,
    Vec2,
)
from spacetime_lab.diagrams.render import render_svg
from spacetime_lab.geodesics import GeodesicIntegrator, GeodesicState
from spacetime_lab.metrics import Schwarzschild

router = APIRouter(prefix="/diagrams")


class PenroseManifest(BaseModel):
    """Metadata about a Penrose diagram (regions, infinities, etc.)."""

    kind: str
    name: str
    regions: list[int] = Field(..., description="Coordinate-chart region indices")
    physical_coordinates: list[str] = Field(...)
    infinities: list[str] = Field(..., description="Named infinities (i+, i-, i0, ...)")


SUPPORTED_KINDS = {"minkowski", "schwarzschild"}


def _build_chart(kind: str, mass: float = 1.0):
    if kind == "minkowski":
        return MinkowskiPenrose()
    if kind == "schwarzschild":
        return SchwarzschildPenrose(mass=mass)
    raise HTTPException(
        status_code=400,
        detail=f"unknown kind '{kind}'; supported: {sorted(SUPPORTED_KINDS)}",
    )


@router.get("/penrose/{kind}/svg", response_class=Response)
async def get_penrose_svg(
    kind: str = FastApiPath(..., description="Diagram kind: minkowski or schwarzschild"),
    mass: float = Query(1.0, gt=0, description="(Schwarzschild only) mass M"),
    width: int = Query(520, ge=200, le=1200),
    height: int = Query(520, ge=200, le=1200),
    show_labels: bool = Query(True),
) -> Response:
    """Return the Penrose diagram as a raw SVG string (image/svg+xml)."""
    chart = _build_chart(kind, mass=mass)
    try:
        scene = chart.to_scene()
        svg = render_svg(
            scene=scene,
            width=width,
            height=height,
            show_labels=show_labels,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/penrose/{kind}/manifest", response_model=PenroseManifest)
async def get_penrose_manifest(
    kind: str = FastApiPath(..., description="Diagram kind"),
    mass: float = Query(1.0, gt=0),
) -> PenroseManifest:
    """Return metadata about the diagram (regions, infinities, coord names).

    Used by the frontend to label hover regions and tooltips."""
    chart = _build_chart(kind, mass=mass)
    try:
        infinities = [inf.name for inf in chart.infinities()]
    except Exception:
        infinities = []
    return PenroseManifest(
        kind=kind,
        name=chart.name,
        regions=list(chart.regions),
        physical_coordinates=list(chart.physical_coordinate_names),
        infinities=infinities,
    )


@router.get("/penrose/available")
async def list_available_penrose() -> dict:
    """List Penrose diagram kinds that the API can render."""
    return {
        "kinds": sorted(SUPPORTED_KINDS),
        "deferred": ["reissner_nordstrom", "de_sitter", "flrw"],
    }


# ──────────────────────────────────────────────────────────────────
# v2.7.1: Schwarzschild Penrose + geodesic overlay
# ──────────────────────────────────────────────────────────────────

class GeodesicOverlayRequest(BaseModel):
    """Body for POST /api/diagrams/penrose/schwarzschild/with_geodesic.

    Single-geodesic legacy form (kept for backward compatibility with
    v2.7.1).  For multiple overlays at once use the new
    `/with_geodesics` (plural) endpoint.
    """

    mass: float = Field(1.0, gt=0, description="BH mass M")
    initial_position: list[float] = Field(
        ...,
        description="x = (t, r, theta, phi); r must be > 2M for region I overlay",
        min_length=4, max_length=4,
    )
    initial_momentum: list[float] = Field(
        ...,
        description="p_mu (covariant)",
        min_length=4, max_length=4,
    )
    step_size: float = Field(0.5, gt=0, le=10)
    n_steps: int = Field(1000, ge=10, le=10_000)
    width: int = Field(620, ge=200, le=1200)
    height: int = Field(620, ge=200, le=1200)
    overlay_color: str = Field(
        "#fbbf24", pattern=r"^#[0-9a-fA-F]{6}$",
        description="Stroke color of the overlaid trajectory (#RRGGBB)",
    )


class GeodesicSpec(BaseModel):
    """One trajectory in a multi-overlay request."""
    initial_position: list[float] = Field(..., min_length=4, max_length=4)
    initial_momentum: list[float] = Field(..., min_length=4, max_length=4)
    step_size: float = Field(0.5, gt=0, le=10)
    n_steps: int = Field(1000, ge=10, le=10_000)
    color: str = Field("#fbbf24", pattern=r"^#[0-9a-fA-F]{6}$")
    label: str | None = Field(None, max_length=80)


class MultiGeodesicOverlayRequest(BaseModel):
    """Body for POST /api/diagrams/penrose/schwarzschild/with_geodesics.

    All trajectories are rendered on the same Schwarzschild Penrose
    diagram, each with its own colour.  Hard cap of 5 trajectories
    per request to bound payload + render time.
    """
    mass: float = Field(1.0, gt=0)
    width: int = Field(620, ge=200, le=1200)
    height: int = Field(620, ge=200, le=1200)
    geodesics: list[GeodesicSpec] = Field(..., min_length=1, max_length=5)


@router.post("/penrose/schwarzschild/with_geodesic", response_class=Response)
async def schwarzschild_penrose_with_geodesic(
    req: GeodesicOverlayRequest,
) -> Response:
    """Render the maximally-extended Schwarzschild Penrose diagram with
    a region-I geodesic projected onto it.

    The trajectory comes from spacetime_lab.geodesics on a fresh
    Schwarzschild(M).  Each (t, r) sample with r > 2M is mapped to the
    chart's compact (U, V) via SchwarzschildPenrose.physical_to_compact;
    samples with r ≤ 2M (interior — region II) are skipped, since the
    chart's region-I projection is undefined there.  A note about
    skipped samples is added as an SVG <title> attribute on the path.

    The overlay is added to the Scene as a new DiagramPath BEFORE
    rendering, so the existing render_svg bounding-box computation
    naturally accommodates it (no separate coordinate-system risk).
    """
    M = req.mass
    chart = SchwarzschildPenrose(mass=M)
    bh = Schwarzschild(mass=M)
    integrator = GeodesicIntegrator(bh)

    try:
        state0 = GeodesicState(
            x=np.array(req.initial_position, dtype=float),
            p=np.array(req.initial_momentum, dtype=float),
        )
    except Exception as exc:
        raise HTTPException(400, f"initial state error: {exc}") from exc

    if state0.x[1] <= 2.0 * M:
        raise HTTPException(
            400,
            f"r must be > 2M for the region-I overlay "
            f"(got r={state0.x[1]}, 2M={2*M})",
        )

    try:
        states = integrator.integrate(
            state0, h=req.step_size, n_steps=req.n_steps,
        )
    except Exception as exc:
        raise HTTPException(500, f"integration failed: {exc}") from exc

    # Project (t, r) → (U, V) in compact coords; skip samples with r ≤ 2M
    pts: list[Vec2] = []
    skipped = 0
    for s in states:
        t_val = float(s.x[0])
        r_val = float(s.x[1])
        if r_val <= 2.0 * M + 1e-9:
            skipped += 1
            continue
        try:
            uv = chart.physical_to_compact(1, t=t_val, r=r_val)
            pts.append(uv)
        except (ValueError, ZeroDivisionError, OverflowError):
            skipped += 1

    if len(pts) < 2:
        raise HTTPException(
            400,
            "no valid region-I samples to overlay "
            "(geodesic may have plunged immediately or projection failed)",
        )

    # Build the scene + add the overlay path
    scene = chart.to_scene()
    # Use kind="world_line" — the renderer's _DRAW_ORDER includes it,
    # and PathStyle.stroke overrides the default colour at render time
    # (render_svg line 314).  Drawn AFTER boundaries/horizons/singularity
    # so the trajectory sits on top of them.
    overlay_path = DiagramPath(
        kind="world_line",
        points=pts,
        style=PathStyle(stroke=req.overlay_color, width=2.0),
    )
    scene.add(overlay_path)

    svg = render_svg(
        scene=scene,
        width=req.width,
        height=req.height,
        show_labels=True,
    )

    # Optional metadata for the frontend (skipped count) goes in a header
    headers = {
        "X-Overlay-Samples": str(len(pts)),
        "X-Overlay-Skipped": str(skipped),
        "X-Geodesic-Final-R": f"{float(states[-1].x[1]):.4f}",
    }
    return Response(content=svg, media_type="image/svg+xml", headers=headers)


# ──────────────────────────────────────────────────────────────────
# v2.7.2: Multiple-geodesic overlay (closes 1 of 2 v2.7.2 items)
# ──────────────────────────────────────────────────────────────────

@router.post(
    "/penrose/schwarzschild/with_geodesics",
    response_class=Response,
)
async def schwarzschild_penrose_with_multiple_geodesics(
    req: MultiGeodesicOverlayRequest,
) -> Response:
    """Render the Schwarzschild Penrose diagram with up to 5 region-I
    geodesics overlaid, each with its own colour.

    Implementation pattern matches the singular endpoint but loops over
    the request list and adds one DiagramPath per trajectory.

    Region tracking — honest scope deferral
    ----------------------------------------
    All overlays here use ``region=1`` (the exterior, r > 2M).  A
    plunging geodesic crosses the horizon at r = 2M, but in
    Schwarzschild coordinates t → ∞ at the horizon, so the integrator
    asymptotes there and never produces samples with r < 2M.  Real
    region-II overlays would require switching the integrator to
    Kruskal-Szekeres coordinates (a substantial new module — the
    integrator currently lambdifies the metric_tensor returned by
    Schwarzschild, which is in Schwarzschild coords).  Tracked as a
    separate v2.7.3 task.
    """
    M = req.mass
    chart = SchwarzschildPenrose(mass=M)
    bh = Schwarzschild(mass=M)
    integrator = GeodesicIntegrator(bh)

    scene = chart.to_scene()
    per_traj_summary: list[dict] = []

    for idx, g in enumerate(req.geodesics):
        try:
            state0 = GeodesicState(
                x=np.array(g.initial_position, dtype=float),
                p=np.array(g.initial_momentum, dtype=float),
            )
        except Exception as exc:
            raise HTTPException(
                400,
                f"trajectory {idx}: initial state error: {exc}",
            ) from exc

        if state0.x[1] <= 2.0 * M:
            raise HTTPException(
                400,
                f"trajectory {idx}: r must be > 2M (got r={state0.x[1]})",
            )

        try:
            states = integrator.integrate(state0, h=g.step_size, n_steps=g.n_steps)
        except Exception as exc:
            raise HTTPException(
                500, f"trajectory {idx}: integration failed: {exc}",
            ) from exc

        pts: list[Vec2] = []
        skipped = 0
        for s in states:
            r_val = float(s.x[1])
            if r_val <= 2.0 * M + 1e-9:
                skipped += 1
                continue
            try:
                uv = chart.physical_to_compact(1, t=float(s.x[0]), r=r_val)
                pts.append(uv)
            except (ValueError, ZeroDivisionError, OverflowError):
                skipped += 1

        if len(pts) < 2:
            # One bad trajectory in the bunch shouldn't kill the whole
            # render — record it in the summary but skip rendering.
            per_traj_summary.append({
                "index": idx,
                "label": g.label,
                "samples": 0,
                "skipped": skipped,
                "status": "no valid region-I samples",
            })
            continue

        scene.add(DiagramPath(
            kind="world_line",
            points=pts,
            style=PathStyle(stroke=g.color, width=2.0),
        ))
        per_traj_summary.append({
            "index": idx,
            "label": g.label,
            "samples": len(pts),
            "skipped": skipped,
            "final_r": round(float(states[-1].x[1]), 4),
            "color": g.color,
            "status": "ok",
        })

    svg = render_svg(
        scene=scene, width=req.width, height=req.height, show_labels=True,
    )

    headers = {
        "X-Trajectories-Total": str(len(req.geodesics)),
        "X-Trajectories-Rendered": str(
            sum(1 for t in per_traj_summary if t["status"] == "ok")
        ),
    }
    # Encode per-trajectory summary as JSON in another header
    import json as _json
    headers["X-Trajectories-Summary"] = _json.dumps(per_traj_summary)
    return Response(content=svg, media_type="image/svg+xml", headers=headers)
