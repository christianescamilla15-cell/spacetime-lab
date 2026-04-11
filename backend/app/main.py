"""Spacetime Lab — FastAPI backend.

Provides REST API for metric computation, geodesic integration, and
physical observables of black hole spacetimes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import metrics

app = FastAPI(
    title="Spacetime Lab API",
    description="Interactive platform for exploring black hole physics.",
    version="0.0.1",
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


@app.get("/api/health")
async def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Spacetime Lab API",
        "version": "0.0.1",
    }


@app.get("/api/version")
async def version() -> dict:
    """Return current API version."""
    return {"version": "0.0.1"}
