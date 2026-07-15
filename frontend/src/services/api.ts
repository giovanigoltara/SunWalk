import type { Coordinate, RoutePreference, SunPosition, ShadowResponse, MultiRouteResponse } from '../types'

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }

  return response.json()
}

export const api = {
  async getSunPosition(lat: number, lon: number, timestamp?: Date): Promise<SunPosition> {
    const params = new URLSearchParams({
      lat: lat.toString(),
      lon: lon.toString(),
    })

    if (timestamp) {
      params.append('timestamp', timestamp.toISOString())
    }

    return fetchJSON<SunPosition>(`${API_BASE}/sun/position?${params}`)
  },

  async getShadows(timestamp?: Date): Promise<ShadowResponse> {
    const params = new URLSearchParams()

    if (timestamp) {
      params.append('timestamp', timestamp.toISOString())
    }

    const url = timestamp
      ? `${API_BASE}/shadows/at-time?${params}`
      : `${API_BASE}/shadows/current`

    return fetchJSON<ShadowResponse>(url)
  },

  async calculateRoute(
    origin: Coordinate,
    destination: Coordinate,
    preference: RoutePreference,
    departureTime?: Date
  ): Promise<MultiRouteResponse> {
    const body = {
      origin,
      destination,
      preference,
      departure_time: departureTime?.toISOString()
    }

    return fetchJSON<MultiRouteResponse>(`${API_BASE}/routes/optimize`, {
      method: 'POST',
      body: JSON.stringify(body)
    })
  }
}
