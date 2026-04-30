"""Kerr-Newman REST endpoint — second metric of v3.2."""

from __future__ import annotations

import math

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from spacetime_lab.metrics import KerrNewman

router = APIRouter(prefix="/metrics")


class KNProperties(BaseModel):
    mass: float
    spin: float
    charge: float
    a_over_m: float
    q_over_m: float
    a_squared_plus_q_squared: float
    outer_horizon: float
    inner_horizon: float
    ergo_equator: float = Field(..., description="r_E(θ=π/2) = M + sqrt(M²-Q²)")
    ergo_pole: float = Field(..., description="r_E(θ=0) = r_+")
    angular_velocity_horizon: float
    surface_gravity: float
    hawking_temperature: float
    horizon_area: float
    bekenstein_hawking_entropy: float
    is_extremal: bool
    line_element_latex: str


@router.get("/kerr-newman", response_model=KNProperties)
async def get_kerr_newman(
    mass: float = Query(1.0, gt=0),
    spin: float = Query(0.0, ge=0),
    charge: float = Query(0.0, ge=0),
) -> KNProperties:
    """Kerr-Newman observables.  Cosmic censorship: a² + Q² ≤ M²."""
    try:
        bh = KerrNewman(mass=mass, spin=spin, charge=charge)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return KNProperties(
        mass=mass,
        spin=spin,
        charge=charge,
        a_over_m=spin / mass,
        q_over_m=charge / mass,
        a_squared_plus_q_squared=spin ** 2 + charge ** 2,
        outer_horizon=bh.outer_horizon(),
        inner_horizon=bh.inner_horizon(),
        ergo_equator=bh.ergosphere(math.pi / 2),
        ergo_pole=bh.ergosphere(0.0),
        angular_velocity_horizon=bh.angular_velocity_horizon(),
        surface_gravity=bh.surface_gravity(),
        hawking_temperature=bh.hawking_temperature(),
        horizon_area=bh.horizon_area(),
        bekenstein_hawking_entropy=bh.bekenstein_hawking_entropy(),
        is_extremal=bh.is_extremal,
        line_element_latex=bh.line_element_latex(),
    )
