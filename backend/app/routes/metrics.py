"""Metric computation endpoints.

Provides REST access to the `spacetime_lab.metrics` module.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from spacetime_lab.metrics import Schwarzschild

router = APIRouter(prefix="/metrics")


class SchwarzschildProperties(BaseModel):
    """Physical properties of a Schwarzschild black hole."""

    mass: float = Field(..., description="Mass parameter M in geometric units")
    event_horizon: float = Field(..., description="Schwarzschild radius r_s = 2M")
    isco: float = Field(..., description="Innermost Stable Circular Orbit at r = 6M")
    photon_sphere: float = Field(..., description="Photon sphere at r = 3M")
    surface_gravity: float = Field(..., description="Surface gravity kappa = 1/(4M)")
    hawking_temperature: float = Field(..., description="Hawking temperature T_H = 1/(8 pi M)")
    bekenstein_hawking_entropy: float = Field(
        ..., description="Bekenstein-Hawking entropy S = 4 pi M^2"
    )
    line_element_latex: str = Field(..., description="Line element in LaTeX format")


class MetricTensorResponse(BaseModel):
    """Metric tensor evaluated at a point."""

    metric_name: str
    coordinates: dict[str, float]
    tensor: list[list[float]]


@router.get("/schwarzschild", response_model=SchwarzschildProperties)
async def get_schwarzschild(
    mass: float = Query(1.0, gt=0, description="Mass parameter (must be positive)"),
) -> SchwarzschildProperties:
    """Get physical properties of a Schwarzschild black hole.

    Returns the event horizon, ISCO, photon sphere, Hawking temperature,
    and other invariants for a Schwarzschild black hole of given mass.
    """
    try:
        bh = Schwarzschild(mass=mass)
        return SchwarzschildProperties(
            mass=mass,
            event_horizon=float(bh.event_horizon()),
            isco=float(bh.isco()),
            photon_sphere=float(bh.photon_sphere()),
            surface_gravity=float(bh.surface_gravity()),
            hawking_temperature=float(bh.hawking_temperature()),
            bekenstein_hawking_entropy=float(bh.bekenstein_hawking_entropy()),
            line_element_latex=bh.line_element_latex(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/schwarzschild/tensor", response_model=MetricTensorResponse)
async def schwarzschild_tensor(
    mass: float = Query(1.0, gt=0),
    r: float = Query(..., gt=0, description="Radial coordinate"),
    theta: float = Query(1.5708, description="Polar angle (theta)"),
    phi: float = Query(0.0, description="Azimuthal angle (phi)"),
    t: float = Query(0.0, description="Time coordinate"),
) -> MetricTensorResponse:
    """Evaluate the Schwarzschild metric tensor at a point."""
    try:
        bh = Schwarzschild(mass=mass)
        g = bh.metric_at(t=t, r=r, theta=theta, phi=phi)
        return MetricTensorResponse(
            metric_name="Schwarzschild",
            coordinates={"t": t, "r": r, "theta": theta, "phi": phi},
            tensor=g.tolist(),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/available")
async def list_available_metrics() -> dict:
    """List metrics currently available in the platform."""
    return {
        "metrics": [
            {
                "name": "Schwarzschild",
                "description": "Static, spherically symmetric vacuum BH",
                "parameters": ["mass"],
                "phase": 1,
                "available": True,
            },
            {
                "name": "Kerr",
                "description": "Rotating vacuum BH",
                "parameters": ["mass", "spin"],
                "phase": 3,
                "available": False,
            },
            {
                "name": "Reissner-Nordström",
                "description": "Charged static BH",
                "parameters": ["mass", "charge"],
                "phase": 4,
                "available": False,
            },
            {
                "name": "BTZ",
                "description": "3D AdS black hole",
                "parameters": ["mass", "spin", "cosmological_constant"],
                "phase": 7,
                "available": False,
            },
            {
                "name": "AdS (Anti-de Sitter)",
                "description": "Negative cosmological constant background",
                "parameters": ["radius"],
                "phase": 7,
                "available": False,
            },
        ]
    }
