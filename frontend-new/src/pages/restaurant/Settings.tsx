import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import { useAuth } from '../../contexts/AuthContext'
import { Phone, Save, AlertCircle, CheckCircle, Info, ExternalLink, Clock, Search, MapPin, Loader2, Trash2, Plus, Edit, Leaf, Flame, UtensilsCrossed } from 'lucide-react'
import CreateMenuModal from '../../components/CreateMenuModal'

export default function Settings() {
  const { user } = useAuth()
  const accountId = user?.id
  const queryClient = useQueryClient()
  const [phoneNumber, setPhoneNumber] = useState('')
  const [openingTime, setOpeningTime] = useState('')
  const [closingTime, setClosingTime] = useState('')
  const [operatingDays, setOperatingDays] = useState<number[]>([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  // Google Maps search state
  const [searchQuery, setSearchQuery] = useState('')
  const [searchLocation, setSearchLocation] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [selectedPlace, setSelectedPlace] = useState<any>(null)
  
  // Menu state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  
  const weekdays = [
    { value: 0, label: 'Monday' },
    { value: 1, label: 'Tuesday' },
    { value: 2, label: 'Wednesday' },
    { value: 3, label: 'Thursday' },
    { value: 4, label: 'Friday' },
    { value: 5, label: 'Saturday' },
    { value: 6, label: 'Sunday' },
  ]

  // Fetch current account details
  const { data: account, isLoading } = useQuery({
    queryKey: ['account', accountId],
    queryFn: async () => {
      const response = await restaurantAPI.getAccount(accountId!)
      return response.data
    },
    enabled: !!accountId,
  })

  // Fetch menu data
  const { data: menuData, isLoading: isMenuLoading } = useQuery({
    queryKey: ['menu', accountId],
    queryFn: () => restaurantAPI.getMenu(accountId!),
    enabled: !!accountId,
  })

  const menu = menuData?.data

  // Mutation to delete a single menu item
  const deleteItemMutation = useMutation({
    mutationFn: (itemId: number) => restaurantAPI.deleteMenuItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
    },
  })

  // Mutation to delete all menu items
  const deleteAllItemsMutation = useMutation({
    mutationFn: ({ accountId, menuId }: { accountId: number; menuId: number }) =>
      restaurantAPI.deleteAllMenuItems(accountId, menuId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
    },
  })

  const handleDeleteItem = (itemId: number, itemName: string) => {
    if (window.confirm(`Are you sure you want to delete "${itemName}"? This action cannot be undone.`)) {
      deleteItemMutation.mutate(itemId)
    }
  }

  const handleDeleteAllItems = (menuId: number, menuName: string) => {
    if (window.confirm(`Are you sure you want to delete ALL items from "${menuName}"? This action cannot be undone.`)) {
      if (accountId) {
        deleteAllItemsMutation.mutate({ accountId, menuId })
      }
    }
  }

  const getDietaryBadge = (tags: string[]) => {
    const badges = []
    if (tags?.includes('vegetarian')) {
      badges.push(
        <span key="veg" className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-green-100 text-green-700 rounded">
          <Leaf className="w-3 h-3" /> Vegetarian
        </span>
      )
    }
    if (tags?.includes('vegan')) {
      badges.push(
        <span key="vegan" className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-green-100 text-green-700 rounded">
          <Leaf className="w-3 h-3" /> Vegan
        </span>
      )
    }
    if (tags?.includes('halal')) {
      badges.push(
        <span key="halal" className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
          Halal
        </span>
      )
    }
    if (tags?.includes('spicy')) {
      badges.push(
        <span key="spicy" className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-red-100 text-red-700 rounded">
          <Flame className="w-3 h-3" /> Spicy
        </span>
      )
    }
    return badges
  }

  // Update form fields when account data loads
  useEffect(() => {
    if (account) {
      if (account.twilio_phone_number) {
        setPhoneNumber(account.twilio_phone_number)
      }
      if (account.opening_time) {
        setOpeningTime(account.opening_time)
      }
      if (account.closing_time) {
        setClosingTime(account.closing_time)
      }
      if (account.operating_days) {
        setOperatingDays(account.operating_days)
      }
    }
  }, [account])

  // Mutation to update phone number
  const updatePhoneMutation = useMutation({
    mutationFn: async (phone: string) => {
      return restaurantAPI.updateTwilioPhone(accountId!, phone)
    },
    onSuccess: () => {
      setSuccess('Phone number updated successfully!')
      setError('')
      queryClient.invalidateQueries({ queryKey: ['account', accountId] })
      setTimeout(() => setSuccess(''), 5000)
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to update phone number')
      setSuccess('')
    },
  })

  // Mutation to remove phone number
  const removePhoneMutation = useMutation({
    mutationFn: async () => {
      return restaurantAPI.removeTwilioPhone(accountId!)
    },
    onSuccess: () => {
      setSuccess('Phone number removed successfully!')
      setError('')
      setPhoneNumber('')
      queryClient.invalidateQueries({ queryKey: ['account', accountId] })
      setTimeout(() => setSuccess(''), 5000)
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to remove phone number')
      setSuccess('')
    },
  })

  const handleRemovePhone = () => {
    if (window.confirm('Are you sure you want to remove the phone number? Voice AI will be disabled until you set a new number.')) {
      removePhoneMutation.mutate()
    }
  }

  // Mutation to update operating hours
  const updateHoursMutation = useMutation({
    mutationFn: async (hours: { opening_time?: string; closing_time?: string; operating_days?: number[] }) => {
      return restaurantAPI.updateOperatingHours(accountId!, hours)
    },
    onSuccess: () => {
      setSuccess('Operating hours updated successfully!')
      setError('')
      queryClient.invalidateQueries({ queryKey: ['account', accountId] })
      setTimeout(() => setSuccess(''), 5000)
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to update operating hours')
      setSuccess('')
    },
  })

  // Mutation to update hours from Google Maps
  const updateHoursFromGoogleMutation = useMutation({
    mutationFn: async (placeId: string) => {
      return restaurantAPI.updateHoursFromGoogle(accountId!, placeId)
    },
    onSuccess: (response) => {
      const data = response.data
      // Update form fields with imported hours
      if (data.opening_time) setOpeningTime(data.opening_time)
      if (data.closing_time) setClosingTime(data.closing_time)
      if (data.operating_days) setOperatingDays(data.operating_days)
      setSuccess('Operating hours imported from Google Maps successfully!')
      setError('')
      setSelectedPlace(null)
      setSearchResults([])
      setSearchQuery('')
      queryClient.invalidateQueries({ queryKey: ['account', accountId] })
      setTimeout(() => setSuccess(''), 5000)
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to import hours from Google Maps')
      setSuccess('')
    },
  })

  // Handle Google Maps search
  const handleGoogleMapsSearch = async (e: React.FormEvent) => {
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
      setError(err.response?.data?.detail || 'Failed to search Google Maps. Make sure GOOGLE_MAPS_API_KEY is configured.')
    } finally {
      setIsSearching(false)
    }
  }

  // Handle selecting a place from search results
  const handleSelectPlace = async (place: any) => {
    setSelectedPlace(place)
    setError('')
    
    try {
      // Get place details to preview hours
      const response = await restaurantAPI.getGoogleMapsPlace(place.place_id)
      const placeDetails = response.data
      
      // Show preview of hours
      const hours = placeDetails.opening_hours
      if (hours?.opening_time && hours?.closing_time) {
        setOpeningTime(hours.opening_time)
        setClosingTime(hours.closing_time)
      }
      if (hours?.operating_days) {
        setOperatingDays(hours.operating_days)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to get place details')
    }
  }

  // Handle importing hours from selected place
  const handleImportHours = () => {
    if (!selectedPlace) {
      setError('Please select a restaurant from the search results')
      return
    }
    updateHoursFromGoogleMutation.mutate(selectedPlace.place_id)
  }

  const handlePhoneSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    // Validate phone number format
    if (!phoneNumber.trim()) {
      setError('Phone number is required')
      return
    }

    if (!phoneNumber.startsWith('+')) {
      setError('Phone number must be in E.164 format (e.g., +15551234567). Must start with +')
      return
    }

    const digitsOnly = phoneNumber.replace(/[^\d]/g, '')
    if (digitsOnly.length < 10) {
      setError('Phone number must contain at least 10 digits')
      return
    }

    updatePhoneMutation.mutate(phoneNumber.trim())
  }

  const handleHoursSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    // Validate time format
    const timeRegex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/
    
    if (openingTime && !timeRegex.test(openingTime)) {
      setError('Opening time must be in HH:MM format (e.g., 09:00)')
      return
    }

    if (closingTime && !timeRegex.test(closingTime)) {
      setError('Closing time must be in HH:MM format (e.g., 22:00)')
      return
    }

    if (openingTime && closingTime && openingTime >= closingTime) {
      setError('Opening time must be before closing time')
      return
    }

    updateHoursMutation.mutate({
      opening_time: openingTime || undefined,
      closing_time: closingTime || undefined,
      operating_days: operatingDays.length > 0 ? operatingDays : undefined,
    })
  }

  const toggleDay = (day: number) => {
    setOperatingDays(prev => 
      prev.includes(day) 
        ? prev.filter(d => d !== day)
        : [...prev, day].sort()
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-primary-200 border-t-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in pb-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-secondary-600 rounded-2xl p-8 text-white shadow-xl">
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-blue-100">Configure your restaurant's phone number, operating hours, and menu</p>
      </div>

      {/* Twilio Phone Number Configuration */}
      <div className="bg-white rounded-2xl p-8 shadow-card border border-gray-100">
        <div className="flex items-start gap-4 mb-6">
          <div className="p-3 bg-primary-100 rounded-xl">
            <Phone className="w-6 h-6 text-primary-600" />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Voice AI Phone Number</h2>
            <p className="text-gray-600">
              Configure the Twilio phone number that customers will call. This number is used to identify your restaurant when calls come in.
            </p>
          </div>
        </div>

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-blue-900 mb-2">How to get a Twilio phone number:</p>
              <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                <li>Sign up for a Twilio account at{' '}
                  <a href="https://www.twilio.com/try-twilio" target="_blank" rel="noopener noreferrer" 
                     className="underline hover:text-blue-900 inline-flex items-center gap-1">
                    twilio.com <ExternalLink className="w-3 h-3" />
                  </a>
                </li>
                <li>Buy a phone number in the Twilio Console (starts at $1/month)</li>
                <li>Configure webhooks in Twilio:
                  <ul className="list-disc list-inside ml-4 mt-1 space-y-0.5">
                    <li>Voice: <code className="bg-blue-100 px-1 rounded">https://your-domain.com/api/voice/welcome</code></li>
                    <li>SMS: <code className="bg-blue-100 px-1 rounded">https://your-domain.com/api/voice/sms/incoming</code></li>
                  </ul>
                </li>
                <li>Enter your Twilio phone number below (E.164 format: +15551234567)</li>
              </ol>
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handlePhoneSubmit} className="space-y-4">
          <div>
            <label htmlFor="phone" className="block text-sm font-semibold text-gray-700 mb-2">
              Twilio Phone Number
            </label>
            <div className="flex gap-3">
              <div className="flex-1">
                <input
                  type="text"
                  id="phone"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="+15551234567"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                  disabled={updatePhoneMutation.isPending}
                />
                <p className="text-xs text-gray-500 mt-2">
                  Format: +[country code][number] (e.g., +15551234567 for US)
                </p>
              </div>
              <button
                type="submit"
                disabled={updatePhoneMutation.isPending || !phoneNumber.trim()}
                className="px-6 py-3 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {updatePhoneMutation.isPending ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Save
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-800">{success}</p>
            </div>
          )}

          {/* Current Status */}
          {account?.twilio_phone_number && (
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-semibold text-gray-700 mb-1">Current Phone Number:</p>
                  <p className="text-lg font-mono text-gray-900">{account.twilio_phone_number}</p>
                  <p className="text-xs text-gray-500 mt-2">
                    Customers can call this number to reach your AI assistant
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleRemovePhone}
                  disabled={removePhoneMutation.isPending}
                  className="ml-4 px-4 py-2 bg-red-50 text-red-600 border border-red-200 rounded-xl font-medium hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  <Trash2 className="w-4 h-4" />
                  {removePhoneMutation.isPending ? 'Removing...' : 'Remove'}
                </button>
              </div>
            </div>
          )}

          {!account?.twilio_phone_number && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
              <p className="text-sm text-yellow-800">
                <strong>No phone number configured.</strong> Voice AI will not work until you set a Twilio phone number.
              </p>
            </div>
          )}
        </form>
      </div>

      {/* Operating Hours Configuration */}
      <div className="bg-white rounded-2xl p-8 shadow-card border border-gray-100">
        <div className="flex items-start gap-4 mb-6">
          <div className="p-3 bg-primary-100 rounded-xl">
            <Clock className="w-6 h-6 text-primary-600" />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Operating Hours</h2>
            <p className="text-gray-600">
              Set your restaurant's operating hours manually or import them from Google Maps. The AI assistant will use this information to answer customer questions about when you're open.
            </p>
          </div>
        </div>

        {/* Google Maps Search Section */}
        <div className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border-2 border-blue-300 shadow-md">
          <div className="flex items-start gap-3 mb-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <MapPin className="w-6 h-6 text-blue-600 flex-shrink-0" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900 mb-1">Import from Google Maps</h3>
              <p className="text-sm text-gray-600">
                Search for your restaurant on Google Maps to automatically import operating hours and use the restaurant information for menu creation.
              </p>
            </div>
          </div>

          <form onSubmit={handleGoogleMapsSearch} className="space-y-3 mb-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="md:col-span-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search for your restaurant (e.g., 'Joe's Pizza' or 'Joe's Pizza, New York')"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isSearching}
                />
              </div>
              <div>
                <input
                  type="text"
                  value={searchLocation}
                  onChange={(e) => setSearchLocation(e.target.value)}
                  placeholder="Location (optional)"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isSearching}
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={isSearching || !searchQuery.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isSearching ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  Search Google Maps
                </>
              )}
            </button>
          </form>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-sm font-semibold text-gray-700">Search Results:</p>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {searchResults.map((place) => (
                  <button
                    key={place.place_id}
                    type="button"
                    onClick={() => handleSelectPlace(place)}
                    className={`w-full text-left p-3 rounded-lg border-2 transition-all ${
                      selectedPlace?.place_id === place.place_id
                        ? 'border-blue-600 bg-blue-50'
                        : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <p className="font-semibold text-gray-900">{place.name}</p>
                        <p className="text-sm text-gray-600 mt-1">
                          {place.formatted_address || place.vicinity}
                        </p>
                        {place.rating && (
                          <p className="text-xs text-gray-500 mt-1">
                            ⭐ {place.rating} ({place.user_ratings_total} reviews)
                          </p>
                        )}
                      </div>
                      {selectedPlace?.place_id === place.place_id && (
                        <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0" />
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Selected Place Actions */}
          {selectedPlace && (
            <div className="mt-4 p-4 bg-white rounded-lg border border-blue-300">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <p className="font-semibold text-gray-900">{selectedPlace.name}</p>
                  <p className="text-sm text-gray-600">{selectedPlace.formatted_address || selectedPlace.vicinity}</p>
                </div>
                <button
                  type="button"
                  onClick={handleImportHours}
                  disabled={updateHoursFromGoogleMutation.isPending}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  {updateHoursFromGoogleMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Importing...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      Import Hours
                    </>
                  )}
                </button>
              </div>
              <div className="space-y-2">
                <p className="text-xs text-gray-500">
                  Click "Import Hours" to automatically set your operating hours from Google Maps.
                </p>
                <p className="text-xs text-blue-600">
                  💡 <strong>Tip:</strong> You can use the restaurant name "{selectedPlace.name}" when creating your menu. The restaurant information from Google Maps will help ensure consistency across your listing.
                </p>
              </div>
            </div>
          )}

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gradient-to-r from-blue-50 to-indigo-50 text-gray-500">OR</span>
            </div>
          </div>
        </div>

        <form onSubmit={handleHoursSubmit} className="space-y-6">
          {/* Time Inputs */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="opening-time" className="block text-sm font-semibold text-gray-700 mb-2">
                Opening Time
              </label>
              <input
                type="time"
                id="opening-time"
                value={openingTime}
                onChange={(e) => setOpeningTime(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                disabled={updateHoursMutation.isPending}
              />
              <p className="text-xs text-gray-500 mt-2">When your restaurant opens (24-hour format)</p>
            </div>

            <div>
              <label htmlFor="closing-time" className="block text-sm font-semibold text-gray-700 mb-2">
                Closing Time
              </label>
              <input
                type="time"
                id="closing-time"
                value={closingTime}
                onChange={(e) => setClosingTime(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                disabled={updateHoursMutation.isPending}
              />
              <p className="text-xs text-gray-500 mt-2">When your restaurant closes (24-hour format)</p>
            </div>
          </div>

          {/* Operating Days */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Operating Days
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {weekdays.map((day) => (
                <button
                  key={day.value}
                  type="button"
                  onClick={() => toggleDay(day.value)}
                  disabled={updateHoursMutation.isPending}
                  className={`px-4 py-2 rounded-lg border-2 transition-all ${
                    operatingDays.includes(day.value)
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:border-primary-300'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {day.label}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">Select the days your restaurant is open</p>
          </div>

          {/* Save Button */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={updateHoursMutation.isPending}
              className="px-6 py-3 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {updateHoursMutation.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save Hours
                </>
              )}
            </button>
          </div>
        </form>

        {/* Current Hours Display */}
        {(account?.opening_time || account?.closing_time || account?.operating_days?.length) && (
          <div className="mt-6 bg-gray-50 border border-gray-200 rounded-xl p-4">
            <p className="text-sm font-semibold text-gray-700 mb-2">Current Operating Hours:</p>
            {account.opening_time && account.closing_time && (
              <p className="text-lg text-gray-900 mb-2">
                {account.opening_time} - {account.closing_time}
              </p>
            )}
            {account.operating_days && account.operating_days.length > 0 && (
              <p className="text-sm text-gray-600">
                Open: {account.operating_days.map((d: number) => weekdays[d].label).join(', ')}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Menu Configuration */}
      <div className="bg-white rounded-2xl p-8 shadow-card border border-gray-100">
        <div className="flex items-start gap-4 mb-6">
          <div className="p-3 bg-primary-100 rounded-xl">
            <UtensilsCrossed className="w-6 h-6 text-primary-600" />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-xl font-bold text-gray-900">Menu</h2>
              <button 
                onClick={() => setIsCreateModalOpen(true)} 
                className="btn btn-primary"
              >
                <Plus className="w-5 h-5 mr-2" /> Create Menu
              </button>
            </div>
            <p className="text-gray-600">
              Manage your restaurant menu. The AI assistant uses this information to answer customer questions about your menu items.
            </p>
          </div>
        </div>

        {isMenuLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-200 border-t-primary-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading menu...</p>
          </div>
        ) : !menu?.menus || menu.menus.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-xl border border-gray-200">
            <p className="text-gray-500">No menu created yet. Start by creating your first menu.</p>
          </div>
        ) : (
          <div className="space-y-8">
            {menu.menus.map((menuObj: any) => {
              const totalItems = menuObj.categories.reduce((sum: number, cat: any) => sum + (cat.items?.length || 0), 0)
              return (
                <div key={menuObj.id} className="border border-gray-200 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-6 p-4 bg-gray-50 rounded-lg">
                    <div>
                      <h3 className="text-xl font-bold">{menuObj.name}</h3>
                      <p className="text-sm text-gray-500 mt-1">{totalItems} item(s) total</p>
                    </div>
                    {totalItems > 0 && (
                      <button
                        onClick={() => handleDeleteAllItems(menuObj.id, menuObj.name)}
                        disabled={deleteAllItemsMutation.isPending}
                        className="px-4 py-2 bg-red-50 text-red-600 border border-red-200 rounded-lg font-medium hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                      >
                        <Trash2 className="w-4 h-4" />
                        {deleteAllItemsMutation.isPending ? 'Deleting...' : 'Delete All Items'}
                      </button>
                    )}
                  </div>
                  {menuObj.categories.map((category: any) => (
                    <div key={category.id} className="mb-6">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="text-lg font-bold">{category.name}</h4>
                        <button className="text-sm text-primary-600 hover:text-primary-700">
                          Edit Category
                        </button>
                      </div>
                      <div className="grid gap-4">
                        {category.items.map((item: any) => (
                          <div key={item.id} className="card hover:shadow-md transition-shadow">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-start justify-between">
                                  <div>
                                    <h5 className="font-semibold text-lg">{item.name}</h5>
                                    <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                                  </div>
                                  <p className="text-xl font-bold text-primary-600 ml-4">
                                    ${(item.price_cents / 100).toFixed(2)}
                                  </p>
                                </div>
                                {item.dietary_tags && item.dietary_tags.length > 0 && (
                                  <div className="flex gap-2 mt-3">
                                    {getDietaryBadge(item.dietary_tags)}
                                  </div>
                                )}
                                {item.modifiers && item.modifiers.length > 0 && (
                                  <div className="mt-3 pt-3 border-t border-gray-200">
                                    <p className="text-xs font-medium text-gray-700 mb-2">Customizations:</p>
                                    <div className="flex flex-wrap gap-2">
                                      {item.modifiers.map((mod: any) => (
                                        <span
                                          key={mod.id}
                                          className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded"
                                        >
                                          {mod.name}
                                          {mod.price_cents > 0 && ` (+$${(mod.price_cents / 100).toFixed(2)})`}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                              <div className="ml-4 flex gap-2">
                                <button className="p-2 text-gray-400 hover:text-gray-600">
                                  <Edit className="w-5 h-5" />
                                </button>
                                <button
                                  onClick={() => handleDeleteItem(item.id, item.name)}
                                  disabled={deleteItemMutation.isPending}
                                  className="p-2 text-red-400 hover:text-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                  title="Delete item"
                                >
                                  <Trash2 className="w-5 h-5" />
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Additional Information */}
      <div className="bg-white rounded-2xl p-8 shadow-card border border-gray-100">
        <h3 className="text-lg font-bold text-gray-900 mb-4">What happens after configuration?</h3>
        <div className="space-y-3 text-gray-700">
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-semibold text-sm flex-shrink-0 mt-0.5">
              1
            </div>
            <p>Customer calls your Twilio phone number</p>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-semibold text-sm flex-shrink-0 mt-0.5">
              2
            </div>
            <p>AI assistant answers and identifies your restaurant by the phone number</p>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-semibold text-sm flex-shrink-0 mt-0.5">
              3
            </div>
            <p>AI can answer operating hours questions, take orders, and make reservations</p>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-semibold text-sm flex-shrink-0 mt-0.5">
              4
            </div>
            <p>Orders and reservations appear in your dashboard automatically</p>
          </div>
        </div>
      </div>

      {/* Create Menu Modal */}
      {accountId && (
        <CreateMenuModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          accountId={accountId}
        />
      )}
    </div>
  )
}
