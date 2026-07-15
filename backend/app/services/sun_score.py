"""
Sun Score calculation engine.

Scores walking routes for sun/shade exposure by intersecting
the route geometry with building shadow polygons.
"""
import logging
from dataclasses import dataclass, field

from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.prepared import prep
from shapely import ops

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class SegmentScore:
    """Sun exposure score for a single route segment."""
    start_coord: list[float]     # [lon, lat] in WGS84
    end_coord: list[float]       # [lon, lat] in WGS84
    distance_m: float
    sun_exposure_pct: float      # 0-100


@dataclass
class SunScoreResult:
    """Overall sun exposure score for a route."""
    sun_exposure_pct: float      # 0-100
    shade_exposure_pct: float    # 0-100
    total_distance_m: float
    shaded_distance_m: float
    sunny_distance_m: float
    segment_scores: list[SegmentScore] = field(default_factory=list)


class SunScoreCalculator:
    """
    Calculates sun exposure for walking routes by intersecting
    route geometry with shadow polygons.

    The shadow union is expected in EPSG:25833 (metric CRS).
    Route coordinates are in WGS84 and will be projected.
    """

    def __init__(self):
        # Transformers for CRS conversion
        self._to_metric = Transformer.from_crs(
            settings.default_crs, settings.metric_crs, always_xy=True
        )
        self._to_wgs = Transformer.from_crs(
            settings.metric_crs, settings.default_crs, always_xy=True
        )

    def score_route(
        self,
        coordinates: list[list[float]],
        shadow_union_metric
    ) -> SunScoreResult:
        """
        Score a route for sun exposure against shadow geometry.

        Args:
            coordinates: Route coordinates as [[lon, lat], ...] in WGS84
            shadow_union_metric: Shadow union geometry in EPSG:25833.
                                 Can be None (100% sun if no shadows).

        Returns:
            SunScoreResult with overall and per-segment scores.
        """
        if not coordinates or len(coordinates) < 2:
            return SunScoreResult(
                sun_exposure_pct=100.0,
                shade_exposure_pct=0.0,
                total_distance_m=0.0,
                shaded_distance_m=0.0,
                sunny_distance_m=0.0,
            )

        # Project route coordinates to metric CRS
        metric_coords = [
            self._to_metric.transform(coord[0], coord[1])
            for coord in coordinates
        ]

        # Create route LineString in metric CRS
        route_line = LineString(metric_coords)
        total_distance = route_line.length

        if total_distance == 0:
            return SunScoreResult(
                sun_exposure_pct=100.0,
                shade_exposure_pct=0.0,
                total_distance_m=0.0,
                shaded_distance_m=0.0,
                sunny_distance_m=0.0,
            )

        # If no shadow geometry, route is 100% in sun
        if shadow_union_metric is None or shadow_union_metric.is_empty:
            segment_scores = self._score_segments_no_shadow(
                coordinates, metric_coords
            )
            return SunScoreResult(
                sun_exposure_pct=100.0,
                shade_exposure_pct=0.0,
                total_distance_m=total_distance,
                shaded_distance_m=0.0,
                sunny_distance_m=total_distance,
                segment_scores=segment_scores,
            )

        # Prepare shadow geometry for fast intersection checks
        prepared_shadow = prep(shadow_union_metric)

        # Calculate overall intersection
        try:
            shaded_part = route_line.intersection(shadow_union_metric)
            shaded_distance = shaded_part.length if not shaded_part.is_empty else 0.0
        except Exception as e:
            logger.warning(f"Shadow intersection failed: {e}")
            shaded_distance = 0.0

        sunny_distance = max(0.0, total_distance - shaded_distance)
        sun_pct = (sunny_distance / total_distance) * 100.0
        shade_pct = 100.0 - sun_pct

        # Per-segment scoring
        segment_scores = self._score_segments(
            coordinates, metric_coords, shadow_union_metric
        )

        return SunScoreResult(
            sun_exposure_pct=round(sun_pct, 1),
            shade_exposure_pct=round(shade_pct, 1),
            total_distance_m=round(total_distance, 1),
            shaded_distance_m=round(shaded_distance, 1),
            sunny_distance_m=round(sunny_distance, 1),
            segment_scores=segment_scores,
        )

    def _score_segments(
        self,
        wgs_coords: list[list[float]],
        metric_coords: list[tuple[float, float]],
        shadow_union_metric
    ) -> list[SegmentScore]:
        """Score individual route segments against shadow geometry."""
        scores = []

        for i in range(len(wgs_coords) - 1):
            seg_start_m = metric_coords[i]
            seg_end_m = metric_coords[i + 1]

            seg_line = LineString([seg_start_m, seg_end_m])
            seg_dist = seg_line.length

            if seg_dist == 0:
                continue

            try:
                shaded_part = seg_line.intersection(shadow_union_metric)
                shaded_len = shaded_part.length if not shaded_part.is_empty else 0.0
            except Exception:
                shaded_len = 0.0

            sun_pct = ((seg_dist - shaded_len) / seg_dist) * 100.0

            scores.append(SegmentScore(
                start_coord=wgs_coords[i],
                end_coord=wgs_coords[i + 1],
                distance_m=round(seg_dist, 1),
                sun_exposure_pct=round(max(0.0, min(100.0, sun_pct)), 1),
            ))

        return scores

    def _score_segments_no_shadow(
        self,
        wgs_coords: list[list[float]],
        metric_coords: list[tuple[float, float]]
    ) -> list[SegmentScore]:
        """Create segment scores when there are no shadows (all sun)."""
        scores = []

        for i in range(len(wgs_coords) - 1):
            seg_line = LineString([metric_coords[i], metric_coords[i + 1]])
            seg_dist = seg_line.length

            if seg_dist == 0:
                continue

            scores.append(SegmentScore(
                start_coord=wgs_coords[i],
                end_coord=wgs_coords[i + 1],
                distance_m=round(seg_dist, 1),
                sun_exposure_pct=100.0,
            ))

        return scores
