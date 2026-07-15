"""
Pydantic schemas for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class RoutePreference(str, Enum):
    """Route optimization preference."""
    SUN = "sun"
    SHADE = "shade"
    BALANCED = "balanced"


class Coordinate(BaseModel):
    """Geographic coordinate (WGS84)."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")


class BoundingBox(BaseModel):
    """Bounding box for area of interest."""
    min_lon: float = Field(..., ge=-180, le=180)
    min_lat: float = Field(..., ge=-90, le=90)
    max_lon: float = Field(..., ge=-180, le=180)
    max_lat: float = Field(..., ge=-90, le=90)


class ShadowRequest(BaseModel):
    """Request for shadow data at a specific time."""
    timestamp: Optional[datetime] = Field(
        None,
        description="UTC timestamp for shadow calculation. Defaults to current time."
    )
    bbox: Optional[BoundingBox] = Field(
        None,
        description="Bounding box. Defaults to Berlin Mitte."
    )
    format: str = Field(
        "geojson",
        description="Output format: 'geojson', 'png', or 'tiles'"
    )


class ShadowResponse(BaseModel):
    """Shadow calculation response."""
    timestamp: datetime
    sun_altitude: float = Field(..., description="Sun altitude in degrees")
    sun_azimuth: float = Field(..., description="Sun azimuth in degrees")
    is_daytime: bool
    shadow_geojson: Optional[dict] = None
    overlay_url: Optional[str] = None


class RouteRequest(BaseModel):
    """Request for route optimization."""
    origin: Coordinate
    destination: Coordinate
    preference: RoutePreference = RoutePreference.SUN
    departure_time: Optional[datetime] = Field(
        None,
        description="Departure time for shadow calculation. Defaults to now."
    )


class RouteStep(BaseModel):
    """A single step in the route."""
    coordinates: list[list[float]]  # [[lon, lat], ...]
    distance_m: float
    sun_exposure_pct: float = Field(..., ge=0, le=100)
    instruction: Optional[str] = None


class RouteResponse(BaseModel):
    """Optimized route response."""
    origin: Coordinate
    destination: Coordinate
    preference: RoutePreference
    departure_time: datetime
    total_distance_m: float
    total_duration_min: float
    sun_exposure_pct: float
    shade_exposure_pct: float
    route_geojson: dict
    steps: list[RouteStep]


class SunPositionResponse(BaseModel):
    """Current sun position."""
    timestamp: datetime
    latitude: float
    longitude: float
    altitude_deg: float = Field(..., description="Sun altitude above horizon")
    azimuth_deg: float = Field(..., description="Sun azimuth from north")
    is_daytime: bool
    sunrise: datetime
    sunset: datetime


class SegmentScoreSchema(BaseModel):
    """Sun exposure score for a single route segment."""
    coordinates: list[list[float]]  # [[lon, lat], [lon, lat]]
    distance_m: float
    sun_exposure_pct: float = Field(..., ge=0, le=100)


class RouteAlternative(BaseModel):
    """A single route alternative with sun scoring."""
    label: str = Field(..., description="Route label: 'fastest', 'sunniest', 'shadiest'")
    total_distance_m: float
    total_duration_min: float
    sun_exposure_pct: float = Field(..., ge=0, le=100)
    shade_exposure_pct: float = Field(..., ge=0, le=100)
    route_geojson: dict  # GeoJSON Feature with LineString geometry
    segment_scores: list[SegmentScoreSchema] = Field(
        default_factory=list,
        description="Per-segment sun exposure for map coloring"
    )


class MultiRouteResponse(BaseModel):
    """Response with multiple route alternatives ranked by sun exposure."""
    origin: Coordinate
    destination: Coordinate
    departure_time: datetime
    sun_altitude: float = Field(..., description="Sun altitude in degrees at departure time")
    sun_azimuth: float = Field(..., description="Sun azimuth in degrees at departure time")
    is_daytime: bool
    routes: list[RouteAlternative]
    recommended_index: int = Field(
        0, description="Index of recommended route based on user preference"
    )


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str
    timestamp: datetime
