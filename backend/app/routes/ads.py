"""AdS metric REST endpoints — second new physics surface in v2.5.

Wraps ``spacetime_lab.metrics.AdS`` (Phase 7, v0.7.0) — the constant-
negative-curvature background for AdS/CFT.  Returns curvature scalar,
cosmological constant, Brown-Henneaux central charge (for d=3), and
the LaTeX line element.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from spacetime_lab.metrics import AdS

router = APIRouter(prefix="/metrics")


class AdSProperties(BaseModel):
    """Physical constants of an AdS_d background at given dimension and radius."""

    dimension: int = Field(..., description="Spacetime dimension n (≥ 2)")
    radius: float = Field(..., description="AdS radius L")
    cosmological_constant: float = Field(
        ..., description="Λ = -(n-1)(n-2) / (2 L²)  (Einstein vacuum w/ Λ)"
    )
    ricci_scalar: float = Field(..., description="R = -n(n-1)/L²")
    ricci_proportionality: float = Field(
        ..., description="Coefficient λ in R_μν = λ g_μν, equal to -(n-1)/L²"
    )
    brown_henneaux_central_charge: float | None = Field(
        None,
        description="c = 3L/(2 G_N) for d=3 only; null otherwise",
    )
    line_element_latex: str = Field(..., description="Line element in Poincaré coords")


@router.get("/ads", response_model=AdSProperties)
async def get_ads(
    dimension: int = Query(3, ge=2, le=10, description="Spacetime dim"),
    radius: float = Query(1.0, gt=0, description="AdS radius L"),
    G_N: float = Query(1.0, gt=0, description="Newton's constant (for Brown-Henneaux)"),
) -> AdSProperties:
    """Return physical observables of the AdS_n background.

    For ``dimension == 3`` (AdS_3) we additionally compute the
    Brown-Henneaux boundary CFT central charge:

    .. math:: c = \\frac{3 L}{2 G_N}.

    For other dimensions ``brown_henneaux_central_charge`` is null.
    """
    try:
        ads = AdS(dimension=dimension, radius=radius)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    central_charge = None
    if dimension == 3:
        central_charge = 3.0 * radius / (2.0 * G_N)

    return AdSProperties(
        dimension=dimension,
        radius=radius,
        cosmological_constant=float(ads.cosmological_constant()),
        ricci_scalar=float(ads.expected_ricci_scalar()),
        ricci_proportionality=float(ads.expected_ricci_proportionality()),
        brown_henneaux_central_charge=central_charge,
        line_element_latex=ads.line_element_latex(),
    )
