import { useState, useCallback, useRef } from 'react'
import Landing from './components/Landing'
import Map, { MapHandle } from './components/Map'
import FloatingControls from './components/FloatingControls'
import SearchModal from './components/SearchModal'
import BottomSheet from './components/BottomSheet'
import { useSunPosition } from './hooks/useSunPosition'
import { useRoute } from './hooks/useRoute'
import type { Coordinate, RoutePreference } from './types'

function App() {
  const mapRef = useRef<MapHandle>(null)

  // Landing page (shown once per browser session)
  const [showLanding, setShowLanding] = useState(
    () => sessionStorage.getItem('sunwalk-entered') !== '1'
  )
  const handleEnterApp = useCallback(() => {
    sessionStorage.setItem('sunwalk-entered', '1')
    setShowLanding(false)
  }, [])

  // Location state
  const [origin, setOrigin] = useState<Coordinate | null>(null)
  const [destination, setDestination] = useState<Coordinate | null>(null)
  const [destinationName, setDestinationName] = useState('')
  const [isLocating, setIsLocating] = useState(false)

  // UI state
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [isSelectingOnMap, setIsSelectingOnMap] = useState(false)

  // Route state
  const [selectedTime, setSelectedTime] = useState<Date>(new Date())
  const [routePreference, setRoutePreference] = useState<RoutePreference>('sun')

  // Berlin Mitte center
  const defaultCenter: Coordinate = { lat: 52.52, lon: 13.405 }

  // Hooks
  const { sunPosition } = useSunPosition(origin || defaultCenter, selectedTime)
  const {
    routeData,
    selectedIndex,
    setSelectedIndex,
    isLoading: routeLoading,
    calculateRoute,
    clearRoute
  } = useRoute()

  // Handle GPS click
  const handleGpsClick = useCallback(() => {
    setIsLocating(true)
    mapRef.current?.triggerGeolocate()
  }, [])

  // Handle location found from GPS
  const handleLocationFound = useCallback((coord: Coordinate) => {
    setOrigin(coord)
    setIsLocating(false)
    mapRef.current?.flyTo(coord)
  }, [])

  // Handle search result selection
  const handleSelectDestination = useCallback((coord: Coordinate, name: string) => {
    setDestination(coord)
    setDestinationName(name)
    mapRef.current?.flyTo(coord)
  }, [])

  // Handle map click (for manual selection)
  const handleMapClick = useCallback((coord: Coordinate) => {
    if (isSelectingOnMap) {
      setDestination(coord)
      setDestinationName('Selected location')
      setIsSelectingOnMap(false)
    }
  }, [isSelectingOnMap])

  // Calculate route
  const handleCalculateRoute = useCallback(() => {
    if (origin && destination) {
      calculateRoute(origin, destination, routePreference, selectedTime)
    }
  }, [origin, destination, routePreference, selectedTime, calculateRoute])

  // Clear route and destination
  const handleClearRoute = useCallback(() => {
    clearRoute()
    setDestination(null)
    setDestinationName('')
  }, [clearRoute])

  // Settings click (placeholder)
  const handleSettingsClick = useCallback(() => {
    // TODO: Open settings modal
    console.log('Settings clicked')
  }, [])

  if (showLanding) {
    return <Landing onEnter={handleEnterApp} />
  }

  return (
    <div className="app">
      {/* Full-screen Map */}
      <Map
        ref={mapRef}
        center={defaultCenter}
        sunAltitude={sunPosition?.altitude_deg || 0}
        sunAzimuth={sunPosition?.azimuth_deg || 180}
        routeData={routeData}
        selectedRouteIndex={selectedIndex}
        onRouteSelect={setSelectedIndex}
        origin={origin}
        destination={destination}
        onMapClick={handleMapClick}
        onLocationFound={handleLocationFound}
        isSelecting={isSelectingOnMap}
      />

      {/* Floating Glass Controls */}
      <FloatingControls
        onGpsClick={handleGpsClick}
        onSearchClick={() => setIsSearchOpen(true)}
        onSettingsClick={handleSettingsClick}
        isLocating={isLocating}
      />

      {/* Search Modal */}
      <SearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onSelectLocation={handleSelectDestination}
        placeholder="Where do you want to go?"
      />

      {/* Bottom Sheet with Time Slider & Route Info */}
      <BottomSheet
        sunPosition={sunPosition}
        selectedTime={selectedTime}
        onTimeChange={setSelectedTime}
        origin={origin}
        destination={destination}
        destinationName={destinationName}
        routePreference={routePreference}
        onPreferenceChange={setRoutePreference}
        onCalculateRoute={handleCalculateRoute}
        onClearRoute={handleClearRoute}
        routeData={routeData}
        selectedRouteIndex={selectedIndex}
        onSelectRoute={setSelectedIndex}
        isCalculating={routeLoading}
      />

      {/* Map Selection Hint */}
      {isSelectingOnMap && (
        <div className="selection-overlay">
          <div className="selection-hint">
            Tap on the map to select destination
            <button onClick={() => setIsSelectingOnMap(false)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
