"""Holography REST endpoints — Page curves (eternal + evaporating).

Wraps the v0.9 / v1.0 / v1.1 ``spacetime_lab.holography.island`` and
``.evaporating`` modules so the frontend can show the famous Page
curves interactively.

Two endpoints:
    GET /api/holography/page_curve/eternal
        Eternal BTZ at fixed (r_+, L, ε): grows linearly, saturates
        at 2 S_BH.  Phase label per timestep.

    GET /api/holography/page_curve/evaporating
        Schwarzschild evaporation: bell-shaped, zero at endpoints,
        peak at the closed-form Page time t_P ≈ 0.6464 t_evap.
"""

from __future__ import annotations

import numpy as np
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from spacetime_lab.holography.evaporating import (
    page_curve_evaporating,
    page_time_evaporating,
    schwarzschild_evaporation_time,
)
from spacetime_lab.holography.island import (
    island_saddle_entropy,
    page_curve,
    page_time,
)

router = APIRouter(prefix="/holography")


class PageCurveSamples(BaseModel):
    """Time-sampled Page curve and metadata."""

    kind: str = Field(..., description="'eternal' or 'evaporating'")
    t_values: list[float] = Field(..., description="Time samples")
    s_values: list[float] = Field(..., description="Page curve entropy at each t")
    phase_labels: list[str] = Field(
        ..., description="Per-sample winning saddle: 'trivial'/'hawking' or 'island'"
    )
    page_time: float = Field(..., description="Time at which the saddles cross")
    saturation_entropy: float = Field(
        ..., description="Asymptotic entropy: 2 S_BH for eternal, peak for evaporating"
    )
    parameters: dict = Field(..., description="Echo of input params for trace")


@router.get("/page_curve/eternal", response_model=PageCurveSamples)
async def page_curve_eternal(
    horizon_radius: float = Query(1.0, gt=0, description="BTZ outer horizon r_+"),
    ads_radius: float = Query(1.0, gt=0, description="AdS radius L"),
    epsilon: float = Query(0.01, gt=0, description="UV cutoff ε"),
    G_N: float = Query(1.0, gt=0, description="Newton's constant"),
    t_max: float = Query(20.0, gt=0, description="Max time to sample"),
    n_samples: int = Query(150, ge=10, le=2000),
) -> PageCurveSamples:
    """Eternal BTZ Page curve: linear-growth Hartman-Maldacena saddle
    vs. constant island saddle.  Returns per-sample (t, S, phase)."""
    try:
        t_p = page_time(
            horizon_radius=horizon_radius,
            ads_radius=ads_radius,
            epsilon=epsilon,
            G_N=G_N,
        )
        ts = np.linspace(0.0, t_max, n_samples).tolist()
        s_values: list[float] = []
        phase_labels: list[str] = []
        for t in ts:
            s, phase = page_curve(
                t=t,
                horizon_radius=horizon_radius,
                ads_radius=ads_radius,
                epsilon=epsilon,
                G_N=G_N,
            )
            s_values.append(float(s))
            phase_labels.append(phase)
        s_island = float(
            island_saddle_entropy(horizon_radius=horizon_radius, G_N=G_N)
        )
        return PageCurveSamples(
            kind="eternal",
            t_values=ts,
            s_values=s_values,
            phase_labels=phase_labels,
            page_time=float(t_p),
            saturation_entropy=s_island,
            parameters={
                "horizon_radius": horizon_radius,
                "ads_radius": ads_radius,
                "epsilon": epsilon,
                "G_N": G_N,
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/page_curve/evaporating", response_model=PageCurveSamples)
async def page_curve_evap(
    initial_mass: float = Query(1.0, gt=0, description="Initial Schwarzschild mass M_0"),
    G_N: float = Query(1.0, gt=0, description="Newton's constant"),
    n_samples: int = Query(150, ge=10, le=2000),
) -> PageCurveSamples:
    """Bell-shaped evaporating-BH Page curve.  Samples uniformly from
    t=0 to t=t_evap.  Hawking saddle dominates early, island saddle
    late, crossing at the closed-form Page time t_P ≈ 0.6464 t_evap."""
    try:
        t_evap = float(schwarzschild_evaporation_time(initial_mass, G_N=G_N))
        t_p = float(page_time_evaporating(initial_mass, G_N=G_N, t_evap=t_evap))
        # Sample tightly near both endpoints to avoid missing the bell shape
        ts = np.linspace(1e-9, t_evap * (1 - 1e-9), n_samples).tolist()
        s_values: list[float] = []
        phase_labels: list[str] = []
        for t in ts:
            s, phase = page_curve_evaporating(
                t=t, initial_mass=initial_mass, G_N=G_N, t_evap=t_evap
            )
            s_values.append(float(s))
            phase_labels.append(phase)
        peak = float(max(s_values)) if s_values else 0.0
        return PageCurveSamples(
            kind="evaporating",
            t_values=ts,
            s_values=s_values,
            phase_labels=phase_labels,
            page_time=t_p,
            saturation_entropy=peak,
            parameters={
                "initial_mass": initial_mass,
                "G_N": G_N,
                "t_evap": t_evap,
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
