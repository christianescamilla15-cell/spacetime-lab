"""Kerr metric REST endpoints — first new physics surface in v2.5.

Wraps the already-shipped ``spacetime_lab.metrics.Kerr`` (Phase 3, v0.3
→ v1.2) so the React frontend can drive sliders for ``M`` and ``a``
and read out horizons, ergosphere, ISCO branches, photon sphere
branches, and BH thermodynamics.

All formulae verified against Wald 1984, MTW 1973, and Bardeen-Press-
Teukolsky 1972 in the Python test suite (see
``tests/test_phase_3.py``).  This module is a pure thin wrapper — no
new physics derivations live here.
"""

from __future__ import annotations

import math

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from spacetime_lab.metrics import Kerr

router = APIRouter(prefix="/metrics")


class KerrProperties(BaseModel):
    """Physical observables of a Kerr black hole at given (M, a)."""

    mass: float = Field(..., description="Mass parameter M (geometric units G=c=1)")
    spin: float = Field(..., description="Spin parameter a = J/M (same dim as M)")
    a_over_m: float = Field(..., description="Dimensionless spin a/M ∈ [0, 1]")

    # Horizons
    outer_horizon: float = Field(..., description="r_+ = M + sqrt(M² - a²)")
    inner_horizon: float = Field(..., description="r_- = M - sqrt(M² - a²)")

    # Ergosphere
    ergo_equator: float = Field(..., description="r_E(θ=π/2) = 2M (independent of a)")
    ergo_pole: float = Field(..., description="r_E(θ=0) = r_+")

    # Circular orbits
    isco_prograde: float = Field(..., description="ISCO co-rotating with the BH")
    isco_retrograde: float = Field(..., description="ISCO counter-rotating")
    photon_sphere_prograde: float = Field(..., description="Unstable photon orbit, prograde")
    photon_sphere_retrograde: float = Field(..., description="Unstable photon orbit, retrograde")

    # Thermodynamics
    angular_velocity_horizon: float = Field(..., description="Ω_H = a / (r_+² + a²)")
    horizon_area: float = Field(..., description="A = 4π (r_+² + a²)")
    surface_gravity: float = Field(..., description="κ = (r_+ - r_-) / 2(r_+² + a²)")
    hawking_temperature: float = Field(..., description="T_H = κ / (2π)")
    bekenstein_hawking_entropy: float = Field(..., description="S = A/4 = π(r_+² + a²)")

    # Provenance
    line_element_latex: str = Field(..., description="Boyer-Lindquist line element")
    is_extremal: bool = Field(..., description="True iff a == M (within tolerance)")


@router.get("/kerr", response_model=KerrProperties)
async def get_kerr(
    mass: float = Query(1.0, gt=0, description="Mass parameter M (must be > 0)"),
    spin: float = Query(0.0, ge=0, description="Spin a = J/M (0 ≤ a ≤ M)"),
) -> KerrProperties:
    """Return physical observables of a Kerr black hole.

    Constraints:
        - ``mass > 0``
        - ``0 ≤ spin ≤ mass`` (cosmic censorship)

    The two ISCO and two photon-sphere branches are returned because
    Kerr orbits are chiral: a co-rotating geodesic can come closer to
    the BH than a counter-rotating one.  At ``a → M`` (extremal),
    prograde ISCO → ``M`` and retrograde → ``9M``.
    """
    try:
        bh = Kerr(mass=mass, spin=spin)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        return KerrProperties(
            mass=mass,
            spin=spin,
            a_over_m=spin / mass,
            outer_horizon=float(bh.outer_horizon()),
            inner_horizon=float(bh.inner_horizon()),
            ergo_equator=float(bh.ergosphere(theta=math.pi / 2)),
            ergo_pole=float(bh.ergosphere(theta=0.0)),
            isco_prograde=float(bh.isco(prograde=True)),
            isco_retrograde=float(bh.isco(prograde=False)),
            photon_sphere_prograde=float(bh.photon_sphere_equatorial(prograde=True)),
            photon_sphere_retrograde=float(bh.photon_sphere_equatorial(prograde=False)),
            angular_velocity_horizon=float(bh.angular_velocity_horizon()),
            horizon_area=float(bh.horizon_area()),
            surface_gravity=float(bh.surface_gravity()),
            hawking_temperature=float(bh.hawking_temperature()),
            bekenstein_hawking_entropy=float(bh.bekenstein_hawking_entropy()),
            line_element_latex=bh.line_element_latex(),
            is_extremal=abs(spin - mass) < 1e-12,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
