import type { Coordinate, RoutePreference } from '../types'

interface ControlsProps {
  selectedTime: Date
  onTimeChange: (time: Date) => void
  routePreference: RoutePreference
  onPreferenceChange: (pref: RoutePreference) => void
  onSelectOrigin: () => void
  onSelectDestination: () => void
  onUseCurrentLocation: () => void
  onCalculateRoute: () => void
  origin: Coordinate | null
  destination: Coordinate | null
  isCalculating: boolean
  isSelectingOrigin: boolean
  isSelectingDestination: boolean
}

export default function Controls({
  selectedTime,
  onTimeChange,
  routePreference,
  onPreferenceChange,
  onSelectOrigin,
  onSelectDestination,
  onUseCurrentLocation,
  onCalculateRoute,
  origin,
  destination,
  isCalculating,
  isSelectingOrigin,
  isSelectingDestination
}: ControlsProps) {
  const formatTimeForInput = (date: Date) => {
    return date.toTimeString().slice(0, 5)
  }

  const handleTimeChange = (timeStr: string) => {
    const [hours, minutes] = timeStr.split(':').map(Number)
    const newDate = new Date(selectedTime)
    newDate.setHours(hours, minutes)
    onTimeChange(newDate)
  }

  return (
    <div className="controls">
      <div className="controls-header">
        <h1>☀️ SunWalk</h1>
        <p>Find your perfect route</p>
      </div>

      <div className="control-group">
        <label>Time</label>
        <input
          type="time"
          value={formatTimeForInput(selectedTime)}
          onChange={(e) => handleTimeChange(e.target.value)}
        />
      </div>

      <div className="control-group">
        <label>Route Preference</label>
        <div className="preference-buttons">
          <button
            className={`pref-btn ${routePreference === 'sun' ? 'active' : ''}`}
            onClick={() => onPreferenceChange('sun')}
          >
            ☀️ Sun
          </button>
          <button
            className={`pref-btn ${routePreference === 'shade' ? 'active' : ''}`}
            onClick={() => onPreferenceChange('shade')}
          >
            🌳 Shade
          </button>
          <button
            className={`pref-btn ${routePreference === 'balanced' ? 'active' : ''}`}
            onClick={() => onPreferenceChange('balanced')}
          >
            ⚖️ Mix
          </button>
        </div>
      </div>

      <div className="control-group">
        <label>Start Point</label>
        <div className="point-buttons">
          <button
            className={`point-btn ${isSelectingOrigin ? 'selecting' : ''}`}
            onClick={onSelectOrigin}
          >
            {origin ? '✓ Selected' : '📍 Select on map'}
          </button>
          <button className="point-btn secondary" onClick={onUseCurrentLocation}>
            📱 Use GPS
          </button>
        </div>
      </div>

      <div className="control-group">
        <label>Destination</label>
        <button
          className={`point-btn ${isSelectingDestination ? 'selecting' : ''}`}
          onClick={onSelectDestination}
        >
          {destination ? '✓ Selected' : '📍 Select on map'}
        </button>
      </div>

      <button
        className="calculate-btn"
        onClick={onCalculateRoute}
        disabled={!origin || !destination || isCalculating}
      >
        {isCalculating ? 'Calculating...' : '🚶 Get Route'}
      </button>

      {(isSelectingOrigin || isSelectingDestination) && (
        <div className="selection-hint">
          👆 Tap on the map to select {isSelectingOrigin ? 'start' : 'destination'}
        </div>
      )}
    </div>
  )
}
