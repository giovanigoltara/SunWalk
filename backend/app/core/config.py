"""
SunWalk Configuration
"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "SunWalk API"
    app_version: str = "0.1.0"
    debug: bool = False

    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Database
    database_url: Optional[str] = None
    redis_url: Optional[str] = "redis://localhost:6379"

    # Geospatial defaults
    default_crs: str = "EPSG:4326"
    metric_crs: str = "EPSG:25833"  # UTM 33N for Berlin
    shadow_resolution_m: float = 2.0

    # Berlin Mitte AOI (default)
    default_aoi_bbox: list[float] = [13.387, 52.510, 13.416, 52.533]

    # OSRM routing
    osrm_base_url: str = "https://router.project-osrm.org"
    osrm_timeout_s: float = 10.0
    osrm_alternatives: int = 3

    # Pre-computation settings
    precompute_start_hour: int = 6
    precompute_end_hour: int = 21
    precompute_interval_minutes: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
