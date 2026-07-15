export interface Coordinate {
  lat: number
  lon: number
}

export type RoutePreference = 'sun' | 'shade' | 'balanced'

export interface SunPosition {
  timestamp: string
  latitude: number
  longitude: number
  altitude_deg: number
  azimuth_deg: number
  is_daytime: boolean
  sunrise: string
  sunset: string
}

export interface ShadowResponse {
  timestamp: string
  sun_altitude: number
  sun_azimuth: number
  is_daytime: boolean
  shadow_geojson?: GeoJSON.FeatureCollection
}

export interface RouteStep {
  coordinates: number[][]
  distance_m: number
  sun_exposure_pct: number
  instruction?: string
}

// Legacy single route (kept for backward compat)
export interface Route {
  origin: Coordinate
  destination: Coordinate
  preference: RoutePreference
  departure_time: string
  total_distance_m: number
  total_duration_min: number
  sun_exposure_pct: number
  shade_exposure_pct: number
  route_geojson: GeoJSON.Feature
  steps: RouteStep[]
}

// New multi-route types

export interface SegmentScore {
  coordinates: number[][]   // [[lon,lat], [lon,lat]]
  distance_m: number
  sun_exposure_pct: number
}

export interface RouteAlternative {
  label: string  // 'fastest' | 'sunniest' | 'shadiest' | 'alternative'
  total_distance_m: number
  total_duration_min: number
  sun_exposure_pct: number
  shade_exposure_pct: number
  route_geojson: GeoJSON.Feature
  segment_scores: SegmentScore[]
}

export interface MultiRouteResponse {
  origin: Coordinate
  destination: Coordinate
  departure_time: string
  sun_altitude: number
  sun_azimuth: number
  is_daytime: boolean
  routes: RouteAlternative[]
  recommended_index: number
}
