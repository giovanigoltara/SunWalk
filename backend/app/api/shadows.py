"""
Shadow calculation API endpoints.
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from typing import Optional

from app.models.schemas import ShadowRequest, ShadowResponse, BoundingBox
from app.services.shadow import ShadowService
from app.services.solar import SolarService
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()
shadow_service = ShadowService()
solar_service = SolarService()


@router.get("/current")
async def get_current_shadows(
    min_lon: float = Query(settings.default_aoi_bbox[0]),
    min_lat: float = Query(settings.default_aoi_bbox[1]),
    max_lon: float = Query(settings.default_aoi_bbox[2]),
    max_lat: float = Query(settings.default_aoi_bbox[3]),
    format: str = Query("geojson", description="Output format: geojson or summary")
):
    """
    Get current shadow polygons for the specified area.

    Default area is Berlin Mitte.
    """
    timestamp = datetime.now(timezone.utc)
    bbox = BoundingBox(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)

    # Get sun position
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    sun_pos = solar_service.get_sun_position(center_lat, center_lon, timestamp)

    if not sun_pos.is_daytime:
        return JSONResponse(
            content={
                "timestamp": timestamp.isoformat(),
                "is_daytime": False,
                "message": "Sun is below horizon - no shadows to calculate",
                "sun_altitude": sun_pos.altitude_deg
            }
        )

    # Calculate shadows
    shadow_geojson = await shadow_service.get_shadows(
        bbox=bbox,
        timestamp=timestamp,
        sun_altitude=sun_pos.altitude_deg,
        sun_azimuth=sun_pos.azimuth_deg
    )

    if format == "summary":
        return {
            "timestamp": timestamp.isoformat(),
            "sun_altitude": sun_pos.altitude_deg,
            "sun_azimuth": sun_pos.azimuth_deg,
            "is_daytime": True,
            "shadow_area_sqm": shadow_geojson.get("properties", {}).get("area_sqm", 0),
            "building_count": shadow_geojson.get("properties", {}).get("building_count", 0)
        }

    return ShadowResponse(
        timestamp=timestamp,
        sun_altitude=sun_pos.altitude_deg,
        sun_azimuth=sun_pos.azimuth_deg,
        is_daytime=True,
        shadow_geojson=shadow_geojson
    )


@router.get("/at-time")
async def get_shadows_at_time(
    timestamp: datetime = Query(..., description="UTC timestamp"),
    min_lon: float = Query(settings.default_aoi_bbox[0]),
    min_lat: float = Query(settings.default_aoi_bbox[1]),
    max_lon: float = Query(settings.default_aoi_bbox[2]),
    max_lat: float = Query(settings.default_aoi_bbox[3])
):
    """
    Get shadow polygons for a specific time.

    Useful for planning walks at future times.
    """
    bbox = BoundingBox(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)

    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    sun_pos = solar_service.get_sun_position(center_lat, center_lon, timestamp)

    if not sun_pos.is_daytime:
        return JSONResponse(
            content={
                "timestamp": timestamp.isoformat(),
                "is_daytime": False,
                "message": "Sun is below horizon at requested time"
            }
        )

    shadow_geojson = await shadow_service.get_shadows(
        bbox=bbox,
        timestamp=timestamp,
        sun_altitude=sun_pos.altitude_deg,
        sun_azimuth=sun_pos.azimuth_deg
    )

    return ShadowResponse(
        timestamp=timestamp,
        sun_altitude=sun_pos.altitude_deg,
        sun_azimuth=sun_pos.azimuth_deg,
        is_daytime=True,
        shadow_geojson=shadow_geojson
    )


@router.get("/overlay/{timestamp_str}")
async def get_shadow_overlay(
    timestamp_str: str,
    resolution: float = Query(2.0, description="Resolution in meters")
):
    """
    Get a pre-computed shadow overlay PNG for a timestamp.

    Timestamp format: YYYY-MM-DDTHHMMSS (e.g., 2025-02-04T120000)
    """
    try:
        # Parse timestamp
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H%M%S")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid timestamp format. Use YYYY-MM-DDTHHMMSS"
        )

    overlay_info = await shadow_service.get_overlay(timestamp, resolution)

    if overlay_info is None:
        raise HTTPException(
            status_code=404,
            detail="Overlay not found for this timestamp"
        )

    return overlay_info
