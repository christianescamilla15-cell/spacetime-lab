"""Geodesic integration REST endpoint — first surface of v2.6.

Wraps spacetime_lab.geodesics.GeodesicIntegrator (Phase 3, v0.3) with
a POST endpoint so the frontend Three.js scene can request a Kerr or
Schwarzschild geodesic given an initial state and integration params.

Returns the trajectory (decimated to keep payload small) plus the four
constants of motion at every kept sample, plus drift residuals so the
frontend can show conservation diagnostics.
"""

from __future__ import annotations

import time
from typing import Literal

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from spacetime_lab.geodesics import GeodesicIntegrator, GeodesicState
from spacetime_lab.metrics import Kerr, Schwarzschild

router = APIRouter(prefix="/geodesics")

# Hard caps to bound payload + cost.  Frontend slider should respect
# these; if the request exceeds them we 400 rather than silently chop.
MAX_N_STEPS = 20_000
MAX_RETURNED_POINTS = 4_000


class GeodesicIntegrateRequest(BaseModel):
    """Body of POST /api/geodesics/integrate."""

    metric: Literal["kerr", "schwarzschild"] = Field(
        ..., description="Background metric"
    )
    params: dict = Field(
        ..., description="Metric parameters: {mass, spin?} for Kerr, {mass} for Schwarzschild"
    )
    initial_position: list[float] = Field(
        ...,
        description="x = (t, r, theta, phi) — Boyer-Lindquist for Kerr",
        min_length=4,
        max_length=4,
    )
    initial_momentum: list[float] = Field(
        ...,
        description="p = (p_t, p_r, p_theta, p_phi) — COVARIANT components",
        min_length=4,
        max_length=4,
    )
    step_size: float = Field(
        0.5, gt=0, le=10, description="Affine-parameter step h"
    )
    n_steps: int = Field(
        2000, ge=10, le=MAX_N_STEPS, description="Number of integration steps"
    )
    decimation: int = Field(
        1, ge=1, le=200,
        description="Return every Nth sample to bound payload size",
    )


class GeodesicSample(BaseModel):
    """Single point of the returned trajectory."""

    lambda_: float = Field(..., alias="lambda", description="Affine parameter λ")
    x: list[float] = Field(..., description="(t, r, theta, phi)")
    p: list[float] = Field(..., description="(p_t, p_r, p_theta, p_phi)")
    E: float = Field(..., description="Energy E = -p_t (conserved for Kerr)")
    L_z: float = Field(..., description="z-component of angular momentum (conserved)")
    mu_squared: float = Field(..., description="Mass-shell -2H (conserved)")
    Q_carter: float | None = Field(
        None, description="Carter constant (Kerr only); null for Schwarzschild"
    )

    model_config = {"populate_by_name": True}


class GeodesicResponse(BaseModel):
    """Result of a geodesic integration request."""

    trajectory: list[GeodesicSample] = Field(...)
    drift_residuals: dict = Field(
        ...,
        description="Max absolute drift of each conserved quantity over the trajectory",
    )
    metadata: dict = Field(...)


def _build_metric(metric: str, params: dict):
    if metric == "kerr":
        return Kerr(
            mass=float(params.get("mass", 1.0)),
            spin=float(params.get("spin", 0.0)),
        )
    if metric == "schwarzschild":
        return Schwarzschild(mass=float(params.get("mass", 1.0)))
    raise HTTPException(400, f"unknown metric '{metric}'")


def _carter_constant_safe(bh, state) -> float | None:
    """Return Carter Q for Kerr; None for any metric without it."""
    if not hasattr(bh, "carter_constant_from_state"):
        return None
    try:
        return float(bh.carter_constant_from_state(state))
    except Exception:
        return None


@router.post("/integrate", response_model=GeodesicResponse)
async def integrate(req: GeodesicIntegrateRequest) -> GeodesicResponse:
    """Integrate a single geodesic and return its trajectory + conserved quantities.

    Performance notes:
      - The integrator is symplectic implicit-midpoint, 2nd-order.  Cost
        scales as O(n_steps × scipy.optimize.fsolve iterations).  For
        typical Kerr geodesics, ~2 ms/step on a modern laptop.
      - Decimation is applied AFTER integration: the integrator runs
        n_steps full steps and we keep every Nth state.  This bounds
        payload without touching numerical accuracy.
    """
    bh = _build_metric(req.metric, req.params)

    try:
        state0 = GeodesicState(
            x=np.array(req.initial_position, dtype=float),
            p=np.array(req.initial_momentum, dtype=float),
        )
    except Exception as exc:
        raise HTTPException(400, f"initial state error: {exc}") from exc

    integrator = GeodesicIntegrator(bh)

    n_returned = (req.n_steps // req.decimation) + 1
    if n_returned > MAX_RETURNED_POINTS:
        raise HTTPException(
            400,
            f"would return {n_returned} points (cap {MAX_RETURNED_POINTS}); "
            f"increase decimation or reduce n_steps",
        )

    t_start = time.monotonic()
    try:
        states = integrator.integrate(state0, h=req.step_size, n_steps=req.n_steps)
    except Exception as exc:
        raise HTTPException(500, f"integration failed: {exc}") from exc
    integration_time = time.monotonic() - t_start

    # Decimate
    kept = states[::req.decimation]
    if kept[-1] is not states[-1]:
        kept.append(states[-1])  # always include final state for visualisation

    # Build samples + collect conserved quantities for drift analysis
    samples: list[GeodesicSample] = []
    Es: list[float] = []
    Lzs: list[float] = []
    mus: list[float] = []
    Qs: list[float] = []
    for i, s in enumerate(kept):
        E = float(-s.p[0])
        Lz = float(s.p[3])
        mu_sq = float(-2.0 * integrator.hamiltonian(s))
        Q = _carter_constant_safe(bh, s)
        Es.append(E)
        Lzs.append(Lz)
        mus.append(mu_sq)
        if Q is not None:
            Qs.append(Q)
        samples.append(GeodesicSample(
            **{"lambda": i * req.decimation * req.step_size},
            x=s.x.tolist(),
            p=s.p.tolist(),
            E=E,
            L_z=Lz,
            mu_squared=mu_sq,
            Q_carter=Q,
        ))

    def _drift(values: list[float]) -> float:
        if not values:
            return 0.0
        return float(max(values) - min(values))

    drift = {
        "E_drift": _drift(Es),
        "L_z_drift": _drift(Lzs),
        "mu_squared_drift": _drift(mus),
        "Q_carter_drift": _drift(Qs) if Qs else None,
    }

    return GeodesicResponse(
        trajectory=samples,
        drift_residuals=drift,
        metadata={
            "metric": req.metric,
            "params": req.params,
            "step_size": req.step_size,
            "n_steps": req.n_steps,
            "decimation": req.decimation,
            "n_returned_points": len(samples),
            "integration_seconds": round(integration_time, 4),
        },
    )


@router.get("/example")
async def example_request() -> dict:
    """Convenience: a known-good Kerr example payload that the frontend
    can use as initial form values."""
    return {
        "metric": "kerr",
        "params": {"mass": 1.0, "spin": 0.5},
        "initial_position": [0.0, 10.0, 1.5708, 0.0],
        "initial_momentum": [-0.94, 0.0, 1.5, 3.0],
        "step_size": 0.5,
        "n_steps": 1500,
        "decimation": 5,
    }
