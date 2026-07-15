import { useRef, useEffect, useImperativeHandle, forwardRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { Coordinate, MultiRouteResponse } from '../types'

interface MapProps {
  center: Coordinate
  sunAltitude: number
  sunAzimuth: number
  routeData: MultiRouteResponse | null
  selectedRouteIndex: number
  onRouteSelect: (index: number) => void
  origin: Coordinate | null
  destination: Coordinate | null
  onMapClick: (coord: Coordinate) => void
  onLocationFound: (coord: Coordinate) => void
  isSelecting: boolean
}

export interface MapHandle {
  flyTo: (coord: Coordinate) => void
  triggerGeolocate: () => void
}

// SunWalk Color Palette
const COLORS = {
  solarGold: '#FFD700',
  shadowNavy: '#1A1A2E',
  coolCyan: '#00F5FF',
  buildingLight: '#2D2D44',
  buildingDark: '#1E1E2E',
  groundDark: '#0D0D15',
}

// Route color by label
function getRouteColor(label: string): string {
  switch (label) {
    case 'sunniest': return COLORS.solarGold
    case 'shadiest': return COLORS.coolCyan
    case 'fastest': return '#FFFFFF'
    default: return '#888888'
  }
}

const emptyFC: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: [] }

const Map = forwardRef<MapHandle, MapProps>(({
  center,
  sunAltitude,
  sunAzimuth,
  routeData,
  selectedRouteIndex,
  onRouteSelect,
  origin,
  destination,
  onMapClick,
  onLocationFound,
  isSelecting
}, ref) => {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const originMarker = useRef<maplibregl.Marker | null>(null)
  const destMarker = useRef<maplibregl.Marker | null>(null)
  const geolocateControl = useRef<maplibregl.GeolocateControl | null>(null)

  // Expose methods to parent
  useImperativeHandle(ref, () => ({
    flyTo: (coord: Coordinate) => {
      map.current?.flyTo({
        center: [coord.lon, coord.lat],
        zoom: 17,
        pitch: 60,
        bearing: sunAzimuth - 180, // Face towards sun
        duration: 2000
      })
    },
    triggerGeolocate: () => {
      geolocateControl.current?.trigger()
    }
  }))

  // Initialize map with dark style
  useEffect(() => {
    if (map.current || !mapContainer.current) return

    // Dark style optimized for SunWalk
    const darkStyle: maplibregl.StyleSpecification = {
      version: 8,
      name: 'SunWalk Dark',
      sources: {
        'carto-dark': {
          type: 'raster',
          tiles: [
            'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
            'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
            'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png'
          ],
          tileSize: 256,
          attribution: '&copy; CARTO, OpenStreetMap'
        }
      },
      layers: [
        {
          id: 'background',
          type: 'background',
          paint: { 'background-color': COLORS.groundDark }
        },
        {
          id: 'base-tiles',
          type: 'raster',
          source: 'carto-dark',
          minzoom: 0,
          maxzoom: 20,
          paint: { 'raster-opacity': 0.8 }
        }
      ]
    }

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: darkStyle,
      center: [center.lon, center.lat],
      zoom: 16,
      pitch: 60,
      bearing: -17,
      maxPitch: 85,
      attributionControl: false
    })

    // Hidden geolocate control (triggered programmatically)
    geolocateControl.current = new maplibregl.GeolocateControl({
      positionOptions: { enableHighAccuracy: true },
      trackUserLocation: true
    })
    map.current.addControl(geolocateControl.current, 'top-right')

    // Hide the default control - we'll use our floating button
    setTimeout(() => {
      const geoBtn = document.querySelector('.maplibregl-ctrl-geolocate')
      if (geoBtn) (geoBtn as HTMLElement).style.display = 'none'
    }, 100)

    geolocateControl.current.on('geolocate', (e: GeolocationPosition) => {
      onLocationFound({
        lat: e.coords.latitude,
        lon: e.coords.longitude
      })
    })

    map.current.on('load', () => {
      // Shadow polygons layer (ground shadows)
      map.current!.addSource('shadows', {
        type: 'geojson',
        data: emptyFC
      })

      map.current!.addLayer({
        id: 'shadow-fill',
        type: 'fill',
        source: 'shadows',
        paint: {
          'fill-color': COLORS.shadowNavy,
          'fill-opacity': 0.6
        }
      })

      // Alternative routes source (rendered below primary)
      map.current!.addSource('route-alternatives', {
        type: 'geojson',
        data: emptyFC
      })

      map.current!.addLayer({
        id: 'route-alt-line',
        type: 'line',
        source: 'route-alternatives',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': ['get', 'color'],
          'line-width': 3,
          'line-opacity': 0.4,
          'line-dasharray': [2, 4]
        }
      })

      // Primary route source
      map.current!.addSource('route', {
        type: 'geojson',
        data: emptyFC
      })

      // Route glow (outer)
      map.current!.addLayer({
        id: 'route-glow',
        type: 'line',
        source: 'route',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': COLORS.solarGold,
          'line-width': 16,
          'line-opacity': 0.3,
          'line-blur': 8
        }
      })

      // Route line (main)
      map.current!.addLayer({
        id: 'route-line',
        type: 'line',
        source: 'route',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': COLORS.solarGold,
          'line-width': 5,
          'line-opacity': 1
        }
      })

      // Route dashes (animated effect)
      map.current!.addLayer({
        id: 'route-arrows',
        type: 'symbol',
        source: 'route',
        layout: {
          'symbol-placement': 'line',
          'symbol-spacing': 50,
          'text-field': '▸',
          'text-size': 16,
          'text-keep-upright': false,
          'text-rotation-alignment': 'map'
        },
        paint: {
          'text-color': '#FFFFFF',
          'text-halo-color': COLORS.solarGold,
          'text-halo-width': 1
        }
      })

      // Click on alternative routes to select them
      map.current!.on('click', 'route-alt-line', (e) => {
        if (e.features?.[0]?.properties?.routeIndex !== undefined) {
          onRouteSelect(e.features[0].properties.routeIndex)
        }
      })

      // Cursor pointer on alt routes
      map.current!.on('mouseenter', 'route-alt-line', () => {
        if (map.current) map.current.getCanvas().style.cursor = 'pointer'
      })
      map.current!.on('mouseleave', 'route-alt-line', () => {
        if (map.current && !isSelecting) map.current.getCanvas().style.cursor = ''
      })

      // Load initial shadows
      loadShadows()
    })

    return () => {
      map.current?.remove()
      map.current = null
    }
  }, [])

  // Load shadows from API
  const loadShadows = async () => {
    try {
      const response = await fetch('/api/v1/shadows/current')
      const data = await response.json()

      if (data.shadow_geojson && map.current?.getSource('shadows')) {
        const source = map.current.getSource('shadows') as maplibregl.GeoJSONSource
        source.setData(data.shadow_geojson)
      }
    } catch (error) {
      console.log('Shadows will load on next update')
    }
  }

  // Handle map clicks
  useEffect(() => {
    if (!map.current) return

    const handleClick = (e: maplibregl.MapMouseEvent) => {
      if (isSelecting) {
        onMapClick({ lat: e.lngLat.lat, lon: e.lngLat.lng })
      }
    }

    map.current.on('click', handleClick)
    map.current.getCanvas().style.cursor = isSelecting ? 'crosshair' : ''

    return () => {
      map.current?.off('click', handleClick)
    }
  }, [isSelecting, onMapClick])

  // Update shadows when sun position changes
  useEffect(() => {
    if (!map.current?.isStyleLoaded() || sunAltitude <= 0) return
    loadShadows()
  }, [sunAltitude, sunAzimuth])

  // Update route visualization (multi-route)
  useEffect(() => {
    if (!map.current?.isStyleLoaded()) return

    const primarySource = map.current.getSource('route') as maplibregl.GeoJSONSource
    const altSource = map.current.getSource('route-alternatives') as maplibregl.GeoJSONSource
    if (!primarySource || !altSource) return

    if (routeData && routeData.routes.length > 0) {
      const selected = routeData.routes[selectedRouteIndex] ?? routeData.routes[0]

      // Set primary route
      primarySource.setData({
        type: 'FeatureCollection',
        features: [selected.route_geojson]
      })

      // Set alternative routes (all non-selected)
      const altFeatures = routeData.routes
        .map((route, i) => {
          if (i === selectedRouteIndex) return null
          return {
            ...route.route_geojson,
            properties: {
              ...route.route_geojson.properties,
              routeIndex: i,
              color: getRouteColor(route.label),
            }
          }
        })
        .filter(Boolean) as GeoJSON.Feature[]

      altSource.setData({
        type: 'FeatureCollection',
        features: altFeatures,
      })

      // Color primary route based on label
      const routeColor = getRouteColor(selected.label)
      map.current.setPaintProperty('route-line', 'line-color', routeColor)
      map.current.setPaintProperty('route-glow', 'line-color', routeColor)
      map.current.setPaintProperty('route-arrows', 'text-halo-color', routeColor)

      // Fit map to selected route's coordinates
      const coords = (selected.route_geojson.geometry as GeoJSON.LineString).coordinates
      if (coords && coords.length > 0) {
        const bounds = new maplibregl.LngLatBounds()
        for (const coord of coords) {
          bounds.extend([coord[0], coord[1]])
        }
        map.current.fitBounds(bounds, {
          padding: { top: 100, bottom: 300, left: 50, right: 50 },
          pitch: 50,
          duration: 1500
        })
      }
    } else {
      primarySource.setData(emptyFC)
      altSource.setData(emptyFC)
    }
  }, [routeData, selectedRouteIndex])

  // Origin marker (pulsing dot)
  useEffect(() => {
    if (!map.current) return

    originMarker.current?.remove()
    originMarker.current = null

    if (origin) {
      const el = document.createElement('div')
      el.className = 'marker-origin'

      originMarker.current = new maplibregl.Marker({ element: el, anchor: 'center' })
        .setLngLat([origin.lon, origin.lat])
        .addTo(map.current)
    }
  }, [origin])

  // Destination marker (pin)
  useEffect(() => {
    if (!map.current) return

    destMarker.current?.remove()
    destMarker.current = null

    if (destination) {
      const el = document.createElement('div')
      el.className = 'marker-destination'

      destMarker.current = new maplibregl.Marker({ element: el, anchor: 'bottom' })
        .setLngLat([destination.lon, destination.lat])
        .addTo(map.current)
    }
  }, [destination])

  return <div ref={mapContainer} className="map-container" />
})

Map.displayName = 'Map'
export default Map
