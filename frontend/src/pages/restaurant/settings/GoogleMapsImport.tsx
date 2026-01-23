import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../../../services/api'
import { MapPin, Search, CheckCircle, Loader2 } from 'lucide-react'

interface GoogleMapsImportProps {
  accountId: number
  onHoursImported: (hours: { opening_time?: string; closing_time?: string; operating_days?: number[] }) => void
}

export default function GoogleMapsImport({ accountId, onHoursImported }: GoogleMapsImportProps) {
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')
  const [searchLocation, setSearchLocation] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [selectedPlace, setSelectedPlace] = useState<any>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState('')

  const updateHoursFromGoogleMutation = useMutation({
    mutationFn: (placeId: string) => restaurantAPI.updateHoursFromGoogle(accountId, placeId),
    onSuccess: (response) => {
      const data = response.data
      onHoursImported({
        opening_time: data.opening_time,
        closing_time: data.closing_time,
        operating_days: data.operating_days,
      })
      setSelectedPlace(null)
      setSearchResults([])
      setSearchQuery('')
      queryClient.invalidateQueries({ queryKey: ['account', accountId] })
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to import hours from Google Maps')
    },
  })

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) {
      setError('Please enter a search query')
      return
    }

    setIsSearching(true)
    setError('')
    setSearchResults([])
    setSelectedPlace(null)

    try {
      const response = await restaurantAPI.searchGoogleMaps(searchQuery.trim(), searchLocation.trim() || undefined)
      setSearchResults(response.data.results || [])
      if (response.data.results.length === 0) {
        setError('No restaurants found. Try a different search term.')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to search Google Maps.')
    } finally {
      setIsSearching(false)
    }
  }

  const handleSelectPlace = async (place: any) => {
    setSelectedPlace(place)
    setError('')

    try {
      const response = await restaurantAPI.getGoogleMapsPlace(place.place_id)
      const hours = response.data.opening_hours
      if (hours?.opening_time && hours?.closing_time) {
        onHoursImported({
          opening_time: hours.opening_time,
          closing_time: hours.closing_time,
          operating_days: hours.operating_days,
        })
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to get place details')
    }
  }

  const handleImportHours = () => {
    if (!selectedPlace) {
      setError('Please select a restaurant from the search results')
      return
    }
    updateHoursFromGoogleMutation.mutate(selectedPlace.place_id)
  }

  return (
    <div className="p-4 rounded-lg bg-accent/10 border border-accent/20">
      <div className="flex items-start gap-3 mb-4">
        <MapPin className="w-5 h-5 text-accent flex-shrink-0" />
        <div className="flex-1">
          <h3 className="font-medium mb-1">Import from Google Maps</h3>
          <p className="text-sm text-dim">
            Search for your restaurant to automatically import hours.
          </p>
        </div>
      </div>

      <form onSubmit={handleSearch} className="space-y-3 mb-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="md:col-span-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for your restaurant..."
              disabled={isSearching}
            />
          </div>
          <div>
            <input
              type="text"
              value={searchLocation}
              onChange={(e) => setSearchLocation(e.target.value)}
              placeholder="Location (optional)"
              disabled={isSearching}
            />
          </div>
        </div>
        <button
          type="submit"
          disabled={isSearching || !searchQuery.trim()}
          className="btn btn-primary flex items-center gap-2"
        >
          {isSearching ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Searching...
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              Search
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="p-3 mb-4 rounded-lg bg-danger/10 border border-danger/20">
          <p className="text-sm text-danger">{error}</p>
        </div>
      )}

      {searchResults.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium">Search Results:</p>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {searchResults.map((place) => (
              <button
                key={place.place_id}
                type="button"
                onClick={() => handleSelectPlace(place)}
                className={`w-full text-left p-3 rounded-lg border transition-all ${
                  selectedPlace?.place_id === place.place_id
                    ? 'border-accent bg-accent/10'
                    : 'border-[--border] bg-white/5 hover:border-accent/50'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <p className="font-medium">{place.name}</p>
                    <p className="text-sm text-dim mt-1">
                      {place.formatted_address || place.vicinity}
                    </p>
                    {place.rating && (
                      <p className="text-xs text-dim mt-1">
                        {place.rating} ({place.user_ratings_total} reviews)
                      </p>
                    )}
                  </div>
                  {selectedPlace?.place_id === place.place_id && (
                    <CheckCircle className="w-5 h-5 text-accent flex-shrink-0" />
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {selectedPlace && (
        <div className="mt-4 p-4 rounded-lg bg-white/5 border border-[--border]">
          <div className="flex items-start justify-between gap-4 mb-3">
            <div>
              <p className="font-medium">{selectedPlace.name}</p>
              <p className="text-sm text-dim">{selectedPlace.formatted_address || selectedPlace.vicinity}</p>
            </div>
            <button
              type="button"
              onClick={handleImportHours}
              disabled={updateHoursFromGoogleMutation.isPending}
              className="btn btn-success flex items-center gap-2"
            >
              {updateHoursFromGoogleMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Importing...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Import
                </>
              )}
            </button>
          </div>
          <p className="text-xs text-dim">
            Click "Import" to set your operating hours from Google Maps.
          </p>
        </div>
      )}
    </div>
  )
}
