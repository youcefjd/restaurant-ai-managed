import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import { useAuth } from '../../contexts/AuthContext'
import { Phone, Save, AlertCircle, CheckCircle, Info, ExternalLink, Clock } from 'lucide-react'

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
    <div className="space-y-6 animate-fade-in pb-8 max-w-4xl">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-secondary-600 rounded-2xl p-8 text-white shadow-xl">
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-blue-100">Configure your restaurant's phone number and operating hours</p>
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
              <p className="text-sm font-semibold text-gray-700 mb-1">Current Phone Number:</p>
              <p className="text-lg font-mono text-gray-900">{account.twilio_phone_number}</p>
              <p className="text-xs text-gray-500 mt-2">
                Customers can call this number to reach your AI assistant
              </p>
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
              Set your restaurant's operating hours. The AI assistant will use this information to answer customer questions about when you're open.
            </p>
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
    </div>
  )
}
