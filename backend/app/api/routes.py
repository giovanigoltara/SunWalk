"""
Route optimization API endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.models.schemas import (
    RouteRequest,
    RouteResponse,
    RoutePreference,
    Coordinate,
    RouteAlternative,
    SegmentScoreSchema,
    MultiRouteResponse,
)
from app.services.routing import RoutingService
from app.services.solar import SolarService

logger = logging.getLogger(__name__)

router = APIRouter()
routing_service = RoutingService()
solar_service = SolarService()

# Fixed simulation time: November 15th, 12:00 PM CET (UTC+1)
FIXED_DEPARTURE = datetime(2025, 11, 15, 12, 0, 0, tzinfo=ZoneInfo("Europe/Berlin"))


@router.post("/optimize", response_model=MultiRouteResponse)
async def optimize_route(request: RouteRequest):
    """
    Calculate walking routes with real OSRM paths and sun exposure scoring.

    Returns up to 3 alternative routes labeled fastest/sunniest/shadiest.
    Time is currently fixed to November 15, 12:00 PM CET for iterative testing.

    - **sun**: Recommends the route with maximum sun exposure
    - **shade**: Recommends the route with maximum shade
    - **balanced**: Recommends the fastest route
    """
    # Use fixed departure time (ignoring request.departure_time)
    departure = FIXED_DEPARTURE.astimezone(timezone.utc)

    # Get sun position at fixed time
    center_lat = (request.origin.lat + request.destination.lat) / 2
    center_lon = (request.origin.lon + request.destination.lon) / 2
    sun_pos = solar_service.get_sun_position(center_lat, center_lon, departure)

    if not sun_pos.is_daytime:
        # At night, return single route with no sun data
        fallback = await routing_service.get_shortest_route(
            origin=request.origin,
            destination=request.destination,
            departure_time=departure,
        )
        return MultiRouteResponse(
            origin=request.origin,
            destination=request.destination,
            departure_time=departure,
            sun_altitude=sun_pos.altitude_deg,
            sun_azimuth=sun_pos.azimuth_deg,
            is_daytime=False,
            routes=[
                RouteAlternative(
                    label="fastest",
                    total_distance_m=fallback.total_distance_m,
                    total_duration_min=fallback.total_duration_min,
                    sun_exposure_pct=50.0,
                    shade_exposure_pct=50.0,
                    route_geojson=fallback.route_geojson,
                    segment_scores=[],
                )
            ],
            recommended_index=0,
        )

    # Get scored route alternatives
    scored_routes = await routing_service.get_routes_with_alternatives(
        origin=request.origin,
        destination=request.destination,
        preference=request.preference,
        departure_time=departure,
        sun_altitude=sun_pos.altitude_deg,
        sun_azimuth=sun_pos.azimuth_deg,
    )

    # Convert to response model
    alternatives = []
    for sr in scored_routes:
        geojson_feature = {
            "type": "Feature",
            "properties": {
                "label": sr.label,
                "distance_m": sr.osrm_route.distance_m,
                "duration_min": sr.osrm_route.duration_min,
                "sun_exposure_pct": sr.sun_score.sun_exposure_pct,
                "shade_exposure_pct": sr.sun_score.shade_exposure_pct,
            },
            "geometry": {
                "type": "LineString",
                "coordinates": sr.osrm_route.coordinates,
            },
        }

        segment_schemas = [
            SegmentScoreSchema(
                coordinates=[seg.start_coord, seg.end_coord],
                distance_m=seg.distance_m,
                sun_exposure_pct=seg.sun_exposure_pct,
            )
            for seg in sr.sun_score.segment_scores
        ]

        alternatives.append(RouteAlternative(
            label=sr.label,
            total_distance_m=sr.osrm_route.distance_m,
            total_duration_min=sr.osrm_route.duration_min,
            sun_exposure_pct=sr.sun_score.sun_exposure_pct,
            shade_exposure_pct=sr.sun_score.shade_exposure_pct,
            route_geojson=geojson_feature,
            segment_scores=segment_schemas,
        ))

    # Determine recommended route based on preference
    recommended_idx = 0
    if request.preference == RoutePreference.SUN:
        recommended_idx = max(
            range(len(alternatives)),
            key=lambda i: alternatives[i].sun_exposure_pct,
        )
    elif request.preference == RoutePreference.SHADE:
        recommended_idx = max(
            range(len(alternatives)),
            key=lambda i: alternatives[i].shade_exposure_pct,
        )
    # BALANCED: keep recommended_idx = 0 (fastest)

    logger.info(
        f"Route optimization: {len(alternatives)} alternatives, "
        f"recommended={alternatives[recommended_idx].label} "
        f"(sun={alternatives[recommended_idx].sun_exposure_pct:.0f}%)"
    )

    return MultiRouteResponse(
        origin=request.origin,
        destination=request.destination,
        departure_time=departure,
        sun_altitude=sun_pos.altitude_deg,
        sun_azimuth=sun_pos.azimuth_deg,
        is_daytime=sun_pos.is_daytime,
        routes=alternatives,
        recommended_index=recommended_idx,
    )


@router.get("/sun-route")
async def get_sun_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float
):
    """
    Quick endpoint for sun-optimized route.

    Use POST /optimize for more options.
    """
    request = RouteRequest(
        origin=Coordinate(lat=origin_lat, lon=origin_lon),
        destination=Coordinate(lat=dest_lat, lon=dest_lon),
        preference=RoutePreference.SUN
    )
    return await optimize_route(request)


@router.get("/shade-route")
async def get_shade_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float
):
    """
    Quick endpoint for shade-optimized route.

    Use POST /optimize for more options.
    """
    request = RouteRequest(
        origin=Coordinate(lat=origin_lat, lon=origin_lon),
        destination=Coordinate(lat=dest_lat, lon=dest_lon),
        preference=RoutePreference.SHADE
    )
    return await optimize_route(request)
