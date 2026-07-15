"""
SunWalk API - Real-Time Urban Sun & Shade Mapping
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from app.core.config import get_settings
from app.models.schemas import HealthResponse
from app.api import shadows, routes, sun

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    SunWalk API provides real-time sun and shade data for urban navigation.

    ## Features
    - Shadow calculations based on building geometry and solar position
    - Sun-optimized or shade-optimized walking routes
    - Real-time and pre-computed shadow overlays

    ## Coverage
    Currently supports Berlin-Mitte. More areas coming soon.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    shadows.router,
    prefix=f"{settings.api_prefix}/shadows",
    tags=["Shadows"]
)
app.include_router(
    routes.router,
    prefix=f"{settings.api_prefix}/routes",
    tags=["Routes"]
)
app.include_router(
    sun.router,
    prefix=f"{settings.api_prefix}/sun",
    tags=["Sun Position"]
)


@app.get("/", tags=["Root"])
async def root():
    """API root - redirects to docs."""
    return {
        "message": "Welcome to SunWalk API",
        "docs": "/docs",
        "version": settings.app_version
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc)
    )
