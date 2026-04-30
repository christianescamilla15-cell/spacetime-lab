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


class EffectivePotentialResponse(BaseModel):
    """Effective potential V_eff(r) computed over a range of radii."""

    mass: float
    angular_momentum: float
    particle_type: str
    r_values: list[float]
    v_values: list[float]
    event_horizon: float
    photon_sphere: float
    isco: float
    critical_points: list[dict[str, float]] = Field(
        default_factory=list,
        description="Extrema of V_eff (min = stable orbit, max = unstable)"
    )


@router.get("/schwarzschild/effective_potential", response_model=EffectivePotentialResponse)
async def effective_potential(
    mass: float = Query(1.0, gt=0, description="Mass parameter M"),
    angular_momentum: float = Query(4.0, ge=0, description="Angular momentum L"),
    particle_type: str = Query("massive", description="'massive' or 'photon'"),
    r_min: float = Query(2.5, gt=0, description="Inner radius"),
    r_max: float = Query(30.0, description="Outer radius"),
    n_points: int = Query(500, ge=10, le=2000),
) -> EffectivePotentialResponse:
    """Compute V_eff(r) over a range of radii for the Schwarzschild black hole.

    The effective potential determines the radial motion of test particles
    in equatorial geodesics. Extrema correspond to circular orbits:
    - Maximum = unstable orbit (photon sphere for photons, outer turning for massive)
    - Minimum = stable orbit (for massive particles with L > 2√3 M)
    """
    import numpy as np

    if particle_type not in ("massive", "photon"):
        raise HTTPException(400, "particle_type must be 'massive' or 'photon'")

    try:
        bh = Schwarzschild(mass=mass)
        r_values = np.linspace(max(r_min, 2 * mass + 0.01), r_max, n_points).tolist()
        v_values = [
            float(bh.effective_potential(r, angular_momentum, particle_type))
            for r in r_values
        ]

        # Find extrema (simple local min/max detection)
        critical_points = []
        for i in range(1, len(v_values) - 1):
            if v_values[i - 1] < v_values[i] > v_values[i + 1]:
                critical_points.append({"r": r_values[i], "v": v_values[i], "type": "max"})
            elif v_values[i - 1] > v_values[i] < v_values[i + 1]:
                critical_points.append({"r": r_values[i], "v": v_values[i], "type": "min"})

        return EffectivePotentialResponse(
            mass=mass,
            angular_momentum=angular_momentum,
            particle_type=particle_type,
            r_values=r_values,
            v_values=v_values,
            event_horizon=float(bh.event_horizon()),
            photon_sphere=float(bh.photon_sphere()),
            isco=float(bh.isco()),
            critical_points=critical_points,
        )
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@router.get("/available")
async def list_available_metrics() -> dict:
    """List metrics currently available in the platform.

    "shipped_in_python" reflects what the spacetime_lab Python package
    actually exposes; "rest_endpoint" tracks whether the FastAPI layer
    has wrapped it yet.  v2.5 closes the Kerr gap; v2.6 will close BTZ
    and AdS, v2.6+ Reissner-Nordström.
    """
    return {
        "metrics": [
            {
                "name": "Schwarzschild",
                "description": "Static, spherically symmetric vacuum BH",
                "parameters": ["mass"],
                "phase": 1,
                "shipped_in_python": "v0.1.0",
                "rest_endpoint": "/api/metrics/schwarzschild",
                "available": True,
            },
            {
                "name": "Kerr",
                "description": "Rotating vacuum BH (Boyer-Lindquist)",
                "parameters": ["mass", "spin"],
                "phase": 3,
                "shipped_in_python": "v0.3.0",
                "rest_endpoint": "/api/metrics/kerr",
                "available": True,
            },
            {
                "name": "AdS (Anti-de Sitter)",
                "description": "Negative cosmological constant background (Poincaré)",
                "parameters": ["dim", "L_AdS"],
                "phase": 7,
                "shipped_in_python": "v0.7.0",
                "rest_endpoint": "/api/metrics/ads",
                "available": True,
            },
            {
                "name": "BTZ",
                "description": "3D AdS black hole (static; rotating in v1.3 Python only)",
                "parameters": ["horizon_radius", "ads_radius"],
                "phase": 8,
                "shipped_in_python": "v0.8.0 (static), v1.3.0 (rotating)",
                "rest_endpoint": "/api/metrics/btz",
                "available": True,
            },
            {
                "name": "Reissner-Nordström",
                "description": "Static, spherically symmetric, electrically charged BH",
                "parameters": ["mass", "charge"],
                "phase": 4,
                "shipped_in_python": "v3.1.0",
                "rest_endpoint": "/api/metrics/reissner-nordstrom",
                "available": True,
            },
        ]
    }
