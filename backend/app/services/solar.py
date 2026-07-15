"""
Solar position calculation service.

Ported from SunWalk notebook using Pysolar.
"""
import math
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pysolar.solar import get_altitude, get_azimuth

from app.models.schemas import SunPositionResponse


class SolarService:
    """Service for solar position calculations."""

    def __init__(self, default_timezone: str = "Europe/Berlin"):
        self.default_tz = ZoneInfo(default_timezone)

    def get_sun_position(
        self,
        lat: float,
        lon: float,
        timestamp: datetime
    ) -> SunPositionResponse:
        """
        Calculate sun position for a given location and time.

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            timestamp: UTC timestamp

        Returns:
            SunPositionResponse with altitude, azimuth, and day/night info
        """
        # Ensure timestamp is timezone-aware UTC
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        # Pysolar expects timezone-aware datetime
        altitude = float(get_altitude(lat, lon, timestamp))
        azimuth = float(get_azimuth(lat, lon, timestamp))

        # Calculate sunrise/sunset for this day
        sunrise, sunset = self._calculate_sunrise_sunset(lat, lon, timestamp)

        return SunPositionResponse(
            timestamp=timestamp,
            latitude=lat,
            longitude=lon,
            altitude_deg=altitude,
            azimuth_deg=azimuth,
            is_daytime=altitude > 0,
            sunrise=sunrise,
            sunset=sunset
        )

    def _calculate_sunrise_sunset(
        self,
        lat: float,
        lon: float,
        timestamp: datetime
    ) -> tuple[datetime, datetime]:
        """
        Estimate sunrise and sunset times for the given day.

        Uses a simple binary search approach.
        """
        # Get the date in local timezone
        local_dt = timestamp.astimezone(self.default_tz)
        date = local_dt.date()

        # Search for sunrise (morning)
        sunrise = self._find_horizon_crossing(
            lat, lon, date, hour_start=4, hour_end=12, rising=True
        )

        # Search for sunset (evening)
        sunset = self._find_horizon_crossing(
            lat, lon, date, hour_start=12, hour_end=22, rising=False
        )

        return sunrise, sunset

    def _find_horizon_crossing(
        self,
        lat: float,
        lon: float,
        date,
        hour_start: int,
        hour_end: int,
        rising: bool
    ) -> datetime:
        """Find when sun crosses horizon using binary search."""
        tz = self.default_tz

        # Create datetime range
        start = datetime(date.year, date.month, date.day, hour_start, tzinfo=tz)
        end = datetime(date.year, date.month, date.day, hour_end, tzinfo=tz)

        # Binary search for horizon crossing
        for _ in range(20):  # ~1 minute precision
            mid = start + (end - start) / 2
            mid_utc = mid.astimezone(timezone.utc)
            alt = get_altitude(lat, lon, mid_utc)

            if rising:
                if alt < 0:
                    start = mid
                else:
                    end = mid
            else:
                if alt > 0:
                    start = mid
                else:
                    end = mid

        return start.astimezone(timezone.utc)

    def shadow_length(
        self,
        height_m: float,
        altitude_deg: float,
        cap_m: float = 200.0
    ) -> float:
        """
        Calculate shadow length from building height and sun altitude.

        Args:
            height_m: Building height in meters
            altitude_deg: Sun altitude above horizon in degrees
            cap_m: Maximum shadow length cap

        Returns:
            Shadow length in meters
        """
        if height_m is None or math.isnan(height_m) or altitude_deg <= 0:
            return 0.0

        alt_rad = math.radians(altitude_deg)
        if alt_rad <= 0:
            return 0.0

        length = height_m / math.tan(alt_rad)
        return float(min(max(length, 0.0), cap_m))
