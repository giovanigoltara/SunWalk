import type { SunPosition } from '../types'

interface SunInfoProps {
  sunPosition: SunPosition | null
  isLoading: boolean
}

export default function SunInfo({ sunPosition, isLoading }: SunInfoProps) {
  if (isLoading) {
    return (
      <div className="sun-info">
        <span>Loading sun data...</span>
      </div>
    )
  }

  if (!sunPosition) {
    return null
  }

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="sun-info">
      {sunPosition.is_daytime ? (
        <>
          <span className="sun-icon">☀️</span>
          <span className="sun-altitude">
            {sunPosition.altitude_deg.toFixed(1)}°
          </span>
          <span className="sun-times">
            🌅 {formatTime(sunPosition.sunrise)} • 🌇 {formatTime(sunPosition.sunset)}
          </span>
        </>
      ) : (
        <>
          <span className="sun-icon">🌙</span>
          <span>Night time</span>
        </>
      )}
    </div>
  )
}
