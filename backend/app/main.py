"""Spacetime Lab — FastAPI backend.

Provides REST API for metric computation, geodesic integration, and
physical observables of black hole spacetimes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import ads, btz, diagrams, geodesics, holography, kerr, kerr_newman, metrics, reissner_nordstrom

app = FastAPI(
    title="Spacetime Lab API",
    description="Interactive platform for exploring black hole physics.",
    version="0.2.5",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS — allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(metrics.router, prefix="/api", tags=["metrics"])
app.include_router(kerr.router, prefix="/api", tags=["kerr"])
app.include_router(ads.router, prefix="/api", tags=["ads"])
app.include_router(btz.router, prefix="/api", tags=["btz"])
app.include_router(holography.router, prefix="/api", tags=["holography"])
app.include_router(diagrams.router, prefix="/api", tags=["diagrams"])
app.include_router(geodesics.router, prefix="/api", tags=["geodesics"])
app.include_router(reissner_nordstrom.router, prefix="/api", tags=["reissner-nordstrom"])
app.include_router(kerr_newman.router, prefix="/api", tags=["kerr-newman"])


@app.get("/api/health")
async def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Spacetime Lab API",
        "version": app.version,
    }


@app.get("/api/version")
async def version() -> dict:
    """Return current API version."""
    return {"version": app.version}
