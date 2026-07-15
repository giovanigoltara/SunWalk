import { useState, useEffect } from 'react'
import { api } from '../services/api'
import type { ShadowResponse } from '../types'

export function useShadows(time: Date) {
  const [shadows, setShadows] = useState<ShadowResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    let cancelled = false

    async function fetchShadows() {
      setIsLoading(true)
      setError(null)

      try {
        const shadowData = await api.getShadows(time)
        if (!cancelled) {
          setShadows(shadowData)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error('Failed to fetch shadows'))
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    fetchShadows()

    return () => {
      cancelled = true
    }
  }, [time.getTime()])

  return { shadows, isLoading, error }
}
