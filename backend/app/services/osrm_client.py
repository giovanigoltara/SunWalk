"""
OSRM (Open Source Routing Machine) client for real walking routes.

Fetches actual walking paths from the OSRM public demo server
instead of straight-line connections between coordinates.
"""
import logging
from dataclasses import dataclass, field

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class OSRMRoute:
    """A single walking route returned by OSRM."""
    coordinates: list[list[float]]  # [[lon, lat], ...]
    distance_m: float               # total distance in meters
    duration_s: float               # total duration in seconds

    @property
    def duration_min(self) -> float:
        return self.duration_s / 60.0


class OSRMClient:
    """
    Client for the OSRM routing API.

    Uses the public demo server for walking routes with alternatives.
    Falls back gracefully if the server is unavailable.
    """

    def __init__(self):
        self._base_url = settings.osrm_base_url
        self._timeout = settings.osrm_timeout_s
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-init the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def get_walking_routes(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        num_alternatives: int = 3
    ) -> list[OSRMRoute]:
        """
        Fetch walking routes from OSRM.

        Args:
            origin_lat: Origin latitude
            origin_lon: Origin longitude
            dest_lat: Destination latitude
            dest_lon: Destination longitude
            num_alternatives: Max number of alternative routes (default 3)

        Returns:
            List of OSRMRoute objects. Empty list on error (caller should fallback).
        """
        # OSRM URL format: /route/v1/foot/{lon},{lat};{lon},{lat}
        coords_str = f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        url = f"{self._base_url}/route/v1/foot/{coords_str}"

        params = {
            "alternatives": str(num_alternatives).lower() if num_alternatives > 1 else "false",
            "geometries": "geojson",
            "overview": "full",
            "steps": "true",
        }

        try:
            client = await self._get_client()
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get("code") != "Ok":
                logger.warning(f"OSRM returned non-Ok code: {data.get('code')}")
                return []

            routes = []
            for route_data in data.get("routes", []):
                geometry = route_data.get("geometry", {})
                coordinates = geometry.get("coordinates", [])

                if not coordinates:
                    continue

                routes.append(OSRMRoute(
                    coordinates=coordinates,
                    distance_m=route_data.get("distance", 0.0),
                    duration_s=route_data.get("duration", 0.0),
                ))

            logger.info(
                f"OSRM returned {len(routes)} walking route(s) "
                f"from ({origin_lat:.4f},{origin_lon:.4f}) "
                f"to ({dest_lat:.4f},{dest_lon:.4f})"
            )
            return routes

        except httpx.TimeoutException:
            logger.warning(f"OSRM request timed out after {self._timeout}s")
            return []
        except httpx.HTTPStatusError as e:
            logger.warning(f"OSRM HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"OSRM unexpected error: {e}")
            return []

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
