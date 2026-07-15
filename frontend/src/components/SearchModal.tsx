import { useState, useRef, useEffect } from 'react'
import type { Coordinate } from '../types'

interface SearchModalProps {
  isOpen: boolean
  onClose: () => void
  onSelectLocation: (coord: Coordinate, name: string) => void
  placeholder?: string
}

// Simple geocoding using Nominatim (OSM)
async function searchLocation(query: string): Promise<Array<{ name: string; coord: Coordinate }>> {
  if (!query.trim()) return []

  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&viewbox=13.2,52.4,13.6,52.6&bounded=1`,
      { headers: { 'User-Agent': 'SunWalk/1.0' } }
    )
    const data = await response.json()

    return data.map((item: any) => ({
      name: item.display_name.split(',').slice(0, 3).join(', '),
      coord: {
        lat: parseFloat(item.lat),
        lon: parseFloat(item.lon)
      }
    }))
  } catch (error) {
    console.error('Search failed:', error)
    return []
  }
}

export default function SearchModal({
  isOpen,
  onClose,
  onSelectLocation,
  placeholder = 'Search destination...'
}: SearchModalProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Array<{ name: string; coord: Coordinate }>>([])
  const [isSearching, setIsSearching] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus()
      setQuery('')
      setResults([])
    }
  }, [isOpen])

  const handleSearch = (value: string) => {
    setQuery(value)

    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }

    if (value.length < 3) {
      setResults([])
      return
    }

    debounceRef.current = setTimeout(async () => {
      setIsSearching(true)
      const locations = await searchLocation(value)
      setResults(locations)
      setIsSearching(false)
    }, 300)
  }

  const handleSelect = (result: { name: string; coord: Coordinate }) => {
    onSelectLocation(result.coord, result.name)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="search-modal-overlay" onClick={onClose}>
      <div className="search-modal" onClick={e => e.stopPropagation()}>
        <div className="search-input-wrapper">
          <svg className="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => handleSearch(e.target.value)}
            placeholder={placeholder}
            className="search-input"
          />
          {query && (
            <button className="search-clear" onClick={() => handleSearch('')}>
              ×
            </button>
          )}
        </div>

        {isSearching && (
          <div className="search-loading">
            <span className="spinner" />
            Searching...
          </div>
        )}

        {results.length > 0 && (
          <ul className="search-results">
            {results.map((result, i) => (
              <li key={i}>
                <button onClick={() => handleSelect(result)}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" />
                    <circle cx="12" cy="10" r="3" />
                  </svg>
                  <span>{result.name}</span>
                </button>
              </li>
            ))}
          </ul>
        )}

        {query.length >= 3 && !isSearching && results.length === 0 && (
          <div className="search-empty">
            No results found. Try a different search.
          </div>
        )}

        <button className="search-close" onClick={onClose}>
          Cancel
        </button>
      </div>
    </div>
  )
}
