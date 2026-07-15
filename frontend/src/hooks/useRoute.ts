import { useState, useCallback, useMemo } from 'react'
import { api } from '../services/api'
import type { Coordinate, RoutePreference, MultiRouteResponse, RouteAlternative } from '../types'

export function useRoute() {
  const [routeData, setRouteData] = useState<MultiRouteResponse | null>(null)
  const [selectedIndex, setSelectedIndex] = useState<number>(0)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const selectedRoute: RouteAlternative | null = useMemo(() => {
    if (!routeData || routeData.routes.length === 0) return null
    return routeData.routes[selectedIndex] ?? routeData.routes[0]
  }, [routeData, selectedIndex])

  const calculateRoute = useCallback(async (
    origin: Coordinate | null,
    destination: Coordinate | null,
    preference: RoutePreference,
    departureTime: Date
  ) => {
    if (!origin || !destination) {
      setRouteData(null)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const data = await api.calculateRoute(origin, destination, preference, departureTime)
      setRouteData(data)
      setSelectedIndex(data.recommended_index)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to calculate route'))
      setRouteData(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const clearRoute = useCallback(() => {
    setRouteData(null)
    setSelectedIndex(0)
    setError(null)
  }, [])

  return {
    routeData,
    selectedRoute,
    selectedIndex,
    setSelectedIndex,
    isLoading,
    error,
    calculateRoute,
    clearRoute
  }
}
