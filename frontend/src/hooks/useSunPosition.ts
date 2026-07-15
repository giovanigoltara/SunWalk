import { useState, useEffect } from 'react'
import { api } from '../services/api'
import type { Coordinate, SunPosition } from '../types'

export function useSunPosition(location: Coordinate, time: Date) {
  const [sunPosition, setSunPosition] = useState<SunPosition | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    let cancelled = false

    async function fetchSunPosition() {
      setIsLoading(true)
      setError(null)

      try {
        const position = await api.getSunPosition(location.lat, location.lon, time)
        if (!cancelled) {
          setSunPosition(position)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error('Failed to fetch sun position'))
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    fetchSunPosition()

    return () => {
      cancelled = true
    }
  }, [location.lat, location.lon, time.getTime()])

  return { sunPosition, isLoading, error }
}
