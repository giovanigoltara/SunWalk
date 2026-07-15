"""
Sun position API endpoints.
"""
from fastapi import APIRouter, Query
from datetime import datetime, timezone
from typing import Optional

from app.models.schemas import SunPositionResponse, Coordinate
from app.services.solar import SolarService

router = APIRouter()
solar_service = SolarService()


@router.get("/position", response_model=SunPositionResponse)
async def get_sun_position(
    lat: float = Query(52.52, description="Latitude (default: Berlin)"),
    lon: float = Query(13.405, description="Longitude (default: Berlin)"),
    timestamp: Optional[datetime] = Query(None, description="UTC timestamp (default: now)")
):
    """
    Get the current sun position for a location.

    Returns altitude, azimuth, and sunrise/sunset times.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    return solar_service.get_sun_position(lat, lon, timestamp)


@router.get("/is-daytime")
async def is_daytime(
    lat: float = Query(52.52, description="Latitude"),
    lon: float = Query(13.405, description="Longitude"),
    timestamp: Optional[datetime] = Query(None, description="UTC timestamp")
):
    """Check if it's currently daytime at the given location."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    position = solar_service.get_sun_position(lat, lon, timestamp)
    return {
        "is_daytime": position.is_daytime,
        "sun_altitude": position.altitude_deg,
        "timestamp": timestamp
    }
