"""de Sitter REST endpoint (v3.2 partial)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from spacetime_lab.metrics import DeSitter

router = APIRouter(prefix="/metrics")


class DSProperties(BaseModel):
    radius: float = Field(..., description="de Sitter radius L = 1/H = sqrt(3/Λ)")
    cosmological_horizon: float = Field(..., description="r_c = L (closed form)")
    cosmological_constant: float = Field(..., description="Λ = 3/L²")
    hubble_parameter: float = Field(..., description="H = 1/L")
    hawking_temperature: float = Field(..., description="T_GH = 1/(2π L)")
    horizon_area: float = Field(..., description="A = 4π L²")
    bekenstein_hawking_entropy: float = Field(..., description="S = π L²")
    ricci_scalar: float = Field(..., description="R = 12/L² = 4Λ")
    line_element_latex: str


@router.get("/de-sitter", response_model=DSProperties)
async def get_de_sitter(
    radius: float = Query(1.0, gt=0, description="de Sitter radius L > 0"),
) -> DSProperties:
    """Return de Sitter (static-patch) observables.

    All quantities closed form; references: Wald §5.2; Gibbons-Hawking 1977.
    """
    try:
        ds = DeSitter(radius=radius)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return DSProperties(
        radius=radius,
        cosmological_horizon=ds.cosmological_horizon(),
        cosmological_constant=ds.cosmological_constant(),
        hubble_parameter=ds.hubble_parameter(),
        hawking_temperature=ds.hawking_temperature(),
        horizon_area=ds.horizon_area(),
        bekenstein_hawking_entropy=ds.bekenstein_hawking_entropy(),
        ricci_scalar=ds.expected_ricci_scalar(),
        line_element_latex=ds.line_element_latex(),
    )
