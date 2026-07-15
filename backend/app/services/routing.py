"""
Route optimization service.

Fetches real walking routes from OSRM, scores them against
building shadow geometry, and returns ranked alternatives.
"""
import math
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.schemas import (
    RouteResponse,
    RoutePreference,
    Coordinate,
    RouteStep,
    RouteAlternative,
    SegmentScoreSchema,
    MultiRouteResponse,
)
from app.services.osrm_client import OSRMClient, OSRMRoute
from app.services.sun_score import SunScoreCalculator, SunScoreResult
from app.services.shadow import ShadowService
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ScoredRoute:
    """Internal dataclass for a route with its sun score."""
    index: int
    osrm_route: OSRMRoute
    sun_score: SunScoreResult
    label: str = ""


class RoutingService:
    """Service for route optimization based on sun/shade preferences."""

    def __init__(self):
        self._osrm_client = OSRMClient()
        self._shadow_service = ShadowService()
        self._sun_scorer = SunScoreCalculator()
        self._shadow_cache: dict[tuple[float, float], object] = {}

    async def get_routes_with_alternatives(
        self,
        origin: Coordinate,
        destination: Coordinate,
        preference: RoutePreference,
        departure_time: datetime,
        sun_altitude: float,
        sun_azimuth: float,
    ) -> list[ScoredRoute]:
        """
        Fetch real walking routes, score each for sun exposure,
        and return all alternatives with labels.

        Falls back to straight-line route if OSRM is unavailable.
        """
        # 1. Fetch OSRM walking routes
        osrm_routes = await self._osrm_client.get_walking_routes(
            origin_lat=origin.lat,
            origin_lon=origin.lon,
            dest_lat=destination.lat,
            dest_lon=destination.lon,
            num_alternatives=settings.osrm_alternatives,
        )

        # Fallback: if OSRM fails, create a straight-line route
        if not osrm_routes:
            logger.warning("OSRM returned no routes, falling back to straight-line")
            distance_m = self._haversine_distance(
                origin.lat, origin.lon, destination.lat, destination.lon
            )
            fallback_route = OSRMRoute(
                coordinates=[
                    [origin.lon, origin.lat],
                    [destination.lon, destination.lat],
                ],
                distance_m=distance_m,
                duration_s=(distance_m / 1000) / 5 * 3600,  # 5 km/h
            )
            osrm_routes = [fallback_route]

        # 2. Get shadow union (cached for same sun position)
        cache_key = (round(sun_altitude, 1), round(sun_azimuth, 1))
        if cache_key in self._shadow_cache:
            shadow_union = self._shadow_cache[cache_key]
        else:
            shadow_union = await self._shadow_service.get_shadow_union_metric(
                timestamp=departure_time,
                sun_altitude=sun_altitude,
                sun_azimuth=sun_azimuth,
            )
            self._shadow_cache[cache_key] = shadow_union
            logger.info(
                f"Computed shadow union for alt={sun_altitude:.1f} az={sun_azimuth:.1f} "
                f"(cached, shadow={'exists' if shadow_union else 'none'})"
            )

        # 3. Score each route
        scored_routes: list[ScoredRoute] = []
        for i, osrm_route in enumerate(osrm_routes):
            sun_score = self._sun_scorer.score_route(
                coordinates=osrm_route.coordinates,
                shadow_union_metric=shadow_union,
            )
            scored_routes.append(ScoredRoute(
                index=i,
                osrm_route=osrm_route,
                sun_score=sun_score,
            ))

        # 4. Label routes
        self._label_routes(scored_routes)

        return scored_routes

    def _label_routes(self, routes: list[ScoredRoute]) -> None:
        """
        Assign labels to routes:
        - 'fastest': shortest duration (OSRM index 0)
        - 'sunniest': highest sun exposure
        - 'shadiest': highest shade exposure
        """
        if not routes:
            return

        # Fastest is always the first OSRM result
        routes[0].label = "fastest"

        # Find sunniest (highest sun_exposure_pct)
        sunniest = max(routes, key=lambda r: r.sun_score.sun_exposure_pct)
        if sunniest.label == "":
            sunniest.label = "sunniest"
        elif sunniest.label == "fastest":
            # Fastest is also sunniest — find next sunniest if available
            sunniest.label = "sunniest"  # sunniest takes priority over fastest label
            # Re-assign fastest to 2nd route if available
            for r in routes:
                if r.label == "":
                    r.label = "fastest"
                    break

        # Find shadiest (highest shade_exposure_pct) among unlabeled
        unlabeled = [r for r in routes if r.label == ""]
        if unlabeled:
            shadiest = max(unlabeled, key=lambda r: r.sun_score.shade_exposure_pct)
            shadiest.label = "shadiest"

        # Label any remaining routes
        for r in routes:
            if r.label == "":
                r.label = "alternative"

    async def get_shortest_route(
        self,
        origin: Coordinate,
        destination: Coordinate,
        departure_time: datetime
    ) -> RouteResponse:
        """
        Get the shortest walking route (no sun/shade optimization).

        Used as fallback for nighttime or when shadows aren't relevant.
        """
        # Calculate straight-line distance
        distance_m = self._haversine_distance(
            origin.lat, origin.lon,
            destination.lat, destination.lon
        )

        # Estimate walking time (5 km/h average)
        duration_min = (distance_m / 1000) / 5 * 60

        # Create simple route GeoJSON
        route_geojson = {
            "type": "Feature",
            "properties": {
                "distance_m": distance_m,
                "duration_min": duration_min
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [origin.lon, origin.lat],
                    [destination.lon, destination.lat]
                ]
            }
        }

        return RouteResponse(
            origin=origin,
            destination=destination,
            preference=RoutePreference.BALANCED,
            departure_time=departure_time,
            total_distance_m=distance_m,
            total_duration_min=duration_min,
            sun_exposure_pct=50.0,
            shade_exposure_pct=50.0,
            route_geojson=route_geojson,
            steps=[
                RouteStep(
                    coordinates=[[origin.lon, origin.lat], [destination.lon, destination.lat]],
                    distance_m=distance_m,
                    sun_exposure_pct=50.0,
                    instruction="Walk to destination"
                )
            ]
        )

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance between two points in meters."""
        R = 6371000  # Earth radius in meters

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _calculate_bearing(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate bearing between two points in degrees."""
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_lambda = math.radians(lon2 - lon1)

        x = math.sin(delta_lambda) * math.cos(phi2)
        y = (math.cos(phi1) * math.sin(phi2) -
             math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda))

        bearing = math.atan2(x, y)
        return (math.degrees(bearing) + 360) % 360
