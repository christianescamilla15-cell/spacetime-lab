"""Reissner-Nordström REST endpoint — first item of v3.1 backlog.

Wraps spacetime_lab.metrics.ReissnerNordstrom with one GET endpoint.
Cosmic censorship validated at the FastAPI Query layer.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from spacetime_lab.metrics import ReissnerNordstrom

router = APIRouter(prefix="/metrics")


class RNProperties(BaseModel):
    mass: float = Field(..., description="Mass parameter M")
    charge: float = Field(..., description="Electric charge |Q|")
    q_over_m: float = Field(..., description="Dimensionless |Q|/M ∈ [0, 1]")
    outer_horizon: float = Field(..., description="r_+ = M + sqrt(M² - Q²)")
    inner_horizon: float = Field(..., description="r_- = M - sqrt(M² - Q²)")
    photon_sphere: float = Field(..., description="r_γ = (3M + sqrt(9M² - 8Q²))/2")
    isco: float = Field(..., description="ISCO from dL²_circ/dr = 0 (numerical)")
    surface_gravity: float = Field(..., description="κ = (r_+ - r_-)/(2 r_+²)")
    hawking_temperature: float = Field(..., description="T_H = κ/(2π)")
    horizon_area: float = Field(..., description="A = 4π r_+²")
    bekenstein_hawking_entropy: float = Field(..., description="S = π r_+²")
    is_extremal: bool = Field(..., description="True iff |Q| = M")
    line_element_latex: str = Field(...)


@router.get("/reissner-nordstrom", response_model=RNProperties)
async def get_reissner_nordstrom(
    mass: float = Query(1.0, gt=0, description="Mass M (M > 0)"),
    charge: float = Query(0.0, ge=0, description="|Q| (0 ≤ |Q| ≤ M)"),
) -> RNProperties:
    """Return physical observables of a Reissner-Nordström black hole.

    Closed-form invariants (horizons, photon sphere, surface gravity,
    Hawking T, BH entropy) come from the canonical Wald §6.4 formulae.
    The ISCO is computed numerically from dL²_circ/dr = 0; reduces to
    6M at Q = 0 to ≤ 1e-9.
    """
    try:
        bh = ReissnerNordstrom(mass=mass, charge=charge)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RNProperties(
        mass=mass,
        charge=charge,
        q_over_m=charge / mass,
        outer_horizon=bh.outer_horizon(),
        inner_horizon=bh.inner_horizon(),
        photon_sphere=bh.photon_sphere(),
        isco=bh.isco(),
        surface_gravity=bh.surface_gravity(),
        hawking_temperature=bh.hawking_temperature(),
        horizon_area=bh.horizon_area(),
        bekenstein_hawking_entropy=bh.bekenstein_hawking_entropy(),
        is_extremal=bh.is_extremal,
        line_element_latex=bh.line_element_latex(),
    )
