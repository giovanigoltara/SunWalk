import type { Route } from '../types'

interface RoutePanelProps {
  route: Route
  onClose: () => void
}

export default function RoutePanel({ route, onClose }: RoutePanelProps) {
  const formatDistance = (meters: number) => {
    if (meters < 1000) {
      return `${Math.round(meters)} m`
    }
    return `${(meters / 1000).toFixed(1)} km`
  }

  const formatDuration = (minutes: number) => {
    if (minutes < 60) {
      return `${Math.round(minutes)} min`
    }
    const hours = Math.floor(minutes / 60)
    const mins = Math.round(minutes % 60)
    return `${hours}h ${mins}min`
  }

  return (
    <div className="route-panel">
      <div className="route-panel-header">
        <h2>Your Route</h2>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>

      <div className="route-stats">
        <div className="stat">
          <span className="stat-icon">📏</span>
          <span className="stat-value">{formatDistance(route.total_distance_m)}</span>
          <span className="stat-label">Distance</span>
        </div>
        <div className="stat">
          <span className="stat-icon">⏱️</span>
          <span className="stat-value">{formatDuration(route.total_duration_min)}</span>
          <span className="stat-label">Walking time</span>
        </div>
      </div>

      <div className="exposure-bars">
        <div className="exposure-bar sun">
          <div className="bar-fill" style={{ width: `${route.sun_exposure_pct}%` }} />
          <span className="bar-label">☀️ {route.sun_exposure_pct.toFixed(0)}% sun</span>
        </div>
        <div className="exposure-bar shade">
          <div className="bar-fill" style={{ width: `${route.shade_exposure_pct}%` }} />
          <span className="bar-label">🌳 {route.shade_exposure_pct.toFixed(0)}% shade</span>
        </div>
      </div>

      <div className="route-preference-badge">
        {route.preference === 'sun' && '☀️ Sun-optimized route'}
        {route.preference === 'shade' && '🌳 Shade-optimized route'}
        {route.preference === 'balanced' && '⚖️ Balanced route'}
      </div>

      {route.steps.length > 0 && (
        <div className="route-steps">
          <h3>Directions</h3>
          {route.steps.map((step, i) => (
            <div key={i} className="step">
              <span className="step-number">{i + 1}</span>
              <span className="step-instruction">
                {step.instruction || 'Continue walking'}
              </span>
              <span className="step-distance">{formatDistance(step.distance_m)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
