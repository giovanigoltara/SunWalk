import { useState, useRef } from 'react'
import type { Coordinate, RoutePreference, MultiRouteResponse, RouteAlternative, SunPosition } from '../types'

interface BottomSheetProps {
  sunPosition: SunPosition | null
  selectedTime: Date
  onTimeChange: (time: Date) => void
  origin: Coordinate | null
  destination: Coordinate | null
  destinationName: string
  routePreference: RoutePreference
  onPreferenceChange: (pref: RoutePreference) => void
  onCalculateRoute: () => void
  onClearRoute: () => void
  routeData: MultiRouteResponse | null
  selectedRouteIndex: number
  onSelectRoute: (index: number) => void
  isCalculating: boolean
}

function getLabelEmoji(label: string): string {
  switch (label) {
    case 'sunniest': return '☀️'
    case 'shadiest': return '🌳'
    case 'fastest': return '⚡'
    default: return '🔀'
  }
}

function getLabelText(label: string): string {
  switch (label) {
    case 'sunniest': return 'Sunniest'
    case 'shadiest': return 'Shadiest'
    case 'fastest': return 'Fastest'
    default: return 'Alt'
  }
}

export default function BottomSheet({
  sunPosition,
  selectedTime,
  onTimeChange,
  origin,
  destination,
  destinationName,
  routePreference,
  onPreferenceChange,
  onCalculateRoute,
  onClearRoute,
  routeData,
  selectedRouteIndex,
  onSelectRoute,
  isCalculating
}: BottomSheetProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const sheetRef = useRef<HTMLDivElement>(null)

  const selectedRoute: RouteAlternative | null =
    routeData && routeData.routes.length > 0
      ? routeData.routes[selectedRouteIndex] ?? routeData.routes[0]
      : null

  // Calculate time range for slider (sunrise to sunset)
  const sunrise = sunPosition?.sunrise ? new Date(sunPosition.sunrise) : new Date()
  const sunset = sunPosition?.sunset ? new Date(sunPosition.sunset) : new Date()
  sunrise.setHours(Math.max(6, sunrise.getHours()))
  sunset.setHours(Math.min(21, sunset.getHours()))

  const timeToMinutes = (date: Date) => date.getHours() * 60 + date.getMinutes()
  const minutesToTime = (minutes: number) => {
    const d = new Date(selectedTime)
    d.setHours(Math.floor(minutes / 60), minutes % 60)
    return d
  }

  const minMinutes = timeToMinutes(sunrise)
  const maxMinutes = timeToMinutes(sunset)
  const currentMinutes = timeToMinutes(selectedTime)

  const formatTime = (date: Date) =>
    date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })

  const formatDistance = (m: number) => m < 1000 ? `${Math.round(m)}m` : `${(m / 1000).toFixed(1)}km`
  const formatDuration = (min: number) => min < 60 ? `${Math.round(min)} min` : `${Math.floor(min / 60)}h ${Math.round(min % 60)}m`

  return (
    <div
      ref={sheetRef}
      className={`bottom-sheet ${isExpanded ? 'expanded' : ''} ${routeData ? 'has-route' : ''}`}
    >
      {/* Drag Handle */}
      <div className="sheet-handle" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="handle-bar" />
      </div>

      {/* Weather Bar */}
      <div className="weather-bar">
        <div className="weather-item">
          {sunPosition?.is_daytime ? (
            <>
              <span className="weather-icon">☀️</span>
              <span className="weather-value">{sunPosition.altitude_deg.toFixed(0)}°</span>
              <span className="weather-label">altitude</span>
            </>
          ) : (
            <>
              <span className="weather-icon">🌙</span>
              <span className="weather-value">Night</span>
              <span className="weather-label">no sun</span>
            </>
          )}
        </div>
        <div className="weather-divider" />
        <div className="weather-item">
          <span className="weather-icon">🌅</span>
          <span className="weather-value">{formatTime(new Date(sunPosition?.sunrise || ''))}</span>
          <span className="weather-label">sunrise</span>
        </div>
        <div className="weather-divider" />
        <div className="weather-item">
          <span className="weather-icon">🌇</span>
          <span className="weather-value">{formatTime(new Date(sunPosition?.sunset || ''))}</span>
          <span className="weather-label">sunset</span>
        </div>
      </div>

      {/* Time Slider */}
      <div className="time-slider-container">
        <span className="time-label">{formatTime(sunrise)}</span>
        <div className="time-slider-wrapper">
          <input
            type="range"
            min={minMinutes}
            max={maxMinutes}
            value={currentMinutes}
            onChange={e => onTimeChange(minutesToTime(parseInt(e.target.value)))}
            className="time-slider"
          />
          <div className="time-current">{formatTime(selectedTime)}</div>
        </div>
        <span className="time-label">{formatTime(sunset)}</span>
      </div>

      {/* Route Section */}
      {(origin || destination) && (
        <div className="route-section">
          {/* Destination Display */}
          {destination && (
            <div className="destination-display">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFD700" strokeWidth="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" />
                <circle cx="12" cy="10" r="3" />
              </svg>
              <span>{destinationName || 'Selected destination'}</span>
              <button onClick={onClearRoute} className="clear-btn">×</button>
            </div>
          )}

          {/* Route Preference Toggle */}
          <div className="preference-toggle">
            <button
              className={`pref-option ${routePreference === 'sun' ? 'active sun' : ''}`}
              onClick={() => onPreferenceChange('sun')}
            >
              <span className="pref-icon">☀️</span>
              <span>Sunny</span>
            </button>
            <button
              className={`pref-option ${routePreference === 'shade' ? 'active shade' : ''}`}
              onClick={() => onPreferenceChange('shade')}
            >
              <span className="pref-icon">🌳</span>
              <span>Shady</span>
            </button>
          </div>

          {/* Calculate Button */}
          {origin && destination && !routeData && (
            <button
              className="calculate-route-btn"
              onClick={onCalculateRoute}
              disabled={isCalculating}
            >
              {isCalculating ? (
                <><span className="spinner" /> Calculating...</>
              ) : (
                <>Get {routePreference === 'sun' ? '☀️ Sunny' : '🌳 Shady'} Route</>
              )}
            </button>
          )}

          {/* Route Tabs - select between alternatives */}
          {routeData && routeData.routes.length > 1 && (
            <div className="route-tabs">
              {routeData.routes.map((alt, i) => (
                <button
                  key={i}
                  className={`route-tab ${i === selectedRouteIndex ? 'active' : ''} ${alt.label}`}
                  onClick={() => onSelectRoute(i)}
                >
                  <span className="route-tab-emoji">{getLabelEmoji(alt.label)}</span>
                  <span className="route-tab-label">{getLabelText(alt.label)}</span>
                  <span className="route-tab-sun">{alt.sun_exposure_pct.toFixed(0)}% sun</span>
                </button>
              ))}
            </div>
          )}

          {/* Route Result */}
          {selectedRoute && (
            <div className="route-result">
              <div className="route-stats">
                <div className="stat">
                  <span className="stat-value">{formatDistance(selectedRoute.total_distance_m)}</span>
                  <span className="stat-label">distance</span>
                </div>
                <div className="stat">
                  <span className="stat-value">{formatDuration(selectedRoute.total_duration_min)}</span>
                  <span className="stat-label">walking</span>
                </div>
                <div className="stat sun-stat">
                  <span className="stat-value">{selectedRoute.sun_exposure_pct.toFixed(0)}%</span>
                  <span className="stat-label">☀️ sun</span>
                </div>
                <div className="stat shade-stat">
                  <span className="stat-value">{selectedRoute.shade_exposure_pct.toFixed(0)}%</span>
                  <span className="stat-label">🌳 shade</span>
                </div>
              </div>

              {/* Exposure Bar */}
              <div className="exposure-bar">
                <div
                  className="exposure-sun"
                  style={{ width: `${selectedRoute.sun_exposure_pct}%` }}
                />
                <div
                  className="exposure-shade"
                  style={{ width: `${selectedRoute.shade_exposure_pct}%` }}
                />
              </div>

              <button className="new-route-btn" onClick={onClearRoute}>
                New Route
              </button>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!origin && !destination && (
        <div className="empty-state">
          <p>Tap <strong>GPS</strong> to start from your location</p>
          <p>Then <strong>Search</strong> for a destination</p>
        </div>
      )}
    </div>
  )
}
