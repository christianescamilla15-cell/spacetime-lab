"""Penrose diagram SVG endpoint — fourth new surface of v2.5.

Reuses spacetime_lab.diagrams.render.render_svg (v1.5.0) which
renders to a pure standalone <svg>...</svg> string with no runtime
deps.  Frontend embeds the returned SVG directly.

Two diagram kinds for now:
    minkowski       - causal structure of flat spacetime
    schwarzschild   - the four-region maximally extended Schwarzschild
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from spacetime_lab.diagrams.penrose import (
    MinkowskiPenrose,
    SchwarzschildPenrose,
)
from spacetime_lab.diagrams.render import render_svg

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
    kind: str = Path(..., description="Diagram kind: minkowski or schwarzschild"),
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
    kind: str = Path(..., description="Diagram kind"),
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
