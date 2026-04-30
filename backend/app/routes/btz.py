"""BTZ (3D AdS black hole) REST endpoint — third metric of v2.5.

Wraps spacetime_lab.metrics.BTZ (Phase 8, v0.8.0 — static / non-
rotating).  The rotating two-parameter (M, J) family lives in
spacetime_lab.holography.btz_rotating (v1.3) and will be exposed in
a follow-up patch.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from spacetime_lab.metrics import BTZ

router = APIRouter(prefix="/metrics")


class BTZProperties(BaseModel):
    """Physical observables of a non-rotating BTZ black hole."""

    horizon_radius: float = Field(..., description="Outer horizon r_+ (= r_-)")
    ads_radius: float = Field(..., description="AdS radius L")
    mass_parameter: float = Field(..., description="ADM mass M = r_+² / (8 G L²)")
    hawking_temperature: float = Field(..., description="T_H = r_+ / (2π L²)")
    bekenstein_hawking_entropy: float = Field(
        ..., description="S = π r_+ / (2 G_N) (= 2π · circumference / (8 G L²) · L²)"
    )
    thermal_beta: float = Field(..., description="β = 1/T_H")
    central_charge_brown_henneaux: float = Field(
        ..., description="c = 3L/(2 G_N) — same as for AdS_3 background"
    )
    line_element_latex: str = Field(..., description="BTZ line element")


@router.get("/btz", response_model=BTZProperties)
async def get_btz(
    horizon_radius: float = Query(1.0, gt=0, description="r_+ (must be > 0)"),
    ads_radius: float = Query(1.0, gt=0, description="L (must be > 0)"),
    G_N: float = Query(1.0, gt=0, description="Newton's constant"),
) -> BTZProperties:
    """Return non-rotating BTZ observables.

    Cardy / Brown-Henneaux verification (Strominger 1998):
    the boundary CFT central charge ``c = 3L/(2 G_N)`` and the BH
    entropy ``S = π r_+ / (2 G_N)`` reproduce each other via the
    Cardy formula.  Verified numerically in Phase 8 / v0.8.0.
    """
    try:
        bh = BTZ(horizon_radius=horizon_radius, ads_radius=ads_radius)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return BTZProperties(
        horizon_radius=horizon_radius,
        ads_radius=ads_radius,
        mass_parameter=float(bh.mass_parameter(G_N=G_N)),
        hawking_temperature=float(bh.hawking_temperature()),
        bekenstein_hawking_entropy=float(bh.bekenstein_hawking_entropy(G_N=G_N)),
        thermal_beta=float(bh.thermal_beta()),
        central_charge_brown_henneaux=3.0 * ads_radius / (2.0 * G_N),
        line_element_latex=bh.line_element_latex(),
    )
