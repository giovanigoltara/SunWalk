"""
Shadow calculation service.

Handles building shadow projection and rasterization.
Loads building footprints with heights from OSM (local cache or Overpass API).
"""
import math
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
import numpy as np
import geopandas as gpd
from shapely import affinity
from shapely.ops import unary_union
from shapely.geometry import shape, mapping, Polygon

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ShadowService:
    """Service for shadow calculations and rasterization."""

    def __init__(self):
        self.crs_metric = settings.metric_crs
        self.crs_wgs = settings.default_crs
        self._buildings_gdf = None
        self._aoi_gdf = None

    def _load_buildings(self) -> gpd.GeoDataFrame:
        """
        Load and cache building data.

        Tries local GeoPackage first, falls back to Overpass API
        to fetch building footprints with heights from OpenStreetMap.
        """
        if self._buildings_gdf is not None:
            return self._buildings_gdf

        # Try to load from local data
        data_path = Path(__file__).parent.parent.parent.parent / "src" / "buildings_mitte.gpkg"

        if data_path.exists():
            gdf = gpd.read_file(data_path, layer="buildings")

            # Ensure height_m column exists
            if "height_m" not in gdf.columns:
                gdf["height_m"] = self._estimate_heights(gdf)

            # Keep only polygons and project to metric CRS
            gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
            gdf = gdf.to_crs(self.crs_metric)

            # Simplify for performance
            gdf["geometry"] = gdf.geometry.simplify(0.2, preserve_topology=True)

            self._buildings_gdf = gdf
            logger.info(f"Loaded {len(gdf)} buildings from local GeoPackage")
            return gdf

        # Fallback: fetch from Overpass API
        logger.info("No local GeoPackage found, fetching buildings from Overpass API")
        gdf = self._fetch_buildings_from_overpass()
        if gdf is not None and len(gdf) > 0:
            self._buildings_gdf = gdf
            return gdf

        # Last resort: empty GeoDataFrame
        logger.warning("No building data available")
        return gpd.GeoDataFrame(geometry=[], crs=self.crs_metric)

    def _fetch_buildings_from_overpass(self) -> Optional[gpd.GeoDataFrame]:
        """
        Fetch building footprints with height data from the Overpass API.

        Queries OpenStreetMap for buildings within the Berlin Mitte AOI,
        including height and building:levels attributes for shadow calculation.
        """
        bbox = settings.default_aoi_bbox  # [min_lon, min_lat, max_lon, max_lat]
        # Overpass bbox format: south, west, north, east
        overpass_bbox = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}"

        query = f"""
        [out:json][timeout:120];
        (
          way["building"]({overpass_bbox});
          relation["building"]({overpass_bbox});
        );
        out body;
        >;
        out skel qt;
        """

        try:
            response = httpx.post(
                "https://overpass-api.de/api/interpreter",
                data={"data": query},
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"Overpass API request failed: {e}")
            return None

        # Parse Overpass JSON into nodes and ways
        nodes = {}
        ways = []
        relations_meta = {}

        for element in data.get("elements", []):
            if element["type"] == "node":
                nodes[element["id"]] = (element["lon"], element["lat"])
            elif element["type"] == "way":
                ways.append(element)
            elif element["type"] == "relation":
                relations_meta[element["id"]] = element.get("tags", {})

        # Build GeoDataFrame from ways
        features = []
        for way in ways:
            node_ids = way.get("nodes", [])
            coords = [nodes[nid] for nid in node_ids if nid in nodes]

            if len(coords) < 4:
                continue

            # Close the polygon if needed
            if coords[0] != coords[-1]:
                coords.append(coords[0])

            try:
                geom = Polygon(coords)
                if geom.is_valid and not geom.is_empty:
                    tags = way.get("tags", {})
                    features.append({
                        "geometry": geom,
                        "height": tags.get("height"),
                        "building:levels": tags.get("building:levels"),
                        "building": tags.get("building", "yes"),
                    })
            except Exception:
                continue

        if not features:
            logger.warning("No valid building features parsed from Overpass response")
            return None

        gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")

        # Estimate heights from OSM attributes
        gdf["height_m"] = self._estimate_heights(gdf)

        # Log height data coverage
        has_explicit = gdf["height"].notna().sum() if "height" in gdf.columns else 0
        has_levels = gdf["building:levels"].notna().sum() if "building:levels" in gdf.columns else 0
        logger.info(
            f"Fetched {len(gdf)} buildings from Overpass API "
            f"({has_explicit} with explicit height, "
            f"{has_levels} with building:levels)"
        )

        # Keep only polygons and project to metric CRS
        gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
        gdf = gdf.to_crs(self.crs_metric)

        # Simplify for performance
        gdf["geometry"] = gdf.geometry.simplify(0.2, preserve_topology=True)

        return gdf

    def _estimate_heights(self, gdf: gpd.GeoDataFrame) -> np.ndarray:
        """Estimate building heights from OSM attributes."""
        heights = np.full(len(gdf), np.nan)

        # Try explicit height attribute
        if "height" in gdf.columns:
            for i, h in enumerate(gdf["height"]):
                if h is not None:
                    try:
                        heights[i] = float(str(h).strip().lower().replace("m", ""))
                    except (ValueError, TypeError):
                        pass

        # Fall back to building:levels * 3m
        if "building:levels" in gdf.columns:
            for i, lvl in enumerate(gdf["building:levels"]):
                if np.isnan(heights[i]) and lvl is not None:
                    try:
                        heights[i] = float(lvl) * 3.0
                    except (ValueError, TypeError):
                        pass

        # Default height for buildings without data
        heights = np.where(np.isnan(heights), 12.0, heights)  # Default 4 floors

        return heights

    def _translate_along_azimuth(
        self,
        geom,
        length_m: float,
        azimuth_deg: float
    ):
        """
        Translate geometry along shadow direction.

        Pysolar azimuth is degrees clockwise from North.
        Shadow points away from sun: azimuth + 180.
        """
        theta = math.radians(azimuth_deg + 180.0)
        dx = length_m * math.sin(theta)  # Easting
        dy = length_m * math.cos(theta)  # Northing
        return affinity.translate(geom, xoff=dx, yoff=dy)

    def _shadow_length(
        self,
        height_m: float,
        altitude_deg: float,
        cap_m: float = 200.0
    ) -> float:
        """Calculate shadow length from height and sun altitude."""
        if height_m is None or np.isnan(height_m) or altitude_deg <= 0:
            return 0.0

        alt_rad = math.radians(altitude_deg)
        if alt_rad <= 0:
            return 0.0

        length = height_m / math.tan(alt_rad)
        return float(min(max(length, 0.0), cap_m))

    def _building_shadow(
        self,
        geom,
        height_m: float,
        altitude_deg: float,
        azimuth_deg: float
    ):
        """
        Compute shadow polygon for a single building.

        Returns convex hull of building footprint and translated footprint.
        """
        length = self._shadow_length(height_m, altitude_deg)
        if length <= 0:
            return None

        shifted = self._translate_along_azimuth(geom, length, azimuth_deg)
        return unary_union([geom, shifted]).convex_hull

    async def get_shadows(
        self,
        bbox,
        timestamp: datetime,
        sun_altitude: float,
        sun_azimuth: float
    ) -> dict:
        """
        Calculate shadow polygons for an area.

        Returns GeoJSON FeatureCollection.
        """
        buildings = self._load_buildings()

        if len(buildings) == 0 or sun_altitude <= 0:
            return {
                "type": "FeatureCollection",
                "features": [],
                "properties": {
                    "timestamp": timestamp.isoformat(),
                    "sun_altitude": sun_altitude,
                    "building_count": 0,
                    "area_sqm": 0
                }
            }

        # Compute shadows for all buildings
        shadows = []
        heights = buildings.get("height_m", np.full(len(buildings), 12.0)).to_numpy()

        for geom, h in zip(buildings.geometry.to_numpy(), heights):
            try:
                shadow = self._building_shadow(
                    geom,
                    float(h) if h is not None else 12.0,
                    sun_altitude,
                    sun_azimuth
                )
                if shadow is not None and not shadow.is_empty:
                    shadows.append(shadow)
            except Exception:
                continue

        if not shadows:
            return {
                "type": "FeatureCollection",
                "features": [],
                "properties": {
                    "timestamp": timestamp.isoformat(),
                    "sun_altitude": sun_altitude,
                    "building_count": len(buildings),
                    "area_sqm": 0
                }
            }

        # Union all shadows
        shadow_union = unary_union(shadows)

        # Convert to WGS84 for GeoJSON output
        shadow_gdf = gpd.GeoDataFrame(
            geometry=[shadow_union],
            crs=self.crs_metric
        ).to_crs(self.crs_wgs)

        # Calculate area in metric CRS
        area_sqm = shadow_union.area if shadow_union else 0

        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "type": "shadow",
                        "timestamp": timestamp.isoformat(),
                        "sun_altitude": sun_altitude,
                        "sun_azimuth": sun_azimuth
                    },
                    "geometry": mapping(shadow_gdf.geometry.iloc[0])
                }
            ],
            "properties": {
                "timestamp": timestamp.isoformat(),
                "sun_altitude": sun_altitude,
                "building_count": len(buildings),
                "area_sqm": area_sqm
            }
        }

    async def get_shadow_union_metric(
        self,
        timestamp: datetime,
        sun_altitude: float,
        sun_azimuth: float
    ):
        """
        Get shadow union geometry in metric CRS (EPSG:25833).

        Returns the unary_union of all building shadows directly in the metric
        coordinate system, avoiding the WGS84 round-trip. This is optimized for
        route intersection calculations.

        Returns:
            Shapely geometry (Polygon/MultiPolygon) in EPSG:25833, or None if
            no shadows can be computed.
        """
        buildings = self._load_buildings()

        if len(buildings) == 0 or sun_altitude <= 0:
            return None

        # Compute shadows for all buildings
        shadows = []
        heights = buildings.get("height_m", np.full(len(buildings), 12.0)).to_numpy()

        for geom, h in zip(buildings.geometry.to_numpy(), heights):
            try:
                shadow = self._building_shadow(
                    geom,
                    float(h) if h is not None else 12.0,
                    sun_altitude,
                    sun_azimuth
                )
                if shadow is not None and not shadow.is_empty:
                    shadows.append(shadow)
            except Exception:
                continue

        if not shadows:
            return None

        # Return union in metric CRS (no WGS84 conversion)
        return unary_union(shadows)

    async def get_overlay(
        self,
        timestamp: datetime,
        resolution: float
    ) -> Optional[dict]:
        """
        Get pre-computed overlay info for a timestamp.

        Returns overlay metadata or None if not found.
        """
        # Check for pre-computed overlay
        data_path = Path(__file__).parent.parent.parent.parent / "src" / "time_masks"

        # Format timestamp for filename matching
        ts_str = timestamp.strftime("%Y-%m-%dT%H%M%S")

        for tif_file in data_path.glob(f"*{ts_str}*.tif"):
            return {
                "timestamp": timestamp.isoformat(),
                "file": str(tif_file),
                "resolution_m": resolution,
                "format": "geotiff"
            }

        return None
